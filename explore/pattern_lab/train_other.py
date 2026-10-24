"""Leave-one-voice-out check and final LDA for /m/-/n/ and /tʃ/-/ʃ/ (raw features, no per-voice normalisation: the app has no
calibration for these sounds). Writes app/assets/model/other_lda.json. python train_other.py na.pkl"""
import sys, pickle, json, warnings; warnings.filterwarnings("ignore")
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
o = pickle.load(open(sys.argv[1], "rb"))
SPECS = {"nasal": (["M", "N"], [f"f{i}_{k}" for i in (1, 2, 3) for k in range(0, 90, 20)]),
         "affricate": (["CH", "SH"], ["rise_ms", "rise_db_per_ms"])}
model = {}
for name, ((a, b), feats) in SPECS.items():
    d = o[o.phone.isin([a, b])].dropna(subset=feats)
    accs = []
    for v in d.spk.unique():
        tr, te = d[d.spk != v], d[d.spk == v]
        p = LDA(solver="lsqr", shrinkage="auto", priors=[.5, .5]).fit(tr[feats], tr.phone).predict(te[feats])
        accs.append(np.mean([np.mean(p[te.phone.values == c] == c) for c in (a, b)]))
    print(name, "LOVO balanced", round(np.mean(accs), 3), "worst", round(min(accs), 3), "n", len(d))
    m = LDA(solver="lsqr", shrinkage="auto", priors=[.5, .5]).fit(d[feats], d.phone)
    assert list(m.classes_) == sorted([a, b])
    # decision > 0 means the second class in sorted order
    model[name] = dict(features=feats, classes=list(m.classes_), coef=m.coef_[0].tolist(), intercept=float(m.intercept_[0]),
                       mean=d[feats].mean().tolist(), n=len(d), lovo=round(float(np.mean(accs)), 3))
model.pop("nasal")      # Praat formant features only reach 0.63 for m/n: the app uses the phone recogniser instead
json.dump(model, open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app", "assets", "model", "other_lda.json"), "w"), indent=1)
