import pytest

from fricative.ablation import cog_ablation, segmentation_ablation
from fricative.audio import load
from fricative.config import DEFAULT_THRESHOLDS
from fricative.reference import load_reference

D1 = {r.file: r for r in load_reference()}


def test_segmentation_ablation_rows_with_manual_reference():
    r = D1["See - US.mp3"]
    rows = segmentation_ablation(load(r.path), "s", DEFAULT_THRESHOLDS, manual=(r.start_s, r.end_s))
    assert [row.key for row in rows] == ["anchored", "energy_pitch_v1", "band_ratio", "zcr", "frame_cog"]
    current = rows[0]
    assert current.error is None
    assert abs(current.onset_err_ms) < 20 and abs(current.offset_err_ms) < 20
    assert current.mark == "◯" and current.heard == "s"
    failed = rows[2]
    assert failed.error and "too short" in failed.error
    assert failed.onset_s is None and failed.cog_hz is None and failed.mark is None


def test_segmentation_ablation_without_manual_has_no_errors_columns():
    r = D1["She - UK.mp3"]
    rows = segmentation_ablation(load(r.path), "sh", DEFAULT_THRESHOLDS)
    assert all(row.onset_err_ms is None and row.offset_err_ms is None for row in rows)
    assert rows[0].heard == "sh"


def test_cog_ablation_variants_on_manual_boundaries():
    r = D1["See - UK.mp3"]
    variants = dict(cog_ablation(load(r.path), r.start_s, r.end_s))
    assert list(variants) == [
        "Rectangular, 0 Hz–Nyquist (current)",
        "Hanning",
        "Multitaper (NW = 4)",
        "Rectangular, 0–12 kHz",
        "Rectangular, 1–11 kHz",
    ]
    assert variants["Rectangular, 0 Hz–Nyquist (current)"] == pytest.approx(r.manual_cog_hz, abs=5)
    assert variants["Hanning"] == pytest.approx(6593, abs=30)
    assert variants["Rectangular, 0–12 kHz"] == pytest.approx(6192, abs=15)
    assert variants["Rectangular, 1–11 kHz"] == pytest.approx(6126, abs=15)


def _row(key, name, on=None, off=None, error=None):
    from fricative.ablation import SegRow
    return SegRow(key, name, onset_s=on, offset_s=off, error=error)


def test_summary_compares_with_current_detector_when_no_manual():
    from fricative.ablation import summarize_segmentation
    rows = [
        _row("anchored", "Current", 0.596, 0.705),
        _row("energy_pitch_v1", "V1", 0.072, 0.705),
        _row("band_ratio", "Ratio", error="Frication too short (< 30 ms)"),
        _row("zcr", "ZCR", 0.660, 0.712),
        _row("frame_cog", "CoG", 0.600, 0.708),
    ]
    lines = summarize_segmentation(rows)
    text = " ".join(lines)
    assert "compared with the current detector" in lines[0]
    assert "V1 starts 524 ms earlier" in text
    assert "Ratio failed" in text
    assert "ZCR starts 64 ms later" in text
    assert "CoG agrees" in text


def test_summary_compares_with_manual_when_available():
    from fricative.ablation import summarize_segmentation
    rows = [_row("anchored", "Current", 0.014, 0.220), _row("zcr", "ZCR", 0.024, 0.220)]
    lines = summarize_segmentation(rows, manual=(0.031, 0.221))
    assert "compared with the manual Praat boundaries" in lines[0]
    assert any(l.startswith("Current agrees (onset -17 ms") for l in lines)
    assert any(l.startswith("ZCR agrees") for l in lines)


def test_summary_when_current_detector_failed():
    from fricative.ablation import summarize_segmentation
    rows = [_row("anchored", "Current", error="No frication found"), _row("zcr", "ZCR", 0.1, 0.2)]
    lines = summarize_segmentation(rows)
    assert "Current failed" in " ".join(lines)
    assert "spectrogram" in lines[0]


def test_summary_never_prints_negative_zero():
    from fricative.ablation import summarize_segmentation
    rows = [_row("anchored", "Current", 0.0304, 0.2206)]
    line = summarize_segmentation(rows, manual=(0.0306, 0.2208))[1]
    assert "-0 ms" not in line and "+0 ms" in line
