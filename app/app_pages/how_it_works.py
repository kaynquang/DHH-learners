"""How it works: a qualitative tour of every mechanism, illustrated on a D1 sample."""
import pandas as pd
import streamlit as st

from fricative import config as C
from fricative.audio import load
from fricative.calibrated import load_model
from fricative.classify import MARKS, LABELS
from fricative.measure import analysis_window, measure
from fricative.plots import decision_figure, detection_figure, spectrogram_figure
from fricative.reference import load_reference
from fricative.segment import trace_boundaries
from fricative.segment_alt import METHODS

st.title("How it works")
st.caption("What the app does with a recording, step by step, and why each step is built the way it is.")

st.markdown("""
```mermaid
graph LR
    A[Recording] --> B[Find the frication]
    B --> C[Measure the middle 50%]
    C --> D[Score: f or sibilant, then s or ʃ]
    D --> E[Compare with D1 voices]
```
""")

refs = {r.file: r for r in load_reference()}
if not refs:
    st.info("The step-by-step illustration needs the D1 dictionary recordings (SOUNDS/ and boundaries.csv), which are not part of this repository.", icon=":material/info:")
    st.stop()
choice = st.selectbox("Example recording (D1)", list(refs), key="explain_sample")
row = refs[choice]
sound = load(row.path)
trace = trace_boundaries(sound)

# ---------------------------------------------------------------------------
st.header("Reading the audio")
st.markdown(
    "Files are decoded with **Parselmouth**, which is Praat running inside Python. Using the same "
    "decoder as the phonetician's manual measurements matters: MP3 decoders differ in how much "
    "padding they add at the start, and a few milliseconds of shift would move every boundary. "
    "Stereo recordings are mixed down to mono and anything after 5 seconds is ignored."
)

# ---------------------------------------------------------------------------
st.header("Finding the frication")
st.markdown(
    "A fricative such as /s/ is **turbulent noise**: air squeezed through a narrow gap. It has a lot of "
    "energy at high frequencies and no regular rhythm. The vowel that follows (the *ee* in *see*) is "
    "the opposite: the vocal folds vibrate, so it is **periodic** and Praat can measure its pitch. "
    "The detector uses exactly these two facts."
)
st.markdown("""
1. **Listen to the high band.** Every 2 ms, measure the energy between 2.5 and 12 kHz, where the hiss lives.
2. **Learn the room.** The quietest 5% of frames tell us how loud the background is. The threshold is
   that noise floor **plus 15 dB**, so it rises in a noisy room and falls in a quiet one; nothing is hard-coded in dB.
3. **Join the pieces.** Frames above the threshold form runs. Gaps shorter than 20 ms are bridged, because
   a weak /f/ flickers around the threshold.
4. **Anchor on the vowel.** Find where voicing starts. The frication is the run that **leads straight into** it:
   its start is the onset and the voicing start is the offset. A click or a breath before the word is a separate
   run, so it is ignored.
5. **No vowel?** If the speaker only said "sss", the longest run is used and the vowel-based checks are skipped.
""")
st.plotly_chart(detection_figure(trace), width="stretch",
                alt="High-band energy over time with noise floor, threshold, runs, voicing start and result")
st.caption(
    "Grey line: high-band energy. Dotted grey: noise floor. Dashed: floor + 15 dB. Blue bands: runs above the "
    "threshold. Green dotted: voicing starts. Red: the chosen onset and offset."
)
if trace.boundaries is not None:
    b = trace.boundaries
    st.plotly_chart(spectrogram_figure(sound, b.onset_s, b.offset_s), width="stretch",
                    alt="Spectrogram with the detected frication boundaries")
    c1, c2, c3 = st.columns(3)
    c1.metric("Detected onset", f"{b.onset_s * 1000:.0f} ms", f"{(b.onset_s - row.start_s) * 1000:+.0f} ms vs manual",
              delta_color="off")
    c2.metric("Detected offset", f"{b.offset_s * 1000:.0f} ms", f"{(b.offset_s - row.end_s) * 1000:+.0f} ms vs manual",
              delta_color="off")
    c3.metric("Frication length", f"{(b.offset_s - b.onset_s) * 1000:.0f} ms")
else:
    st.warning(f"The detector failed on this file: {trace.error}.")

