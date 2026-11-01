"""The home page "SeeSound", drawn to the user's second home mockup (assets/mockups/home_v2_path.png, made by an image bot from the assistant's brief; the first one is home_v1_cards.png):
the logo and the blue mascot with a big "Continue" button on the left; the PATH of the eight sounds on the right (done = green check, the next one = big blue with "START", the others = grey, stars under each);
a banner at the top with the child, the stars and "Teachers"; "Sound Check" and "My Stars" as two small buttons at the bottom right.
With no child saved yet (the first time the app is opened) the mascot welcomes the child and the big button leads to Sound Check; "Skip for now" goes to the map.
The mascot, the logo, the node pictures and the texts are the assistant's (the mockup's pictures are not used): to be reviewed. The mockup's "3 days" chip is not drawn: nothing counts days.
"My Stars" has no page of its own: it opens the map. "Teachers" opens the Dev app (port 8501 of this computer).
"""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from fricative.calibrated import last_profile, list_profiles, load_room, remember_profile

from . import stars
from .lessons import LESSONS, ORDER
from .pictures import ART, MEANING
from .screen import svg_img

MASCOT_PNG = Path(__file__).resolve().parent / "assets" / "mascot_wave.png"      # the blue mascot as the image bot drew it, cut out of its home mockup (home_v2_path.png)
TEACHER_URL = "http://localhost:8501"          # the Dev app, run beside this one by start_apps.ps1
_INK = "#1B2440"
W, H = 1024, 572                                # the mockup's pixels: the stage is drawn on this grid and scaled


@lru_cache(maxsize=1)
def _mascot() -> str:
    return '<img src="data:image/png;base64,' + base64.b64encode(MASCOT_PNG.read_bytes()).decode('ascii') + '" alt="">'


def u(px: float) -> str:
    return f"{px / W * 100:.3f}cqw"


def _svg(inner: str, box: str = "0 0 100 100") -> str:
    return f'<svg viewBox="{box}" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _ic(svg: str, style: str = "") -> str:
    return svg_img(svg, style)


S = f'stroke="{_INK}" stroke-linecap="round" stroke-linejoin="round"'
EYE = _svg(f'<path d="M 8 56 C 28 28, 72 28, 92 56 C 72 84, 28 84, 8 56 Z" fill="#fff" {S} stroke-width="5"/><circle cx="50" cy="56" r="17" fill="{_INK}"/><circle cx="56" cy="50" r="5.5" fill="#fff"/>'
           f'<path d="M 28 30 L 22 18 M 50 24 L 50 10 M 72 30 L 78 18" fill="none" {S} stroke-width="5"/>')
AVATAR = _svg(f'<circle cx="50" cy="50" r="48" fill="#BFE3AE"/><circle cx="50" cy="54" r="26" fill="#FFD9B8" {S} stroke-width="4"/><path d="M 24 50 C 22 24, 78 20, 76 50 C 66 38, 40 36, 24 50 Z" fill="#7A4A2B" {S} stroke-width="4"/>'
              f'<circle cx="41" cy="56" r="3" fill="{_INK}"/><circle cx="59" cy="56" r="3" fill="{_INK}"/><path d="M 40 66 C 46 72 54 72 60 66" fill="none" {S} stroke-width="3.5"/>')
ADD = _svg(f'<circle cx="50" cy="50" r="44" fill="#fff" stroke="#fff" stroke-width="2"/><circle cx="50" cy="50" r="40" fill="none" stroke="#8CA2C8" stroke-width="5" stroke-dasharray="8 8"/><path d="M 50 32 L 50 68 M 32 50 L 68 50" stroke="#2F6FE4" stroke-width="8" stroke-linecap="round"/>')
STAR = _svg(f'<polygon points="50,8 62,36 92,38 69,58 77,88 50,72 23,88 31,58 8,38 38,36" fill="#FFC800" {S} stroke-width="6"/>')
GEAR = _svg(f'<circle cx="50" cy="50" r="22" fill="none" stroke="#fff" stroke-width="7"/><circle cx="50" cy="50" r="8" fill="none" stroke="#fff" stroke-width="6"/>'
            + "".join(f'<line x1="{50 + 30 * c:.1f}" y1="{50 + 30 * s:.1f}" x2="{50 + 41 * c:.1f}" y2="{50 + 41 * s:.1f}" stroke="#fff" stroke-width="9" stroke-linecap="round"/>'
                      for c, s in ((1, 0), (.707, .707), (0, 1), (-.707, .707), (-1, 0), (-.707, -.707), (0, -1), (.707, -.707))))
