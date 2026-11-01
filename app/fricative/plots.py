"""Plotly figures for the app, in a quiet Japanese palette (washi, sumi, ai, shu)."""
from __future__ import annotations

import numpy as np
import parselmouth
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import PHONE_LABEL, Thresholds
from .measure import Measures, analysis_window

SUMI = "#2b2b2b"        # ink
NEZUMI = "#8c8780"      # mouse grey
WASHI = "#f7f4ee"       # paper
AI = "#2e4a62"          # indigo
SHU = "#c0432e"         # vermilion
KARASHI = "#c08a3e"     # mustard
MATCHA = "#6e8b54"      # green tea

PHONE_COLOR = {"s": AI, "sh": KARASHI, "f": MATCHA}
USER_COLOR = SHU
BOUNDARY_COLOR = SHU
SPEC_SCALE = [[0.0, WASHI], [0.55, "#a7a199"], [1.0, SUMI]]
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=56, r=16, t=16, b=48), font=dict(color=SUMI),
)
_AXIS = dict(showgrid=False, zeroline=False, linecolor="#d8d1c5", ticks="outside", tickcolor="#d8d1c5")


def spectrogram_figure(sound: parselmouth.Sound, onset_s: float, offset_s: float, fmax: float = 16000.0) -> go.Figure:
    sg = sound.to_spectrogram(window_length=0.005, maximum_frequency=fmax, time_step=0.002, frequency_step=60)
    db = 10 * np.log10(sg.values + 1e-20)
    top = float(db.max())
    fig = go.Figure(go.Heatmap(
        x=sg.xs() * 1000, y=sg.ys(), z=db, zmin=top - 60, zmax=top,
        colorscale=SPEC_SCALE, showscale=False,
        hovertemplate="%{x:.0f} ms<br>%{y:.0f} Hz<extra></extra>",
    ))
    a, b = analysis_window(onset_s, offset_s)
    fig.add_vrect(x0=a * 1000, x1=b * 1000, fillcolor=AI, opacity=0.12, line_width=0)
    for t in (onset_s, offset_s):
        fig.add_vline(x=t * 1000, line_color=BOUNDARY_COLOR, line_width=1.5)
    fig.update_layout(**_LAYOUT, height=300,
                      xaxis=dict(title="Time (ms)", **_AXIS), yaxis=dict(title="Frequency (Hz)", **_AXIS))
    return fig


