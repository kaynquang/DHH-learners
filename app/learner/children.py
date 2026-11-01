"""What the learners' app keeps about each child besides the voice numbers (fricative/calibrated.py) and the stars (learner/stars.py): boy or girl,
for the face shown next to the name on the home page. Kept in the profiles folder (personal data, not in git)."""
from __future__ import annotations

import json

from fricative.calibrated import PROFILES_DIR, clean_name

GENDERS = ("boy", "girl")
_FILE = PROFILES_DIR / "_children.json"


def _load() -> dict[str, dict]:
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gender(name: str | None) -> str | None:
    """"boy", "girl", or None when it was never set."""
    return _load().get(clean_name(name), {}).get("gender") if name else None


def set_gender(name: str, value: str) -> None:
    if value not in GENDERS:
        return
    data = _load()
    data.setdefault(clean_name(name), {})["gender"] = value
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def forget(name: str) -> None:
    data = _load()
    if data.pop(clean_name(name), None) is not None:
        _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
