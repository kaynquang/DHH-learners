from dataclasses import replace

import numpy as np

from fricative.audio import load
from fricative.config import DEFAULT_THRESHOLDS
from fricative.measure import Measures
from fricative.plots import comparison_figure, spectrogram_figure, spectrum_figure
from fricative.reference import load_reference, measure_reference


def test_spectrogram_has_heatmap_boundaries_and_window():
    r = load_reference()[0]
    fig = spectrogram_figure(load(r.path), r.start_s, r.end_s)
    assert fig.data[0].type == "heatmap"
    xs = sorted(s.x0 for s in fig.layout.shapes if s.type == "line")
    assert np.allclose(xs, [r.start_s * 1000, r.end_s * 1000])
    rect = [s for s in fig.layout.shapes if s.type == "rect"][0]
    d = r.end_s - r.start_s
    assert np.isclose(rect.x0, (r.start_s + d / 4) * 1000)


def test_comparison_threshold_lines_follow_settings():
    refs = measure_reference()
    user = Measures(0.03, 0.2, 5000.0, -4.0, 4000.0, 170.0)
    th = replace(DEFAULT_THRESHOLDS, cog_s_sh_hz=4000.0, relamp_f_db=-20.0)
    fig = comparison_figure(user, refs, th)
    xs = [s.x0 for s in fig.layout.shapes]
    ys = [s.y0 for s in fig.layout.shapes]
    assert 4000.0 in xs and -20.0 in ys
    names = [t.name for t in fig.data]
    assert "Your recording" in names and len(fig.data) == 4


def test_comparison_without_vowel_draws_user_line():
    refs = measure_reference()
    fig = comparison_figure(Measures(0.03, 0.2, 5000.0, None, 4000.0, 170.0), refs, DEFAULT_THRESHOLDS)
    assert len(fig.data) == 3
    assert any(s.x0 == 5000.0 for s in fig.layout.shapes)


def test_spectrum_traces_normalised_to_peak():
    f = np.linspace(0, 16000, 100)
    user = (f, np.linspace(-80, -20, 100))
    refs = [("D1 UK /s/", f, np.linspace(-50, -10, 100))]
    fig = spectrum_figure(user, refs)
    assert len(fig.data) == 2
    assert all(np.isclose(max(t.y), 0) for t in fig.data)


def test_comparison_range_includes_user_point_above_9_khz():
    refs = measure_reference()
    user = Measures(0.03, 0.2, 11900.0, 0.1, 4000.0, 170.0)
    fig = comparison_figure(user, refs, DEFAULT_THRESHOLDS)
    lo, hi = fig.layout.xaxis.range
    assert lo <= 11900.0 <= hi


def test_detection_figure_shows_energy_floor_threshold_and_boundaries():
    from fricative.plots import detection_figure
    from fricative.segment import trace_boundaries
    tr = trace_boundaries(load(load_reference()[0].path))
    fig = detection_figure(tr)
    assert fig.data[0].name == "High-band energy"
    ys = [s.y0 for s in fig.layout.shapes if s.type == "line" and s.y0 == s.y1]
    assert any(np.isclose(y, tr.floor_db) for y in ys) and any(np.isclose(y, tr.threshold_db) for y in ys)
    xs = [s.x0 for s in fig.layout.shapes if s.type == "line" and s.x0 == s.x1]
    assert any(np.isclose(x, tr.boundaries.onset_s * 1000) for x in xs)


def test_timeline_figure_has_one_bar_per_method_and_marks_failures():
    from fricative.ablation import segmentation_ablation
    from fricative.plots import timeline_figure
    r = [x for x in load_reference() if x.file == "See - US.mp3"][0]
    snd = load(r.path)
    rows = segmentation_ablation(snd, "s", DEFAULT_THRESHOLDS, manual=(r.start_s, r.end_s))
    fig = timeline_figure(rows, manual=(r.start_s, r.end_s))
    bars = [t for t in fig.data if t.type == "bar"]
    assert len(bars) == 1 and len(bars[0].y) == 4
    assert any("failed" in (a.text or "") for a in fig.layout.annotations)
    assert any(s.type == "rect" for s in fig.layout.shapes)


