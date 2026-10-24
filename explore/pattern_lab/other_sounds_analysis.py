"""Leave-one-voice-out accuracy of candidate measures for m/n and p/b. python other_sounds_analysis.py other.pkl"""
import sys, pickle, warnings
import numpy as np, pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
warnings.filterwarnings("ignore")
df = pickle.load(open(sys.argv[1], "rb"))

def bal(y, p, a, b):
    return np.mean([np.mean(p[y == c] == c) for c in (a, b)])

def study(a, b, singles, combos):
    d = df[df.phone.isin([a, b])].copy()
    print(f"\n== {a} vs {b}: tokens {d.phone.value_counts().to_dict()}")
    out = []
    for name, feats in [(f, [f]) for f in singles] + combos:
        x = d.dropna(subset=feats)
        for norm in ("raw", "per-voice z"):
            X = x[feats].copy()
            if norm != "raw":
                X = (X - X.groupby(x.spk).transform("mean")) / X.groupby(x.spk).transform("std")
            accs = []
            for v in x.spk.unique():
                tr, te = x.spk != v, x.spk == v
                m = LDA().fit(X[tr], x.phone[tr]); accs.append(bal(x.phone[te].values, m.predict(X[te]), a, b))
            out.append((name, norm, len(x), np.mean(accs), np.min(accs)))
    print(pd.DataFrame(out, columns=["measure", "scaling", "n", "mean", "worst voice"]).sort_values("mean", ascending=False).head(12).round(3).to_string(index=False))

study("M", "N", ["f2_15", "f2_30", "f2_50", "f2_slope", "f1_15", "f3_15", "mur_cog", "mur_lo", "mur_mid", "mur_hi"],
      [("f2_15+f2_50", ["f2_15", "f2_50"]), ("f2_15+f3_15", ["f2_15", "f3_15"]), ("f2_15+murmur lo/mid", ["f2_15", "mur_lo", "mur_mid"]),
       ("f2_15+f2_slope+mur_cog", ["f2_15", "f2_slope", "mur_cog"])])
study("P", "B", ["vot_ms", "prevoice_ms", "closure_ms", "dur_ms", "burst_rise_db", "burst_to_vowel_ms"],
      [("vot+prevoice", ["vot_ms", "prevoice_ms"]), ("vot+dur", ["vot_ms", "dur_ms"]), ("vot+prevoice+burst", ["vot_ms", "prevoice_ms", "burst_rise_db"])])
print("\nVOT (ms) medians by voice and class:"); print(df[df.phone.isin(["P", "B"])].groupby(["phone", "spk"]).vot_ms.median().unstack().round(0).to_string())
print("\nF2 at +15 ms (Hz) medians:"); print(df[df.phone.isin(["M", "N"])].groupby(["phone", "spk"]).f2_15.median().unstack().round(0).to_string())
print("\nCH rise time (ms), median per voice:"); print(df[df.phone == "CH"].groupby("spk").rise_ms.median().round(1).to_string(), "\nCH duration ms:", df[df.phone == "CH"].dur_ms.median())

study("CH", "SH", ["rise_ms", "dur_ms"], [("rise+dur", ["rise_ms", "dur_ms"])])
print("\nSH rise (ms), median per voice:"); print(df[df.phone == "SH"].groupby("spk").rise_ms.median().round(1).to_string(), "\nSH duration ms:", df[df.phone == "SH"].dur_ms.median())
# fixed VOT threshold for p/b (what a learner-facing rule would use)
d = df[df.phone.isin(["P", "B"])].dropna(subset=["vot_ms"])
print("\nVOT threshold sweep (raw, leave-one-voice-out threshold chosen on the other voices):")
accs = []
for v in d.spk.unique():
    tr, te = d[d.spk != v], d[d.spk == v]
    th = max(range(10, 50), key=lambda t: np.mean([np.mean((tr.vot_ms[tr.phone == c] >= t) == (c == "P")) for c in "PB"]))
    accs.append((v, th, np.mean([np.mean((te.vot_ms[te.phone == c] >= th) == (c == "P")) for c in "PB"])))
print(pd.DataFrame(accs, columns=["held-out voice", "threshold ms", "balanced acc"]).round(3).to_string(index=False), "\nmean", round(np.mean([a[2] for a in accs]), 3))
