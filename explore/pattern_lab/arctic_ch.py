"""CMU ARCTIC (bdl male, slt female; festvox labels): how /tʃ/ ('ch') differs from /ʃ/ ('sh') and /t/ in the high band (2.5-7.9 kHz)."""
import glob, os, sys
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, welch

ROOT = r"C:\Users\tuank\Data\arctic_festvox"
FS = 16000
SOS = butter(4, [2500, 7900], btype="band", fs=FS, output="sos")
PH = {"ch", "sh", "t", "jh"}


def labels(path):
    out, prev = [], 0.0
    for line in open(path):
        p = line.split()
        if len(p) == 3 and p[0] != "#":
            end = float(p[0]); out.append((prev, end, p[2])); prev = end
    return out


def measures(x):
    y = sosfilt(SOS, x)
    win, hop = int(0.005 * FS), int(0.001 * FS)
    if len(y) < win + hop: return None
    amp = np.array([np.sqrt(np.mean(y[i:i + win] ** 2)) for i in range(0, len(y) - win, hop)])
    mx = amp.max()
    if mx < 1e-4: return None
    t10 = int(np.argmax(amp >= 0.1 * mx))
    t90 = t10 + int(np.argmax(amp[t10:] >= 0.9 * mx))
    last = len(amp) - 1 - int(np.argmax(amp[::-1] >= 0.1 * mx))
    db = 20 * np.log10(amp + 1e-9)
    slope = float(np.max(np.diff(db[max(0, t10 - 2):t90 + 3]))) if t90 + 3 > t10 else np.nan
    seg = x[t10 * hop:(last + 1) * hop + win]
    cog = np.nan
    if len(seg) > 128:
        f, p = welch(seg, FS, nperseg=min(256, len(seg)))
        m = (f >= 1000) & (f <= 8000)
        cog = float((f[m] * p[m]).sum() / p[m].sum())
    return dict(closure_ms=t10, rise_ms=t90 - t10, hiss_ms=last - t10 + 1, slope_db_ms=slope, cog_hz=cog, peak_db=20 * np.log10(mx + 1e-9))


rows = []
for spk in ("bdl", "slt"):
    for lab in sorted(glob.glob(f"{ROOT}/cmu_us_{spk}_arctic/lab/arctic_*.lab")):
        base = os.path.basename(lab)[:-4]
        segs = labels(lab)
        wav = f"{ROOT}/cmu_us_{spk}_arctic/wav/{base}.wav"
        if not any(s[2] in PH for s in segs): continue
        fs, x = wavfile.read(wav); x = x.astype(float) / 32768
        for i, (a, b, ph) in enumerate(segs):
            if ph not in PH or b - a < 0.02: continue
            m = measures(x[int(a * FS):int(b * FS)])
            if m: rows.append(dict(spk=spk, phone=ph, dur_ms=(b - a) * 1000, nxt=segs[i + 1][2] if i + 1 < len(segs) else "", **m))
df = pd.DataFrame(rows)
df.to_pickle(os.path.join(os.path.dirname(__file__), "arctic_ch.pkl"))
pd.set_option("display.width", 200)
cols = ["dur_ms", "closure_ms", "rise_ms", "hiss_ms", "slope_db_ms", "cog_hz"]
print(df.groupby(["spk", "phone"]).size().unstack())
for spk in ("bdl", "slt"):
    print(f"\n== {spk}: median [25th-75th percentile]")
    for ph in ("ch", "sh", "t", "jh"):
        d = df[(df.spk == spk) & (df.phone == ph)]
        if len(d):
            print(ph.ljust(3), f"n={len(d):3d} ", "  ".join(f"{c}={d[c].median():.1f} [{d[c].quantile(.25):.1f}-{d[c].quantile(.75):.1f}]" for c in cols))
