import csv

from measure_dataset import FIELDS, run


def test_run_writes_six_rows_matching_manual(tmp_path):
    out = tmp_path / "measurements_auto.csv"
    rows = run(out)
    assert len(rows) == 6
    for row in rows:
        assert abs(row["diff_hz"]) < 5
        assert abs(row["onset_err_ms"]) < 20
        assert abs(row["offset_err_ms"]) < 20
    with open(out, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == FIELDS
        first = next(reader)
    assert "," not in first["diff_hz"]
    float(first["diff_hz"])


def test_measure_reference_returns_pairs():
    from fricative.reference import measure_reference
    pairs = measure_reference()
    assert len(pairs) == 6
    r, m = pairs[0]
    assert abs(m.cog_hz - r.manual_cog_hz) < 5
