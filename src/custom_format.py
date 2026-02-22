""".kee custom format reader / writer.

File layout
-----------
Offset  Size       Field
0       4          Magic bytes  b"KEE\\x00"
4       2          Format version (uint16, little-endian)
6       4          Metadata length in bytes (uint32, little-endian)
10      M          JSON-encoded metadata (variable length M)
10+M    ...        Payload – raw PCM int16 samples (little-endian)
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

from .metadata import CodecMetadata

MAGIC = b"KEE\x00"
FORMAT_VERSION = 1


def write_kee(path: str | Path, metadata: CodecMetadata, samples: np.ndarray) -> None:
    """Serialize metadata + audio payload into a .kee file."""
    meta_bytes = metadata.to_bytes()

    pcm = np.clip(samples, -1.0, 1.0)
    pcm_int16 = (pcm * 32767).astype("<i2")  # little-endian int16

    with open(str(path), "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<H", FORMAT_VERSION))
        f.write(struct.pack("<I", len(meta_bytes)))
        f.write(meta_bytes)
        f.write(pcm_int16.tobytes())


def read_kee(path: str | Path) -> tuple[CodecMetadata, np.ndarray]:
    """Deserialize a .kee file into (metadata, float64 samples)."""
    with open(str(path), "rb") as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError(f"Not a valid .kee file (magic={magic!r})")

        (version,) = struct.unpack("<H", f.read(2))
        if version > FORMAT_VERSION:
            raise ValueError(f"Unsupported .kee version {version}")

        (meta_len,) = struct.unpack("<I", f.read(4))
        meta_bytes = f.read(meta_len)
        metadata = CodecMetadata.from_bytes(meta_bytes)

        payload = f.read()

    pcm_int16 = np.frombuffer(payload, dtype="<i2")

    if metadata.channels > 1:
        pcm_int16 = pcm_int16.reshape(-1, metadata.channels)

    samples = pcm_int16.astype(np.float64) / 32767.0
    return metadata, samples
