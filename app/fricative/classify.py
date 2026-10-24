"""Green / yellow / red scoring in two steps: relative amplitude, then CoG."""
from __future__ import annotations

from dataclasses import dataclass

from .config import DEFAULT_THRESHOLDS, PHONE_LABEL, Thresholds
from .measure import Measures

# Provisional tips, to be rewritten by the phonetics lead.
TIPS = {
    "s": "Place the tongue tip just behind the upper teeth, spread the lips slightly, and push a strong, narrow stream of air.",
    "sh": "Pull the tongue back a little, round and push the lips forward, and let the air flow wider than for /s/.",
    "f": "Rest the upper teeth lightly on the lower lip and blow gently through the gap.",
}
LABELS = {"green": "Correct", "yellow": "Almost", "red": "Not yet"}
MARKS = {"green": "◯", "yellow": "△", "red": "✕"}  # Japanese grading marks


@dataclass(frozen=True)
class Verdict:
    color: str          # "green" | "yellow" | "red"
    label: str          # "Correct" | "Almost" | "Not yet"
    mark: str           # "◯" | "△" | "✕"
    heard: str          # "s" | "sh" | "f"
    target: str
    message: str        # "You said /s/"
    tip: str
    note: str | None = None


def heard_phone(m: Measures, th: Thresholds) -> str:
    if m.relamp_db is not None and m.relamp_db < th.relamp_f_db:
        return "f"
    return "s" if m.cog_hz >= th.cog_s_sh_hz else "sh"


def _is_clear(m: Measures, heard: str, th: Thresholds) -> bool:
    if heard == "f":
        return m.relamp_db is not None and m.relamp_db < th.relamp_f_db - th.relamp_margin_db
    relamp_ok = m.relamp_db is None or m.relamp_db >= th.relamp_f_db + th.relamp_margin_db
    if heard == "s":
        return relamp_ok and m.cog_hz >= th.cog_s_sh_hz + th.cog_margin_hz
    return relamp_ok and m.cog_hz < th.cog_s_sh_hz - th.cog_margin_hz


def classify(m: Measures, target: str, th: Thresholds = DEFAULT_THRESHOLDS) -> Verdict:
    heard = heard_phone(m, th)
    if heard != target:
        color, tip = "red", TIPS[target]
    elif _is_clear(m, heard, th):
        color, tip = "green", "Well done. Keep the same tongue and lip position."
    else:
        color, tip = "yellow", "Close. " + TIPS[target]
    note = "No vowel after the hiss, so /f/ could not be checked." if m.relamp_db is None else None
    return Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said {PHONE_LABEL[heard]}", tip, note)
