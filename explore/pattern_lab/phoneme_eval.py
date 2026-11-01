"""Run the phone recogniser on word-initial fricatives cut from ARCTIC sentences (a stand-in for isolated words).

usage: W2V_DIR=<model folder> python phoneme_eval.py <folder with x_arctic and wav_*> <out.pkl> [per_class_per_voice] [pad_s]
"""
import os, re, sys, time, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, parselmouth
import w2v_phones as W

S, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 80
PAD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.08
CLASSES = {"S": "S", "SH": "SH", "F": "F", "TH": "TH"}
rng = np.random.default_rng(0)

def tiers(path):
    t = open(path, encoding="utf-8", errors="replace").read(); out = {}
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', t, flags=re.S):
        out[m.group(2).lower()] = [(float(a), float(b), re.sub(r"\d", "", x)) for a, b, x in
                                   re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return out

voices = sorted(d[4:] for d in os.listdir(S) if d.startswith("wav_") and os.path.isdir(f"{S}/{d}") and len(os.listdir(f"{S}/{d}")) >= 290)
print("voices:", voices, "| per class per voice:", N, "| pad:", PAD)
rows, t0 = [], time.time()
for spk in voices:
    cand = {c: [] for c in CLASSES}
    for tg in sorted(os.listdir(f"{S}/x_arctic/tg/{spk}"))[:300]:
        base = tg.replace(".TextGrid", "")
        if not os.path.exists(f"{S}/wav_{spk}/{base}.wav"): continue
        T = tiers(f"{S}/x_arctic/tg/{spk}/{tg}")
        if "words" not in T or "phones" not in T: continue
        for ws, we, word in T["words"]:
            if not word: continue
            ph = next(((a, b, l) for a, b, l in T["phones"] if abs(a - ws) < 0.002 and l), None)
            if ph and ph[2] in CLASSES and ph[1] - ph[0] >= 0.03:
                cand[ph[2]].append((base, word, ws, we, ph[0], ph[1]))
    for c, lst in cand.items():
        idx = rng.permutation(len(lst))[:N]
        for k in idx:
            base, word, ws, we, a, b = lst[k]
            snd = parselmouth.Sound(f"{S}/wav_{spk}/{base}.wav")
            c0, c1 = max(0.0, ws - PAD), min(snd.xmax, we + PAD)
            x = snd.values[0][int(c0 * 16000):int(c1 * 16000)]
            post = W.posteriors(x)
            m = W.group_mass(post, a - c0, b - c0)
            rows.append(dict(spk=spk, file=base, word=word, phone=c, start=a, end=b, clip0=c0, decoded=W.greedy(post),
                             **{f"m_{g}": v for g, v in m.items()}))
        print(f"  {spk} {c}: {len(idx)} of {len(lst)} words  ({len(rows)} clips, {time.time() - t0:.0f}s)", flush=True)
df = pd.DataFrame(rows)
pickle.dump(df, open(OUT, "wb"))
print("wrote", OUT, len(df))
