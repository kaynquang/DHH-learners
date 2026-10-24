"""End-to-end /tʃ/ vs /ʃ/: segment with the app's find_boundaries on a clip with 0.2 s of lead-in, embed that segment with wav2vec2 layer 8, probe LOVO.
python ch_probe_e2e.py <S> <ckpt> <out.pkl>"""
import sys, pickle
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
import numpy as np, pandas as pd, parselmouth, torch
from transformers import Wav2Vec2Model
from fricative.segment import find_boundaries, SegmentationError
S, CKPT, OUT = sys.argv[1:4]; LAYER = 8
model = Wav2Vec2Model.from_pretrained(CKPT).eval()
df = pickle.load(open(f"{S}/other.pkl", "rb")); df = df[df.phone.isin(["CH", "SH"])]
rows = []
for r in df.itertuples():
    c = parselmouth.Sound(f"{S}/wav_{r.spk}/{r.file}.wav").extract_part(r.start, r.end + r.vowel_ms / 1000, parselmouth.WindowShape.RECTANGULAR, 1, False).values[0]
    x = np.concatenate([np.zeros(3200), c, np.zeros(1600)]) + np.random.default_rng(0).normal(0, 1e-4, 4800 + len(c))
    snd = parselmouth.Sound(x, sampling_frequency=16000)
    try: b = find_boundaries(snd)
    except SegmentationError: continue
    seg = x[int(b.onset_s * 16000):int(b.offset_s * 16000)]
    if len(seg) < 640: continue
    seg = (seg - seg.mean()) / (seg.std() + 1e-7)
    with torch.no_grad(): h = model(torch.tensor(seg, dtype=torch.float32)[None], output_hidden_states=True).hidden_states[LAYER][0].mean(0).numpy()
    rows.append(dict(spk=r.spk, phone=r.phone, emb=h))
pickle.dump(pd.DataFrame(rows), open(OUT, "wb")); print(len(rows), "of", len(df))
