import numpy as np
import parselmouth
import scipy.signal as sg

from fricative import pipeline
from fricative.classify import Verdict
from fricative.measure import measure


def _blown_hiss(fs=48000, dur=1.0):
    """A weak broadband hiss under a strong low rumble, like a /f/ blown into the microphone."""
    rng = np.random.default_rng(2)
    n = int(fs * dur)
    rumble = sg.sosfilt(sg.butter(4, 120, "lowpass", fs=fs, output="sos"), rng.normal(0, 1, n)) * 8.0
    hiss = sg.sosfilt(sg.butter(4, 3000, "highpass", fs=fs, output="sos"), rng.normal(0, 1, n)) * 0.05
    return parselmouth.Sound((rumble + hiss).astype(float), sampling_frequency=fs)


def test_removing_the_rumble_lets_the_hiss_show():
    snd = _blown_hiss()
    raw = measure(snd, 0.1, 0.9, False).cog_hz
    clean = measure(pipeline.without_rumble(snd), 0.1, 0.9, False).cog_hz
    assert raw < 1000 < clean                       # the gate (MIN_HISS_COG_HZ) now sees a hiss


def test_green_is_capped_at_yellow_but_the_rest_is_kept():
    green = Verdict("green", "Correct", "◯", "f", "f", "You said /f/", "tip")
    capped = pipeline.cap_at_yellow(green, "note")
    assert capped.color == "yellow" and capped.heard == "f" and capped.note == "note"
    red = Verdict("red", "Not yet", "✕", "s", "f", "You said /s/", "tip")
    assert pipeline.cap_at_yellow(red, "note") is red
