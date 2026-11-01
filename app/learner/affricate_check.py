"""/tʃ/ ("ch") in a recorded word: does it start with a pop, and does the hiss last long enough?

From CMU ARCTIC (bdl, slt; app/METHOD_NOTES.md 8c.v) the cues that separate /tʃ/ from its neighbours, on the 2.5-7.9 kHz band, are
  - against /ʃ/ ("sh"): how steeply the hiss climbs at its start (dB per ms): /tʃ/ bursts in, /ʃ/ fades in;
  - against /t/: how long the hiss lasts: a /tʃ/ hiss is about 100 ms, a /t/ release about 35 ms.
The 10-90 % rise time and the centre of gravity did not separate /tʃ/ from /ʃ/, so they are not used. The limits below come from the ARCTIC tokens that start after a pause (explore/pattern_lab/arctic_isolated.py, few of them: no /tʃ/ at all, 24 /ʃ/ and 14 /t/ of one voice) and from the running-speech /tʃ/; they are for adult voices and are a
first guess for children. The measures are those of the first hiss of the recording: the closing /t/ of "cheat" comes after the vowel.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, resample_poly, sosfilt

FS = 16000
SOS = butter(4, [2500, 7900], btype="band", fs=FS, output="sos")
WIN, HOP = int(0.005 * FS), int(0.001 * FS)          # a 5 ms envelope, one value per ms
STRONG_DB = 30.0             # the hiss starts where the band is within this many dB of its loudest point of the whole recording
END_DB = 15.0                # the hiss ends when it has fallen this far below its peak
SLOPE_OK_DB_MS = 10.0        # the hiss starts at least this steeply: a pop. Words that start after a pause in ARCTIC (slt): /ʃ/ 2.5 dB/ms (IQR 2.0-2.8, n = 24), /t/ 28 (n = 14); /tʃ/ in running speech 8.6-24.6
SLOPE_ALMOST_DB_MS = 5.0
HISS_OK_MS = 85.0            # a hiss at least this long is not a /t/ (ARCTIC words that start after a pause: /t/ 69 ms, IQR 63-78, n = 14; /tʃ/ in running speech 95-108 ms)
HISS_ALMOST_MS = 70.0


@dataclass(frozen=True)
class Check:
    slope_db_ms: float
    hiss_ms: float
    pop: str                 # "green" | "yellow" | "red"
    hiss: str


def _level(value: float, ok: float, almost: float) -> str:
    return "green" if value >= ok else "yellow" if value >= almost else "red"


def measure(x: np.ndarray, fs: float) -> tuple[float, float] | None:
    """(steepest climb in dB per ms, hiss length in ms) of the first hiss in x, or None when there is none."""
    if int(fs) != FS:
        from math import gcd
        g = gcd(int(fs), FS)
        x = resample_poly(x, FS // g, int(fs) // g)
    y = sosfilt(SOS, np.asarray(x, dtype=float))
    if len(y) < 4 * WIN:
        return None
    amp = np.sqrt(np.convolve(y ** 2, np.ones(WIN) / WIN, mode="valid")[::HOP])
    db = 20 * np.log10(amp + 1e-9)
    if db.max() < -90:                                         # nothing in the band at all
        return None
    above = np.flatnonzero(db > db.max() - STRONG_DB)      # the first strong stretch, however the recorder fades its noise in before it (seen in the saved recordings of 26 Oct)
    if not len(above):
        return None
    first = int(above[0])
    peak_i = first + int(np.argmax(db[first:first + 250]))                      # the peak of this first stretch of hiss (within 250 ms)
    peak = amp[peak_i]
    begin = first + int(np.argmax(amp[first:peak_i + 1] >= 0.1 * peak))
    after = np.flatnonzero(amp[peak_i:] < 10 ** (-END_DB / 20) * peak)           # the hiss ends when it has fallen END_DB below its peak (the vowel's own energy in this band stays above 20 dB below)
    end = peak_i + (int(after[0]) if len(after) else len(amp) - 1 - peak_i)
    rise = np.diff(db[max(0, begin - 2):peak_i + 1])
    slope = float(np.max(rise)) if len(rise) else 0.0
    return slope, float(end - begin + 1)


def check(sound) -> Check | None:
    """The check of a parselmouth Sound (the learner's recording)."""
    m = measure(np.asarray(sound.values)[0], sound.sampling_frequency)
    if m is None:
        return None
    slope, hiss = m
    return Check(slope, hiss, _level(slope, SLOPE_OK_DB_MS, SLOPE_ALMOST_DB_MS), _level(hiss, HISS_OK_MS, HISS_ALMOST_MS))
