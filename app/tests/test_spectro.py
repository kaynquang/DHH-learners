from learner import spectro


def test_zones_follow_the_scoring_threshold():
    z = spectro.zones("s")
    assert (z["lo"], z["hi"]) == (4040.0, 4640.0)            # the /s/-/ʃ/ boundary 4340 Hz and its 300 Hz margin
    assert z["target"] == "s" and spectro.zones("sh")["target"] == "sh"
    assert spectro.zones("b") is None                         # no picture yet for the other sounds


def test_no_picture_for_a_sound_without_zones():
    assert spectro.render(b"", "b") is None


def test_the_live_dot_has_its_own_zones():
    z = spectro.zones("sh", live=True)
    assert (z["lo"], z["hi"]) == (3940.0, 4540.0) and (z["f_lo"], z["f_hi"]) == (2000.0, 8000.0)       # the dot's own limit, from ARCTIC measured the dot's way
    assert spectro.zones("sh", 1.1, live=True)["lo"] == 3940.0 * 1.1                                      # the child's voice size moves it the same way
    assert spectro.zones("sh")["lo"] == 4040.0                                                            # the picture after the recording keeps the scoring's zones
