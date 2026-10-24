"""Optional cross-check with a multilingual phone recogniser (wav2vec2 XLSR-53 fine-tuned on eSpeak phones).

Needs torch, transformers and the checkpoint folder (set W2V_DIR, or place it in app/assets/model/w2v_phone). The rest of the app
works without it. The checkpoint is facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0, about 1.2 GB, 16 kHz input).
"""
from __future__ import annotations

import importlib.util
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import parselmouth

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "assets" / "model" / "w2v_phone"
RATE_HZ, PRE_S, POST_S = 16000, 0.08, 0.30
FRAME_S, FIRST_CENTRE_S = 0.02, 0.0125
FLOOR = 0.02            # a group needs at least this much mean posterior over the hiss to count as heard
# The vocabulary mixes many languages: "s." and ʂ are retroflex, which English /ʃ/ is often transcribed as.
GROUPS = {"S": ["s", "s̪", "s^"], "SH": ["ʃ", "s.", "ʂ", "ɕ", "ʂʲ", "ɕʲ"], "F": ["f", "fʲ", "ɸ"], "TH": ["θ"]}


@dataclass(frozen=True)
class PhoneCheck:
    masses: dict[str, float]            # mean posterior of each group over the hiss
    heard: str | None                   # "S", "SH", "F", "TH" or None when nothing reaches FLOOR
    decoded: str                        # greedy phone string of the whole clip
    centres: np.ndarray                 # frame centres, seconds from the start of the clip
    track: dict[str, np.ndarray]        # per-frame posterior of each group
    hiss_window: tuple[float, float]    # the hiss, seconds from the start of the clip


def model_dir() -> Path | None:
    for cand in (os.environ.get("W2V_DIR"), DEFAULT_DIR):
        if cand and (Path(cand) / "pytorch_model.bin").exists() and (Path(cand) / "vocab.json").exists():
            return Path(cand)
    return None


def available() -> bool:
    return model_dir() is not None and all(importlib.util.find_spec(m) for m in ("torch", "transformers"))


@lru_cache(maxsize=1)
def _load(directory: str):
    import torch
    from transformers import Wav2Vec2ForCTC
    model = Wav2Vec2ForCTC.from_pretrained(directory).eval()
    vocab = json.loads((Path(directory) / "vocab.json").read_text(encoding="utf-8"))
    return torch, model, vocab


def check(sound: parselmouth.Sound, onset_s: float, offset_s: float) -> PhoneCheck:
    """What the recogniser hears at the hiss, given the hiss boundaries found by the app."""
    torch, model, vocab = _load(str(model_dir()))
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    t0, t1 = max(s.xmin, onset_s - PRE_S), min(s.xmax, offset_s + POST_S)
    x = s.values[0][int(t0 * RATE_HZ):int(t1 * RATE_HZ)].astype(np.float64)
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        post = torch.softmax(model(torch.tensor(x, dtype=torch.float32)[None]).logits[0], dim=-1).numpy()
    centres = np.arange(len(post)) * FRAME_S + FIRST_CENTRE_S
    track = {g: post[:, [vocab[t] for t in toks if t in vocab]].sum(axis=1) for g, toks in GROUPS.items()}
    window = (onset_s - t0, offset_s - t0)
    sel = np.flatnonzero((centres >= window[0] - 0.01) & (centres <= window[1] + 0.01))
    if len(sel) == 0:
        sel = np.array([int(np.argmin(np.abs(centres - sum(window) / 2)))])
    masses = {g: float(v[sel].mean()) for g, v in track.items()}
    heard = max(masses, key=masses.get) if max(masses.values()) >= FLOOR else None
    ids2tok = {i: t for t, i in vocab.items()}
    blank, prev, out = vocab["<pad>"], -1, []
    for k in post.argmax(-1):
        if k != prev and k != blank:
            out.append(ids2tok[int(k)])
        prev = k
    return PhoneCheck(masses, heard, " ".join(out), centres, track, window)


def agrees(app_heard: str, group: str | None) -> bool:
    """Does the recogniser's group match what the app heard ("s", "sh", or "f" = a weak /f/ or /θ/)?"""
    return group in {"s": {"S"}, "sh": {"SH"}, "f": {"F", "TH"}}[app_heard]


# Which kind of sound opens the word. Only a different KIND is a reason not to score (a /b/ said for /p/ is scored, a /f/ for /p/ is not).
GATE_GROUPS = {**GROUPS, "P": ["p", "pʰ", "p^"], "B": ["b", "ɓ"], "M": ["m"], "N": ["n"], "CH": ["tʃ", "t͡ʃ", "tʃʰ", "tɕ"]}
FAMILY = {"S": "fricative", "SH": "fricative", "F": "fricative", "TH": "fricative", "P": "stop", "B": "stop", "M": "nasal", "N": "nasal",
          "CH": "affricate"}
GATE_LABEL = {"S": "/s/", "SH": "/ʃ/", "F": "/f/", "TH": "/θ/", "P": "/p/", "B": "/b/", "M": "/m/", "N": "/n/", "CH": "/tʃ/"}
TARGET_FAMILY = {"s": "fricative", "sh": "fricative", "f": "fricative", "p": "stop", "b": "stop", "m": "nasal", "n": "nasal", "tʃ": "affricate"}


def first_consonant(sound: parselmouth.Sound) -> str | None:
    """The group (key of GATE_GROUPS) of the first or second phone the recogniser decodes for the whole clip, if it is one of them."""
    torch, model, vocab = _load(str(model_dir()))
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    x = s.values[0].astype(np.float64)
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        ids = model(torch.tensor(x, dtype=torch.float32)[None]).logits[0].argmax(-1).numpy()
    ids2tok, blank, prev, phones = {i: t for t, i in vocab.items()}, vocab["<pad>"], -1, []
    for k in ids:
        if k != prev and k != blank:
            phones.append(ids2tok[int(k)])
        prev = k
    lookup = {tok: g for g, toks in GATE_GROUPS.items() for tok in toks}
    return next((lookup[ph] for ph in phones[:2] if ph in lookup), None)


