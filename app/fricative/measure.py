"""Measurements on the middle 50% of the frication. CoG matches the manual Praat method."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import parselmouth
from nitime.algorithms import multi_taper_psd
from parselmouth.praat import call

from . import config as C


@dataclass(frozen=True)
class Measures:
    onset_s: float
    offset_s: float
    cog_hz: float
    relamp_db: float | None
    fm_hz: float
    duration_ms: float


def analysis_window(onset_s: float, offset_s: float) -> tuple[float, float]:
    d = offset_s - onset_s
    return onset_s + d / 4, offset_s - d / 4


def _part(sound: parselmouth.Sound, a: float, b: float) -> parselmouth.Sound:
    return call(sound, "Extract part", a, b, "rectangular", 1, "no")


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)))


def spectrum_db(sound: parselmouth.Sound, a: float, b: float, fmax: float = 16000.0) -> tuple[np.ndarray, np.ndarray]:
    """Multitaper spectrum (NW = 4) of [a, b]: (frequency in Hz, dB)."""
    part = _part(sound, a, b)
    f, psd, _ = multi_taper_psd(part.values[0], Fs=part.sampling_frequency, NW=4, adaptive=False, jackknife=False)
    keep = f <= fmax
    return f[keep], 10 * np.log10(psd[keep] + 1e-20)


def measure(sound: parselmouth.Sound, onset_s: float, offset_s: float, has_vowel: bool = True) -> Measures:
    if offset_s <= onset_s:
        raise ValueError("offset must be greater than onset")
    a, b = analysis_window(onset_s, offset_s)
    part = _part(sound, a, b)
    cog = call(part.to_spectrum(), "Get centre of gravity", 2.0)

    relamp = None
    v_a, v_b = offset_s + C.VOWEL_GAP_S, min(offset_s + C.VOWEL_GAP_S + C.VOWEL_LEN_S, sound.xmax)
    if has_vowel and v_b - v_a >= 0.02:
        hiss_rms, vowel_rms = _rms(part.values[0]), _rms(_part(sound, v_a, v_b).values[0])
        if hiss_rms > 1e-10 and vowel_rms > 1e-10:
            relamp = 20 * np.log10(hiss_rms / vowel_rms)

    f, db = spectrum_db(sound, a, b)
    band = (f >= C.FM_BAND_HZ[0]) & (f <= C.FM_BAND_HZ[1])
    fm = float(f[band][np.argmax(db[band])])

    return Measures(onset_s, offset_s, float(cog), None if relamp is None else float(relamp), fm, (offset_s - onset_s) * 1000)
