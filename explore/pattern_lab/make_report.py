"""Exploration only: build docs/exploration/spectral-patterns.html from tokens.pkl."""
import sys, numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

S = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, S)
from analysis import (load, normalise, split, cross, thresh_fn, lda_fn, template_fn, same_rows, best_thresh, bal_acc,
                      table, SCALARS, F2FEATS, LDA)

df = load(S)
dfn = normalise(df, SCALARS + F2FEATS)
GRID = np.arange(0, 8000, 200); XC = GRID + 100
SPK = {"bdl": "bdl (nam)", "slt": "slt (nữ)"}
PH = {"S": "#2e4a62", "SH": "#c08a3e", "F": "#6e8b54", "TH": "#c0432e", "Z": "#8c8780"}
LAB = {"S": "/s/", "SH": "/ʃ/", "F": "/f/", "TH": "/θ/", "Z": "/z/"}
FONT = dict(family="Be Vietnam Pro, sans-serif", color="#2b2b2b", size=13)
AXIS = dict(showgrid=False, zeroline=False, linecolor="#d8d1c5", ticks="outside", tickcolor="#d8d1c5")
THR = 4340.0


def style(fig, h, legend=True):
    fig.update_layout(height=h, margin=dict(l=60, r=20, t=50, b=95), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=FONT, showlegend=legend,
                      legend=dict(orientation="h", y=-0.34, font=dict(size=12)))
    fig.update_xaxes(**AXIS); fig.update_yaxes(**AXIS)
    for a in fig.layout.annotations: a.font = dict(size=13, color="#2b2b2b")
    return fig


# ---------------------------------------------------------------- evaluation numbers
ext = {
    "template (speaker-normalised shape)": (template_fn("shape"), template_fn("shape_n")),
    "LDA shape (40 bands)": (lda_fn(shape="shape_t"), lda_fn(shape="shape_n")),
    "LDA 11 scalar features": (lda_fn(cols=SCALARS), lda_fn(cols=SCALARS)),
}
F2NEED = ["d0", "d10", "d30", "f2mid"]
ext_s = dict(ext)
ext_s["LDA 11 scalars (rows with F2)"] = (same_rows(lda_fn(cols=SCALARS), F2NEED), same_rows(lda_fn(cols=SCALARS), F2NEED))
ext_s["LDA 11 scalars + F2"] = (lda_fn(cols=SCALARS + F2NEED), lda_fn(cols=SCALARS + F2NEED))
T_ss = table(df, ("S", "SH"), SCALARS + F2FEATS, ext_s).set_index("method")
ext_f = dict(ext)
ext_f["LDA 11 scalars (rows with F2)"] = (same_rows(lda_fn(cols=SCALARS), F2NEED), same_rows(lda_fn(cols=SCALARS), F2NEED))
ext_f["LDA 11 scalars + F2"] = (lda_fn(cols=SCALARS + F2NEED), lda_fn(cols=SCALARS + F2NEED))
T_ft = table(df, ("F", "TH"), SCALARS + F2FEATS, ext_f).set_index("method")
f1 = T_ss.loc[SCALARS, "normalised"]
best_single = f1.idxmax()
R = dict(cog_raw=T_ss.loc["cog", "raw"], cog_n=T_ss.loc["cog", "normalised"], fm_raw=T_ss.loc["fm", "raw"],
         fm_n=T_ss.loc["fm", "normalised"], best=best_single, best_v=f1.max(),
         lda_raw=T_ss.loc["LDA 11 scalar features", "raw"], lda_n=T_ss.loc["LDA 11 scalar features", "normalised"],
         shape_raw=T_ss.loc["LDA shape (40 bands)", "raw"], shape_n=T_ss.loc["LDA shape (40 bands)", "normalised"],
         tmpl_n=T_ss.loc["template (speaker-normalised shape)", "normalised"],
         f_cog=T_ft.loc["cog", ["raw", "normalised"]].max(), f_lda=T_ft.loc["LDA 11 scalars (rows with F2)", ["raw", "normalised"]].max(),
         f_f2=T_ft.loc["LDA 11 scalars + F2", ["raw", "normalised"]].max(), f_shape=T_ft.loc["LDA shape (40 bands)", ["raw", "normalised"]].max())
R.update(s_f2=float(T_ss.loc["d0", ["raw", "normalised"]].max()),
         s_lda_rows=float(T_ss.loc["LDA 11 scalars (rows with F2)", ["raw", "normalised"]].max()),
         s_lda_f2=float(T_ss.loc["LDA 11 scalars + F2", ["raw", "normalised"]].max()))
_d = split(normalise(df, SCALARS + F2FEATS), ("S", "SH"))
R["cog_dir"] = cross(_d, thresh_fn("cog"))[1]; R["lda_dir"] = cross(_d, lda_fn(cols=SCALARS))[1]
print({k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v) for k, v in R.items()})
n_tok = df.groupby(["spk", "phone"]).size().unstack()

figs = {}
REC = {}
E2m = {}

# ---------------------------------------------------------------- A1: histogram of CoG
fig = make_subplots(rows=1, cols=2, subplot_titles=["_"] * 2, shared_yaxes=True)
for j, spk in enumerate(SPK, 1):
    d = df[df.spk == spk]
    rec_s = (d[d.phone == "S"].cog >= THR).mean(); rec_sh = (d[d.phone == "SH"].cog < THR).mean()
    for ph in ("S", "SH"):
        fig.add_trace(go.Histogram(x=d[d.phone == ph].cog, name=LAB[ph], histnorm="probability", xbins=dict(start=1000, end=8000, size=200),
                                   marker_color=PH[ph], opacity=0.65, showlegend=(j == 1)), row=1, col=j)
    REC[spk] = (rec_s, rec_sh); fig.add_vline(x=THR, line=dict(color="#2b2b2b", dash="dot", width=1.5), row=1, col=j)
    fig.layout.annotations[j - 1].text = f"{SPK[spk]}: tại 4.340 Hz, /s/ đúng {rec_s:.0%}, /ʃ/ đúng {rec_sh:.0%}"
