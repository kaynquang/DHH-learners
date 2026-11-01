from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
PRACTICE = str(Path(__file__).resolve().parents[1] / "app_pages" / "practice.py")


def run_app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


@pytest.fixture(autouse=True)
def _without_the_recogniser(monkeypatch):
    """The tests below describe the app without the optional recogniser unless a test fakes it."""
    monkeypatch.delenv("W2V_DIR", raising=False)
    monkeypatch.setattr("fricative.phoneme_check.DEFAULT_DIR", Path("/nonexistent"))


def verdict(at):
    return " ".join(m.value for m in at.markdown)


def test_ui_text_is_english():
    at = run_app()
    assert at.title[0].value == "Fricative practice"
    assert at.segmented_control(key="source").options == ["Sample", "Record", "Upload"]
    assert at.segmented_control(key="word").label == "Target sounds"
    assert at.segmented_control(key="word").options == ["/s/", "/ʃ/", "/f/", "/p/", "/b/", "/m/", "/n/", "/tʃ/"]


def test_opens_with_sample_and_green_verdict():
    at = run_app()
    assert not at.exception
    assert "Correct" in verdict(at) and "You said /s/" in verdict(at)


def test_wrong_target_word_is_red():
    at = run_app()
    at.segmented_control(key="word").set_value("she").run()
    assert "Not yet" in verdict(at) and "You said /s/" in verdict(at)


def test_threshold_edit_then_reset():
    at = run_app()
    at.number_input(key="th_cog").set_value(7000.0).run()
    assert "You said /ʃ/" in verdict(at)
    at.sidebar.button[0].click().run()
    assert at.number_input(key="th_cog").value == 4340.0
    assert "Correct" in verdict(at) and "You said /s/" in verdict(at)


def test_fee_sample_scores_f():
    at = run_app()
    at.segmented_control(key="word").set_value("fee").run()
    at.selectbox(key="sample").set_value("Fee - US.mp3").run()
    assert "Correct" in verdict(at) and "You said /f/" in verdict(at)


def test_too_short_manual_boundary_shows_error():
    at = run_app()
    at.slider[0].set_value((0.100, 0.110)).run()
    assert any("too short" in e.value for e in at.error)


def _app_with_fake_audio(kind):
    """Run the app with load() swapped for fake audio (only for this run)."""
    script = f'''
import numpy as np
import parselmouth
import fricative.audio as _audio
_real = _audio.load
def _fake(data, name=None):
    if "{kind}".startswith("stop"):
        vot = int("{kind}".split(":")[1])
        fs, rng = 16000, np.random.default_rng(1)
        x = rng.normal(0, 1e-4, int(0.6 * fs)); a, v = int(0.2 * fs), int((0.2 + vot / 1000) * fs)
        x[a:v + 64] += rng.normal(0, 0.05, v + 64 - a)
        tt = np.arange(len(x) - v) / fs
        x[v:] += sum(0.1 / k * np.sin(2 * np.pi * 120 * k * tt) for k in range(1, 12))
        return parselmouth.Sound(x, sampling_frequency=fs)
    if "{kind}" == "zeros":
        return parselmouth.Sound(np.zeros(48000), sampling_frequency=48000)
    return parselmouth.Sound(np.random.default_rng(0).normal(0, 1e-3, 48000), sampling_frequency=48000)
_audio.load = _fake
try:
    exec(open({PRACTICE!r}, encoding="utf-8").read())
finally:
    _audio.load = _real
'''
    at = AppTest.from_string(script, default_timeout=120)
    at.run()
    return at


def test_noise_only_input_is_not_scored():
    at = _app_with_fake_audio("noise")
    assert not at.exception
    assert "You said" not in verdict(at)
    assert any("No frication" in w.value or "too short" in w.value for w in at.warning)


def test_digital_silence_input_does_not_crash():
    at = _app_with_fake_audio("zeros")
    assert not at.exception
    assert "You said" not in verdict(at)


