"""Encoding pipeline: audio file -> .kee metafile."""

from __future__ import annotations

import math
from pathlib import Path

from .custom_format import write_kee
from .downsample_factor import compute_auto_downsample_factor
from .io_audio import load_audio
from .metadata import CodecMetadata, compute_checksum
from .resample import decimate, lowpass_filter


def encode(
    audio_path: str | Path,
    output_path: str | Path,
    downsample_factor: int | None = None,
    threshold: float = 500.0,
) -> CodecMetadata:
    """Encode an audio file into a .kee metafile.

    Parameters
    ----------
    audio_path : path to the input audio file (WAV, FLAC, etc.).
    output_path : destination path for the .kee file.
    downsample_factor : integer D supplied by the user.  When *None* the
        FFT-based auto-computation is used instead.
    threshold : amplitude threshold for auto-D computation (ignored when
        *downsample_factor* is provided).

    Returns
    -------
    The CodecMetadata written into the .kee file.
    """
    audio = load_audio(audio_path)
    samples = audio.samples
    fs_original = audio.sample_rate

    if downsample_factor is not None:
        d = max(1, downsample_factor)
        fs_new = int(math.ceil(fs_original / d))
    else:
        d, fs_new = compute_auto_downsample_factor(samples, fs_original, threshold)

    if d > 1:
        cutoff = fs_new / 2.0
        filtered = lowpass_filter(samples, cutoff, fs_original)
        downsampled = decimate(filtered, d)
    else:
        downsampled = samples

    checksum = compute_checksum(downsampled)

    metadata = CodecMetadata(
        fs_original=fs_original,
        fs_new=fs_new,
        downsample_factor=d,
        channels=audio.channels,
        duration=audio.duration,
        n_samples_original=audio.n_samples,
        checksum=checksum,
    )

    write_kee(output_path, metadata, downsampled)
    return metadata
