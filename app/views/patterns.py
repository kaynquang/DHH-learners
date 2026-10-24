"""Patterns view (experimental): the recording against two ARCTIC reference voices."""
import hashlib

import pandas as pd
import streamlit as st

from fricative import config as C
from fricative.audio import load
from fricative.patterns import SCALAR_KEYS, contrast_threshold, experimental_verdict, extract, load_reference, template_distances
from fricative.plots import (f2_figure, pattern_distribution_figure, template_figure, trajectory_figure, variability_figure)

from .context import Ctx


@st.cache_data
def reference() -> dict:
    return load_reference()


@st.cache_data(max_entries=8)
def analyse(digest: str, data: bytes, name: str, onset: float, offset: float, has_vowel: bool, max_formant: float):
    return extract(load(data, name), onset, offset, has_vowel, max_formant)


def render(ctx: Ctx) -> None:
    st.subheader("Patterns")
    st.caption("Experimental. Your recording, analysed at 16 kHz and set against two CMU ARCTIC voices.")
    ref = reference()
    voice = st.segmented_control("Reference voice", list(ref["voices"]), default="bdl", required=True, key="ref_voice",
                                 format_func=lambda v: f"{v} · {ref['voices'][v]['sex']}")
    f = analyse(hashlib.md5(ctx.data).hexdigest(), ctx.data, ctx.name, ctx.onset, ctx.offset, ctx.has_vowel,
                ref["voices"][voice]["max_formant_hz"])
    ev = experimental_verdict(f, ref, voice)
    dist = template_distances(f, ref, voice)

    # ---------- Experimental reading ----------
    with st.container(border=True):
        st.markdown("**Experimental reading**")
        thr = contrast_threshold(ref, voice)
        cue_values = {"Relative amplitude": f"{f.scalars['relamp']:.1f} dB (boundary {C.DEFAULT_THRESHOLDS.relamp_f_db:.0f})",
                      "Spectral contrast": f"{f.scalars['contrast']:.1f} dB (boundary {thr:.1f})"}
        st.dataframe(pd.DataFrame([{"Cue": k, "Value": cue_values[k],
                                    "Says": "sibilant (/s/ or /ʃ/)" if v == "sibilant" else "weak hiss (/f/ or /θ/)"}
                                   for k, v in ev.family_cues.items()]), hide_index=True,
                     alt="What each cue says about whether the hiss is a sibilant or a weak hiss")
        if "Relative amplitude" not in ev.family_cues:
            st.caption("No vowel after the hiss, so only spectral contrast could be used.")
        if ev.family == "unsure":
            st.markdown("### The cues disagree")
            st.caption("Could be a sibilant or a weak hiss, so nothing is scored. Try the other reference voice.")
        elif ev.family == "sibilant":
            agree = "all three rules agree" if ev.unanimous else "the rules disagree (2 of 3)"
            st.markdown(f"### Looks like {C.PHONE_LABEL[ev.heard]}")
            st.caption(f"Target word: {ctx.word} {C.PHONE_LABEL[ctx.target]} · {agree}")
            st.dataframe(pd.DataFrame([{"Rule": k, "Says": C.PHONE_LABEL[v]} for k, v in ev.votes.items()]), hide_index=True,
                         alt="What each pattern rule says about the recording")
        else:
            st.markdown("### Weak hiss: /f/ or /θ/")
            st.caption(f"Not scored (these two cannot be told apart reliably). Nearest spectral template: "
                       f"{'/f/' if ev.weak_nearest == 'F' else '/θ/'}")
        st.caption(f"For comparison, the verdict above is {ctx.verdict.mark} {ctx.verdict.label} "
                   f"(heard {C.PHONE_LABEL[ctx.verdict.heard]}).")
    st.warning(
        "These rules come from a single reference voice and use no speaker calibration. In the experiments, speaker differences "
        "(for example 1,000 Hz in the CoG of /s/ between two voices) were larger than the difference between sounds, and "
        "calibrating to the speaker was the biggest improvement. Try both reference voices and treat the result as a hint.",
        icon=":material/science:")

    # ---------- 1. Shape features ----------
    st.subheader("1 · Shape features")
    st.caption("Boxes: where the reference tokens of each sound fall (whiskers 5th–95th percentile, box 25th–75th, line = median). "
               "The red line is your recording.")
    st.plotly_chart(pattern_distribution_figure(f, ref, voice), width="stretch",
                    alt="Distribution of six spectral features for each reference sound with your recording marked")
    with st.expander("Your numbers"):
        st.dataframe(pd.DataFrame([{"Feature": k, "Value": None if f.scalars[k] != f.scalars[k] else round(f.scalars[k], 3)}
                                   for k in SCALAR_KEYS]), hide_index=True, alt="Feature values of your recording")

    # ---------- 2. Spectral template ----------
    st.subheader("2 · Spectral template")
    st.caption("Each thin line is the average shape of a sound (shaded: ±1 SD) once every token's own loudness is removed. "
               "Your recording is the thick red line.")
    left, right = st.columns([3, 1], gap="large")
    with left:
        st.plotly_chart(template_figure(f, ref, voice), width="stretch",
                        alt="Spectral shape of your recording over the average shape of each reference sound")
    with right:
        nearest = min(("S", "SH", "F", "TH"), key=lambda p: dist[p])
        st.markdown("**Distance to each template** (dB, smaller is closer)")
        st.dataframe(pd.DataFrame([{"Sound": ("→ " if p == nearest else "") + {"S": "/s/", "SH": "/ʃ/", "F": "/f/", "TH": "/θ/"}[p],
                                    "Distance": round(dist[p], 1)} for p in ("S", "SH", "F", "TH")]),
                     hide_index=True, alt="Distance from your recording to each spectral template")

    # ---------- 3. Over time ----------
    st.subheader("3 · Over time")
    st.caption("The first and last tenth of a hiss are transitions to and from the vowel, so CoG is lower there. "
               "Your hiss ends where voicing starts, so its last tenth includes a few milliseconds of vowel; the reference hisses end "
               "where the aligner places the end of the noise, so expect your last point to sit lower. "
               "F2 is measured against the vowel's middle (a held vowel is capped at 0.12 s to match the reference).")
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("**CoG across the hiss**")
        st.plotly_chart(trajectory_figure(f, ref, voice), width="stretch",
                        alt="Centre of gravity in five parts of the hiss for your recording and the reference sounds")
    with b:
        st.markdown("**F2 after the hiss**")
        st.plotly_chart(f2_figure(f, ref, voice), width="stretch",
                        alt="Second formant after the hiss relative to the vowel middle for your recording and the reference sounds")

    # ---------- 4. Variability ----------
    st.subheader("4 · Variability")
    st.caption("Sibilants (/s/, /ʃ/) are peaky and steady: high spectral contrast and little CoG wobble. /f/ and /θ/ are flat and "
               "unsteady, /θ/ most of all. The dotted line is the boundary used to tell the two families apart.")
    st.plotly_chart(variability_figure(f, ref, voice), width="stretch",
                    alt="Spectral contrast and CoG wobble of your recording against the reference sounds with the family boundary")

    # ---------- Evidence ----------
    with st.expander("How much data is behind this?", icon=":material/rule:"):
        m = ref["meta"]
        counts = {ph: sum(v["phones"][ph]["n"] for v in ref["voices"].values()) for ph in ("S", "SH", "F", "TH")}
        st.markdown(
            f"**Reference shown on this page:** {m['tokens']:,} fricative tokens from 2 voices (bdl male, slt female), the first 300 "
            f"sentences of each in CMU ARCTIC, boundaries from MFA and not checked by hand. /s/ {counts['S']}, /ʃ/ {counts['SH']}, "
            f"/f/ {counts['F']}, /θ/ {counts['TH']}. The three rules above use one of these voices and no calibration.\n\n"
            "**Eight-voice test** (train on 7 voices, test on the 8th; about 8,500 tokens): \n"
            "- /s/ vs /ʃ/: CoG alone 87% (worst voice 56%); with speaker normalisation 93%; a 13-feature model with speaker "
            "normalisation 97%, better than normalised CoG on 7 of 8 voices and worse on none (gain +1.5 to +8 points). Without "
            "normalisation the same model drops to 90% (worst voice 54%).\n"
            "- Sibilant vs weak hiss: relative amplitude 89%; spectral contrast alone 88% but only 72–74% on two voices; relative "
            "amplitude with three variability cues 93–94%.\n"
            "- /f/ vs /θ/: at most about 75%. F2 added about 2 points on the same tokens, within noise. Display only.\n"
            "- The different spread of /s/ and /ʃ/ gave no gain.\n"
            "- Calibration: normalising from 6 of the learner's own tokens (see, she, fee, twice each) reached 95% when training used "
            "the same protocol; with a different token mix it fell to 91%.\n\n"
            "Tokens come from running speech, not isolated words, and the boundaries are the aligner's, so the numbers are an upper "
            "guide for the app.\n\n"
            "The two-voice write-up with every figure is in `docs/exploration/spectral-patterns.html`; the eight-voice scripts are in `explore/pattern_lab/`.")
