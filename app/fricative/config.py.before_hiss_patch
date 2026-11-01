"""Defaults. Thresholds are PROVISIONAL, derived from the two D1 voices; replace with D2 norms."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Thresholds:
    cog_s_sh_hz: float = 4340.0      # CoG >= threshold -> /s/, below -> /ʃ/
    relamp_f_db: float = -15.0       # relative amplitude < threshold -> /f/
    cog_margin_hz: float = 300.0     # closer than this to the CoG threshold -> yellow
    relamp_margin_db: float = 3.0    # closer than this to the relative-amplitude threshold -> yellow


DEFAULT_THRESHOLDS = Thresholds()

# Word-initial hiss followed by a vowel; the first word of each sound is the one used in calibration and the D1 samples.
TARGETS = {"see": "s", "sip": "s", "sun": "s", "she": "sh", "ship": "sh", "shoe": "sh", "fee": "f", "fan": "f", "food": "f"}
# The other charter sounds, each with its own way of scoring.
NASAL_TARGETS = {"me": "m", "knee": "n"}       # scored by the phone recogniser (fricative/nasals.py)
AFFRICATE_TARGETS = {"cheat": "tʃ"}            # scored by how the hiss starts (fricative/affricate.py)
STOP_TARGETS = {"pea": "p", "bee": "b"}     # scored by VOT (fricative/stops.py)
PHONE_LABEL = {"s": "/s/", "sh": "/ʃ/", "f": "/f/", "m": "/m/", "n": "/n/", "p": "/p/", "b": "/b/", "tʃ": "/tʃ/"}

# Articulation diagrams (app/assets/articulation) and one-line descriptions.
ARTICULATION_IMAGE = {p: Path(__file__).resolve().parents[1] / "assets" / "articulation" / f"{p}.jpg"
                      for p in ("s", "sh", "f")}
ARTICULATION_NOTE = {
    "s": "Tongue tip close behind the upper teeth; a narrow jet of air hits the teeth.",
    "sh": "Tongue pulled back and lips rounded; a wider channel and a larger space in front.",
    "f": "Upper teeth resting on the lower lip; a gentle, spread-out flow of air.",
}

# Energy analysis frames
FRAME_WIN_S = 0.010
FRAME_HOP_S = 0.002
HI_BAND_HZ = (2500.0, 12000.0)
ONSET_DB_ABOVE_FLOOR = 15.0
GAP_BRIDGE_S = 0.020          # gaps shorter than this still count as one hiss
MIN_VOICED_S = 0.020          # voiced stretches shorter than this are ignored

# Pitch (vowel detection)
PITCH_FLOOR_HZ = 75.0
PITCH_CEILING_HZ = 500.0
VOICING_SEARCH_DELAY_S = 0.020

# Measurement
MIN_FRICATION_S = 0.030
VOWEL_GAP_S = 0.020
VOWEL_LEN_S = 0.060
FM_BAND_HZ = (2000.0, 8000.0)
MAX_DURATION_S = 5.0