MIC = _svg(f'<rect x="38" y="14" width="24" height="42" rx="12" fill="#fff" {S} stroke-width="6"/><path d="M 28 46 C 28 66, 72 66, 72 46 M 50 66 L 50 82 M 36 84 L 64 84" fill="none" {S} stroke-width="6"/>')
ISLAND = _svg(f'<path d="M 50 74 C 50 60, 52 50, 56 40" fill="none" {S} stroke-width="7"/><path d="M 56 40 C 44 26, 28 30, 22 40 M 56 40 C 62 24, 80 24, 86 36 M 56 40 C 48 42, 38 50, 34 58 M 56 40 C 64 44, 72 52, 74 60" fill="none" {S} stroke-width="7"/>'
              f'<path d="M 12 84 C 22 70, 78 70, 88 84 Z" fill="#F0B65A" {S} stroke-width="5"/>')
FLAG = _svg(f'<path d="M 30 94 L 30 10" fill="none" {S} stroke-width="7"/><path d="M 30 12 L 84 26 L 30 44 Z" fill="#8FC2F2" {S} stroke-width="6"/><ellipse cx="30" cy="94" rx="22" ry="6" fill="#4FA85A" {S} stroke-width="4"/>')
CHECK = _svg('<path d="M 22 54 L 42 74 L 80 28" fill="none" stroke="#1FA45B" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>')
# the sounds in the order of the app, as the centres of the nodes on the mockup's 1024 x 572 grid
POS = {"see": (523, 418), "she": (445, 258), "fee": (598, 165), "pea": (770, 190), "bee": (918, 163), "me": (918, 304), "knee": (787, 345), "cheat": (662, 292)}      # a loop in the order of the app (see, she, fee, pea, bee, me, knee, cheat): the first three are where the mockup has them


def _trail() -> str:
    pts = [POS[w] for w in ORDER]
    d = f"M {pts[0][0]} {pts[0][1]}"
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        d += f" Q {(x0 + x1) / 2 + (28 if i % 2 else -28)} {(y0 + y1) / 2 + (-18 if i % 2 else 18)} {x1} {y1}"
    svg = f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><path d="{d}" fill="none" stroke="{_INK}" stroke-width="5" stroke-linecap="round" stroke-dasharray="0.5 12"/></svg>'
    return svg_img(svg, "").replace('style=""', 'class="hm-trail"')


