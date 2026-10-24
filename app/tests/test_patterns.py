from dataclasses import replace

import numpy as np
import pytest

from fricative.audio import load
from fricative.measure import measure
from fricative.patterns import (SCALAR_KEYS, experimental_verdict, extract, load_reference, percentiles)
from fricative.reference import load_reference as load_d1

D1 = {r.file: r for r in load_d1()}
REF = load_reference()


def feats(name, has_vowel=True, voice="slt"):
    r = D1[name]
    return extract(load(r.path), r.start_s, r.end_s, has_vowel, REF["voices"][voice]["max_formant_hz"])


def test_reference_file_has_both_voices_and_every_phone():
    assert REF["meta"]["tokens"] == 2148
    assert list(REF["voices"]) == ["bdl", "slt"]
    for voice in REF["voices"].values():
        assert set(voice["phones"]) == {"S", "SH", "F", "TH", "Z"}
        for ph in voice["phones"].values():
            assert set(ph["q"]) == set(SCALAR_KEYS)
            assert all(np.all(np.diff(q) >= 0) and len(q) == 5 for q in ph["q"].values())
            assert len(ph["shape_mean"]) == len(ph["shape_sd"]) == 40
            assert len(ph["traj_mean"]) == 5 and len(ph["f2_mean"]) in (0, 7)


def test_extract_returns_every_pattern_for_a_normal_token():
    f = feats("See - UK.mp3")
    assert set(f.scalars) == set(SCALAR_KEYS)
    assert f.scalars["e0_2"] + f.scalars["e2_4"] + f.scalars["e4_6"] + f.scalars["e6_8"] == pytest.approx(1.0, abs=0.01)
    assert f.shape.shape == (40,) and abs(f.shape.mean()) < 1e-6
    assert f.traj.shape == (5,) and not np.isnan(f.traj).any()
    assert f.f2.shape == (7,)


def test_extract_analyses_at_16_khz_like_the_reference():
    r = D1["Fee - UK.mp3"]
    snd = load(r.path)
    f = extract(snd, r.start_s, r.end_s, True, 5000.0)
    at16 = measure(snd.resample(16000, 50), r.start_s, r.end_s).cog_hz
    native = measure(snd, r.start_s, r.end_s).cog_hz
    assert f.scalars["cog"] == pytest.approx(at16, abs=1.0)
    assert abs(f.scalars["cog"] - native) > 1000        # the band limit really changes /f/


def test_short_or_vowelless_segments_degrade_gracefully():
    r = D1["She - UK.mp3"]
    snd = load(r.path)
    short = extract(snd, r.start_s, r.start_s + 0.05, True, 5000.0)
    assert np.isnan(short.traj).all()
    novowel = extract(snd, r.start_s, r.end_s, False, 5000.0)
    assert np.isnan(novowel.scalars["relamp"])


def test_percentiles_place_a_token_inside_its_own_class():
    f = feats("See - UK.mp3")
    p = percentiles(f, REF, "bdl")
    assert set(p) == {"S", "SH", "F", "TH", "Z"}
    assert p["SH"]["cog"] == 95.0                     # far above every /ʃ/ in the reference
    assert 5.0 <= p["S"]["cog"] <= 95.0


KNOWN_SPEAKER_MISS = pytest.mark.xfail(strict=True, reason=(
    "Without per-speaker normalisation the low /s/ of this D1 voice (CoG 4,709 Hz, 41% of the energy at 2-4 kHz, spectral contrast "
    "8.1 dB) looks flat to both reference voices, so the two family cues disagree. If this starts passing, speaker calibration "
    "has been added: remove the marker."))
BORDERLINE = pytest.mark.xfail(strict=True, reason=(
    "She - UK has a spectral contrast of 9.10 dB, just under the 9.56 dB boundary of the bdl voice, so the cues disagree."))