fig.update_layout(barmode="overlay")
fig.update_xaxes(title_text="CoG (Hz)"); fig.update_yaxes(title_text="tỉ lệ trong từng âm", col=1)
figs["A1"] = style(fig, 340)

# ---------------------------------------------------------------- A2: same CoG, different shape
d = df[(df.spk == "bdl") & df.phone.isin(["S", "SH"]) & df.cog.between(3900, 4700)]
a, b = d[d.phone == "S"], d[d.phone == "SH"]
dd = np.abs(a.cog.values[:, None] - b.cog.values[None, :]); i, k = np.unravel_index(dd.argmin(), dd.shape)
ta, tb = a.iloc[i], b.iloc[k]
fig = go.Figure()
for t, ph in ((ta, "S"), (tb, "SH")):
    fig.add_trace(go.Scatter(x=XC, y=t.shape_t, mode="lines", name=f"{LAB[ph]}: CoG {t.cog:,.0f} Hz, 2–4 kHz chiếm {t.e2_4:.0%}",
                             line=dict(color=PH[ph], width=3)))
fig.add_vline(x=(ta.cog + tb.cog) / 2, line=dict(color="#2b2b2b", dash="dot"), annotation_text="cùng CoG", annotation_position="top")
fig.update_layout(xaxis_title="Tần số (Hz)", yaxis_title="dB so với mức trung bình của đoạn")
figs["A2"] = style(fig, 380)
R["a2"] = (ta.cog, tb.cog, ta.e2_4, tb.e2_4)

# ---------------------------------------------------------------- B1: features annotated on a typical token
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=["_", "_"])
bands = [(0, 2000, "e0_2"), (2000, 4000, "e2_4"), (4000, 6000, "e4_6"), (6000, 8000, "e6_8")]
for r_i, ph in enumerate(("S", "SH"), 1):
    d = df[(df.spk == "bdl") & (df.phone == ph)]
    t = d.iloc[(d.cog - d.cog.median()).abs().argmin()]
    y = np.array(t["shape"]) - np.max(t["shape"])
    fig.add_trace(go.Scatter(x=XC, y=y, mode="lines", line=dict(color=PH[ph], width=3), showlegend=False), row=r_i, col=1)
    for k, (lo, hi, c) in enumerate(bands):
        fig.add_vrect(x0=lo, x1=hi, fillcolor="#2b2b2b", opacity=0.05 if k % 2 == 0 else 0.0, line_width=0, row=r_i, col=1)
        fig.add_annotation(x=(lo + hi) / 2, y=12, text=f"{t[c]:.0%}", showarrow=False, font=dict(size=13, color="#2b2b2b"), row=r_i, col=1)
    fig.add_vline(x=t.cog, line=dict(color="#c0432e", width=2), row=r_i, col=1)
    fig.add_annotation(x=t.cog, y=-52, text=f"CoG {t.cog:,.0f}", showarrow=False, xanchor="left", font=dict(color="#c0432e"), row=r_i, col=1)
    yy = float(np.interp(t.fm, XC, y))
    fig.add_trace(go.Scatter(x=[t.fm], y=[yy], mode="markers+text", text=[f"Fm {t.fm:,.0f}"], textposition="top center",
                             marker=dict(size=11, color="#2b2b2b", symbol="diamond"), showlegend=False), row=r_i, col=1)
    fig.layout.annotations[r_i - 1].text = f"{LAB[ph]}: SD {t.sd:,.0f} Hz · skew {t["skew"]:.1f} · kurtosis {t["kurt"]:.1f}"
fig.update_yaxes(range=[-58, 17], title_text="dB so với đỉnh"); fig.update_xaxes(title_text="Tần số (Hz)", row=2, col=1)
figs["B1"] = style(fig, 560, legend=False)

