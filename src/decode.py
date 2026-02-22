"""Decoding pipeline: .kee metafile -> restored audio file."""

from __future__ import annotations

from pathlib import Path

from .custom_format import read_kee
from .io_audio import save_audio
from .metadata import CodecMetadata
from .resample import lowpass_filter, upsample


def decode(
    kee_path: str | Path,
    output_audio_path: str | Path,
) -> CodecMetadata:
    """Decode a .kee metafile back into an audio file.

    Steps
    -----
    1. Read .kee  -> (metadata, downsampled samples at fs_new).
    2. Upsample by D  -> signal at fs_original = fs_new * D.
    3. Reconstruction LPF at cutoff = fs_new / 2  (keep baseband only).
    4. Write restored audio as WAV at fs_original.

    Returns
    -------
    The CodecMetadata read from the .kee file.
    """
    metadata, samples = read_kee(kee_path)

    d = metadata.downsample_factor
    fs_new = metadata.fs_new
    fs_original = metadata.fs_original

    if d > 1:
        upsampled = upsample(samples, d)
        cutoff = fs_new / 2.0
        restored = lowpass_filter(upsampled, cutoff, fs_original)
    else:
        restored = samples

    # Trim to original length (upsampling may add a few extra samples)
    n_target = metadata.n_samples_original
    if restored.ndim == 1:
        restored = restored[:n_target]
    else:
        restored = restored[:n_target, :]

    save_audio(output_audio_path, restored, fs_original)
    return metadata
