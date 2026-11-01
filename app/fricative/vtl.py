"""Voice size from a long vowel: a scale factor for the frequency thresholds, without asking the child to say the target sounds right.

Why a vowel: for a learner who is deaf or hard of hearing the sounds being taught (/s/ /ʃ/ /f/) are the ones that may not be right yet, so
they cannot be the reference. A long "aaa" says how big the voice is (the third formant F3 is higher when the vocal tract is shorter) and
is easy for any child to produce. The thresholds in config.py come from adult voices; scaling them by F3 / reference F3 is a vocal tract
length normalisation. PROVISIONAL: the link between F3 and where a child's /s/ lies is an assumption, supported only by the adult data
(CMU ARCTIC: the middle between the /s/ and /ʃ/ medians is 4770 Hz for the male voice and 5350 Hz for the female voice, a ratio of 1.12, close
to the F3 ratio of the two voices), and has to be checked on children's recordings.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from parselmouth.praat import call

from . import config as C

REF_F3_HZ = 2625.0           # the middle of adult male (about 2440 Hz) and female (about 2810 Hz) F3 in /a/ (Peterson and Barney 1952, from memory)
SCALE_MIN, SCALE_MAX = 0.85, 1.5
F3_RANGE_HZ = (1800.0, 4500.0)
MIN_VOICED_FRAMES = 15       # 10 ms frames


@dataclass(frozen=True)
class Vowel:
    f3_hz: float
    voiced_s: float          # seconds of steady voiced sound the measure rests on


def measure_vowel(sound) -> Vowel | None:
    """F3 of the steady, voiced, loudest part of a recording of a long vowel; None when there is no voiced vowel to measure."""
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=100, pitch_ceiling=600)
    median_f0 = call(pitch, "Get quantile", 0, 0, 0.5, "Hertz")
    if not np.isfinite(median_f0):
        return None
    # the formant ceiling has to follow the voice (Praat's own advice: lower for low voices, higher for children); on synthetic vowels with the
    # right F3 a ceiling that is too low for a child's voice gave an F3 600 to 800 Hz too low
    ceiling = 5000.0 if median_f0 < 160 else 5500.0 if median_f0 < 260 else 7000.0
    formant = sound.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=ceiling, window_length=0.03, pre_emphasis_from=50.0)
    intensity = sound.to_intensity(minimum_pitch=100.0, time_step=0.01)
    times = np.arange(max(sound.xmin, 0.05), sound.xmax - 0.05, 0.01)
    rows = []
    for t in times:
        f0 = call(pitch, "Get value at time", t, "Hertz", "linear")
        f3 = call(formant, "Get value at time", 3, t, "Hertz", "linear")
        db = call(intensity, "Get value at time", t, "cubic")
        if np.isfinite(f0) and np.isfinite(f3) and np.isfinite(db):
            rows.append((db, f3))
    if len(rows) < MIN_VOICED_FRAMES:
        return None
    rows.sort(reverse=True)
    loud = [f3 for _, f3 in rows[: max(MIN_VOICED_FRAMES, len(rows) // 2)]]          # the louder half: the held part, not the start and the end
    f3 = float(np.median(loud))
    if not F3_RANGE_HZ[0] <= f3 <= F3_RANGE_HZ[1]:
        return None
    return Vowel(f3, len(loud) * 0.01)


def scale_from(f3_hz: float) -> float:
    return float(min(SCALE_MAX, max(SCALE_MIN, f3_hz / REF_F3_HZ)))


def thresholds(scale: float = 1.0) -> C.Thresholds:
    """The /s/-/ʃ/ boundary and its margin moved to this voice (1.0 gives the defaults)."""
    d = C.DEFAULT_THRESHOLDS
    return replace(d, cog_s_sh_hz=d.cog_s_sh_hz * scale, cog_margin_hz=d.cog_margin_hz * scale)
