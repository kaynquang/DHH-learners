"""Camera log (testing phase): what the lip mirror and the recorder of the learner app each measured, on one time axis.

The learner app writes logs/camera.jsonl (learner/camlog.py): one line per turn, numbers only (no picture, no sound). Pick a turn here to see the sound
level, the voice test, the lips and the stage of the mirror, with the recorder's own numbers of the same moment, to find where the two disagree.
"""
import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from learner.camlog import PATH

st.title("Camera log")
st.caption("The lip mirror and the recorder of the learner app, measured at the same moments. Numbers only: no picture of the face, no sound.")


@st.cache_data(show_spinner=False)
def _turns(mtime: float) -> list[dict]:
    out = []
    for n, line in enumerate(PATH.read_text(encoding="utf-8").splitlines(), 1):
        try:
            o = json.loads(line)
            f = o["frames"] if "frames" in o else [{"t": r[0], "db": r[1], "bands": r[2:] if o["src"] == "mic-fine" else r[2:3]} for r in o["rows"]]       # "mic-fine": rows of [time, level, 8 bands]
            out.append({"n": n, "src": o["src"], "word": o.get("word", ""), "reason": o.get("reason", ""), "together": o.get("together"),
                        "t0": f[0]["t"], "t1": f[-1]["t"], "frames": f, "meta": {k: v for k, v in o.items() if k not in ("frames", "rows")}})
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    return out


if not PATH.exists():
    st.info("Nothing logged yet. Open the learner app on a lip sound (for example ?word=me), switch the Lip mirror on and press "
            "“Record and mirror together”; the numbers appear here when the turn ends or Restart is pressed.")
    st.stop()

turns = _turns(PATH.stat().st_mtime)
if not turns:
    st.info("The log file is empty.")
    st.stop()
clock = lambda ms: datetime.fromtimestamp(ms / 1000).strftime("%H:%M:%S")

table = pd.DataFrame([{"#": t["n"], "time": clock(t["t0"]), "source": {"mirror": "mirror", "mic": "recorder", "mic-fine": "recorder, fine", "mic-ch": "recorder, /tʃ/ live", "mic-fric": "recorder, hiss live"}.get(t["src"], t["src"]), "word": t["word"],
                       "seconds": round((t["t1"] - t["t0"]) / 1000, 1), "ended by": t["reason"], "frames": len(t["frames"]),
                       "together": "yes" if t["together"] else ("" if t["together"] is None else "no")} for t in turns])
