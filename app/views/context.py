"""What every Practice view needs to know about the current recording."""
from dataclasses import dataclass

import parselmouth

from fricative.classify import Verdict
from fricative.config import Thresholds
from fricative.measure import Measures


@dataclass(frozen=True)
class Ctx:
    sound: parselmouth.Sound
    data: bytes
    name: str
    word: str
    target: str
    onset: float
    offset: float
    has_vowel: bool
    m: Measures
    th: Thresholds
    verdict: Verdict
    manual: tuple[float, float] | None
