"""Summarise phoneme_robust.py: context, noise and cross-splicing controls.

usage: python phoneme_robust_analysis.py <ph_robust.pkl>
"""
import sys
import numpy as np, pandas as pd

d = pd.read_pickle(sys.argv[1])
pd.set_option("display.width", 200)
G = ["S", "SH", "F", "TH"]
single = d[~d.cond.str.startswith("hybrid")]
print("== Single tokens: hard 4-way recall per class and two-way accuracy (mean over voices)")
rows = []
for cond, g in single.groupby("cond"):
    rec = {c: np.mean([(x[x.truth == c].pred == c).mean() for _, x in g.groupby("spk")]) for c in G}
    def pair(a, b):
        out = []
        for _, x in g.groupby("spk"):
            x = x[x.truth.isin([a, b])]; diff = x[f"m_{a}"] - x[f"m_{b}"]
            ok = np.where(x.truth == a, diff > 1e-3, diff < -1e-3)
            out.append(np.mean([ok[(x.truth == a).values].mean(), ok[(x.truth == b).values].mean()]))
        return np.mean(out), np.min(out)
    ssh, fth = pair("S", "SH"), pair("F", "TH")
    rows.append(dict(condition=cond, **{f"recall {c}": rec[c] for c in G}, **{"S vs SH": ssh[0], "S vs SH worst": ssh[1], "F vs TH": fth[0], "F vs TH worst": fth[1]}))
order = ["plain", "hiss_40ms", "hiss_only", "noise20", "noise10"]
print(pd.DataFrame(rows).set_index("condition").loc[order].round(3).to_string())

print("\n== Cross-spliced words: does the recogniser follow the HISS or the CONTEXT (the rest of the word)?")
h = d[d.cond.str.startswith("hybrid")].copy()
h["follows_hiss"] = h.apply(lambda r: r[f"m_{r.truth}"] > r[f"m_{r.context}"] + 1e-3, axis=1)
h["follows_context"] = h.apply(lambda r: r[f"m_{r.context}"] > r[f"m_{r.truth}"] + 1e-3, axis=1)
out = []
for cond, g in h.groupby("cond"):
    per = g.groupby("spk").follows_hiss.mean()
    out.append(dict(hybrid=cond.replace("hybrid:", ""), n=len(g), follows_hiss=g.follows_hiss.mean(), follows_context=g.follows_context.mean(),
                    neither=1 - g.follows_hiss.mean() - g.follows_context.mean(), worst_voice_follows_hiss=per.min()))
print(pd.DataFrame(out).set_index("hybrid").round(3).to_string())
print("\nexample decodes (hiss -> context):")
for cond, g in h.groupby("cond"):
    print(cond, "|", "; ".join(f"{r.pred}" for r in g.head(8).itertuples()))