# ---------------------------------------------------------------- B2: distributions of features
feats = [("cog", "CoG"), ("e2_4", "% năng lượng 2–4 kHz"), ("e6_8", "% năng lượng 6–8 kHz"), ("skew", "skewness"), ("fm", "Fm (đỉnh phổ)"), ("relamp", "biên độ tương đối")]
fig = make_subplots(rows=2, cols=3, subplot_titles=[f"{n}: /s/–/ʃ/ đúng {T_ss.loc[c, 'normalised']:.0%}" for c, n in feats], vertical_spacing=0.2)
for k, (c, n) in enumerate(feats):
    for ph in ("S", "SH", "F", "TH"):
        fig.add_trace(go.Box(y=dfn[dfn.phone == ph][c], name=LAB[ph], marker_color=PH[ph], showlegend=(k == 0), boxpoints=False,
                             line=dict(width=1.5)), row=k // 3 + 1, col=k % 3 + 1)
fig.update_yaxes(title_text="z-score trong từng giọng", col=1)
figs["B2"] = style(fig, 620)

# ---------------------------------------------------------------- B3: single feature accuracy bars
t = T_ss.loc[SCALARS].sort_values("normalised")
names = {"cog": "CoG", "fm": "Fm", "sd": "SD", "skew": "skewness", "kurt": "kurtosis", "e0_2": "% 0–2 kHz", "e2_4": "% 2–4 kHz",
         "e4_6": "% 4–6 kHz", "e6_8": "% 6–8 kHz", "relamp": "biên độ tương đối", "dur": "thời lượng", "d0": "F2 ngay sau tiếng xì", "d10": "F2 sau 10 ms", "d30": "F2 sau 30 ms", "f2_10": "F2 tuyệt đối sau 10 ms", "f2mid": "F2 giữa nguyên âm"}
fig = go.Figure()
fig.add_trace(go.Bar(y=[names[i] for i in t.index], x=t.raw, orientation="h", name="giá trị tuyệt đối", marker_color="#bdb6aa"))
fig.add_trace(go.Bar(y=[names[i] for i in t.index], x=t.normalised, orientation="h", name="đã chuẩn hoá theo từng người", marker_color="#2e4a62"))
fig.add_vline(x=0.5, line=dict(color="#2b2b2b", dash="dot"), annotation_text="ngẫu nhiên", annotation_position="top")
fig.update_layout(barmode="group", xaxis=dict(range=[0, 1], title="độ chính xác cân bằng /s/–/ʃ/ (huấn luyện giọng này, thử giọng kia)"))
figs["B3"] = style(fig, 520)

# ---------------------------------------------------------------- C1: templates
fig = make_subplots(rows=1, cols=2, subplot_titles=[SPK[s] for s in SPK], shared_yaxes=True)
for j, spk in enumerate(SPK, 1):
    for ph in ("S", "SH", "F", "TH"):
        M = np.stack(df[(df.spk == spk) & (df.phone == ph)].shape_t.values)
        m, s = M.mean(0), M.std(0)
        fig.add_trace(go.Scatter(x=np.r_[XC, XC[::-1]], y=np.r_[m + s, (m - s)[::-1]], fill="toself", fillcolor=PH[ph], opacity=0.12,
                                 line=dict(width=0), hoverinfo="skip", showlegend=False), row=1, col=j)
        fig.add_trace(go.Scatter(x=XC, y=m, mode="lines", name=f"{LAB[ph]} (n={len(M)})" if j == 1 else LAB[ph],
                                 line=dict(color=PH[ph], width=3), showlegend=(j == 1)), row=1, col=j)
fig.update_xaxes(title_text="Tần số (Hz)"); fig.update_yaxes(title_text="dB (mẫu phổ trung bình ± 1 SD)", col=1)
figs["C1"] = style(fig, 400)

# ---------------------------------------------------------------- C2: template-distance score, held-out speaker
dn = split(dfn, ("S", "SH"))
fig = make_subplots(rows=1, cols=2, subplot_titles=["_"] * 2, shared_yaxes=True)
C2 = {}
for j, (tr, te) in enumerate((("bdl", "slt"), ("slt", "bdl")), 1):
    a, b = dn[dn.spk == tr], dn[dn.spk == te]
    A, B = np.stack(a.shape_n.values), np.stack(b.shape_n.values)
    m0, m1 = A[a.y.values == 0].mean(0), A[a.y.values == 1].mean(0)
    score = np.linalg.norm(B - m1, axis=1) - np.linalg.norm(B - m0, axis=1)      # > 0 : closer to /s/
    acc = bal_acc(b.y.values, (score < 0).astype(int)); C2[te] = acc
    for ph, y in (("S", 0), ("SH", 1)):
        fig.add_trace(go.Histogram(x=score[b.y.values == y], name=LAB[ph], marker_color=PH[ph], opacity=0.65, histnorm="probability",
                                   nbinsx=30, showlegend=(j == 1)), row=1, col=j)
    fig.add_vline(x=0, line=dict(color="#2b2b2b", dash="dot"), row=1, col=j)
    fig.layout.annotations[j - 1].text = f"mẫu từ {tr} → thử trên {te}: đúng {acc:.0%}"
fig.update_layout(barmode="overlay")
fig.update_xaxes(title_text="d(/ʃ/) − d(/s/); >0: giống /s/ hơn")
figs["C2"] = style(fig, 340)

# ---------------------------------------------------------------- D1: LDA weights over frequency
fig = go.Figure()
W = {}
for spk in SPK:
    a = dn[dn.spk == spk]
    m = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5]).fit(np.stack(a.shape_n.values), a.y.values)
    w = -m.coef_[0]; w = w / np.linalg.norm(w); W[spk] = w
    fig.add_trace(go.Scatter(x=XC, y=w, mode="lines", name=SPK[spk], line=dict(width=3)))
fig.add_hline(y=0, line=dict(color="#2b2b2b", width=1))
R["wcorr"] = float(np.corrcoef(W["bdl"], W["slt"])[0, 1])
fig.update_layout(xaxis_title="Tần số (Hz)", yaxis_title="trọng số (>0: /s/, <0: /ʃ/)")
figs["D1"] = style(fig, 360)

# ---------------------------------------------------------------- D2: standardised weights of the 11-feature LDA
dnc = dn.dropna(subset=SCALARS)
m = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5]).fit(dnc[SCALARS].values, dnc.y.values)
w = pd.Series(-m.coef_[0], index=SCALARS).sort_values()
fig = go.Figure(go.Bar(y=[names[i] for i in w.index], x=w.values, orientation="h",
                       marker_color=["#2e4a62" if v > 0 else "#c08a3e" for v in w.values]))
fig.add_vline(x=0, line=dict(color="#2b2b2b", width=1))
fig.update_layout(xaxis_title="trọng số chuẩn hoá (>0: nghiêng về /s/, <0: nghiêng về /ʃ/)")
figs["D2"] = style(fig, 440, legend=False)

# ---------------------------------------------------------------- D3: score histograms on held-out speaker
fig = make_subplots(rows=1, cols=2, subplot_titles=["_", "_"], shared_yaxes=True)
tr, te = "bdl", "slt"
a, b = dnc[dnc.spk == tr], dnc[dnc.spk == te]
res = {}
for j, (title, fn) in enumerate((("CoG một mình", None), ("gộp 11 đặc trưng (LDA)", "lda")), 1):
    if fn is None:
        sa, sb = a.cog.values, b.cog.values
    else:
        mm = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5]).fit(a[SCALARS].values, a.y.values)
        sa, sb = -mm.decision_function(a[SCALARS].values), -mm.decision_function(b[SCALARS].values)
    acc_t, t0, o = best_thresh(sa, 1 - a.y.values)
    pred = (o * (sb - t0) > 0).astype(int)
    acc = bal_acc(1 - b.y.values, pred); res[title] = acc
    for ph, y in (("S", 0), ("SH", 1)):
        fig.add_trace(go.Histogram(x=sb[b.y.values == y], name=LAB[ph], marker_color=PH[ph], opacity=0.65, histnorm="probability",
                                   nbinsx=30, showlegend=(j == 1)), row=1, col=j)
    fig.add_vline(x=t0, line=dict(color="#2b2b2b", dash="dot"), row=1, col=j)
    fig.layout.annotations[j - 1].text = f"{title}: đúng {acc:.0%} (huấn luyện {tr}, thử {te})"