# ---------------------------------------------------------------------------
st.header("The three sounds")
st.markdown(
    "All three are made by forcing air through a narrow gap. What differs is **where** the gap is and how "
    "much space lies in front of it. That space acts like a resonator: the smaller it is, the higher the hiss."
)
for col, phone in zip(st.columns(3, gap="large"), ("s", "sh", "f")):
    with col:
        st.image(str(C.ARTICULATION_IMAGE[phone]), width=220, caption=f"{C.PHONE_LABEL[phone]}  as in "
                 f"{next(w for w, p in C.TARGETS.items() if p == phone)}")
        st.caption(C.ARTICULATION_NOTE[phone])
st.markdown(
    "- **/s/** has the smallest space in front of the constriction, so its energy sits highest (CoG ≈ 5–6 kHz).\n"
    "- **/ʃ/** moves the constriction back and rounds the lips, adding space, so its energy is lower (≈ 3–4 kHz).\n"
    "- **/f/** has almost no space in front and the air does not hit the teeth, so the hiss is weak and flat: "
    "its CoG says little, but its loudness relative to the vowel says a lot."
)

# ---------------------------------------------------------------------------
st.header("Measuring")
st.markdown(
    "Only the **middle 50%** of the frication is measured. The first and last quarters are transitions "
    "(the tongue is still moving, the vowel is starting), and they are also where a boundary error would land. "
    "Trimming them makes the numbers stable even when the boundaries are a little off."
)
if trace.boundaries is not None:
    m = measure(sound, trace.boundaries.onset_s, trace.boundaries.offset_s, trace.boundaries.found_vowel)
    a, b2 = analysis_window(trace.boundaries.onset_s, trace.boundaries.offset_s)
    st.markdown(f"Analysis window for this file: **{a * 1000:.0f}–{b2 * 1000:.0f} ms**.")
    c1, c2, c3 = st.columns(3)
    c1.metric("CoG", f"{m.cog_hz:,.0f} Hz")
    c2.metric("Relative amplitude", "—" if m.relamp_db is None else f"{m.relamp_db:.1f} dB")
    c3.metric("Peak (Fm)", f"{m.fm_hz:,.0f} Hz")
st.markdown("""
- **Centre of gravity (CoG)** is the balance point of the spectrum: where the hiss energy sits on average.
  /s/ is made with a small cavity in front of the teeth, so its energy is high (around 5–6 kHz);
  /ʃ/ has a larger cavity with rounded lips, so its energy is lower (around 3–4 kHz).
  It is computed exactly as in the manual Praat workflow: *Extract part* with a **Rectangular** window,
  *To Spectrum*, *Get centre of gravity* with power 2. This reproduces the manual values within 2 Hz.
- **Relative amplitude** compares the loudness of the hiss with the loudness of the vowel right after it
  (20–80 ms after the offset). /s/ and /ʃ/ are sibilants: the air jet hits the teeth and the hiss is almost as
  loud as the vowel. /f/ is not: it is about 20 dB quieter. This is what separates /f/, whose flat spectrum makes
  its CoG meaningless.
- **Peak frequency (Fm)** is the highest point of a smoothed (multitaper) spectrum between 2 and 8 kHz.
  It is shown for reference only.
""")

# ---------------------------------------------------------------------------
st.header("Scoring")
th = C.Thresholds(**{f: float(st.session_state.get(k, getattr(C.DEFAULT_THRESHOLDS, f)))
                     for f, k in {"cog_s_sh_hz": "th_cog", "relamp_f_db": "th_relamp",
                                  "cog_margin_hz": "th_cog_margin", "relamp_margin_db": "th_relamp_margin"}.items()})
st.markdown(f"""
The decision takes two steps, mirroring how the sounds differ:

1. **Is it /f/?** If the hiss is more than **{abs(th.relamp_f_db):.0f} dB** quieter than the vowel, it is /f/.
2. **/s/ or /ʃ/?** Otherwise, a CoG of at least **{th.cog_s_sh_hz:,.0f} Hz** is /s/, below is /ʃ/.

If the sound heard is not the target, the verdict is **{MARKS['red']} {LABELS['red']}**. If it is the target
but close to a threshold (within {th.cog_margin_hz:,.0f} Hz or {th.relamp_margin_db:.1f} dB, the shaded bands),
it is **{MARKS['yellow']} {LABELS['yellow']}**. Otherwise it is **{MARKS['green']} {LABELS['green']}**.
The marks are the ones Japanese teachers use on tests. Thresholds come from only two dictionary voices and can be
changed in *Scoring settings* on the Practice page.
""")
st.plotly_chart(decision_figure(th), width="stretch", alt="Scoring regions for /s/, /ʃ/ and /f/ with yellow margins")

