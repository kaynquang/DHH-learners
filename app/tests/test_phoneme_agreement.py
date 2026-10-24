import pytest

from fricative.phoneme_check import agrees


@pytest.mark.parametrize("app,group,expected", [
    ("s", "S", True), ("s", "SH", False), ("sh", "SH", True), ("sh", "S", False),
    ("f", "F", True), ("f", "TH", True), ("f", "S", False), ("s", None, False)])
def test_agreement_between_the_app_and_the_recogniser(app, group, expected):
    assert agrees(app, group) is expected


@pytest.mark.parametrize("target,group,expected", [("p", "F", True), ("p", "B", False), ("s", "SH", False), ("s", "P", True),
                                                   ("b", None, False), ("f", "TH", False), ("sh", "M", True)])
def test_only_a_different_kind_of_sound_is_wrong(target, group, expected):
    from fricative.phoneme_check import wrong_kind
    assert wrong_kind(target, group) is expected


def test_recogniser_decides_the_sound_and_the_measure_decides_the_shade():
    from fricative.classify import Verdict
    from fricative.phoneme_check import reconcile
    v = lambda color, heard: Verdict(color, "x", "m", heard, "s", f"You said /{heard}/", "tip")
    assert reconcile(v("green", "s"), "SH").color == "red"        # recogniser hears /ʃ/ for target /s/
    assert reconcile(v("red", "sh"), "S").color == "yellow"       # recogniser hears /s/: thresholds alone are not trusted to say red
    assert reconcile(v("green", "s"), "S").color == "green"
    assert reconcile(v("yellow", "s"), "S").color == "yellow"
    assert reconcile(v("green", "s"), None).color == "green"
