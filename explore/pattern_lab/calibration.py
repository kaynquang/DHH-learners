"""Two controls on the 8-voice result.

1. /f/ vs /θ/: does F2 help once the comparison uses exactly the same rows?
2. Speaker normalisation: how many of the user's own tokens does it need? (the app has to ask for them)

usage: python calibration.py <folder with tokens.pkl>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy import stats
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from analysis import load, normalise, split, thresh_fn, lda_fn, bal_acc, best_thresh, SCALARS, F2FEATS

S = sys.argv[1]
df = load(S)
df["contrast"] = df.shape_t.apply(np.std)
df["wobble"] = df.traj.apply(lambda a: np.std(a[1:4]) if not np.isnan(a).any() else np.nan)
df["shape_peak"] = df.shape_t.apply(np.max)
ALL = SCALARS + ["contrast", "wobble"]
dfn = normalise(df, ALL + ["shape_peak"] + F2FEATS)
SPK = sorted(df.spk.unique())

def loso(d, fn):
    out = {}
    for s in SPK:
        a, b = d[d.spk != s].dropna(subset=fn.need), d[d.spk == s].dropna(subset=fn.need)
        out[s] = bal_acc(b.y.values, fn(a, b))
    return pd.Series(out)

def paired(a, b):
    diff = (a - b).dropna()
    lo, hi = stats.t.interval(0.95, len(diff) - 1, loc=diff.mean(), scale=stats.sem(diff))
    return f"{diff.mean():+.3f} [{lo:+.3f}, {hi:+.3f}] wins {int((diff > .005).sum())} losses {int((diff < -.005).sum())}"

print("== 1. /f/ vs /θ/ on the SAME rows (only tokens followed by a vowel of 80 ms or more)")
F2 = ["d0", "d10", "d30", "f2mid"]
d = split(dfn, ("F", "TH")).dropna(subset=ALL + F2)
print("rows:", len(d), d.groupby("phone").size().to_dict())
r = {"CoG": loso(d, thresh_fn("cog")), "13 scalars LDA": loso(d, lda_fn(cols=ALL)), "F2 features alone LDA": loso(d, lda_fn(cols=F2)),
     "13 scalars + F2 LDA": loso(d, lda_fn(cols=ALL + F2))}
for k, v in r.items(): print(f"{k:24} mean {v.mean():.3f}  sd {v.std():.3f}  worst {v.min():.2f}")
print("F2 added to the 13 scalars:", paired(r["13 scalars + F2 LDA"], r["13 scalars LDA"]))
print("13 scalars + F2 vs CoG   :", paired(r["13 scalars + F2 LDA"], r["CoG"]))

print("\n== 2. /s/ vs /ʃ/: speaker normalisation from only k of the held-out voice's own tokens (all five classes, random)")
rng = np.random.default_rng(0)
tr_all = split(dfn, ("S", "SH"))
def run(k, strat=False, reps=15):
    res = {"CoG": [], "LDA 13": []}
    for _ in range(1 if k is None else reps):
        a_cog, a_lda = [], []
        for held in SPK:
            train = tr_all[tr_all.spk != held].dropna(subset=ALL)
            raw = df[df.spk == held]
            if k is None: sub = raw
            elif strat: sub = pd.concat([raw[raw.phone == p].sample(k, random_state=int(rng.integers(1e9))) for p in ("S", "SH", "F")])
            else: sub = raw.sample(k, random_state=int(rng.integers(1e9)))
            mu, sd = sub[ALL].mean(), sub[ALL].std().replace(0, np.nan).fillna(1.0)
            test = split(raw, ("S", "SH")).copy(); test[ALL] = (test[ALL] - mu) / sd
            test = test.dropna(subset=ALL)
            _, t0, o = best_thresh(train.cog.values, train.y.values)
            a_cog.append(bal_acc(test.y.values, (o * (test.cog.values - t0) > 0).astype(int)))
            m = LDA(solver="lsqr", shrinkage="auto", priors=[.5, .5]).fit(train[ALL].values, train.y.values)
            a_lda.append(bal_acc(test.y.values, m.predict(test[ALL].values)))
        res["CoG"].append(np.mean(a_cog)); res["LDA 13"].append(np.mean(a_lda))
    return {k2: (np.mean(v), np.std(v)) for k2, v in res.items()}
print(f"{'calibration tokens':32} {'CoG thr':>14} {'LDA 13 scalars':>16}")
for k in (2, 4, 8, 16, 32, 64, 128):
    r = run(k); print(f"{k:3d} random tokens{'':16} {r['CoG'][0]:.3f} ±{r['CoG'][1]:.3f}   {r['LDA 13'][0]:.3f} ±{r['LDA 13'][1]:.3f}")
for k in (1, 2, 4, 8):
    r = run(k, strat=True); print(f"{k:3d} per word (see, she, fee){'':5} {r['CoG'][0]:.3f} ±{r['CoG'][1]:.3f}   {r['LDA 13'][0]:.3f} ±{r['LDA 13'][1]:.3f}   ({3 * k} tokens)")
r = run(None); print(f"all tokens of the voice{'':9} {r['CoG'][0]:.3f}            {r['LDA 13'][0]:.3f}")

print("\n== 3. Same protocol for training and for the user: normalise every voice from a class-balanced set of S, SH, F tokens")
BAL = ("S", "SH", "F")
def bal_stats(raw, k, seed):
    r = np.random.default_rng(seed)
    sub = pd.concat([raw[raw.phone == p].sample(k, random_state=int(r.integers(1e9)), replace=len(raw[raw.phone == p]) < k) for p in BAL])
    return sub[ALL].mean(), sub[ALL].std().replace(0, np.nan).fillna(1.0)
def train_set(held, n=80):
    parts = []
    for s in SPK:
        if s == held: continue
        raw = df[df.spk == s]; mu, sd = bal_stats(raw, n, 1)
        t = split(raw, ("S", "SH")).copy(); t[ALL] = (t[ALL] - mu) / sd; parts.append(t)
    return pd.concat(parts).dropna(subset=ALL)
trains = {h: train_set(h) for h in SPK}
print(f"{'calibration':34} {'CoG thr':>14} {'LDA 13 scalars':>16}")
for k in (1, 2, 4, 8, 16):
    c, l = [], []
    for _ in range(15):
        a_c, a_l = [], []
        for held in SPK:
            train = trains[held]; raw = df[df.spk == held]
            mu, sd = bal_stats(raw, k, int(rng.integers(1e9)))
            test = split(raw, ("S", "SH")).copy(); test[ALL] = (test[ALL] - mu) / sd; test = test.dropna(subset=ALL)
            _, t0, o = best_thresh(train.cog.values, train.y.values)
            a_c.append(bal_acc(test.y.values, (o * (test.cog.values - t0) > 0).astype(int)))
            m = LDA(solver="lsqr", shrinkage="auto", priors=[.5, .5]).fit(train[ALL].values, train.y.values)
            a_l.append(bal_acc(test.y.values, m.predict(test[ALL].values)))
        c.append(np.mean(a_c)); l.append(np.mean(a_l))
    print(f"{k:2d} per word (see, she, fee) = {3*k:2d} tokens {np.mean(c):.3f} ±{np.std(c):.3f}   {np.mean(l):.3f} ±{np.std(l):.3f}")
