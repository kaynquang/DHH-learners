"""Exploration: end-to-end candidate measures for /m/-/n/ and /tʃ/-/ʃ/ on isolated-like clips (0.2 s of silence + token + 0.1 s).
python nasal_affricate.py <S> <other.pkl> <out.pkl>"""
import sys, pickle
import numpy as np, pandas as pd, parselmouth
from scipy.signal import butter, sosfilt
S, PKL, OUT = sys.argv[1:4]
df = pickle.load(open(PKL, "rb")); df = df[df.phone.isin(["M", "N", "CH", "SH"])]
rows = []
for r in df.itertuples():
    snd = parselmouth.Sound(f"{S}/wav_{r.spk}/{r.file}.wav")
    c = snd.extract_part(r.start, r.end + r.vowel_ms / 1000, parselmouth.WindowShape.RECTANGULAR, 1, False).values[0]
    pad = 0.2; x = np.concatenate([np.zeros(int(pad * 16000)), c, np.zeros(int(0.1 * 16000))]) + np.random.default_rng(0).normal(0, 1e-4, int((pad + 0.1) * 16000) + len(c))
    clip = parselmouth.Sound(x, sampling_frequency=16000)
    d = dict(spk=r.spk, phone=r.phone, true_end=pad + (r.end - r.start))
    if r.phone in ("M", "N"):
        pitch = clip.to_pitch(0.002, 75, 500); inten = clip.to_intensity(100, 0.002)
        ts = pitch.xs(); v = [t for t in ts if np.isfinite(pitch.get_value_at_time(t) or np.nan)]
        if not v: continue
        v0 = v[0]
        tt = np.arange(v0, clip.xmax - 0.02, 0.002); ii = np.array([inten.get_value(t) for t in tt])
        pk = np.nanmax(ii); k = np.flatnonzero(ii >= pk - 8)
        if not len(k): continue
        vo = float(tt[k[0]])
        fm = clip.to_formant_burg(0.005, 5, 5250, 0.025, 50)
        for j, ms in enumerate(range(0, 90, 10)):
            d[f"f2_{ms}"] = fm.get_value_at_time(2, vo + ms / 1000); d[f"f1_{ms}"] = fm.get_value_at_time(1, vo + ms / 1000)
            d[f"f3_{ms}"] = fm.get_value_at_time(3, vo + ms / 1000)
        d.update(nasal_end=vo, murmur_ms=(vo - v0) * 1000, end_err_ms=(vo - d["true_end"]) * 1000)
    else:
        sos = butter(4, [2500, 7900], btype="band", fs=16000, output="sos"); y = sosfilt(sos, x)
        n, hop = 80, 32; st = np.arange(0, len(y) - n, hop)
        db = np.array([10 * np.log10(np.mean(y[s:s + n] ** 2) + 1e-12) for s in st]); t = (st + n / 2) / 16000
        hot = np.flatnonzero(db > np.percentile(db, 5) + 15)
        if len(hot) < 5: continue
        on = hot[0]; amp = 10 ** (db / 20); seg = amp[on:on + 60]; pk = seg.max()
        d["rise_ms"] = (np.argmax(seg >= 0.9 * pk) - np.argmax(seg >= 0.1 * pk)) * 2
        d["rise_db_per_ms"] = float(np.max(db[on + 2:on + 30] - db[on:on + 28]) / 4) if len(db) > on + 30 else np.nan
        d["early_peak_db"] = db[on:on + 10].max() - db[on + 15:on + 40].mean() if len(db) > on + 40 else np.nan
        d["hiss_ms"] = (hot[-1] - hot[0]) * 2
    rows.append(d)
o = pd.DataFrame(rows); pickle.dump(o, open(OUT, "wb"))
print(o.groupby("phone").size().to_dict()); print(o[o.phone.isin(["M", "N"])].end_err_ms.describe().round(1).to_dict())
