from dataclasses import replace

import pytest

from fricative.audio import load
from fricative.classify import classify
from fricative.config import DEFAULT_THRESHOLDS
from fricative.measure import Measures, measure
from fricative.reference import load_reference
from fricative.segment import find_boundaries


def M(cog, relamp):
    return Measures(onset_s=0.03, offset_s=0.2, cog_hz=cog, relamp_db=relamp, fm_hz=5000, duration_ms=170)


@pytest.mark.parametrize("cog,relamp,target,color,heard", [
    (6000, -3, "s", "green", "s"),
    (4500, -3, "s", "yellow", "s"),     # close to the CoG threshold
    (6000, -13, "s", "yellow", "s"),    # close to the relative-amplitude threshold
    (3000, -3, "s", "red", "sh"),
    (3000, -5, "sh", "green", "sh"),
    (4200, -5, "sh", "yellow", "sh"),
    (6000, -2, "sh", "red", "s"),
    (6000, -25, "f", "green", "f"),
    (6000, -16, "f", "yellow", "f"),
    (6000, -25, "s", "red", "f"),
    (6000, -3, "f", "red", "s"),
])
def test_rules(cog, relamp, target, color, heard):
    v = classify(M(cog, relamp), target)
    assert (v.color, v.heard) == (color, heard)
    assert v.target == target
    assert v.message.startswith("You said /")
    assert v.tip


def test_labels_and_marks():
    assert classify(M(6000, -3), "s").label == "Correct"
    assert classify(M(4500, -3), "s").label == "Almost"
    assert classify(M(3000, -3), "s").label == "Not yet"
    assert [classify(M(c, -3), "s").mark for c in (6000, 4500, 3000)] == ["◯", "△", "✕"]


def test_custom_thresholds_change_result():
    th = replace(DEFAULT_THRESHOLDS, cog_s_sh_hz=4000.0)
    assert classify(M(4500, -3), "s").color == "yellow"
    assert classify(M(4500, -3), "s", th).color == "green"
    zero_margin = replace(DEFAULT_THRESHOLDS, cog_margin_hz=0.0, relamp_margin_db=0.0)
    assert classify(M(4341, -14), "s", zero_margin).color == "green"


def test_no_vowel_scores_sibilants_and_adds_note():
    v = classify(M(6000, None), "s")
    assert (v.color, v.heard) == ("green", "s")
    assert v.note and "/f/" in v.note
    assert classify(M(6000, None), "f").color == "red"


@pytest.mark.parametrize("row", load_reference(), ids=lambda r: r.file)
def test_d1_end_to_end_is_green(row):
    snd = load(row.path)
    b = find_boundaries(snd)
    v = classify(measure(snd, b.onset_s, b.offset_s, b.found_vowel), row.phone)
    assert (v.heard, v.color) == (row.phone, "green")