def test_how_it_works_page_renders_each_mechanism():
    at = run_app()
    at.switch_page("app_pages/how_it_works.py").run()
    assert not at.exception
    assert at.title[0].value == "How it works"
    headers = [h.value for h in at.header]
    for h in ["Finding the frication", "Measuring", "Scoring", "Alternative detectors"]:
        assert h in headers
    at.selectbox(key="explain_sample").set_value("Fee - US.mp3").run()
    assert not at.exception


def test_practice_shows_articulation_diagram_for_target():
    at = run_app()
    assert len(at.image) == 1 and "/s/" in at.image[0].captions[0]
    at.segmented_control(key="word").set_value("she").run()
    assert "/ʃ/" in at.image[0].captions[0]


def test_how_it_works_shows_all_three_diagrams():
    at = run_app()
    at.switch_page("app_pages/how_it_works.py").run()
    captions = " ".join(c for im in at.image for c in im.captions)
    assert len(at.image) == 3
    for phone in ["/s/", "/ʃ/", "/f/"]:
        assert phone in captions


CALIBRATE = str(Path(__file__).resolve().parents[1] / "app_pages" / "calibrate.py")


def _calibrate_with_demo(at):
    at.switch_page("app_pages/calibrate.py").run()
    at.button(key="cal_demo").click().run()
    return at


def test_calibrate_page_demo_builds_a_calibration_from_six_recordings():
    at = _calibrate_with_demo(run_app())
    assert not at.exception
    assert at.title[0].value == "Calibrate"
    cal = at.session_state["calibration"]
    assert cal.n_tokens == 6 and len(at.session_state["cal_tokens"]) == 6
    assert any("calibrated" in s.value.lower() for s in at.success)


def test_calibrate_wizard_collects_the_six_words_one_by_one():
    at = run_app()
    at.switch_page("app_pages/calibrate.py").run()
    order = ["see", "she", "fee", "see", "she", "fee"]
    files = {"see": "See - UK.mp3", "she": "She - UK.mp3", "fee": "Fee - UK.mp3"}
    for i, word in enumerate(order):
        assert f"Step {i + 1} of 6: say **{word}**" in " ".join(m.value for m in at.markdown)
        at.segmented_control(key=f"cal_source_{i}").set_value("Sample").run()
        at.selectbox(key=f"cal_sample_{i}").set_value(files[word]).run()
        at.button(key=f"cal_accept_{i}").click().run()
        assert not at.exception
    assert len(at.session_state["cal_tokens"]) == 6 and at.session_state["calibration"].n_tokens == 6


def test_calibrate_page_can_start_over():
    at = _calibrate_with_demo(run_app())
    at.button(key="cal_redo").click().run()
    assert "calibration" not in at.session_state and len(at.session_state["cal_tokens"]) == 0


def test_calibrate_page_rejects_a_recording_without_a_hiss():
    script = f'''
import numpy as np
import parselmouth
import fricative.audio as _audio
_real = _audio.load
_audio.load = lambda data, name=None: parselmouth.Sound(np.zeros(48000), sampling_frequency=48000)
try:
    exec(open({CALIBRATE!r}, encoding="utf-8").read())
finally:
    _audio.load = _real
'''
    at = AppTest.from_string(script, default_timeout=120).run()
    at.segmented_control(key="cal_source_0").set_value("Sample").run()
    at.selectbox(key="cal_sample_0").set_value("See - UK.mp3").run()
    assert not at.exception
    assert any("record this word again" in e.value for e in at.error)
    assert not [b for b in at.button if b.key == "cal_accept_0"]


def test_practice_uses_the_calibration_when_it_exists_and_can_switch_it_off():
    at = _calibrate_with_demo(run_app())
    at.switch_page("app_pages/practice.py").run()
    assert not at.exception
    caps = " ".join(c.value for c in at.caption)
    assert "Calibrated to your voice" in caps and "rule-based" in caps.lower()
    assert "Correct" in verdict(at)
    at.toggle(key="use_calibration").set_value(False).run()
    assert "Calibrated to your voice" not in " ".join(c.value for c in at.caption)


def test_practice_without_calibration_suggests_calibrating():
    at = run_app()
    assert "Calibrate" in " ".join(c.value for c in at.caption)


