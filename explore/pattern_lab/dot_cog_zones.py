"""From dot_cog.pkl (arctic_dot_cog.py): where to put the s / sh zones of the live dot, measured the way the dot measures."""
import os
import numpy as np, pandas as pd
df = pd.read_pickle(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dot_cog.pkl"))


def best(a, b):
    """a: values of /s/ (higher), b: values of /sh/. AUC, best limit, balanced accuracy there."""
    x = np.concatenate([a, b]); y = np.r_[np.ones(len(a)), np.zeros(len(b))]
    order = np.argsort(x); ranks = np.empty(len(x)); ranks[order] = np.arange(1, len(x) + 1)
    auc = (ranks[y == 1].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))
    cand = np.unique(np.round(x, -1)); sc = [((a >= t).mean() + (b < t).mean()) / 2 for t in cand]
    i = int(np.argmax(sc)); return auc, cand[i], sc[i]


for col, name in (("cog_a", "the dot's measure (A)"), ("cog_b", "the scoring pipeline's measure (B)")):
    print("==", name)
    for spk in list(df.spk.unique()) + ["all"]:
        d = df if spk == "all" else df[df.spk == spk]
        s, sh = d[d.phone == "s"][col].dropna().to_numpy(), d[d.phone == "sh"][col].dropna().to_numpy()
        auc, t, ba = best(s, sh)
        print(f"  {spk:4s} AUC {auc:.2f}  best limit {t:.0f} Hz  balanced accuracy {ba:.2f}   /s/ median {np.median(s):.0f}  /sh/ median {np.median(sh):.0f}")
d = df
s, sh = d[d.phone == "s"].cog_a.dropna().to_numpy(), d[d.phone == "sh"].cog_a.dropna().to_numpy()
_, t, _ = best(s, sh)
print("\npooled limit", t, "-> share of /sh/ under (limit - m) and of /s/ over (limit + m), for margins m:")
for m in (150, 250, 350, 450):
    print(f"  m={m}: /sh/ below {t-m:.0f}: {np.mean(sh < t - m):.0%} (and /s/ below it: {np.mean(s < t - m):.0%});  /s/ above {t+m:.0f}: {np.mean(s >= t + m):.0%} (and /sh/ above it: {np.mean(sh >= t + m):.0%})")