def teacher_spectrogram(sound: parselmouth.Sound, windows: list[tuple[float, float, str]] | None = None,
                        lines: list[tuple[float, str]] | None = None, fmax: float = 10000.0) -> go.Figure:
    """The whole recording as a readable spectrogram with its waveform: time in seconds, frequency in Hz, a dB scale.
    `windows` shade the stretches the scoring looked at (start s, end s, label); `lines` are horizontal reference lines (Hz, label)."""
    fmax = min(fmax, sound.sampling_frequency / 2)
    sg = sound.to_spectrogram(window_length=0.01, maximum_frequency=fmax, time_step=0.004, frequency_step=40)
    db = 10 * np.log10(sg.values + 1e-20)
    top = float(db.max())
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
    fig.add_trace(go.Heatmap(x=sg.xs(), y=sg.ys(), z=db, zmin=top - 70, zmax=top, colorscale=SPEC_SCALE,
                             colorbar=dict(title="dB", len=0.75, y=0.62, thickness=10),
                             hovertemplate="%{x:.3f} s<br>%{y:.0f} Hz<extra></extra>"), row=1, col=1)
    x = np.asarray(sound.xs())
    y = np.asarray(sound.values).reshape(-1)
    step = max(1, len(y) // 4000)
    fig.add_trace(go.Scatter(x=x[::step], y=y[::step], mode="lines", line=dict(color=AI, width=1), hoverinfo="skip", showlegend=False), row=2, col=1)
    for t0, t1, label in windows or []:
        fig.add_vrect(x0=t0, x1=t1, fillcolor=AI, opacity=0.12, line_width=0, row="all", col=1,
                      annotation_text=label, annotation_position="top left", annotation_font_size=11)
        for t in (t0, t1):
            fig.add_vline(x=t, line_color=BOUNDARY_COLOR, line_width=1.2, row="all", col=1)
    for hz, label in lines or []:
        fig.add_hline(y=hz, line_color=KARASHI, line_dash="dash", line_width=1.2, row=1, col=1,
                      annotation_text=label, annotation_position="top right", annotation_font_size=11)
    fig.update_layout(**_LAYOUT, height=470)
    fig.update_xaxes(title_text="Time (s)", row=2, col=1, **_AXIS)
    fig.update_xaxes(row=1, col=1, **_AXIS)
    fig.update_yaxes(title_text="Frequency (Hz)", row=1, col=1, **_AXIS)
    fig.update_yaxes(title_text="Level", row=2, col=1, showticklabels=False, **_AXIS)
    return fig


def gop_figure(tracks: dict[str, list[float]], target: str, start_s: float, end_s: float, frame_s: float = 0.02) -> go.Figure:
    """Probability of each candidate sound over time, with the stretch the GOP score was computed on shaded."""
    fig = go.Figure()
    colours = [AI, SHU, KARASHI, MATCHA, NEZUMI]
    names = [target] + [n for n in tracks if n != target]
    for colour, name in zip(colours, names):
        y = tracks[name]
        fig.add_trace(go.Scatter(x=[(i + 0.5) * frame_s * 1000 for i in range(len(y))], y=y, mode="lines", name=f"/{name}/",
                                 line=dict(color=colour, width=3 if name == target else 1.5)))
    fig.add_vrect(x0=start_s * 1000, x1=end_s * 1000, fillcolor=AI, opacity=0.08, line_width=0)
    fig.update_layout(**_LAYOUT, height=220, legend=dict(orientation="h", y=1.15),
                      xaxis=dict(title="Time (ms)", **_AXIS), yaxis=dict(title="Probability", range=[0, 1.02], **_AXIS))
    return fig


def comparison_figure(user: Measures, refs: list[tuple], th: Thresholds) -> go.Figure:
    """CoG × relative amplitude: the user's point next to the D1 points. refs = [(RefRow, Measures)]."""
    fig = go.Figure()
    for phone in ("s", "sh", "f"):
        pts = [(r, m) for r, m in refs if r.phone == phone]
        fig.add_trace(go.Scatter(
            x=[m.cog_hz for _, m in pts], y=[m.relamp_db for _, m in pts],
            mode="markers+text", text=[f"{PHONE_LABEL[phone]} {r.accent}" for r, _ in pts],
            textposition="top center", textfont=dict(color=NEZUMI, size=11), name=f"D1 {PHONE_LABEL[phone]}",
            marker=dict(size=10, color=PHONE_COLOR[phone]),
            hovertemplate="%{text}<br>CoG %{x:.0f} Hz<br>%{y:.1f} dB<extra></extra>",
        ))
    y_top = 5.0
    y_bottom = min([-35.0] + [m.relamp_db - 5 for _, m in refs if m.relamp_db is not None]
                   + ([user.relamp_db - 5] if user.relamp_db is not None else []))
    if user.relamp_db is not None:
        fig.add_trace(go.Scatter(
            x=[user.cog_hz], y=[user.relamp_db], mode="markers+text", text=["You"],
            textposition="bottom center", textfont=dict(color=SHU, size=12), name="Your recording",
            marker=dict(size=20, symbol="star", color=USER_COLOR, line=dict(color=WASHI, width=1.5)),
            hovertemplate="You<br>CoG %{x:.0f} Hz<br>%{y:.1f} dB<extra></extra>",
        ))
    else:
        fig.add_vline(x=user.cog_hz, line_color=USER_COLOR, line_width=2, line_dash="dot",
                      annotation_text="You (no vowel)")
    fig.add_shape(type="line", x0=th.cog_s_sh_hz, x1=th.cog_s_sh_hz, y0=th.relamp_f_db, y1=y_top,
                  line=dict(color=NEZUMI, dash="dot", width=1))
    fig.add_shape(type="line", x0=1000, x1=max(10000.0, user.cog_hz + 1000), y0=th.relamp_f_db, y1=th.relamp_f_db,
                  line=dict(color=NEZUMI, dash="dot", width=1))
    fig.update_layout(
        **_LAYOUT, height=360,
        xaxis=dict(title="CoG (Hz)", range=[min(1500.0, user.cog_hz - 500), max(9000.0, user.cog_hz + 500)], **_AXIS),
        yaxis=dict(title="Relative amplitude (dB)", range=[y_bottom, y_top], **_AXIS),
        legend=dict(orientation="h", y=-0.22, font=dict(color=NEZUMI)),
    )
    return fig


def spectrum_figure(user: tuple[np.ndarray, np.ndarray], refs: list[tuple[str, np.ndarray, np.ndarray]]) -> go.Figure:
    """Spectrum of the middle 50%, each curve normalised to a 0 dB peak. refs = [(label, f, db)]."""
    fig = go.Figure()
    for label, f, db in refs:
        fig.add_trace(go.Scatter(x=f, y=db - db.max(), mode="lines", name=label,
                                 line=dict(width=1.2, color="#bdb6aa")))
    f, db = user
    fig.add_trace(go.Scatter(x=f, y=db - db.max(), mode="lines", name="Your recording",
                             line=dict(width=2, color=USER_COLOR)))
    fig.update_layout(
        **_LAYOUT, height=360,
        xaxis=dict(title="Frequency (Hz)", range=[0, 16000], **_AXIS),
        yaxis=dict(title="dB re peak", range=[-60, 3], **_AXIS),
        legend=dict(orientation="h", y=-0.22, font=dict(color=NEZUMI)),
    )
    return fig


def detection_figure(trace) -> go.Figure:
    """Step-by-step view of `segment.trace_boundaries`: energy, floor, threshold, runs, voicing, result."""
    t_ms = trace.t * 1000
    fig = go.Figure(go.Scatter(x=t_ms, y=trace.hi_db, mode="lines", name="High-band energy",
                               line=dict(color=SUMI, width=1.4),
                               hovertemplate="%{x:.0f} ms<br>%{y:.1f} dB<extra></extra>"))
    for a, b in trace.runs:
        fig.add_vrect(x0=a * 1000, x1=b * 1000, fillcolor=AI, opacity=0.10, line_width=0)
    fig.add_hline(y=trace.floor_db, line=dict(color=NEZUMI, dash="dot", width=1),
                  annotation_text="noise floor (5th percentile)", annotation_position="bottom right")
    fig.add_hline(y=trace.threshold_db, line=dict(color=KARASHI, dash="dash", width=1.2),
                  annotation_text="floor + 15 dB", annotation_position="top right")
    for v in trace.voiced_starts:
        fig.add_vline(x=v * 1000, line=dict(color=MATCHA, dash="dot", width=1.5),
                      annotation_text="voicing starts", annotation_position="top left")
    if trace.boundaries is not None:
        for t in (trace.boundaries.onset_s, trace.boundaries.offset_s):
            fig.add_vline(x=t * 1000, line=dict(color=SHU, width=2))
    fig.update_layout(**_LAYOUT, height=320, showlegend=False,
                      xaxis=dict(title="Time (ms)", **_AXIS), yaxis=dict(title="Energy 2.5–12 kHz (dB)", **_AXIS))
    return fig


def timeline_figure(rows, manual: tuple[float, float] | None = None) -> go.Figure:
    """One horizontal bar per detector (onset to offset); failed detectors are annotated."""
    ok = [r for r in rows if r.error is None]
    names = [r.name for r in rows]
    fig = go.Figure(go.Bar(
        y=[r.name for r in ok], x=[(r.offset_s - r.onset_s) * 1000 for r in ok],
        base=[r.onset_s * 1000 for r in ok], orientation="h",
        marker=dict(color=[SHU if r.key == "anchored" else AI for r in ok], opacity=0.85),
        hovertemplate="%{y}<br>%{base:.0f}–%{x:.0f} ms<extra></extra>", width=0.45,
    ))
    for r in rows:
        if r.error is not None:
            fig.add_annotation(x=0, y=r.name, text=f"failed: {r.error}", showarrow=False,
                               xanchor="left", font=dict(color=SHU, size=12))
    if manual is not None:
        fig.add_vrect(x0=manual[0] * 1000, x1=manual[1] * 1000, fillcolor=MATCHA, opacity=0.12, line_width=0,
                      annotation_text="manual (Praat)", annotation_position="top left")
    fig.update_layout(**_LAYOUT, height=60 + 48 * len(rows), showlegend=False,
                      xaxis=dict(title="Time (ms)", rangemode="tozero", **_AXIS),
                      yaxis=dict(categoryorder="array", categoryarray=names[::-1], **_AXIS))
    return fig


def decision_figure(th: Thresholds) -> go.Figure:
    """The scoring regions in CoG × relative amplitude, with the yellow margins."""
    x0, x1, y0, y1 = 1000.0, 10000.0, -40.0, 5.0
    c, r = th.cog_s_sh_hz, th.relamp_f_db
    fig = go.Figure()
    regions = [
        ((c, x1, r, y1), AI, "/s/", ((c + x1) / 2, (r + y1) / 2)),
        ((x0, c, r, y1), KARASHI, "/ʃ/", ((x0 + c) / 2, (r + y1) / 2)),
        ((x0, x1, y0, r), MATCHA, "/f/", ((x0 + x1) / 2, (y0 + r) / 2)),
    ]
    for (a, b, lo, hi), color, label, (lx, ly) in regions:
        fig.add_shape(type="rect", x0=a, x1=b, y0=lo, y1=hi, fillcolor=color, opacity=0.14, line_width=0)
        fig.add_annotation(x=lx, y=ly, text=label, showarrow=False, font=dict(size=22, color=color))
    fig.add_shape(type="rect", x0=c - th.cog_margin_hz, x1=c + th.cog_margin_hz, y0=r, y1=y1,
                  fillcolor="#b8862b", opacity=0.22, line_width=0)
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=r - th.relamp_margin_db, y1=r + th.relamp_margin_db,
                  fillcolor="#b8862b", opacity=0.22, line_width=0)
    fig.add_annotation(x=c, y=y1, text="△ yellow margin", showarrow=False, yanchor="bottom",
                       font=dict(size=11, color=NEZUMI))
    fig.update_layout(**_LAYOUT, height=340,
                      xaxis=dict(title="CoG (Hz)", range=[x0, x1], **_AXIS),
                      yaxis=dict(title="Relative amplitude (dB)", range=[y0, y1 + 3], **_AXIS))
    return fig


