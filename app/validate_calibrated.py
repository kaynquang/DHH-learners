"""Validate the calibrated scoring on isolated-word recordings.

Name the files <speaker>_<word>_<n>.wav (or .mp3), with word one of see, she, fee and n = 1, 2, 3, ...
For every speaker the two lowest takes of each word calibrate the app (the same "see, she, fee, twice each" protocol the
Calibrate page uses); every other take is scored against the sound it was meant to be.

Usage: python app/validate_calibrated.py <folder> [--out results.csv]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

from fricative.audio import limit_duration, load
from fricative.calibrated import CAL_WORDS, build_calibration, load_model, read
from fricative.config import TARGETS
from fricative.patterns import extract
from fricative.segment import SegmentationError, find_boundaries

WORDS = ("see", "she", "fee")
K_CAL = CAL_WORDS.count("see")
AUDIO = {".wav", ".mp3"}
COLUMNS = ["speaker", "word", "take", "file", "heard", "p_s", "p_sh", "p_f", "color", "correct", "error"]


def parse_name(path) -> tuple[str, str, int]:
    name = Path(path).name
    m = re.fullmatch(r"(.+)_([A-Za-z]+)_(\d+)", Path(path).stem)
    if not m:
        raise ValueError(f"'{name}': expected <speaker>_<word>_<n>.wav")
    speaker, word, n = m.group(1), m.group(2).lower(), int(m.group(3))
    if word not in WORDS:
        raise ValueError(f"'{name}': the word must be one of {', '.join(WORDS)}")
    return speaker, word, n


def _features(path: Path):
    sound, _ = limit_duration(load(path))
    b = find_boundaries(sound)
    return extract(sound, b.onset_s, b.offset_s, b.found_vowel, with_f2=False)


def run(folder) -> tuple[list[dict], dict]:
    groups: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for p in sorted(Path(folder).iterdir()):
        if p.suffix.lower() in AUDIO:
            speaker, word, n = parse_name(p)
            groups[speaker][word].append((n, p))
    model, rows, summary = load_model(), [], {}
    for speaker, words in sorted(groups.items()):
        short = [w for w in WORDS if len(words[w]) < K_CAL]
        if short:
            summary[speaker] = {"n_scored": 0, "skipped": f"needs {K_CAL} takes of each word, missing: {', '.join(short)}"}
            continue
        takes = {w: sorted(words[w]) for w in WORDS}
        seen = defaultdict(int)
        cal_files = []
        for w in CAL_WORDS:
            cal_files.append(takes[w][seen[w]][1]); seen[w] += 1
        cal = build_calibration([_features(p) for p in cal_files])
        mine = []
        for w in WORDS:
            for n, p in takes[w][K_CAL:]:
                target = TARGETS[w]
                try:
                    rd = read(_features(p), cal, model, target)
                    row = dict(speaker=speaker, word=w, take=n, file=p.name, heard=rd.verdict.heard, p_s=round(rd.probs["s"], 3),
                               p_sh=round(rd.probs["sh"], 3), p_f=round(rd.probs["f"], 3), color=rd.verdict.color,
                               correct=rd.verdict.heard == target, error="")
                except (ValueError, SegmentationError) as exc:
                    row = dict(speaker=speaker, word=w, take=n, file=p.name, heard="", p_s="", p_sh="", p_f="", color="", correct=False, error=str(exc))
                mine.append(row)
        rows += mine
        per_word = {w: sum(r["correct"] for r in mine if r["word"] == w) / n_w for w in WORDS if (n_w := sum(r["word"] == w for r in mine))}
        summary[speaker] = {"n_scored": len(mine), "per_word": per_word, "three_way": sum(per_word.values()) / len(per_word) if per_word else None}
    scored = [s for s in summary.values() if s["n_scored"] > 0]
    summary["_all"] = {"speakers": len(scored), "n_scored": sum(s["n_scored"] for s in scored),
                       "three_way": sum(s["three_way"] for s in scored) / len(scored) if scored else None}
    return rows, summary


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", type=Path, help="write one row per scored recording to this CSV")
    args = ap.parse_args(argv)
    rows, summary = run(args.folder)
    for speaker, s in summary.items():
        if speaker == "_all":
            continue
        if s.get("skipped"):
            print(f"{speaker:12} skipped: {s['skipped']}")
        else:
            words = "  ".join(f"{w} {v:.0%}" for w, v in s.get("per_word", {}).items())
            print(f"{speaker:12} scored {s['n_scored']:3d}  balanced accuracy {s['three_way']:.0%}  ({words})" if s["n_scored"] else f"{speaker:12} nothing to score")
    a = summary["_all"]
    if a["speakers"]:
        print(f"\nAll speakers: {a['speakers']} speakers, {a['n_scored']} recordings, mean balanced accuracy {a['three_way']:.0%}")
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main(sys.argv[1:])
