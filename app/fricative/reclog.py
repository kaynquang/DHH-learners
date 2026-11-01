"""A log of every scored recording, so wrong verdicts can be flagged by the learner and debugged later.

Each recording is stored as logs/audio/<id>.<ext> (the audio exactly as scored) next to logs/entries/<id>.json (what the app
decided and why). The id comes from the audio and the target word, so scoring the same recording again updates its entry instead of
adding a copy, and the learner's flag and note are kept.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(os.environ.get("FRICATIVE_LOGS") or Path(__file__).resolve().parents[1] / "logs")
KEEP = ("flagged", "note", "flagged_at")        # fields the learner owns; never overwritten by a re-score


def _entries() -> Path:
    return LOG_DIR / "entries"


def entry_id(data: bytes, word: str) -> str:
    return hashlib.md5(data + word.encode("utf-8")).hexdigest()[:12]


def log_recording(data: bytes, name: str, word: str, **fields) -> str:
    """Save the audio once and write or refresh the entry. fields = what the app decided (verdict, measurements, settings)."""
    eid = entry_id(data, word)
    ext = Path(name or "recording.wav").suffix.lower() or ".wav"
    (LOG_DIR / "audio").mkdir(parents=True, exist_ok=True)
    _entries().mkdir(parents=True, exist_ok=True)
    audio = LOG_DIR / "audio" / f"{eid}{ext}"
    if not audio.exists():
        audio.write_bytes(data)
    old = get(eid) or {}
    entry = {"id": eid, "time": old.get("time") or datetime.now().isoformat(timespec="seconds"), "word": word,
             "audio": audio.name, "flagged": False, "note": "", **fields}
    entry.update({k: old[k] for k in KEEP if k in old})
    (_entries() / f"{eid}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return eid


def get(eid: str) -> dict | None:
    try:
        return json.loads((_entries() / f"{eid}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def update(eid: str, **fields) -> None:
    entry = get(eid)
    if entry is None:
        return
    entry.update(fields)
    (_entries() / f"{eid}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def flag(eid: str, note: str) -> None:
    """The learner says: I said this correctly, but the app judged it wrong."""
    update(eid, flagged=True, note=note.strip(), flagged_at=datetime.now().isoformat(timespec="seconds"))


def unflag(eid: str) -> None:
    update(eid, flagged=False)


def list_entries() -> list[dict]:
    """Newest first."""
    if not _entries().exists():
        return []
    rows = [e for p in _entries().glob("*.json") if (e := get(p.stem)) is not None]
    return sorted(rows, key=lambda e: e.get("time", ""), reverse=True)


def audio_path(entry: dict) -> Path:
    return LOG_DIR / "audio" / entry["audio"]


def delete_many(keep_flagged: bool = False) -> int:
    """Delete every logged recording (or only the ones that are not flagged). Returns how many were deleted."""
    doomed = [e for e in list_entries() if not (keep_flagged and e.get("flagged"))]
    for e in doomed:
        delete(e["id"])
    return len(doomed)


def delete(eid: str) -> None:
    entry = get(eid)
    if entry is not None:
        audio_path(entry).unlink(missing_ok=True)
    (_entries() / f"{eid}.json").unlink(missing_ok=True)
