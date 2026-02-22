"""Flask backend for the CODEC web UI."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import uuid

from flask import Flask, jsonify, render_template, request, send_file

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.decode import decode
from src.encode import encode

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "codec_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".flac", ".ogg", ".aiff"}


def _safe_path(filename: str) -> str:
    uid = uuid.uuid4().hex[:12]
    return os.path.join(UPLOAD_DIR, f"{uid}_{filename}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/encode", methods=["POST"])
def encode_endpoint():
    if "file" not in request.files:
        return jsonify(error="No file provided"), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify(error="Empty filename"), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify(error=f"Unsupported format '{ext}'. Use: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"), 400

    audio_path = _safe_path(f.filename)
    f.save(audio_path)

    file_size = os.path.getsize(audio_path)
    if file_size > MAX_UPLOAD_BYTES:
        os.remove(audio_path)
        return jsonify(error=f"File too large ({file_size:,} bytes). Max: {MAX_UPLOAD_BYTES:,} bytes."), 400

    d_str = request.form.get("downsample_factor", "").strip()
    downsample_factor = int(d_str) if d_str else None

    threshold_str = request.form.get("threshold", "500").strip()
    threshold = float(threshold_str) if threshold_str else 500.0

    kee_path = os.path.splitext(audio_path)[0] + ".kee"

    try:
        metadata = encode(audio_path, kee_path, downsample_factor, threshold)
    except Exception as exc:
        return jsonify(error=str(exc)), 500
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

    kee_size = os.path.getsize(kee_path)

    with open(kee_path, "rb") as kf:
        kee_bytes = kf.read()
    os.remove(kee_path)

    response = send_file(
        io.BytesIO(kee_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=os.path.splitext(os.path.basename(f.filename))[0] + ".kee",
    )
    response.headers["X-Codec-Fs-Original"] = str(metadata.fs_original)
    response.headers["X-Codec-Fs-New"] = str(metadata.fs_new)
    response.headers["X-Codec-D"] = str(metadata.downsample_factor)
    response.headers["X-Codec-Channels"] = str(metadata.channels)
    response.headers["X-Codec-Duration"] = f"{metadata.duration:.3f}"
    response.headers["X-Codec-Original-Size"] = str(file_size)
    response.headers["X-Codec-Compressed-Size"] = str(kee_size)
    response.headers["Access-Control-Expose-Headers"] = (
        "X-Codec-Fs-Original, X-Codec-Fs-New, X-Codec-D, "
        "X-Codec-Channels, X-Codec-Duration, X-Codec-Original-Size, X-Codec-Compressed-Size"
    )
    return response


@app.route("/decode", methods=["POST"])
def decode_endpoint():
    if "file" not in request.files:
        return jsonify(error="No .kee file provided"), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify(error="Empty filename"), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext != ".kee":
        return jsonify(error="Only .kee files are accepted for decoding"), 400

    kee_path = _safe_path(f.filename)
    f.save(kee_path)

    wav_path = os.path.splitext(kee_path)[0] + "_restored.wav"

    try:
        metadata = decode(kee_path, wav_path)
    except Exception as exc:
        return jsonify(error=str(exc)), 500
    finally:
        if os.path.exists(kee_path):
            os.remove(kee_path)

    with open(wav_path, "rb") as wf:
        wav_bytes = wf.read()
    os.remove(wav_path)

    original_name = os.path.splitext(os.path.basename(f.filename))[0]
    response = send_file(
        io.BytesIO(wav_bytes),
        mimetype="audio/wav",
        as_attachment=True,
        download_name=f"{original_name}_restored.wav",
    )
    response.headers["X-Codec-Fs-Original"] = str(metadata.fs_original)
    response.headers["X-Codec-D"] = str(metadata.downsample_factor)
    response.headers["X-Codec-Duration"] = f"{metadata.duration:.3f}"
    response.headers["Access-Control-Expose-Headers"] = (
        "X-Codec-Fs-Original, X-Codec-D, X-Codec-Duration"
    )
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
