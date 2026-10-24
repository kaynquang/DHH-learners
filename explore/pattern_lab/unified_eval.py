"""One protocol for every sound: the FINAL app pipeline on word-initial consonants of native (ARCTIC sentences 301+, never used for training) and
learner (L2-ARCTIC, annotated) speech, same extraction rules, same padding, same app boundaries, same metrics.
python unified_eval.py <corpus: arctic|l2> <wav root> <textgrid root> <out.pkl>
arctic: wav root = scratchpad (wav_<spk>/), textgrid root = scratchpad/x_arctic/tg ; l2: wav root = l2/wav, textgrid root = l2/tg/textgrids_l2arctic"""
import sys, re, glob, os
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
import numpy as np, pandas as pd, parselmouth
from fricative import config as C, phoneme_check as pc
from fricative.affricate import classify_affricate
from fricative.classify import classify
from fricative.measure import measure
from fricative.nasals import classify_nasal
from fricative.segment import SegmentationError, find_boundaries
from fricative.stops import classify_stop_probe, measure_vot
CORPUS, WAV, TG, OUT = sys.argv[1:5]
T = {"S": "s", "SH": "sh", "F": "f", "CH": "tʃ", "M": "m", "N": "n", "B": "b", "P": "p"}
V = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
def tier(text, name):
    for m in re.finditer(r'item \[\d+\]:\s*class = "(\w+)"\s*name = "([^"]*)"(.*?)(?=item \[\d+\]:|\Z)', text, flags=re.S):
        if m.group(2).lower() == name: return [(float(a), float(b), x.strip()) for a, b, x in re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', m.group(3))]
    return []
def clean(l): return re.sub(r"[\d*]", "", l.split(",")[0]).upper()
if CORPUS == "arctic":
    files = []
    for spk in ["aew","bdl","clb","eey","ljm","lnh","rms","slt"]:
        allf = sorted(glob.glob(f"{TG}/{spk}/arctic_a*.TextGrid"))
        files += [(spk, f, f"{WAV}/wav_{spk}/{os.path.basename(f)[:-9]}.wav") for f in allf[300:]]
else:
    files = [(f.split("/")[-3], f, f"{WAV}/{f.split('/')[-3]}/wav/{os.path.basename(f)[:-9]}.wav") for f in sorted(glob.glob(f"{TG}/*/annotation/arctic_*.TextGrid"))]
rows = []
for spk, tg, wav in files:
    if not os.path.exists(wav): continue
    txt = open(tg, encoding="utf-8", errors="replace").read(); ph, wd = tier(txt, "phones"), tier(txt, "words"); starts = {round(a, 2) for a, b, x in wd if x}
    idx = [i for i, (a, b, l) in enumerate(ph) if round(a, 2) in starts and clean(l) in T and i + 1 < len(ph) and clean(ph[i + 1][2]) in V]
    if not idx: continue
    snd = parselmouth.Sound(wav); snd = snd.resample(16000, 50) if round(snd.sampling_frequency) != 16000 else snd; x = snd.values[0]
    for i in idx:
        a, b, l = ph[i]; va, vb, _ = ph[i + 1]; cpl = clean(l); p = l.split(",")
        if vb - va < 0.05 or b - a < 0.02: continue
        n = int(vb * 16000) - int(a * 16000)
        s = parselmouth.Sound(np.concatenate([np.zeros(3200), x[int(a * 16000):int(vb * 16000)], np.zeros(1600)]) + np.random.default_rng(0).normal(0, 1e-4, 4800 + n), sampling_frequency=16000)
        t = T[cpl]; r = dict(corpus=CORPUS, spk=spk, phone=cpl, error=len(p) > 2 and p[2].strip() == "s", file=os.path.basename(tg), t=a, color="none", gate=False)
        try:
            first = pc.first_consonant(s)
            r["gate"] = pc.wrong_kind(t, first) and not (t == "tʃ" and first == "SH")
            if cpl in ("S", "SH", "F"):
                bd = find_boundaries(s); v = classify(measure(s, bd.onset_s, bd.offset_s, bd.found_vowel), t)
                v = pc.reconcile(v, pc.check(s, bd.onset_s, bd.offset_s).heard); r.update(color=v.color, heard=v.heard)
            elif cpl == "CH":
                bd = find_boundaries(s); v = classify_affricate(pc.probability_ch(s, bd.onset_s, bd.offset_s)); r.update(color=v.color, heard=v.heard)
            elif cpl in ("M", "N"):
                v = classify_nasal(pc.nasal_reading(s)[0], t)
                if v: r.update(color=v.color, heard=v.heard)
            else:
                m = measure_vot(s); v = classify_stop_probe(pc.probability_p(s, m.burst_s, m.voicing_s), t); r.update(color=v.color, heard=v.heard, vot=m.vot_ms)
        except SegmentationError: pass
        rows.append(r)
    if len(rows) % 300 < len(idx): print(spk, len(rows), flush=True)
pd.DataFrame(rows).to_pickle(OUT); print("done", len(rows))
