"""The centre of gravity as the live dot of the learner app computes it (method A), on CMU ARCTIC /s/ and /ʃ/, to set the zones of the dot.

The dot (app/learner/mic.py, startDot) reads the browser's AnalyserNode: a Blackman window of 2048 samples at 48 kHz (43 ms), the magnitudes smoothed in time (smoothingTimeConstant 0.5),
one frame per screen frame (about 16.7 ms), and the centre of gravity of the magnitudes (not of the power) between F_LO and F_HI, smoothed again (0.6 old + 0.4 new). ARCTIC is 16 kHz, so it is
resampled to 48 kHz and the band stops at 8 kHz (F_HI = 8000 in learner/spectro.py). The scoring pipeline's measure (Praat, power 2, whole spectrum, method B) is computed on the same tokens for comparison.
python arctic_dot_cog.py <folder with cmu_us_<speaker>_arctic from festvox.org> [speakers, comma separated]
Writes dot_cog.pkl next to this file.
"""
import glob, os, sys
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample_poly

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app"))
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tuank\Data\arctic_festvox"
SPEAKERS = (sys.argv[2] if len(sys.argv) > 2 else "bdl,slt,rms,clb").split(",")
SEX = {"bdl": "male", "rms": "male", "slt": "female", "clb": "female"}
FS, N, HOP = 48000, 2048, 800
F_LO, F_HI = 1000.0, 8000.0
WIN = np.blackman(N)                                       # the AnalyserNode's window (alpha 0.16)
BIN_HZ = FS / N
LO_BIN, HI_BIN = int(np.ceil(F_LO / BIN_HZ)), int(np.floor(F_HI / BIN_HZ))
FREQ = np.arange(HI_BIN + 1) * BIN_HZ


def labels(path):
    out, prev = [], 0.0
    for line in open(path):
        p = line.split()
        if len(p) == 3 and p[0] != "#":
            out.append((prev, float(p[0]), p[2])); prev = float(p[0])
    return out


def dot_cog(x48: np.ndarray, start: int, stop: int):
    """The dot's centre of gravity for the frames that end between start and stop (samples), the way the browser computes it."""
    smooth = np.zeros(N // 2); f = None; out = []
    for end in range(N, len(x48), HOP):
        mag = np.abs(np.fft.rfft(x48[end - N:end] * WIN))[:N // 2] / N
        smooth = 0.5 * smooth + 0.5 * mag                    # smoothingTimeConstant 0.5
        if start <= end <= stop:
            w = smooth[LO_BIN:HI_BIN + 1]
            if w.sum() > 0:
                c = float((w * FREQ[LO_BIN:HI_BIN + 1]).sum() / w.sum())
                f = c if f is None else 0.6 * f + 0.4 * c
                out.append(f)
    return out


if __name__ == "__main__":
    import parselmouth
    from fricative.measure import measure
    rows = []
    for spk in SPEAKERS:
        for lab in sorted(glob.glob(f"{ROOT}/cmu_us_{spk}_arctic/lab/arctic_*.lab")):
            segs = labels(lab)
            if not any(s[2] in ("s", "sh") for s in segs): continue
            fs, x = wavfile.read(lab.replace("lab", "wav").replace(".lab", ".wav")); x = x.astype(float) / 32768
            x48 = resample_poly(x, 3, 1)
            snd = parselmouth.Sound(x, fs)
            for i, (a, b, ph) in enumerate(segs):
                if ph not in ("s", "sh") or b - a < 0.08: continue
                # the middle 60 % of the token: the edges are the neighbours' transitions
                a2, b2 = a + 0.2 * (b - a), b - 0.2 * (b - a)
                frames = dot_cog(x48, int(a2 * FS), int(b2 * FS))
                if len(frames) < 2: continue
                try:
                    cog_b = measure(snd, a, b, True).cog_hz
                except Exception:
                    cog_b = np.nan
                rows.append(dict(spk=spk, sex=SEX.get(spk, "?"), phone=ph, dur=b - a, cog_a=float(np.median(frames)), cog_b=cog_b))
    df = pd.DataFrame(rows)
    df.to_pickle(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dot_cog.pkl"))
    pd.set_option("display.width", 200)
    print(df.groupby(["spk", "phone"]).agg(n=("cog_a", "size"), a_p25=("cog_a", lambda s: s.quantile(.25)), a_med=("cog_a", "median"), a_p75=("cog_a", lambda s: s.quantile(.75)),
                                           b_med=("cog_b", "median")).round(0).to_string())
