---
name: kee-audio-codec
description: >
  Use this skill whenever the user wants to compress an audio file, encode audio,
  decode audio, restore a .kee file, use the KEE audio codec, or perform any operation
  involving the KEE_audio_codec GitHub repo. Triggers include: "compress my audio",
  "encode this wav", "decode the .kee file", "restore audio", "use the KEE codec",
  "convert audio to .kee", or any mention of .kee files. Always use this skill if the
  user provides a .wav, .mp3, .flac, or .kee file and asks to compress, encode, decode,
  or restore it.
---

# KEE audio codec skill

Clones the KEE_audio_codec repo and uses it to either **encode** (compress)
an audio file into `.kee` format, or **decode** (restore) a `.kee` file back to `.wav`.

## Workflow

1. Determine operation (ENCODE or DECODE)
2. Locate the input file from user uploads
3. Clone the repo + install dependencies
4. Run the appropriate CLI command
5. Present the output file to the user

## Step 1 — Determine Operation

| User intent | Operation |
|---|---|
| Compress / encode WAV/MP3/FLAC → .kee | ENCODE |
| Decompress / decode / restore .kee → WAV | DECODE |

If ambiguous, ask the user before proceeding.

## Step 2 — Locate Input File
```bash
ls /mnt/user-data/uploads/
cp "/mnt/user-data/uploads/" /home/claude/
```

## Step 3 — Set Up the Codec
```bash
cd /home/claude

if [ ! -d "KEE_audio_codec" ]; then
  git clone https://github.com/ke-ets/KEE_audio_codec.git
fi

cd KEE_audio_codec
pip install -r requirements.txt --break-system-packages -q
```

## Step 4 — Run the Codec

### ENCODE (audio → .kee)
```bash
cd /home/claude/KEE_audio_codec

python -m scripts.cli_encode "/home/claude/" \
  -o "/home/claude/.kee"
```

Optional flags:
- `-d <int>` — manual downsample factor
- `--threshold <int>` — FFT amplitude threshold (default: 500)
Omit both to use automatic FFT-based mode.

### DECODE (.kee → .wav)
```bash
cd /home/claude/KEE_audio_codec

python -m scripts.cli_decode "/home/claude/.kee" \
  -o "/home/claude/_restored.wav"
```

## Step 5 — Deliver Output

Copy the result to the outputs folder and present it:
```bash
cp /home/claude/ /mnt/user-data/outputs/
```

Then use the `present_files` tool to share the file with the user.

## Error Handling

| Error | Fix |
|---|---|
| `git` not available | Ask user to upload repo files manually |
| Network blocked | Same as above |
| Unsupported audio format | Inform user; supported: WAV, MP3, FLAC, OGG |
| `.kee` file corrupt / wrong magic bytes | Inform user the file may be invalid |

## Notes

- Always prefer automatic FFT-based downsample (no `-d` flag) unless the user explicitly sets one
- After encoding, tell the user the compression achieved (compare input vs output file size)
- After decoding, mention that the restored audio is at the original sample rate
