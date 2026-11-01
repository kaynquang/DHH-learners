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


def test_sounds_open_one_after_the_other():
    from learner.lessons import ORDER
    assert ORDER[:2] == ["she", "see"]
    none = {}
    assert stars.unlocked(none, ORDER[0]) and not any(stars.unlocked(none, w) for w in ORDER[1:])
    assert stars.frontier(none) == ORDER[0]
    one = {ORDER[0]: {"best": 1, "tries": 1}}                     # one star opens the next sound, even if it is not 3
    assert stars.unlocked(one, ORDER[1]) and not stars.unlocked(one, ORDER[2])
    assert stars.frontier(one) == ORDER[1]
    red = {ORDER[0]: {"best": 0, "tries": 4}}                     # tried, no star yet: still closed
    assert not stars.unlocked(red, ORDER[1]) and stars.frontier(red) == ORDER[0]
    every = {w: {"best": 1, "tries": 1} for w in ORDER}
    assert all(stars.unlocked(every, w) for w in ORDER) and stars.frontier(every) is None


def test_boy_or_girl_is_kept(tmp_path, monkeypatch):
    from learner import children
    monkeypatch.setattr(children, "_FILE", tmp_path / "_children.json")
    assert children.gender("Mia") is None
    children.set_gender("Mia", "girl")
    children.set_gender("Mia", "dragon")                          # not a choice: ignored
    assert children.gender("Mia") == "girl"
    children.forget("Mia")
    assert children.gender("Mia") is None
