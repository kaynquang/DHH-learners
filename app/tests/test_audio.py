import numpy as np
import parselmouth
import pytest
from parselmouth.praat import call

from fricative.audio import limit_duration, load
from fricative.reference import SOUNDS_DIR


def test_load_mp3_path_is_mono_48k():
    snd = load(SOUNDS_DIR / "See - UK.mp3")
    assert snd.n_channels == 1
    assert snd.sampling_frequency == 48000
    assert 0.6 < snd.xmax - snd.xmin < 0.75


def test_load_wav_bytes_without_name(tmp_path):
    src = load(SOUNDS_DIR / "She - US.mp3")
    wav = tmp_path / "x.wav"
    call(src, "Save as WAV file", str(wav))
    snd = load(wav.read_bytes())
    assert snd.n_channels == 1
    assert snd.xmax == pytest.approx(src.xmax, abs=0.001)


def test_stereo_44k_recording_becomes_mono(tmp_path):
    t = np.arange(44100) / 44100
    x = 0.2 * np.sin(2 * np.pi * 440 * t)
    stereo = parselmouth.Sound(np.vstack([x, 0.5 * x]), sampling_frequency=44100)
    wav = tmp_path / "rec.wav"
    call(stereo, "Save as WAV file", str(wav))
    snd = load(wav.read_bytes(), "recording.wav")
    assert snd.n_channels == 1
    assert snd.sampling_frequency == 44100


def test_garbage_bytes_raise_value_error():
    with pytest.raises(ValueError, match="wav or mp3"):
        load(b"this is not audio at all", "note.wav")


def test_limit_duration_cuts_to_five_seconds():
    long = parselmouth.Sound(np.zeros(6 * 16000), sampling_frequency=16000)
    cut, truncated = limit_duration(long)
    assert truncated
    assert cut.xmax - cut.xmin == pytest.approx(5.0, abs=0.001)
    short = parselmouth.Sound(np.zeros(16000), sampling_frequency=16000)
    same, truncated = limit_duration(short)
    assert not truncated and same is short
