"""Exploration only: per-token spectral features for fricatives from ARCTIC (bdl, slt)."""
import sys, re, glob, os, pickle
import numpy as np, pandas as pd, parselmouth
from parselmouth.praat import call
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
from fricative.measure import measure, spectrum_db

S = sys.argv[1]
SPEAKERS = {"aew": ("male", 5000.0), "bdl": ("male", 5000.0), "rms": ("male", 5000.0),
            "clb": ("female", 5500.0), "eey": ("female", 5500.0), "ljm": ("female", 5500.0), "lnh": ("female", 5500.0),
            "slt": ("female", 5500.0)}
if len(sys.argv) > 2:                      # optional: python extract_tokens.py <S> bdl,slt
    SPEAKERS = {k: v for k, v in SPEAKERS.items() if k in sys.argv[2].split(",")}
PHONES = {"S", "SH", "F", "TH", "Z"}
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
GRID = np.arange(0, 8000, 200)

def phones_tier(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', t, flags=re.S):
        if m.group(2).lower() == "phones":
            return [(float(a), float(b), re.sub(r"\d", "", x)) for a, b, x in
                    re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []

def band_db(f, db):
    p = 10 ** (db / 10)
    out = np.array([10 * np.log10(p[(f >= lo) & (f < lo + 200)].mean() + 1e-20) if ((f >= lo) & (f < lo + 200)).any() else np.nan for lo in GRID])
    ok = ~np.isnan(out)
    return np.interp(GRID, GRID[ok], out[ok])

rows, skipped = [], {}
for spk, (sex, fmax) in SPEAKERS.items():
    for tg in sorted(glob.glob(f"{S}/x_arctic/tg/{spk}/arctic_a*.TextGrid"))[:300]:
        base = os.path.basename(tg).replace(".TextGrid", "")
        wav = f"{S}/wav_{spk}/{base}.wav"
        if not os.path.exists(wav): continue
        snd = parselmouth.Sound(wav)
        ph = phones_tier(tg)
        formant = snd.to_formant_burg(0.005, 5, fmax, 0.025, 50)
        for i, (a, b, lab) in enumerate(ph):
            if lab not in PHONES: continue
            d = b - a
            if d < 0.030:
                skipped[(spk, lab)] = skipped.get((spk, lab), 0) + 1; continue
            nxt = ph[i + 1][2] if i + 1 < len(ph) and ph[i + 1][2] else "sil"
            prv = ph[i - 1][2] if i > 0 and ph[i - 1][2] else "sil"
            m = measure(snd, a, b, has_vowel=True)
            ma, mb = a + d / 4, b - d / 4
            part = call(snd, "Extract part", ma, mb, "rectangular", 1, "no")
            sp = part.to_spectrum()
            f, db = spectrum_db(snd, ma, mb, fmax=8000)
            P = 10 ** (db / 10); tot = P.sum()
            frac = lambda lo, hi: float(P[(f >= lo) & (f < hi)].sum() / tot)
            traj = [np.nan] * 5
            if d >= 0.060:
                traj = [float(call(call(snd, "Extract part", a + k * d / 5, a + (k + 1) * d / 5, "rectangular", 1, "no").to_spectrum(), "Get centre of gravity", 2)) for k in range(5)]
            f2 = [np.nan] * 7; f2mid = np.nan
            if nxt in VOWELS and i + 1 < len(ph) and ph[i + 1][1] - ph[i + 1][0] >= 0.08:
                dv = ph[i + 1][1] - ph[i + 1][0]
                f2 = [formant.get_value_at_time(2, b + k * 0.01) for k in range(7)]
                f2mid = formant.get_value_at_time(2, b + dv / 2)
            rows.append(dict(spk=spk, sex=sex, file=base, phone=lab, nxt=nxt, prv=prv, start=a, end=b, dur_ms=d * 1000,
                             cog=m.cog_hz, relamp=m.relamp_db, fm=m.fm_hz,
                             sd=float(call(sp, "Get standard deviation", 2)), skew=float(call(sp, "Get skewness", 2)),
                             kurt=float(call(sp, "Get kurtosis", 2)),
                             e2_4=frac(2000, 4000), e4_6=frac(4000, 6000), e6_8=frac(6000, 8000), e0_2=frac(0, 2000),
                             shape=band_db(f, db), traj=np.array(traj), f2=np.array(f2), f2mid=f2mid))
df = pd.DataFrame(rows)
pickle.dump(df, open(f"{S}/tokens.pkl", "wb"))
print(df.groupby(["spk", "phone"]).size().unstack().to_string())
print("skipped (<30 ms):", skipped)
print("with trajectory:", int(df.traj.apply(lambda x: not np.isnan(x[0])).sum()), "| with F2:", int(df.f2.apply(lambda x: not np.isnan(x[1])).sum()))
