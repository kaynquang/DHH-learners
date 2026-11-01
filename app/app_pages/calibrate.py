"""Calibrate page: six short recordings (see, she, fee, twice each) so the app can learn the learner's own voice."""
import pandas as pd
import streamlit as st

from fricative.audio import limit_duration, load
from fricative.calibrated import CAL_WORDS, build_calibration, save_profile
from fricative.noise import check, noise_floor_db
from fricative.patterns import SCALAR_KEYS, extract
from fricative.plots import spectrogram_figure
from fricative.reference import load_reference
from fricative.segment import SegmentationError, find_boundaries
from views.autorecord import auto_record, playback

st.title("Calibrate")
st.caption("Say see, she and fee, twice each. The app uses these six recordings to learn how your voice sounds before it "
           "judges it. It takes about a minute, and nothing is stored after you close the page.")

SAMPLES = {r.file: r for r in load_reference()}
tokens = st.session_state.setdefault("cal_tokens", [])
N = len(CAL_WORDS)


def finish() -> None:
    cal = build_calibration([t["feats"] for t in st.session_state["cal_tokens"]])
    st.session_state["calibration"] = cal
    if st.session_state.get("profile_select", "No profile") != "No profile":
        save_profile(cal, st.session_state["cal_tokens"], st.session_state["profile_select"])


def start_over() -> None:
    st.session_state["cal_tokens"] = []
    st.session_state.pop("calibration", None)
    st.session_state.pop("cal_noise_db", None)            # measure the room again


def demo() -> None:
    """Fill the six steps from the UK dictionary voice, for people without a microphone."""
    st.session_state["cal_tokens"] = []
    for w in CAL_WORDS:
        r = SAMPLES[f"{w.capitalize()} - UK.mp3"]
        snd = load(r.path)
        st.session_state["cal_tokens"].append(dict(word=w, feats=extract(snd, r.start_s, r.end_s, True, with_f2=False)))
    finish()


done = len(tokens)
st.progress(done / N, text=f"{done} of {N} recorded")

if done == N and st.session_state.get("calibration") is not None:
    cal = st.session_state["calibration"]
    profile = st.session_state.get("profile_select", "No profile")
    saved_note = (f"Saved in the profile “{profile}” and loaded again when you choose it."
                  if profile != "No profile" else "Not saved: add a profile in the sidebar, then calibrate again to keep it.")
    st.success(f"Calibrated from {cal.n_tokens} recordings. Practice now judges you against your own voice. {saved_note}",
               icon=":material/check_circle:")
    st.dataframe(pd.DataFrame([{"Word": t["word"], **{k: round(t["feats"].scalars[k], 2) for k in ("cog", "contrast", "relamp")}}
                               for t in tokens]).rename(columns={"cog": "CoG (Hz)", "contrast": "Contrast (dB)", "relamp": "Relative amplitude (dB)"}),
                 hide_index=True, alt="Measurements of the six calibration recordings")
    st.button("Redo calibration", icon=":material/restart_alt:", on_click=start_over, key="cal_redo")
    st.stop()

VERDICT_TEXT = {"good": ("success", "Quiet room: good."), "ok": ("info", "A little noise: results should still be fine."),
                "noisy": ("warning", "Too noisy: the voice is not far enough above the room noise. Move somewhere quieter and record this word again.")}


def room_check() -> None:
    """Before the first word: 3 seconds of silence give the noise level of the room."""
    st.markdown("### Room check: stay silent")
    st.caption("Press record and say nothing for 3 seconds, so the app can measure how noisy the room is. It is used to warn you "
               "if a word is recorded too close to the noise.")
    rec = auto_record("cal_room_rec")
    if rec is not None:
        level = noise_floor_db(load(rec, "recording.wav"))
        st.metric("Room noise", f"{level:.0f} dBFS", help="Lower is quieter. Typical quiet rooms are below −55 dBFS on this kind of microphone.")
        if st.button("Use this level", type="primary", key="cal_room_use"):
            st.session_state["cal_noise_db"] = level
            st.rerun()
    if st.button("Skip the room check", key="cal_room_skip"):
        st.session_state["cal_noise_db"] = None
        st.rerun()
    if SAMPLES:
        st.button("Demo: use the UK dictionary voice", on_click=demo, key="cal_demo_room", help="Calibrates with recorded sample words, no microphone needed.")
    st.stop()


if "cal_noise_db" not in st.session_state and done == 0:
    room_check()
noise_db = st.session_state.get("cal_noise_db")

i = done
word = CAL_WORDS[i]
st.markdown(f"### Step {i + 1} of {N}: say **{word}**")
source = st.segmented_control("Input", ["Record", "Sample", "Upload"] if SAMPLES else ["Record", "Upload"], default="Record", required=True, key=f"cal_source_{i}")
data, name = None, None
if source == "Record":
    st.caption(f"Press record and say “{word}”. It stops by itself after 3 seconds.")
    rec = auto_record(f"cal_rec_{i}")
    if rec is not None:
        data, name = rec, "recording.wav"
elif source == "Upload":
    up = st.file_uploader("Upload a wav or mp3 file", type=["wav", "mp3"], key=f"cal_upload_{i}")
    if up is not None:
        data, name = up.getvalue(), up.name
else:
    options = list(SAMPLES)
    choice = st.selectbox("D1 sample", options, index=options.index(f"{word.capitalize()} - UK.mp3"), key=f"cal_sample_{i}")
    data, name = SAMPLES[choice].path.read_bytes(), choice

if data is not None:
    try:
        sound, _ = limit_duration(load(data, name))
        b = find_boundaries(sound)
    except (ValueError, SegmentationError) as exc:
        st.error(f"{exc}. Please record this word again.")
        st.stop()
    room = check(noise_db, sound) if noise_db is not None and source == "Record" else None
    if room is not None:
        kind, text = VERDICT_TEXT[room.verdict]
        getattr(st, kind)(f"{text} Word is {room.snr_db:.0f} dB above the room noise.")
    playback(data, f"cal_play_{i}", name)
    st.plotly_chart(spectrogram_figure(sound, b.onset_s, b.offset_s), width="stretch", alt="Spectrogram of the recording with the hiss marked")
    if st.button("Use this recording", type="primary", key=f"cal_accept_{i}"):
        st.session_state["cal_tokens"].append(dict(word=word, feats=extract(sound, b.onset_s, b.offset_s, b.found_vowel, with_f2=False)))
        if len(st.session_state["cal_tokens"]) == N:
            finish()
        st.rerun()

st.space("small")
left, right = st.columns(2)
left.button("Start over", on_click=start_over, key="cal_reset", disabled=done == 0)
if SAMPLES:
    right.button("Demo: use the UK dictionary voice", on_click=demo, key="cal_demo", help="Calibrates with recorded sample words, no microphone needed.")