@pytest.mark.parametrize("name,expected,voice", [
    ("See - UK.mp3", "s", "bdl"), ("See - UK.mp3", "s", "slt"),
    pytest.param("See - US.mp3", "s", "bdl", marks=KNOWN_SPEAKER_MISS), pytest.param("See - US.mp3", "s", "slt", marks=KNOWN_SPEAKER_MISS),
    pytest.param("She - UK.mp3", "sh", "bdl", marks=BORDERLINE), ("She - UK.mp3", "sh", "slt"),
    ("She - US.mp3", "sh", "bdl"), ("She - US.mp3", "sh", "slt")])
def test_experimental_verdict_on_sibilants(name, expected, voice):
    v = experimental_verdict(feats(name, voice=voice), REF, voice)
    assert v.family == "sibilant"
    assert set(v.votes) == {"CoG threshold", "Low-band energy (2–4 kHz)", "Nearest spectral template"}
    assert v.heard == expected


def test_borderline_contrast_depends_on_the_reference_voice():
    f = feats("She - UK.mp3", voice="slt")
    assert experimental_verdict(f, REF, "slt").family == "sibilant"
    assert experimental_verdict(f, REF, "bdl").family == "unsure"


def test_experimental_verdict_sends_weak_hiss_to_display_only():
    v = experimental_verdict(feats("Fee - UK.mp3"), REF, "bdl")
    assert v.family == "weak" and v.heard is None and v.votes == {}
    assert v.weak_nearest in ("F", "TH")


def test_f2_transition_converges_even_when_the_vowel_is_held_long():
    """Isolated words hold the vowel for ~0.4 s; the reference vowels are ~0.1 s, so the middle is capped."""
    f = feats("See - UK.mp3")
    assert not np.isnan(f.f2).any()
    assert abs(f.f2[-1]) < 150           # F2 has reached the vowel target 60 ms after the hiss
    assert abs(f.f2[-1]) < abs(f.f2[0])


def test_variability_features_are_measured_and_separate_sibilants_from_weak_hiss():
    see, fee = feats("See - UK.mp3").scalars, feats("Fee - UK.mp3").scalars
    for k in ("contrast", "wobble"):
        assert k in SCALAR_KEYS and not np.isnan(see[k]) and not np.isnan(fee[k])
    assert see["contrast"] > fee["contrast"]            # sibilants are peakier than weak hisses
    assert fee["wobble"] > see["wobble"]                # and steadier across the hiss


def test_wobble_is_missing_for_a_short_hiss():
    r = D1["She - UK.mp3"]
    f = extract(load(r.path), r.start_s, r.start_s + 0.05, True, 5000.0)
    assert np.isnan(f.scalars["wobble"]) and not np.isnan(f.scalars["contrast"])


@pytest.mark.parametrize("name,family", [("See - UK.mp3", "sibilant"), ("She - US.mp3", "sibilant"), ("Fee - UK.mp3", "weak"), ("Fee - US.mp3", "weak")])
def test_family_uses_both_cues_when_a_vowel_follows(name, family):
    v = experimental_verdict(feats(name), REF, "bdl")
    assert list(v.family_cues) == ["Relative amplitude", "Spectral contrast"]
    assert v.family == family and set(v.family_cues.values()) == {family}


@pytest.mark.parametrize("name,family,voice", [("See - UK.mp3", "sibilant", "bdl"), ("She - UK.mp3", "sibilant", "slt"),
                                               ("Fee - UK.mp3", "weak", "bdl"), ("Fee - US.mp3", "weak", "bdl")])
def test_family_falls_back_to_spectral_contrast_without_a_vowel(name, family, voice):
    v = experimental_verdict(feats(name, has_vowel=False, voice=voice), REF, voice)
    assert list(v.family_cues) == ["Spectral contrast"] and v.family == family


def test_conflicting_cues_are_reported_as_unsure_and_not_scored():
    f = feats("See - UK.mp3")
    flat = replace(f, scalars={**f.scalars, "contrast": 5.0})        # loud hiss but a flat spectrum
    v = experimental_verdict(flat, REF, "bdl")
    assert v.family == "unsure" and v.votes == {} and v.heard is None
    assert set(v.family_cues.values()) == {"sibilant", "weak"}
