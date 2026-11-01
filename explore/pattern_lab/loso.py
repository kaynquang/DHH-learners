"""Leave-one-speaker-out evaluation of the pattern ideas on many voices.

For every held-out voice: train on the others (pooled), test on the held-out voice, report balanced accuracy.
Methods are compared with a paired difference over voices (t interval, df = n_voices - 1).

usage: python loso.py <folder with tokens.pkl>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy import stats
from analysis import load, normalise, split, thresh_fn, lda_fn, template_fn, bal_acc, SCALARS, F2FEATS

S = sys.argv[1]
df = load(S)
df["contrast"] = df.shape_t.apply(np.std)
df["wobble"] = df.traj.apply(lambda a: np.std(a[1:4]) if not np.isnan(a).any() else np.nan)
df["shape_peak"] = df.shape_t.apply(np.max)
EXTRA = ["contrast", "wobble", "shape_peak"]
ALL = SCALARS + EXTRA
dfn = normalise(df, ALL + F2FEATS)
SPK = sorted(df.spk.unique())
print("voices:", SPK, "| tokens per phone:", df.groupby("phone").size().to_dict())

def gauss(cols):
    def f(a, b):
        X, y = a[cols].values, a.y.values
        mu = [X[y == c].mean(0) for c in (0, 1)]; sd = [X[y == c].std(0) + 1e-6 for c in (0, 1)]
        ll = lambda Z, c: (-0.5 * ((Z - mu[c]) / sd[c]) ** 2 - np.log(sd[c])).sum(1)
        return (ll(b[cols].values, 1) > ll(b[cols].values, 0)).astype(int)
    f.need = cols; return f

def loso(d, fn):
    out = {}
    for s in SPK:
        a, b = d[d.spk != s].dropna(subset=fn.need), d[d.spk == s].dropna(subset=fn.need)
        out[s] = bal_acc(b.y.values, fn(a, b)) if b.y.nunique() == 2 and len(b) > 10 else np.nan
    return pd.Series(out)

def report(title, d_raw, d_nrm, methods, baseline):
    res = {}
    for name, (which, fn) in methods.items():
        res[name] = loso(d_raw if which == "raw" else d_nrm, fn)
    R = pd.DataFrame(res).T
    base = R.loc[baseline]
    rows = []
    for name, r in R.iterrows():
        diff = (r - base).dropna()
        ci = stats.t.interval(0.95, len(diff) - 1, loc=diff.mean(), scale=stats.sem(diff)) if len(diff) > 2 and diff.std() > 0 else (np.nan, np.nan)
        rows.append(dict(method=name, mean=r.mean(), sd=r.std(), worst=r.min(), best=r.max(), d_vs_baseline=diff.mean(),
                         ci_lo=ci[0], ci_hi=ci[1], wins=int((diff > 0.005).sum()), losses=int((diff < -0.005).sum())))
    print(f"\n== {title}  (balanced accuracy, leave-one-voice-out over {len(SPK)} voices; baseline = {baseline})")
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("per voice:\n" + R.round(2).to_string())

FIVE = ["cog", "e2_4", "skew", "kurt", "fm"]
dr, dn = split(df, ("S", "SH")), split(dfn, ("S", "SH"))
report("/s/ vs /ʃ/", dr, dn, {
    "CoG, raw": ("raw", thresh_fn("cog")), "CoG, speaker-normalised": ("nrm", thresh_fn("cog")),
    "Fm, raw": ("raw", thresh_fn("fm")), "Fm, speaker-normalised": ("nrm", thresh_fn("fm")),
    "% energy 2-4 kHz, normalised": ("nrm", thresh_fn("e2_4")),
    "CoG Gaussian class-specific spread, normalised": ("nrm", gauss(["cog"])),
    "5 shape features LDA, normalised": ("nrm", lda_fn(cols=FIVE)),
    "11 scalars LDA, raw": ("raw", lda_fn(cols=SCALARS)), "11 scalars LDA, normalised": ("nrm", lda_fn(cols=SCALARS)),
    "13 scalars (+contrast, wobble) LDA, normalised": ("nrm", lda_fn(cols=ALL[:13])),
    "40-band shape LDA, normalised": ("nrm", lda_fn(shape="shape_n")),
    "40-band template Euclidean, normalised": ("nrm", template_fn("shape_n")),
}, "CoG, speaker-normalised")

d_all = df[df.phone.isin(["S", "SH", "F", "TH"])].copy(); d_all["y"] = d_all.phone.isin(["F", "TH"]).astype(int)
dn_all = dfn[dfn.phone.isin(["S", "SH", "F", "TH"])].copy(); dn_all["y"] = dn_all.phone.isin(["F", "TH"]).astype(int)
report("sibilant (/s ʃ/) vs weak hiss (/f θ/)", d_all, dn_all, {
    "relative amplitude (needs a vowel)": ("raw", thresh_fn("relamp")),
    "spectral contrast (no vowel)": ("raw", thresh_fn("contrast")),
    "spectral SD (no vowel)": ("raw", thresh_fn("sd")),
    "contrast + wobble + SD LDA (no vowel)": ("raw", lda_fn(cols=["contrast", "wobble", "sd"])),
    "relamp + contrast + wobble + SD LDA": ("raw", lda_fn(cols=["relamp", "contrast", "wobble", "sd"])),
    "relamp + contrast + wobble + SD LDA, normalised": ("nrm", lda_fn(cols=["relamp", "contrast", "wobble", "sd"])),
}, "relative amplitude (needs a vowel)")

dr_f, dn_f = split(df, ("F", "TH")), split(dfn, ("F", "TH"))
report("/f/ vs /θ/", dr_f, dn_f, {
    "CoG, raw": ("raw", thresh_fn("cog")), "CoG, speaker-normalised": ("nrm", thresh_fn("cog")),
    "wobble alone, raw": ("raw", thresh_fn("wobble")), "shape_peak alone, raw": ("raw", thresh_fn("shape_peak")),
    "CoG + wobble LDA, raw": ("raw", lda_fn(cols=["cog", "wobble"])), "CoG + wobble LDA, normalised": ("nrm", lda_fn(cols=["cog", "wobble"])),
    "13 scalars LDA, normalised": ("nrm", lda_fn(cols=ALL[:13])),
    "13 scalars + F2 LDA, normalised": ("nrm", lda_fn(cols=ALL[:13] + ["d0", "d10", "d30", "f2mid"])),
}, "CoG, speaker-normalised")
