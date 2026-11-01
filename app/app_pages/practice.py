"""Practice page: record or pick a word, get a verdict, then explore it in the Compare, Patterns and Detectors views."""
import hashlib

import streamlit as st

from fricative import config as C
from fricative.audio import limit_duration, load
from fricative.calibrated import load_model, read as read_calibrated
from fricative.classify import classify
from fricative.measure import measure
from fricative.patterns import extract
from fricative.plots import gop_figure, spectrogram_figure
from fricative.reference import available as reference_available, load_reference
from fricative.segment import SegmentationError, estimate_snr, find_boundaries
from fricative.affricate import classify_affricate, measure_affricate, probability_ch
from fricative.stops import MAX_VOT_MS, VOT_P_MS, classify_stop, measure_vot
from fricative import gop, phoneme_check, reclog
from views import compare, detectors, patterns, phoneme
from views.autorecord import auto_record, playback
from views.context import Ctx

TH_KEYS = {
    "cog_s_sh_hz": "th_cog",
    "relamp_f_db": "th_relamp",
    "cog_margin_hz": "th_cog_margin",
    "relamp_margin_db": "th_relamp_margin",
}
MARK_COLOR = {"green": "green", "yellow": "orange", "red": "red"}


def reset_thresholds() -> None:
    for field, key in TH_KEYS.items():
        st.session_state[key] = getattr(C.DEFAULT_THRESHOLDS, field)


def log_result(verdict: dict, details: dict | None = None) -> None:
    """Log this recording and what the app decided (unless the learner turned logging off or discarded it), and offer to keep, discard
    or flag it as wrong under the result."""
    eid = reclog.entry_id(data, word)
    discarded = st.session_state.setdefault("log_discarded", set())

    def save() -> str:
        return reclog.log_recording(
            data, name or "recording.wav", word, target=target, source=source, profile=st.session_state.get("profile_select"),
            verdict=verdict, details=details or {},
            settings=dict(recogniser=phoneme_check.available(), calibrated=st.session_state.get("calibration") is not None
                          and st.session_state.get("use_calibration", True), thresholds={f: st.session_state[k] for f, k in TH_KEYS.items()}))

    def discard() -> None:
        reclog.delete(eid)
        discarded.add(eid)

    def keep() -> None:
        discarded.discard(eid)
        save()

    if st.session_state.get("log_auto", True) and eid not in discarded:
        save()
    entry = reclog.get(eid)
    with st.container(horizontal=True, vertical_alignment="center"):
        if entry is None:
            st.caption("This recording is not in the log.")
            st.button("Keep in log", icon=":material/bookmark_add:", on_click=keep, key=f"keep_{eid}")
            return
        st.caption("Saved in the log.")
        st.button("Discard", icon=":material/delete:", on_click=discard, key=f"discard_{eid}",
                  help="Delete this recording from the log. It is not saved again for this recording.")
        with st.popover("Said it right but the result is wrong?", icon=":material/flag:"):
            if entry.get("flagged"):
                st.caption("Already flagged. You can change the note.")
            note = st.text_area("What happened?", value=entry.get("note", ""), key=f"note_{eid}",
                                placeholder=f"For example: I said “{word}” clearly and the app said I was wrong.")
            if st.button("Save to the log", key=f"flag_{eid}", icon=":material/flag:"):
                reclog.flag(eid, note)
                st.toast("Saved. Open the Log page to see it.", icon=":material/check:")

def log_unscored(reason: str, details: dict | None = None) -> None:
    log_result(dict(label="Not scored", mark="–", color="none", heard=None, message=reason), details)


def verdict_dict(v) -> dict:
    return dict(label=v.label, mark=v.mark, color=v.color, heard=v.heard, message=v.message, tip=v.tip)


def show_verdict(v, extra: str | None = None, details: dict | None = None) -> None:
    """Verdict box for the sounds that have no views (stops, nasals, affricates)."""
    with st.container(border=True, horizontal=True, vertical_alignment="center", gap="large"):
        st.markdown(f"# :{MARK_COLOR[v.color]}[{v.mark}]", width="content")
        with st.container():
            st.markdown(f"### {v.label}")
            st.markdown(f"{v.message} · target **{word}** {C.PHONE_LABEL[target]}")
            st.caption(v.tip)
            if extra:
                st.caption(extra)
    log_result(verdict_dict(v), {**(details or {}), "extra": extra})


