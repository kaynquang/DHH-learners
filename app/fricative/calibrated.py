"""Scoring calibrated to the learner's own voice.

The model is a pair of LDAs trained on eight ARCTIC voices that were each normalised the same way the learner is:
from a few tokens of /s/, /ʃ/ and /f/ (see, she, fee, twice each). Experimental: it has not been validated on isolated
words or on deaf and hard-of-hearing speakers.
"""
from __future__ import annotations

import json
import os
import re
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


PROFILES_DIR = Path(os.environ.get("FRICATIVE_PROFILES") or Path(__file__).resolve().parents[1] / "profiles")
NAME_OK = re.compile(r"[^\w \-]", re.UNICODE)


def clean_name(raw: str) -> str:
    """A profile name that is safe as a file name: letters, digits, spaces, _ and -, at most 30 characters ("" if nothing is left)."""
    return " ".join(NAME_OK.sub("", raw).split())[:30]


def _path(name: str) -> Path:
    return PROFILES_DIR / f"{clean_name(name)}.json"


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json")) if PROFILES_DIR.exists() else []


def create_profile(name: str) -> str | None:
    """Make an empty profile; returns its cleaned name, or None when the name is empty or already taken."""
    name = clean_name(name)
    if not name or name in list_profiles():
        return None
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    _path(name).write_text("{}", encoding="utf-8")
    return name


def delete_profile(name: str) -> None:
    _path(name).unlink(missing_ok=True)


def last_profile() -> str | None:
    try:
        name = (PROFILES_DIR / "_last.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return name if name in list_profiles() else None


def remember_profile(name: str | None) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILES_DIR / "_last.txt").write_text(name or "", encoding="utf-8")


def save_profile(cal: Calibration, tokens: list[dict], name: str, noise_db: float | None = None) -> None:
    """Keep the learner's calibration on disk so it survives a restart. tokens = [{"word", "feats"}] as the Calibrate page holds them.
    Optional room measures (Sound Check): noise_db for the room, and "speech_db" / "snr" in each token."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    _path(name).write_text(json.dumps({
        "mu": cal.mu.tolist(), "sd": cal.sd.tolist(), "n_tokens": cal.n_tokens, "noise_db": noise_db,
        "tokens": [{"word": t["word"], "scalars": t["feats"].scalars, "speech_db": t.get("speech_db"), "snr": t.get("snr")} for t in tokens],
    }, ensure_ascii=False, indent=1), encoding="utf-8")


def save_voice(name: str, takes: list[dict], noise_db: float | None) -> None:
    """Keep a child's voice size (Sound Check): takes = [{"f3_hz", "speech_db", "snr"}], from fricative/vtl.py. The scale is their median F3
    relative to the reference. This replaces the old calibration from see / she / fee, which asked the child to say the target sounds right."""
    from .vtl import scale_from
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    f3 = float(np.median([t["f3_hz"] for t in takes]))
    _path(name).write_text(json.dumps({"voice": {"f3_hz": f3, "scale": scale_from(f3), "takes": takes}, "noise_db": noise_db},
                                      ensure_ascii=False, indent=1), encoding="utf-8")


def load_voice(name: str | None) -> dict | None:
    """{"f3_hz", "scale", "takes"} of a child, or None (no child, nothing recorded, or an old see/she/fee profile)."""
    if not name:
        return None
    try:
        v = json.loads(_path(name).read_text(encoding="utf-8")).get("voice")
        return v if isinstance(v, dict) and "scale" in v else None
    except (OSError, ValueError, AttributeError):
        return None


def voice_scale(name: str | None) -> float:
    v = load_voice(name)
    return float(v["scale"]) if v else 1.0


def load_room(name: str) -> float | None:
    """The room noise level (dBFS) kept with the profile, or None."""
    try:
        v = json.loads(_path(name).read_text(encoding="utf-8")).get("noise_db")
        return None if v is None else float(v)
    except (OSError, ValueError, TypeError, AttributeError):
        return None

def load_profile(name: str) -> tuple[Calibration, list[dict]] | None:
    """The saved calibration and the tokens it came from (their shapes are not kept), or None when there is none or it is unreadable."""
    try:
        d = json.loads(_path(name).read_text(encoding="utf-8"))
        cal = Calibration(np.array(d["mu"], dtype=float), np.array(d["sd"], dtype=float), int(d["n_tokens"]))
        empty = np.array([])
        tokens = [dict(word=t["word"], feats=Features(t["scalars"], empty, empty, empty), speech_db=t.get("speech_db"), snr=t.get("snr"))
                  for t in d["tokens"]]
        return cal, tokens
    except (OSError, ValueError, KeyError, TypeError):
        return None


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
