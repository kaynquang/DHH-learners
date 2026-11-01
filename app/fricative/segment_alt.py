"""Alternative frication detectors, kept for ablation studies.

All share the frame grid of `segment` (10 ms Hanning window, 2 ms hop). Only
`anchored` (= `segment.find_boundaries`) is used for scoring; the others reproduce
the methods compared in the D1 spike so their behaviour can be inspected.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import parselmouth

from . import config as C
from .segment import Boundaries, SegmentationError, find_boundaries

ZCR_MIN_PER_S = 2500.0
FRAME_COG_MIN_HZ = 2500.0
LOW_BAND_HZ = (80.0, 1000.0)


@dataclass(frozen=True)
class Method:
    name: str
    summary: str
    run: Callable[[parselmouth.Sound], Boundaries]


def frame_features(sound: parselmouth.Sound) -> dict[str, np.ndarray]:
    """Per-frame features: time, high/low/total band energy (dB), zero-crossing rate, CoG."""
    x = sound.values[0]
    fs = sound.sampling_frequency
    n = int(C.FRAME_WIN_S * fs)
    h = int(C.FRAME_HOP_S * fs)
    if len(x) < n + h:
        raise SegmentationError("Recording too short")
    starts = np.arange(0, len(x) - n, h)
    raw = np.stack([x[s:s + n] for s in starts])
    power = np.abs(np.fft.rfft(raw * np.hanning(n), axis=1)) ** 2 + 1e-12
    f = np.fft.rfftfreq(n, 1 / fs)
    hi = (f >= C.HI_BAND_HZ[0]) & (f <= C.HI_BAND_HZ[1])
    lo = (f >= LOW_BAND_HZ[0]) & (f <= LOW_BAND_HZ[1])
    return {
        "t": sound.xmin + (starts + n / 2) / fs,
        "hi_db": 10 * np.log10(power[:, hi].sum(axis=1)),
        "lo_db": 10 * np.log10(power[:, lo].sum(axis=1)),
        "tot_db": 10 * np.log10(power.sum(axis=1)),
        "zcr": np.mean(np.abs(np.diff(np.sign(raw), axis=1)) > 0, axis=1) * fs,
        "cog": (power * f).sum(axis=1) / power.sum(axis=1),
    }


def _first_onset(F: dict[str, np.ndarray]) -> int:
    above = F["hi_db"] > np.percentile(F["hi_db"], 5) + C.ONSET_DB_ABOVE_FLOOR
    if not above.any():
        raise SegmentationError("No frication found")
    return int(np.argmax(above))


def _checked(onset: float, offset: float, found_vowel: bool) -> Boundaries:
    if offset - onset < C.MIN_FRICATION_S:
        raise SegmentationError("Frication too short (< 30 ms)")
    return Boundaries(onset, offset, found_vowel)


def energy_pitch_v1(sound: parselmouth.Sound) -> Boundaries:
    """Spike v1: first frame above the high-band floor + 15 dB; first voiced frame after it."""
    F = frame_features(sound)
    i = _first_onset(F)
    onset = max(sound.xmin, float(F["t"][i] - C.FRAME_WIN_S / 2))
    pitch = sound.to_pitch(time_step=C.FRAME_HOP_S, pitch_floor=C.PITCH_FLOOR_HZ, pitch_ceiling=C.PITCH_CEILING_HZ)
    ts, f0 = pitch.xs(), pitch.selected_array["frequency"]
    voiced = ts[(f0 > 0) & (ts > onset + C.VOICING_SEARCH_DELAY_S)]
    if len(voiced):
        return _checked(onset, float(voiced[0]), True)
    return _checked(onset, float(sound.xmax), False)


def band_ratio(sound: parselmouth.Sound) -> Boundaries:
    """Onset as v1; offset where the low band (80-1000 Hz) first becomes louder than the high band."""
    F = frame_features(sound)
    i = _first_onset(F)
    t = F["t"]
    after = np.where((F["lo_db"] > F["hi_db"]) & (np.arange(len(t)) > i))[0]
    j = int(after[0]) if len(after) else len(t) - 1
    return _checked(max(sound.xmin, float(t[i] - C.FRAME_WIN_S / 2)), float(t[j] - C.FRAME_WIN_S / 2), len(after) > 0)


def _longest_run(mask: np.ndarray) -> tuple[int, int]:
    best, i, n = (0, 0), 0, len(mask)
    while i < n:
        if mask[i]:
            a = i
            while i < n and mask[i]:
                i += 1
            if i - a > best[1] - best[0]:
                best = (a, i)
        else:
            i += 1
    return best


def _run_detector(sound: parselmouth.Sound, feature: str, minimum: float) -> Boundaries:
    F = frame_features(sound)
    loud = F["tot_db"] > np.percentile(F["tot_db"], 5) + C.ONSET_DB_ABOVE_FLOOR
    a, b = _longest_run(loud & (F[feature] > minimum))
    if b == a:
        raise SegmentationError("No frication found")
    t = F["t"]
    offset = float(t[b - 1] + C.FRAME_WIN_S / 2)
    has_audio_after = sound.xmax - offset >= C.VOWEL_GAP_S + 0.02
    return _checked(max(sound.xmin, float(t[a] - C.FRAME_WIN_S / 2)), offset, has_audio_after)


def zcr(sound: parselmouth.Sound) -> Boundaries:
    """Longest run of loud frames whose zero-crossing rate exceeds 2,500 per second."""
    return _run_detector(sound, "zcr", ZCR_MIN_PER_S)


def frame_cog(sound: parselmouth.Sound) -> Boundaries:
    """Longest run of loud frames whose own CoG exceeds 2,500 Hz."""
    return _run_detector(sound, "cog", FRAME_COG_MIN_HZ)


METHODS: dict[str, Method] = {
    "anchored": Method(
        "Anchored energy + pitch (current)",
        "High-band run that leads into the first voiced stretch; clicks and breaths are skipped.",
        find_boundaries,
    ),
    "energy_pitch_v1": Method(
        "Energy + pitch (spike v1)",
        "First frame above the high-band floor + 15 dB; offset at the first voiced frame.",
        energy_pitch_v1,
    ),
    "band_ratio": Method(
        "High / low band ratio",
        "Onset as v1; offset where 80-1000 Hz energy overtakes 2.5-12 kHz energy.",
        band_ratio,
    ),
    "zcr": Method(
        "ZCR + intensity",
        "Longest run of loud frames with more than 2,500 zero crossings per second.",
        zcr,
    ),
    "frame_cog": Method(
        "Frame-wise CoG",
        "Longest run of loud frames whose own centre of gravity is above 2,500 Hz.",
        frame_cog,
    ),
}