for _field, _key in TH_KEYS.items():
    st.session_state.setdefault(_key, getattr(C.DEFAULT_THRESHOLDS, _field))


# ---------- Sidebar ----------
with st.sidebar:
    ALL_TARGETS = {**C.TARGETS, **C.STOP_TARGETS, **C.NASAL_TARGETS, **C.AFFRICATE_TARGETS}
    # one example word per sound, so each of the eight sounds appears once
    SOUND_WORDS = {}
    for _w, _p in ALL_TARGETS.items():
        SOUND_WORDS.setdefault(_p, _w)
    word = st.segmented_control("Target sounds", list(SOUND_WORDS.values()), default="see", required=True, key="word",
                                format_func=lambda w: C.PHONE_LABEL[ALL_TARGETS[w]])
    target = ALL_TARGETS[word]
    st.caption(f"Say the word “{word}”")
    st.space("small")
    if st.session_state.get("calibration") is not None:
        st.toggle("Use my voice calibration", value=True, key="use_calibration",
                  help="Judge the recording against your own six calibration recordings instead of fixed thresholds.")
    st.toggle("Save recordings to the log", value=True, key="log_auto",
              help="Every scored recording is kept in the Log page so you can flag wrong results. Turn off to keep only the ones you choose.")
    with st.expander("Scoring settings", icon=":material/tune:"):
        st.number_input("CoG threshold /s/–/ʃ/ (Hz)", 1000.0, 10000.0, step=50.0, key="th_cog")
        st.number_input("Relative amplitude threshold /f/ (dB)", -60.0, 0.0, step=1.0, key="th_relamp")
        st.number_input("Yellow margin, CoG (Hz)", 0.0, 3000.0, step=50.0, key="th_cog_margin")
        st.number_input("Yellow margin, relative amplitude (dB)", 0.0, 20.0, step=0.5, key="th_relamp_margin")
        st.button("Reset to defaults", icon=":material/restart_alt:", on_click=reset_thresholds)
        st.caption("Provisional values from the two D1 voices. Changes last for this session only.")

th = C.Thresholds(**{field: float(st.session_state[key]) for field, key in TH_KEYS.items()})

# ---------- Input ----------
st.title("Fricative practice")
st.caption("Say one word. See where your hiss lands.")

SOURCES = ["Sample", "Record", "Upload"] if reference_available() else ["Record", "Upload"]
source = st.segmented_control("Input", SOURCES, default=SOURCES[0], required=True, key="source")
data, name, manual = None, None, None
if source == "Record":
    st.caption("Press record and say the word right away. It stops by itself after 3 seconds. For the best result, use a quiet room "
               "and keep the microphone close to your mouth.")
    rec = auto_record("rec")
    if rec is not None:
        data, name = rec, "recording.wav"
elif source == "Upload":
    up = st.file_uploader("Upload a wav or mp3 file", type=["wav", "mp3"], key="upload")
    if up is not None:
        data, name = up.getvalue(), up.name
else:
    refs = {r.file: r for r in load_reference()}
    choice = st.selectbox("D1 sample", list(refs), key="sample")
    data, name = refs[choice].path.read_bytes(), choice
    manual = (refs[choice].start_s, refs[choice].end_s)

if data is None:
    st.info("Record or upload a word to begin.", icon=":material/mic:")
    st.stop()

playback(data, "practice_play", name)
try:
    sound = load(data, name)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
sound, truncated = limit_duration(sound)
if truncated:
    st.warning("The recording is longer than 5 seconds; only the first 5 seconds are used.")

RECOGNISER = phoneme_check.available()      # the optional wav2vec2 phone recogniser (torch, transformers and the checkpoint)