def test_how_it_works_explains_the_calibrated_scoring_with_the_model_numbers():
    at = run_app()
    at.switch_page("app_pages/how_it_works.py").run()
    assert not at.exception
    assert "Calibrated scoring" in [h.value for h in at.header]
    text = " ".join(m.value for m in at.markdown)
    assert "Calibrate" in text and "weak hiss vs sibilant" in text and "worst voice" in text



def open_view(at, view):
    at.segmented_control(key="view").set_value(view).run()
    assert not at.exception
    return at


def test_practice_has_a_view_switch_and_renders_only_the_chosen_view():
    at = run_app()
    sw = at.segmented_control(key="view")
    assert sw.options == ["Compare", "Patterns", "Detectors"] and sw.value == "Compare"
    assert "Compared with the D1 voices" in [h.value for h in at.subheader]
    assert "Ablation studies" not in [h.value for h in at.subheader]
    assert len(at.get("plotly_chart")) >= 3


def test_detectors_view_lists_every_detector_and_cog_setting():
    at = open_view(run_app(), "Detectors")
    assert "Ablation studies" in [h.value for h in at.subheader]
    frames = [d.value for d in at.dataframe]
    seg = next(f for f in frames if "Method" in f.columns)
    cog = next(f for f in frames if "Setting" in f.columns)
    assert len(seg) == 5 and seg.iloc[0]["Method"].startswith("Anchored") and "Δ onset (ms)" in seg.columns
    assert "failed" not in str(seg.iloc[0]["Verdict"])
    assert len(cog) == 5 and cog.iloc[0]["Setting"].endswith("(current)")


def test_detectors_view_has_a_reading_guide_and_a_summary():
    at = open_view(run_app(), "Detectors")
    text = " ".join(m.value for m in at.markdown)
    assert "How to read this chart" in text and "red bar" in text
    assert "compared with the manual Praat boundaries" in text and "agrees" in text


def test_patterns_view_labels_itself_experimental_and_uses_the_practice_recording():
    at = open_view(run_app(), "Patterns")
    text = " ".join([m.value for m in at.markdown] + [w.value for w in at.warning])
    assert "Experimental" in text and "calibration" in text.lower() and "Looks like /s/" in text
    assert len(at.get("plotly_chart")) >= 6
    assert "Compared with the D1 voices" not in [h.value for h in at.subheader]


def test_patterns_view_changes_with_the_reference_voice():
    at = open_view(run_app(), "Patterns")
    at.segmented_control(key="ref_voice").set_value("slt").run()
    assert not at.exception


def test_patterns_view_marks_a_weak_hiss_as_not_scored():
    at = run_app()
    at.segmented_control(key="word").set_value("fee").run()
    at.selectbox(key="sample").set_value("Fee - UK.mp3").run()
    open_view(at, "Patterns")
    text = " ".join(m.value for m in at.markdown)
    assert "Weak hiss" in text and "Looks like" not in text


def test_patterns_view_sibilant_branch_for_she():
    at = run_app()
    at.segmented_control(key="word").set_value("she").run()
    at.selectbox(key="sample").set_value("She - US.mp3").run()
    open_view(at, "Patterns")
    assert any("Looks like /ʃ/" in m.value for m in at.markdown)


def test_patterns_view_says_when_the_two_cues_disagree():
    at = run_app()
    at.selectbox(key="sample").set_value("See - US.mp3").run()
    open_view(at, "Patterns")
    text = " ".join(m.value for m in at.markdown)
    assert "The cues disagree" in text and "Looks like" not in text


def test_patterns_view_has_a_variability_section_and_shows_both_family_cues():
    at = open_view(run_app(), "Patterns")
    assert "4 · Variability" in [h.value for h in at.subheader]
    cues = [d.value for d in at.dataframe if "Cue" in d.value.columns]
    assert cues and list(cues[0]["Cue"]) == ["Relative amplitude", "Spectral contrast"]


def test_the_standalone_patterns_page_is_gone_from_the_navigation():
    at = run_app()
    with pytest.raises(ValueError):
        at.switch_page("app_pages/patterns.py")