def test_decision_figure_regions_follow_thresholds():
    from fricative.plots import decision_figure
    th = replace(DEFAULT_THRESHOLDS, cog_s_sh_hz=4000.0, relamp_f_db=-18.0)
    fig = decision_figure(th)
    rects = [s for s in fig.layout.shapes if s.type == "rect"]
    assert any(np.isclose(s.x0, 4000.0) or np.isclose(s.x1, 4000.0) for s in rects)
    assert any(np.isclose(s.y0, -18.0) or np.isclose(s.y1, -18.0) for s in rects)
    texts = {a.text for a in fig.layout.annotations}
    assert {"/s/", "/ʃ/", "/f/"} <= texts


def _pattern_inputs(name="See - UK.mp3", voice="bdl", has_vowel=True):
    from fricative.patterns import extract, load_reference as load_ref
    ref = load_ref()
    r = [x for x in load_reference() if x.file == name][0]
    return extract(load(r.path), r.start_s, r.end_s, has_vowel, ref["voices"][voice]["max_formant_hz"]), ref, voice


def test_pattern_distribution_figure_has_a_box_per_phone_and_feature_and_a_user_line():
    from fricative.plots import pattern_distribution_figure
    f, ref, voice = _pattern_inputs()
    fig = pattern_distribution_figure(f, ref, voice)
    boxes = [t for t in fig.data if t.type == "box"]
    assert len(boxes) == 6 * 4
    assert sum(1 for a in fig.layout.annotations if a.text == "You") == 6
    assert {t.name for t in boxes} == {"/s/", "/ʃ/", "/f/", "/θ/"}


def test_template_figure_overlays_the_recording_on_four_templates():
    from fricative.plots import template_figure
    f, ref, voice = _pattern_inputs()
    fig = template_figure(f, ref, voice)
    names = [t.name for t in fig.data if t.mode == "lines"]
    assert names[-1] == "Your recording" and len(names) == 5
    assert len(fig.data[-1].y) == 40


def test_trajectory_and_f2_figures_explain_missing_data():
    from fricative.plots import f2_figure, trajectory_figure
    f, ref, voice = _pattern_inputs()
    assert [t.name for t in trajectory_figure(f, ref, voice).data][-1] == "Your recording"
    assert [t.name for t in f2_figure(f, ref, voice).data][-1] == "Your recording"
    from dataclasses import replace
    empty = replace(f, traj=np.full(5, np.nan), f2=np.full(7, np.nan))
    assert any("shorter than 60 ms" in a.text for a in trajectory_figure(empty, ref, voice).layout.annotations)
    assert any("no vowel" in a.text.lower() for a in f2_figure(empty, ref, voice).layout.annotations)


def test_variability_figure_shows_contrast_and_wobble_with_the_family_boundary():
    from fricative.plots import variability_figure
    f, ref, voice = _pattern_inputs()
    fig = variability_figure(f, ref, voice)
    assert len([t for t in fig.data if t.type == "box"]) == 2 * 4
    assert sum(1 for a in fig.layout.annotations if a.text == "You") == 2
    assert any(a.text == "family boundary" for a in fig.layout.annotations)
    from dataclasses import replace
    short = replace(f, scalars={**f.scalars, "wobble": float("nan")})
    assert sum(1 for a in variability_figure(short, ref, voice).layout.annotations if a.text == "You") == 1


def _phone_check(heard="S"):
    import numpy as np
    from fricative.phoneme_check import PhoneCheck
    centres = np.arange(40) * 0.02 + 0.0125
    track = {g: np.zeros(40) for g in ("S", "SH", "F", "TH")}
    track[heard][10:16] = 0.9
    masses = {g: float(v[8:20].mean()) for g, v in track.items()}
    return PhoneCheck(masses, heard, "s iː", centres, track, (0.2, 0.4))


def test_phoneme_figure_shows_group_evidence_over_time_and_marks_the_hiss():
    from fricative.plots import phoneme_figure
    fig = phoneme_figure(_phone_check("SH"))
    assert len([t for t in fig.data if t.type == "bar"]) == 1 and len([t for t in fig.data if t.type == "scatter" and t.mode == "lines"]) == 4
    assert list(fig.data[0].x) == ["/s/", "/ʃ/", "/f/", "/θ/"]
    assert any(s.type == "rect" for s in fig.layout.shapes)