if RECOGNISER and target in gop.SUPPORTED:
    # Goodness of pronunciation: how likely is each sound the word could be mistaken for at the start of the speech (any vowel after it)?
    gop_key = f"gop_{hashlib.md5(data).hexdigest()[:10]}_{target}"
    if gop_key not in st.session_state:
        with st.spinner("Listening to the first sound…"):
            st.session_state[gop_key] = gop.score(sound, target)
    g = st.session_state[gop_key]
    if g is None:
        st.warning("No speech was heard in this recording, so it is not scored. Say the word right after you press Record, "
                   "in a quiet room and close to the microphone.", icon=":material/hearing:")
        st.plotly_chart(spectrogram_figure(sound, 0.0, 0.0), width="stretch", alt="Spectrogram of the recording")
        log_unscored("No speech heard")
        st.stop()
    gop_details = dict(gop={k: round(v, 4) for k, v in g.probs.items()}, top=g.top, start_s=round(g.start_s, 3), end_s=round(g.end_s, 3),
                       decoded_phones=list(g.phones))
    gop_v = gop.verdict(g, target)
    if gop_v is None:
        st.warning(f"The recogniser is not sure which sound starts this word (best guess /{g.top}/, {g.probs[g.top]:.0%}), so it is not scored. "
                   "Say the word again in a quiet room, close to the microphone, with a short pause before it.", icon=":material/hearing:")
        log_unscored("Not sure which sound starts the word", gop_details)
    else:
        show_verdict(gop_v, f"Chance of /{target}/ among the sounds it is confused with: {g.p(target):.0%}. Provisional thresholds; "
                            "the score does not depend on the vowel you say after the consonant.", details=gop_details)
    st.plotly_chart(spectrogram_figure(sound, g.start_s, g.end_s), width="stretch", alt="Spectrogram with the analysed stretch marked")
    st.plotly_chart(gop_figure(g.tracks, target, g.start_s, g.end_s), width="stretch", alt="Probability of each candidate sound over time")
    st.caption("What the recogniser decodes: " + (" ".join(g.phones) or "nothing"))
    st.caption("How likely each sound is at the start of the word: " + ", ".join(
        f"/{k}/ {v:.0%}" for k, v in sorted(g.probs.items(), key=lambda kv: -kv[1])))
    st.stop()

if RECOGNISER and target in ("s", "sh", "f"):      # fricatives: is this the right kind of sound for the word?
    gate_key = f"gate_{hashlib.md5(data).hexdigest()[:10]}"
    if gate_key not in st.session_state:
        with st.spinner("Checking the first sound…"):
            st.session_state[gate_key] = phoneme_check.first_consonant(sound)
    opens = st.session_state[gate_key]
    if opens is None:      # no consonant of any scored kind at the start (a vowel, silence, another consonant): do not score
        st.warning(f"The recogniser does not hear a consonant like {C.PHONE_LABEL[target]} at the start of this recording, so it is not scored. "
                   "Say the word again, with a short pause before it.", icon=":material/hearing:")
        log_unscored("Gate: no consonant heard at the start", dict(gate=opens))
        st.stop()
    if phoneme_check.wrong_kind(target, opens):
        st.warning(f"The recogniser hears {phoneme_check.GATE_LABEL[opens]} at the start of this recording, which is a different kind "
                   f"of sound from {C.PHONE_LABEL[target]} in \"{word}\". Check that you picked the word you said; it is not scored.",
                   icon=":material/hearing:")
        log_unscored(f"Gate: heard {phoneme_check.GATE_LABEL[opens]} at the start, a different kind of sound", dict(gate=opens))
        st.stop()

# From here: sounds scored without the recogniser (acoustic rules), or fricatives.
if word in C.NASAL_TARGETS:
    st.info(f"Scoring {C.PHONE_LABEL[target]} needs the phone recogniser (torch, transformers and the wav2vec2 checkpoint), "
            "which is not installed here. Praat formant measures alone are only 63% accurate for /m/ against /n/.", icon=":material/info:")
    st.stop()

if word in C.AFFRICATE_TARGETS:
    try:
        aff = measure_affricate(sound)
    except SegmentationError as exc:
        st.warning(f"{exc}. Check the word, and leave a short pause before it.")
        st.plotly_chart(spectrogram_figure(sound, 0.0, 0.0), width="stretch", alt="Spectrogram of the recording")
        log_unscored(str(exc))
        st.stop()
    p_ch = probability_ch(aff)
    show_verdict(classify_affricate(p_ch), f"Chance of /tʃ/ rather than /ʃ/: {p_ch:.0%} (an estimate). Experimental: 80% balanced accuracy on eight "
                 "ARCTIC voices in running speech, worst voice 74%. The rise time is not reliable in a noisy room.",
                 details=dict(p_ch=p_ch, rise_ms=aff.rise_ms, slope_db_per_ms=aff.slope_db_per_ms, hiss_ms=aff.hiss_ms))
    st.plotly_chart(spectrogram_figure(sound, aff.onset_s, aff.onset_s + aff.rise_ms / 1000), width="stretch",
                    alt="Spectrogram with the rise of the hiss shaded")
    with st.container(horizontal=True, gap="large"):
        st.metric("Rise time", f"{aff.rise_ms:.0f} ms")
        st.metric("Steepest climb", f"{aff.slope_db_per_ms:.1f} dB/ms")
        st.metric("Hiss length", f"{aff.hiss_ms:.0f} ms")
    st.caption("An affricate starts abruptly (about 36 ms to reach full strength in the data) and a plain /ʃ/ fades in (about 66 ms).")
    st.stop()

