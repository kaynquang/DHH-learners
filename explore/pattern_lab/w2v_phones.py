"""Thin wrapper around facebook/wav2vec2-xlsr-53-espeak-cv-ft: posteriors per 20 ms frame, grouped fricative evidence.

The checkpoint is a multilingual phone recogniser (Apache-2.0, 16 kHz). Set W2V_DIR to the downloaded folder.
"""
import json, os
import numpy as np
import torch
from transformers import Wav2Vec2ForCTC

MODEL = os.environ["W2V_DIR"]
VOCAB = json.load(open(f"{MODEL}/vocab.json"))
ID2TOK = {i: t for t, i in VOCAB.items()}
BLANK = VOCAB["<pad>"]
# the vocabulary mixes many languages' symbols: "s." and ʂ are retroflex, which English /ʃ/ is often heard as
GROUPS = {"S": ["s", "s̪", "s^"], "SH": ["ʃ", "s.", "ʂ", "ɕ", "ʂʲ", "ɕʲ"], "F": ["f", "fʲ", "ɸ"], "TH": ["θ"]}
GROUP_IDS = {g: [VOCAB[t] for t in toks if t in VOCAB] for g, toks in GROUPS.items()}
FRAME_S, FIRST_CENTRE_S = 0.02, 0.0125
_model = None


def model():
    global _model
    if _model is None:
        _model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
    return _model


@torch.no_grad()
def posteriors(x16k: np.ndarray) -> np.ndarray:
    """(frames, vocab) softmax posteriors, one frame per 20 ms. x16k is mono 16 kHz float."""
    x = (x16k - x16k.mean()) / (x16k.std() + 1e-7)
    return torch.softmax(model()(torch.tensor(x, dtype=torch.float32)[None]).logits[0], dim=-1).numpy()


def greedy(post: np.ndarray) -> str:
    ids, out, prev = post.argmax(-1), [], -1
    for k in ids:
        if k != prev and k != BLANK:
            out.append(ID2TOK[int(k)])
        prev = k
    return " ".join(out)


def group_mass(post: np.ndarray, t0: float, t1: float) -> dict[str, float]:
    """Mean posterior of each fricative group over the frames whose centre lies in [t0, t1] (clip-relative seconds)."""
    centres = np.arange(len(post)) * FRAME_S + FIRST_CENTRE_S
    sel = np.flatnonzero((centres >= t0 - 0.01) & (centres <= t1 + 0.01))
    if len(sel) == 0:
        sel = np.array([int(np.argmin(np.abs(centres - (t0 + t1) / 2)))])
    return {g: float(post[sel][:, ids].sum(axis=1).mean()) for g, ids in GROUP_IDS.items()}