fig.update_layout(barmode="overlay"); fig.update_xaxes(title_text="điểm (cao: giống /s/ hơn)")
figs["D3"] = style(fig, 340)

# ---------------------------------------------------------------- E1: CoG trajectories
fig = make_subplots(rows=1, cols=2, subplot_titles=[SPK[s] for s in SPK], shared_yaxes=True)
xs = [10, 30, 50, 70, 90]
for j, spk in enumerate(SPK, 1):
    for ph in ("S", "SH", "F", "TH"):
        T = np.stack(df[(df.spk == spk) & (df.phone == ph)].traj.values); T = T[~np.isnan(T).any(axis=1)]
        m, se = T.mean(0), T.std(0) / np.sqrt(len(T))
        fig.add_trace(go.Scatter(x=xs, y=m, mode="lines+markers", name=f"{LAB[ph]} (n={len(T)})" if j == 1 else LAB[ph],
                                 line=dict(color=PH[ph], width=3), error_y=dict(type="data", array=se, visible=True, thickness=1.2),
                                 showlegend=(j == 1)), row=1, col=j)
fig.update_xaxes(title_text="vị trí trong đoạn xì (%)", tickvals=xs); fig.update_yaxes(title_text="CoG (Hz), trung bình ± sai số chuẩn", col=1)
figs["E1"] = style(fig, 380)

# ---------------------------------------------------------------- E2: F2 transition after offset
fig = make_subplots(rows=1, cols=2, subplot_titles=[SPK[s] for s in SPK], shared_yaxes=True)
ms = [0, 10, 20, 30, 40, 50, 60]
E2n = {}
for j, spk in enumerate(SPK, 1):
    for ph in ("S", "SH", "F", "TH"):
        d = df[(df.spk == spk) & (df.phone == ph) & df.f2mid.notna()]
        D = np.stack(d.f2.values) - d.f2mid.values[:, None]
        D = D[~np.isnan(D).any(axis=1)]; E2n[(spk, ph)] = len(D)
        m, se = D.mean(0), D.std(0) / np.sqrt(len(D)); E2m[(spk, ph)] = m
        fig.add_trace(go.Scatter(x=ms, y=m, mode="lines+markers", name=f"{LAB[ph]} (n={len(D)})" if j == 1 else LAB[ph],
                                 line=dict(color=PH[ph], width=3), error_y=dict(type="data", array=se, visible=True, thickness=1.2),
                                 showlegend=(j == 1)), row=1, col=j)
fig.add_hline(y=0, line=dict(color="#2b2b2b", width=1))
fig.update_xaxes(title_text="thời gian sau khi tiếng xì kết thúc (ms)"); fig.update_yaxes(title_text="F2 − F2 giữa nguyên âm (Hz)", col=1)
figs["E2"] = style(fig, 380)

# ---------------------------------------------------------------- F: following-vowel context
ROUNDED = {"UW", "UH", "OW", "AO", "OY"}
VOW = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
df["ctx"] = df.nxt.apply(lambda x: "nguyên âm tròn môi" if x in ROUNDED else ("nguyên âm khác" if x in VOW else "phụ âm / im lặng"))
fig = make_subplots(rows=1, cols=2, subplot_titles=[LAB["S"], LAB["SH"]])
CT = {}
for j, ph in enumerate(("S", "SH"), 1):
    for spk, col in (("bdl", "#2e4a62"), ("slt", "#c08a3e")):
        for ctx in ("nguyên âm tròn môi", "nguyên âm khác", "phụ âm / im lặng"):
            y = df[(df.spk == spk) & (df.phone == ph) & (df.ctx == ctx)].cog
            CT[(spk, ph, ctx)] = (y.median(), len(y))
        fig.add_trace(go.Box(x=df[(df.spk == spk) & (df.phone == ph)].ctx, y=df[(df.spk == spk) & (df.phone == ph)].cog, name=SPK[spk],
                             marker_color=col, boxpoints=False, showlegend=(j == 1), line=dict(width=1.5)), row=1, col=j)
fig.update_layout(boxmode="group"); fig.update_yaxes(title_text="CoG (Hz)", col=1)
figs["F"] = style(fig, 400)
dr = {spk: CT[(spk, "S", "nguyên âm tròn môi")][0] - CT[(spk, "S", "nguyên âm khác")][0] for spk in SPK}

# ---------------------------------------------------------------- G: scoreboard
fig = make_subplots(rows=1, cols=2, subplot_titles=["/s/ vs /ʃ/", "/f/ vs /θ/"], horizontal_spacing=0.22)
a_rows = [("CoG, giá trị tuyệt đối", T_ss.loc["cog", "raw"]), ("CoG, chuẩn hoá theo người", T_ss.loc["cog", "normalised"]),
          (f"{names[best_single]}, chuẩn hoá", f1.max()), ("mẫu phổ, chuẩn hoá", T_ss.loc["template (speaker-normalised shape)", "normalised"]),
          ("LDA 40 dải phổ, chuẩn hoá", T_ss.loc["LDA shape (40 bands)", "normalised"]), ("LDA 11 đặc trưng, chuẩn hoá", T_ss.loc["LDA 11 scalar features", "normalised"]),
          ("F2 ngay sau tiếng xì (1 đặc trưng)", R["s_f2"]), ("LDA 11, các đoạn có F2", R["s_lda_rows"]), ("LDA 11 + F2, các đoạn có F2", R["s_lda_f2"])]