# ---------------------------------------------------------------- pattern figures (reference = ARCTIC voices)
FUJI = "#8b7bb0"        # wisteria, for /θ/
PATTERN_COLOR = {"S": AI, "SH": KARASHI, "F": MATCHA, "TH": FUJI}
PATTERN_LABEL = {"S": "/s/", "SH": "/ʃ/", "F": "/f/", "TH": "/θ/"}
PATTERN_FEATURES = [("cog", "CoG (Hz)", None), ("e2_4", "Energy 2–4 kHz", ".0%"), ("e6_8", "Energy 6–8 kHz", ".0%"),
                    ("skew", "Skewness", None), ("fm", "Peak Fm (Hz)", None), ("relamp", "Relative amplitude (dB)", None)]


def pattern_distribution_figure(f, ref: dict, voice: str) -> go.Figure:
    """One panel per feature: reference box per phone (5/25/50/75/95th percentile) and the recording as a line."""
    fig = make_subplots(rows=2, cols=3, subplot_titles=[t for _, t, _ in PATTERN_FEATURES], vertical_spacing=0.2)
    phones = ref["voices"][voice]["phones"]
    for k, (key, _, fmt) in enumerate(PATTERN_FEATURES):
        row, col = k // 3 + 1, k % 3 + 1
        for ph in ("S", "SH", "F", "TH"):
            q = phones[ph]["q"][key]
            fig.add_trace(go.Box(x=[PATTERN_LABEL[ph]], lowerfence=[q[0]], q1=[q[1]], median=[q[2]], q3=[q[3]], upperfence=[q[4]],
                                 name=PATTERN_LABEL[ph], marker_color=PATTERN_COLOR[ph], line=dict(width=1.5),
                                 showlegend=(k == 0)), row=row, col=col)
        v = f.scalars[key]
        if not np.isnan(v):
            fig.add_hline(y=v, line=dict(color=USER_COLOR, width=2.5), row=row, col=col,
                          annotation_text="You", annotation_position="top left", annotation_font=dict(color=USER_COLOR))
        if fmt:
            fig.update_yaxes(tickformat=fmt, row=row, col=col)
    fig.update_layout(**_LAYOUT, height=580, legend=dict(orientation="h", y=-0.12, font=dict(color=NEZUMI)))
    fig.update_layout(margin=dict(l=56, r=16, t=60, b=48))
    fig.update_xaxes(**_AXIS); fig.update_yaxes(**_AXIS)
    return fig


