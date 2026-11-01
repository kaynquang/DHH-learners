"""Spectral patterns of a fricative and how they compare with the ARCTIC reference voices.

Experimental: the reference comes from two voices (bdl, slt), so nothing here replaces the
main scoring in `classify`. Features are computed exactly like in `explore/pattern_lab`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import parselmouth
from parselmouth.praat import call

from .config import DEFAULT_THRESHOLDS
from .measure import analysis_window, measure, spectrum_db

REFERENCE_JSON = Path(__file__).resolve().parents[1] / "assets" / "reference" / "arctic_patterns.json"
RATE_HZ = 16000
SCALAR_KEYS = ["cog", "fm", "sd", "skew", "kurt", "e0_2", "e2_4", "e4_6", "e6_8", "relamp", "dur", "contrast", "wobble"]
BAND_EDGES_HZ = np.arange(0, 8000, 200)
TRAJ_MIN_S = 0.060
VOWEL_MIN_S = 0.080
VOWEL_MAX_S = 0.120    # the reference vowels last ~0.1 s, so a held vowel is not allowed to move the "middle" far away
F2_STEPS = 7           # F2 at offset + 0, 10, ... 60 ms
PHONES = ("S", "SH", "F", "TH", "Z")


@dataclass(frozen=True)
class Features:
    scalars: dict[str, float]
    shape: np.ndarray            # 40 bands of 200 Hz, dB, own mean removed
    traj: np.ndarray             # CoG in 5 equal parts of the hiss (nan if shorter than 60 ms)
    f2: np.ndarray               # F2(offset + k * 10 ms) - F2(vowel middle), nan if no vowel of 80 ms or more


@dataclass(frozen=True)
class ExpVerdict:
    family: str                          # "sibilant", "weak" or "unsure" (the two cues disagree)
    votes: dict[str, str] = field(default_factory=dict)      # method -> "s" | "sh"
    heard: str | None = None             # majority of the votes
    unanimous: bool = False
    weak_nearest: str | None = None      # "F" or "TH", shown for information only
    family_cues: dict[str, str] = field(default_factory=dict)  # cue -> "sibilant" | "weak"


def load_reference(path: Path = REFERENCE_JSON) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _band_db(f: np.ndarray, db: np.ndarray) -> np.ndarray:
    power = 10 ** (db / 10)
    out = np.full(len(BAND_EDGES_HZ), np.nan)
    for i, lo in enumerate(BAND_EDGES_HZ):
        m = (f >= lo) & (f < lo + 200)
        if m.any():
            out[i] = 10 * np.log10(power[m].mean() + 1e-20)
    ok = ~np.isnan(out)
    return np.interp(BAND_EDGES_HZ, BAND_EDGES_HZ[ok], out[ok])


def _vowel_length(sound: parselmouth.Sound, offset_s: float) -> float:
    """Length of the voiced stretch that starts right after the hiss (gaps up to 20 ms allowed)."""
    pitch = sound.to_pitch(time_step=0.002, pitch_floor=75.0, pitch_ceiling=500.0)
    ts, voiced = pitch.xs(), pitch.selected_array["frequency"] > 0
    i = int(np.searchsorted(ts, offset_s - 1e-9))
    start = next((j for j in range(i, min(i + 15, len(ts))) if voiced[j]), None)
    if start is None:
        return 0.0
    end, gap = start, 0
    for j in range(start, len(ts)):
        if voiced[j]:
            end, gap = j, 0
        else:
            gap += 1
            if gap > 10:
                break
    return float(ts[end] - offset_s)


def extract(sound: parselmouth.Sound, onset_s: float, offset_s: float, has_vowel: bool = True,
            max_formant_hz: float = 5000.0, with_f2: bool = True) -> Features:
    """All pattern features of one hiss, analysed at 16 kHz to match the reference. `with_f2=False` skips the F2 analysis."""
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    m = measure(s, onset_s, offset_s, has_vowel)
    d = offset_s - onset_s
    a, b = analysis_window(onset_s, offset_s)
    sp = call(s, "Extract part", a, b, "rectangular", 1, "no").to_spectrum()
    f, db = spectrum_db(s, a, b, fmax=8000)
    P = 10 ** (db / 10)
    frac = lambda lo, hi: float(P[(f >= lo) & (f < hi)].sum() / P.sum())
    scalars = {
        "cog": m.cog_hz, "fm": m.fm_hz, "sd": float(call(sp, "Get standard deviation", 2)),
        "skew": float(call(sp, "Get skewness", 2)), "kurt": float(call(sp, "Get kurtosis", 2)),
        "e0_2": frac(0, 2000), "e2_4": frac(2000, 4000), "e4_6": frac(4000, 6000), "e6_8": frac(6000, 8000),
        "relamp": np.nan if m.relamp_db is None else m.relamp_db, "dur": m.duration_ms,
    }
    shape = _band_db(f, db)
    shape = shape - shape.mean()
    scalars["contrast"] = float(np.std(shape))        # how peaky the spectrum is across frequency (dB)

    traj = np.full(5, np.nan)
    if d >= TRAJ_MIN_S:
        traj = np.array([call(call(s, "Extract part", onset_s + k * d / 5, onset_s + (k + 1) * d / 5, "rectangular", 1, "no")
                              .to_spectrum(), "Get centre of gravity", 2) for k in range(5)], dtype=float)

    scalars["wobble"] = float(np.std(traj[1:4])) if not np.isnan(traj).any() else np.nan   # CoG variation across the hiss (Hz)

    f2 = np.full(F2_STEPS, np.nan)
    dv = _vowel_length(s, offset_s) if (has_vowel and with_f2) else 0.0
    if dv >= VOWEL_MIN_S:
        formant = s.to_formant_burg(0.005, 5, max_formant_hz, 0.025, 50)
        mid = formant.get_value_at_time(2, offset_s + min(dv, VOWEL_MAX_S) / 2)
        f2 = np.array([formant.get_value_at_time(2, offset_s + k * 0.01) for k in range(F2_STEPS)], dtype=float) - mid
    return Features(scalars, shape, traj, f2)


def percentiles(f: Features, ref: dict, voice: str) -> dict[str, dict[str, float]]:
    """Where each scalar falls among the tokens of every phone of `voice` (clamped to 5..95)."""
    out = {}
    for ph, data in ref["voices"][voice]["phones"].items():
        out[ph] = {k: float(np.interp(f.scalars[k], data["q"][k], [5, 25, 50, 75, 95])) if not np.isnan(f.scalars[k]) else np.nan
                   for k in SCALAR_KEYS}
    return out


def template_distances(f: Features, ref: dict, voice: str) -> dict[str, float]:
    """Euclidean distance (dB) between the token's shape and each phone's mean shape."""
    return {ph: float(np.linalg.norm(f.shape - np.array(d["shape_mean"]))) for ph, d in ref["voices"][voice]["phones"].items()}


def contrast_threshold(ref: dict, voice: str) -> float:
    """Spectral contrast that separates sibilants from weak hisses: halfway between the two groups' medians."""
    ph = ref["voices"][voice]["phones"]
    sib = np.mean([ph[p]["q"]["contrast"][2] for p in ("S", "SH")])
    weak = np.mean([ph[p]["q"]["contrast"][2] for p in ("F", "TH")])
    return float((sib + weak) / 2)


