"""Leave-one-voice-out accuracy of a linear probe on wav2vec2 layers, per pair, 'alone' vs 'context' clips. python w2v_probe_analysis.py probe.pkl"""
import sys, pickle, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
df = pickle.load(open(sys.argv[1], "rb"))
PAIRS = {"S/SH": ("S", "SH"), "F/TH": ("F", "TH"), "CH/SH": ("CH", "SH"), "P/B": ("P", "B"), "M/N": ("M", "N")}
layers = sorted({int(c.split("_")[1]) for c in df.columns if c.startswith("alone_")})
out = []
for name, (a, b) in PAIRS.items():
    d = df[df.phone.isin([a, b])]
    for cond in [c for c in ("alone", "ctx") if f"{c}_{layers[0]}" in df.columns]:
        for L in layers:
            X = np.stack(d[f"{cond}_{L}"].values); y = d.phone.values; accs = []
            for v in d.spk.unique():
                tr, te = d.spk.values != v, d.spk.values == v
                sc = StandardScaler().fit(X[tr])
                p = LogisticRegression(C=0.05, max_iter=300, class_weight="balanced").fit(sc.transform(X[tr]), y[tr]).predict(sc.transform(X[te]))
                accs.append(np.mean([np.mean(p[y[te] == c] == c) for c in (a, b)]))
            out.append((name, cond, L, np.mean(accs), np.min(accs), len(d)))
r = pd.DataFrame(out, columns=["pair", "clip", "layer", "mean", "worst", "n"]).round(3)
print(r.pivot_table(index=["pair", "layer"], columns="clip", values="mean").to_string())
print("\nBest per pair:"); print(r.loc[r.groupby(["pair", "clip"])["mean"].idxmax()].to_string(index=False))
