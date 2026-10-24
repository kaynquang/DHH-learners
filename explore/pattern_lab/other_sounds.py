"""Exploration: candidate measures for the five charter sounds the app does not score yet (m n p b tʃ; ʃ for comparison with tʃ), word-initial before a vowel on ARCTIC (any preceding sound: only ~8 tokens per voice and class follow silence).

python other_sounds.py <S> <out.pkl>      # S as in extract_tokens.py
"""
import sys, re, glob, os, pickle
import numpy as np, pandas as pd, parselmouth
from parselmouth.praat import call

S, OUT = sys.argv[1], sys.argv[2]
SPEAKERS = {"aew": 5000.0, "bdl": 5000.0, "rms": 5000.0, "clb": 5500.0, "eey": 5500.0, "ljm": 5500.0, "lnh": 5500.0, "slt": 5500.0}
WANT = {"M", "N", "P", "B", "CH", "SH"}
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}


def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name:
            return [(float(a), float(b), re.sub(r"\d", "", x)) for a, b, x in
                    re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []


def band_env(snd, lo, hi, a, b, step=0.002):
    part = snd.extract_part(a, b, parselmouth.WindowShape.RECTANGULAR, 1, False)
    filt = call(part, "Filter (pass Hann band)", lo, hi, 100)
    t = np.arange(a + 0.0025, b - 0.0025, step)
    y = np.array([20 * np.log10(call(filt, "Get root-mean-square", tt - 0.0025 - a, tt + 0.0025 - a) + 1e-9) for tt in t])
    return t, y


rows = []
for spk, fmax in SPEAKERS.items():
    for tg in sorted(glob.glob(f"{S}/x_arctic/tg/{spk}/arctic_a*.TextGrid"))[:300]:
        base = os.path.basename(tg).replace(".TextGrid", "")
        wav = f"{S}/wav_{spk}/{base}.wav"
        if not os.path.exists(wav): continue
        txt = open(tg, encoding="utf-8", errors="replace").read()
        ph, words = tier(txt, "phones"), tier(txt, "words")
        starts = {round(a, 3) for a, b, w in words if w}
        cand = [i for i, (a, b, l) in enumerate(ph) if l in WANT and round(a, 3) in starts and i + 1 < len(ph) and ph[i + 1][2] in VOWELS]
        if not cand: continue
        snd = parselmouth.Sound(wav)
        formant = snd.to_formant_burg(0.005, 5, fmax, 0.025, 50)
        pitch = snd.to_pitch(0.002, 75, 500)
        for i in cand:
            a, b, lab = ph[i]; va, vb, _ = ph[i + 1]
            if vb - va < 0.06: continue
            r = dict(spk=spk, file=base, phone=lab, start=a, end=b, dur_ms=(b - a) * 1000, vowel_ms=(vb - va) * 1000)
            # nasals: F2 / F3 at +15 and +30 ms into the vowel, murmur spectrum
            for k in (0.015, 0.030, 0.050):
                r[f"f2_{int(k*1000)}"] = formant.get_value_at_time(2, b + k)
                r[f"f1_{int(k*1000)}"] = formant.get_value_at_time(1, b + k)
                r[f"f3_{int(k*1000)}"] = formant.get_value_at_time(3, b + k)
            r["f2_slope"] = (r["f2_50"] - r["f2_15"]) / 0.035 if np.isfinite(r["f2_50"]) and np.isfinite(r["f2_15"]) else np.nan
            if b - a >= 0.03:
                sp = snd.extract_part(a + (b - a) * 0.25, b - (b - a) * 0.25, parselmouth.WindowShape.RECTANGULAR, 1, False).to_spectrum()
                r["mur_cog"] = float(call(sp, "Get centre of gravity", 2))
                lo = call(sp, "Get band energy", 0, 1000); mid = call(sp, "Get band energy", 1000, 2500); hi = call(sp, "Get band energy", 2500, 5000)
                tot = lo + mid + hi + 1e-30
                r["mur_lo"], r["mur_mid"], r["mur_hi"] = lo / tot, mid / tot, hi / tot
            # stops: burst = largest rise of 1-8 kHz envelope inside the interval; voicing onset = first voiced frame
            if lab in ("P", "B") and b - a >= 0.02:
                t, y = band_env(snd, 1500, 7500, a, min(b + 0.03, vb))
                d = np.diff(y); j = int(np.argmax(d)); burst = t[j + 1]
                v_on = next((tt for tt in np.arange(burst, vb, 0.002) if np.isfinite(pitch.get_value_at_time(tt) or np.nan)), np.nan)
                prev = [tt for tt in np.arange(a, burst, 0.002) if np.isfinite(pitch.get_value_at_time(tt) or np.nan)]
                r.update(burst_s=burst, vot_ms=(v_on - burst) * 1000, prevoice_ms=len(prev) * 2.0, burst_rise_db=float(d[j]),
                         burst_to_vowel_ms=(va - burst) * 1000, closure_ms=(burst - a) * 1000)
            # affricate / fricative rise: time for the 2.5-8 kHz envelope to climb from 10% to 90% of its peak
            if lab in ("CH", "SH") and b - a >= 0.04:
                t, y = band_env(snd, 2500, 7900, a, b)
                amp = 10 ** (y / 20); pk = amp.max()
                t10 = t[np.argmax(amp >= 0.1 * pk)]; t90 = t[np.argmax(amp >= 0.9 * pk)]
                r["rise_ms"] = (t90 - t10) * 1000
            rows.append(r)
    print(spk, len(rows), flush=True)
df = pd.DataFrame(rows)
pickle.dump(df, open(OUT, "wb"))
print(df.groupby(["spk", "phone"]).size().unstack().to_string())
