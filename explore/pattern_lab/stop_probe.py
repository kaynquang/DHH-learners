"""wav2vec2 probe for /p/ vs /b/ on the burst-to-voicing stretch (+40 ms). Train on ARCTIC (native), test on L2-ARCTIC (annotated errors).
python stop_probe.py <ARCTIC S> <other.pkl> <L2 wav> <L2 textgrid root> <ckpt> <out.pkl>"""
import sys, re, glob, os, pickle
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
import numpy as np, pandas as pd, parselmouth, torch
from transformers import Wav2Vec2Model
from fricative.segment import SegmentationError
from fricative.stops import measure_vot
S, PKL, L2W, L2T, CK, OUT = sys.argv[1:7]
model = Wav2Vec2Model.from_pretrained(CK).eval()
def emb(clip):
    try: m = measure_vot(clip)
    except SegmentationError: return None, None
    a, b = max(m.burst_s - 0.01, 0), m.voicing_s + 0.04
    x = clip.values[0][int(a * 16000):int(b * 16000)].astype(np.float64)
    if len(x) < 800: return None, None
    x = (x - x.mean()) / (x.std() + 1e-7)
    with torch.no_grad(): h = model(torch.tensor(x, dtype=torch.float32)[None], output_hidden_states=True).hidden_states[8][0].mean(0).numpy()
    return h, m.vot_ms
def pad(x): return parselmouth.Sound(np.concatenate([np.zeros(3200), x, np.zeros(1600)]) + np.random.default_rng(0).normal(0, 1e-4, 4800 + len(x)), sampling_frequency=16000)
rows = []
df = pickle.load(open(PKL, "rb")); df = df[df.phone.isin(["P", "B"])]
for r in df.itertuples():
    c = parselmouth.Sound(f"{S}/wav_{r.spk}/{r.file}.wav").extract_part(r.start, r.end + r.vowel_ms / 1000, parselmouth.WindowShape.RECTANGULAR, 1, False).values[0]
    h, vot = emb(pad(c))
    if h is not None: rows.append(dict(set="arctic", spk=r.spk, phone=r.phone, error=False, vot=vot, emb=h))
print("arctic", len(rows), flush=True)
def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name: return [(float(a), float(b), x.strip()) for a, b, x in re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []
V = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
for tg in sorted(glob.glob(f"{L2T}/*/annotation/arctic_*.TextGrid")):
    spk, base = tg.split("/")[-3], os.path.basename(tg)[:-9]; w = f"{L2W}/{spk}/wav/{base}.wav"
    if not os.path.exists(w): continue
    txt = open(tg, encoding="utf-8", errors="replace").read(); ph, wd = tier(txt, "phones"), tier(txt, "words"); starts = {round(a, 2) for a, b, x in wd if x}
    snd = parselmouth.Sound(w); snd = snd.resample(16000, 50) if round(snd.sampling_frequency) != 16000 else snd; x = snd.values[0]
    for i, (a, b, l) in enumerate(ph):
        p = l.split(","); cpl = re.sub(r"[\d*]", "", p[0]).upper()
        if cpl not in ("P", "B") or round(a, 2) not in starts or i + 1 >= len(ph) or re.sub(r"[\d*]", "", ph[i + 1][2].split(",")[0]).upper() not in V: continue
        vb = ph[i + 1][1]
        if vb - ph[i + 1][0] < 0.05: continue
        h, vot = emb(pad(x[int(a * 16000):int(vb * 16000)]))
        if h is not None: rows.append(dict(set="l2", spk=spk, phone=cpl, error=len(p) > 2 and p[2].strip() == "s", vot=vot, emb=h))
pickle.dump(pd.DataFrame(rows), open(OUT, "wb")); print("done", len(rows))
