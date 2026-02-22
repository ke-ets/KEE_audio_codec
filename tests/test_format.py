"""Tests for .kee custom format read/write and metadata serialization."""

import os
import tempfile

import numpy as np
import pytest

from src.custom_format import read_kee, write_kee
from src.metadata import CodecMetadata, compute_checksum


class TestMetadata:
    def test_round_trip(self):
        meta = CodecMetadata(
            fs_original=44100, fs_new=11025, downsample_factor=4,
            channels=1, duration=2.5, n_samples_original=110250,
            checksum="abc123",
        )
        raw = meta.to_bytes()
        restored = CodecMetadata.from_bytes(raw)
        assert restored.fs_original == 44100
        assert restored.fs_new == 11025
        assert restored.downsample_factor == 4
        assert restored.channels == 1
        assert restored.duration == 2.5
        assert restored.n_samples_original == 110250
        assert restored.checksum == "abc123"

    def test_checksum_deterministic(self):
        arr = np.array([0.1, -0.5, 0.9], dtype=np.float64)
        assert compute_checksum(arr) == compute_checksum(arr.copy())


class TestKeeFormat:
    def _make_temp_kee(self):
        fd, path = tempfile.mkstemp(suffix=".kee")
        os.close(fd)
        return path

    def test_mono_round_trip(self):
        path = self._make_temp_kee()
        try:
            samples = np.random.uniform(-1, 1, 1000).astype(np.float64)
            meta = CodecMetadata(
                fs_original=44100, fs_new=22050, downsample_factor=2,
                channels=1, duration=1.0, n_samples_original=2000,
            )
            write_kee(path, meta, samples)
            meta_r, samples_r = read_kee(path)

            assert meta_r.fs_original == 44100
            assert meta_r.downsample_factor == 2
            assert samples_r.shape == (1000,)
            # int16 quantization tolerance
            np.testing.assert_allclose(samples_r, samples, atol=1.0 / 32767)
        finally:
            os.remove(path)

    def test_stereo_round_trip(self):
        path = self._make_temp_kee()
        try:
            samples = np.random.uniform(-1, 1, (500, 2)).astype(np.float64)
            meta = CodecMetadata(
                fs_original=48000, fs_new=12000, downsample_factor=4,
                channels=2, duration=0.5, n_samples_original=2000,
            )
            write_kee(path, meta, samples)
            meta_r, samples_r = read_kee(path)

            assert meta_r.channels == 2
            assert samples_r.shape == (500, 2)
            np.testing.assert_allclose(samples_r, samples, atol=1.0 / 32767)
        finally:
            os.remove(path)

    def test_bad_magic_rejected(self):
        path = self._make_temp_kee()
        try:
            with open(path, "wb") as f:
                f.write(b"BADM")
            with pytest.raises(ValueError, match="Not a valid .kee file"):
                read_kee(path)
        finally:
            os.remove(path)
