"""Detectors view: every frication detector and every CoG setting on this recording (ablation studies)."""
from dataclasses import replace

import pandas as pd
import streamlit as st

from fricative import config as C
from fricative.ablation import cog_ablation, segmentation_ablation, summarize_segmentation
from fricative.classify import classify
from fricative.plots import timeline_figure

from .context import Ctx


def render(ctx: Ctx) -> None:
    st.subheader("Ablation studies")
    st.caption(
        "Every detector and every CoG setting, run on this recording. Only the first detector "
        "and the first CoG setting are used for scoring."
        + (" Δ columns compare with the manual Praat boundaries." if ctx.manual else "")
    )

    st.markdown("**Frication detectors**")
    seg_rows = segmentation_ablation(ctx.sound, ctx.target, ctx.th, ctx.manual)
    st.plotly_chart(timeline_figure(seg_rows, ctx.manual), width="stretch",
                    alt="Onset-to-offset bars for each frication detector")
    with st.container(horizontal=True, gap="large"):
        with st.container():
            st.markdown(
                "**How to read this chart**\n\n"
                "- Each row is one detector. Its bar runs from where it thinks the hiss **starts** (onset) "
                "to where it **ends** (offset), in ms from the start of the recording.\n"
                "- The **red bar** is the detector used for scoring; blue bars are only for comparison.\n"
                "- Bars that **line up** mean the detectors agree. A bar that is much **longer or shifted** "
                "means that detector was fooled, for example by a click or a breath before the word.\n"
                "- **failed** means the detector found no usable hiss.\n"
                "- For D1 samples, the **green band** is the manual Praat segmentation (the answer key)."
            )
        with st.container():
            st.markdown("**On this recording**\n\n" + "\n".join(f"- {line}" for line in summarize_segmentation(seg_rows, ctx.manual)))
    seg_table = []
    for r in seg_rows:
        nan = float("nan")
        row = {"Method": r.name,
               "Verdict": f"failed: {r.error}" if r.error else f"{r.mark} {r.label}",
               "Heard": "" if r.heard is None else C.PHONE_LABEL[r.heard],
               "Onset (ms)": nan if r.onset_s is None else round(r.onset_s * 1000),
               "Offset (ms)": nan if r.offset_s is None else round(r.offset_s * 1000)}
        if ctx.manual:
            row["Δ onset (ms)"] = nan if r.onset_err_ms is None else round(r.onset_err_ms, 1)
            row["Δ offset (ms)"] = nan if r.offset_err_ms is None else round(r.offset_err_ms, 1)
        row["CoG (Hz)"] = nan if r.cog_hz is None else round(r.cog_hz)
        row["Relative amplitude (dB)"] = nan if r.relamp_db is None else round(r.relamp_db, 1)
        seg_table.append(row)
    st.dataframe(pd.DataFrame(seg_table), hide_index=True, alt="Results of every frication detector")

    st.markdown("**CoG settings** (on the boundaries above the spectrogram)")
    variants = cog_ablation(ctx.sound, ctx.onset, ctx.offset)
    current_cog = variants[0][1]
    st.dataframe(pd.DataFrame([
        {"Setting": name, "CoG (Hz)": round(value), "Δ vs current (Hz)": round(value - current_cog),
         "Heard with this CoG": C.PHONE_LABEL[classify(replace(ctx.m, cog_hz=value), ctx.target, ctx.th).heard]}
        for name, value in variants
    ]), hide_index=True, alt="CoG under different window functions and frequency bands")

