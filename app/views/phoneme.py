"""Phoneme-check view: a multilingual phone recogniser as a second opinion on the hiss."""
import streamlit as st

from fricative import config as C
from fricative import phoneme_check
from fricative.audio import load
from fricative.plots import phoneme_figure

from .context import Ctx

LABEL = {"S": "/s/", "SH": "/ʃ/", "F": "/f/", "TH": "/θ/"}


def render(ctx: Ctx) -> None:
    st.subheader("Phoneme check")
    st.caption("Experimental. A multilingual phone recogniser listens to the same recording and reports which sound it hears at the "
               "hiss. It is a second opinion and does not change the verdict.")
    pc = phoneme_check.check(load(ctx.data, ctx.name), ctx.onset, ctx.offset)
    with st.container(border=True):
        if pc.heard is None:
            st.markdown("### The recogniser hears no fricative at the hiss")
            st.markdown("It cannot confirm the verdict above.")
        else:
            st.markdown(f"### The recogniser hears {LABEL[pc.heard]}")
            if phoneme_check.agrees(ctx.verdict.heard, pc.heard):
                st.markdown(f"It **agrees** with the verdict above ({C.PHONE_LABEL[ctx.verdict.heard]}).")
            else:
                st.markdown(f"It **disagrees** with the verdict above, which heard {C.PHONE_LABEL[ctx.verdict.heard]}. "
                            "Listen to the recording again and check the hiss boundaries.")
        st.caption(f"Phone string for the whole clip: {pc.decoded or '(nothing)'}")
    st.plotly_chart(phoneme_figure(pc), width="stretch", alt="Evidence for /s/, /ʃ/, /f/ and /θ/ at the hiss and over the clip")
    with st.expander("How much can this be trusted?", icon=":material/rule:"):
        st.markdown(
            "The recogniser reads the whole clip, so it can lean on the rest of the word. Tested on eight ARCTIC voices "
            "(word-initial hiss, 320 splices per case):\n"
            "- **/s/ vs /ʃ/:** 0.997 on whole words and still 0.94 on the hiss alone. When a /ʃ/ hiss is spliced into a word "
            "that has /s/, it follows the hiss 73% of the time (90% for /s/ hiss in a /ʃ/ word).\n"
            "- **/f/ vs /θ/:** 0.988 on whole words but only 0.67 on the hiss alone, and when the hiss and the word disagree it "
            "follows the **word** 69–73% of the time. Treat its /f/ vs /θ/ answer as a reading of the word, not of your hiss.\n"
            "- **Noise:** at 20 dB SNR /s/ vs /ʃ/ stays at 0.995; at 10 dB /f/ vs /θ/ falls to 0.71.\n\n"
            "Checkpoint: `facebook/wav2vec2-xlsr-53-espeak-cv-ft` (Apache-2.0). Not yet tested on isolated words or on deaf and "
            "hard-of-hearing speakers.")
