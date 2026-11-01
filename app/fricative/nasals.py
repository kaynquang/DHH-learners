"""/m/ against /n/ from the phone recogniser. Praat formant measures only reach 0.63 balanced accuracy for this pair on running speech
(explore/pattern_lab/train_other.py), while the recogniser separates them far better; "me" and "knee" share the vowel, so
the rest of the word does not give the answer away. Needs the optional recogniser (fricative/phoneme_check.py).
"""
from __future__ import annotations

from . import config as C
from .calibrated import GREEN_P
from .classify import LABELS, MARKS, Verdict

TIPS = {
    "m": "Close both lips and let the voice hum through the nose before you open into the vowel.",
    "n": "Press the tongue tip against the ridge behind the upper teeth, keep the lips apart, and hum through the nose.",
}


def classify_nasal(p_m: float | None, target: str) -> Verdict | None:
    """Verdict from the share of /m/ against /n/ (None when no nasal was heard)."""
    if p_m is None:
        return None
    heard = "m" if p_m >= 0.5 else "n"
    p = p_m if heard == "m" else 1 - p_m
    if heard != target:
        color, tip = "red", TIPS[target]
    elif p >= GREEN_P:
        color, tip = "green", "Well done. Keep the same lip and tongue position."
    else:
        color, tip = "yellow", "Close. " + TIPS[target]
    return Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said {C.PHONE_LABEL[heard]}", tip)
