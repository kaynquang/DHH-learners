"""The Dev prototype's scoring of /s/, /ʃ/ and /f/ as one function, step for step as app_pages/practice.py does it, so another front end
(the learners' app) gives the same verdict for the same recording.

Steps: the recogniser's first-sound gate; the hiss boundaries (the Dev page lets the user drag them when they cannot be found, here the
recording is simply not scored); the measures; the rule verdict, replaced by the calibrated one when a calibration is given; and the
recogniser's check of the hiss, which can refuse to score and which can correct the verdict (phoneme_check.reconcile).
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from parselmouth.praat import call

from . import config as C
from . import phoneme_check
from .calibrated import Calibration, Reading, load_model, read as read_calibrated
from .classify import Verdict, classify
from .measure import Measures, measure
from .patterns import extract
from .segment import Boundaries, SegmentationError, find_boundaries


@dataclass(frozen=True)
class FricativeScore:
    verdict: Verdict | None = None
    measures: Measures | None = None
    boundaries: Boundaries | None = None
    reading: Reading | None = None
    rule_verdict: Verdict | None = None     # what the fixed thresholds said, before calibration and the recogniser
    notice: str = ""                        # why there is no verdict


RUMBLE_HZ = 150.0      # below this a recording holds the blow of the breath on the microphone, not speech (a child's voice starts at about 250 Hz)


def without_rumble(sound):
    """The sound with everything below RUMBLE_HZ removed. Blowing hard into a microphone makes a low rumble that can outweigh a weak hiss such as
    /f/ (measured on three recordings of "fee": a CoG of 384 to 557 Hz over a hiss of 0.9 to 1.3 s, and 3.5 to 5 kHz once the rumble was removed)."""
    return call(sound, "Filter (pass Hann band)", RUMBLE_HZ, sound.sampling_frequency / 2 - 1, 30)


def cap_at_yellow(v: Verdict, note: str) -> Verdict:
    """The same verdict, at best yellow: a green that nothing but the numbers vouches for is never shown."""
    from .classify import LABELS, MARKS
    return v if v.color != "green" else replace(v, color="yellow", label=LABELS["yellow"], mark=MARKS["yellow"], note=note)


def score_fricative(sound, target: str, calibration: Calibration | None = None, th: C.Thresholds = C.DEFAULT_THRESHOLDS) -> FricativeScore:
    recogniser = phoneme_check.available()
    if recogniser:      # is this the right kind of sound for the word?
        opens = phoneme_check.first_consonant(sound)
        if opens is None:
            return FricativeScore(notice="No consonant was heard at the start.")
        if phoneme_check.wrong_kind(target, opens):
            return FricativeScore(notice=f"A different kind of sound was heard at the start ({phoneme_check.GATE_LABEL[opens]}).")
    try:
        b = find_boundaries(sound)
    except SegmentationError as exc:
        return FricativeScore(notice=f"{exc}.")
    if b.offset_s - b.onset_s < C.MIN_FRICATION_S:
        return FricativeScore(boundaries=b, notice="The hiss is too short to measure.")
    m = measure(sound, b.onset_s, b.offset_s, b.found_vowel)
    # is there a hiss at all? asked of the sound without the rumble, so a blown /f/ is not taken for silence; every other measure is on the original,
    # because the thresholds were set on unfiltered recordings
    if measure(without_rumble(sound), b.onset_s, b.offset_s, b.found_vowel).cog_hz < C.MIN_HISS_COG_HZ:
        return FricativeScore(measures=m, boundaries=b, notice="No hiss was found.")
    v = v_rule = classify(m, target, th)
    reading = None
    if calibration is not None:
        reading = read_calibrated(extract(sound, b.onset_s, b.offset_s, b.found_vowel, with_f2=False), calibration, load_model(), target)
        v = reading.verdict
    if recogniser:
        heard = phoneme_check.check(sound, b.onset_s, b.offset_s).heard
        if heard is None:       # the recogniser hears none of /s ʃ f θ/ over the hiss: never show green
            if target == "f" and v.heard == "f":      # /f/ is the weak one the recogniser often misses: the numbers say /f/, so show at most yellow
                note = "The recogniser did not confirm this sound, so it cannot be green."
                return FricativeScore(cap_at_yellow(v, note), m, b, reading, v_rule)
            return FricativeScore(measures=m, boundaries=b, rule_verdict=v_rule, notice="No /s ʃ f/ sound was heard in the hiss.")
        v = phoneme_check.reconcile(v, heard)
    return FricativeScore(v, m, b, reading, v_rule)
