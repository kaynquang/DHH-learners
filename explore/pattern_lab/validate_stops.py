"""End-to-end check of app/fricative/stops.py on ARCTIC word-initial /p/ and /b/ (clip = the start of the stop to the end of the vowel)."""
import sys, pickle
import numpy as np, pandas as pd, parselmouth
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "app"))
from fricative.segment import SegmentationError
from fricative.stops import heard_stop, measure_vot
S = sys.argv[1]
df = pickle.load(open(f"{S}/other.pkl", "rb")); df = df[df.phone.isin(["P", "B"])]
rows = []
for r in df.itertuples():
    snd = parselmouth.Sound(f"{S}/wav_{r.spk}/{r.file}.wav")
    clip = snd.extract_part(r.start, r.end + r.vowel_ms / 1000, parselmouth.WindowShape.RECTANGULAR, 1, False)
    try: m = measure_vot(clip)
    except SegmentationError: rows.append((r.spk, r.phone, np.nan)); continue
    rows.append((r.spk, r.phone, m.vot_ms))
o = pd.DataFrame(rows, columns=["spk", "phone", "vot"])
print(o.groupby("phone").vot.describe(percentiles=[.5,.9,.95,.99]).round(0).to_string()); print("failed:", int(o.vot.isna().sum()), "of", len(o))
o = o.dropna(); o["ok"] = (o.vot.map(heard_stop) == o.phone.str.lower())
acc = o.groupby(["spk", "phone"]).ok.mean().unstack(); acc["balanced"] = acc.mean(axis=1)
print(acc.round(3).to_string()); print("mean balanced", round(acc.balanced.mean(), 3), "| median VOT", o.groupby("phone").vot.median().round(1).to_dict())
