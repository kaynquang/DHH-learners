"""Needs torch, transformers and the wav2vec2 phoneme checkpoint (set W2V_DIR); skipped otherwise."""
import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")

from fricative.audio import load
from fricative.phoneme_check import GROUPS, available, check, first_consonant, model_dir
from fricative.reference import load_reference

pytestmark = pytest.mark.skipif(not available(), reason="phoneme checkpoint not found (set W2V_DIR)")
D1 = {r.file: r for r in load_reference()}


def run(name):
    r = D1[name]
    return check(load(r.path), r.start_s, r.end_s)


def test_groups_cover_the_four_sounds_and_the_retroflex_symbols_used_for_sh():
    assert set(GROUPS) == {"S", "SH", "F", "TH"}
    assert "s." in GROUPS["SH"] and "ʃ" in GROUPS["SH"] and "θ" in GROUPS["TH"]


@pytest.mark.parametrize("name,expected", [("See - UK.mp3", "S"), ("See - US.mp3", "S"), ("She - UK.mp3", "SH"), ("She - US.mp3", "SH"),
                                           ("Fee - UK.mp3", "F"), ("Fee - US.mp3", "F")])
def test_d1_isolated_words_are_heard_as_their_own_initial_sound(name, expected):
    pc = run(name)
    assert pc.heard == expected
    assert pc.masses[expected] == max(pc.masses.values())


def test_the_result_carries_what_the_page_needs_to_draw_it():
    pc = run("She - UK.mp3")
    assert pc.decoded and isinstance(pc.decoded, str)
    assert set(pc.track) == {"S", "SH", "F", "TH"}
    assert all(len(v) == len(pc.centres) for v in pc.track.values())
    a, b = pc.hiss_window
    assert 0 <= a < b <= pc.centres[-1] + 0.02


def test_silence_is_heard_as_nothing():
    import parselmouth
    pc = check(parselmouth.Sound(np.zeros(16000), sampling_frequency=16000), 0.3, 0.5)
    assert pc.heard is None


def test_model_dir_follows_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("W2V_DIR", str(tmp_path))
    assert model_dir() is None                # an empty folder is not a checkpoint


@pytest.mark.parametrize("name,expected", [("See - UK.mp3", "S"), ("She - US.mp3", "SH"), ("Fee - UK.mp3", "F")])
def test_first_consonant_of_the_d1_words(name, expected):
    assert first_consonant(load(D1[name].path)) == expected
