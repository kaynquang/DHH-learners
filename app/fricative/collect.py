"""Data collection for a research session run by a teacher (no Streamlit here, so it can be tested).

One folder per participant code under logs/collect/<code>/:
  session.json   who consented (teacher's initials and date), whether audio may be kept, the words and the number of takes, the app version
  takes.jsonl    one line per take: word, take number, quality numbers, what the app decided (the app's verdict is NOT shown to the child or to the raters)
  audio/<id>.wav the recording, only when audio was consented to
  labels.jsonl   one line per rating by a teacher listening to a take (correct / almost / not yet), several raters allowed
Participants are known by a code (for example S01), never by name. Everything stays on this computer until the teacher exports it.
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

from . import reclog

LOG_DIR = reclog.LOG_DIR
LABELS = ("correct", "almost", "not yet")          # what a rater chooses
APP_LABEL = {"green": "correct", "yellow": "almost", "red": "not yet", None: "not scored"}
TAKES_PER_WORD = 2


def root() -> Path:
    return Path(os.environ.get("FRICATIVE_LOGS") or LOG_DIR) / "collect"


def clean_code(raw: str) -> str:
    """Letters, digits, - and _ only, up to 20 characters (a code, not a name)."""
    return re.sub(r"[^A-Za-z0-9_-]", "", raw or "").upper()[:20]


def _dir(code: str) -> Path:
    return root() / clean_code(code)


def participants() -> list[str]:
    return sorted(p.name for p in root().iterdir() if (p / "session.json").exists()) if root().exists() else []


def start_session(code: str, words: list[str], consent_by: str, audio_ok: bool, takes_per_word: int = TAKES_PER_WORD, **extra) -> dict:
    """Create (or reopen) a session. consent_by: the teacher's initials who confirmed the consent. Returns the session dict."""
    code = clean_code(code)
    if not code:
        raise ValueError("A participant code is required.")
    if not consent_by.strip():
        raise ValueError("The teacher's initials are required to confirm the consent.")
    d = _dir(code)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "session.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    s = {"code": code, "started": datetime.now().isoformat(timespec="seconds"), "consent_confirmed_by": consent_by.strip()[:10], "audio_consent": bool(audio_ok),
         "words": words, "takes_per_word": takes_per_word, "version": reclog.app_version(), **extra}
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return s


