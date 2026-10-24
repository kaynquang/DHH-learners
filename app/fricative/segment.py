"""Frication detection: onset from high-band energy, offset from voicing onset."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import parselmouth

from . import config as C


class SegmentationError(Exception):
    """No usable frication segment was found."""


@dataclass(frozen=True)
class Boundaries:
    onset_s: float
    offset_s: float
    found_vowel: bool


def frame_energies(sound: parselmouth.Sound) -> dict[str, np.ndarray]:
    """Per-frame energy in dB: 't' frame centre, 'hi_db' high band, 'tot_db' full band."""
    x = sound.values[0]
    fs = sound.sampling_frequency
    n = int(C.FRAME_WIN_S * fs)
    h = int(C.FRAME_HOP_S * fs)
    if len(x) < n + h:
        raise SegmentationError("Recording too short")
    starts = np.arange(0, len(x) - n, h)
    frames = np.stack([x[s:s + n] for s in starts]) * np.hanning(n)
    power = np.abs(np.fft.rfft(frames, axis=1)) ** 2 + 1e-12
    f = np.fft.rfftfreq(n, 1 / fs)
    band = (f >= C.HI_BAND_HZ[0]) & (f <= C.HI_BAND_HZ[1])
    return {
        "t": sound.xmin + (starts + n / 2) / fs,
        "hi_db": 10 * np.log10(power[:, band].sum(axis=1)),
        "tot_db": 10 * np.log10(power.sum(axis=1)),
    }


def estimate_snr(sound: parselmouth.Sound) -> float:
    """Estimated SNR in dB: 95th minus 5th percentile of frame energy."""
    tot = frame_energies(sound)["tot_db"]
    return float(np.percentile(tot, 95) - np.percentile(tot, 5))


def _runs(mask: np.ndarray, bridge: int) -> list[tuple[int, int]]:
    """Runs of True as [a, b) after bridging False gaps of at most `bridge` frames."""
    runs: list[tuple[int, int]] = []
    i, n = 0, len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        a = i
        while i < n and mask[i]:
            i += 1
        if runs and a - runs[-1][1] <= bridge:
            runs[-1] = (runs[-1][0], i)
        else:
            runs.append((a, i))
    return runs


def _voiced_starts(sound: parselmouth.Sound) -> list[float]:
    """Start times of voiced stretches lasting at least MIN_VOICED_S."""
    pitch = sound.to_pitch(
        time_step=C.FRAME_HOP_S, pitch_floor=C.PITCH_FLOOR_HZ, pitch_ceiling=C.PITCH_CEILING_HZ
    )
    ts = pitch.xs()
    voiced = pitch.selected_array["frequency"] > 0
    min_len = int(round(C.MIN_VOICED_S / C.FRAME_HOP_S))
    return [float(ts[a]) for a, b in _runs(voiced, 0) if b - a >= min_len]


@dataclass(frozen=True)
class Trace:
    """Every intermediate step of `find_boundaries`, for explanation and plotting."""
    t: np.ndarray
    hi_db: np.ndarray
    floor_db: float
    threshold_db: float
    runs: list[tuple[float, float]]
    voiced_starts: list[float]
    boundaries: Boundaries | None
    error: str | None


def trace_boundaries(sound: parselmouth.Sound) -> Trace:
    """Run the detector and keep its intermediate steps. Never raises SegmentationError."""
    F = frame_energies(sound)
    t, hi = F["t"], F["hi_db"]
    floor = float(np.percentile(hi, 5))
    threshold = floor + C.ONSET_DB_ABOVE_FLOOR
    idx_runs = _runs(hi > threshold, int(round(C.GAP_BRIDGE_S / C.FRAME_HOP_S)))

    def start_of(a: int) -> float:
        return max(sound.xmin, float(t[a] - C.FRAME_WIN_S / 2))

    def end_of(b: int) -> float:
        return float(t[b - 1] + C.FRAME_WIN_S / 2)

    runs = [(start_of(a), end_of(b)) for a, b in idx_runs]
    voiced = _voiced_starts(sound)
    boundaries, error = None, None
    if not runs:
        error = "No frication found"
    else:
        for v in voiced:
            hit = next(((a, b) for a, b in runs if a <= v - C.MIN_FRICATION_S and b >= v), None)
            if hit:
                boundaries = Boundaries(hit[0], v, True)
                break
        if boundaries is None:
            a, b = max(runs, key=lambda r: r[1] - r[0])
            if b - a < C.MIN_FRICATION_S:
                error = "Frication too short (< 30 ms)"
            else:
                boundaries = Boundaries(a, b, False)
    return Trace(t, hi, floor, threshold, runs, voiced, boundaries, error)


def find_boundaries(sound: parselmouth.Sound) -> Boundaries:
    """Onset = start of the high-band run that leads into the vowel; offset = voicing onset.

    With no vowel, the longest high-band run is used. Clicks and breaths separated from
    the hiss by more than GAP_BRIDGE_S of quiet are never taken as the onset.
    """
    tr = trace_boundaries(sound)
    if tr.boundaries is None:
        raise SegmentationError(tr.error)
    return tr.boundaries