def _app_with_fake_phoneme_check(heard, opens=None, p_m=None):
    script = f'''
import numpy as np
import fricative.phoneme_check as pc
_real = (pc.available, pc.check, pc.first_consonant, pc.nasal_reading)
def _fake(sound, onset, offset):
    centres = np.arange(40) * 0.02 + 0.0125
    track = {{g: np.zeros(40) for g in ("S", "SH", "F", "TH")}}
    track[{heard!r}][10:16] = 0.9
    masses = {{g: float(v[8:20].mean()) for g, v in track.items()}}
    return pc.PhoneCheck(masses, {heard!r}, "s iː", centres, track, (0.2, 0.4))
pc.available, pc.check, pc.first_consonant, pc.nasal_reading = (lambda: True), _fake, (lambda sound: {opens!r}), (lambda sound: ({p_m!r}, ''))
try:
    exec(open({PRACTICE!r}, encoding="utf-8").read())
finally:
    pc.available, pc.check, pc.first_consonant, pc.nasal_reading = _real
'''
    return AppTest.from_string(script, default_timeout=120).run()


def test_phoneme_check_view_is_offered_only_when_the_recogniser_is_available():
    assert "Phoneme check" not in run_app().segmented_control(key="view").options
    at = _app_with_fake_phoneme_check("S")
    assert "Phoneme check" in at.segmented_control(key="view").options


def test_phoneme_check_view_reports_agreement_with_the_verdict():
    at = _app_with_fake_phoneme_check("S")
    at.segmented_control(key="view").set_value("Phoneme check").run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Phoneme check" in [h.value for h in at.subheader]
    assert "hears /s/" in text and "agrees" in text.lower()


def test_phoneme_check_view_flags_a_disagreement():
    at = _app_with_fake_phoneme_check("SH")
    at.segmented_control(key="view").set_value("Phoneme check").run()
    text = " ".join(m.value for m in at.markdown)
    assert "hears /ʃ/" in text and "✕" in text      # the recogniser's answer now overrules the measured verdict


def test_nasal_words_need_the_recogniser_and_say_so_without_it():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.segmented_control(key="word").set_value("me").run()
    assert not at.exception
    assert any("needs the phone recogniser" in i.value for i in at.info)
    assert not at.get("plotly_chart")


@pytest.mark.parametrize("p_m,word,mark", [(0.97, "me", "◯"), (0.65, "me", "△"), (0.1, "me", "✕"), (0.05, "knee", "◯")])
def test_nasal_words_are_scored_from_the_recogniser(p_m, word, mark):
    at = _app_with_fake_phoneme_check("S", opens=None, p_m=p_m)
    at.segmented_control(key="word").set_value(word).run()
    assert not at.exception
    assert mark in verdict(at)


def test_cheat_is_scored_from_how_the_hiss_starts():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.selectbox(key="sample").set_value("She - UK.mp3").run()
    at.segmented_control(key="word").set_value("cheat").run()
    assert not at.exception
    assert any(m.label == "Rise time" for m in at.metric)
    assert any(x in verdict(at) for x in "◯△✕")



@pytest.mark.parametrize("vot,word,mark", [(70, "pea", "◯"), (8, "pea", "✕"), (8, "bee", "◯")])
def test_stop_words_are_scored_by_vot(vot, word, mark):
    at = _app_with_fake_audio(f"stop:{vot}")
    at.segmented_control(key="word").set_value(word).run()
    assert not at.exception
    assert mark in verdict(at) and any(m.label == "VOT" for m in at.metric)


def test_recording_of_another_kind_of_sound_is_not_scored():
    at = _app_with_fake_phoneme_check("F", opens="F")
    at.segmented_control(key="word").set_value("pea").run()
    assert not at.exception
    assert any("different kind" in w.value and "/f/" in w.value for w in at.warning)
    assert "You said" not in verdict(at)


def test_matching_kind_of_sound_is_scored_as_usual():
    at = _app_with_fake_phoneme_check("S", opens="S")
    assert not at.exception and not any("different kind" in w.value for w in at.warning)
    assert "You said" in verdict(at)
