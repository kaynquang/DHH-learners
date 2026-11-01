"""Teacher view: the recording as a readable spectrogram, for every sound, with what the scoring did with it, so a teacher or a researcher
can follow a child alongside the learner app (record here, or upload a file the learner app logged).

The picture is the whole recording (time in seconds, frequency in Hz, dB scale) with the stretch the scoring measured shaded, and for
/s/, /ʃ/ and /f/ the /s/-/ʃ/ boundary of the child's voice size. Next to it: what the child was shown (label, stars), the recording quality,
the voice size, and the numbers behind the verdict. Nothing is stored.
"""
import pandas as pd
import streamlit as st

from fricative import config as C
from fricative import gop, phoneme_check, vtl
from fricative.audio import limit_duration, load
from fricative.calibrated import load_voice, voice_scale
from fricative.noise import recording_quality
from fricative.pipeline import score_fricative
from fricative.plots import gop_figure, teacher_spectrogram
from learner import result, stars
from learner.lessons import LESSONS, ORDER
from views.autorecord import auto_record, playback

st.title("Teacher view")
st.caption("See the sound the child just made, for every sound, with the numbers behind the score.")

profile = st.session_state.get("profile_select")
child = None if profile in (None, "No profile") else profile
voice = load_voice(child)

c1, c2, c3 = st.columns([3, 2, 2])
word = c1.segmented_control("Target sound", ORDER, default="see", required=True, key="tv_word", format_func=lambda w: LESSONS[w].label)
phone = LESSONS[word].phone
scale = c2.number_input("Voice size ×", 0.5, 2.0, value=float(voice_scale(child)), step=0.01, key=f"tv_scale_{child}",
                        help="Moves the /s/-/ʃ/ boundary for this child (1.00 = the adult thresholds). From the child's Sound Check in the learner app; "
                             "change it to see what a different value would do.")
source = c3.segmented_control("Input", ["Record", "Upload"], default="Record", required=True, key="tv_source")
if voice:
    st.caption(f"Child “{child}”: F3 of “aaa” {voice['f3_hz']:.0f} Hz, voice size ×{voice['scale']:.2f}.")
else:
    st.caption("No Sound Check for the chosen profile: voice size ×1.00 (pick a profile in the sidebar, or type a value).")

data, name = None, None
if source == "Record":
    st.caption(f"Say “{word}”. It stops by itself after 3 seconds.")
    rec = auto_record("tv_rec")
    if rec is not None:
        data, name = rec, "recording.wav"
else:
    up = st.file_uploader("Upload a wav or mp3 file (for example a recording from the Log page)", type=["wav", "mp3"], key="tv_upload")
    if up is not None:
        data, name = up.getvalue(), up.name
if data is None:
    st.info("Record or upload a word to begin.", icon=":material/mic:")
    st.stop()

playback(data, "tv_play", name)
try:
    sound, _ = limit_duration(load(data, name))
except ValueError as exc:
    st.error(str(exc))
    st.stop()

th = vtl.thresholds(scale)
windows: list[tuple[float, float, str]] = []
lines: list[tuple[float, str]] = []
numbers: list[tuple[str, str]] = []
tracks_fig = None

if phone in ("s", "sh", "f"):
    s = score_fricative(sound, phone, None, th)
    lines.append((th.cog_s_sh_hz, f"/s/–/ʃ/ boundary {th.cog_s_sh_hz:.0f} Hz"))
    if s.boundaries:
        windows.append((s.boundaries.onset_s, s.boundaries.offset_s, "hiss measured"))
    if s.measures:
        m = s.measures
        numbers += [("Hiss", f"{m.onset_s:.3f} to {m.offset_s:.3f} s ({m.duration_ms:.0f} ms)"), ("CoG of the hiss", f"{m.cog_hz:.0f} Hz"),
                    ("Relative amplitude (hiss vs vowel)", "–" if m.relamp_db is None else f"{m.relamp_db:.1f} dB"),
                    ("Thresholds used", f"CoG {th.cog_s_sh_hz:.0f} ± {th.cog_margin_hz:.0f} Hz, relamp {th.relamp_f_db:.0f} ± {th.relamp_margin_db:.0f} dB")]
    if s.rule_verdict:
        numbers.append(("Rule (numbers only)", f"{s.rule_verdict.color}: {s.rule_verdict.message}"))
    if s.verdict:
        numbers.append(("After the recogniser", f"{s.verdict.color}: {s.verdict.message}"))
    if s.notice:
        numbers.append(("Not scored because", s.notice))
elif phone in gop.SUPPORTED and phoneme_check.available():
    g = gop.score(sound, phone)
    if g is None:
        numbers.append(("Not scored because", "No speech was heard."))
    else:
        windows.append((g.start_s, g.end_s, "GOP window"))
        numbers += [("Window analysed", f"{g.start_s:.3f} to {g.end_s:.3f} s"), ("Decoded", " ".join(g.phones) or "–"),
                    ("Probabilities", ", ".join(f"/{n}/ {p:.2f}" for n, p in sorted(g.probs.items(), key=lambda kv: -kv[1])))]
        tracks_fig = gop_figure(g.tracks, phone, g.start_s, g.end_s)
        v = gop.verdict(g, phone)
        numbers.append(("Verdict", "not sure which sound" if v is None else f"{v.color}: {v.message}"))
else:
    numbers.append(("Not scored", "No scoring is available for this sound on this machine."))

st.plotly_chart(teacher_spectrogram(sound, windows, lines), width="stretch",
                alt="Spectrogram of the whole recording, with the part the scoring measured shaded")

left, right = st.columns(2)
with left:
    st.subheader("What the child saw")
    res = result.score(data, phone, scale)
    if res.color is None:
        st.warning(res.notice or "Nothing could be scored.")
    else:
        earned = stars.stars(res.color, res.closeness)
        st.markdown(f"**{res.label}** · {res.message}  \n{'★' * earned}{'☆' * (stars.MAX_STARS - earned)}  ({earned} of {stars.MAX_STARS} stars)")
        if res.tip:
            st.caption(res.tip)
        if res.closeness is not None:
            st.caption(f"Closeness to the target: {res.closeness:.2f} (green from 0.80, yellow 0.50 to 0.80, red below)")
    q = recording_quality(sound)
    st.subheader("Recording quality")
    qa, qb, qc = st.columns(3)
    qa.metric("Louder than the room by", f"{q.snr_db:.0f} dB")
    qb.metric("Level", f"{q.level_db:.0f} dBFS")
    qc.metric("Verdict", {None: "fine", "noisy": "too noisy", "quiet": "too quiet", "loud": "too loud"}[q.problem])
with right:
    st.subheader("Numbers behind the verdict")
    st.dataframe(pd.DataFrame(numbers, columns=["Measure", "Value"]), hide_index=True, width="stretch")
if tracks_fig is not None:
    st.subheader("How likely each sound is, over time")
    st.plotly_chart(tracks_fig, width="stretch", alt="Probability of each candidate sound over time")