def template_figure(f, ref: dict, voice: str) -> go.Figure:
    """Mean spectral shape of each phone (± 1 SD) with the recording's shape on top."""
    fig = go.Figure()
    x = np.array(ref["meta"]["grid_hz"])
    for ph in ("S", "SH", "F", "TH"):
        d = ref["voices"][voice]["phones"][ph]
        m, s = np.array(d["shape_mean"]), np.array(d["shape_sd"])
        fig.add_trace(go.Scatter(x=np.r_[x, x[::-1]], y=np.r_[m + s, (m - s)[::-1]], fill="toself", fillcolor=PATTERN_COLOR[ph],
                                 opacity=0.10, line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=x, y=m, mode="lines", name=PATTERN_LABEL[ph], line=dict(color=PATTERN_COLOR[ph], width=2)))
    fig.add_trace(go.Scatter(x=x, y=f.shape, mode="lines", name="Your recording", line=dict(color=USER_COLOR, width=3.5)))
    fig.update_layout(**_LAYOUT, height=380, xaxis=dict(title="Frequency (Hz)", **_AXIS),
                      yaxis=dict(title="dB (own mean removed)", **_AXIS), legend=dict(orientation="h", y=-0.4))
    fig.update_layout(margin=dict(l=60, r=20, t=30, b=110))
    return fig


