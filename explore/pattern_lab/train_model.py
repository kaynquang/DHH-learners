"""Train the calibrated LDA models from tokens.pkl (8 ARCTIC voices) and write app/assets/model/calibrated_lda.json.

Every voice is normalised from a class-balanced sample of /s/, /ʃ/ and /f/ tokens, the same recipe the app applies to the
learner's six calibration recordings (see, she, fee, twice each). Equal class priors.

usage: python train_model.py <folder with tokens.pkl> <out.json>
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from analysis import load, SCALARS

S, OUT = sys.argv[1], sys.argv[2]
df = load(S)
df["contrast"] = df.shape_t.apply(np.std)
df["wobble"] = df.traj.apply(lambda a: np.std(a[1:4]) if not np.isnan(a).any() else np.nan)
FEATS = SCALARS + ["contrast", "wobble"]
FAMILY = ["relamp", "contrast", "wobble", "sd"]
FAMILY_NOVOWEL = ["contrast", "wobble", "sd"]
BAL, N_BAL, K_CAL = ("S", "SH", "F"), 80, 2
SPK = sorted(df.spk.unique())

def stats(raw, k, rng):
    sub = pd.concat([raw[raw.phone == p].sample(k, random_state=int(rng.integers(1e9))) for p in BAL])
    sd = sub[FEATS].std().replace(0, np.nan).fillna(1.0)
    return sub[FEATS].mean(), sd

def normalised(raw, mu, sd):
    out = raw.copy(); out[FEATS] = (out[FEATS] - mu) / sd; return out

def fit(train, feats, pos):
    d = train.dropna(subset=feats)
    m = LDA(solver="lsqr", shrinkage="auto", priors=[0.5, 0.5]).fit(d[feats].values, d.phone.isin(pos).astype(int).values)
    return m

def spec(m, feats, positive):
    return {"features": feats, "coef": [round(float(c), 6) for c in m.coef_[0]], "intercept": round(float(m.intercept_[0]), 6), "positive": positive}

def models(train):
    sib = train[train.phone.isin(["S", "SH"])]; fam = train[train.phone.isin(["S", "SH", "F", "TH"])]
    return (fit(sib, FEATS, ["SH"]), fit(fam, FAMILY, ["F", "TH"]), fit(fam, FAMILY_NOVOWEL, ["F", "TH"]))

def read(models_, row):
    """(p_s, p_sh, p_weak, p_sh_if_sibilant) for one standardised token, mirroring fricative.calibrated.read."""
    m_sib, m_fam, m_nv = models_
    z = row[FEATS].astype(float).fillna(0.0)
    fam = m_fam if not np.isnan(row["relamp"]) else m_nv
    cols = FAMILY if fam is m_fam else FAMILY_NOVOWEL
    p_weak = 1 / (1 + np.exp(-float(fam.decision_function(z[cols].values[None])[0])))
    p_sh = 1 / (1 + np.exp(-float(m_sib.decision_function(z[FEATS].values[None])[0])))
    return (1 - p_weak) * (1 - p_sh), (1 - p_weak) * p_sh, p_weak, p_sh

def train_set(voices, rng):
    parts = []
    for s in voices:
        raw = df[df.spk == s]
        mu, sd = stats_n(raw, rng)
        parts.append(normalised(raw[raw.phone.isin(["S", "SH", "F", "TH"])], mu, sd))
    return pd.concat(parts)

def stats_n(raw, rng):
    return stats(raw, N_BAL, rng)

print("self-check: leave-one-voice-out, held-out voice normalised from its own", 3 * K_CAL, "tokens")
rng = np.random.default_rng(0)
res = {"s_vs_sh_if_sibilant": [], "family": [], "three_way": []}
for held in SPK:
    tr = train_set([s for s in SPK if s != held], np.random.default_rng(1))
    mods = models(tr)
    raw = df[(df.spk == held) & df.phone.isin(["S", "SH", "F", "TH"])]
    accs = {k: [] for k in res}
    for _ in range(10):
        mu, sd = stats(df[df.spk == held], K_CAL, rng)
        te = normalised(raw, mu, sd)
        P = np.array([read(mods, r) for _, r in te.iterrows()])
        heard = P[:, :3].argmax(axis=1)                            # 0 s, 1 sh, 2 weak
        p_sh_cond = P[:, 3]
        truth = te.phone.map({"S": 0, "SH": 1, "F": 2, "TH": 2}).values
        sib = te.phone.isin(["S", "SH"]).values
        rec = lambda mask, cls: float((heard[mask] == cls).mean())
        accs["s_vs_sh_if_sibilant"].append(np.mean([float((p_sh_cond[te.phone.values == "S"] < 0.5).mean()), float((p_sh_cond[te.phone.values == "SH"] >= 0.5).mean())]))
        accs["family"].append(np.mean([float((heard[sib] != 2).mean()), float((heard[~sib] == 2).mean())]))
        accs["three_way"].append(np.mean([rec(te.phone.values == "S", 0), rec(te.phone.values == "SH", 1), rec(truth == 2, 2)]))
    for k in res: res[k].append(float(np.mean(accs[k])))
    print(f"  held out {held}: /s/-/ʃ/ (given sibilant) {res['s_vs_sh_if_sibilant'][-1]:.3f}  family {res['family'][-1]:.3f}  three-way {res['three_way'][-1]:.3f}")
summ = {k: {"mean": round(float(np.mean(v)), 3), "sd": round(float(np.std(v, ddof=1)), 3), "worst": round(float(np.min(v)), 3)} for k, v in res.items()}
print("summary:", summ)

final = models(train_set(SPK, np.random.default_rng(1)))
out = {"meta": {"voices": SPK, "protocol": f"normalise from {K_CAL} tokens of each of /s/ /ʃ/ /f/ (see, she, fee twice); training stats from {N_BAL} per class",
                "features": FEATS, "calibration_tokens": 3 * K_CAL, "tokens_trained_on": int(df.phone.isin(["S", "SH", "F", "TH"]).sum()),
                "leave_one_voice_out": summ, "weak_hiss_covers": "/f/ and /θ/ (not told apart)"},
       "sibilant": spec(final[0], FEATS, "SH"), "family": spec(final[1], FAMILY, "weak"), "family_novowel": spec(final[2], FAMILY_NOVOWEL, "weak")}
json.dump(out, open(OUT, "w"), indent=1)
print("wrote", OUT)
