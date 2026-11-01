"""Summary table of unified_eval output with speaker-cluster bootstrap intervals and an L2 dev/test split of speakers.
python unified_eval_analysis.py uni_arctic.pkl uni_l2.pkl index_l2arctic.csv"""
import sys
import numpy as np, pandas as pd
na, l2 = pd.read_pickle(sys.argv[1]), pd.read_pickle(sys.argv[2]); idx = pd.read_csv(sys.argv[3])
l1 = idx.drop_duplicates("speaker").set_index("speaker").L1
sp = sorted(l2.spk.unique()); test = [s for L in l1.unique() for s in sorted([x for x in sp if l1.get(x) == L])[2:]]
l2["split"] = np.where(l2.spk.isin(test), "test", "dev")
rng = np.random.default_rng(0)
def rate(df, col):
    return df[col].mean() if len(df) else np.nan
def boot(df, col, reps=1000):
    spk = df.spk.unique()
    if len(spk) < 2 or not len(df): return (np.nan, np.nan)
    g = {s: df[df.spk == s][col].values for s in spk}; out = []
    for _ in range(reps):
        v = np.concatenate([g[s] for s in rng.choice(spk, len(spk))]); out.append(v.mean())
    return tuple(np.percentile(out, [2.5, 97.5]))
def fmt(df, col):
    if not len(df): return "--"
    lo, hi = boot(df, col); return f"{rate(df, col)*100:.0f} [{lo*100:.0f},{hi*100:.0f}] n={len(df)}"
for d in (na, l2): d["reject"] = (d.color == "red") | d.gate; d["scored"] = d.color != "none"
print("Unscored share (no consonant/vowel found, gate not counted):")
rows = []
for p in ["S", "SH", "F", "CH", "M", "N", "P", "B"]:
    n, c, e = na[na.phone == p], l2[(l2.phone == p) & ~l2.error], l2[(l2.phone == p) & l2.error]
    ct, et = c[c.split == "test"], e[e.split == "test"]
    rows.append((p, fmt(n, "reject"), fmt(c, "reject"), fmt(ct, "reject"), fmt(e, "reject"), fmt(et, "reject"), f"{(1-n.scored.mean())*100:.0f}/{(1-c.scored.mean())*100:.0f}"))
print(pd.DataFrame(rows, columns=["sound", "native FR", "L2 FR (all)", "L2 FR (test spk)", "L2 Det (all)", "L2 Det (test spk)", "unscored % nat/L2"]).to_string(index=False))
print("\ntest speakers:", test)
