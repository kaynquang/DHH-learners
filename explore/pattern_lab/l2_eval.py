"""Run the app's scorers on L2-ARCTIC word-initial target sounds and compare with the human annotation.
python l2_eval.py <wav_root> <textgrid_root> <out.pkl>
Annotation: phone text 'CPL,PPL,s' = the canonical phone CPL was heard as PPL (substitution); 'CPL,sil,d' / ',d' = deletion; no comma = correct.
Token = target phone to end of the next vowel, 0.2 s of silence in front (like an isolated word)."""
import sys, re, glob, os, pickle
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
import numpy as np, pandas as pd, parselmouth
from fricative import config as C, phoneme_check as pc
from fricative.audio import load
from fricative.classify import classify
from fricative.measure import measure
from fricative.segment import SegmentationError, find_boundaries
from fricative.stops import classify_stop, measure_vot
WAV, TG, OUT = sys.argv[1:4]
TARGET = {"S": "s", "SH": "sh", "F": "f", "CH": "tʃ", "M": "m", "N": "n", "B": "b", "P": "p"}
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}

def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name:
            return [(float(a), float(b), x.strip()) for a, b, x in re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []
def split(label):
    p = label.split(",")
    return (re.sub(r"[\d*]", "", p[0]).upper(), p[1].upper() if len(p) > 1 else None, p[2] if len(p) > 2 else None)

rows = []
for tg in sorted(glob.glob(f"{TG}/*/annotation/arctic_*.TextGrid")):
    spk, base = tg.split("/")[-3], os.path.basename(tg)[:-9]
    wav = f"{WAV}/{spk}/wav/{base}.wav"
    if not os.path.exists(wav): continue
    txt = open(tg, encoding="utf-8", errors="replace").read(); ph, wd = tier(txt, "phones"), tier(txt, "words")
    starts = {round(a, 2) for a, b, w in wd if w}
    idx = [i for i, (a, b, l) in enumerate(ph) if round(a, 2) in starts and split(l)[0] in TARGET and i + 1 < len(ph)
           and split(ph[i + 1][2])[0] in VOWELS]
    if not idx: continue
    snd = load(wav) if False else parselmouth.Sound(wav)
    if round(snd.sampling_frequency) != 16000: snd = snd.resample(16000, 50)
    x = snd.values[0]
    for i in idx:
        a, b, l = ph[i]; cpl, ppl, kind = split(l); va, vb, _ = ph[i + 1]
        if vb - va < 0.05 or b - a < 0.02: continue
        clip = np.concatenate([np.zeros(3200), x[int(a * 16000):int(vb * 16000)], np.zeros(1600)]) + np.random.default_rng(0).normal(0, 1e-4, 4800 + int(vb * 16000) - int(a * 16000))
        s = parselmouth.Sound(clip, sampling_frequency=16000); t = TARGET[cpl]
        r = dict(spk=spk, phone=cpl, ppl=ppl, kind=kind, error=kind == "s", deleted=kind == "d", file=base, t=a)
        try:
            if cpl in ("S", "SH", "F"):
                bd = find_boundaries(s); v = classify(measure(s, bd.onset_s, bd.offset_s, bd.found_vowel), t); r.update(color=v.color, heard=v.heard)
                r["w2v_hiss"] = pc.check(s, bd.onset_s, bd.offset_s).heard if pc.available() else None
            elif cpl in ("B", "P"):
                v = classify_stop(measure_vot(s), t); r.update(color=v.color, heard=v.heard)
            elif cpl in ("M", "N") and pc.available():
                from fricative.nasals import classify_nasal
                v = classify_nasal(pc.nasal_reading(s)[0], t)
                if v: r.update(color=v.color, heard=v.heard)
            elif cpl == "CH" and pc.available():
                bd = find_boundaries(s); p = pc.probability_ch(s, bd.onset_s, bd.offset_s)
                from fricative.affricate import classify_affricate
                v = classify_affricate(p); r.update(color=v.color, heard=v.heard)
            if pc.available(): r["first"] = pc.first_consonant(s)
        except SegmentationError:
            r["color"] = "fail"
        rows.append(r)
    if len(rows) % 200 < len(idx): print(spk, len(rows), flush=True)
pickle.dump(pd.DataFrame(rows), open(OUT, "wb")); print("done", len(rows))
