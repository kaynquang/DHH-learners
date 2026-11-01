"""Variability features for /f/ vs /θ/ and for sibilant vs non-sibilant (no vowel needed).

usage: python variability2.py <folder with tokens.pkl>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from analysis import load, normalise, split, thresh_fn, lda_fn, bal_acc, cross, SCALARS, F2FEATS

S = sys.argv[1]
df = load(S)
df["traj_sd"] = df.traj.apply(lambda a: np.nanstd(a[1:4]) if not np.isnan(a).any() else np.nan)
df["shape_sd"] = df.shape_t.apply(np.std)
df["shape_peak"] = df.shape_t.apply(np.max)
EXTRA = ["traj_sd", "shape_sd", "shape_peak"]
dfn = normalise(df, SCALARS + F2FEATS + EXTRA)
rng = np.random.default_rng(0)

def boot(d, fn):
    out = []
    for tr, te in (("bdl", "slt"), ("slt", "bdl")):
        a, b = d[d.spk == tr].dropna(subset=fn.need), d[d.spk == te].dropna(subset=fn.need)
        p, y = fn(a, b), b.y.values; acc = bal_acc(y, p)
        i0, i1 = np.where(y == 0)[0], np.where(y == 1)[0]
        bs = [bal_acc(y[(ix := np.r_[rng.choice(i0, len(i0)), rng.choice(i1, len(i1))])], p[ix]) for _ in range(500)]
        out.append(f"{acc:.2f} [{np.percentile(bs, 2.5):.2f}-{np.percentile(bs, 97.5):.2f}]")
    return " | ".join(out)

print("== /f/ vs /θ/  (bdl>slt | slt>bdl), balanced accuracy [95% CI of the test set]")
for nm, d in (("raw", split(df, ("F", "TH"))), ("normalised", split(dfn, ("F", "TH")))):
    for label, fn in [("CoG alone", thresh_fn("cog")), ("traj_sd alone (CoG wobble across the hiss)", thresh_fn("traj_sd")),
                      ("shape_peak alone (how peaky the spectrum is)", thresh_fn("shape_peak")),
                      ("LDA cog + traj_sd", lda_fn(cols=["cog", "traj_sd"])),
                      ("LDA cog + shape_peak", lda_fn(cols=["cog", "shape_peak"])),
                      ("LDA traj_sd + shape_peak", lda_fn(cols=["traj_sd", "shape_peak"])),
                      ("LDA cog + traj_sd + shape_peak", lda_fn(cols=["cog", "traj_sd", "shape_peak"])),
                      ("LDA 11 scalars (reference)", lda_fn(cols=SCALARS))]:
        print(f"{nm:11} {label:46} {boot(d, fn)}   (rows: {len(d.dropna(subset=fn.need))})")

print("\n== sibilant (/s ʃ/) vs weak hiss (/f θ/), no vowel needed")
for nm, base in (("raw", df), ("normalised", dfn)):
    d = base[base.phone.isin(["S", "SH", "F", "TH"])].copy(); d["y"] = d.phone.isin(["F", "TH"]).astype(int)
    for label, fn in [("relative amplitude (needs a vowel)", thresh_fn("relamp")), ("shape_sd (spectral peakiness)", thresh_fn("shape_sd")),
                      ("traj_sd (CoG wobble)", thresh_fn("traj_sd")), ("spectral SD", thresh_fn("sd")),
                      ("LDA shape_sd + traj_sd + sd (no vowel)", lda_fn(cols=["shape_sd", "traj_sd", "sd"])),
                      ("LDA relamp + shape_sd + traj_sd + sd", lda_fn(cols=["relamp", "shape_sd", "traj_sd", "sd"]))]:
        print(f"{nm:11} {label:46} {boot(d, fn)}   (rows: {len(d.dropna(subset=fn.need))})")
