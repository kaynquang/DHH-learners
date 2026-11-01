import os
import numpy as np, pandas as pd
df = pd.read_pickle(os.path.join(os.path.dirname(__file__), "arctic_ch.pkl"))


def best(a, b):
    """a = values of the target class (should be higher), b = the other class. Returns AUC, best threshold, balanced accuracy there."""
    x = np.concatenate([a, b]); y = np.r_[np.ones(len(a)), np.zeros(len(b))]
    order = np.argsort(x); ranks = np.empty(len(x)); ranks[order] = np.arange(1, len(x) + 1)
    auc = (ranks[y == 1].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))
    best_t, best_ba = None, 0
    for t in np.unique(x):
        ba = ((a >= t).mean() + (b < t).mean()) / 2
        if ba > best_ba: best_t, best_ba = t, ba
    return auc, best_t, best_ba


for spk in ("bdl", "slt", "both"):
    d = df if spk == "both" else df[df.spk == spk]
    ch, sh, t = d[d.phone == "ch"], d[d.phone == "sh"], d[d.phone == "t"]
    print(f"== {spk}")
    for name, col, sign in (("steepest climb of the 2.5-7.9 kHz envelope (dB/ms)", "slope_db_ms", 1), ("hiss length (ms)", "hiss_ms", -1), ("10-90% rise (ms)", "rise_ms", -1)):
        a, b = sign * ch[col].dropna().to_numpy(), sign * sh[col].dropna().to_numpy()
        auc, th, ba = best(a, b)
        print(f"  ch vs sh  {name}: AUC {auc:.2f}, best limit {sign * th:.1f}, balanced accuracy {ba:.2f}")
    for name, col, sign in (("hiss length (ms)", "hiss_ms", 1), ("centre of gravity (Hz)", "cog_hz", 1)):
        a, b = sign * ch[col].dropna().to_numpy(), sign * t[col].dropna().to_numpy()
        auc, th, ba = best(a, b)
        print(f"  ch vs t   {name}: AUC {auc:.2f}, best limit {sign * th:.1f}, balanced accuracy {ba:.2f}")
