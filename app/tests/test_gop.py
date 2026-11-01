"""GOP scoring: the CTC likelihood, the normalisation over the confusable set, and the verdict thresholds (no model needed)."""
import numpy as np
import pytest

from fricative import gop

BLANK = 0
VOCAB = {"<pad>": BLANK, "b": 1, "p": 2, "m": 3, "n": 4, "d": 5, "v": 6, "t": 7, "f": 8, "i": 9, "a": 10, "u": 11, "ː": 12}


def frames(*phones: int, noise: float = 0.0, n: int = 22) -> np.ndarray:
    """Log posteriors where each phone in turn owns a few frames and the rest is blank."""
    p = np.full((n, len(VOCAB)), 1e-4)
    p[:, BLANK] = 0.6
    slot = 4
    for k, ph in enumerate(phones):
        p[2 + k * slot: 2 + (k + 1) * slot, ph] = 0.95
        p[2 + k * slot: 2 + (k + 1) * slot, BLANK] = 0.04
    p = p + noise
    return np.log(p / p.sum(axis=1, keepdims=True))


def test_exact_sequence_is_much_likelier_than_a_wrong_one():
    lp = frames(VOCAB["b"], VOCAB["i"])
    assert gop.ctc_log_likelihood(lp, [VOCAB["b"], VOCAB["i"]], BLANK) > gop.ctc_log_likelihood(lp, [VOCAB["m"], VOCAB["i"]], BLANK) + 5


def test_repeated_symbols_need_a_blank_between_them():
    lp = frames(VOCAB["b"])
    assert gop.ctc_log_likelihood(lp, [VOCAB["b"]], BLANK) > gop.ctc_log_likelihood(lp, [VOCAB["b"], VOCAB["b"]], BLANK)


@pytest.mark.parametrize("vowel", ["i", "a", "u"])
def test_the_vowel_after_the_consonant_does_not_matter(vowel):
    out = gop.onset_probs(frames(VOCAB["b"], VOCAB[vowel]), VOCAB, ["b", "p", "m", "d", "v"])
    probs, _ = out
    assert max(probs, key=probs.get) == "b" and probs["b"] > 0.9
    assert sum(probs.values()) == pytest.approx(1.0)


def test_a_different_consonant_is_named_as_what_was_heard():
    probs, _ = gop.onset_probs(frames(VOCAB["m"], VOCAB["i"]), VOCAB, ["b", "p", "m", "d", "v"])
    g = gop.Gop(probs, max(probs, key=probs.get), 0.0)
    v = gop.verdict(g, "b")
    assert v.color == "red" and v.heard == "m" and "/m/" in v.message


def test_silence_has_no_speech():
    lp = np.log(np.full((22, len(VOCAB)), 1e-4))
    lp[:, BLANK] = np.log(0.99)
    assert gop.onset_probs(lp, VOCAB, ["b", "p"]) is None


@pytest.mark.parametrize("p_target,top,expected", [
    (0.95, "b", "green"), (0.65, "b", "yellow"), (0.10, "m", "red"), (0.40, "m", None), (0.45, "b", None)])
def test_verdict_thresholds(p_target, top, expected):
    rest = 1 - p_target
    probs = {"b": p_target, "m": rest if top == "m" else rest / 2, "p": 0.0 if top == "m" else rest / 2}
    if top == "m" and expected is None:
        probs = {"b": p_target, "m": 0.5, "p": 0.1}
    v = gop.verdict(gop.Gop(probs, max(probs, key=probs.get), 0.0), "b")
    assert (v.color if v else None) == expected
