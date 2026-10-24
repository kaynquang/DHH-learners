"""How well does the phone recogniser separate /s ʃ f θ/, and does it add anything to the 13 features?

usage: python phoneme_analysis.py <folder with tokens.pkl> <phoneme_eval.pkl>
"""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy import stats
from analysis import load, normalise, thresh_fn, lda_fn, bal_acc, SCALARS

S, PH = sys.argv[1], sys.argv[2]
ph = pickle.load(open(PH, "rb"))
pd.set_option("display.width", 220)
G = ["S", "SH", "F", "TH"]
M = ph[[f"m_{g}" for g in G]].values
ph["pred"] = np.where(M.max(axis=1) < 0.02, "none", np.array(G)[M.argmax(axis=1)])
SPK = sorted(ph.spk.unique())
print(f"{len(ph)} word-initial clips from {len(SPK)} voices:", ph.groupby("phone").size().to_dict())

print("\n== 1. Hard 4-way decision (largest group mass over the hiss; 'none' = nothing above 0.02), pooled over voices")
conf = pd.crosstab(ph.phone, ph.pred).reindex(index=G, columns=G + ["none"], fill_value=0)
print(conf.to_string()); print((conf.div(conf.sum(axis=1), axis=0) * 100).round(0).astype(int).to_string())
per_voice = pd.DataFrame({s: {c: float((g[g.phone == c].pred == c).mean()) for c in G} for s, g in ph.groupby("spk")}).T
per_voice["balanced"] = per_voice[G].mean(axis=1)
print("recall per voice:\n" + per_voice.round(2).to_string())
print(f"4-way balanced accuracy across voices: mean {per_voice.balanced.mean():.3f}  sd {per_voice.balanced.std():.3f}  worst {per_voice.balanced.min():.2f}")

def pair(a, b, label):
    d = ph[ph.phone.isin([a, b])].copy(); d["diff"] = d[f"m_{a}"] - d[f"m_{b}"]
    d["abstain"] = d["diff"].abs() < 1e-3
    d["ok"] = np.where(d.phone == a, d["diff"] > 1e-3, d["diff"] < -1e-3)
    accs = {s: np.mean([g[g.phone == a].ok.mean(), g[g.phone == b].ok.mean()]) for s, g in d.groupby("spk")}
    ab = d.abstain.mean()
    print(f"{label}: balanced accuracy per voice mean {np.mean(list(accs.values())):.3f} sd {np.std(list(accs.values()), ddof=1):.3f} "
          f"worst {min(accs.values()):.2f} | abstain {ab:.0%} | {({k: round(v, 2) for k, v in accs.items()})}")
print("\n== 2. Two-way, by comparing the two groups' mass (abstentions count as wrong)")
pair("S", "SH", "/s/ vs /ʃ/"); pair("F", "TH", "/f/ vs /θ/"); pair("S", "F", "/s/ vs /f/ (control)")

print("\n== 3. Does it add to the 13 features? Leave-one-voice-out on the same word-initial tokens")
df = load(S)
df["contrast"] = df.shape_t.apply(np.std)
df["wobble"] = df.traj.apply(lambda a: np.std(a[1:4]) if not np.isnan(a).any() else np.nan)
ALL = SCALARS + ["contrast", "wobble"]
dfn = normalise(df, ALL)
dfn["start"] = dfn.start.round(3)
ph["start"] = ph.start.round(3)
mg = dfn.merge(ph[["spk", "file", "start"] + [f"m_{g}" for g in G]], on=["spk", "file", "start"], how="inner")
eps = 1e-3
mg["r_ssh"] = np.log(mg.m_S + eps) - np.log(mg.m_SH + eps)
mg["r_fth"] = np.log(mg.m_F + eps) - np.log(mg.m_TH + eps)
print("merged tokens:", len(mg), mg.groupby("phone").size().to_dict())

def loso(d, fn):
    out = {}
    for s in SPK:
        a, b = d[d.spk != s].dropna(subset=fn.need), d[d.spk == s].dropna(subset=fn.need)
        out[s] = bal_acc(b.y.values, fn(a, b)) if b.y.nunique() == 2 else np.nan
    return pd.Series(out)

def report(a, b, rcol, label):
    d = mg[mg.phone.isin([a, b])].copy(); d["y"] = (d.phone == b).astype(int)
    d = d.dropna(subset=ALL + [rcol])
    res = {"13 features": loso(d, lda_fn(cols=ALL)), "recogniser alone": loso(d, thresh_fn(rcol)),
           "13 features + recogniser": loso(d, lda_fn(cols=ALL + [rcol]))}
    base = res["13 features"]
    print(f"\n{label}  ({len(d)} tokens: {d.groupby('phone').size().to_dict()})")
    for k, v in res.items():
        diff = (v - base).dropna()
        ci = stats.t.interval(0.95, len(diff) - 1, loc=diff.mean(), scale=stats.sem(diff)) if diff.std() > 0 else (np.nan, np.nan)
        extra = "" if k == "13 features" else f"  vs 13 features {diff.mean():+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}] wins {int((diff > .005).sum())} losses {int((diff < -.005).sum())}"
        print(f"  {k:26} mean {v.mean():.3f} sd {v.std():.3f} worst {v.min():.2f}{extra}")
report("S", "SH", "r_ssh", "/s/ vs /ʃ/"); report("F", "TH", "r_fth", "/f/ vs /θ/")
