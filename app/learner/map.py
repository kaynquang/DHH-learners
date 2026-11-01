"""Map screen "Sound Islands", drawn to the Map mockup (1366 x 768): one island per sound, opened with a tap, free order.

The whole map is one 1366 x 768 picture area that is scaled to fit the window height, so nothing scrolls and nothing overlaps at any size
(every length below is a pixel of the mockup, turned into a container-relative unit by u()). Island pictures are small drawings made here.

Nothing about progress is recorded yet, so every island reads "not started" with empty stars: the star rule and the ordering rule are
still to be decided by the content owner (shown as dashed "to be added" notes, as in the mockup). Words and Chinese meanings are the ones
printed on the mockup.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from urllib.parse import quote

from fricative.calibrated import last_profile, list_profiles, remember_profile

from . import stars
from .lessons import ACCENT, LESSONS, ORDER
from .screen import svg_img

W, H = 1366, 768


def u(px: float) -> str:
    """A mockup pixel as a length relative to the map width."""
    return f"{px / W * 100:.3f}cqw"


COLOR = {"see": "#FFD6E0", "she": "#FFE0B0", "fee": "#D9F3E3", "me": "#F8DFD6", "bee": "#FFF3C4", "pea": "#E1F2D2", "knee": "#DCE8FB",
         "cheat": "#E6DEF5", "sound": "#CFE6FB"}
# island centre x, top of the island picture (mockup pixels); the label card sits 132 px below the top
POS = {"sound": (160, 122), "see": (420, 120), "she": (680, 120), "fee": (960, 120),
       "me": (420, 345), "bee": (680, 345), "pea": (960, 345), "knee": (160, 505), "cheat": (600, 555)}
CARD_W = {"see": 176}
ISLAND_W, CARD_H, CARD_DY = 212, 56, 132

from .pictures import ART, MEANING, _INK, _OUT

def _art(key: str) -> str:
    return svg_img(f'<svg viewBox="0 0 100 100">{ART[key]}</svg>', "width:100%;height:100%;display:block")


CSS = f"""
.block-container {{ padding-bottom: 1rem !important; }}      /* the sky and the sea behind come from learner/sky.py, as on every page */
.mp-map {{ position: relative; width: min(100%, calc((100vh - 90px) * {W} / {H})); aspect-ratio: {W} / {H}; margin: 0 auto;
  container-type: inline-size; color: var(--ink); }}