st.download_button("Download camera.jsonl", PATH.read_bytes(), file_name="camera.jsonl", mime="application/jsonl")
event = st.dataframe(table.iloc[::-1], hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", height=260, key="cl_table")
st.caption(f"{len(turns)} turns, newest first. Pick one to see it.")

rows = event.selection.rows if event and event.selection else []
pair_overlap = lambda a, b: max(0, min(a["t1"], b["t1"]) - max(a["t0"], b["t0"])) if a["src"] != b["src"] else 0
if rows:
    chosen = turns[len(turns) - 1 - rows[0]]
else:       # nothing picked: the newest turn that has a turn of the other side at the same time (a recorder and a mirror turn side by side)
    chosen = next((t for t in reversed(turns) if any(pair_overlap(t, o) > 2000 for o in turns)), turns[-1])


def fine_view(t: dict) -> None:
    """A recording of one word with the level and 8 bands at about 60 frames a second (for /tʃ/ against /ʃ/ and /t/): the silence, the rise, the hiss and its length."""
    import numpy as np
    f, edges = t["frames"], t["meta"].get("edges", [])
    x = np.array([(r["t"] - f[0]["t"]) / 1000 for r in f])
    db = np.array([r["db"] for r in f])
    bands = np.array([r["bands"] for r in f], dtype=float).T            # 8 x frames
    st.subheader(f"Turn {t['n']} ({clock(t['t0'])}), the word “{t['word']}”, {len(f)} frames")
    floor = float(np.percentile(db[db > -100], 10)) if (db > -100).any() else -100.0
    on = np.argmax(db > floor + 12) if (db > floor + 12).any() else None
    m = {"room (10th percentile, dB)": round(floor, 1)}
    if on is not None:
        peak_i = on + int(np.argmax(db[on:on + int(0.6 * len(x) / max(x[-1], 1e-6))])) if on + 1 < len(db) else on
        peak = db[peak_i]
        to90 = np.argmax(db[on:] >= floor + 0.9 * (peak - floor)) if (db[on:] >= floor + 0.9 * (peak - floor)).any() else None
        m.update({"sound begins (s after the tap)": round(float(x[on]), 3), "peak level in the first 0.6 s (dB)": round(float(peak), 1),
                  "rise from the room to 90 % of that peak (ms)": None if to90 is None else round(float(x[on + to90] - x[on]) * 1000)})
        if bands.shape[0] >= 8:
            high = 10 * np.log10(np.sum(10 ** (bands[5:8] / 10), axis=0)); low = 10 * np.log10(np.sum(10 ** (bands[0:3] / 10), axis=0))
            voiced_i = np.argmax((low - high)[on:] > 10) if ((low - high)[on:] > 10).any() else None
            m["hiss until the low sounds win by 10 dB (ms)"] = None if voiced_i is None else round(float(x[on + voiced_i] - x[on]) * 1000)
    ev = t["meta"].get("event")
    if ev:                                                                   # the live /tʃ/ guide: what it found while the child was speaking
        if ev.get("slope") is not None: m["live guide: steepest climb (dB/ms)"] = round(ev["slope"], 1)
        if ev.get("hiss") is not None: m["live guide: hiss length (ms)"] = ev["hiss"]
        if ev.get("inZone") is not None: m["live guide: hiss in the target zone (ms)"] = ev["inZone"]
        if ev.get("gap") is not None: m["live guide: voice started after the hiss ended (ms)"] = ev["gap"]
        if ev.get("voice"): m["live guide: voice time counted for the train (ms)"] = ev["voice"]
    st.table(pd.DataFrame({"measure": list(m), "value": ["" if v is None else v for v in m.values()]}))
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, subplot_titles=["Level (dB)", "Energy per band (dB)"])
    fig.add_scatter(x=x, y=db, name="level", line=dict(color="#2F6FE4"), row=1, col=1)
    fig.add_hline(y=floor, line=dict(color="#8A96B0", dash="dot"), row=1, col=1)
    labels = [f"{a / 1000:g}-{b / 1000:g}k" for a, b in edges] or (["2.5-7.9k (live guide)"] if len(bands) == 1 else [str(i) for i in range(len(bands))])
    fig.add_heatmap(x=x, y=labels, z=bands, colorscale="Blues", showscale=False, row=2, col=1)
    fig.update_layout(height=620, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    fig.update_xaxes(title_text="seconds", row=2, col=1)
    st.plotly_chart(fig, width="stretch")


if chosen["src"] in ("mic-fine", "mic-ch", "mic-fric"):
    fine_view(chosen)
    st.stop()
other_src = "mic" if chosen["src"] == "mirror" else "mirror"
overlap = lambda t: pair_overlap(t, chosen)
partners = sorted((t for t in turns if t["src"] == other_src and overlap(t) > 0), key=lambda t: t["t0"])      # a mirror turn can hold several recordings
if chosen["src"] == "mirror":
    mirror, mics = chosen, partners
else:
    mics, mirror = [chosen], (max(partners, key=overlap) if partners else None)
mic = mics[0] if mics else None
others = ", ".join(f"{'recorder' if other_src == 'mic' else 'mirror'} turn {t['n']}" for t in partners)

st.subheader(f"Turn {chosen['n']} ({clock(chosen['t0'])})" + (f" with {others}" if partners else " (nothing from the other side at this time)"))
t_zero = min(t["t0"] for t in ([mirror] if mirror else []) + mics)
sec = lambda f, key: [(x["t"] - t_zero) / 1000 for x in f if x.get(key) is not None]
col = lambda f, key: [x[key] for x in f if x.get(key) is not None]

bands_turn = next((t for t in mics if t["frames"] and "bands" in t["frames"][0]), None)
rows_n = 4 + (1 if bands_turn else 0)
fig = make_subplots(rows=rows_n, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                    subplot_titles=["Sound level (dB) and the gate", "Voice test (1 = clearly a voice)", "Lips (the mirror)", "Where each side thinks it is"] + (["Recorder: energy per band (dB)"] if rows_n == 5 else []))
recorder_colours = ["#D9363E", "#7C3AED", "#0E7490", "#B45309"]
series = ([(mirror, "mirror", "#2F6FE4")] if mirror else []) + [(t, f"recorder {t['n']}", recorder_colours[i % 4]) for i, t in enumerate(mics)]
for t, name, colour in series:
    f = t["frames"]
    fig.add_scatter(x=sec(f, "db"), y=col(f, "db"), name=f"{name} level", line=dict(color=colour), row=1, col=1)
    if any("gate" in x for x in f):
        fig.add_scatter(x=sec(f, "gate"), y=col(f, "gate"), name=f"{name} gate", line=dict(color=colour, dash="dot"), row=1, col=1)
    fig.add_scatter(x=sec(f, "per"), y=col(f, "per"), name=f"{name} voice test", line=dict(color=colour), row=2, col=1)
    if t["meta"].get("periodic") is not None:
        fig.add_hline(y=t["meta"]["periodic"], line=dict(color=colour, dash="dot"), row=2, col=1)
if mirror:
    f = [x for x in mirror["frames"] if x.get("face")]
    fig.add_scatter(x=sec(f, "gap"), y=col(f, "gap"), name="lip gap / face", line=dict(color="#C2410C"), row=3, col=1)
    fig.add_scatter(x=sec(f, "width"), y=col(f, "width"), name="lip width / face", line=dict(color="#1FA45B"), row=3, col=1)
    if any(x.get("ratio") is not None for x in f):                                   # /tʃ/: the width against the relaxed lips of the same turn (x1.00 = relaxed; the smile test is from x1.08)
        fig.add_scatter(x=sec(f, "ratio"), y=[v / 5 for v in col(f, "ratio")], name="width / relaxed width (shown /5)", line=dict(color="#7C3AED", dash="dot"), row=3, col=1)
    fig.add_scatter(x=sec(mirror["frames"], "stage"), y=col(mirror["frames"], "stage"), name="mirror stage", line=dict(color="#2F6FE4", shape="hv"), row=4, col=1)
    if mirror["meta"].get("closedBelow"):
        fig.add_hline(y=mirror["meta"]["closedBelow"], line=dict(color="#C2410C", dash="dot"), row=3, col=1)
for i, t in enumerate(mics):
    f = t["frames"]
    c = recorder_colours[i % 4]
    fig.add_scatter(x=sec(f, "m"), y=[v / 400 for v in col(f, "m")], name=f"recorder {t['n']}: hum counted (1 = done)", line=dict(color=c, shape="hv"), row=4, col=1)
    fig.add_scatter(x=sec(f, "ee"), y=[v / 400 for v in col(f, "ee")], name=f"recorder {t['n']}: vowel counted (1 = done)", line=dict(color=c, shape="hv", dash="dot"), row=4, col=1)
if bands_turn:
    f = bands_turn["frames"]
    z = [[b[i] for b in col(f, "bands")] for i in range(len(f[0]["bands"]))]
    edges = ["0.1-0.3k", "0.3-0.6k", "0.6-1k", "1-1.5k", "1.5-2k", "2-3k", "3-4.5k"]
    fig.add_heatmap(x=sec(f, "bands"), y=edges, z=z, colorscale="Blues", showscale=False, row=5, col=1)
fig.update_layout(height=190 * rows_n + 80, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.05))
fig.update_xaxes(title_text="seconds", row=rows_n, col=1)
st.plotly_chart(fig, width="stretch")

meta = st.expander("Settings written with these turns")
for t in ([mirror] if mirror else []) + mics:
    meta.write(f"{'mirror' if t is mirror else 'recorder'} turn {t['n']}:")
    meta.json(t["meta"])