if word in C.STOP_TARGETS:
    try:
        stop = measure_vot(sound, strict=False)
    except SegmentationError as exc:
        st.warning(f"{exc}. Check the word, and leave a short pause before it.")
        st.plotly_chart(spectrogram_figure(sound, 0.0, 0.0), width="stretch", alt="Spectrogram of the recording")
        log_unscored(str(exc))
        st.stop()
    if stop.vot_ms > MAX_VOT_MS:
        st.warning(f"The gap between the burst and the voice is {stop.vot_ms:.0f} ms, much longer than a normal stop. The score below may be "
                   "unreliable: check the word, leave a short pause before it, and start speaking right after you press Record.")
    show_verdict(classify_stop(stop, target), details=dict(vot_ms=stop.vot_ms, burst_s=stop.burst_s, voicing_s=stop.voicing_s))
    st.plotly_chart(spectrogram_figure(sound, stop.burst_s, stop.voicing_s), width="stretch",
                    alt="Spectrogram with the interval from the burst to the start of voicing shaded")
    with st.container(horizontal=True, gap="large"):
        st.metric("VOT", f"{stop.vot_ms:.0f} ms")
        st.metric("Burst at", f"{stop.burst_s * 1000:,.0f} ms")
        st.metric("Voicing starts", f"{stop.voicing_s * 1000:,.0f} ms")
    st.caption(f"VOT is the time from the burst to the first voiced frame. About {VOT_P_MS:.0f} ms or more sounds like /p/ and less like /b/. "
               "Experimental: the threshold comes from eight ARCTIC voices in running speech (balanced accuracy 0.88), and the "
               "recording must start with a short pause. Room noise makes the burst finder unreliable.")
    st.stop()

verdict_box = st.container()

# ---------- Boundaries ----------
duration = float(sound.xmax)
seg_failed = False
try:
    b = find_boundaries(sound)
    auto, has_vowel = (b.onset_s, b.offset_s), b.found_vowel
except SegmentationError as exc:
    auto, has_vowel, seg_failed = (0.0, min(duration, 0.3)), True, True
    st.warning(f"{exc}. Drag the slider below to select the hiss; scoring starts once you do.")

st.subheader("Spectrogram")
digest = hashlib.md5(data).hexdigest()[:10]
onset, offset = st.slider(
    "Frication boundaries (s)", 0.0, duration,
    (round(auto[0], 3), round(auto[1], 3)), step=0.001, format="%.3f", key=f"bounds_{digest}",
)
spec_alt = "Spectrogram of the recording with the frication boundaries marked"
if seg_failed and (onset, offset) == (round(auto[0], 3), round(auto[1], 3)):
    st.plotly_chart(spectrogram_figure(sound, onset, offset), width="stretch", alt=spec_alt)
    st.stop()
if offset - onset < C.MIN_FRICATION_S:
    st.error("The selected hiss is too short to measure (< 30 ms). Widen the slider.")
    st.stop()

m = measure(sound, onset, offset, has_vowel)
if m.cog_hz < C.MIN_HISS_COG_HZ:       # the "hiss" is low-frequency (a vowel or noise), so no fricative can be scored
    st.warning(f"No hiss was found: the centre of gravity is only {m.cog_hz:,.0f} Hz, far below any /s ʃ f θ/. Not scored. "
               "Check the word, or drag the slider onto the hiss.", icon=":material/graphic_eq:")
    st.plotly_chart(spectrogram_figure(sound, onset, offset), width="stretch", alt=spec_alt)
    log_unscored("No hiss found (CoG too low)", dict(cog_hz=m.cog_hz, onset_s=onset, offset_s=offset))
    st.stop()
