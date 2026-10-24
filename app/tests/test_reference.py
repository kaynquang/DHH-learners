import pytest

from fricative.reference import load_reference


def test_loads_six_d1_rows():
    rows = load_reference()
    assert len(rows) == 6
    assert {r.phone for r in rows} == {"s", "sh", "f"}
    assert {r.accent for r in rows} == {"UK", "US"}
    for r in rows:
        assert r.path.exists(), r.path
        assert 0 < r.start_s < r.end_s < 1.0


def test_see_uk_values_are_in_seconds():
    see_uk = next(r for r in load_reference() if r.file == "See - UK.mp3")
    assert see_uk.start_s == pytest.approx(0.031050)
    assert see_uk.end_s == pytest.approx(0.220865)
    assert see_uk.manual_cog_hz == pytest.approx(6306.50)


def test_rejects_comma_decimal(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text(
        'file,phone,accent,start_s,end_s,manual_cog_hz\n'
        'See - UK.mp3,s,UK,"0,031050",0.220865,6306.50\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="decimal point"):
        load_reference(p)


def test_rejects_end_before_start(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text(
        "file,phone,accent,start_s,end_s,manual_cog_hz\n"
        "See - UK.mp3,s,UK,0.3,0.2,6306.50\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="end_s"):
        load_reference(p)


def test_articulation_images_exist_for_every_phone():
    from fricative.config import ARTICULATION_IMAGE, TARGETS
    assert set(ARTICULATION_IMAGE) == set(TARGETS.values())
    assert all(p.exists() for p in ARTICULATION_IMAGE.values())
