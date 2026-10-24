"""Voice onset time (VOT) for word-initial /p/ and /b/.

VOT is the time from the burst (the release of the lips) to the first voiced frame. English /p/ is aspirated, so voicing
starts late (about 40 to 80 ms); /b/ starts voicing at or near the burst (0 to 20 ms). Experimental: the 30 ms threshold
comes from eight ARCTIC voices in running speech (leave-one-voice-out balanced accuracy 0.89), not from isolated words.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import parselmouth
from scipy.signal import butter, sosfilt

from . import config as C
from .classify import LABELS, MARKS, Verdict
from .segment import SegmentationError

BURST_BAND_HZ = (1500.0, 7500.0)
FRAME_S, STEP_S = 0.005, 0.002
RISE_DB = 15.0               # the burst starts when the band is this far above the recording's own floor
VOT_P_MS = 30.0              # at or above: /p/. Provisional (ARCTIC, running speech)
MAX_VOT_MS = 120.0           # longer than this is a sustained hiss (fricative), not a stop; D1 fricatives measure 134 to 268 ms
MARGIN_MS = 10.0             # closer than this to the threshold: yellow
TIPS = {
    "p": "Close the lips, build up air, and release it with a clear puff, like blowing out a candle, before the vowel starts.",
    "b": "Close the lips and start the voice as you release them, with no puff of air before the vowel.",
}


@dataclass(frozen=True)
class StopMeasure:
    burst_s: float
    voicing_s: float
    vot_ms: float


def _band_db(sound: parselmouth.Sound) -> tuple[np.ndarray, np.ndarray]:
    x, fs = sound.values[0], sound.sampling_frequency
    hi = min(BURST_BAND_HZ[1], 0.45 * fs)
    y = sosfilt(butter(4, [BURST_BAND_HZ[0], hi], btype="band", fs=fs, output="sos"), x)
    n, hop = int(FRAME_S * fs), int(STEP_S * fs)
    starts = np.arange(0, max(len(y) - n, 1), hop)
    db = np.array([10 * np.log10(np.mean(y[s:s + n] ** 2) + 1e-12) for s in starts])
    return sound.xmin + (starts + n / 2) / fs, db


def measure_vot(sound: parselmouth.Sound) -> StopMeasure:
    """Burst = first frame of the 1.5 to 7.5 kHz band that is 15 dB above the floor; voicing = first voiced frame after it."""
    t, db = _band_db(sound)
    hot = np.flatnonzero(db > np.percentile(db, 5) + RISE_DB)
    if not len(hot):
        raise SegmentationError("No burst found")
    burst = float(t[hot[0]])
    pitch = sound.to_pitch(STEP_S, C.PITCH_FLOOR_HZ, C.PITCH_CEILING_HZ)
    voiced = [tt for tt in pitch.xs() if tt >= burst and np.isfinite(pitch.get_value_at_time(tt) or np.nan)]
    if not voiced:
        raise SegmentationError("No voicing after the burst")
    vot = (float(voiced[0]) - burst) * 1000
    if vot > MAX_VOT_MS:
        raise SegmentationError(f"The sound before the vowel lasts {vot:.0f} ms, which is a long hiss rather than a stop burst")
    return StopMeasure(burst, float(voiced[0]), vot)


def heard_stop(vot_ms: float) -> str:
    return "p" if vot_ms >= VOT_P_MS else "b"


def classify_stop(m: StopMeasure, target: str) -> Verdict:
    heard = heard_stop(m.vot_ms)
    clear = abs(m.vot_ms - VOT_P_MS) >= MARGIN_MS
    if heard != target:
        color, tip = "red", TIPS[target]
    elif clear:
        color, tip = "green", "Well done. Keep the same lip release."
    else:
        color, tip = "yellow", "Close. " + TIPS[target]
    return Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said {C.PHONE_LABEL[heard]}", tip)


def classify_stop_probe(p_p: float, target: str) -> Verdict:
    """Verdict from the probe's chance of /p/ (same colours rule as the other recogniser-based scorers)."""
    heard = "p" if p_p >= 0.5 else "b"
    p = p_p if heard == "p" else 1 - p_p
    if heard != target:
        color, tip = "red", TIPS[target]
    elif p >= 0.80:
        color, tip = "green", "Well done. Keep the same lip release."
    else:
        color, tip = "yellow", "Close. " + TIPS[target]
    return Verdict(color, LABELS[color], MARKS[color], heard, target, f"You said {C.PHONE_LABEL[heard]}", tip)
