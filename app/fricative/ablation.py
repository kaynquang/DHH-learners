"""Ablation studies: run every detector and every CoG setting on one recording."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import parselmouth
from parselmouth.praat import call

from .classify import classify
from .config import Thresholds
from .measure import analysis_window, measure, spectrum_db
from .segment import SegmentationError
from .segment_alt import METHODS


@dataclass(frozen=True)
class SegRow:
    key: str
    name: str
    onset_s: float | None = None
    offset_s: float | None = None
    onset_err_ms: float | None = None
    offset_err_ms: float | None = None
    cog_hz: float | None = None
    relamp_db: float | None = None
    heard: str | None = None
    mark: str | None = None
    label: str | None = None
    error: str | None = None


def segmentation_ablation(
    sound: parselmouth.Sound, target: str, th: Thresholds, manual: tuple[float, float] | None = None
) -> list[SegRow]:
    """One row per detector: boundaries, error against `manual` (if given), measures and verdict."""
    rows = []
    for key, method in METHODS.items():
        try:
            b = method.run(sound)
        except SegmentationError as exc:
            rows.append(SegRow(key, method.name, error=str(exc)))
            continue
        m = measure(sound, b.onset_s, b.offset_s, b.found_vowel)
        v = classify(m, target, th)
        rows.append(SegRow(
            key, method.name, b.onset_s, b.offset_s,
            None if manual is None else (b.onset_s - manual[0]) * 1000,
            None if manual is None else (b.offset_s - manual[1]) * 1000,
            m.cog_hz, m.relamp_db, v.heard, v.mark, v.label,
        ))
    return rows


def _band_cog(spectrum, lo: float, hi: float) -> float:
    f = np.array([spectrum.get_frequency_from_bin_number(i + 1) for i in range(spectrum.nx)])
    p = spectrum.values[0] ** 2 + spectrum.values[1] ** 2
    keep = (f >= lo) & (f <= hi)
    return float((f[keep] * p[keep]).sum() / p[keep].sum())


def cog_ablation(sound: parselmouth.Sound, onset_s: float, offset_s: float) -> list[tuple[str, float]]:
    """CoG of the middle 50% under different window functions and frequency bands."""
    a, b = analysis_window(onset_s, offset_s)
    rect = call(sound, "Extract part", a, b, "rectangular", 1, "no")
    hann = call(sound, "Extract part", a, b, "Hanning", 1, "no")
    spec = rect.to_spectrum()
    f, db = spectrum_db(sound, a, b, fmax=sound.sampling_frequency / 2)
    power = 10 ** (db / 10)
    band = (f >= 300) & (f <= 11000)
    return [
        ("Rectangular, 0 Hz–Nyquist (current)", float(call(spec, "Get centre of gravity", 2.0))),
        ("Hanning", float(call(hann.to_spectrum(), "Get centre of gravity", 2.0))),
        ("Multitaper (NW = 4)", float((f[band] * power[band]).sum() / power[band].sum())),
        ("Rectangular, 0–12 kHz", _band_cog(spec, 0, 12000)),
        ("Rectangular, 1–11 kHz", _band_cog(spec, 1000, 11000)),
    ]


AGREE_MS = 20.0


def summarize_segmentation(rows: list[SegRow], manual: tuple[float, float] | None = None) -> list[str]:
    """Plain-language reading of the detector timeline.

    Each detector is compared with the manual boundaries when they exist, otherwise with the
    current detector. Both ends within AGREE_MS count as agreement.
    """
    current = rows[0]
    if manual is not None:
        ref, lines = manual, [f"Each detector compared with the manual Praat boundaries "
                              f"(agreement = both ends within {AGREE_MS:.0f} ms)."]
        others = rows
    elif current.error is None:
        ref, lines = (current.onset_s, current.offset_s), [
            f"No manual boundaries for this recording, so each detector is compared with the current detector "
            f"(agreement = both ends within {AGREE_MS:.0f} ms)."]
        others = rows[1:]
    else:
        ref, lines = None, ["The current detector failed and there is no manual reference: "
                            "judge the bars against the spectrogram above."]
        others = rows
    for r in others:
        if r.error is not None:
            lines.append(f"{r.name} failed: {r.error}.")
            continue
        if ref is None:
            lines.append(f"{r.name} found {r.onset_s * 1000:.0f}–{r.offset_s * 1000:.0f} ms.")
            continue
        d_on, d_off = (r.onset_s - ref[0]) * 1000, (r.offset_s - ref[1]) * 1000
        if abs(d_on) <= AGREE_MS and abs(d_off) <= AGREE_MS:
            lines.append(f"{r.name} agrees (onset {round(d_on) + 0:+d} ms, offset {round(d_off) + 0:+d} ms).")
            continue
        parts = []
        if abs(d_on) > AGREE_MS:
            parts.append(f"starts {abs(d_on):.0f} ms {'earlier' if d_on < 0 else 'later'}")
        if abs(d_off) > AGREE_MS:
            parts.append(f"ends {abs(d_off):.0f} ms {'earlier' if d_off < 0 else 'later'}")
        lines.append(f"{r.name} {' and '.join(parts)}.")
    return lines
