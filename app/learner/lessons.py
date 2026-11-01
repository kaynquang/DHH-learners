"""What the learner sees for each word. "see" is filled in from the design mockup (S mockup pdf.pdf); the two round pictures and the meaning of the other words are filled
in at the end of this file from learner/pictures.py (drawn by the assistant, the meanings are those printed on the map mockup); a field that is still None shows a quiet "to be added" box."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from fricative import config as C

ASSETS = Path(__file__).resolve().parent / "assets"
ACCENT = "#2F6FE4"

SNAKE_SVG = """<svg viewBox="0 0 100 100" role="img" aria-label="Snake – makes a hiss sound">
<path d="M 66 30 C 40 26, 28 46, 50 55 C 72 63, 70 86, 38 80" fill="none" stroke="#3E8E3A" stroke-width="13" stroke-linecap="round"/>
<path d="M 66 30 C 40 26, 28 46, 50 55 C 72 63, 70 86, 38 80" fill="none" stroke="#6CB85A" stroke-width="4" stroke-linecap="round" stroke-dasharray="2 7"/>
<ellipse cx="70" cy="30" rx="12" ry="9.5" fill="#3E8E3A"/>
<circle cx="73" cy="26.5" r="3" fill="#FFFFFF"/><circle cx="73.6" cy="26.5" r="1.5" fill="#1B2440"/>
<path d="M 82 33 L 90 34 M 90 34 L 95 30.5 M 90 34 L 95 37.5" fill="none" stroke="#D9363E" stroke-width="2.2" stroke-linecap="round"/>
</svg>"""

EYE_SVG = f"""<svg viewBox="0 0 100 100" role="img" aria-label="Eye – means see">
<path d="M 30 28 L 26 18 M 50 24 L 50 13 M 70 28 L 74 18" fill="none" stroke="#1B2440" stroke-width="4" stroke-linecap="round"/>
<path d="M 8 52 C 26 28, 74 28, 92 52 C 74 76, 26 76, 8 52 Z" fill="#FFFFFF" stroke="#1B2440" stroke-width="4.5" stroke-linejoin="round"/>
<circle cx="50" cy="52" r="16" fill="{ACCENT}"/><circle cx="50" cy="52" r="7.5" fill="#1B2440"/><circle cx="55" cy="46.5" r="3.5" fill="#FFFFFF"/>
</svg>"""


@dataclass(frozen=True)
class Motion:
    """One step of the mouth animation: a spotlight on part of the picture, marks that move there, and the words shown with it.
    Coordinates are pixels of the lesson's mouth picture. `shapes` are dicts: {"type": "ring", "cx", "cy", "r"}, {"type": "arrow", "x", "y",
    "dx", "dy"} (an arrow from (x, y) that points along (dx, dy) and bobs that way) or {"type": "flow", "d": "<svg path>"} (moving air)."""
    caption: tuple[tuple[str, str], ...]                  # (English, Chinese) lines
    spot: tuple[float, float, float, float]               # centre x, centre y, radius x, radius y of the lit area
    shapes: tuple[dict, ...] = ()
    icon: str | None = None                               # "novoice": a crossed-out buzz line next to the words


@dataclass(frozen=True)
class Step:
    """One picture of a lesson that has several (a sound made in steps, like /m/: close the lips, hum, open): the picture, the tips for it
    and how long it stays on screen when the steps play by themselves."""
    image: Path
    checks: tuple[tuple[str, ...], ...]                   # (English, Chinese[, pinyin]) lines under the picture
    seconds: float = 4.0
    shapes: tuple[dict, ...] = ()                         # moving marks drawn on the picture, like Motion.shapes (plus {"type": "wave", ...}: a vibration)
    display_height: int | None = None                    # hide embedded check cards when rendered as accessible text below


@dataclass(frozen=True)
class Lesson:
    word: str
    phone: str                                    # key of config.PHONE_LABEL, e.g. "s"
    highlight: str | None = None                  # the letters that make the target sound, shown in the accent colour
    meaning_zh: str | None = None
    hiss_svg: str | None = None                   # picture for the sound (the snake for /s/)
    hiss_caption: tuple[str, str] | None = None   # (English, Chinese)
    meaning_svg: str | None = None
    mouth_image: Path | None = None
    checks: tuple[tuple[str, ...], ...] = field(default_factory=tuple)    # (English, Chinese[, pinyin]) lines under the mouth picture
    motions: tuple[Motion, ...] = ()              # the 2-3 steps of the mouth animation; without them the still picture is shown
    steps: tuple[Step, ...] = ()                  # several pictures shown one after another instead of one (mouth_image and checks are then unused)

    @property
    def label(self) -> str:
        return C.PHONE_LABEL[self.phone]


_ALL = {**C.TARGETS, **C.STOP_TARGETS, **C.NASAL_TARGETS, **C.AFFRICATE_TARGETS}
# one word per sound, in the order the Dev app lists them
ORDER = []
for _w, _p in _ALL.items():
    if _p not in [_ALL[x] for x in ORDER]:
        ORDER.append(_w)

# Letters that spell the target sound. "knee" is left out on purpose (its /n/ is spelled with a silent k): to be decided with the content owner.
HIGHLIGHT = {"see": "s", "she": "sh", "fee": "f", "pea": "p", "bee": "b", "me": "m", "cheat": "ch"}


# The three steps for /s/, on assets/mouth_s.jpg (1285 x 860). Proposed from the four tips; to be confirmed by the content owner.
MOTIONS_S = (
    Motion((("Teeth close, small smile", "牙齒輕碰，微笑"),), (690, 385, 175, 150),
           ({"type": "ring", "cx": 672, "cy": 350, "r": 62}, {"type": "ring", "cx": 655, "cy": 425, "r": 50})),
    Motion((("Tongue tip down by lower teeth", "舌尖放在下排牙後面"), ("Front of tongue up a little", "舌頭前段微微抬高，留窄縫")), (520, 440, 255, 105),
           ({"type": "ring", "cx": 624, "cy": 450, "r": 38}, {"type": "arrow", "x": 624, "y": 392, "dx": 0, "dy": 36},
            {"type": "ring", "cx": 443, "cy": 388, "r": 32}, {"type": "arrow", "x": 443, "y": 432, "dx": 0, "dy": -36})),
    Motion((("Voice off: no buzz", "手摸喉嚨：不要振動"),), (600, 378, 300, 95),
           ({"type": "flow", "d": "M 345 352 C 430 335, 520 372, 640 370 C 720 368, 780 372, 835 374"},
            {"type": "flow", "d": "M 360 374 C 450 366, 560 392, 650 396 C 730 400, 790 410, 825 428"}), icon="novoice"),
)
LESSONS: dict[str, Lesson] = {w: Lesson(w, _ALL[w], HIGHLIGHT.get(w)) for w in ORDER}
LESSONS["see"] = Lesson(
    "see", "s", "s", meaning_zh="看見", hiss_svg=SNAKE_SVG, hiss_caption=("Hiss: sssss", "嘶嘶聲"), meaning_svg=EYE_SVG,
    mouth_image=ASSETS / "mouth_s.jpg",
    motions=MOTIONS_S,
    checks=(("Teeth close, small smile", "牙齒輕碰，微笑"),
            ("Tongue tip down by lower teeth", "舌尖放在下排牙後面"),
            ("Front of tongue up a little", "舌頭前段微微抬高，留窄縫"),
            ("Voice off: no buzz", "手摸喉嚨：不要振動")),
)
# From the mouth picture for /ʃ/ (the sound picture, the meaning and its translation are still to be provided).
LESSONS["she"] = Lesson(
    "she", "sh", "sh", mouth_image=ASSETS / "mouth_sh.jpg",
    checks=(("Round lips slightly", "嘴唇微圓", "Zuǐchún wēi yuán"),
            ("Tongue up and back", "舌頭抬高，稍往後", "Shétou táigāo, shāo wǎng hòu"),
            ("Keep air flowing", "持續送氣", "Chíxù sòngqì"),
            ("Voice off: no buzz", "聲帶不振動", "Shēngdài bù zhèndòng")),
)
# From the mouth picture for /f/ (the sound picture, the meaning and its translation are still to be provided).
LESSONS["fee"] = Lesson(
    "fee", "f", "f", mouth_image=ASSETS / "mouth_f.jpg",
    checks=(("Upper teeth on lower lip", "上排牙齒輕碰下唇", "Shàng pái yáchǐ qīng pèng xià chún"),
            ("Keep contact light", "輕輕接觸", "Qīngqīng jiēchù"),
            ("Keep air flowing", "持續送氣", "Chíxù sòngqì"),
            ("Voice off: no buzz", "聲帶不振動", "Shēngdài bù zhèndòng")),
)

def _ring(cx, cy, r, color=None):
    return {"type": "ring", "cx": cx, "cy": cy, "r": r, **({"color": color} if color else {})}


def _wave(cx, cy, r, color="#B26BE8"):
    return {"type": "wave", "cx": cx, "cy": cy, "r": r, "color": color}


def _arrow(x, y, dx, dy):
    return {"type": "arrow", "x": x, "y": y, "dx": dx, "dy": dy}


def _flow(d):
    return {"type": "flow", "d": d}


# /m/ is made in three steps, each with its own picture (the picture carries its own step number and title). Coordinates of the marks are
# pixels of that picture (1295 x 897); they are a first placement and can be moved without touching the code that draws them.
LESSONS["me"] = Lesson(
    "me", "m", "m",
    steps=(
        Step(ASSETS / "me_1.jpg", (("Lips together", "雙唇閉合", "Shuāng chún bìhé"),
                                   ("Stay relaxed", "保持放鬆", "Bǎochí fàngsōng"),
                                   ("Hand on throat", "手輕放喉嚨", "Shǒu qīng fàng hóulóng")), 4.0,
             # the lips come together (two arrows) and the hand is shown where to rest
             (_ring(680, 400, 46), _arrow(680, 352, 0, 30), _arrow(680, 450, 0, -30), _ring(1085, 700, 95, "#B26BE8"))),
        Step(ASSETS / "me_2.jpg", (("Lips closed", "雙唇閉合", "Shuāng chún bìhé"),
                                   ("Air through nose", "氣流通過鼻子", "Qìliú tōngguò bízi"),
                                   ("Voice ON • feel vibration", "發聲並感受振動", "Fāshēng bìng gǎnshòu zhèndòng")), 5.0,
             # air flows up to the nose and out, the lips stay closed, the throat vibrates
             (_flow("M 70 480 C 80 360, 160 270, 280 242 C 380 220, 460 170, 540 158 C 600 152, 650 215, 680 218 C 715 218, 740 195, 850 165"),
              _ring(743, 188, 36), _ring(680, 400, 44), _wave(965, 650, 62), _wave(1215, 650, 62))),
        Step(ASSETS / "me_3.jpg", (("Lips open gently", "輕輕張開雙唇", "Qīngqīng zhāngkāi shuāng chún"),
                                   ("Air through mouth", "氣流通過嘴巴", "Qìliú tōngguò zuǐba"),
                                   ("Voice ON • feel vibration", "發聲並感受振動", "Fāshēng bìng gǎnshòu zhèndòng")), 4.0,
             # air flows out through the open mouth, the lips open, the throat still vibrates
             (_flow("M 100 470 C 130 340, 250 258, 400 258 C 520 258, 600 300, 650 372 C 670 392, 740 392, 840 390"),
              _ring(700, 438, 44), _wave(965, 650, 62), _wave(1215, 650, 62))),
    ),
)

# Same player, timing, check cards and animated marks as /m/.
LESSONS["knee"] = Lesson(
    "knee", "n",
    steps=(
        Step(ASSETS / "knee_1.jpg", (
            ("Tongue tip up", "舌尖抬起", "Shéjiān táiqǐ"),
            ("Lips slightly open", "嘴唇微開", "Zuǐchún wēi kāi"),
            ("Hand on throat", "手輕放喉嚨", "Shǒu qīng fàng hóulóng")), 4.0,
            (_ring(678, 254, 40), _arrow(635, 320, 15, -40), _ring(1095, 760, 95, "#B26BE8")), 922),
        Step(ASSETS / "knee_2.jpg", (
            ("Tongue tip up", "舌尖抬起", "Shéjiān táiqǐ"),
            ("Air through nose", "氣流通過鼻子", "Qìliú tōngguò bízi"),
            ("Voice ON • feel vibration", "發聲並感受振動", "Fāshēng bìng gǎnshòu zhèndòng")), 5.0,
            (_flow("M 80 500 C 65 380, 140 310, 250 270 C 360 240, 425 165, 530 145 C 610 125, 625 210, 695 190"),
             _ring(715, 176, 36), _ring(678, 254, 40), _wave(980, 655, 62), _wave(1220, 655, 62)), 922),
        Step(ASSETS / "knee_3.jpg", (
            ("Release tongue tip", "舌尖離開齒齦", "Shéjiān líkāi chǐyín"),
            ("Air through mouth", "氣流通過嘴巴", "Qìliú tōngguò zuǐba"),
            ("Voice ON • feel vibration", "發聲並感受振動", "Fāshēng bìng gǎnshòu zhèndòng")), 4.0,
            (_flow("M 205 343 C 270 300, 390 325, 470 335 C 620 355, 710 405, 835 420"),
             _ring(642, 480, 40), _wave(980, 655, 62), _wave(1220, 655, 62)), 922),
    ),
)


# /ʃ/ and /f/ have one picture each: the same spotlight loop as /s/ (Motion), with the words of their checks. Coordinates are pixels of
# the picture (1301 x 841 and 1301 x 840); a first placement that can be moved without touching the code that draws them.
LESSONS["she"] = replace(LESSONS["she"], motions=(
    Motion((("Round lips slightly", "嘴唇微圓"),), (775, 300, 130, 100),
           (_ring(775, 305, 50), _arrow(690, 305, 40, 0))),
    Motion((("Tongue up and back", "舌頭抬高，稍往後"),), (500, 340, 260, 120),
           (_ring(500, 318, 38), _arrow(500, 385, 0, -34))),
    Motion((("Keep air flowing", "持續送氣"),), (650, 330, 300, 100),
           (_flow("M 410 292 C 500 262, 580 275, 630 310 C 670 350, 700 365, 790 372"), _flow("M 710 368 C 770 372, 810 374, 850 378"))),
    Motion((("Voice off: no buzz", "聲帶不振動"),), (700, 340, 260, 100),
           (_flow("M 480 300 C 560 275, 620 300, 670 340 C 710 365, 760 372, 840 376"),), icon="novoice"),
))
LESSONS["fee"] = replace(LESSONS["fee"], motions=(
    Motion((("Upper teeth on lower lip", "上排牙齒輕碰下唇"),), (650, 335, 150, 110),
           (_ring(650, 345, 40), _arrow(632, 275, 0, 26))),
    Motion((("Keep contact light", "輕輕接觸"),), (650, 345, 120, 90), (_ring(650, 345, 36),)),
    Motion((("Keep air flowing", "持續送氣"),), (700, 345, 260, 90),
           (_flow("M 470 322 C 560 322, 620 345, 690 348 C 760 345, 800 340, 850 335"), _flow("M 700 352 C 770 355, 810 362, 850 368"))),
    Motion((("Voice off: no buzz", "聲帶不振動"),), (700, 345, 260, 90),
           (_flow("M 470 322 C 560 322, 620 345, 690 348 C 760 345, 800 340, 850 335"),), icon="novoice"),
))

# Pictures with their own bilingual checks (so none repeated underneath), played in articulation order like /m/ and /n/, with moving marks
# on the mouth. Coordinates are pixels of the 1334 x 1179 pictures; a first placement.
LESSONS["pea"] = Lesson(
    "pea", "p", "p",
    steps=(
        Step(ASSETS / "pea_1.jpg", (), 4.0,
             (_ring(700, 420, 40), _arrow(700, 365, 0, 28), _arrow(700, 478, 0, -28))),
        Step(ASSETS / "pea_2.jpg", (), 3.0,
             (_ring(700, 440, 36), _flow("M 660 425 C 720 412, 790 410, 845 410"))),
        Step(ASSETS / "pea_3.jpg", (), 4.0,
             (_flow("M 360 285 C 520 290, 620 340, 710 390 C 760 410, 800 415, 845 420"), _ring(690, 505, 40),
              _wave(965, 800, 58), _wave(1250, 790, 58))),
    ),
)
LESSONS["bee"] = Lesson(
    "bee", "b", "b",
    steps=(
        Step(ASSETS / "bee_1.jpg", (), 4.0,
             (_ring(722, 410, 38), _arrow(722, 358, 0, 28), _arrow(722, 468, 0, -28))),
        Step(ASSETS / "bee_2.jpg", (), 3.0,
             (_ring(735, 440, 36), _flow("M 670 415 C 720 410, 760 410, 795 415"), _wave(1010, 745, 55), _wave(1205, 745, 55))),
        Step(ASSETS / "bee_3.jpg", (), 4.0,
             (_flow("M 330 300 C 480 300, 600 340, 700 400 C 740 425, 770 430, 790 432"), _ring(730, 470, 40),
              _wave(1010, 745, 55), _wave(1205, 745, 55))),
    ),
)
LESSONS["cheat"] = Lesson(
    "cheat", "tʃ", "ch",
    steps=(
        Step(ASSETS / "cheat_1.jpg", (), 4.0,
             (_ring(668, 268, 40), _arrow(640, 340, 15, -40), _ring(1100, 190, 95))),
        Step(ASSETS / "cheat_2.jpg", (), 3.0,
             (_flow("M 160 380 C 300 370, 420 270, 560 262 C 650 258, 720 280, 800 322"), _ring(662, 262, 36))),
        Step(ASSETS / "cheat_3.jpg", (), 4.0,
             (_flow("M 210 350 C 300 320, 520 330, 650 380 C 720 405, 790 415, 850 420"), _ring(648, 483, 36),
              _wave(980, 640, 62), _wave(1235, 640, 62))),
    ),
)

# The two round pictures of the word card and the meaning in Chinese, for every word that has none yet (only "see" has the content owner's pictures).
from .pictures import ART, MEANING, SOUND_ART, SOUND_CAPTION, svg_of  # noqa: E402

for _w in ORDER:
    _l = LESSONS[_w]
    LESSONS[_w] = replace(
        _l, meaning_zh=_l.meaning_zh or MEANING.get(_w),
        hiss_svg=_l.hiss_svg or (svg_of(*SOUND_ART[_w]) if _w in SOUND_ART else None), hiss_caption=_l.hiss_caption or SOUND_CAPTION.get(_w),
        meaning_svg=_l.meaning_svg or (svg_of(ART[_w], f"Picture for {_w}") if _w in ART else None))
