"""Room noise: how loud the room is when nobody speaks, and how far above it a spoken word is.

The levels are in dB relative to the loudest possible sample (dBFS), measured over 25 ms frames. The limits are provisional: tried on one
microphone and one room, to be checked on the real recording setup.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FRAME_S = 0.025
SNR_TOO_NOISY_DB = 20.0      # below this the hiss measures cannot be trusted
SNR_GOOD_DB = 30.0           # from here on the room is fine


ROOM_QUIET_DBFS = -55.0      # the quiet room alone (no speech): below this it is quiet, above ROOM_NOISY_DBFS it is too noisy
ROOM_NOISY_DBFS = -45.0


def room_verdict(noise_db: float) -> str:
    return "good" if noise_db < ROOM_QUIET_DBFS else "noisy" if noise_db >= ROOM_NOISY_DBFS else "ok"


def _frame_db(sound) -> np.ndarray:
    x = np.asarray(sound.values, dtype=float).reshape(-1)
    n = max(1, int(sound.sampling_frequency * FRAME_S))
    frames = x[: len(x) // n * n].reshape(-1, n) if len(x) >= n else x.reshape(1, -1)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-7))


def noise_floor_db(sound) -> float:
    """Level of the quiet room: the median frame (a cough or a click in a few frames does not move it)."""
    return float(np.median(_frame_db(sound)))


def speech_level_db(sound) -> float:
    """Level of the spoken word: the loud end of its frames."""
    return float(np.percentile(_frame_db(sound), 95))


@dataclass(frozen=True)
class RoomCheck:
    noise_db: float
    speech_db: float

    @property
    def snr_db(self) -> float:
        return self.speech_db - self.noise_db

    @property
    def verdict(self) -> str:
        return "noisy" if self.snr_db < SNR_TOO_NOISY_DB else "ok" if self.snr_db < SNR_GOOD_DB else "good"


def check(noise_db: float, sound) -> RoomCheck:
    return RoomCheck(noise_db, speech_level_db(sound))


RECORDING_MIN_SNR_DB = 12.0  # only a recording this close to its own background is refused. Set from the first real recordings (quality.csv):
                             # a normal room gave 16 to 24 dB, so the earlier 20 refused good recordings.
TOO_QUIET_DBFS = -45.0      # the loud end of the recording is below this: the child was too far from the microphone or too soft
CLIP_PEAK = 0.99             # a sample this close to full scale: the microphone was overloaded


@dataclass(frozen=True)
class Quality:
    problem: str | None      # None (fine), "noisy", "quiet" or "loud"
    snr_db: float
    level_db: float


def log_quality(word: str, q: Quality, color: str | None = None, cog_hz: float | None = None, heard: str | None = None,
                notice: str | None = None, path=None) -> None:
    """One line of numbers per recording (no audio), so the limits above can be set from real rooms. Append-only CSV in the logs folder."""
    import csv
    import datetime
    import os
    from pathlib import Path
    path = Path(path or Path(os.environ.get("FRICATIVE_LOGS") or Path(__file__).resolve().parents[1] / "logs") / "quality.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ["time", "word", "problem", "snr_db", "level_dbfs", "verdict", "cog_hz", "heard", "notice"]
    if path.exists():                                   # an older file without the "notice" column: add it
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if rows and rows[0] != header:
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(r + [""] * (len(header) - len(r)) for r in rows[1:])
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), word, q.problem or "ok", f"{q.snr_db:.1f}", f"{q.level_db:.1f}",
                    color or "", f"{cog_hz:.0f}" if cog_hz else "", heard or "", notice or ""])


def recording_quality(sound, room_db: float | None = None) -> Quality:
    """Is this recording good enough to score? The quiet part of the clip itself stands for the room (a 3 s clip holds mostly silence),
    so no earlier measurement is needed. Provisional limits, like the ones above.
    room_db: the room level the recorder measured while recording (the guided recorder follows the child's voice, so a clip can be all voice,
    from the first 0.2 s to the last; then the 10th percentile of its frames is the voice, not the room, and the SNR comes out far too low:
    8 dB for a voice 15 dB over the room in the log of 18:48). The quieter of the two is taken as the room."""
    frames = _frame_db(sound)
    noise, level = float(np.percentile(frames, 10)), float(np.percentile(frames, 95))
    if room_db is not None:
        noise = min(noise, room_db)
    peak = float(np.max(np.abs(np.asarray(sound.values))))
    problem = ("loud" if peak >= CLIP_PEAK else "quiet" if level < TOO_QUIET_DBFS else "noisy" if level - noise < RECORDING_MIN_SNR_DB else None)
    return Quality(problem, level - noise, level)
