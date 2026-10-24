import csv
import shutil

import pytest

from fricative.reference import SOUNDS_DIR
from validate_calibrated import parse_name, run


def make_folder(tmp_path, speakers=("uk",), copies=4):
    """D1 has one recording per word and voice, so each is copied `copies` times as <speaker>_<word>_<n>.mp3."""
    for spk in speakers:
        for w in ("see", "she", "fee"):
            for n in range(1, copies + 1):
                shutil.copy(SOUNDS_DIR / f"{w.capitalize()} - UK.mp3", tmp_path / f"{spk}_{w}_{n}.mp3")
    return tmp_path


def test_parse_name_reads_speaker_word_and_take():
    assert parse_name("S01_see_3.wav") == ("S01", "see", 3)
    assert parse_name("/some/dir/anna_fee_12.mp3") == ("anna", "fee", 12)
    with pytest.raises(ValueError, match="<speaker>_<word>_<n>"):
        parse_name("recording.wav")
    with pytest.raises(ValueError, match="word"):
        parse_name("S01_cat_1.wav")


def test_first_two_takes_calibrate_and_the_rest_are_scored(tmp_path):
    rows, summary = run(make_folder(tmp_path, copies=4))
    assert len(rows) == 6                                    # takes 3 and 4 of three words
    assert {r["take"] for r in rows} == {3, 4}
    assert all(r["correct"] for r in rows)
    assert summary["uk"]["three_way"] == pytest.approx(1.0)
    assert summary["_all"]["n_scored"] == 6 and summary["_all"]["speakers"] == 1


def test_speakers_are_calibrated_separately(tmp_path):
    rows, summary = run(make_folder(tmp_path, speakers=("a", "b"), copies=3))
    assert {r["speaker"] for r in rows} == {"a", "b"} and len(rows) == 6
    assert summary["_all"]["speakers"] == 2


def test_a_speaker_with_too_few_takes_is_reported_not_crashed(tmp_path):
    folder = make_folder(tmp_path, copies=2)                 # only calibration takes, nothing to score
    rows, summary = run(folder)
    assert rows == [] and "uk" in summary and summary["uk"]["n_scored"] == 0
    shutil.copy(SOUNDS_DIR / "Fee - UK.mp3", folder / "x_fee_1.mp3")
    rows, summary = run(folder)
    assert summary["x"]["skipped"].startswith("needs")


def test_cli_writes_a_csv(tmp_path):
    from validate_calibrated import main
    out = tmp_path / "out.csv"
    main([str(make_folder(tmp_path, copies=3)), "--out", str(out)])
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 3 and {"speaker", "word", "take", "heard", "p_s", "p_sh", "p_f", "correct"} <= set(rows[0])