CSS = f"""
:root {{ --sw: min(100vw, calc(100vh * {W} / {H})); }}                                    /* the width of the picture on the screen: the whole window when it can, else as wide as the window is high */
.block-container {{ max-width: none !important; padding: 0 !important; }}
.hm-bgfix {{ position: fixed; left: 0; top: 0; width: 100vw; height: 100vh; z-index: 0; background: #8FCDE8 url(/app/static/home_bg.jpg) center top / calc(3 * var(--sw)) auto no-repeat; }}      /* the bot's picture IS the background, not a box on it */
.hm {{ position: relative; z-index: 1; width: var(--sw); margin: 0 auto; container-type: inline-size; color: var(--ink); }}
.hm a {{ color: inherit; text-decoration: none; }}
.hm-stage {{ position: relative; width: 100%; aspect-ratio: {W} / {H}; }}
.hm-stage > * {{ position: absolute; }}
.hm-eye img, .hm-mascot img, .hm-child .av img {{ width: 100%; height: 100%; display: block; }}
.hm-eye, .hm-word, .hm-tag, .hm-hero, .hm-mascot, .hm-foot {{ display: none; }}      /* drawn in the picture; shown again only on a narrow screen, where the picture is not used */
.hm-eye {{ left: {u(128)}; top: {u(26)}; width: {u(64)}; height: {u(52)}; }}
.hm-word {{ left: {u(36)}; top: {u(76)}; font-size: {u(64)}; font-weight: 900; letter-spacing: -2px; line-height: 1.05; white-space: nowrap; }} .hm-word i {{ font-style: normal; color: #2F6FE4; }}
.hm-tag {{ left: {u(42)}; top: {u(150)}; font-size: {u(21)}; font-weight: 800; line-height: 1.25; }} .hm-tag span {{ display: block; }}
.hm-hero {{ left: {u(34)}; top: {u(262)}; width: {u(300)}; height: {u(276)}; box-sizing: border-box; background: #FBF3DC; border: 3px solid {_INK}; border-radius: {u(22)}; z-index: 1; box-shadow: {u(6)} {u(7)} 0 rgba(27,36,64,.14); }}
.hm-mascot {{ left: {u(100)}; top: {u(238)}; width: {u(186)}; z-index: 4; pointer-events: none; }} .hm-mascot img {{ height: auto; }}
.hm-bubble {{ left: {u(268)}; top: {u(184)}; width: {u(150)}; box-sizing: border-box; padding: {u(12)} {u(14)}; background: #fff; border: 3px solid {_INK}; border-radius: {u(40)}; font-weight: 900; font-size: {u(14)}; line-height: 1.3; text-align: center; z-index: 5; }}
.hm-bubble::after {{ content: ""; position: absolute; left: {u(-10)}; bottom: {u(14)}; width: {u(18)}; height: {u(18)}; background: #fff; border-left: 3px solid {_INK}; border-bottom: 3px solid {_INK}; transform: rotate(45deg) skew(12deg, 12deg); }}
.hm-go {{ left: {u(62)}; top: {u(437)}; width: {u(244)}; height: {u(64)}; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border-radius: {u(14)}; background: #2F6FE4; color: #fff !important;
  border: 3px solid {_INK}; box-shadow: 0 {u(6)} 0 #1B3E8F; font-size: {u(27)}; font-weight: 900; z-index: 3; transition: transform .12s; }}
.hm-go:hover {{ transform: translateY({u(-3)}); }} .hm-go:active {{ transform: translateY({u(3)}); box-shadow: 0 {u(2)} 0 #1B3E8F; }}
.hm-next {{ left: {u(62)}; top: {u(513)}; width: {u(244)}; text-align: center; font-size: {u(15)}; font-weight: 800; z-index: 3; }} .hm-next a {{ text-decoration: underline; text-underline-offset: 3px; }}
.hm-banner {{ left: {u(352)}; top: {u(4)}; width: {u(664)}; height: {u(60)}; box-sizing: border-box; display: flex; align-items: center; gap: {u(14)}; padding: 0 {u(6)} 0 {u(8)}; color: #fff; z-index: 6; }}
.hm-child {{ position: relative; }} .hm-child summary {{ list-style: none; cursor: pointer; display: flex; align-items: center; gap: {u(10)}; font-weight: 900; font-size: {u(22)}; white-space: nowrap; }}
.hm-child summary::-webkit-details-marker {{ display: none; }} .hm-child .av {{ width: {u(46)}; height: {u(46)}; border-radius: 50%; border: 3px solid #fff; overflow: hidden; background: #fff; flex: 0 0 auto; }}
.hm-child .small {{ font-size: {u(16)}; font-weight: 800; }}
.hm-list {{ position: absolute; left: 0; top: {u(58)}; min-width: {u(260)}; background: #fff; border: 3px solid {_INK}; border-radius: {u(16)}; padding: {u(6)}; display: flex; flex-direction: column; max-height: {u(260)}; overflow-y: auto; color: var(--ink); z-index: 20; }}
.hm-list a {{ padding: {u(9)} {u(12)}; border-radius: {u(10)}; font-weight: 800; font-size: {u(16)}; }} .hm-list a:hover {{ background: #EEF3FD; }} .hm-list a.on {{ background: #EAF1FF; font-weight: 900; }}
.hm-list a.add {{ color: #2F6FE4; border-top: 1.5px solid var(--line); border-radius: 0 0 {u(10)} {u(10)}; margin-top: {u(4)}; }}
.hm-stars {{ display: flex; align-items: center; gap: {u(8)}; font-size: {u(26)}; font-weight: 900; color: #FFC800; }} .hm-stars img {{ width: {u(30)}; height: {u(30)}; }}
.hm-teach {{ margin-left: auto; display: flex; align-items: center; gap: {u(12)}; }}
.hm-tbtn {{ background: #2F6FE4; border: 3px solid #fff; border-radius: {u(12)}; padding: {u(6)} {u(15)}; font-size: {u(19)}; font-weight: 900; color: #fff !important; white-space: nowrap; }}
.hm-teach img {{ width: {u(32)}; height: {u(32)}; display: block; }}
.hm-path {{ left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; }}
.hm-trail {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; }}
.hm-node {{ position: absolute; transform: translate(-50%, {u(-47)}); width: {u(110)}; display: flex; flex-direction: column; align-items: center; pointer-events: auto; text-align: center; }}
.hm-node .c {{ width: {u(94)}; height: {u(94)}; border-radius: 50%; box-sizing: border-box; border: 4px solid #7C8AA6; background: #C9D3E6; display: grid; place-items: center; padding: {u(15)}; transition: transform .12s; }}
.hm-node:hover .c {{ transform: scale(1.06); }} .hm-node:focus-visible {{ outline: 3px solid #2F6FE4; outline-offset: 6px; border-radius: 18px; }}
.hm-node .c img {{ width: 100%; height: 100%; display: block; filter: grayscale(1) opacity(.5); }}
.hm-node .l {{ margin-top: {u(7)}; font-size: {u(17)}; font-weight: 900; white-space: nowrap; background: rgba(255,255,255,.7); padding: 0 {u(6)}; border-radius: 8px; }} .hm-node .l .zh {{ font-weight: 700; color: var(--ink2); }}
.hm-node .s {{ margin-top: {u(2)}; font-size: {u(19)}; color: #FFC800; letter-spacing: 1px; line-height: 1; -webkit-text-stroke: .6px {_INK}; min-height: {u(19)}; }}
.hm-node.done .c {{ background: #fff; border-color: #1FA45B; border-width: 5px; padding: {u(8)}; }} .hm-node.done .c img {{ filter: none; }}
.hm-node.now {{ z-index: 5; width: {u(160)}; transform: translate(-50%, {u(-68)}); }} .hm-node.now .c {{ width: {u(136)}; height: {u(136)}; background: #2F6FE4; border: 5px solid {_INK}; padding: {u(20)}; box-shadow: 0 0 0 {u(8)} rgba(47,111,228,.25), 0 0 0 {u(16)} rgba(47,111,228,.12); animation: hm-pulse 1.8s ease-in-out infinite; }}
.hm-node.now .c img {{ filter: none; background: #fff; border-radius: 50%; padding: {u(7)}; box-sizing: border-box; }} .hm-node.now .l {{ font-size: {u(22)}; }}
.hm-node.part .c {{ border-color: #F5B400; }}
.hm-start {{ position: absolute; top: {u(-58)}; left: 50%; transform: translateX(-50%); background: #5FA2F5; color: #fff; border: 3px solid {_INK}; border-radius: {u(18)}; padding: {u(4)} {u(16)}; font-weight: 900; font-size: {u(18)}; line-height: 1.1; white-space: nowrap; }}
.hm-start::after {{ content: ""; position: absolute; left: 50%; bottom: {u(-9)}; width: {u(14)}; height: {u(14)}; background: #5FA2F5; border-right: 3px solid {_INK}; border-bottom: 3px solid {_INK}; transform: translateX(-50%) rotate(45deg); }}
@keyframes hm-pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.04); }} }}
@media (prefers-reduced-motion: reduce) {{ .hm-node.now .c {{ animation: none; }} }}
.hm-quick {{ top: {u(466)}; display: flex; align-items: center; gap: {u(10)}; height: {u(64)}; box-sizing: border-box; padding: 0 {u(16)}; background: #FBF3DC; border: 3px solid {_INK}; border-radius: {u(16)}; font-weight: 900; font-size: {u(19)}; line-height: 1.15; z-index: 4;
  box-shadow: 0 {u(4)} 0 rgba(27,36,64,.2); }} .hm-quick img {{ width: {u(32)}; height: {u(32)}; }} .hm-quick small {{ display: block; font-size: {u(16)}; font-weight: 800; }}
.hm-q1 {{ left: {u(622)}; width: {u(212)}; }} .hm-q2 {{ left: {u(844)}; width: {u(172)}; }}
.hm-pill {{ position: absolute; right: {u(10)}; top: {u(-16)}; background: #1FA45B; color: #fff; border-radius: 999px; padding: {u(1)} {u(10)}; font-size: {u(13)}; font-weight: 900; }}
.hm-foot {{ font-weight: 800; }}
.hm-first .hm-path .hm-node.now .c {{ background: #fff; }}
.hm-go.two {{ top: {u(437)}; height: {u(70)}; font-size: {u(25)}; line-height: 1.1; text-align: center; }} .hm-go.two small {{ display: block; white-space: nowrap; font-size: {u(12)}; font-weight: 800; margin-top: {u(3)}; opacity: .95; }}
.hm-steps {{ left: {u(600)}; top: {u(458)}; width: {u(418)}; height: {u(74)}; box-sizing: border-box; display: flex; gap: {u(8)}; padding: {u(6)}; background: #FBF3DC; border: 3px solid {_INK}; border-radius: {u(18)}; z-index: 4; }}
.hm-step {{ flex: 1; display: flex; align-items: center; gap: {u(6)}; padding: 0 {u(8)}; border-radius: {u(14)}; font-weight: 900; font-size: {u(14)}; line-height: 1.1; position: relative; }}
.hm-step b {{ position: absolute; left: {u(-2)}; top: {u(-12)}; width: {u(24)}; height: {u(24)}; border-radius: 50%; background: #8CA2C8; color: #fff; display: grid; place-items: center; font-size: {u(14)}; border: 2px solid {_INK}; }}
.hm-step small {{ display: block; font-size: {u(14)}; font-weight: 800; }} .hm-step img {{ width: {u(28)}; height: {u(28)}; flex: 0 0 auto; }}
.hm-step.on {{ background: #fff; box-shadow: 0 0 0 {u(3)} #2F6FE4; }} .hm-step.on b {{ background: #2F6FE4; }}
.hm-deco {{ z-index: 1; pointer-events: none; }} .hm-deco img {{ width: 100%; height: 100%; display: block; }}
.hm-skip {{ left: {u(62)}; top: {u(513)}; width: {u(244)}; text-align: center; font-size: {u(15)}; font-weight: 800; z-index: 3; text-decoration: underline; text-underline-offset: 3px; }}
.hm-hot {{ position: absolute; display: block; z-index: 8; border-radius: {u(18)}; transition: background .12s; }}
.hm-hot:hover {{ background: rgba(255,255,255,.16); }} .hm-hot:focus-visible {{ outline: 3px solid #2F6FE4; outline-offset: 2px; }}
.hm-pick {{ position: absolute; z-index: 9; }} .hm-pick summary {{ display: block; width: 100%; height: 100%; list-style: none; cursor: pointer; border-radius: {u(18)}; }}
.hm-pick summary::-webkit-details-marker {{ display: none; }} .hm-pick summary:hover {{ background: rgba(255,255,255,.16); }} .hm-pick .hm-list {{ top: 100%; }}
.hm-show-hot .hm-hot, .hm-show-hot .hm-pick {{ outline: 2px dashed #E5484D; }}                                   /* ?hot=1: show the tap areas (to check them) */
@media (min-width: 861px) {{ .hm-stage > :not(.hm-hot):not(.hm-pick) {{ display: none !important; }} }}          /* on a computer: only the picture and its tap areas */
@media (max-width: 860px) {{
  .hm-hot, .hm-pick {{ display: none !important; }}
  .hm-bgfix {{ display: none; }} .block-container {{ padding: 12px 14px 0 !important; }} .hm-word, .hm-tag, .hm-mascot, .hm-foot {{ display: block; }} .hm {{ width: 100%; }} .hm-stage {{ aspect-ratio: auto; display: flex; flex-direction: column; gap: 14px; padding-bottom: 60px; }}
  .hm-stage > *, .hm-node {{ position: static !important; transform: none !important; }}
  .hm-trail, .hm-eye {{ display: none; }} .hm-banner {{ background: #2B4C8C; }} .hm-banner {{ width: auto; border-radius: 18px; flex-wrap: wrap; height: auto; padding: 12px 16px; gap: 10px 14px; }}
  .hm-banner * {{ font-size: 17px !important; }} .hm-child .av {{ width: 40px; height: 40px; }} .hm-stars img, .hm-gear {{ width: 26px; height: 26px; }}
  .hm-word {{ font-size: 54px; }} .hm-tag {{ font-size: 19px; }}
  .hm-hero {{ display: none; }} .hm-banner {{ order: -1; }} .hm-mascot, .hm-bubble {{ margin: 0 auto; }} .hm-first .hm-bubble {{ width: auto; font-size: 16px; }}`n  .hm-hero-x {{ height: auto; display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; }}
  .hm-hero > * {{ position: static !important; }} .hm-mascot {{ width: 130px; height: 154px; }} .hm-bubble {{ width: auto; font-size: 16px; }}
  .hm-go {{ width: 100%; height: 64px; font-size: 26px; }} .hm-next, .hm-skip {{ width: auto; font-size: 16px; }}
  .hm-path {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 22px 8px; padding-top: 50px; }} .hm-node, .hm-node.now {{ width: auto; }}
  .hm-node .c {{ width: 92px; height: 92px; }} .hm-node.now .c {{ width: 110px; height: 110px; }} .hm-node .l, .hm-node.now .l {{ font-size: 17px; }} .hm-node .s {{ font-size: 20px; min-height: 20px; }}
  .hm-start {{ top: -46px; font-size: 16px; }} .hm-quick, .hm-q1, .hm-q2 {{ width: auto; height: auto; min-height: 56px; padding: 10px 14px; font-size: 18px; }}
  .hm-pill {{ position: static !important; margin-left: 6px; }} .hm-quick img {{ width: 28px; height: 28px; }} .hm-quick small {{ font-size: 15px; }}
  .hm-foot {{ background: rgba(27,36,64,.88); color: #fff; position: static !important; height: auto; padding: 8px 12px; font-size: 12px; justify-content: center; text-align: center; border-radius: 10px; }}
}}
"""


