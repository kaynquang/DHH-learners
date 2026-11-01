import numpy as np
import parselmouth
import pytest
from parselmouth.praat import call

from fricative.audio import load
from fricative.reference import load_reference
from fricative.segment import SegmentationError, estimate_snr, find_boundaries

D1 = load_reference()


@pytest.mark.parametrize("row", D1, ids=[r.file for r in D1])
def test_d1_boundaries_within_20_ms_of_manual(row):
    b = find_boundaries(load(row.path))
    assert b.found_vowel
    assert abs(b.onset_s - row.start_s) < 0.020
    assert abs(b.offset_s - row.end_s) < 0.020


@pytest.mark.parametrize("name,start", [("See - UK.mp3", 0.031050), ("She - US.mp3", 0.033422)])
def test_long_leading_silence_with_room_noise(name, start):
    snd = load(load_reference()[0].path.parent / name)
    x, fs = snd.values[0], snd.sampling_frequency
    rms = np.sqrt(np.mean(x ** 2))
    y = np.concatenate([np.zeros(int(0.5 * fs)), x])
    y = y + np.random.default_rng(0).normal(0, rms * 10 ** (-40 / 20), len(y))
    b = find_boundaries(parselmouth.Sound(y, sampling_frequency=fs))
    assert abs(b.onset_s - (0.5 + start)) < 0.020


def test_no_vowel_falls_back_to_end_of_hiss():
    see = load_reference()[0]
    snd = call(load(see.path), "Extract part", 0, see.end_s, "rectangular", 1, "no")
    b = find_boundaries(snd)
    assert not b.found_vowel
    assert abs(b.offset_s - see.end_s) < 0.020


def test_silence_raises():
    with pytest.raises(SegmentationError, match="No frication"):
        find_boundaries(parselmouth.Sound(np.zeros(48000), sampling_frequency=48000))


def test_steady_tone_raises():
    t = np.arange(48000) / 48000
    with pytest.raises(SegmentationError):
        find_boundaries(parselmouth.Sound(0.3 * np.sin(2 * np.pi * 1000 * t), sampling_frequency=48000))


def test_tiny_clip_raises():
    with pytest.raises(SegmentationError, match="too short"):
        find_boundaries(parselmouth.Sound(np.zeros(100), sampling_frequency=48000))


def test_snr_drops_when_noise_added():
    snd = load(load_reference()[0].path)
    x = snd.values[0]
    noisy = x + np.random.default_rng(1).normal(0, np.sqrt(np.mean(x ** 2)) * 0.1, len(x))
    clean_snr = estimate_snr(snd)
    noisy_snr = estimate_snr(parselmouth.Sound(noisy, sampling_frequency=snd.sampling_frequency))
    assert clean_snr > 35
    assert noisy_snr < clean_snr - 10


def _see_uk_after_silence():
    """See - UK after 1 s of silence with room noise at -40 dB. Returns (samples, fs, manual onset, manual offset, rms)."""
    row = load_reference()[0]
    snd = load(row.path)
    x, fs = snd.values[0], snd.sampling_frequency
    rms = np.sqrt(np.mean(x ** 2))
    y = np.concatenate([np.zeros(fs_int(fs)), x])
    y = y + np.random.default_rng(2).normal(0, rms * 10 ** (-40 / 20), len(y))
    return y, fs, 1.0 + row.start_s, 1.0 + row.end_s, rms


def fs_int(fs):
    return int(fs)


def test_click_before_speech_does_not_move_onset():
    y, fs, on, off, rms = _see_uk_after_silence()
    i = int(0.1 * fs)
    y[i:i + int(0.003 * fs)] += 0.5
    b = find_boundaries(parselmouth.Sound(y, sampling_frequency=fs))
    assert abs(b.onset_s - on) < 0.020
    assert abs(b.offset_s - off) < 0.020


def test_breath_before_speech_does_not_move_onset():
    y, fs, on, off, rms = _see_uk_after_silence()
    i, n = int(0.4 * fs), int(0.08 * fs)
    y[i:i + n] += np.random.default_rng(3).normal(0, rms * 10 ** (-20 / 20), n)
    b = find_boundaries(parselmouth.Sound(y, sampling_frequency=fs))
    assert abs(b.onset_s - on) < 0.020
    assert abs(b.offset_s - off) < 0.020


def test_weak_f_without_vowel_keeps_whole_hiss():
    fee = next(r for r in load_reference() if r.file == "Fee - US.mp3")
    snd = call(load(fee.path), "Extract part", 0, fee.end_s, "rectangular", 1, "no")
    b = find_boundaries(snd)
    assert not b.found_vowel
    # The cut file is only 0.2 s long, so the noise floor estimate is rougher; allow 25 ms on onset.
    assert abs(b.onset_s - fee.start_s) < 0.025
    assert abs(b.offset_s - fee.end_s) < 0.020


def test_trace_matches_find_boundaries_and_exposes_steps():
    from fricative.segment import trace_boundaries
    for row in D1:
        snd = load(row.path)
        tr = trace_boundaries(snd)
        assert tr.boundaries == find_boundaries(snd)
        assert tr.error is None
        assert tr.threshold_db == pytest.approx(tr.floor_db + 15)
        assert len(tr.t) == len(tr.hi_db)
        assert tr.runs and tr.voiced_starts
        assert any(a <= tr.boundaries.onset_s + 0.006 and b >= tr.boundaries.offset_s for a, b in tr.runs)


def test_trace_reports_error_instead_of_raising():
    from fricative.segment import trace_boundaries
    tr = trace_boundaries(parselmouth.Sound(np.zeros(48000), sampling_frequency=48000))
    assert tr.boundaries is None
    assert "No frication" in tr.error