.mp-map > * {{ position: absolute; }}
.mp-title {{ left: {u(28)}; top: {u(24)}; font-size: {u(31)}; font-weight: 900; line-height: 1.1; white-space: nowrap; }}
.mp-title b {{ color: {ACCENT}; }} .mp-title .zh {{ font-size: {u(24)}; font-weight: 700; color: var(--ink2); }}
.mp-sub {{ left: {u(28)}; top: {u(75)}; font-size: {u(15)}; font-weight: 800; color: var(--ink2); }}
.mp-home {{ left: {u(880)}; top: {u(34)}; width: {u(150)}; height: {u(46)}; box-sizing: border-box; display: flex; align-items: center; justify-content: center; background: #fff; border: 1.5px solid var(--line); border-radius: 999px; font-weight: 800; font-size: {u(16)}; color: var(--ink); text-decoration: none; box-shadow: 0 {u(3)} 0 var(--line); z-index: 20; }}
.mp-child {{ left: {u(1060)}; top: {u(34)}; width: {u(278)}; z-index: 20; }}
.mp-child summary {{ list-style: none; cursor: pointer; height: {u(46)}; box-sizing: border-box; display: flex; align-items: center; justify-content: center; gap: {u(10)};
  background: #fff; border: 1.5px solid var(--line); border-radius: 999px; font-weight: 800; font-size: {u(16)}; color: var(--ink);
  box-shadow: 0 {u(3)} 0 var(--line); white-space: nowrap; overflow: hidden; }}
.mp-child summary::-webkit-details-marker {{ display: none; }}
.mp-list {{ margin-top: {u(8)}; background: #fff; border: 1.5px solid var(--line); border-radius: {u(16)}; padding: {u(6)}; box-shadow: 0 {u(4)} 0 var(--line);
  display: flex; flex-direction: column; max-height: {u(300)}; overflow-y: auto; }}
.mp-list a {{ padding: {u(9)} {u(12)}; border-radius: {u(10)}; text-decoration: none; color: var(--ink); font-weight: 700; font-size: {u(15)}; }}
.mp-list a:hover {{ background: #EEF3FD; }} .mp-list a.on {{ background: #EAF1FF; font-weight: 900; }}
.mp-list a.add {{ color: {ACCENT}; font-weight: 800; border-top: 1.5px solid var(--line); border-radius: 0 0 {u(10)} {u(10)}; margin-top: {u(4)}; }}
.mp-trail {{ left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; }}
.mp-isle {{ width: {u(ISLAND_W)}; height: {u(CARD_DY + CARD_H)}; text-decoration: none; color: var(--ink); display: block; }}
.mp-isle > * {{ position: absolute; }}
.mp-isle:hover .mp-blob {{ transform: translateY({u(-4)}); }} .mp-isle:focus-visible {{ outline: 3px solid {ACCENT}; outline-offset: 4px; border-radius: 24px; }}
.mp-blob {{ left: {u(11)}; top: 0; width: {u(190)}; height: {u(118)}; border-radius: 50% 50% 46% 46% / 66% 66% 34% 34%; display: grid; place-items: center; transition: transform .15s; }}
.mp-blob > div {{ width: {u(64)}; height: {u(64)}; margin-top: {u(8)}; }}
.mp-base {{ left: {u(31)}; top: {u(104)}; width: {u(150)}; height: {u(22)}; border-radius: 50%; background: #F3E4BC; z-index: 0; }}
.mp-blob {{ z-index: 1; }} .mp-blob {{ box-shadow: 0 {u(-2)} 0 rgba(255,255,255,.3) inset; }}
.mp-card {{ top: {u(CARD_DY)}; height: {u(CARD_H)}; box-sizing: border-box; background: #fff; border-radius: {u(14)}; box-shadow: 0 {u(3)} 0 #D5DFF0, 0 0 0 1px #E1E9F6;
  text-align: center; display: flex; flex-direction: column; justify-content: center; gap: {u(2)}; z-index: 2; }}
.mp-name {{ font-size: {u(17)}; font-weight: 900; white-space: nowrap; line-height: 1.2; }} .mp-name em {{ font-style: normal; color: {ACCENT}; }}
.mp-name .zh {{ font-weight: 600; color: var(--ink2); font-size: {u(14)}; }}
.mp-row {{ display: flex; justify-content: center; align-items: center; gap: {u(6)}; font-size: {u(11)}; line-height: 1.2; }}
.mp-stars {{ color: #F2B705; letter-spacing: {u(1)}; font-size: {u(16)}; line-height: 1; }}
.mp-tag {{ border: 1.5px solid #C9D3E6; border-radius: 999px; padding: {u(1)} {u(8)}; font-weight: 800; color: var(--ink2); background: #F1F4FA; white-space: nowrap; font-size: {u(11)}; }}
.mp-tag.prog {{ border-color: #F2B705; background: #FFF6D6; color: #6B4E00; }} .mp-tag.done {{ border-color: #1FA45B; background: #EAF7EE; color: #17794A; }}
.mp-key {{ left: {u(1092)}; top: {u(325)}; width: {u(250)}; box-sizing: border-box; background: #fff; border: 1.5px solid #E1E9F6; border-radius: {u(20)};
  padding: {u(14)} {u(15)}; display: flex; flex-direction: column; gap: {u(7)}; box-shadow: 0 {u(3)} 0 #D5DFF0; }}
.mp-key h4 {{ margin: 0; font-size: {u(16)}; font-weight: 900; }} .mp-tags {{ display: flex; flex-wrap: wrap; gap: {u(6)}; }}
.mp-note {{ border: 2px dashed #C9D3E6; border-radius: {u(10)}; padding: {u(6)} {u(9)}; font-size: {u(11.5)}; font-weight: 700; color: var(--ink2); line-height: 1.3; }}
.mp-fin {{ left: {u(1092)}; top: {u(622)}; width: {u(250)}; height: {u(123)}; box-sizing: border-box; border: 2.5px dashed #AEBBD4; border-radius: {u(20)}; background: rgba(255,255,255,.4);
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; font-weight: 800; font-size: {u(13)}; line-height: 1.35; color: var(--ink2); padding: {u(8)}; }}
.mp-fin .zh {{ font-size: {u(15)}; color: var(--ink); }}
"""

# the dotted path from island to island (mockup pixels)
TRAIL = ("M 258 178 L 322 182", "M 500 238 C 540 250, 600 248, 640 240", "M 775 178 L 868 176", "M 1040 255 C 1050 300, 1042 340, 1035 372",
         "M 895 462 C 850 472, 810 462, 775 455", "M 585 412 L 520 412", "M 350 468 C 300 480, 260 500, 235 522", "M 265 662 C 360 655, 440 625, 500 620")


def _trail() -> str:
    paths = "".join(f'<path d="{d}"/>' for d in TRAIL)
    svg = (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><g fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" '
           f'stroke-dasharray="0.5 17">{paths}</g></svg>')
    return svg_img(svg, "").replace('style=""', 'class="mp-trail"')


def _isle(key: str, href: str, name_html: str, tags_html: str) -> str:
    cx, top = POS[key]
    cw = CARD_W.get(key, ISLAND_W)
    return (f'<a class="mp-isle" href="{href}" target="_self" style="left:{u(cx - ISLAND_W / 2)};top:{u(top)}">'
            f'<div class="mp-base"></div><div class="mp-blob" style="background:{COLOR[key]}"><div>{_art(key)}</div></div>'
            f'<div class="mp-card" style="left:{u((ISLAND_W - cw) / 2)};width:{u(cw)}"><div class="mp-name">{name_html}</div>'
            f'<div class="mp-row">{tags_html}</div></div></a>')


def render() -> None:
    st.html(f"<style>{CSS}</style>")
    names = list_profiles()
    picked = st.query_params.get("child")
    if picked in names:                                      # ?child=NAME from the list below: this child is the one playing now
        remember_profile(picked)
    if "child" in st.query_params:
        del st.query_params["child"]
    child = last_profile()
    progress = stars.load(child)
    items ="".join(f'<a href="?page=map&child={quote(n)}" target="_self"{" class=on" if n == child else ""}>{"✓ " if n == child else ""}{escape(n)}</a>'
                    for n in names)
    parts = [
        '<div class="mp-title"><b>Sound</b> Islands <span class="zh">聲音小島</span></div>',
        '<div class="mp-sub">Pick an island! 選一個小島！</div>',
        f'<details class="mp-child"><summary>🧒 {escape(child) if child else "Choose a child 選擇學生"} ▾</summary>'
        f'<div class="mp-list">{items}<a class="add" href="?page=sound" target="_self">＋ Add / record a child 新增或錄製學生</a></div></details>',
        '<a class="mp-home" href="?page=home" target="_self">🏠 Home 首頁</a>',
        _trail(),
        _isle("sound", "?page=sound", 'Sound check <span class="zh">聲音檢查</span>',
              '<span class="mp-tag">optional 可選</span><span>s · ʃ · f only</span>'),
    ]
    for w in ORDER:
        name = f'<em>{escape(LESSONS[w].label)}</em> {escape(w)} <span class="zh">{escape(MEANING.get(w, ""))}</span>'
        best = progress.get(w, {}).get("best", 0)
        state = stars.status(progress, w)
        tag = {"not started": '<span class="mp-tag">not started 未開始</span>', "in progress": '<span class="mp-tag prog">in progress 進行中</span>',
               "done": '<span class="mp-tag done">done 完成 ✓</span>'}[state]
        parts.append(_isle(w, f"?word={w}", name, f'<span class="mp-stars">{"★" * best}{"☆" * (stars.MAX_STARS - best)}</span>{tag}'))
    parts.append('<div class="mp-key"><h4>Map key 圖例</h4><div class="mp-tags"><span class="mp-tag">not started 未開始</span>'
                 '<span class="mp-tag prog">in progress 進行中</span><span class="mp-tag done">done 完成 ✓</span></div>'
                 '<div class="mp-note">★ green 3 · yellow 2 or 1 · red 0 (practise again) · 綠3、黃2或1、紅0（再練習）</div>'
                 '<div class="mp-note">All islands open (free order) — ordering rule to be decided · 順序規則待定</div>'
                 '<div class="mp-note">“cheat” word may need replacing · 例詞可能需更換</div></div>')
    parts.append('<div class="mp-fin">🎉 End-of-lesson celebration &amp; next lesson<span class="zh">課程結束慶祝／下一課</span>— to be added 待補 —</div>')
    st.html(f'<div class="mp-map">{"".join(parts)}</div>')
