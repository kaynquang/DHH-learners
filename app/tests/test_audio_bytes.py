"""Load recordings from bytes without the D1 sample set.

Streamlit's mic widget hands over WAV bytes, which used to fail on Windows
because Praat could not open a still-locked NamedTemporaryFile.
"""
import numpy as np
import parselmouth
import pytest
from parselmouth.praat import call

from fricative.audio import load


def _wav_bytes(fs=16000) -> bytes:
    t = np.arange(fs) / fs
    snd = parselmouth.Sound(0.2 * np.sin(2 * np.pi * 440 * t), sampling_frequency=fs)
    import tempfile
    from pathlib import Path
    import os

    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    path = Path(tmp)
    try:
        call(snd, "Save as WAV file", str(path))
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


def test_load_wav_bytes_labelled_recording():
    data = _wav_bytes()
    assert data[:4] == b"RIFF"
    snd = load(data, "recording.wav")
    assert snd.n_channels == 1
    assert snd.sampling_frequency == 16000
    assert snd.xmax - snd.xmin == pytest.approx(1.0, abs=0.02)


def test_garbage_bytes_raise_value_error():
    with pytest.raises(ValueError, match="wav or mp3"):
        load(b"this is not audio at all", "recording.wav")
