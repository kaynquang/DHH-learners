import numpy as np
import parselmouth
import pytest

from fricative.affricate import classify_affricate, measure_affricate, probability_ch
from fricative.segment import SegmentationError


def hiss(rise_ms, length_ms=250, fs=16000):
    """Silence, then high-passed noise that reaches full strength over `rise_ms`."""
    rng = np.random.default_rng(2)
    n = int(0.8 * fs)
    x = rng.normal(0, 1e-4, n)
    a, k = int(0.2 * fs), int(length_ms / 1000 * fs)
    env = np.minimum(np.arange(k) / max(rise_ms / 1000 * fs, 1), 1.0)
    noise = np.diff(rng.normal(0, 0.1, k + 1)) * 2
    x[a:a + k] += env * noise
    return parselmouth.Sound(x, sampling_frequency=fs)


def test_an_abrupt_start_is_more_affricate_than_a_slow_one():
    abrupt, slow = measure_affricate(hiss(10)), measure_affricate(hiss(120))
    assert abrupt.rise_ms < slow.rise_ms
    assert probability_ch(abrupt) > probability_ch(slow)


def test_silence_has_no_hiss():
    with pytest.raises(SegmentationError):
        measure_affricate(parselmouth.Sound(np.zeros(16000), sampling_frequency=16000))


@pytest.mark.parametrize("p,color", [(0.95, "green"), (0.65, "yellow"), (0.2, "red")])
def test_verdict_colours(p, color):
    assert classify_affricate(p).color == color
