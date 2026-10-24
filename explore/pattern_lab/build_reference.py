"""Pack per-voice, per-phone pattern statistics from tokens.pkl into a small JSON for the app.

usage: python build_reference.py <folder with tokens.pkl> <out.json>
"""
import json, pickle, sys
import numpy as np

S, OUT = sys.argv[1], sys.argv[2]
df = pickle.load(open(f"{S}/tokens.pkl", "rb"))
SCALARS = ["cog", "fm", "sd", "skew", "kurt", "e0_2", "e2_4", "e4_6", "e6_8", "relamp", "dur", "contrast", "wobble"]
df["dur"] = df.dur_ms
df["contrast"] = df["shape"].apply(lambda s: float(np.std(s)))                                        # spectral peakiness across frequency (dB)
df["wobble"] = df["traj"].apply(lambda a: float(np.std(a[1:4])) if not np.isnan(a).any() else np.nan)  # CoG variation across the middle of the hiss (Hz)
sh = np.stack(df["shape"].values)
df["shape_t"] = list(sh - sh.mean(axis=1, keepdims=True))
MAXF = {"bdl": 5000.0, "slt": 5500.0}

def q5(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return [round(float(v), 4) for v in np.percentile(x, [5, 25, 50, 75, 95])]

def stack(col):
    return np.stack(col.values)

out = {"meta": {"source": "CMU ARCTIC bdl (male) + slt (female), first 300 sentences each, MFA labels not hand-checked",
                "sample_rate_hz": 16000, "grid_hz": [int(v) for v in np.arange(100, 8000, 200)], "scalars": SCALARS,
                "tokens": int(len(df)), "sentences_per_voice": {s: int(df[df.spk == s].file.nunique()) for s in MAXF}},
       "voices": {}}
for spk, d in df.groupby("spk"):
    v = {"sex": d.sex.iloc[0], "max_formant_hz": MAXF[spk], "phones": {}}
    for ph, g in d.groupby("phone"):
        T = stack(g.traj); T = T[~np.isnan(T).any(axis=1)]
        F2 = stack(g.f2) - g.f2mid.values[:, None]; F2 = F2[~np.isnan(F2).any(axis=1)]
        Sh = stack(g.shape_t)
        v["phones"][ph] = {
            "n": int(len(g)), "q": {k: q5(g[k]) for k in SCALARS},
            "shape_mean": [round(float(x), 3) for x in Sh.mean(0)], "shape_sd": [round(float(x), 3) for x in Sh.std(0)],
            "traj_n": int(len(T)), "traj_mean": [round(float(x), 1) for x in T.mean(0)],
            "traj_se": [round(float(x), 1) for x in T.std(0) / np.sqrt(len(T))],
            "f2_n": int(len(F2)), "f2_mean": [round(float(x), 1) for x in F2.mean(0)] if len(F2) else [],
            "f2_se": [round(float(x), 1) for x in F2.std(0) / np.sqrt(len(F2))] if len(F2) else []}
    out["voices"][spk] = v
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print("wrote", OUT, f"{len(json.dumps(out)) / 1024:.0f} KB", {s: {p: x['n'] for p, x in v['phones'].items()} for s, v in out['voices'].items()})
