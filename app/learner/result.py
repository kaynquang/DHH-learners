"""Scoring a learner's recording and the result panel that takes the place of the record button.

Scoring uses the rules the Dev app already has, nothing new:
- /s/ and /ʃ/: the CoG of the hiss against the Dev threshold (fricative/classify.py).
- /b/ /p/ /m/ /n/ /tʃ/: goodness of pronunciation (fricative/gop.py), when the phone recogniser is installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

import parselmouth
import streamlit as st

from fricative import config as C
from fricative import gop, phoneme_check
from fricative.audio import limit_duration, load
from fricative import vtl
from fricative.pipeline import score_fricative

from . import affricate_check, spectro, stars, tongue, zh
from .lessons import ACCENT
from .screen import svg_img

MARK_COLOUR = {"green": "#3E8E3A", "yellow": "#E0A100", "red": "#D9363E"}


@dataclass(frozen=True)
class Result:
    color: str | None = None        # "green" | "yellow" | "red", None when nothing could be scored
    label: str = ""
    mark: str = ""
    message: str = ""
    tip: str = ""
    heard: str | None = None        # the sound the verdict says was heard
    cog_hz: float | None = None     # /s/, /ʃ/ and /f/: centre of gravity of the hiss
    position: float | None = None   # /s/ and /ʃ/: 0 = /ʃ/ ... 1 = /s/, where the sound lies
    notice: str = ""                # why there is no score
    relamp_db: float | None = None  # /f/: how much weaker the hiss is than the vowel after it (negative dB); the /f/ cue, see bars_html
    closeness: float | None = None  # 0 (far) to 1 (right on the target), inside the verdict's own zone: tells the two halves of yellow apart
    affricate: object | None = None  # /tʃ/: the pop and the hiss (learner/affricate_check.py: Check), shown as two lamps


RED_RANGE_HZ = 3000.0       # a CoG this far on the wrong side of the /s/-/ʃ/ threshold is the far end of the red zone
GREEN_RANGE_HZ = 3000.0     # and this far past the yellow margin on the right side is the far end of the green zone
ZONE = {"green": (tongue.YELLOW_Q_MAX, 1.0), "yellow": (tongue.RED_Q_MAX + 0.02, tongue.YELLOW_Q_MAX - 0.02), "red": (0.0, tongue.RED_Q_MAX - 0.02)}


def closeness(s, phone: str, color: str, th: C.Thresholds = C.DEFAULT_THRESHOLDS) -> float:
    """How close the sound is to the target, 0 (far) to 1 (right on it), laid out so that the green, yellow and red zones of the slider are
    exactly the verdict's colours (red below 0.5, yellow 0.5 to 0.8, green from 0.8, the same cut as the calibrated model's GREEN_P).
    With a calibration it is the model's probability of the target; without, the CoG's distance from the threshold, with the yellow zone as
    wide as the Dev app's CoG margin. The verdict can also come from the recogniser's check, so the value is kept inside its own zone."""
    if s.reading is not None:
        q = s.reading.probs[phone]
    else:
        signed =(s.measures.cog_hz - th.cog_s_sh_hz) if phone == "s" else (th.cog_s_sh_hz - s.measures.cog_hz)
        if signed < 0:
            q = 0.5 * max(0.0, 1 + signed / RED_RANGE_HZ)
        elif signed < th.cog_margin_hz:
            q = 0.5 + 0.3 * signed / th.cog_margin_hz
        else:
            q = 0.8 + 0.2 * min(1.0, (signed - th.cog_margin_hz) / GREEN_RANGE_HZ)
    lo, hi = ZONE[color]
    return min(hi, max(lo, q))


@st.cache_data(show_spinner="…")
def score(wav: bytes, phone: str, scale: float = 1.0) -> Result:
    """Score a recording. /s/, /ʃ/, /f/ go through the Dev prototype's pipeline (fricative/pipeline.py). `scale` is the size of the child's
    voice (fricative/vtl.py: 1.0 = the adult thresholds): it moves the /s/-/ʃ/ boundary. The learner is not asked to say the target
    sounds right beforehand, so there is no calibration from the sounds being taught."""
    try:
        sound, _ = limit_duration(load(wav, "recording.wav"))
    except ValueError as exc:
        return Result(notice=str(exc))
    if phone in ("s", "sh", "f"):
        th = vtl.thresholds(scale)
        s = score_fricative(sound, phone, None, th)
        if s.verdict is None:
            return Result(notice=s.notice)
        v = s.verdict
        q = closeness(s, phone, v.color, th)
        pos = (q if phone == "s" else 1 - q) if phone in ("s", "sh") else None     # the target is the /s/ end for "s", the /ʃ/ end for "sh"
        return Result(v.color, v.label, v.mark, v.message, v.tip, heard=v.heard, cog_hz=s.measures.cog_hz, position=pos, closeness=q,
                      relamp_db=s.measures.relamp_db)
    if phone in gop.SUPPORTED and phoneme_check.available():
        g = gop.score(sound, phone)
        if g is None:
            return Result(notice="No speech was heard in this recording.")
        v = gop.verdict(g, phone)
        if v is None:
            return Result(notice="Not sure which sound this was.")
        lo, hi = ZONE[v.color]
        return Result(v.color, v.label, v.mark, v.message, v.tip, heard=v.heard, closeness=min(hi, max(lo, g.p(phone))),
                      affricate=affricate_check.check(sound) if phone == "tʃ" else None)
    return Result(notice="This sound cannot be scored yet.")

HELD_GREEN_MS = 800      # a held /s/ or /ʃ/: this long in the right zone is green, from HELD_YELLOW_MS yellow, less is red (guesses, with the 0.4 s of the guide's box)
HELD_YELLOW_MS = 400
HELD_MIN_MS = 300        # a hiss shorter than this is not a hiss


def from_live(live: dict, phone: str) -> Result:
    """The result of a guided practice of a held /s/ or /ʃ/ ("shhh" that goes on into "ee"), made from what the live guide found while the child was speaking
    (the dot and the box, learner/mic.py startFricGuide): how long the hiss lasted and how much of it was in the target zone. The recogniser and the rules of the pipeline
    look at a whole word and refused such recordings ("No consonant was heard at the start") though the hiss was right; and the dot, the box and the result must say the same."""
    hiss, held = int(live.get("hiss") or 0), int(live.get("inZone") or 0)
    if hiss < HELD_MIN_MS:
        return Result(notice="The hiss is too short to measure.")
    from fricative.classify import LABELS, MARKS
    color = "green" if held >= HELD_GREEN_MS else "yellow" if held >= HELD_YELLOW_MS else "red"
    q = (0.8 + 0.2 * min(1.0, (held - HELD_GREEN_MS) / HELD_GREEN_MS) if color == "green" else 0.5 + 0.3 * (held - HELD_YELLOW_MS) / (HELD_GREEN_MS - HELD_YELLOW_MS)
         if color == "yellow" else 0.5 * held / HELD_YELLOW_MS)
    sound = "/s/" if phone == "s" else "/ʃ/"
    message = {"green": f"You held {sound}", "yellow": f"Nearly: hold {sound} a little longer", "red": f"Not yet: keep the dot in the green"}[color]
    tip = f"{hiss / 1000:.1f} s of hiss, {held / 1000:.1f} s in the green" + ("; then the smile" if live.get("win") else "")
    lo, hi = ZONE[color]
    return Result(color, LABELS[color], MARKS[color], message, tip, heard=phone, closeness=min(hi, max(lo, q)))


CSS = f"""
.st-key-result {{ background: #fff; border: 1.5px solid #D5DFF0 !important; border-radius: 24px !important; box-shadow: 0 4px 0 #D5DFF0;
  padding: 24px 22px !important; min-height: 660px; justify-content: center; }}