def family_cues(f: Features, ref: dict, voice: str) -> dict[str, str]:
    """Each cue's call on "sibilant" vs "weak". Relative amplitude needs a vowel; spectral contrast does not."""
    cues = {}
    relamp = f.scalars["relamp"]
    if not np.isnan(relamp):
        cues["Relative amplitude"] = "weak" if relamp < DEFAULT_THRESHOLDS.relamp_f_db else "sibilant"
    cues["Spectral contrast"] = "sibilant" if f.scalars["contrast"] >= contrast_threshold(ref, voice) else "weak"
    return cues


def experimental_verdict(f: Features, ref: dict, voice: str) -> ExpVerdict:
    """Decide the family first (sibilant or weak hiss), then three simple rules for /s/ vs /ʃ/. Experimental."""
    cues = family_cues(f, ref, voice)
    kinds = set(cues.values())
    if kinds == {"weak"}:
        d = template_distances(f, ref, voice)
        return ExpVerdict("weak", family_cues=cues, weak_nearest=min(("F", "TH"), key=lambda p: d[p]))
    if len(kinds) > 1:
        return ExpVerdict("unsure", family_cues=cues)
    phones = ref["voices"][voice]["phones"]
    med = lambda ph, k: phones[ph]["q"][k][2]
    votes = {
        "CoG threshold": "s" if f.scalars["cog"] >= (med("S", "cog") + med("SH", "cog")) / 2 else "sh",
        "Low-band energy (2–4 kHz)": "s" if f.scalars["e2_4"] <= (med("S", "e2_4") + med("SH", "e2_4")) / 2 else "sh",
    }
    d = template_distances(f, ref, voice)
    votes["Nearest spectral template"] = "s" if d["S"] <= d["SH"] else "sh"
    tally = list(votes.values())
    heard = "s" if tally.count("s") >= 2 else "sh"
    return ExpVerdict("sibilant", votes=votes, heard=heard, unanimous=len(set(tally)) == 1, family_cues=cues)