def trajectory_figure(f, ref: dict, voice: str) -> go.Figure:
    """CoG in five equal parts of the hiss, reference mean ± standard error and the recording."""
    fig = go.Figure()
    xs = [10, 30, 50, 70, 90]
    for ph in ("S", "SH", "F", "TH"):
        d = ref["voices"][voice]["phones"][ph]
        fig.add_trace(go.Scatter(x=xs, y=d["traj_mean"], mode="lines+markers", name=PATTERN_LABEL[ph],
                                 line=dict(color=PATTERN_COLOR[ph], width=2), error_y=dict(type="data", array=d["traj_se"], visible=True)))
    if np.isnan(f.traj).any():
        fig.add_annotation(text="Hiss shorter than 60 ms: no trajectory", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           font=dict(color=SHU, size=14))
    else:
        fig.add_trace(go.Scatter(x=xs, y=f.traj, mode="lines+markers", name="Your recording", line=dict(color=USER_COLOR, width=3.5)))
    fig.update_layout(**_LAYOUT, height=360, xaxis=dict(title="Position in the hiss (%)", tickvals=xs, **_AXIS),
                      yaxis=dict(title="CoG (Hz)", **_AXIS), legend=dict(orientation="h", y=-0.4))
    fig.update_layout(margin=dict(l=60, r=20, t=30, b=110))
    return fig


def f2_figure(f, ref: dict, voice: str) -> go.Figure:
    """F2 after the hiss relative to the vowel middle, for the reference phones and the recording."""
    fig = go.Figure()
    ms = [0, 10, 20, 30, 40, 50, 60]
    for ph in ("S", "SH", "F", "TH"):
        d = ref["voices"][voice]["phones"][ph]
        if d["f2_mean"]:
            fig.add_trace(go.Scatter(x=ms, y=d["f2_mean"], mode="lines+markers", name=PATTERN_LABEL[ph],
                                     line=dict(color=PATTERN_COLOR[ph], width=2), error_y=dict(type="data", array=d["f2_se"], visible=True)))
    if np.isnan(f.f2).any():
        fig.add_annotation(text="No vowel of 80 ms or more after the hiss: no F2 transition", x=0.5, y=0.5, xref="paper",
                           yref="paper", showarrow=False, font=dict(color=SHU, size=14))
    else:
        fig.add_trace(go.Scatter(x=ms, y=f.f2, mode="lines+markers", name="Your recording", line=dict(color=USER_COLOR, width=3.5)))
    fig.add_hline(y=0, line=dict(color=SUMI, width=1))
    fig.update_layout(**_LAYOUT, height=360, xaxis=dict(title="Time after the hiss (ms)", **_AXIS),
                      yaxis=dict(title="F2 − vowel-middle F2 (Hz)", **_AXIS), legend=dict(orientation="h", y=-0.4))
    fig.update_layout(margin=dict(l=60, r=20, t=30, b=110))
    return fig