# ---------------------------------------------------------------------------
st.header("Calibrated scoring")
_m = load_model()["meta"]["leave_one_voice_out"]
st.markdown(
    "Two voices can say the same sound with very different numbers: the CoG of /s/ differed by about 1,000 Hz between two "
    "reference voices, more than the gap between /s/ and /ʃ/ in one voice. Fixed thresholds therefore fail on some voices "
    "(in the tests, the CoG rule dropped to 56% on one of eight).\n\n"
    "The **Calibrate** page fixes this. The learner says see, she and fee twice each. The app takes the mean and spread of 13 "
    "measurements over those six recordings and expresses every later recording in the learner's own units. Two small linear "
    "models, trained on eight reference voices that were normalised the same way, then decide:\n"
    "1. weak hiss (/f/, /θ/) or sibilant, from relative amplitude and three variability cues (without a vowel, from the "
    "variability cues alone);\n"
    "2. /s/ or /ʃ/, from all 13 measurements.\n\n"
    f"Tested by holding out one voice at a time and calibrating it from six of its own tokens: /s/ vs /ʃ/ "
    f"{_m['s_vs_sh_if_sibilant']['mean']:.0%}, weak hiss vs sibilant {_m['family']['mean']:.0%}, all three together "
    f"{_m['three_way']['mean']:.0%} (worst voice {_m['three_way']['worst']:.0%}). "
    "These tokens came from running speech, not isolated words, and no deaf or hard-of-hearing speaker was included, so treat the "
    "numbers as a guide until `app/validate_calibrated.py` has been run on real recordings. The confidence shown on the Practice "
    "page is the model's score, not a measured probability."
)

# ---------------------------------------------------------------------------
st.header("Alternative detectors")
st.markdown(
    "Four other ways of finding the frication were compared on D1. They are kept so that the "
    "*Ablation studies* section on the Practice page can run them on any recording."
)
QUALITATIVE = {
    "anchored": ("Uses both cues that define the sound: high-frequency noise and the start of voicing. "
                 "Robust to clicks and breaths before the word.",
                 "Needs a vowel to anchor; without one it falls back to the longest run."),
    "energy_pitch_v1": ("Same cues, simplest form. Very accurate on clean recordings.",
                        "Takes the first loud frame as the onset, so any click or breath before speaking "
                        "moves the onset by hundreds of milliseconds."),
    "band_ratio": ("Needs no pitch tracker: the vowel is where low frequencies take over.",
                   "Vowels and voiced noise can make the low band win too early. On See - US it collapses "
                   "the frication to almost nothing."),
    "zcr": ("Very cheap: noise crosses zero far more often than a vowel.",
            "Zero crossings also come from background noise; onsets of weak fricatives start ~30 ms late "
            "and errors grow quickly with noise."),
    "frame_cog": ("Uses the same quantity that is scored, frame by frame.",
                  "A /ʃ/ or a weak /f/ can drop below the 2.5 kHz cut-off, so runs break up; worst under noise."),
}
st.table(pd.DataFrame([
    {"Detector": METHODS[k].name, "How it works": METHODS[k].summary, "Strength": s, "Weakness": w}
    for k, (s, w) in QUALITATIVE.items()
]).set_index("Detector"))
st.caption("MFA (forced alignment) was not tried: it needs a transcript and is known to be weakest on fricatives.")

# ---------------------------------------------------------------------------
st.header("Known limits")
st.markdown("""
- Thresholds come from two dictionary voices (D1). They will be replaced by norms from 6–10 fluent speakers (D2).
- The D1 MP3 files lose everything above about 12 kHz; a real microphone does not, so live CoG values can be higher.
- In heavy noise (SNR around 20 dB or worse) a weak /f/ disappears into the noise. Check the boundaries on the
  spectrogram and drag them if needed.
""")
