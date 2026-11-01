"""Goodness-of-pronunciation (GOP) scoring of the first consonant, the same way for every learner (no personal calibration).

The recogniser (wav2vec2, CTC, fricative/phoneme_check.py) gives, for each 20 ms frame, a probability for every phone. Instead of
decoding the whole clip and reading off its first phone, this module asks a narrower question: given the first 0.45 s of speech,
how likely is each candidate consonant, followed by any vowel? For a candidate c the score is the CTC likelihood of the sequence
[c, v] summed over every vowel v (so the vowel the learner chose does not matter), and the candidates are then normalised:

    P(c) = L(c) / sum over the confusable set of L(c')

The confusable set holds the target and the sounds it is most often mistaken for (b: p m d v; m: n b p; ...). The target's P is the
GOP-style score; the verdict comes from it and from the strongest competitor. Thresholds are provisional.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.special import logsumexp

from . import affricate, nasals, stops
from .classify import LABELS, MARKS, Verdict

PRE_FRAMES = 3             # frames kept before the first frame where the recogniser hears something (20 ms each)
WIDTH_FRAMES = 22          # about 0.45 s from there: the consonant and the start of the vowel
ACTIVE_BLANK_P = 0.9       # a frame is speech when the blank symbol has less than this probability
GREEN_P = 0.80             # P(target) for green
YELLOW_P = 0.50            # P(target) for yellow (and the target must also be the top candidate)
RED_P = 0.60               # a different top candidate needs at least this P to be named as what was heard

# Each candidate is a list of spellings in the recogniser's vocabulary; a spelling is a sequence of phone tokens.
VARIANTS = {
    "p": [["p"], ["pʰ"]], "b": [["b"]], "m": [["m"]], "n": [["n"]], "d": [["d"]], "t": [["t"], ["tʰ"]], "v": [["v"]], "f": [["f"]],
    "l": [["l"]], "s": [["s"]], "ʃ": [["ʃ"], ["ɕ"]],
    "tʃ": [["tʃ"], ["tɕ"], ["dʒ"], ["t", "ʃ"]],
}
CONFUSABLE = {
    "b": ["b", "p", "m", "d", "v"],
    "p": ["p", "b", "m", "t", "f"],
    "m": ["m", "n", "b", "p"],
    "n": ["n", "m", "d", "t", "l"],
    "tʃ": ["tʃ", "ʃ", "t", "s", "d"],
}
TIPS = {**stops.TIPS, **nasals.TIPS, "tʃ": affricate.TIP}
SUPPORTED = tuple(CONFUSABLE)


@dataclass(frozen=True)
class Gop:
    probs: dict[str, float]      # P(candidate) over the confusable set; sums to 1
    top: str
    start_s: float               # where the analysed stretch starts
    end_s: float = 0.0           # where it ends
    phones: tuple[str, ...] = ()                 # what the recogniser decodes for the whole clip, e.g. ("b@0.58", "i@0.64")
    tracks: dict[str, list[float]] = field(default_factory=dict)   # per 20 ms frame: probability of each candidate's first phone

    def p(self, target: str) -> float:
        return self.probs[target]


def ctc_log_likelihood(log_post: np.ndarray, seq: list[int], blank: int) -> float:
    """Log of the probability that the frames spell exactly `seq` (CTC forward algorithm over all alignments)."""
    S = 2 * len(seq) + 1
    ext = [blank] * S
    for i, tok in enumerate(seq):
        ext[2 * i + 1] = tok
    a = np.full(S, -np.inf)
    a[0] = log_post[0, blank]
    a[1] = log_post[0, ext[1]]
    skip = [s for s in range(3, S, 2) if ext[s] != ext[s - 2]]
    for t in range(1, len(log_post)):
        n = a.copy()
        n[1:] = np.logaddexp(n[1:], a[:-1])
        for s in skip:
            n[s] = np.logaddexp(n[s], a[s - 2])
        a = n + log_post[t, ext]
    return float(np.logaddexp(a[-1], a[-2]))


def vowel_tokens(vocab: dict[str, int]) -> list[str]:
    """Plain vowel symbols of the recogniser (no tone digits), the ones a learner could put after the consonant."""
    from .phoneme_check import VOWEL_LETTERS
    return [t for t in vocab if t and all(ch in VOWEL_LETTERS or ch == "ː" for ch in t)]


def onset_probs(log_post: np.ndarray, vocab: dict[str, int], names: list[str]) -> tuple[dict[str, float], int] | None:
    """P(candidate) for the consonant that opens the speech, and the frame where the analysed stretch starts. None if no speech."""
    blank = vocab["<pad>"]
    active = np.flatnonzero(log_post[:, blank] < np.log(ACTIVE_BLANK_P))
    if not len(active):
        return None
    start = max(int(active[0]) - PRE_FRAMES, 0)
    crop = log_post[start:start + WIDTH_FRAMES]
    vowels = [vocab[v] for v in vowel_tokens(vocab)]
    scores = {}
    for name in names:
        lls = []
        for spelling in VARIANTS[name]:
            ids = [vocab[t] for t in spelling if t in vocab]
            if len(ids) == len(spelling):
                lls.extend(ctc_log_likelihood(crop, ids + [v], blank) for v in vowels)
        scores[name] = float(logsumexp(lls)) if lls else -np.inf
    z = logsumexp(list(scores.values()))
    return {n: float(np.exp(s - z)) for n, s in scores.items()}, start


def score(sound, target: str) -> Gop | None:
    """GOP of the consonant that opens the recording against the sounds it is confused with. Needs the recogniser."""
    from . import phoneme_check
    log_post = phoneme_check.log_posteriors(sound)
    found = onset_probs(log_post, phoneme_check.vocabulary(), CONFUSABLE[target])
    if found is None:
        return None
    probs, start = found
    vocab = phoneme_check.vocabulary()
    frame_s = phoneme_check.FRAME_S
    inv = {i: t for t, i in vocab.items()}
    decoded, prev = [], -1
    for i, k in enumerate(log_post.argmax(axis=1)):
        if k != prev and k != vocab["<pad>"]:
            decoded.append(f"{inv[int(k)]}@{i * frame_s:.2f}")
        prev = k
    tracks = {name: np.exp(log_post[:, [vocab[v[0]] for v in VARIANTS[name] if v[0] in vocab]]).sum(axis=1).round(4).tolist()
              for name in CONFUSABLE[target]}
    return Gop(probs, max(probs, key=probs.get), start * frame_s, (start + WIDTH_FRAMES) * frame_s, tuple(decoded), tracks)


def verdict(g: Gop, target: str) -> Verdict | None:
    """Green, yellow or red from the target's P and the strongest competitor; None when the recogniser is not sure of anything."""
    p, top = g.p(target), g.top
    if p >= GREEN_P:
        color, tip = "green", "Well done. Keep the same movement."
    elif p >= YELLOW_P and top == target:
        color, tip = "yellow", "Close. " + TIPS[target]
    elif top != target and g.probs[top] >= RED_P:
        color, tip = "red", TIPS[target]
    else:
        return None
    heard = target if top == target else top
    return Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said /{heard}/", tip)
