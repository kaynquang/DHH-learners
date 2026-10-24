import pytest

from fricative.nasals import classify_nasal


@pytest.mark.parametrize("p_m,target,color", [(0.95, "m", "green"), (0.65, "m", "yellow"), (0.2, "m", "red"),
                                              (0.03, "n", "green"), (0.4, "n", "yellow"), (0.9, "n", "red")])
def test_verdict_colours(p_m, target, color):
    assert classify_nasal(p_m, target).color == color


def test_no_nasal_heard_gives_no_verdict():
    assert classify_nasal(None, "m") is None
