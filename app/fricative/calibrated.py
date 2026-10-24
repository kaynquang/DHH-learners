"""Scoring calibrated to the learner's own voice.

The model is a pair of LDAs trained on eight ARCTIC voices that were each normalised the same way the learner is:
from a few tokens of /s/, /ʃ/ and /f/ (see, she, fee, twice each). Experimental: it has not been validated on isolated
words or on deaf and hard-of-hearing speakers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .classify import LABELS, MARKS, TIPS, Verdict
from .config import PHONE_LABEL
from .patterns import SCALAR_KEYS, Features

MODEL_JSON = Path(__file__).resolve().parents[1] / "assets" / "model" / "calibrated_lda.json"
CAL_WORDS = ("see", "she", "fee", "see", "she", "fee")
MIN_TOKENS = 3
GREEN_P = 0.80          # probability of the target sound needed for green; provisional


@dataclass(frozen=True)
class Calibration:
    mu: np.ndarray
    sd: np.ndarray
    n_tokens: int


@dataclass(frozen=True)
class Reading:
    verdict: Verdict
    probs: dict[str, float]          # "s", "sh", "f" (weak hiss: /f/ or /θ/); they add up to 1
    missing: tuple[str, ...]         # features that could not be measured and were set to the calibration mean


def load_model(path: Path = MODEL_JSON) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _vector(f: Features) -> np.ndarray:
    return np.array([f.scalars[k] for k in SCALAR_KEYS], dtype=float)


def build_calibration(tokens: list[Features]) -> Calibration:
    """Mean and spread of every feature over the learner's calibration recordings."""
    if len(tokens) < MIN_TOKENS:
        raise ValueError(f"Calibration needs at least {MIN_TOKENS} recordings")
    X = np.stack([_vector(t) for t in tokens])
    mu, sd = np.nanmean(X, axis=0), np.nanstd(X, axis=0, ddof=1)
    sd = np.where(np.isfinite(sd) & (sd > 1e-9), sd, 1.0)
    return Calibration(np.where(np.isfinite(mu), mu, 0.0), sd, len(tokens))


def standardise(f: Features, cal: Calibration) -> tuple[np.ndarray, list[str]]:
    """z-scores against the calibration; a feature that could not be measured becomes 0 and is reported."""
    z = (_vector(f) - cal.mu) / cal.sd
    missing = [SCALAR_KEYS[i] for i in np.flatnonzero(np.isnan(z))]
    return np.nan_to_num(z, nan=0.0), missing


def _score(spec: dict, z: np.ndarray) -> float:
    idx = [SCALAR_KEYS.index(k) for k in spec["features"]]
    return float(np.dot(spec["coef"], z[idx]) + spec["intercept"])


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def read(f: Features, cal: Calibration, model: dict, target: str) -> Reading:
    """Probabilities of /s/, /ʃ/ and a weak hiss, and the green / yellow / red verdict against `target`."""
    z, missing = standardise(f, cal)
    has_vowel = "relamp" not in missing
    p_weak = _sigmoid(_score(model["family"] if has_vowel else model["family_novowel"], z))
    p_sh = _sigmoid(_score(model["sibilant"], z))
    probs = {"s": (1 - p_weak) * (1 - p_sh), "sh": (1 - p_weak) * p_sh, "f": p_weak}
    heard = max(probs, key=probs.get)
    if heard != target:
        color, tip = "red", TIPS[target]
    elif probs[target] >= GREEN_P:
        color, tip = "green", "Well done. Keep the same tongue and lip position."
    else:
        color, tip = "yellow", "Close. " + TIPS[target]
    note = None if has_vowel else "No vowel after the hiss, so the weak-hiss check used spectral cues only."
    verdict = Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said {PHONE_LABEL[heard]}", tip, note)
    return Reading(verdict, probs, tuple(missing))
