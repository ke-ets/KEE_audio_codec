"""Metadata schema for the .kee custom format."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class CodecMetadata:
    fs_original: int
    fs_new: int
    downsample_factor: int
    channels: int
    duration: float
    n_samples_original: int
    checksum: str = ""

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> CodecMetadata:
        d = json.loads(data.decode("utf-8"))
        return cls(**d)


def compute_checksum(samples: np.ndarray) -> str:
    """SHA-256 hex digest of raw sample bytes (for integrity verification)."""
    return hashlib.sha256(np.ascontiguousarray(samples).tobytes()).hexdigest()
