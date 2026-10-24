import numpy as np
import parselmouth
import pytest

from fricative.audio import load
from fricative.reference import load_reference
from fricative.segment import Boundaries, SegmentationError, find_boundaries
from fricative.segment_alt import METHODS

D1 = {r.file: r for r in load_reference()}


def test_registry_lists_five_methods_with_current_first():
    keys = list(METHODS)
    assert keys == ["anchored", "energy_pitch_v1", "band_ratio", "zcr", "frame_cog"]
    assert METHODS["anchored"].run is find_boundaries
    for m in METHODS.values():
        assert m.name and m.summary


KNOWN_FAILURES = {("band_ratio", "See - US.mp3")}


@pytest.mark.parametrize("key", list(METHODS))
@pytest.mark.parametrize("file", list(D1))
def test_every_method_returns_ordered_boundaries_on_d1(key, file):
    if (key, file) in KNOWN_FAILURES:
        pytest.skip("covered by the known-failure test")
    b = METHODS[key].run(load(D1[file].path))
    assert isinstance(b, Boundaries)
    assert 0 <= b.onset_s < b.offset_s


@pytest.mark.parametrize("key", list(METHODS))
def test_every_method_rejects_silence(key):
    with pytest.raises(SegmentationError):
        METHODS[key].run(parselmouth.Sound(np.zeros(48000), sampling_frequency=48000))


def test_energy_pitch_v1_is_close_to_manual():
    for r in D1.values():
        b = METHODS["energy_pitch_v1"].run(load(r.path))
        assert abs(b.onset_s - r.start_s) < 0.020 and abs(b.offset_s - r.end_s) < 0.020


def test_band_ratio_collapses_on_see_us():
    """Low band overtakes high band right after onset, so the segment is empty (spike: offset -265 ms)."""
    with pytest.raises(SegmentationError, match="too short"):
        METHODS["band_ratio"].run(load(D1["See - US.mp3"].path))


@pytest.mark.parametrize("key", ["zcr", "frame_cog"])
def test_zcr_and_frame_cog_start_late_on_fee_us(key):
    r = D1["Fee - US.mp3"]
    b = METHODS[key].run(load(r.path))
    assert b.onset_s - r.start_s > 0.025


@pytest.mark.parametrize("key", ["zcr", "frame_cog"])
def test_run_detectors_report_a_vowel_when_audio_follows(key):
    """Their offset lands at the vowel, so relative amplitude must still be measurable."""
    b = METHODS[key].run(load(D1["Fee - UK.mp3"].path))
    assert b.found_vowel