b_rows = [("CoG", max(T_ft.loc["cog", "raw"], T_ft.loc["cog", "normalised"])), ("biên độ tương đối", max(T_ft.loc["relamp", ["raw", "normalised"]])),
          ("F2 tốt nhất (1 đặc trưng)", max(T_ft.loc[F2FEATS, ["raw", "normalised"]].max())),
          ("LDA 40 dải phổ", max(T_ft.loc["LDA shape (40 bands)", ["raw", "normalised"]])),
          ("LDA 11 đặc trưng (cùng các token có F2)", max(T_ft.loc["LDA 11 scalars (rows with F2)", ["raw", "normalised"]])),
          ("LDA 11 đặc trưng + F2", max(T_ft.loc["LDA 11 scalars + F2", ["raw", "normalised"]]))]
for j, rows in enumerate((a_rows, b_rows), 1):
    fig.add_trace(go.Bar(y=[r[0] for r in rows], x=[r[1] for r in rows], orientation="h", marker_color="#2e4a62",
                         text=[f"{r[1]:.0%}" for r in rows], textposition="outside", showlegend=False), row=1, col=j)
    fig.add_vline(x=0.5, line=dict(color="#2b2b2b", dash="dot"), row=1, col=j)
fig.update_xaxes(range=[0, 1.12], title_text="độ chính xác cân bằng, chéo giọng")
fig.update_yaxes(autorange="reversed")
figs["G"] = style(fig, 480, legend=False)

# ---------------------------------------------------------------- HTML (every number below is computed above)
def fh(key, first=False):
    return figs[key].to_html(full_html=False, include_plotlyjs="cdn" if first else False, config={"displaylogo": False})

def box(kind, title, items):
    return f'<div class="{kind}"><div class="eyebrow">{title}</div><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>"

pct = lambda x: f"{x:.0%}"
mS = {s: df[(df.spk == s) & (df.phone == "S")].cog.median() for s in SPK}
mSH = {s: df[(df.spk == s) & (df.phone == "SH")].cog.median() for s in SPK}
def traj_stats(ph):
    T = np.vstack([np.stack(df[(df.spk == s) & (df.phone == ph)].traj.values) for s in SPK]); T = T[~np.isnan(T).any(axis=1)]
    return T[:, 0].mean(), T[:, 1:4].mean(), T[:, 4].mean()
tS, tSH = traj_stats("S"), traj_stats("SH")
ctxS = df[df.phone == "S"].ctx.value_counts()
dv = {spk: CT[(spk, "S", "nguyên âm khác")][0] - CT[(spk, "S", "phụ âm / im lặng")][0] for spk in SPK}
f2sh = np.mean([E2m[(s, "SH")][0] for s in SPK]); f2s = np.mean([E2m[(s, "S")][0] for s in SPK])
f2f = np.mean([E2m[(s, "F")][1] for s in SPK]); f2th = np.mean([E2m[(s, "TH")][1] for s in SPK])
both_better = all(l > c for l, c in zip(R["lda_dir"], R["cog_dir"]))
nS = int(n_tok.loc["bdl", "S"] + n_tok.loc["slt", "S"]); nSH = int(n_tok.loc["bdl", "SH"] + n_tok.loc["slt", "SH"])
nF = int(n_tok.loc["bdl", "F"] + n_tok.loc["slt", "F"]); nTH = int(n_tok.loc["bdl", "TH"] + n_tok.loc["slt", "TH"])
wtxt = (f"Hai giọng học ra hai đường khá giống nhau (tương quan {R['wcorr']:.2f})." if R["wcorr"] > 0.6
        else f"Hai giọng học ra hai đường khác nhau (tương quan chỉ {R['wcorr']:.2f}).")

html = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pattern phổ của phụ âm xát</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;700&family=Be+Vietnam+Pro:wght@400;500;700&display=swap">
<style>
:root{{--bg:#f7f4ee;--ink:#2b2b2b;--mute:#6f6a62;--line:#ddd6ca;--ai:#2e4a62;--shu:#c0432e;--card:#fffdf9}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 "Be Vietnam Pro",system-ui,sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:40px 20px 90px}}
h1,h2{{font-family:"Shippori Mincho",serif;font-weight:700;line-height:1.25}} h1{{font-size:34px;margin:0 0 8px}} h2{{font-size:26px;margin:0}}
p{{margin:8px 0;max-width:78ch}} .sub{{color:var(--mute)}}
section{{margin-top:54px;border-top:1px solid var(--line);padding-top:22px}}
.eyebrow{{font:600 12px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin-bottom:8px}}
.read,.get,.sum,.warn{{border-radius:6px;padding:14px 18px;margin:12px 0;max-width:90ch}} ul{{margin:4px 0;padding-left:20px}} li{{margin:3px 0}}
.read{{background:var(--card);border:1px solid var(--line)}} .get{{background:#e9eef2;border-left:3px solid var(--ai)}}
.sum{{background:var(--card);border:1px solid var(--ai)}} .warn{{background:#f6e6e1;border-left:3px solid var(--shu)}}
.fig{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px;margin:10px 0}}
</style></head><body><main>
<div class="eyebrow">Thí nghiệm sơ bộ · không phải code sản phẩm</div>
<h1>Pattern phổ thay cho một con số trung bình</h1>
<p class="sub">Dữ liệu: CMU ARCTIC, giọng <b>bdl</b> (nam) và <b>slt</b> (nữ), 300 câu đầu của mỗi giọng, ranh giới do MFA tạo và <b>chưa kiểm tay</b>.
Số đoạn (cộng hai giọng): /s/ {nS}, /ʃ/ {nSH}, /f/ {nF}, /θ/ {nTH}. Mọi con số "đúng" bên dưới là <b>độ chính xác cân bằng chéo giọng</b>:
huấn luyện trên một giọng, thử trên giọng còn lại, lấy trung bình hai chiều. "Cân bằng" nghĩa là /ʃ/ và /s/ có trọng số như nhau, dù /s/ nhiều gấp 4 lần.</p>

<div class="sum"><div class="eyebrow">Kết quả trước khi xem hình</div><ul>
<li><b>CoG một mình</b> đạt {pct(R['cog_raw'])}; sau khi <b>chuẩn hoá theo từng người</b> lên {pct(R['cog_n'])}.</li>
<li><b>Chuẩn hoá theo người là thay đổi lớn nhất</b>, lớn hơn việc chọn đặc trưng: Fm tăng từ {pct(R['fm_raw'])} lên {pct(R['fm_n'])}.</li>
<li>Đặc trưng đơn tốt nhất sau chuẩn hoá là <b>{names[R['best']]}</b> ({pct(R['best_v'])}). Gộp 11 đặc trưng dễ giải thích bằng LDA đạt trung bình <b>{pct(R['lda_n'])}</b> (chưa chuẩn hoá chỉ {pct(R['lda_raw'])}), nhưng <b>không đều giữa hai chiều</b>: {pct(R['lda_dir'][0])} khi huấn luyện bdl thử slt, {pct(R['lda_dir'][1])} chiều ngược lại (CoG: {pct(R['cog_dir'][0])} và {pct(R['cog_dir'][1])}). Với 2 giọng, chưa thể nói gộp đặc trưng chắc chắn hơn CoG.</li>
<li><b>Pattern phổ nhiều chiều chưa thắng:</b> LDA trên 40 dải phổ chỉ {pct(R['shape_n'])}, mẫu phổ trung bình {pct(R['tmpl_n'])}. Với 2 giọng thì chưa đủ dữ liệu để học hình dạng phổ chi tiết.</li>
<li><b>Pattern theo thời gian:</b> hai đầu đoạn xì là chuyển tiếp nên CoG ở đó thấp hơn nhiều, ba khoảng giữa ổn định. Điều này ủng hộ việc đo trên giữa 50%. F2 sau đoạn xì khác nhau rõ giữa /ʃ/ và /s/ <i>trên trung bình</i> nhưng không tách được từng đoạn ({pct(R['s_f2'])}) và không thêm gì cho LDA.</li>
<li><b>/f/ vs /θ/ vẫn không tách được:</b> tốt nhất {pct(max(R['f_f2'], R['f_lda'], R['f_cog']))}. Điều này ủng hộ việc chỉ hiển thị, không chấm cặp này.</li>
</ul></div>
<div class="warn"><div class="eyebrow">Giới hạn</div><ul>
<li>Chỉ 2 giọng. Với khoảng 100 đoạn /ʃ/ mỗi giọng, sai số lấy mẫu của một con số "đúng" khoảng ±3 điểm, nên chênh lệch dưới 4 điểm chưa đáng tin.</li>
<li>Nhãn MFA có thể sai (như ca "perhaps she"); mô hình học luôn cả nhãn sai.</li>
<li>"Chuẩn hoá theo người" ở đây dùng trung bình của mọi đoạn xì của chính người đó (5 loại: /s ʃ f θ z/). Trong app, học sinh chỉ nói một từ, nên cần bước hiệu chỉnh trước.</li></ul></div>

<section><div class="eyebrow">Vấn đề</div><h2>Một con số làm mất gì</h2>
<p>CoG nén cả phổ thành một giá trị. Hai âm có CoG ở cùng chỗ vẫn có thể có phổ khác nhau, và hai giọng khác nhau lại đẩy cả nhóm /s/ sang chỗ khác.</p>
<div class="fig">{fh('A1', True)}</div>
{box('read', 'Cách đọc', ['Mỗi cột là tỉ lệ đoạn có CoG rơi vào khoảng đó, tính riêng cho từng âm. Đường chấm là ngưỡng 4.340 Hz đang dùng trong app.', 'Vùng hai màu chồng lên nhau là những đoạn mà CoG không phân biệt được.'])}
{box('get', 'Điều rút ra', [f'Ngưỡng 4.340 Hz (lấy từ D1) cắt ngay giữa nhóm /ʃ/: chỉ {pct(REC["bdl"][1])} (bdl) và {pct(REC["slt"][1])} (slt) đoạn /ʃ/ nằm đúng phía, trong khi /s/ đúng {pct(REC["bdl"][0])} và {pct(REC["slt"][0])}.', f'Trung vị CoG của /s/ khác nhau {abs(mS["slt"] - mS["bdl"]):,.0f} Hz giữa hai giọng ({mS["bdl"]:,.0f} so với {mS["slt"]:,.0f}), còn của /ʃ/ chỉ khác {abs(mSH["slt"] - mSH["bdl"]):,.0f} Hz. Một ngưỡng chung cho mọi giọng sẽ lệch.'])}
<div class="fig">{fh('A2')}</div>
{box('read', 'Cách đọc', [f'Hai đoạn của cùng giọng bdl, một /s/ và một /ʃ/, có CoG gần như bằng nhau ({R["a2"][0]:,.0f} và {R["a2"][1]:,.0f} Hz). Hình vẽ phổ của từng đoạn.'])}
{box('get', 'Điều rút ra', [f'Cùng CoG nhưng /s/ có {pct(R["a2"][2])} năng lượng ở 2–4 kHz còn /ʃ/ có {pct(R["a2"][3])}. Phần năng lượng ở dải thấp là một dấu hiệu mà CoG không nhìn thấy.'])}</section>

<section><div class="eyebrow">Mức 1</div><h2>Vài đặc trưng hình dạng, dễ giải thích</h2>
<p>Thay vì một con số, lấy một nhóm nhỏ: đỉnh phổ (Fm), độ rộng (SD), độ lệch (skewness), độ nhọn (kurtosis) và tỉ lệ năng lượng trong từng dải 2 kHz.</p>
<div class="fig">{fh('B1')}</div>
{box('read', 'Cách đọc', ['Đường màu là phổ của một đoạn điển hình (đoạn có CoG gần trung vị của âm đó). Vạch đỏ là CoG, hình thoi đen là Fm (đỉnh phổ).', 'Phần trăm ở trên cùng mỗi dải là tỉ lệ năng lượng của dải đó trên tổng 0–8 kHz. Tiêu đề ghi SD, skewness, kurtosis.'])}
<div class="fig">{fh('B2')}</div>
{box('read', 'Cách đọc', ['Mỗi ô là một đặc trưng. Hộp cho thấy khoảng chứa nửa giữa số đoạn của mỗi âm, vạch ngang trong hộp là trung vị. Giá trị đã được chuẩn hoá trong từng giọng (z-score) để đặt hai giọng lên cùng thang.', 'Hộp của hai âm càng ít chồng nhau thì đặc trưng càng tách tốt. Con số trong tiêu đề là độ chính xác /s/–/ʃ/ chéo giọng khi chỉ dùng đặc trưng đó.'])}
<div class="fig">{fh('B3')}</div>
{box('read', 'Cách đọc', ['Mỗi cặp thanh là một đặc trưng. Thanh xám dùng giá trị tuyệt đối, thanh xanh dùng giá trị đã chuẩn hoá trong từng giọng. Đường chấm ở 50% là mức đoán ngẫu nhiên.'])}
{box('get', 'Điều rút ra', [f'Chuẩn hoá theo người nâng gần như mọi đặc trưng, đặc biệt Fm (từ {pct(R["fm_raw"])} lên {pct(R["fm_n"])}) vì nó bỏ đi khác biệt do giọng nam/nữ.', f'{names[R["best"]]} nhỉnh hơn CoG ({pct(R["best_v"])} so với {pct(R["cog_n"])}), nhưng chênh lệch nằm trong sai số lấy mẫu. Hai đặc trưng này mô tả cùng một hiện tượng: /ʃ/ có nhiều năng lượng ở dải thấp hơn.'])}</section>

<section><div class="eyebrow">Mức 2</div><h2>Mẫu phổ trung bình của mỗi âm</h2>
<p>Cách làm: lấy phổ trung bình của từng âm làm "mẫu", rồi xem một đoạn mới giống mẫu nào hơn. Học sinh sẽ thấy phổ của mình chồng lên mẫu.</p>
<div class="fig">{fh('C1')}</div>
{box('read', 'Cách đọc', ['Mỗi đường là phổ trung bình của một âm (đã bỏ mức to nhỏ của từng đoạn để chỉ còn hình dạng). Vùng mờ quanh đường là ± 1 độ lệch chuẩn.', 'Hai bên là hai giọng. Mẫu của hai âm càng cách xa nhau so với độ rộng vùng mờ thì càng dễ tách.'])}
<div class="fig">{fh('C2')}</div>
{box('read', 'Cách đọc', ['Mẫu lấy từ một giọng, thử trên giọng kia. Mỗi đoạn có một điểm: khoảng cách tới mẫu /ʃ/ trừ khoảng cách tới mẫu /s/. Điểm dương nghĩa là giống /s/ hơn.'])}
{box('get', 'Điều rút ra', [f'Mẫu phổ đạt {pct(C2["slt"])} (thử trên slt) và {pct(C2["bdl"])} (thử trên bdl), ngang CoG chuẩn hoá chứ không hơn. Giá trị của nó nằm ở chỗ <b>hiển thị được</b>: học sinh nhìn thấy phổ của mình lệch khỏi mẫu ở dải nào.'])}</section>

<section><div class="eyebrow">Mức 3</div><h2>Bộ phân biệt tuyến tính (LDA)</h2>
<p>LDA học một tổ hợp có trọng số của các đặc trưng để tách hai âm tốt nhất. Hai cách dùng: trên 40 dải phổ, hoặc trên 11 đặc trưng ở mức 1.</p>
<div class="fig">{fh('D1')}</div>
{box('read', 'Cách đọc', ['Mỗi đường là trọng số LDA theo tần số, học riêng trên từng giọng. Trọng số dương nghĩa là năng lượng ở dải đó làm đoạn nghiêng về /s/, âm nghĩa là nghiêng về /ʃ/.'])}
{box('get', 'Điều rút ra', [f'{wtxt} LDA 40 dải đạt {pct(R["shape_n"])} khi thử chéo giọng, thấp hơn CoG chuẩn hoá ({pct(R["cog_n"])}): với 2 giọng, mô hình học đặc điểm riêng của từng giọng nhiều hơn quy luật chung. Cần nhiều giọng hơn.'])}
<div class="fig">{fh('D2')}</div>
{box('read', 'Cách đọc', ['LDA trên 11 đặc trưng, huấn luyện trên cả hai giọng. Mỗi thanh là trọng số của một đặc trưng (đã chuẩn hoá nên so được với nhau).', 'Lưu ý: bốn tỉ lệ năng lượng (0–2, 2–4, 4–6, 6–8 kHz) cộng lại luôn bằng 100%, nên trọng số của chúng bù trừ nhau và không đọc riêng từng thanh được (ví dụ "% 0–2 kHz" có trọng số lớn dù một mình nó chỉ đạt khoảng 48%). Hãy đọc theo nhóm: nhóm các dải năng lượng nói chung với CoG, skewness, kurtosis.'])}
<div class="fig">{fh('D3')}</div>
{box('read', 'Cách đọc', ['Huấn luyện trên bdl, thử trên slt. Hai ô cùng một tập đoạn, chỉ khác cách tính điểm. Vùng hai màu chồng nhau càng nhỏ thì càng ít nhầm.'])}
{box('get', 'Điều rút ra', [f'Gộp đặc trưng: chiều bdl→slt từ {pct(R["cog_dir"][0])} lên {pct(R["lda_dir"][0])}, chiều slt→bdl từ {pct(R["cog_dir"][1])} lên {pct(R["lda_dir"][1])}. ' + ('Cải thiện ở cả hai chiều và vẫn giải thích được vì chỉ có 11 con số có tên.' if both_better else 'Chỉ cải thiện ở một chiều, nên chưa kết luận được.')])}</section>

<section><div class="eyebrow">Mức 4</div><h2>Pattern theo thời gian</h2>
<div class="fig">{fh('E1')}</div>
{box('read', 'Cách đọc', ['CoG đo trong 5 khoảng bằng nhau của đoạn xì (chỉ lấy đoạn từ 60 ms trở lên). Chấm là trung bình, thanh dọc là sai số chuẩn.'])}
{box('get', 'Điều rút ra', [f'CoG không phẳng: so với ba khoảng giữa, 10% đầu thấp hơn {tS[1] - tS[0]:,.0f} Hz (/s/) và {tSH[1] - tSH[0]:,.0f} Hz (/ʃ/), 10% cuối thấp hơn {tS[1] - tS[2]:,.0f} Hz và {tSH[1] - tSH[2]:,.0f} Hz. Hai đầu là chuyển tiếp từ và sang nguyên âm. Ba khoảng giữa (30–70%) ổn định, nên đo trên giữa 50% là hợp lý.', 'Trong ba khoảng giữa, đường /s/ và /ʃ/ song song, chỉ khác mức. Pattern theo thời gian không cho thêm thông tin tách âm ngoài mức CoG.'])}
<div class="fig">{fh('E2')}</div>
{box('read', 'Cách đọc', ['F2 (hình dạng khoang miệng) đo mỗi 10 ms sau khi tiếng xì kết thúc, trừ đi F2 ở giữa nguyên âm. Đường tiến về 0 nghĩa là F2 đã đạt mục tiêu của nguyên âm. Chỉ các đoạn có nguyên âm theo sau dài từ 80 ms.'])}
{box('get', 'Điều rút ra', [f'Trung bình, /ʃ/ bắt đầu cao hơn đích nguyên âm khoảng {f2sh:+,.0f} Hz rồi giảm dần về 0 trong 60 ms, còn /s/ gần như bằng 0 ({f2s:+,.0f} Hz). Khác biệt rõ trên đường trung bình, nhưng từng đoạn dao động mạnh: F2 một mình chỉ tách /s/–/ʃ/ được {pct(R["s_f2"])}, và thêm vào LDA không tăng ({pct(R["s_lda_rows"])} khi không có F2, {pct(R["s_lda_f2"])} khi có, cùng tập đoạn).', f'Với /f/ và /θ/: sau 10 ms, F2 của /f/ thấp hơn đích khoảng {abs(f2f):,.0f} Hz, của /θ/ khoảng {abs(f2th):,.0f} Hz. Chênh khoảng {abs(f2f) - abs(f2th):,.0f} Hz này thấy rõ trên đường trung bình (thanh sai số hầu như không chạm nhau), phù hợp với tài liệu cho rằng chuyển tiếp F2 mang thông tin /f/–/θ/. Nhưng /θ/ chỉ có {E2n[("bdl", "TH")]} và {E2n[("slt", "TH")]} đoạn, và từng đoạn dao động mạnh (một phần do nguyên âm theo sau khác nhau), nên thêm F2 chỉ đưa /f/–/θ/ từ {pct(R["f_lda"])} lên {pct(R["f_f2"])} (cùng tập đoạn). Đáng kiểm lại khi có 8 giọng, và nên thử chuẩn hoá F2 theo từng nguyên âm.'])}</section>

<section><div class="eyebrow">Bối cảnh</div><h2>Âm đứng sau ảnh hưởng tới /s/</h2>
<div class="fig">{fh('F')}</div>
{box('read', 'Cách đọc', ['CoG của /s/ (trái) và /ʃ/ (phải), chia theo âm đứng ngay sau. Nguyên âm tròn môi gồm UW, UH, OW, AO, OY.'])}
{box('get', 'Điều rút ra', [f'Số đoạn /s/ của cả hai giọng: nguyên âm tròn môi {ctxS.get("nguyên âm tròn môi", 0)}, nguyên âm khác {ctxS.get("nguyên âm khác", 0)}, phụ âm hoặc im lặng {ctxS.get("phụ âm / im lặng", 0)}. Nhóm tròn môi quá ít để kiểm tra hiệu ứng làm tròn môi.', f'Chênh lệch rõ hơn nằm giữa "trước nguyên âm" và "trước phụ âm hoặc im lặng": CoG /s/ cao hơn {dv["bdl"]:,.0f} Hz (bdl) và {dv["slt"]:,.0f} Hz (slt) khi có nguyên âm theo sau. Nên cân nhắc tách khoảng chuẩn theo bối cảnh, nhưng phải kiểm lại trên cả 8 giọng.'])}</section>

<section><div class="eyebrow">Tổng kết</div><h2>Mỗi cách đạt bao nhiêu</h2>
<div class="fig">{fh('G')}</div>
{box('read', 'Cách đọc', ['Mỗi thanh là độ chính xác cân bằng chéo giọng. Đường chấm ở 50% là đoán ngẫu nhiên. Với /f/–/θ/ lấy kết quả tốt hơn trong hai cách (tuyệt đối hoặc chuẩn hoá). Các dòng "các đoạn có F2" chỉ tính trên những đoạn có nguyên âm theo sau đủ dài, nên so với nhau chứ không so với các dòng khác.'])}
{box('get', 'Điều rút ra', ['Với /s/–/ʃ/: chuẩn hoá theo người là bước chắc chắn nhất. Gộp một số ít đặc trưng có tên cho trung bình cao nhất nhưng không ổn định giữa hai chiều. Hình dạng phổ chi tiết và F2 chưa giúp thêm ở quy mô 2 giọng.', 'Với /f/–/θ/: không cách nào vượt rõ ràng mức khoảng 75%. Giữ kế hoạch chỉ hiển thị.', 'Việc tiếp theo: lặp lại trên cả 8 giọng. Đó mới là phép thử thật cho mức 3 (40 dải).'])}</section>
</main></body></html>"""
import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, f"{len(html)/1e6:.1f} MB")
