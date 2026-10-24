"""/tʃ/ ("ch") against /ʃ/ from how the hiss starts: an affricate starts abruptly, a plain /ʃ/ fades in.

The measures are the 10% to 90% rise time of the 2.5 to 7.9 kHz envelope and its steepest climb (dB per ms). The hiss length is
reported but not used: it depends on how much of the recording follows the word.
Experimental: a two-class LDA trained on eight ARCTIC voices in running speech (leave-one-voice-out balanced accuracy 0.80,
worst voice 0.74); not validated on isolated words.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import parselmouth
from scipy.signal import butter, sosfilt

from . import config as C
from .calibrated import GREEN_P
from .classify import LABELS, MARKS, Verdict
from .segment import SegmentationError

MODEL_JSON = Path(__file__).resolve().parents[1] / "assets" / "model" / "other_lda.json"
RATE_HZ, BAND_HZ, FRAME, HOP = 16000, (2500.0, 7900.0), 80, 32
TIP = "Start with the tongue against the roof of the mouth, release it suddenly into a short /ʃ/ hiss, with rounded lips."


@dataclass(frozen=True)
class AffricateMeasure:
    rise_ms: float
    slope_db_per_ms: float
    hiss_ms: float
    onset_s: float


def measure_affricate(sound: parselmouth.Sound) -> AffricateMeasure:
    s = sound if round(sound.sampling_frequency) == RATE_HZ else sound.resample(RATE_HZ, 50)
    x = s.values[0]
    y = sosfilt(butter(4, BAND_HZ, btype="band", fs=RATE_HZ, output="sos"), x)
    starts = np.arange(0, len(y) - FRAME, HOP)
    db = np.array([10 * np.log10(np.mean(y[i:i + FRAME] ** 2) + 1e-12) for i in starts])
    hot = np.flatnonzero(db > np.percentile(db, 5) + C.ONSET_DB_ABOVE_FLOOR)
    if len(hot) < 5 or hot[0] + 30 >= len(db):
        raise SegmentationError("No hiss found")
    on = int(hot[0])
    amp = 10 ** (db[on:on + 60] / 20)
    peak = amp.max()
    rise = (np.argmax(amp >= 0.9 * peak) - np.argmax(amp >= 0.1 * peak)) * (HOP / RATE_HZ * 1000)
    slope = float(np.max(db[on + 2:on + 30] - db[on:on + 28]) / 4)
    return AffricateMeasure(float(rise), slope, float((hot[-1] - hot[0]) * HOP / RATE_HZ * 1000), float((starts[on] + FRAME / 2) / RATE_HZ))


def probability_ch(m: AffricateMeasure, model: dict | None = None) -> float:
    """Probability of /tʃ/ (an estimate: LDA scores are over-confident)."""
    spec = (model or json.loads(MODEL_JSON.read_text(encoding="utf-8")))["affricate"]
    x = np.array([m.rise_ms, m.slope_db_per_ms])
    score = float(np.dot(spec["coef"], x) + spec["intercept"])
    p_second = 1 / (1 + np.exp(-score))                  # probability of classes[1]
    return p_second if spec["classes"][1] == "CH" else 1 - p_second


def classify_affricate(p_ch: float) -> Verdict:
    heard = "tʃ" if p_ch >= 0.5 else "sh"
    p = p_ch if heard == "tʃ" else 1 - p_ch
    if heard != "tʃ":
        color, tip = "red", TIP
    elif p >= GREEN_P:
        color, tip = "green", "Well done. Keep the abrupt start."
    else:
        color, tip = "yellow", "Close. " + TIP
    return Verdict(color, LABELS[color], MARKS[color], heard, "tʃ", f"You said {C.PHONE_LABEL[heard]}", tip)
