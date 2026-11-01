import os, numpy as np, pandas as pd
df = pd.read_pickle(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dot_cog_variants.pkl"))
c = "p2_lo2000"
s, sh = df[df.phone == "s"][c].to_numpy(), df[df.phone == "sh"][c].to_numpy()
print("pooled /s/ percentiles 10/25/50/75/90:", [int(np.percentile(s, q)) for q in (10, 25, 50, 75, 90)])
print("pooled /sh/ percentiles 10/25/50/75/90:", [int(np.percentile(sh, q)) for q in (10, 25, 50, 75, 90)])
for spk in df.spk.unique():
    d = df[df.spk == spk]; a, b = d[d.phone == "s"][c], d[d.phone == "sh"][c]
    print(f"  {spk}: /s/ median {a.median():.0f}, /sh/ median {b.median():.0f}, midpoint {(a.median()+b.median())/2:.0f}")
t = 4240
for m in (200, 300, 400):
    print(f"limit {t} margin {m}: /sh/ under {t-m}: {np.mean(sh < t-m):.0%} (of /s/: {np.mean(s < t-m):.0%});  /s/ over {t+m}: {np.mean(s >= t+m):.0%} (of /sh/: {np.mean(sh >= t+m):.0%});  in between: /sh/ {np.mean((sh>=t-m)&(sh<t+m)):.0%} /s/ {np.mean((s>=t-m)&(s<t+m)):.0%}")
