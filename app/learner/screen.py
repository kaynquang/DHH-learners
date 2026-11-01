"""The learner's practice screen, built to match the design mockup (S mockup pdf.pdf): colours, sizes, spacing and radii are the mockup's."""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape

from .lessons import ACCENT, Lesson

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=Noto+Sans+TC:wght@400;500;700&display=swap');
:root {{ --accent: {ACCENT}; --ink: #1B2440; --ink2: #3A4664; --line: #D5DFF0; }}
.stApp {{ background: #F2F6FD; }}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"], footer {{ display: none !important; }}
.block-container {{ max-width: 1368px; padding: 28px 24px 36px !important; }}
.stApp, .stApp * {{ font-family: 'Nunito', 'Noto Sans TC', system-ui, sans-serif; }}
[data-testid="stHorizontalBlock"] {{ gap: 24px; align-items: stretch; }}
.zh {{ font-family: 'Noto Sans TC', sans-serif !important; }}
.ln-top {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; color: var(--ink); margin-bottom: 20px; }}
.ln-pills {{ display: flex; gap: 12px; flex-wrap: wrap; }}
.ln-pill {{ display: inline-flex; align-items: center; gap: 8px; min-height: 46px; padding: 0 20px; box-sizing: border-box; background: #FFF;
  border: 1.5px solid var(--line); border-radius: 999px; font-weight: 800; font-size: 16px; color: var(--ink); text-decoration: none; }}
.ln-progress {{ flex: 1 1 320px; max-width: 520px; display: flex; flex-direction: column; gap: 6px; }}
.ln-bar {{ width: 100%; height: 14px; border-radius: 999px; background: #DFE6F3; overflow: hidden; }}
.ln-bar > div {{ height: 100%; border-radius: 999px; background: var(--accent); }}
.ln-count {{ font-size: 14px; font-weight: 800; text-align: right; color: var(--ink); }}
.ln-count .zh {{ font-weight: 500; color: var(--ink2); }}
.ln-left {{ display: flex; flex-direction: column; gap: 20px; color: var(--ink); }}
.ln-wordcard {{ background: #F2FAEC; border: 1.5px solid #BFE3AE; border-radius: 24px; box-shadow: 0 4px 0 #BFE3AE; padding: 24px 28px;
  display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap; }}
.ln-fig {{ margin: 0; display: flex; flex-direction: column; align-items: center; gap: 10px; flex: 0 0 auto; }}
.ln-circle {{ width: 140px; height: 140px; border-radius: 50%; border: 5px solid var(--ink); box-sizing: border-box; display: flex;
  align-items: center; justify-content: center; }}
.ln-circle img {{ width: 104px; height: 104px; }}
.ln-cap {{ font-size: 14px; font-weight: 800; }}
.ln-cap .zh {{ font-weight: 500; }}
.ln-center {{ display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; min-width: 0; flex: 1 1 220px; }}
.ln-word {{ font-size: 88px; line-height: 0.95; font-weight: 900; letter-spacing: -1px; }}
.ln-word .hl {{ color: var(--accent); text-decoration: underline; text-decoration-thickness: 7px; text-underline-offset: 9px; }}
.ln-meaning {{ font-size: 28px; color: var(--ink2); margin-top: 10px; }}
.ln-sound {{ font-size: 17px; font-weight: 800; color: var(--accent); }}
.ln-sound .zh {{ font-weight: 500; }}
.ln-mouth {{ background: #FFF; border: 1.5px solid var(--line); border-radius: 24px; box-shadow: 0 4px 0 var(--line); padding: 22px;
  display: flex; flex-direction: column; gap: 16px; }}
.ln-h2 {{ margin: 0; text-align: center; font-size: 20px; font-weight: 800; color: var(--ink); }}
.ln-h2 .zh {{ font-weight: 500; color: var(--ink2); }}
.st-key-mouth {{ background: #FFF; border: 1.5px solid var(--line) !important; border-radius: 24px !important; box-shadow: 0 4px 0 var(--line); padding: 22px !important; gap: 16px; }}
.st-key-leftcol {{ gap: 20px; }}
.ln-mouth img {{ display: block; width: 100%; height: auto; border-radius: 16px; }}
.ln-checks {{ margin: 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }}
.ln-checks li {{ display: flex; gap: 10px; align-items: flex-start; background: #F6F9FE; border: 1.5px solid #E1E9F6; border-radius: 16px; padding: 12px; }}
.ln-checks img {{ width: 22px; height: 22px; flex: 0 0 22px; }}
.ln-checks span {{ font-size: 17px; font-weight: 800; line-height: 1.35; color: #0F1A3C; }}
.ln-checks .zh {{ font-weight: 700; color: #2F6FE4; }}
.ln-checks .py {{ font-weight: 400; color: var(--ink2); }}
.ln-missing {{ border: 2px dashed #B9C7E3; border-radius: 16px; color: #6B7896; font-size: 14px; font-weight: 700; display: flex; align-items: center;
  justify-content: center; text-align: center; padding: 10px; box-sizing: border-box; }}
"""

# The buttons that move between the eight sounds (not in the mockup): previous, one button per sound, next. Styled like the mockup's pills.
NAV_CSS = f"""
[data-testid="stIconMaterial"] {{ font-family: "Material Symbols Rounded" !important; }}
.st-key-nav {{ margin: -6px 0 18px; justify-content: center; gap: 10px; flex-wrap: wrap; }}
.st-key-nav button {{ min-height: 46px; min-width: 56px; border-radius: 999px; border: 1.5px solid var(--line); background: #fff; color: var(--ink); padding: 0 16px; }}
.st-key-nav button p {{ font-size: 18px; font-weight: 800; }}
.st-key-nav button:disabled {{ opacity: .4; }}
.st-key-nav button:hover {{ border-color: {ACCENT}; color: var(--ink); }}
.st-key-nav button[kind="primary"] {{ background: {ACCENT}; border-color: {ACCENT}; color: #fff; }}
.st-key-nav button[kind="primary"]:hover {{ color: #fff; }}
.st-key-nav .stButton {{ width: auto; }}
"""
CHECK_SVG = (f'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="{ACCENT}"/>'
             '<path d="M 7 12.5 L 10.5 16 L 17 8.5" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
BACK_SVG = ('<svg viewBox="0 0 24 24" style="width:18px;height:18px" aria-hidden="true"><path d="M 15 5 L 8 12 L 15 19" fill="none" '
            'stroke="#1B2440" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
STAR_SVG = ('<svg viewBox="0 0 24 24" style="width:20px;height:20px" aria-hidden="true"><polygon points="12,2 14.9,8.6 22,9.2 16.6,13.9 18.2,21 12,17.3 '
            '5.8,21 7.4,13.9 2,9.2 9.1,8.6" fill="#F5B400" stroke="#D99A00" stroke-width="1" stroke-linejoin="round"/></svg>')


def svg_img(svg: str, style: str = "") -> str:
    """An SVG as an <img> with a data URI: st.html strips inline <svg> elements, but keeps images."""
    svg = svg if "xmlns=" in svg else svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return f'<img alt="" style="{style}" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode("utf-8")).decode("ascii")}">'


def zh(text: str) -> str:
    return f'<span class="zh">{escape(text)}</span>'


def top_bar(index: int, total: int, stars: int = 0) -> str:
    """Map button (nothing to go back to yet), star count, and the progress through the words."""
    return f"""<div class="ln-top">
<div class="ln-pills">
<a class="ln-pill" href="?page=map" target="_self">{svg_img(BACK_SVG, "width:18px;height:18px")}<span>Map {zh('地圖')}</span></a>
<span class="ln-pill">{svg_img(STAR_SVG, "width:20px;height:20px")}<span>{stars}</span></span>
</div>
<div class="ln-progress">
<div class="ln-bar" role="progressbar" aria-valuenow="{index}" aria-valuemin="0" aria-valuemax="{total}" aria-label="Word {index} of {total}"><div style="width:{100 * index / total:.0f}%"></div></div>
<div class="ln-count">Word {index} / {total} {zh(f'第 {index} 個字')}</div>
</div>
</div>"""


def _missing(what: str, width: str = "", height: str = "") -> str:
    return f'<div class="ln-missing" style="{width}{height}">{escape(what)} to be added</div>'


def _word_html(lesson: Lesson) -> str:
    w, hl = lesson.word, lesson.highlight
    if hl and w.startswith(hl):
        return f'<span class="hl">{escape(hl)}</span>{escape(w[len(hl):])}'
    return escape(w)


def _figure(svg: str | None, background: str, caption: str, what: str) -> str:
    inner = svg_img(svg) if svg else '<span style="font-size:13px;font-weight:700;color:#6B7896;text-align:center">to be added</span>'
    return (f'<figure class="ln-fig"><div class="ln-circle{"" if svg else " empty"}" style="background:{background}">{inner}</div>'
            f'<figcaption class="ln-cap">{caption}</figcaption></figure>')


@lru_cache(maxsize=8)
def _image_uri(path: str) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode("ascii")


def word_card(lesson: Lesson) -> str:
    hiss_cap = (f'<span style="color:#2F6B2C">{escape(lesson.hiss_caption[0])} {zh(lesson.hiss_caption[1])}</span>' if lesson.hiss_caption
                else '<span style="color:#2F6B2C">Sound picture</span>')
    meaning = f'<div class="ln-meaning zh">{escape(lesson.meaning_zh)}</div>' if lesson.meaning_zh else '<div class="ln-meaning zh">&nbsp;</div>'
    return f"""<div class="ln-wordcard">
{_figure(lesson.hiss_svg, '#A6DC8F', hiss_cap, 'Sound picture')}
<div class="ln-center">
<div class="ln-word" data-n="{min(len(lesson.word), 5)}">{_word_html(lesson)}</div>
{meaning}
<div class="ln-sound">Sound {escape(lesson.label)} {zh('目標音')}</div>
</div>
{_figure(lesson.meaning_svg, '#CFE3FF', f'Meaning {zh("字義")}', 'Meaning picture')}
</div>"""


def mouth_title() -> str:
    return f"<h2 class=\"ln-h2\">Watch the mouth {zh('看嘴巴怎麼動')}</h2>"


def checks_html(lesson: Lesson) -> str:
    if not lesson.checks:
        return _missing("Mouth tips", height="min-height:90px;")
    items = "".join(
        f'<li>{svg_img(CHECK_SVG)}<span>{escape(en)}<br>{zh(zh_text)}' + (f'<br><span class="py">{escape(py[0])}</span>' if py else "") + "</span></li>"
        for en, zh_text, *py in lesson.checks)
    return f'<ul class="ln-checks">{items}</ul>'


def mouth_card(lesson: Lesson) -> str:
    """The still picture version of the mouth card (lessons without motions)."""
    if lesson.mouth_image and lesson.mouth_image.exists():
        picture = f'<img src="{_image_uri(str(lesson.mouth_image))}" alt="How to say {escape(lesson.label)}">'
    else:
        picture = _missing("Mouth picture", height="min-height:260px;")
    return f'<div class="ln-mouth">{mouth_title()}{picture}{checks_html(lesson)}</div>'


def left_column(lesson: Lesson) -> str:
    return f'<div class="ln-left">{word_card(lesson)}{mouth_card(lesson)}</div>'
