"""Run the D1 set: measure with code, compare with the manual values, write measurements_auto.csv.

Usage: python app/measure_dataset.py [--out path.csv]
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from fricative.audio import load
from fricative.measure import measure
from fricative.reference import REPO_ROOT, load_reference
from fricative.segment import SegmentationError, find_boundaries

FIELDS = [
    "file", "phone", "accent", "manual_cog_hz", "cog_manual_bounds_hz", "diff_hz",
    "relamp_db", "fm_hz", "auto_onset_s", "auto_offset_s", "onset_err_ms", "offset_err_ms",
    "cog_auto_bounds_hz",
]


def run(out_path: Path) -> list[dict]:
    rows = []
    for r in load_reference():
        sound = load(r.path)
        man = measure(sound, r.start_s, r.end_s)
        row = {
            "file": r.file, "phone": r.phone, "accent": r.accent,
            "manual_cog_hz": r.manual_cog_hz,
            "cog_manual_bounds_hz": round(man.cog_hz, 2),
            "diff_hz": round(man.cog_hz - r.manual_cog_hz, 2),
            "relamp_db": round(man.relamp_db, 2),
            "fm_hz": round(man.fm_hz, 1),
            "auto_onset_s": "", "auto_offset_s": "", "onset_err_ms": "", "offset_err_ms": "",
            "cog_auto_bounds_hz": "",
        }
        try:
            b = find_boundaries(sound)
            auto = measure(sound, b.onset_s, b.offset_s, b.found_vowel)
            row.update(
                auto_onset_s=round(b.onset_s, 4), auto_offset_s=round(b.offset_s, 4),
                onset_err_ms=round((b.onset_s - r.start_s) * 1000, 1),
                offset_err_ms=round((b.offset_s - r.end_s) * 1000, 1),
                cog_auto_bounds_hz=round(auto.cog_hz, 2),
            )
        except SegmentationError:
            pass
        rows.append(row)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "measurements_auto.csv")
    args = parser.parse_args()
    for row in run(args.out):
        print(f"{row['file']:14} manual {row['manual_cog_hz']:8.1f}  code {row['cog_manual_bounds_hz']:8.1f}  "
              f"diff {row['diff_hz']:+6.2f} Hz  onset {row['onset_err_ms']} ms  offset {row['offset_err_ms']} ms")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
