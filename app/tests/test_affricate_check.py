import numpy as np
import parselmouth
from scipy.signal import butter, sosfilt

from learner import affricate_check as A, result

FS = 16000


def _word(rise_ms: float, hiss_ms: float):
    """0.4 s of room, a high-band hiss of the given rise and length, a quiet vowel-like tone, 0.3 s of room."""
    rng = np.random.default_rng(3)
    n = int(hiss_ms / 1000 * FS)
    hiss = sosfilt(butter(4, [3000, 7000], "bandpass", fs=FS, output="sos"), rng.normal(0, 1, n))
    env = np.ones(n)
    r = max(1, int(rise_ms / 1000 * FS))
    env[:r] = np.linspace(0, 1, r) ** 1.0
    env[-int(0.02 * FS):] *= np.linspace(1, 0, int(0.02 * FS))
    tone = 0.02 * np.sin(2 * np.pi * 220 * np.arange(int(0.4 * FS)) / FS)
    x = np.concatenate([rng.normal(0, 1e-4, int(0.4 * FS)), 0.2 * hiss * env, tone, rng.normal(0, 1e-4, int(0.3 * FS))])
    return parselmouth.Sound(x, sampling_frequency=FS)


def test_a_sudden_start_is_a_pop_and_a_slow_one_is_not():
    pop, fade = A.check(_word(2, 100)), A.check(_word(80, 100))
    assert pop.pop == "green" and fade.pop == "red"
    assert pop.slope_db_ms > A.SLOPE_OK_DB_MS > A.SLOPE_ALMOST_DB_MS > fade.slope_db_ms


def test_a_short_release_is_not_a_long_hiss():
    long_, short = A.check(_word(2, 110)), A.check(_word(2, 35))
    assert long_.hiss == "green" and short.hiss == "red"


def test_nothing_to_measure_in_silence():
    assert A.check(parselmouth.Sound(np.zeros(FS), sampling_frequency=FS)) is None


def test_the_lamps_show_for_ch_only():
    c = A.check(_word(2, 110))
    html = result.lamps_html(c)
    assert ">t<" in html and ">sh<" in html and "dB/ms" in html
    assert result.lamps_html(None) == ""
