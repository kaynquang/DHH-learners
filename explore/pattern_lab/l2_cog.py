"""CoG (app measurement) of word-initial /s/ and /ʃ/ in L2-ARCTIC, for the population-shift figure. python l2_cog.py <wav> <textgrid root> <out.pkl>"""
import sys, re, glob, os
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
import numpy as np, pandas as pd, parselmouth
from fricative.measure import measure
from fricative.segment import SegmentationError, find_boundaries
WAV, TG, OUT = sys.argv[1:4]
V = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name: return [(float(a), float(b), x.strip()) for a, b, x in re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []
rows = []
for tg in sorted(glob.glob(f"{TG}/*/annotation/arctic_*.TextGrid")):
    spk, base = tg.split("/")[-3], os.path.basename(tg)[:-9]; w = f"{WAV}/{spk}/wav/{base}.wav"
    if not os.path.exists(w): continue
    txt = open(tg, encoding="utf-8", errors="replace").read(); ph, wd = tier(txt, "phones"), tier(txt, "words"); starts = {round(a, 2) for a, b, x in wd if x}
    snd = parselmouth.Sound(w); snd = snd.resample(16000, 50) if round(snd.sampling_frequency) != 16000 else snd; x = snd.values[0]
    for i, (a, b, l) in enumerate(ph):
        p = l.split(","); cpl = re.sub(r"[\d*]", "", p[0]).upper()
        if cpl not in ("S", "SH") or round(a, 2) not in starts or i + 1 >= len(ph) or re.sub(r"[\d*]", "", ph[i + 1][2].split(",")[0]).upper() not in V: continue
        vb = ph[i + 1][1]
        clip = parselmouth.Sound(np.concatenate([np.zeros(3200), x[int(a * 16000):int(vb * 16000)], np.zeros(1600)]) + np.random.default_rng(0).normal(0, 1e-4, 4800 + int(vb * 16000) - int(a * 16000)), sampling_frequency=16000)
        try: b2 = find_boundaries(clip); m = measure(clip, b2.onset_s, b2.offset_s, b2.found_vowel)
        except SegmentationError: continue
        rows.append(dict(spk=spk, phone=cpl, error=len(p) > 2 and p[2].strip() == "s", cog=m.cog_hz))
pd.DataFrame(rows).to_pickle(OUT); print("done", len(rows))
