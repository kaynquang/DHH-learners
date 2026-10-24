"""Compare view: the recording against the D1 dictionary voices."""
import pandas as pd
import streamlit as st

from fricative import config as C
from fricative.audio import load
from fricative.measure import analysis_window, spectrum_db
from fricative.plots import comparison_figure, spectrum_figure
from fricative.reference import measure_reference

from .context import Ctx


@st.cache_data
def reference_data():
    """D1 measured on the manual boundaries, with the middle-50% spectrum."""
    out = []
    for r, m in measure_reference():
        a, b = analysis_window(r.start_s, r.end_s)
        f, db = spectrum_db(load(r.path), a, b)
        out.append((r, m, f, db))
    return out


def render(ctx: Ctx) -> None:
    st.subheader("Compared with the D1 voices")
    ref = reference_data()
    left, right = st.columns(2, gap="large")
    with left:
        st.caption("CoG against relative amplitude. Dotted lines are the current thresholds.")
        st.plotly_chart(comparison_figure(ctx.m, [(r, rm) for r, rm, _, _ in ref], ctx.th), width="stretch",
                        alt="Scatter of CoG against relative amplitude for your recording and the D1 voices")
    with right:
        st.caption(f"Spectrum of the middle 50%: you against the D1 {C.PHONE_LABEL[ctx.target]} voices.")
        a, b = analysis_window(ctx.onset, ctx.offset)
        ref_specs = [(f"D1 {r.accent} {C.PHONE_LABEL[r.phone]}", f, db) for r, _, f, db in ref if r.phone == ctx.target]
        st.plotly_chart(spectrum_figure(spectrum_db(ctx.sound, a, b), ref_specs), width="stretch",
                        alt="Spectrum of your recording overlaid on the D1 reference spectra")

    st.dataframe(pd.DataFrame(
        [{"": "Your recording", "CoG (Hz)": round(ctx.m.cog_hz),
          "Relative amplitude (dB)": None if ctx.m.relamp_db is None else round(ctx.m.relamp_db, 1),
          "Fm (Hz)": round(ctx.m.fm_hz), "Onset (s)": round(ctx.onset, 3), "Offset (s)": round(ctx.offset, 3)}]
        + [{"": f"D1 {r.file}", "CoG (Hz)": round(rm.cog_hz), "Relative amplitude (dB)": round(rm.relamp_db, 1),
            "Fm (Hz)": round(rm.fm_hz), "Onset (s)": r.start_s, "Offset (s)": r.end_s} for r, rm, _, _ in ref]
    ), hide_index=True, alt="Measurements for your recording and the D1 voices")
