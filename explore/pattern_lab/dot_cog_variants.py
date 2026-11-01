"""Which way of computing the dot's centre of gravity keeps /s/ and /ʃ/ apart? Weights of the spectrum (magnitude or power) and the lower edge of the band, on ARCTIC (arctic_dot_cog.py)."""
import glob, os, sys
import numpy as np, pandas as pd
from scipy.io import wavfile
from scipy.signal import resample_poly
from arctic_dot_cog import labels, ROOT, FS, N, HOP, WIN, BIN_HZ

SPEAKERS = ["bdl", "slt", "rms", "clb"]
VARIANTS = [(1, 1000), (2, 1000), (2, 2000), (1, 2000), (2, 3000), (2, 1500)]       # (exponent of the magnitude, lower edge in Hz); the upper edge is 8000


def auc(a, b):
    x = np.concatenate([a, b]); y = np.r_[np.ones(len(a)), np.zeros(len(b))]
    order = np.argsort(x); r = np.empty(len(x)); r[order] = np.arange(1, len(x) + 1)
    return (r[y == 1].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))


def best(a, b):
    x = np.concatenate([a, b]); cand = np.unique(np.round(x, -1)); sc = [((a >= t).mean() + (b < t).mean()) / 2 for t in cand]
    i = int(np.argmax(sc)); return cand[i], sc[i]


rows = []
hi_bin = int(np.floor(8000 / BIN_HZ))
for spk in SPEAKERS:
    for lab in sorted(glob.glob(f"{ROOT}/cmu_us_{spk}_arctic/lab/arctic_*.lab")):
        segs = labels(lab)
        if not any(s[2] in ("s", "sh") for s in segs): continue
        fs, x = wavfile.read(lab.replace("lab", "wav").replace(".lab", ".wav")); x48 = resample_poly(x.astype(float) / 32768, 3, 1)
        for a, b, ph in segs:
            if ph not in ("s", "sh") or b - a < 0.08: continue
            a2, b2 = int((a + 0.2 * (b - a)) * FS), int((b - 0.2 * (b - a)) * FS)
            sm = np.zeros(N // 2); per = {v: [] for v in VARIANTS}; f = {v: None for v in VARIANTS}
            for end in range(N, min(len(x48), b2 + 1), HOP):
                mag = np.abs(np.fft.rfft(x48[end - N:end] * WIN))[:N // 2] / N
                sm = 0.5 * sm + 0.5 * mag
                if end < a2: continue
                for v in VARIANTS:
                    p, lo = v; lb = int(np.ceil(lo / BIN_HZ)); w = sm[lb:hi_bin + 1] ** p; fr = np.arange(lb, hi_bin + 1) * BIN_HZ
                    if w.sum() > 0:
                        c = float((w * fr).sum() / w.sum()); f[v] = c if f[v] is None else 0.6 * f[v] + 0.4 * c; per[v].append(f[v])
            if all(len(per[v]) >= 2 for v in VARIANTS):
                rows.append(dict(spk=spk, phone=ph, **{f"p{v[0]}_lo{v[1]}": float(np.median(per[v])) for v in VARIANTS}))
df = pd.DataFrame(rows); df.to_pickle(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dot_cog_variants.pkl"))
print("tokens:", len(df))
for v in VARIANTS:
    c = f"p{v[0]}_lo{v[1]}"; out = []
    for spk in SPEAKERS + ["all"]:
        d = df if spk == "all" else df[df.spk == spk]
        s, sh = d[d.phone == "s"][c].to_numpy(), d[d.phone == "sh"][c].to_numpy()
        out.append(f"{spk} AUC {auc(s, sh):.2f}")
    s, sh = df[df.phone == "s"][c].to_numpy(), df[df.phone == "sh"][c].to_numpy(); t, ba = best(s, sh)
    print(f"weights ^{v[0]}, from {v[1]} Hz: " + "; ".join(out) + f"  | pooled best limit {t:.0f} Hz, balanced accuracy {ba:.2f}; medians s {np.median(s):.0f} sh {np.median(sh):.0f}")
