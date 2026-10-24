import numpy as np
import pytest

from fricative.audio import load
from fricative.calibrated import CAL_WORDS, Calibration, build_calibration, load_model, read, standardise
from fricative.patterns import SCALAR_KEYS, extract
from fricative.reference import load_reference

D1 = {r.file: r for r in load_reference()}
MODEL = load_model()


def feats(name, has_vowel=True, with_f2=False):
    r = D1[name]
    return extract(load(r.path), r.start_s, r.end_s, has_vowel, 5000.0, with_f2=with_f2)


def protocol_tokens(accent):
    """The six calibration recordings of one D1 voice: see, she, fee twice (the same file, as only one exists)."""
    return [feats(f"{w.capitalize()} - {accent}.mp3") for w in CAL_WORDS]


def test_calibration_protocol_is_see_she_fee_twice():
    assert CAL_WORDS == ("see", "she", "fee", "see", "she", "fee")


def test_model_file_has_three_models_and_its_own_accuracy():
    assert MODEL["meta"]["features"] == SCALAR_KEYS
    assert len(MODEL["sibilant"]["coef"]) == 13 and MODEL["sibilant"]["positive"] == "SH"
    assert MODEL["family"]["features"] == ["relamp", "contrast", "wobble", "sd"] and len(MODEL["family"]["coef"]) == 4
    assert MODEL["family_novowel"]["features"] == ["contrast", "wobble", "sd"]
    loo = MODEL["meta"]["leave_one_voice_out"]
    assert loo["three_way"]["mean"] > 0.88 and loo["s_vs_sh_if_sibilant"]["mean"] > 0.92
    assert MODEL["meta"]["calibration_tokens"] == 6


def test_extract_can_skip_the_f2_analysis_without_changing_other_features():
    a, b = feats("See - UK.mp3", with_f2=False), feats("See - UK.mp3", with_f2=True)
    assert np.isnan(a.f2).all() and not np.isnan(b.f2).any()
    assert a.scalars == pytest.approx(b.scalars, nan_ok=True)


def test_build_calibration_needs_at_least_three_recordings():
    with pytest.raises(ValueError, match="at least 3"):
        build_calibration(protocol_tokens("UK")[:2])


def test_calibration_statistics_are_finite_and_nonzero():
    cal = build_calibration(protocol_tokens("UK"))
    assert isinstance(cal, Calibration) and cal.n_tokens == 6
    assert cal.mu.shape == cal.sd.shape == (13,)
    assert np.isfinite(cal.mu).all() and (cal.sd > 0).all()


def test_standardise_centres_the_calibration_tokens_and_reports_missing_features():
    toks = protocol_tokens("UK")
    cal = build_calibration(toks)
    z = np.stack([standardise(t, cal)[0] for t in toks])
    assert np.abs(z.mean(axis=0)).max() < 1e-6
    _, missing = standardise(feats("See - UK.mp3", has_vowel=False), cal)
    assert missing == ["relamp"]


@pytest.mark.parametrize("accent", ["UK", "US"])
@pytest.mark.parametrize("word,target", [("See", "s"), ("She", "sh"), ("Fee", "f")])
def test_each_d1_word_is_read_as_its_own_sound_after_calibrating_on_that_voice(accent, word, target):
    cal = build_calibration(protocol_tokens(accent))
    rd = read(feats(f"{word} - {accent}.mp3"), cal, MODEL, target)
    assert rd.verdict.heard == target and rd.verdict.color in ("green", "yellow")
    assert sum(rd.probs.values()) == pytest.approx(1.0)
    assert rd.probs[target] == max(rd.probs.values())


def test_a_wrong_target_is_red_and_carries_the_tip_for_the_target():
    cal = build_calibration(protocol_tokens("UK"))
    rd = read(feats("She - UK.mp3"), cal, MODEL, "s")
    assert rd.verdict.color == "red" and rd.verdict.heard == "sh" and rd.verdict.target == "s"
    assert rd.verdict.message == "You said /ʃ/" and rd.verdict.tip


def test_missing_vowel_uses_the_spectral_only_family_model_and_says_so():
    cal = build_calibration(protocol_tokens("UK"))
    rd = read(feats("See - UK.mp3", has_vowel=False), cal, MODEL, "s")
    assert "relamp" in rd.missing and rd.verdict.note and "No vowel" in rd.verdict.note
    assert rd.verdict.heard == "s"
