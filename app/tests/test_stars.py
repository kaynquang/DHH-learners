from learner import stars


def test_star_rule():
    assert stars.stars("green", 0.95) == 3
    assert stars.stars("yellow", 0.78) == 2          # yellow near green
    assert stars.stars("yellow", 0.52) == 1          # yellow near red
    assert stars.stars("red", 0.2) == 0
    assert stars.stars(None, None) is None


def test_progress_keeps_the_best(tmp_path, monkeypatch):
    monkeypatch.setattr(stars, "PROFILES_DIR", tmp_path)
    assert stars.record("kid", "see", 1) is True              # first try
    assert stars.record("kid", "see", 0) is False             # worse: nothing changes for the child
    assert stars.record("kid", "see", 3) is True
    assert stars.load("kid")["see"] == {"best": 3, "tries": 3}
    assert stars.total("kid") == 3
    assert stars.status(stars.load("kid"), "see") == "done"
    assert stars.status(stars.load("kid"), "she") == "not started"
    stars.record("kid", "she", 2)
    assert stars.status(stars.load("kid"), "she") == "in progress"
    stars.forget("kid")
    assert stars.load("kid") == {}
    assert stars.record(None, "see", 3) is False
