"""Does using the *spread* of each sound help? Compare spread-aware rules with spread-blind ones.

usage: python variability.py <folder with tokens.pkl>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from analysis import load, normalise, split, thresh_fn, lda_fn, template_fn, cross, SCALARS, F2FEATS

S = sys.argv[1]
df = load(S)
mid = lambda a: np.nanstd(a[1:4]) if not np.isnan(a).any() else np.nan
df["traj_sd"] = df.traj.apply(mid)                                                  # CoG wobble across the middle of the hiss
df["traj_range"] = df.traj.apply(lambda a: np.ptp(a) if not np.isnan(a).any() else np.nan)
df["shape_sd"] = df.shape_t.apply(np.std)                                           # peakiness of the spectrum across frequency
df["shape_peak"] = df.shape_t.apply(np.max)
VAR = ["traj_sd", "traj_range", "shape_sd", "shape_peak", "sd"]
EXTRA = ["traj_sd", "traj_range", "shape_sd", "shape_peak"]

pd.set_option("display.width", 220)
print("== SPREAD of each sound (sd of the feature inside the class), per voice")
rows = []
for spk in ("bdl", "slt"):
    for ph in ("S", "SH", "F", "TH"):
        g = df[(df.spk == spk) & (df.phone == ph)]
        rows.append(dict(voice=spk, phone=ph, n=len(g), cog_sd=g.cog.std(), cog_iqr=g.cog.quantile(.75) - g.cog.quantile(.25),
                         e2_4_sd=g.e2_4.std(), fm_sd=g.fm.std(), relamp_sd=g.relamp.std(), shape_sd_med=g.shape_sd.median(),
                         traj_sd_med=g.traj_sd.median()))
print(pd.DataFrame(rows).round(2).to_string(index=False))
t = pd.DataFrame(rows).set_index(["voice", "phone"])
for spk in ("bdl", "slt"):
    print(f"{spk}: SD ratio /s/ : /ʃ/  CoG {t.loc[(spk,'S'),'cog_sd']/t.loc[(spk,'SH'),'cog_sd']:.2f}  e2_4 {t.loc[(spk,'S'),'e2_4_sd']/t.loc[(spk,'SH'),'e2_4_sd']:.2f}"
          f"   |  /f/ : /θ/  CoG {t.loc[(spk,'F'),'cog_sd']/t.loc[(spk,'TH'),'cog_sd']:.2f}")

def gauss(cols, shared=False):
    """Gaussian rule with equal priors. shared=True pools the spread (the classic midpoint rule)."""
    def f(a, b):
        X, y = a[cols].values, a.y.values
        mu = [X[y == c].mean(0) for c in (0, 1)]
        sd = [X[y == c].std(0) + 1e-6 for c in (0, 1)]
        if shared: sd = [np.sqrt((sd[0] ** 2 + sd[1] ** 2) / 2)] * 2
        ll = lambda Z, c: (-0.5 * ((Z - mu[c]) / sd[c]) ** 2 - np.log(sd[c])).sum(1)
        Z = b[cols].values
        return (ll(Z, 1) > ll(Z, 0)).astype(int)
    f.need = cols; return f

def qda_fn(cols, reg=0.3):
    def f(a, b):
        return QDA(priors=[0.5, 0.5], reg_param=reg).fit(a[cols].values, a.y.values).predict(b[cols].values)
    f.need = cols; return f

def template_var(shape, shared=False):
    """Diagonal Gaussian over the 40 bands, per class."""
    def f(a, b):
        A, B, y = np.stack(a[shape].values), np.stack(b[shape].values), a.y.values
        mu = [A[y == c].mean(0) for c in (0, 1)]; sd = [A[y == c].std(0) + 1.0 for c in (0, 1)]
        if shared: sd = [np.sqrt((sd[0] ** 2 + sd[1] ** 2) / 2)] * 2
        ll = lambda Z, c: (-0.5 * ((Z - mu[c]) / sd[c]) ** 2 - np.log(sd[c])).sum(1)
        return (ll(B, 1) > ll(B, 0)).astype(int)
    f.need = [shape]; return f

def run(pair, label):
    raw = split(df, pair); nrm = split(normalise(df, SCALARS + F2FEATS + EXTRA), pair)
    FIVE = ["cog", "e2_4", "skew", "kurt", "fm"]
    methods = [
        ("CoG: best threshold (spread-blind)", thresh_fn("cog")),
        ("CoG: Gaussian, pooled spread (midpoint rule)", gauss(["cog"], shared=True)),
        ("CoG: Gaussian, class-specific spread", gauss(["cog"])),
        ("5 shape features: Gaussian, pooled spread", gauss(FIVE, shared=True)),
        ("5 shape features: Gaussian, class-specific spread", gauss(FIVE)),
        ("5 shape features: LDA (shared covariance)", lda_fn(cols=FIVE)),
        ("5 shape features: QDA (class covariance)", qda_fn(FIVE)),
        ("11 scalars: LDA", lda_fn(cols=SCALARS)),
        ("11 scalars: QDA (class covariance)", qda_fn(SCALARS)),
        ("40-band template: Euclidean (spread-blind)", template_fn("shape_n")),
        ("40-band template: Gaussian, pooled spread", template_var("shape_n", shared=True)),
        ("40-band template: Gaussian, class-specific spread", template_var("shape_n")),
    ] + [(f"variability feature alone: {c}", thresh_fn(c)) for c in VAR]
    print(f"\n== {label}: balanced accuracy, cross-speaker  [raw avg (bdl>slt / slt>bdl)]  [normalised avg (bdl>slt / slt>bdl)]")
    for name, fn in methods:
        out = []
        for d, nm in ((raw, "raw"), (nrm, "nrm")):
            if nm == "raw" and fn.need and any(c.startswith("shape_n") for c in fn.need): out.append("      n/a        "); continue
            a, accs = cross(d, fn)
            out.append(f"{a:.2f} ({accs[0]:.2f}/{accs[1]:.2f})")
        print(f"{name:55} {out[0]:20} {out[1]}")

run(("S", "SH"), "/s/ vs /ʃ/"); run(("F", "TH"), "/f/ vs /θ/")
