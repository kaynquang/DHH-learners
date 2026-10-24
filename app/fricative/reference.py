"""D1 reference set: manual boundaries and CoG (boundaries.csv)."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUNDS_DIR = REPO_ROOT / "SOUNDS"
BOUNDARIES_CSV = REPO_ROOT / "boundaries.csv"


@dataclass(frozen=True)
class RefRow:
    file: str
    phone: str
    accent: str
    start_s: float
    end_s: float
    manual_cog_hz: float

    @property
    def path(self) -> Path:
        return SOUNDS_DIR / self.file


def _num(value: str, field: str, line: int) -> float:
    if "," in value:
        raise ValueError(
            f"boundaries.csv line {line}, column {field}: '{value}' uses a comma; "
            "use a decimal point"
        )
    return float(value)


def available() -> bool:
    """True when the D1 dictionary recordings and their manual boundaries are present (they are not part of the public repository)."""
    return BOUNDARIES_CSV.exists() and SOUNDS_DIR.is_dir()


def load_reference(csv_path: Path = BOUNDARIES_CSV) -> list[RefRow]:
    """D1 rows; an empty list when the default D1 files are absent."""
    if csv_path == BOUNDARIES_CSV and not available():
        return []
    rows: list[RefRow] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for line, r in enumerate(csv.DictReader(fh), start=2):
            row = RefRow(
                file=r["file"],
                phone=r["phone"],
                accent=r["accent"],
                start_s=_num(r["start_s"], "start_s", line),
                end_s=_num(r["end_s"], "end_s", line),
                manual_cog_hz=_num(r["manual_cog_hz"], "manual_cog_hz", line),
            )
            if row.end_s <= row.start_s:
                raise ValueError(f"boundaries.csv line {line}: end_s must be greater than start_s")
            rows.append(row)
    return rows


def measure_reference(rows: list[RefRow] | None = None):
    """Measure D1 on the manual boundaries. Returns list[(RefRow, Measures)]."""
    from .audio import load
    from .measure import measure

    rows = rows if rows is not None else load_reference()
    return [(r, measure(load(r.path), r.start_s, r.end_s)) for r in rows]
