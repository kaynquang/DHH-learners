import pytest
from parselmouth.praat import call

from fricative.audio import load
from fricative.measure import analysis_window, measure, spectrum_db
from fricative.reference import load_reference

D1 = load_reference()


def test_analysis_window_is_middle_half():
    assert analysis_window(0.1, 0.3) == pytest.approx((0.15, 0.25))


@pytest.mark.parametrize("row", D1, ids=[r.file for r in D1])
def test_cog_matches_manual_praat_within_5_hz(row):
    m = measure(load(row.path), row.start_s, row.end_s)
    assert abs(m.cog_hz - row.manual_cog_hz) < 5


def test_relative_amplitude_separates_f_from_sibilants():
    by_phone = {}
    for r in D1:
        by_phone.setdefault(r.phone, []).append(measure(load(r.path), r.start_s, r.end_s).relamp_db)
    assert all(v < -20 for v in by_phone["f"])
    assert all(-10 < v < 0 for v in by_phone["s"] + by_phone["sh"])


def test_fm_inside_search_band_and_duration():
    r = D1[0]
    m = measure(load(r.path), r.start_s, r.end_s)
    assert 2000 <= m.fm_hz <= 8000
    assert m.duration_ms == pytest.approx((r.end_s - r.start_s) * 1000)


def test_no_vowel_gives_no_relative_amplitude():
    r = D1[0]
    snd = load(r.path)
    assert measure(snd, r.start_s, r.end_s, has_vowel=False).relamp_db is None
    cut = call(snd, "Extract part", 0, r.end_s + 0.005, "rectangular", 1, "no")
    assert measure(cut, r.start_s, r.end_s).relamp_db is None


def test_resampled_44k_keeps_cog_close():
    r = D1[1]
    m48 = measure(load(r.path), r.start_s, r.end_s)
    m44 = measure(load(r.path).resample(44100, 50), r.start_s, r.end_s)
    assert abs(m44.cog_hz - m48.cog_hz) < 50


def test_offset_before_onset_raises():
    with pytest.raises(ValueError):
        measure(load(D1[0].path), 0.2, 0.1)


def test_spectrum_db_shapes():
    f, db = spectrum_db(load(D1[0].path), 0.08, 0.17, fmax=16000)
    assert f.shape == db.shape
    assert f.max() <= 16000


def test_digital_silence_gives_no_relative_amplitude_instead_of_crashing():
    import numpy as np
    import parselmouth
    zeros = parselmouth.Sound(np.zeros(48000), sampling_frequency=48000)
    m = measure(zeros, 0.0, 0.3)
    assert m.relamp_db is None
