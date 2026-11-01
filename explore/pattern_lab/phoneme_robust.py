"""Does the phone recogniser really listen to the hiss? Context, noise and cross-splicing controls.

Conditions (all on word-initial fricatives from ARCTIC):
  plain       the hiss with 80 ms before and 300 ms after (a stand-in for an isolated word)
  hiss_only   the hiss with 30 ms margins: no vowel, no word to guess from
  hiss_40ms   the hiss plus 40 ms of the vowel
  noise20/10  plain, with white noise at that SNR
  hybrids     the hiss of one sound spliced into the context (the rest of the word) of another:
              does the recogniser follow the hiss or the context?

usage: W2V_DIR=<model> python phoneme_robust.py <scratch folder> <ph_full.pkl> <out.pkl> [tokens per class per voice]
"""
import os, sys, pickle, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, parselmouth
import w2v_phones as W

S, PH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 40
SR, PRE, POST = 16000, 0.08, 0.30
rng = np.random.default_rng(1)
src = pickle.load(open(PH, "rb"))
G = ["S", "SH", "F", "TH"]
_cache = {}

def wav(spk, base):
    k = (spk, base)
    if k not in _cache:
        _cache.clear(); _cache[k] = parselmouth.Sound(f"{S}/wav_{spk}/{base}.wav").values[0]
    return _cache[k]

def cut(x, t0, t1):
    return x[max(0, int(t0 * SR)):max(0, int(t1 * SR))]

def noisy(x, snr_db):
    return x + rng.normal(0, np.sqrt(np.mean(x ** 2)) / 10 ** (snr_db / 20), len(x))

def masses(x, t0, t1):
    return W.group_mass(W.posteriors(x), t0, t1)

def verdict(m):
    v = np.array([m[g] for g in G])
    return "none" if v.max() < 0.02 else G[int(v.argmax())]

rows, t_start = [], time.time()
for spk, d in src.groupby("spk"):
    pick = {c: g.sample(min(N, len(g)), random_state=int(rng.integers(1e9))) for c, g in d.groupby("phone")}
    toks = pd.concat(pick.values())
    for _, r in toks.iterrows():
        x = wav(spk, r.file); a, b = r.start, r.end
        plain = cut(x, a - PRE, b + POST)
        for cond, clip, w0, w1 in [("plain", plain, PRE, PRE + b - a),
                                   ("noise20", noisy(plain, 20), PRE, PRE + b - a), ("noise10", noisy(plain, 10), PRE, PRE + b - a),
                                   ("hiss_only", cut(x, a - 0.03, b + 0.03), 0.03, 0.03 + b - a),
                                   ("hiss_40ms", cut(x, a - 0.03, b + 0.04), 0.03, 0.03 + b - a)]:
            m = masses(clip, w0, w1)
            rows.append(dict(spk=spk, cond=cond, truth=r.phone, pred=verdict(m), **{f"m_{g}": m[g] for g in G}))
    print(f"  {spk}: single-token conditions done ({len(rows)} clips, {time.time() - t_start:.0f}s)", flush=True)
    for hiss_c, ctx_c in [("S", "SH"), ("SH", "S"), ("F", "TH"), ("TH", "F")]:
        hs, cs = d[d.phone == hiss_c], d[d.phone == ctx_c]
        for _ in range(N):
            h, c = hs.iloc[int(rng.integers(len(hs)))], cs.iloc[int(rng.integers(len(cs)))]
            xh, xc = wav(spk, h.file), wav(spk, c.file)
            hiss = cut(xh, h.start, h.end).copy(); own = cut(xc, c.start, c.end)
            hiss *= np.sqrt(np.mean(own ** 2)) / (np.sqrt(np.mean(hiss ** 2)) + 1e-9)     # same hiss level as the word it replaces
            f = min(int(0.005 * SR), len(hiss) // 4); ramp = np.linspace(0, 1, f)
            hiss[:f] *= ramp; hiss[-f:] *= ramp[::-1]
            pre, post = cut(xc, c.start - PRE, c.start), cut(xc, c.end, c.end + POST)
            clip = np.concatenate([pre, hiss, post])
            m = masses(clip, len(pre) / SR, (len(pre) + len(hiss)) / SR)
            rows.append(dict(spk=spk, cond=f"hybrid:{hiss_c}hiss_in_{ctx_c}word", truth=hiss_c, context=ctx_c, pred=verdict(m),
                             **{f"m_{g}": m[g] for g in G}))
    print(f"  {spk}: hybrids done ({len(rows)} clips, {time.time() - t_start:.0f}s)", flush=True)
pd.DataFrame(rows).to_pickle(OUT)
print("wrote", OUT, len(rows))
