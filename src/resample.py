"""Resampling utilities: low-pass filter, decimate, and upsample."""

import numpy as np
from scipy.signal import firwin, lfilter, resample_poly


def lowpass_filter(
    samples: np.ndarray,
    cutoff_hz: float,
    fs: int,
    numtaps: int = 101,
) -> np.ndarray:
    """Apply a FIR low-pass filter to *samples*."""
    nyquist = fs / 2.0
    if cutoff_hz >= nyquist:
        return samples
    normalized_cutoff = cutoff_hz / nyquist
    coeffs = firwin(numtaps, normalized_cutoff)
    if samples.ndim == 1:
        return lfilter(coeffs, 1.0, samples)
    # multi-channel: filter each channel independently
    return np.column_stack(
        [lfilter(coeffs, 1.0, samples[:, ch]) for ch in range(samples.shape[1])]
    )


def decimate(samples: np.ndarray, factor: int) -> np.ndarray:
    """Decimate (take every *factor*-th sample) without additional filtering."""
    return samples[::factor] if samples.ndim == 1 else samples[::factor, :]


def upsample(samples: np.ndarray, factor: int) -> np.ndarray:
    """Upsample by integer factor using polyphase resampling."""
    if samples.ndim == 1:
        return resample_poly(samples, factor, 1)
    return np.column_stack(
        [resample_poly(samples[:, ch], factor, 1) for ch in range(samples.shape[1])]
    )
