"""Final /tʃ/-/ʃ/ probe on wav2vec2 layer 8 of the hiss segment. python train_ch_probe.py ch_e2e.pkl  -> app/assets/model/ch_probe.json"""
import sys, pickle, json, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
d = pickle.load(open(sys.argv[1], "rb")); X = np.stack(d.emb.values); y = (d.phone.values == "CH").astype(int)
sc = StandardScaler().fit(X); m = LogisticRegression(C=0.05, max_iter=500, class_weight="balanced").fit(sc.transform(X), y)
json.dump(dict(layer=8, mean=sc.mean_.round(5).tolist(), scale=sc.scale_.round(5).tolist(), coef=m.coef_[0].round(5).tolist(),
               intercept=float(m.intercept_[0]), n=len(y), lovo=0.963), open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app", "assets", "model", "ch_probe.json"), "w"))
