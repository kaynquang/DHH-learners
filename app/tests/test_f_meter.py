from learner import spectro


def test_meter_is_for_f_only():
    assert spectro.meter_levels("s", None) is None and spectro.meter_levels("b", None) is None


def test_default_meter_bands_follow_the_scoring_cue():
    m = spectro.meter_levels("f", None)
    assert m["default"] is True and m["ref"] == spectro.DEFAULT_REF_DB
    assert m["yellow_hi"] - m["ref"] == -15.0              # the /f/ threshold: hiss 15 dB under the vowel
    assert m["green_hi"] - m["ref"] == -18.0               # and its 3 dB margin
    assert m["green_lo"] < m["green_hi"] - 5               # room for a green band above the floor