def _hills() -> str:
    svg = (f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
           f'<path d="M 0 430 C 90 380 220 400 330 470 C 410 520 470 540 520 548 L 0 548 Z" fill="#4FA85A" stroke="{_INK}" stroke-width="3"/>'
           f'<path d="M 600 548 C 700 500 860 440 1024 430 L 1024 548 Z" fill="#6BBE5F" stroke="{_INK}" stroke-width="3"/>'
           f'<path d="M 360 548 C 420 520 520 515 580 548 Z" fill="#8FCDE8" stroke="{_INK}" stroke-width="3"/></svg>')
    return f'<div class="hm-hills">{_ic(svg, "width:100%;height:100%;display:block")}</div>'


def render() -> None:
    st.html(f"<style>{CSS}</style>")
    names = list_profiles()
    picked = st.query_params.get("child")
    if picked in names:                                      # ?child=NAME from the list: this child is the one playing now
        remember_profile(picked)
    if "child" in st.query_params:
        del st.query_params["child"]
    child = last_profile()
    first_time = not child                                   # no child saved yet: the very first time the app is opened
    progress = stars.load(child)
    state = {w: stars.status(progress, w) for w in ORDER}
    best = {w: progress.get(w, {}).get("best", 0) for w in ORDER}
    now = next((w for w in ORDER if state[w] != "done"), None)
    items = "".join(f'<a href="?page=home&child={quote(n)}" target="_self"{" class=on" if n == child else ""}>{"✓ " if n == child else ""}{escape(n)}</a>' for n in names)
    who = (f'<span class="av">{_ic(AVATAR)}</span><span>{escape(child)} ▾</span>' if child
           else f'<span class="av" style="border-color:transparent">{_ic(ADD)}</span><span>Add a child <span class="small">新增學生 ▾</span></span>')
    banner = (f'<div class="hm-banner"><details class="hm-child"><summary>{who}</summary><div class="hm-list">{items}'
              '<a class="add" href="?page=sound" target="_self">＋ Add / record a child 新增或錄製學生</a></div></details>'
              f'<span class="hm-stars">{_ic(STAR)}{stars.total(child)}</span>'
              f'<span class="hm-teach"><a class="hm-tbtn" href="{TEACHER_URL}" target="_blank" rel="noopener">Teachers 老師</a>{_ic(GEAR, "")}</span></div>')
    nodes = ""
    for w in ORDER:
        x, y = POS[w]
        cls = "done" if state[w] == "done" else "now" if w == now else "part" if best[w] else ""
        inner = _ic(CHECK) if state[w] == "done" else _ic(f'<svg viewBox="0 0 100 100">{ART[w]}</svg>')
        start = '<div class="hm-start">NEXT 下一個</div>' if (w == now and first_time) else '<div class="hm-start">START 開始</div>' if w == now else ""
        stars_row = "★" * best[w] if best[w] else ""
        nodes += (f'<a class="hm-node {cls}" href="?word={w}" target="_self" style="left:{u(x)};top:{u(y)}" aria-label="{escape(LESSONS[w].label)} {w}">{start}<div class="c">{inner}</div>'
                  f'<div class="l">{escape(LESSONS[w].label)} {w}</div><div class="s">{stars_row}</div></a>')
    target_word = now or ORDER[0]
    if first_time:
        hero = (f'<div class="hm-hero"></div><div class="hm-mascot">{_mascot()}</div><div class="hm-bubble">Hi! Let\'s see your sounds!<br>嗨！一起來看見你的聲音！</div>'
                '<a class="hm-go two" href="?page=sound" target="_self"><span>Let\'s start 開始吧<small>First, a quick sound check 先做聲音檢查</small></span></a>'
                '<a class="hm-skip" href="?page=map" target="_self">Skip for now 先跳過</a>')
    else:
        nxt = f'Next: {escape(LESSONS[target_word].label)} {target_word} {escape(MEANING[target_word])}' if now else 'All done! 全部完成'
        hero = (f'<div class="hm-hero"></div><div class="hm-mascot">{_mascot()}</div>'
                f'<a class="hm-go" href="{"?word=" + target_word if now else "?page=map"}" target="_self">Continue 繼續</a><div class="hm-next">{nxt}</div>')
    has_room = bool(child) and load_room(child) is not None
    quick = (f'<a class="hm-quick hm-q1" href="?page=sound" target="_self">{_ic(MIC)}<span>Sound Check<small>聲音檢查 {"✓" if has_room else ""}</small></span>'
             f'{"" if has_room else "<span class=hm-pill>first time 第一次</span>"}</a>'
             f'<a class="hm-quick hm-q2" href="?page=map" target="_self">{_ic(STAR)}<span>My Stars<small>我的星星</small></span></a>')
    if first_time:                                          # the mockup of the first time: three steps instead of the two buttons, a flag at the end of the path and a few stars
        step = lambda n, href, icon, en, zh_, on="": f'<a class="hm-step{on}" href="{href}" target="_self"><b>{n}</b>{_ic(icon)}<span>{en}<small>{zh_}</small></span></a>'
        quick = (f'<div class="hm-steps">{step(1, "?page=sound", MIC, "Sound check", "聲音檢查", " on")}{step(2, "?page=map", ISLAND, "Pick an island", "選一個小島")}'
                 f'{step(3, "?page=map", STAR, "Collect stars", "收集星星")}</div>'
                 f'<div class="hm-deco" style="left:{u(826)};top:{u(96)};width:{u(50)};height:{u(62)}">{_ic(FLAG)}</div>'
                 + "".join(f'<div class="hm-deco" style="left:{u(x)};top:{u(y)};width:{u(s)};height:{u(s)}">{_ic(_svg(f"<polygon points=\"50,6 62,36 94,38 69,58 78,92 50,73 22,92 31,58 6,38 38,36\" fill=\"{col}\" {S} stroke-width=\"7\"/>"))}</div>'
                           for x, y, s, col in ((836, 232, 30, "#FFC800"), (672, 388, 28, "#FFC800"), (968, 168, 26, "#9CC4F0"), (812, 268, 20, "#4FA85A"))))
    # On a computer the page IS the bot's picture, unchanged (learner/assets/mockups/make_home_pictures.py only sharpens it): the app adds invisible tap areas on its buttons
    # and nodes. Everything drawn above is only for a narrow screen, where the picture does not fit.
    hot = _hotspots(first_time, target_word if now else None, items)
    picture = "home_first.jpg" if first_time else "home_ret.jpg"
    st.html(f'<div class="hm-bgfix" style="background-image:url(/app/static/{picture})"></div>'
            f'<div class="hm{" hm-first" if first_time else ""}{" hm-show-hot" if st.query_params.get("hot") == "1" else ""}"><div class="hm-stage">'
            f'<div class="hm-eye">{_ic(EYE)}</div><div class="hm-word"><i>See</i>Sound</div><div class="hm-tag">See your sound<span>看見你的聲音</span></div>'
            f'{hero}{banner}<div class="hm-path">{_trail()}{nodes}</div>{quick}'
            f'<div class="hm-foot">made for learners who are deaf or hard of hearing 為聽障學習者設計</div>{hot}</div></div>')


