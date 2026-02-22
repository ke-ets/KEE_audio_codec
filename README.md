# KEE Audio CODEC

A custom audio CODEC that compresses audio files into the `.kee` format using
FFT-based downsampling and restores them via upsampling with reconstruction
filtering.

## Quick start

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Encode an audio file (auto downsample factor)
python -m scripts.cli_encode input.wav -o output.kee

# 4. Decode the .kee back to audio
python -m scripts.cli_decode output.kee -o restored.wav
```

## CLI usage

### Encode

```
python -m scripts.cli_encode <input_audio> [-o output.kee] [-d FACTOR] [--threshold VALUE]
```

| Flag | Description |
|------|-------------|
| `-o` | Output `.kee` path (default: `<input_stem>.kee`) |
| `-d` | Downsample factor (omit for FFT-based auto) |
| `--threshold` | Amplitude threshold for auto-D (default: 500) |

### Decode

```
python -m scripts.cli_decode <input.kee> [-o restored.wav]
```

| Flag | Description |
|------|-------------|
| `-o` | Output audio path (default: `<input_stem>_restored.wav`) |

## Web UI

```bash
python web/app.py
# Open http://localhost:5000
```

The web interface provides:

- **Encode** -- browse an audio file, optionally set a downsample factor (or
  leave "Auto"), upload and encode, then download the `.kee` metafile.
- **Decode** -- browse a `.kee` file (or check "Use the metafile from the last
  encode" to reuse the one just produced), decode, then download the restored
  `.wav`.

## `.kee` format

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 B | Magic bytes `KEE\0` |
| 4 | 2 B | Format version (uint16 LE) |
| 6 | 4 B | Metadata length M (uint32 LE) |
| 10 | M B | JSON metadata (fs_original, fs_new, D, channels, duration, n_samples_original, checksum) |
| 10+M | ... | Payload: raw PCM int16 LE samples |

## How the CODEC works

### Encoding

1. Load audio and compute the FFT.
2. Apply an amplitude threshold to find the highest significant frequency bin.
3. Compute `f_max = bin * (fs / N)`, then `fs_new = 2 * f_max` (Nyquist).
4. `D = ceil(fs / fs_new)`.  (Or use the user-supplied D.)
5. Low-pass filter at `fs_new / 2`, then decimate by D.
6. Write metadata + downsampled PCM into a `.kee` file.

### Decoding

1. Read `.kee` header, metadata, and payload.
2. Upsample by D (polyphase resampling).
3. Reconstruction low-pass filter at `fs_new / 2` to keep only the baseband.
4. Write restored audio at `fs_original`.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

## Project structure

```
codec-project/
  src/
    io_audio.py           - Audio file I/O
    metadata.py           - Metadata schema + checksum
    downsample_factor.py  - FFT-based auto D computation
    resample.py           - LPF, decimate, upsample
    custom_format.py      - .kee reader / writer
    encode.py             - Encoding pipeline
    decode.py             - Decoding pipeline
  scripts/
    cli_encode.py         - CLI encoder
    cli_decode.py         - CLI decoder
  web/
    app.py                - Flask backend
    templates/index.html  - Web UI
    static/style.css      - Styles
    static/app.js         - Frontend logic
  tests/
    test_format.py        - .kee format + metadata tests
    test_codec.py         - Encode/decode round-trip tests
  requirements.txt
  README.md
```