def wrong_kind(target: str, group: str | None) -> bool:
    """True when the recogniser clearly hears a different kind of sound (stop, fricative, nasal, affricate) than the target."""
    if target == "tʃ" and group == "SH":        # a plain /ʃ/ is the usual way to miss /tʃ/; the affricate scorer decides that
        return False
    return group is not None and FAMILY[group] != TARGET_FAMILY[target]


def nasal_reading(sound: parselmouth.Sound) -> tuple[float | None, str]:
    """(share of /m/ against /n/ at the nasal, decoded phones). The nasal is the frame, in the first 0.6 s after speech starts, where
    the recogniser puts the most posterior on m or n. None when it never reaches FLOOR."""
    torch, model, vocab = _load(str(model_dir()))
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    x = s.values[0].astype(np.float64)
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        post = torch.softmax(model(torch.tensor(x, dtype=torch.float32)[None]).logits[0], dim=-1).numpy()
    m, n = post[:, vocab["m"]], post[:, vocab["n"]]
    both = m + n
    active = np.flatnonzero(post[:, vocab["<pad>"]] < 0.9)           # frames where the recogniser hears something
    if not len(active):
        return None, ""
    window = np.flatnonzero((np.arange(len(post)) >= active[0]) & (np.arange(len(post)) <= active[0] + 30))
    k = int(window[np.argmax(both[window])])
    sel = slice(max(k - 2, 0), k + 3)
    if both[sel].mean() < FLOOR:
        return None, ""
    return float(m[sel].sum() / both[sel].sum()), ""


CH_PROBE_JSON = Path(__file__).resolve().parents[1] / "assets" / "model" / "ch_probe.json"


def probability_ch(sound: parselmouth.Sound, onset_s: float, offset_s: float) -> float:
    """Chance of /tʃ/ (against /ʃ/) from a linear probe on wav2vec2 layer 8 over the hiss alone (an estimate; leave-one-voice-out
    balanced accuracy 0.963 on eight ARCTIC voices, running speech)."""
    spec = json.loads(CH_PROBE_JSON.read_text(encoding="utf-8"))
    torch, _, _ = _load(str(model_dir()))
    base = _base(str(model_dir()))
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    x = s.values[0][int(onset_s * RATE_HZ):int(offset_s * RATE_HZ)].astype(np.float64)
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        h = base(torch.tensor(x, dtype=torch.float32)[None], output_hidden_states=True).hidden_states[spec["layer"]][0].mean(0).numpy()
    z = (h - np.array(spec["mean"])) / np.array(spec["scale"])
    return float(1 / (1 + np.exp(-(np.dot(spec["coef"], z) + spec["intercept"]))))


@lru_cache(maxsize=1)
def _base(directory: str):
    from transformers import Wav2Vec2Model
    return Wav2Vec2Model.from_pretrained(directory).eval()


def reconcile(verdict, group: str | None):
    """Combine the measured verdict with what the recogniser hears over the hiss alone (/s/, /ʃ/, /f/ words).

    On L2-ARCTIC (annotated learner errors) the fixed-threshold rules flagged 45% of correctly said /s/ and /ʃ/ but the recogniser only
    5%, while catching 88 to 100% of the annotated s/ʃ confusions. So the recogniser decides whether it is the right sound; the measured
    verdict keeps deciding between green and yellow."""
    from dataclasses import replace
    from .classify import LABELS, MARKS, TIPS
    from .config import PHONE_LABEL
    if group is None:
        return verdict
    heard = {"S": "s", "SH": "sh", "F": "f", "TH": "f"}[group]
    if heard != verdict.target:
        return replace(verdict, color="red", label=LABELS["red"], mark=MARKS["red"], heard=heard,
                       message=f"You said {PHONE_LABEL[heard]}", tip=TIPS[verdict.target])
    if verdict.color == "red":     # the recogniser hears the right sound but the thresholds disagree
        return replace(verdict, color="yellow", label=LABELS["yellow"], mark=MARKS["yellow"], heard=heard,
                       message=f"You said {PHONE_LABEL[heard]}", tip="Close. " + TIPS[verdict.target])
    return verdict


PB_PROBE_JSON = Path(__file__).resolve().parents[1] / "assets" / "model" / "pb_probe.json"


def probability_p(sound: parselmouth.Sound, burst_s: float, voicing_s: float) -> float:
    """Chance of /p/ (against /b/) from a linear probe on wav2vec2 layer 8 over burst-10 ms to voicing+40 ms (an estimate). Trained on
    ARCTIC (leave-one-voice-out 0.96). On L2-ARCTIC it flagged 54% of annotated /b/ errors at 10% false alarms and 85% of /p/ errors
    at 36% false alarms; the VOT rule flagged 46% and 43% at 39% and 28%."""
    spec = json.loads(PB_PROBE_JSON.read_text(encoding="utf-8"))
    torch, _, _ = _load(str(model_dir()))
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    x = s.values[0][int(max(burst_s - 0.01, 0) * RATE_HZ):int((voicing_s + 0.04) * RATE_HZ)].astype(np.float64)
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        h = _base(str(model_dir()))(torch.tensor(x, dtype=torch.float32)[None], output_hidden_states=True).hidden_states[spec["layer"]][0].mean(0).numpy()
    z = (h - np.array(spec["mean"])) / np.array(spec["scale"])
    return float(1 / (1 + np.exp(-(np.dot(spec["coef"], z) + spec["intercept"]))))
