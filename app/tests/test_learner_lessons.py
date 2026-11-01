"""The learners' lesson content: every picture a lesson points to exists, and the steps of a lesson are complete."""
import pytest

from learner.lessons import LESSONS, ORDER


def test_every_lesson_word_is_one_of_the_eight_sounds():
    assert len(ORDER) == 8 and set(ORDER) == set(LESSONS)


@pytest.mark.parametrize("word", ORDER)
def test_pictures_exist(word):
    lesson = LESSONS[word]
    if lesson.mouth_image:
        assert lesson.mouth_image.exists()
    for step in lesson.steps:
        assert step.image.exists()


def test_me_is_made_of_three_steps_with_the_same_picture_size():
    from PIL import Image
    steps = LESSONS["me"].steps
    assert len(steps) == 3
    assert len({Image.open(s.image).size for s in steps}) == 1          # the steps change without the picture jumping
    for step in steps:
        assert step.seconds > 0 and len(step.checks) == 3
        assert all(len(c) == 3 and all(c) for c in step.checks)         # English, Chinese and pinyin


@pytest.mark.parametrize("word", ORDER)
def test_motions_stay_inside_their_picture(word):
    from PIL import Image
    lesson = LESSONS[word]
    if not lesson.motions:
        return
    w, h = Image.open(lesson.mouth_image).size
    for m in lesson.motions:
        cx, cy, rx, ry = m.spot
        assert 0 <= cx <= w and 0 <= cy <= h
        for s in m.shapes:
            if s["type"] == "ring":
                assert 0 <= s["cx"] <= w and 0 <= s["cy"] <= h
