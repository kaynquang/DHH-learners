import json

import pytest

from fricative import collect


@pytest.fixture(autouse=True)
def _tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("FRICATIVE_LOGS", str(tmp_path))


def test_code_is_not_a_name():
    assert collect.clean_code(" s 01!? ") == "S01"
    with pytest.raises(ValueError):
        collect.start_session("", ["she"], "KP", True)
    with pytest.raises(ValueError):
        collect.start_session("S01", ["she"], " ", True)


def test_session_runs_through_all_words_and_takes():
    collect.start_session("S01", ["she", "see"], "KP", True, takes_per_word=2)
    seen = []
    while (item := collect.next_item("S01")):
        seen.append(item)
        collect.add_take("S01", item[0], "sh", b"RIFFx", {"problem": None}, {"color": "green"})
    assert seen == [("she", 1), ("she", 2), ("see", 1), ("see", 2)]
    assert collect.session("S01")["audio_consent"] is True
    assert (collect.root() / "S01" / "audio" / "S01_she_1.wav").exists()


def test_no_audio_without_consent():
    collect.start_session("S02", ["she"], "KP", False, takes_per_word=1)
    t = collect.add_take("S02", "she", "sh", b"RIFFx", {}, {"color": "red"})
    assert t["audio"] is None and not (collect.root() / "S02" / "audio").exists()


def test_kappa_and_agreement():
    assert collect.kappa([("correct", "correct"), ("almost", "almost"), ("not yet", "not yet"), ("correct", "correct")]) == 1.0
    k = collect.kappa([("correct", "not yet"), ("not yet", "correct"), ("correct", "not yet"), ("not yet", "correct")])
    assert k is not None and k < 0
    assert collect.kappa([("correct", "correct")]) is None
    collect.start_session("S03", ["she"], "KP", True, takes_per_word=2)
    collect.add_take("S03", "she", "sh", b"x", {}, {"color": "green"})
    collect.add_take("S03", "she", "sh", b"x", {}, {"color": None, "notice": "no speech"})
    collect.add_label("S03_she_1", "AB", "correct")
    collect.add_label("S03_she_2", "AB", "not yet")
    collect.add_label("S03_she_1", "CD", "almost")
    a = collect.agreement()
    assert a["app_vs_rater"]["AB"]["n"] == 2 and a["app_vs_rater"]["AB"]["not_scored"] == 1 and a["app_vs_rater"]["AB"]["exact"] == 1.0
    assert a["rater_vs_rater"]["AB vs CD"]["n"] == 1


def test_export_and_delete():
    collect.start_session("S04", ["she"], "KP", True, takes_per_word=1)
    collect.add_take("S04", "she", "sh", b"x", {}, {"color": "yellow"})
    collect.add_label("S04_she_1", "AB", "almost")
    import io, zipfile
    z = zipfile.ZipFile(io.BytesIO(collect.export_zip()))
    names = z.namelist()
    assert "takes_with_ratings.csv" in names and "S04/session.json" in names and "agreement.json" in names
    assert "rating_AB" in z.read("takes_with_ratings.csv").decode()
    collect.delete_participant("S04")
    assert collect.participants() == [] and collect.labels() == {}


def test_import_merges_without_overwriting(tmp_path, monkeypatch):
    collect.start_session("S01", ["she"], "KP", True, takes_per_word=1)
    collect.add_take("S01", "she", "sh", b"x", {}, {"color": "green"})
    collect.add_label("S01_she_1", "AB", "correct")
    data = collect.export_zip()
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("FRICATIVE_LOGS", str(other))
    collect.start_session("S01", ["see"], "XX", True, takes_per_word=1)          # a different child already has this code here
    collect.start_session("S02", ["she"], "KP", True, takes_per_word=1)
    res = collect.import_zip(data)
    assert res["skipped"] == ["S01"] and res["added"] == [] and res["labels_added"] == 1
    assert collect.session("S01")["words"] == ["see"]                             # not overwritten
    assert collect.import_zip(data)["labels_added"] == 0                          # ratings are not duplicated


def test_undo_last_take_removes_audio_and_rating():
    collect.start_session("S05", ["she"], "KP", True, takes_per_word=2)
    collect.add_take("S05", "she", "sh", b"x", {}, {"color": "green"})
    collect.add_take("S05", "she", "sh", b"x", {}, {"color": "red"})
    collect.add_label("S05_she_2", "AB", "not yet")
    assert collect.next_item("S05") is None
    gone = collect.delete_last_take("S05")
    assert gone["take_id"] == "S05_she_2" and collect.next_item("S05") == ("she", 2)
    assert not (collect.root() / "S05" / "audio" / "S05_she_2.wav").exists() and collect.labels() == {}
    assert collect.delete_last_take("NONE") is None


def test_rejected_skip_and_disagreements():
    collect.start_session("S06", ["she", "see"], "KP", True, takes_per_word=1)
    collect.add_rejected("S06", "she", 1, "quiet")
    collect.add_skip("S06", "she", "sh", "quiet x3")
    assert collect.rejected("S06")[0]["reason"] == "quiet" and collect.next_item("S06") == ("see", 1)
    collect.add_take("S06", "see", "s", b"x", {}, {"color": "green"})
    collect.add_label("S06_see_1", "AB", "correct")
    collect.add_label("S06_see_1", "CD", "almost")
    assert collect.disagreements() == [{"take_id": "S06_see_1", "word": "see", "app": "correct", "rater AB": "correct", "rater CD": "almost"}]
    assert collect.to_label(collect.takes("S06")[0]) == "not scored"
