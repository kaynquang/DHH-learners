"""Linear probe on wav2vec2 hidden states of the consonant alone (no word context) for hard pairs, leave-one-voice-out.
python w2v_probe.py <S> <checkpoint dir> <out.pkl> [per_class_per_voice=60]
Tokens: ARCTIC phones S SH F TH CH P B M N, word-initial and before a vowel, >= 40 ms. Clip = the phone itself ('alone') or with 80 ms
of the preceding and 150 ms of the following sound ('context')."""
import sys, re, glob, os, pickle
import numpy as np, pandas as pd, parselmouth, torch
from transformers import Wav2Vec2Model

S, CKPT, OUT = sys.argv[1:4]; PER = int(sys.argv[4]) if len(sys.argv) > 4 else 60
SPK = ["aew", "bdl", "clb", "eey", "ljm", "lnh", "rms", "slt"]
WANT = {"S", "SH", "F", "TH", "CH", "P", "B", "M", "N"}
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
LAYERS = (4, 8, 12, 16, 20, 24)
model = Wav2Vec2Model.from_pretrained(CKPT).eval()
nl = model.config.num_hidden_layers; LAYERS = tuple(l for l in LAYERS if l <= nl) or (nl,)

def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name:
            return [(float(a), float(b), re.sub(r"\d", "", x)) for a, b, x in re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []

def embed(x):
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad():
        hs = model(torch.tensor(x, dtype=torch.float32)[None], output_hidden_states=True).hidden_states
    return {l: hs[l][0].mean(0).numpy() for l in LAYERS}, hs

rows, rng = [], np.random.default_rng(0)
for spk in SPK:
    cand = []
    for tg in sorted(glob.glob(f"{S}/x_arctic/tg/{spk}/arctic_a*.TextGrid")):
        base = os.path.basename(tg)[:-9]
        if not os.path.exists(f"{S}/wav_{spk}/{base}.wav"): continue
        txt = open(tg, encoding="utf-8", errors="replace").read(); ph, wd = tier(txt, "phones"), tier(txt, "words")
        starts = {round(a, 3) for a, b, w in wd if w}
        for i, (a, b, l) in enumerate(ph):
            if l in WANT and round(a, 3) in starts and b - a >= 0.04 and i + 1 < len(ph) and ph[i + 1][2] in VOWELS:
                cand.append((base, a, b, l, ph[i + 1][1] - ph[i + 1][0]))
    by = {}
    for c in cand: by.setdefault(c[3], []).append(c)
    for lab, lst in by.items():
        for k in rng.permutation(len(lst))[:PER]:
            base, a, b, l, vd = lst[k]
            x = parselmouth.Sound(f"{S}/wav_{spk}/{base}.wav").values[0].astype(np.float64)
            fs = 16000
            alone = x[int(a * fs):int(b * fs)]
            ctx = x[int(max(a - 0.08, 0) * fs):int((b + min(vd, 0.15)) * fs)]
            ea, _ = embed(alone); ec, _ = embed(ctx)
            rows.append(dict(spk=spk, phone=l, dur=(b - a) * 1000, **{f"alone_{L}": ea[L] for L in LAYERS}, **{f"ctx_{L}": ec[L] for L in LAYERS}))
    print(spk, len(rows), flush=True)
pickle.dump(pd.DataFrame(rows), open(OUT, "wb"))