def variability_figure(f, ref: dict, voice: str) -> go.Figure:
    """Spectral contrast and CoG wobble: reference boxes per phone, the recording, and the family boundary."""
    from .patterns import contrast_threshold
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Spectral contrast (dB)", "CoG wobble across the hiss (Hz)"])
    phones = ref["voices"][voice]["phones"]
    for col, key in ((1, "contrast"), (2, "wobble")):
        for ph in ("S", "SH", "F", "TH"):
            q = phones[ph]["q"][key]
            fig.add_trace(go.Box(x=[PATTERN_LABEL[ph]], lowerfence=[q[0]], q1=[q[1]], median=[q[2]], q3=[q[3]], upperfence=[q[4]],
                                 name=PATTERN_LABEL[ph], marker_color=PATTERN_COLOR[ph], line=dict(width=1.5), showlegend=(col == 1)),
                          row=1, col=col)
        v = f.scalars[key]
        if not np.isnan(v):
            fig.add_hline(y=v, line=dict(color=USER_COLOR, width=2.5), row=1, col=col, annotation_text="You",
                          annotation_position="top left", annotation_font=dict(color=USER_COLOR))
    fig.add_hline(y=contrast_threshold(ref, voice), line=dict(color=NEZUMI, dash="dot", width=1.2), row=1, col=1,
                  annotation_text="family boundary", annotation_position="bottom right", annotation_font=dict(color=NEZUMI))
    fig.update_layout(**_LAYOUT, height=380, legend=dict(orientation="h", y=-0.2, font=dict(color=NEZUMI)))
    fig.update_layout(margin=dict(l=56, r=16, t=60, b=60))
    fig.update_xaxes(**_AXIS); fig.update_yaxes(**_AXIS)
    return fig


def phoneme_figure(pc) -> go.Figure:
    """What the phone recogniser hears: mean evidence per group at the hiss, and each group's evidence over time."""
    fig = make_subplots(rows=1, cols=2, column_widths=[0.35, 0.65], subplot_titles=["At the hiss", "Over the clip"])
    groups = ("S", "SH", "F", "TH")
    fig.add_trace(go.Bar(x=[PATTERN_LABEL[g] for g in groups], y=[pc.masses[g] for g in groups],
                         marker_color=[PATTERN_COLOR[g] for g in groups], showlegend=False,
                         hovertemplate="%{x}: %{y:.2f}<extra></extra>"), row=1, col=1)
    for g in groups:
        fig.add_trace(go.Scatter(x=pc.centres * 1000, y=pc.track[g], mode="lines", name=PATTERN_LABEL[g],
                                 line=dict(color=PATTERN_COLOR[g], width=2)), row=1, col=2)
    fig.add_vrect(x0=pc.hiss_window[0] * 1000, x1=pc.hiss_window[1] * 1000, fillcolor=AI, opacity=0.10, line_width=0, row=1, col=2,
                  annotation_text="hiss", annotation_position="top left", annotation_font=dict(color=NEZUMI))
    fig.update_layout(**_LAYOUT, height=340, legend=dict(orientation="h", y=-0.3, font=dict(color=NEZUMI)))
    fig.update_layout(margin=dict(l=56, r=16, t=50, b=90))
    fig.update_xaxes(title_text="Time in the clip (ms)", row=1, col=2); fig.update_yaxes(title_text="posterior", range=[0, 1.05], **_AXIS)
    fig.update_xaxes(**_AXIS)
    return fig
