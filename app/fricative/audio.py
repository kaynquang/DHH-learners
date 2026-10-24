"""Audio loading via Parselmouth (decodes exactly like Praat)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import parselmouth
from parselmouth.praat import call

from .config import MAX_DURATION_S


def _suffix_for(data: bytes, name: str | None) -> str:
    if name and "." in name:
        return "." + name.rsplit(".", 1)[1].lower()
    return ".wav" if data[:4] == b"RIFF" else ".mp3"


def load(source: str | Path | bytes, name: str | None = None) -> parselmouth.Sound:
    """Read wav/mp3 from a path or bytes and return a mono Sound."""
    try:
        if isinstance(source, (str, Path)):
            sound = parselmouth.Sound(str(source))
        else:
            with tempfile.NamedTemporaryFile(suffix=_suffix_for(source, name)) as fh:
                fh.write(source)
                fh.flush()
                sound = parselmouth.Sound(fh.name)
    except parselmouth.PraatError as exc:
        raise ValueError("Could not read the audio file; please use wav or mp3") from exc
    if sound.n_channels > 1:
        sound = sound.convert_to_mono()
    return sound


def limit_duration(sound: parselmouth.Sound, max_s: float = MAX_DURATION_S) -> tuple[parselmouth.Sound, bool]:
    """Keep only the first max_s seconds. Returns (sound, was_truncated)."""
    if sound.xmax - sound.xmin <= max_s:
        return sound, False
    return call(sound, "Extract part", sound.xmin, sound.xmin + max_s, "rectangular", 1, "no"), True
