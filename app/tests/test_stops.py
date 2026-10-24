import numpy as np
import parselmouth
import pytest

from fricative.segment import SegmentationError
from fricative.stops import StopMeasure, classify_stop, heard_stop, measure_vot


def word(vot_ms, fs=16000, burst_at=0.20):
    """Silence, a noise burst plus aspiration of `vot_ms`, then a voiced vowel (harmonics of 120 Hz)."""
    rng = np.random.default_rng(1)
    n = int(0.6 * fs)
    x = rng.normal(0, 1e-4, n)
    a, v = int(burst_at * fs), int((burst_at + vot_ms / 1000) * fs)
    x[a:v + int(0.004 * fs)] += rng.normal(0, 0.05, v + int(0.004 * fs) - a)
    t = np.arange(n - v) / fs
    x[v:] += sum(0.1 / k * np.sin(2 * np.pi * 120 * k * t) for k in range(1, 12))
    return parselmouth.Sound(x, sampling_frequency=fs)


@pytest.mark.parametrize("vot", [10, 25, 60, 80])
def test_vot_is_the_gap_between_burst_and_voicing(vot):
    m = measure_vot(word(vot))
    assert abs(m.burst_s - 0.20) < 0.010
    assert abs(m.vot_ms - vot) < 15


def test_silence_has_no_burst():
    with pytest.raises(SegmentationError):
        measure_vot(parselmouth.Sound(np.zeros(16000), sampling_frequency=16000))


@pytest.mark.parametrize("vot,heard", [(10, "b"), (29, "b"), (30, "p"), (70, "p")])
def test_threshold_between_b_and_p(vot, heard):
    assert heard_stop(vot) == heard


@pytest.mark.parametrize("vot,target,color", [(70, "p", "green"), (35, "p", "yellow"), (10, "p", "red"),
                                              (8, "b", "green"), (25, "b", "yellow"), (70, "b", "red")])
def test_verdict_colours(vot, target, color):
    assert classify_stop(StopMeasure(0.2, 0.2 + vot / 1000, vot), target).color == color


def test_a_long_hiss_is_not_scored_as_a_stop():
    from fricative.audio import load
    from fricative.reference import load_reference
    for row in load_reference():
        with pytest.raises(SegmentationError, match="long hiss"):
            measure_vot(load(row.path))


@pytest.mark.parametrize("p_p,target,color", [(0.95, "p", "green"), (0.6, "p", "yellow"), (0.2, "p", "red"), (0.05, "b", "green"), (0.7, "b", "red")])
def test_probe_verdict_colours(p_p, target, color):
    from fricative.stops import classify_stop_probe
    assert classify_stop_probe(p_p, target).color == color
