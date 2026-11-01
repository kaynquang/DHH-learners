"""CMU ARCTIC /tʃ/, /ʃ/ and /t/ tokens that really start after a pause (the label before is "pau"): like the start of an isolated word, without cutting the audio.
The measures are those of app/learner/affricate_check.py (the first hiss of the clip) plus the 10-90 % rise time of the amplitude. The clip runs from 0.25 s before the token to its end,
so that the vowel after it is not in it and the hiss length is the length of the token itself.
python arctic_isolated.py <folder with cmu_us_<speaker>_arctic from festvox.org>   (the folder was C:\\Users\\tuank\\Data\\arctic_festvox)"""
import glob, os, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app"))
from learner.affricate_check import measure, SOS, WIN, HOP   # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tuank\Data\arctic_festvox"
FS = 16000


def labels(path):
    out, prev = [], 0.0
    for line in open(path):
        p = line.split()
        if len(p) == 3 and p[0] != "#":
            out.append((prev, float(p[0]), p[2])); prev = float(p[0])
    return out


def rise_ms(x):
    y = sosfilt(SOS, x)
    amp = np.sqrt(np.convolve(y ** 2, np.ones(WIN) / WIN, mode="valid")[::HOP])
    pk = int(np.argmax(amp)); mx = amp[pk]
    if mx <= 0: return np.nan
    t10 = int(np.argmax(amp[:pk + 1] >= 0.1 * mx)); t90 = int(np.argmax(amp[:pk + 1] >= 0.9 * mx))
    return float(t90 - t10)


rows = []
for spk in ("bdl", "slt"):
    for lab in sorted(glob.glob(f"{ROOT}/cmu_us_{spk}_arctic/lab/arctic_*.lab")):
        segs = labels(lab)
        wav = None
        for i, (a, b, ph) in enumerate(segs):
            if ph in ("ch", "sh", "t") and i > 0 and segs[i - 1][2] == "pau" and segs[i - 1][1] - segs[i - 1][0] >= 0.1 and b - a >= 0.03:
                if wav is None:
                    fs, wav = wavfile.read(f"{ROOT}/cmu_us_{spk}_arctic/wav/{os.path.basename(lab)[:-4]}.wav"); wav = wav.astype(float) / 32768
                clip = wav[max(0, int((a - 0.25) * FS)):int(b * FS)]
                m = measure(clip, FS)
                if m: rows.append(dict(spk=spk, ph=ph, slope=m[0], hiss=m[1], rise=rise_ms(clip)))
import pandas as pd
df = pd.DataFrame(rows)
print(df.groupby(["spk", "ph"]).size().unstack())
pd.set_option("display.width", 200)
for spk in ("bdl", "slt"):
    for ph in ("ch", "sh", "t"):
        d = df[(df.spk == spk) & (df.ph == ph)]
        if len(d):
            print(spk, ph.ljust(2), f"n={len(d):3d}", "  ".join(f"{c} {d[c].median():.1f} [{d[c].quantile(.25):.1f}-{d[c].quantile(.75):.1f}]" for c in ("slope", "rise", "hiss")))
print(df.groupby("ph")[["slope", "rise", "hiss"]].describe().T.to_string())
