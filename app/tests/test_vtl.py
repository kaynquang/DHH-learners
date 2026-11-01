import numpy as np
import parselmouth
import scipy.signal as sg

from fricative import vtl


def _vowel(f0, formants, fs=16000, dur=2.0):
    """A synthetic "aaa": a pulse train through resonators at the given formants."""
    x = np.zeros(int(fs * dur))
    x[:: int(fs / f0)] = 1.0
    for f, bw in zip(formants, (80, 100, 120, 200, 250)):
        r, th = np.exp(-np.pi * bw / fs), 2 * np.pi * f / fs
        x = sg.lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)
    return parselmouth.Sound(x / np.max(np.abs(x)) * 0.3, sampling_frequency=fs)


def test_f3_follows_the_size_of_the_voice():
    man = vtl.measure_vowel(_vowel(120, (730, 1090, 2440, 3400, 4300)))
    woman = vtl.measure_vowel(_vowel(200, (850, 1220, 2810, 3800, 4800)))
    child = vtl.measure_vowel(_vowel(300, (1030, 1370, 3170, 4200, 5200)))
    for got, want in ((man, 2440), (woman, 2810), (child, 3170)):
        assert got is not None and abs(got.f3_hz - want) < 0.06 * want
    assert vtl.scale_from(child.f3_hz) > vtl.scale_from(woman.f3_hz) > vtl.scale_from(man.f3_hz)


def test_no_vowel_in_noise():
    noise = parselmouth.Sound(np.random.default_rng(0).normal(0, 0.05, 32000), sampling_frequency=16000)
    assert vtl.measure_vowel(noise) is None


def test_scale_moves_the_thresholds_and_is_limited():
    assert vtl.thresholds(1.0).cog_s_sh_hz == 4340.0
    assert vtl.thresholds(1.2).cog_s_sh_hz > 5200
    assert vtl.scale_from(9000) == vtl.SCALE_MAX and vtl.scale_from(500) == vtl.SCALE_MIN
