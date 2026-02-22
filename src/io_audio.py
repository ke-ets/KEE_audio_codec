"""Audio file I/O: load and save audio using soundfile."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass
class AudioData:
    samples: np.ndarray       # shape (n_samples,) for mono or (n_samples, channels) for multi
    sample_rate: int
    channels: int
    subtype: str              # e.g. "PCM_16"
    n_samples: int
    duration: float


def load_audio(path: str | Path) -> AudioData:
    """Load an audio file and return an AudioData object."""
    info = sf.info(str(path))
    samples, sr = sf.read(str(path), dtype="float64", always_2d=False)
    return AudioData(
        samples=samples,
        sample_rate=sr,
        channels=info.channels,
        subtype=info.subtype,
        n_samples=len(samples),
        duration=info.duration,
    )


def save_audio(path: str | Path, samples: np.ndarray, sample_rate: int) -> None:
    """Write samples to a WAV file at the given sample rate."""
    sf.write(str(path), samples, sample_rate, subtype="PCM_16")