# The tap areas on the two pictures, in the pictures' 1024 x 572 pixels: (x0, y0, x1, y1, where it goes, what it is). "NEXT" is filled in with the child's next word.
_NODES = {"see": (478, 375, 570, 490), "fee": (550, 120, 650, 235), "me": (550, 268, 650, 380), "bee": (715, 145, 815, 258), "pea": (740, 318, 835, 430),
          "knee": (870, 265, 965, 378), "cheat": (870, 118, 965, 232)}
HOT_RETURNING = [(380, 128, 525, 358, "?word=she", "/ʃ/ she"), *[(*b, f"?word={w}", w) for w, b in _NODES.items()],
                 (63, 428, 306, 503, "NEXT", "Continue 繼續"), (660, 466, 853, 532, "?page=sound", "Sound Check 聲音檢查"), (857, 466, 1003, 532, "?page=map", "My Stars 我的星星"),
                 (505, 18, 575, 62, "?page=map", "Stars 星星")]
HOT_FIRST = [(388, 190, 515, 320, "?word=she", "/ʃ/ she"), *[(*b, f"?word={w}", w) for w, b in _NODES.items() if w != "see"], (478, 345, 570, 490, "?word=see", "/s/ see"),
             (63, 425, 306, 500, "?page=sound", "Let's start 開始吧"), (105, 506, 262, 534, "?page=map", "Skip for now 先跳過"),
             (604, 458, 742, 532, "?page=sound", "Sound check 聲音檢查"), (746, 458, 876, 532, "?page=map", "Pick an island 選一個小島"), (880, 458, 1018, 532, "?page=map", "Collect stars 收集星星"),
             (358, 8, 560, 68, "?page=sound", "Add a child 新增學生")]