v = classify(m, target, th)
v_rule, reading, cal = v, None, st.session_state.get("calibration")
if cal is not None and st.session_state.get("use_calibration", True):
    reading = read_calibrated(extract(sound, onset, offset, has_vowel, with_f2=False), cal, load_model(), target)
    v = reading.verdict

if phoneme_check.available() and word in C.TARGETS:
    ck = f"hiss_{digest}_{onset:.3f}_{offset:.3f}"
    if ck not in st.session_state:
        st.session_state[ck] = phoneme_check.check(sound, onset, offset).heard
    if st.session_state[ck] is None:   # the recogniser hears none of /s ʃ f θ/ over the hiss: never show green
        st.warning(f"The recogniser does not hear /s ʃ f θ/ in the highlighted part, so {C.PHONE_LABEL[target]} is not scored. "
                   "Check the word, or move the slider onto the hiss.", icon=":material/hearing:")
        st.plotly_chart(spectrogram_figure(sound, onset, offset), width="stretch", alt=spec_alt)
        log_unscored("Recogniser hears none of /s ʃ f θ/ over the hiss", dict(onset_s=onset, offset_s=offset, cog_hz=m.cog_hz, rule_says=v.label))
        st.stop()
    v = phoneme_check.reconcile(v, st.session_state[ck])

with verdict_box:
    with st.container(border=True, horizontal=True, vertical_alignment="center", gap="large"):
        st.markdown(f"# :{MARK_COLOR[v.color]}[{v.mark}]", width="content")
        with st.container():
            st.markdown(f"### {v.label}")
            st.markdown(f"{v.message} · target **{word}** {C.PHONE_LABEL[target]}")
            st.caption(v.tip)
            if v.note:
                st.caption(v.note)
            if reading is not None:
                conf = lambda x: ">99%" if x > 0.995 else "<1%" if x < 0.005 else f"{x:.0%}"
                p = reading.probs
                st.caption(f"Calibrated to your voice ({cal.n_tokens} recordings) · model confidence: /s/ {conf(p['s'])}, "
                           f"/ʃ/ {conf(p['sh'])}, weak hiss {conf(p['f'])} (an estimate, not a measured probability) · "
                           f"rule-based reading: {v_rule.label}, heard {C.PHONE_LABEL[v_rule.heard]}")
            elif cal is None:
                st.caption("Tip: the Calibrate page tunes the scoring to your voice.")
        st.image(str(C.ARTICULATION_IMAGE[target]), width=170,
                 caption=f"How to make {C.PHONE_LABEL[target]}")
    log_result(verdict_dict(v), dict(
        onset_s=onset, offset_s=offset, has_vowel=has_vowel, cog_hz=m.cog_hz, relamp_db=m.relamp_db, fm_hz=m.fm_hz,
        duration_ms=m.duration_ms, snr_db=estimate_snr(sound),
        rule_verdict=dict(label=v_rule.label, heard=v_rule.heard),
        calibrated_probs=None if reading is None else reading.probs,
        recogniser_heard=st.session_state.get(f"hiss_{digest}_{onset:.3f}_{offset:.3f}")))

st.plotly_chart(spectrogram_figure(sound, onset, offset), width="stretch", alt=spec_alt)

with st.container(horizontal=True, gap="large"):
    st.metric("CoG", f"{m.cog_hz:,.0f} Hz")
    st.metric("Relative amplitude", "—" if m.relamp_db is None else f"{m.relamp_db:.1f} dB")
    st.metric("Peak (Fm)", f"{m.fm_hz:,.0f} Hz")
    st.metric("Duration", f"{m.duration_ms:.0f} ms")
    st.metric("SNR (est.)", f"{estimate_snr(sound):.0f} dB")

# ---------- Views ----------
st.space("small")
VIEWS = {"Compare": compare, "Patterns": patterns, "Detectors": detectors} if reference_available() else {"Patterns": patterns, "Detectors": detectors}
if phoneme_check.available():        # needs torch, transformers and the checkpoint; the app works without them
    VIEWS["Phoneme check"] = phoneme
view = st.segmented_control("View", list(VIEWS), default=next(iter(VIEWS)), required=True, key="view")
VIEWS[view].render(Ctx(sound=sound, data=data, name=name, word=word, target=target, onset=onset, offset=offset,
                       has_vowel=has_vowel, m=m, th=th, verdict=v, manual=manual))
