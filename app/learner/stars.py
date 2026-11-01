"""The star rule and what a child has earned so far.

Stars follow the zones of the result slider (learner/result.py):
- green = 3 stars
- yellow, the half nearer to green = 2 stars; yellow, the half nearer to red = 1 star
- red = 0 stars, and the child practises again
The best result a child has had on a word is kept, in their own file under profiles/_progress (a folder, so the profile list never shows it).
A word is "in progress" after its first try and "done" at 3 stars. Provisional until the content owner confirms the rule.
"""
from __future__ import annotations

import json

from fricative.calibrated import PROFILES_DIR, clean_name

YELLOW_SPLIT = 0.65          # the middle of the yellow zone (0.5 to 0.8)
MAX_STARS = 3


def stars(color: str | None, closeness: float | None) -> int | None:
    """Stars for one result (None when nothing was scored)."""
    if color is None:
        return None
    if color == "green":
        return 3
    if color == "red":
        return 0
    return 2 if closeness is None or closeness >= YELLOW_SPLIT else 1


def _path(child: str):
    return PROFILES_DIR / "_progress" / f"{clean_name(child)}.json"


def load(child: str | None) -> dict[str, dict]:
    """{word: {"best": stars, "tries": n}} for this child ({} when none)."""
    if not child:
        return {}
    try:
        return json.loads(_path(child).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def record(child: str | None, word: str, earned: int) -> bool:
    """Keep this try. Returns True when it changed what the child has (a new word or more stars)."""
    if not child:
        return False
    data = load(child)
    old = data.get(word, {"best": 0, "tries": 0})
    new = {"best": max(old["best"], earned), "tries": old["tries"] + 1}
    data[word] = new
    _path(child).parent.mkdir(parents=True, exist_ok=True)
    _path(child).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return old["tries"] == 0 or new["best"] != old["best"]


def forget(child: str) -> None:
    _path(child).unlink(missing_ok=True)


def total(child: str | None) -> int:
    return sum(v["best"] for v in load(child).values())


def status(progress: dict[str, dict], word: str) -> str:
    """"not started", "in progress" or "done"."""
    w = progress.get(word)
    return "not started" if not w else "done" if w["best"] >= MAX_STARS else "in progress"
