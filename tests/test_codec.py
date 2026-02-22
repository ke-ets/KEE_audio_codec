"""Integration tests: encode -> decode round-trip."""

import os
import tempfile

import numpy as np
import soundfile as sf

from src.decode import decode
from src.encode import encode


def _create_test_wav(path: str, duration: float = 1.0, fs: int = 44100, channels: int = 1):
    """Generate a sine-wave test WAV file."""
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    if channels > 1:
        tone = np.column_stack([tone] * channels)
    sf.write(path, tone, fs, subtype="PCM_16")


class TestEncodeDecodeRoundTrip:
    def test_auto_d_mono(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav_in = os.path.join(tmp, "input.wav")
            kee = os.path.join(tmp, "output.kee")
            wav_out = os.path.join(tmp, "restored.wav")

            _create_test_wav(wav_in, duration=0.5, fs=44100, channels=1)
            meta_enc = encode(wav_in, kee)
            assert os.path.isfile(kee)
            assert meta_enc.downsample_factor >= 1

            meta_dec = decode(kee, wav_out)
            assert os.path.isfile(wav_out)

            orig, sr_orig = sf.read(wav_in)
            rest, sr_rest = sf.read(wav_out)
            assert sr_rest == sr_orig
            assert abs(len(rest) - len(orig)) <= 10  # allow tiny length diff

    def test_user_d_mono(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav_in = os.path.join(tmp, "input.wav")
            kee = os.path.join(tmp, "output.kee")
            wav_out = os.path.join(tmp, "restored.wav")

            _create_test_wav(wav_in, duration=0.5, fs=44100, channels=1)
            meta_enc = encode(wav_in, kee, downsample_factor=4)
            assert meta_enc.downsample_factor == 4
            assert os.path.getsize(kee) < os.path.getsize(wav_in)

            decode(kee, wav_out)
            rest, sr_rest = sf.read(wav_out)
            assert sr_rest == 44100

    def test_stereo_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav_in = os.path.join(tmp, "stereo.wav")
            kee = os.path.join(tmp, "stereo.kee")
            wav_out = os.path.join(tmp, "stereo_restored.wav")

            _create_test_wav(wav_in, duration=0.5, fs=44100, channels=2)
            encode(wav_in, kee, downsample_factor=2)
            meta = decode(kee, wav_out)
            assert meta.channels == 2

            rest, sr = sf.read(wav_out)
            assert rest.ndim == 2
            assert rest.shape[1] == 2

    def test_compression_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav_in = os.path.join(tmp, "input.wav")
            kee = os.path.join(tmp, "output.kee")

            _create_test_wav(wav_in, duration=1.0, fs=44100, channels=1)
            encode(wav_in, kee, downsample_factor=4)

            orig_size = os.path.getsize(wav_in)
            comp_size = os.path.getsize(kee)
            assert comp_size < orig_size, "Compressed file should be smaller"
