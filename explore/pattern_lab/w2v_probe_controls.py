"""Is the probe reading the consonant or the vowel/word that follows it? Leave-one-voice-out, per pair:
  vowel only      one-hot following vowel as the only feature
  probe           embeddings (as in w2v_probe_analysis.py)
  probe, vowel-removed   embeddings minus the training mean of their following vowel (both classes pooled)
  probe, vowel-matched   test restricted to vowels that occur in both classes of the held-out voice, each vowel weighted equally
python w2v_probe_controls.py probe3.pkl [layer]"""
import sys, pickle, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
df = pickle.load(open(sys.argv[1], "rb")); L = int(sys.argv[2]) if len(sys.argv) > 2 else 8
PAIRS = {"S/SH": ("S", "SH"), "F/TH": ("F", "TH"), "CH/SH": ("CH", "SH"), "P/B": ("P", "B"), "M/N": ("M", "N")}
def bal(y, p, a, b): return np.mean([np.mean(p[y == c] == c) for c in (a, b)])
def fit(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr); return LogisticRegression(C=0.05, max_iter=300, class_weight="balanced").fit(sc.transform(Xtr), ytr).predict(sc.transform(Xte))
out = []
for name, (a, b) in PAIRS.items():
    d = df[df.phone.isin([a, b])].reset_index(drop=True); X = np.stack(d[f"alone_{L}"].values); y = d.phone.values; V = d.vowel.values
    onehot = pd.get_dummies(d.vowel).values.astype(float)
    r = {k: [] for k in ("vowel only", "probe", "probe, vowel-removed", "probe, vowel-matched")}
    for v in d.spk.unique():
        tr, te = (d.spk != v).values, (d.spk == v).values
        r["vowel only"].append(bal(y[te], fit(onehot[tr], y[tr], onehot[te]), a, b))
        p = fit(X[tr], y[tr], X[te]); r["probe"].append(bal(y[te], p, a, b))
        gm = X[tr].mean(0); vm = {u: X[tr][V[tr] == u].mean(0) for u in set(V[tr])}
        Xr = X - np.stack([vm.get(u, gm) for u in V])
        r["probe, vowel-removed"].append(bal(y[te], fit(Xr[tr], y[tr], Xr[te]), a, b))
        both = [u for u in set(V[te]) if len({c for c in y[te][V[te] == u]}) == 2]
        accs = [bal(y[te][V[te] == u], p[V[te] == u], a, b) for u in both]
        if accs: r["probe, vowel-matched"].append(np.mean(accs))
    out.append((name, *[round(float(np.mean(r[k])), 3) if r[k] else np.nan for k in r]))
print(pd.DataFrame(out, columns=["pair", *r.keys()]).to_string(index=False))
print("\ntokens per class:", df.phone.value_counts().to_dict())