.rs-head {{ display: flex; align-items: center; gap: 16px; justify-content: center; color: #1B2440; }}
.rs-mark {{ width: 76px; height: 76px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 40px; font-weight: 900; }}
.rs-label {{ font-size: 34px; font-weight: 900; line-height: 1.1; }}
.rs-msg {{ font-size: 18px; font-weight: 800; color: #3A4664; }}
.rs-stars {{ display: flex; justify-content: center; gap: 8px; margin: 14px 0 0; font-size: 46px; line-height: 1; }}
.rs-stars span {{ color: #D5DFF0; }} .rs-stars span.on {{ color: #F5B400; text-shadow: 0 2px 0 #D99A00; }}
.rs-again {{ text-align: center; font-size: 20px; font-weight: 900; color: #D9363E; margin-top: 8px; }} .rs-again .zh {{ font-weight: 600; color: #3A4664; }}
.rs-tip {{ font-size: 15px; color: #3A4664; text-align: center; margin: 4px 0 0; }}
.rs-notice {{ font-size: 20px; font-weight: 800; color: #1B2440; text-align: center; padding: 30px 10px; }}
.st-key-again button {{ min-height: 56px; border-radius: 999px; background: {ACCENT}; color: #fff; border: none; font-size: 18px; font-weight: 800;
  box-shadow: inset 0 -4px 0 rgba(0,0,0,.18); }}
.st-key-again button:hover {{ background: {ACCENT}; color: #fff; filter: brightness(1.08); }}
.st-key-again button p {{ font-size: 18px; font-weight: 800; }}
"""


BAR_PX = 170                # height of the vowel bar


def bars_html(relamp_db: float | None) -> str:
    """/f/ as two bars: the hiss "f" and the vowel "ee" after it. /f/ is the soft one: the cue the scoring uses is that the hiss is more than
    15 dB weaker than the vowel (config.Thresholds.relamp_f_db, with its margin), so the "f" bar must stay low, in the green zone behind it.
    The bar heights are amplitude ratios (the vowel is 100%)."""
    if relamp_db is None:
        return ""
    th = C.DEFAULT_THRESHOLDS
    ratio = lambda db: 10 ** (db / 20)
    green_top, yellow_top = ratio(th.relamp_f_db - th.relamp_margin_db), ratio(th.relamp_f_db)
    hiss = min(1.2, ratio(relamp_db))
    colour = MARK_COLOUR["green"] if relamp_db < th.relamp_f_db - th.relamp_margin_db else MARK_COLOUR["yellow"] if relamp_db < th.relamp_f_db else MARK_COLOUR["red"]
    px = lambda r: f"{max(r, 0.0) * BAR_PX:.0f}px"
    zones = (f'<div style="position:absolute;left:0;right:0;bottom:0;height:{px(green_top)};background:#BFE3C9"></div>'
             f'<div style="position:absolute;left:0;right:0;bottom:{px(green_top)};height:{px(yellow_top - green_top)};background:#FFF1B8"></div>'
             f'<div style="position:absolute;left:0;right:0;bottom:{px(yellow_top)};top:0;background:#FFD3D8"></div>')
    col = lambda inner, label: (f'<div style="text-align:center"><div style="position:relative;width:96px;height:{BAR_PX + 20}px;border-radius:14px;'
                                f'overflow:hidden;background:#EEF3FD">{inner}</div>'
                                f'<div style="font-size:28px;font-weight:900;margin-top:6px;color:#1B2440">{label}</div></div>')
    f_bar = col(zones + f'<div style="position:absolute;left:18px;right:18px;bottom:0;height:{px(hiss)};background:{colour};border-radius:8px 8px 0 0"></div>', "f")
    ee_bar = col(f'<div style="position:absolute;left:18px;right:18px;bottom:0;height:{px(1.0)};background:#2F6FE4;border-radius:8px 8px 0 0"></div>', "smile")
    return f'<div style="display:flex;gap:28px;justify-content:center;margin-top:16px" aria-label="The f sound should be softer than the smile after it">{f_bar}{ee_bar}</div>'


def lamps_html(check) -> str:
    """/tʃ/ as two lamps: "t" (the pop at the start) and "sh" (the hiss that follows). Green: right; yellow: nearly; red: not yet. The grey line is the numbers, for the testing phase."""
    if check is None:
        return ""
    lamp = lambda letter, level: (f'<div style="text-align:center"><div style="width:110px;height:110px;border-radius:50%;background:{MARK_COLOUR[level]};color:#fff;display:flex;'
                                  f'align-items:center;justify-content:center;font-size:44px;font-weight:900;box-shadow:inset 0 -6px 0 rgba(0,0,0,.18)">{letter}</div></div>')
    numbers = (f'<div style="margin-top:10px;font-size:12px;color:#8A96B0;text-align:center">pop {check.slope_db_ms:.1f} dB/ms (green from {affricate_check.SLOPE_OK_DB_MS:g}) · '
               f'hiss {check.hiss_ms:.0f} ms (green from {affricate_check.HISS_OK_MS:g})</div>')
    return (f'<div style="display:flex;gap:34px;justify-content:center;margin-top:18px" aria-label="The t pop and the sh hiss of ch">{lamp("t", check.pop)}{lamp("sh", check.hiss)}</div>' + numbers)


def panel(res: Result, phone: str, wav: bytes | None = None, scale: float = 1.0) -> str:
    """The result: a mark and label, the stars, the sound as a picture and the /ʃ/–/s/ line (for those two sounds), and the tip."""
    both = lambda en: escape(en) + (f' <span class="zh">{escape(zh.translate(en))}</span>' if zh.translate(en) else "")        # the English with its Chinese beside it
    if res.color is None:
        return f'<div class="rs-notice">{both(res.notice)}</div>'
    head = (f'<div class="rs-head"><div class="rs-mark" style="background:{MARK_COLOUR[res.color]}">{escape(res.mark)}</div>'
            f'<div><div class="rs-label">{both(res.label)}</div><div class="rs-msg">{both(res.message)}</div></div></div>')
    body = ""
    t = res.position
    if phone in ("s", "sh") and t is not None:
        goal = 1.0 if phone == "s" else 0.0
        picture = spectro.render(wav, phone, res.cog_hz, scale) if wav else None          # the sound drawn, with the target zone on it
        body = (f'<div style="margin-top:14px">{picture}</div>' if picture else "") + (
                f'<div style="margin-top:14px">{svg_img(tongue.mouth_svg(t, goal), "width:42%;height:auto;display:block;margin:0 auto")}</div>'
                f'<div style="margin-top:10px">{tongue.slider_html(t, goal)}</div>')
    earned = stars.stars(res.color, res.closeness)
    star_row = (f'<div class="rs-stars" aria-label="{earned} of 3 stars">' + "".join(
        f'<span class="{"on" if i < earned else ""}">★</span>' for i in range(stars.MAX_STARS)) + "</div>")
    again = ('<div class="rs-again">Let\'s practise again <span class="zh">再練習一次</span></div>' if earned == 0 else "")
    if phone == "f":
        body = bars_html(res.relamp_db)
    if phone == "tʃ":
        body = lamps_html(res.affricate)
    tip = f'<p class="rs-tip">{both(res.tip)}</p>' if res.tip else ""
    return head + star_row + again + body + tip