TEACHER_AREAS = [(812, 15, 962, 56, TEACHER_URL, "Teachers 老師"), (968, 17, 1010, 56, "?page=sound", "Sound Check 聲音檢查")]       # the gear opens the set-up page


def _hotspots(first_time: bool, next_word: str | None, items: str) -> str:
    out = ""
    for x0, y0, x1, y1, href, label in (HOT_FIRST if first_time else HOT_RETURNING) + TEACHER_AREAS:
        if href == "NEXT":
            href = f"?word={next_word}" if next_word else "?page=map"
        tab = ' target="_blank" rel="noopener"' if href.startswith("http") else ' target="_self"'
        out += (f'<a class="hm-hot" href="{href}"{tab} aria-label="{escape(label)}" title="{escape(label)}" '
                f'style="left:{u(x0)};top:{u(y0)};width:{u(x1 - x0)};height:{u(y1 - y0)}"></a>')
    if not first_time:                                      # the child's name in the banner opens the list of children
        out += (f'<details class="hm-pick" style="left:{u(358)};top:{u(10)};width:{u(134)};height:{u(58)}"><summary aria-label="Choose a child 選擇學生" title="Choose a child 選擇學生"></summary>'
                f'<div class="hm-list">{items}<a class="add" href="?page=sound" target="_self">＋ Add / record a child 新增或錄製學生</a></div></details>')
    return out
