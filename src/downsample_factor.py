"""FFT-based automatic downsampling factor computation."""

import math

import numpy as np


def compute_auto_downsample_factor(
    samples: np.ndarray,
    fs_original: int,
    threshold: float = 500.0,
) -> tuple[int, int]:
    """Compute the downsampling factor D from the FFT of the signal.

    Algorithm
    ---------
    1. FFT of the (mono) signal.
    2. Keep frequency bins whose magnitude >= *threshold*.
    3. Highest kept bin gives f_max  =>  fs_new = 2 * f_max  (Nyquist).
    4. D = ceil(fs_original / fs_new).

    Parameters
    ----------
    samples : 1-D array (mono signal).
    fs_original : original sample rate.
    threshold : amplitude threshold for "significant" FFT bins.

    Returns
    -------
    (D, fs_new) – downsampling factor and new sampling frequency.
    """
    if samples.ndim > 1:
        mono = samples[:, 0]
    else:
        mono = samples

    n = len(mono)
    fft_vals = np.fft.rfft(mono)
    magnitudes = np.abs(fft_vals)

    significant_bins = np.where(magnitudes >= threshold)[0]

    if len(significant_bins) == 0:
        return 1, fs_original

    max_bin = int(significant_bins[-1])

    if max_bin == 0:
        return 1, fs_original

    f_max = max_bin * (fs_original / n)
    fs_new = int(math.ceil(2 * f_max))

    # fs_new must be at least 2 (minimum meaningful rate) and <= fs_original
    fs_new = max(2, min(fs_new, fs_original))

    d = math.ceil(fs_original / fs_new)
    d = max(1, d)

    # Recalculate fs_new so it divides evenly with the chosen integer D
    fs_new = int(math.ceil(fs_original / d))

    return d, fs_new