def session(code: str) -> dict | None:
    try:
        return json.loads((_dir(code) / "session.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def takes(code: str) -> list[dict]:
    out = []
    try:
        for ln in (_dir(code) / "takes.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def done(code: str) -> dict[str, int]:
    """{word: number of takes kept}."""
    n: dict[str, int] = {}
    for t in takes(code):
        n[t["word"]] = n.get(t["word"], 0) + 1
    return n


def next_item(code: str) -> tuple[str, int] | None:
    """The next (word, take number from 1) to record, in the order of the session; None when everything is recorded."""
    s = session(code)
    if not s:
        return None
    d = done(code)
    for w in s["words"]:
        if d.get(w, 0) < s["takes_per_word"]:
            return w, d.get(w, 0) + 1
    return None


def add_take(code: str, word: str, phone: str, wav: bytes | None, quality: dict, app: dict) -> dict:
    """Keep one take. The audio is written only if the session has audio consent."""
    s = session(code)
    if not s:
        raise ValueError("Unknown session.")
    n = done(code).get(word, 0) + 1
    tid = f"{clean_code(code)}_{word}_{n}"
    audio = None
    if wav and s["audio_consent"]:
        (_dir(code) / "audio").mkdir(exist_ok=True)
        audio = f"audio/{tid}.wav"
        (_dir(code) / audio).write_bytes(wav)
    line = {"take_id": tid, "time": datetime.now().isoformat(timespec="seconds"), "code": clean_code(code), "word": word, "phone": phone, "take": n, "audio": audio,
            "quality": quality, "app": app}
    with (_dir(code) / "takes.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
    return line


def add_rejected(code: str, word: str, take: int, reason: str) -> None:
    """A recording refused for a technical reason (too quiet, too loud, too noisy, no speech). No audio is kept; the reason is, so a report can say how many were refused."""
    with (_dir(code) / "rejected.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "word": word, "take": take, "reason": reason}) + "\n")


def rejected(code: str) -> list[dict]:
    try:
        return [json.loads(ln) for ln in (_dir(code) / "rejected.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return []


def add_skip(code: str, word: str, phone: str, reason: str) -> dict:
    """The participant could not or would not say this word: the take is recorded as skipped (no audio), so the session can go on and the gap is reported."""
    return add_take(code, word, phone, None, {"problem": reason}, {"color": None, "notice": f"skipped: {reason}", "skipped": True})


def delete_participant(code: str) -> None:
    """Remove everything kept for a participant (the right to have the data deleted)."""
    import shutil
    d = _dir(code)
    if d.exists() and d.parent == root():
        shutil.rmtree(d)
    f = root() / "labels.jsonl"
    if f.exists():
        keep = [ln for ln in f.read_text(encoding="utf-8").splitlines() if not json.loads(ln)["take_id"].startswith(clean_code(code) + "_")]
        f.write_text("".join(ln + "\n" for ln in keep), encoding="utf-8")


# ---- labels (ratings by teachers) ----

def add_label(take_id: str, rater: str, label: str, unsure: bool = False, note: str = "") -> None:
    if label not in LABELS:
        raise ValueError("Unknown label.")
    root().mkdir(parents=True, exist_ok=True)
    line = {"take_id": take_id, "rater": clean_code(rater), "label": label, "unsure": bool(unsure), "note": note[:200], "time": datetime.now().isoformat(timespec="seconds")}
    with (root() / "labels.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def labels() -> dict[tuple[str, str], dict]:
    """{(take_id, rater): label line}, the last rating of a rater on a take wins."""
    out: dict[tuple[str, str], dict] = {}
    try:
        for ln in (root() / "labels.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(ln)
                out[(d["take_id"], d["rater"])] = d
            except (ValueError, KeyError):
                pass
    except OSError:
        pass
    return out


def all_takes() -> list[dict]:
    return [t for c in participants() for t in takes(c)]


def to_label(t: dict) -> str:
    return APP_LABEL.get(t.get("app", {}).get("color"), "not scored")


def kappa(pairs: list[tuple[str, str]], cats: tuple[str, ...] = LABELS, weighted: bool = False) -> float | None:
    """Cohen's kappa (linear weights when weighted) of two raters' labels on the same items. None when it cannot be computed."""
    pairs = [(a, b) for a, b in pairs if a in cats and b in cats]
    n = len(pairs)
    if n < 2:
        return None
    k = len(cats)
    idx = {c: i for i, c in enumerate(cats)}
    w = lambda i, j: (1 - abs(i - j) / (k - 1)) if weighted else float(i == j)
    po = sum(w(idx[a], idx[b]) for a, b in pairs) / n
    pa = [sum(1 for a, _ in pairs if idx[a] == i) / n for i in range(k)]
    pb = [sum(1 for _, b in pairs if idx[b] == j) / n for j in range(k)]
    pe = sum(w(i, j) * pa[i] * pb[j] for i in range(k) for j in range(k))
    return None if pe == 1 else (po - pe) / (1 - pe)


def disagreements() -> list[dict]:
    """Takes on which the app (when it scored) and a rater differ, or two raters differ, for the people who analyse the data (not shown while rating)."""
    L = labels()
    by_take = {t["take_id"]: t for t in all_takes()}
    rows = []
    for tid in sorted({t for t, _ in L}):
        t = by_take.get(tid)
        if not t:
            continue
        ratings = {r: d["label"] for (x, r), d in L.items() if x == tid}
        app = to_label(t)
        diff = len(set(ratings.values())) > 1 or (app in LABELS and any(v != app for v in ratings.values()))
        if diff:
            rows.append({"take_id": tid, "word": t["word"], "app": app, **{f"rater {r}": v for r, v in ratings.items()}})
    return rows


def agreement() -> dict:
    """App against each rater, and rater against rater, over the takes that have a rating. The app's 'not scored' is counted separately (never dropped silently)."""
    L = labels()
    by_take = {t["take_id"]: t for t in all_takes()}
    raters = sorted({r for _, r in L})
    out: dict = {"raters": raters, "n_takes_rated": len({tid for tid, _ in L}), "app_vs_rater": {}, "rater_vs_rater": {}}
    for r in raters:
        items = [(by_take[tid], d["label"]) for (tid, rr), d in L.items() if rr == r and tid in by_take]
        scored = [(to_label(t), lab) for t, lab in items if to_label(t) != "not scored"]
        out["app_vs_rater"][r] = {"n": len(items), "not_scored": len(items) - len(scored), "exact": (sum(a == b for a, b in scored) / len(scored)) if scored else None,
                                  "kappa": kappa(scored), "weighted_kappa": kappa(scored, weighted=True),
                                  "confusion": {a: {b: sum(1 for x, y in scored if x == a and y == b) for b in LABELS} for a in LABELS}}
    for i, r1 in enumerate(raters):
        for r2 in raters[i + 1:]:
            common = [(L[(tid, r1)]["label"], L[(tid, r2)]["label"]) for tid in {t for t, _ in L} if (tid, r1) in L and (tid, r2) in L]
            out["rater_vs_rater"][f"{r1} vs {r2}"] = {"n": len(common), "exact": (sum(a == b for a, b in common) / len(common)) if common else None,
                                                     "kappa": kappa(common), "weighted_kappa": kappa(common, weighted=True)}
    return out


def export_zip(codes: list[str] | None = None) -> bytes:
    """A zip of everything kept for the given participants (all when None), the labels, and a flat CSV of takes with the ratings, ready to hand to the research team."""
    import csv
    codes = codes or participants()
    buf = io.BytesIO()
    L = labels()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        rows = []
        for c in codes:
            d = _dir(c)
            for f in d.rglob("*"):
                if f.is_file():
                    z.write(f, f"{c}/{f.relative_to(d)}")
            for t in takes(c):
                a = t.get("app", {})
                s = session(c) or {}
                r = {"take_id": t["take_id"], "code": c, "age_group": s.get("age_group"), "hearing": s.get("hearing"), "first_language": s.get("first_language"),
                     "microphone": s.get("microphone"), "room": s.get("room"), "word": t["word"], "take": t["take"], "audio": t.get("audio") or "", "app_label": to_label(t), "app_closeness": a.get("closeness"),
                     "app_cog_hz": a.get("cog_hz"), "app_heard": a.get("heard"), "quality_problem": t.get("quality", {}).get("problem") or "ok",
                     "snr_db": t.get("quality", {}).get("snr_db"), "level_dbfs": t.get("quality", {}).get("level_dbfs")}
                for rater in sorted({rr for (tid, rr) in L if tid == t["take_id"]}):
                    r[f"rating_{rater}"] = L[(t["take_id"], rater)]["label"]
                rows.append(r)
        if rows:
            cols = list(dict.fromkeys(k for r in rows for k in r))
            s = io.StringIO()
            w = csv.DictWriter(s, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
            z.writestr("takes_with_ratings.csv", s.getvalue())
        lf = root() / "labels.jsonl"
        if lf.exists():
            z.write(lf, "labels.jsonl")
        z.writestr("agreement.json", json.dumps(agreement(), ensure_ascii=False, indent=1))
    return buf.getvalue()


def import_zip(data: bytes) -> dict:
    """Merge a zip made by export_zip on another computer. A participant code that already exists here is NOT overwritten (reported as skipped), so two
    children can never be mixed under one code; ratings are added when the same line is not already there. Returns {"added": [...], "skipped": [...], "labels_added": n}."""
    added, skipped, n_labels = [], [], 0
    z = zipfile.ZipFile(io.BytesIO(data))
    codes = sorted({n.split("/")[0] for n in z.namelist() if "/" in n and n.split("/")[0] and clean_code(n.split("/")[0]) == n.split("/")[0] and n.split("/")[0] != "agreement.json"})
    for c in codes:
        if not any(n == f"{c}/session.json" for n in z.namelist()):
            continue
        if (_dir(c) / "session.json").exists():
            skipped.append(c)
            continue
        for n in z.namelist():
            if n.startswith(c + "/") and not n.endswith("/") and ".." not in n:
                dest = root() / n
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(n))
        added.append(c)
    if "labels.jsonl" in z.namelist():
        have = set()
        f = root() / "labels.jsonl"
        if f.exists():
            have = set(f.read_text(encoding="utf-8").splitlines())
        new = [ln for ln in z.read("labels.jsonl").decode("utf-8").splitlines() if ln and ln not in have]
        if new:
            root().mkdir(parents=True, exist_ok=True)
            with f.open("a", encoding="utf-8") as fh:
                fh.write("".join(ln + "\n" for ln in new))
        n_labels = len(new)
    return {"added": added, "skipped": skipped, "labels_added": n_labels}


def delete_last_take(code: str) -> dict | None:
    """Undo the last take of a participant (a cough, a wrong word): removes its line, its audio and any rating of it. Returns the removed take, or None."""
    f = _dir(code) / "takes.jsonl"
    try:
        lines = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return None
    if not lines:
        return None
    last = json.loads(lines[-1])
    f.write_text("".join(ln + "\n" for ln in lines[:-1]), encoding="utf-8")
    if last.get("audio"):
        (_dir(code) / last["audio"]).unlink(missing_ok=True)
    lf = root() / "labels.jsonl"
    if lf.exists():
        keep = [ln for ln in lf.read_text(encoding="utf-8").splitlines() if ln and json.loads(ln)["take_id"] != last["take_id"]]
        lf.write_text("".join(ln + "\n" for ln in keep), encoding="utf-8")
    return last
