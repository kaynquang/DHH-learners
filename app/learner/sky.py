"""The "sky" look of the lip lessons (/m/ /p/ /b/), from the user's second sky mockup (Bầu trời bản 2, 2026-10-31): a soft sky with a sun and clouds,
a strip of sea with far islands at the bottom, light see-through cards, a bigger word, a glow on the record button and on the progress bar.
It is only added to those pages; the other lessons keep the look of the first mockup. The background pictures are drawn here as SVG (nothing downloaded).
"""
from __future__ import annotations

import base64
import math


def _uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def _sky() -> str:
    sun_x, sun_y = 480, 6
    rays = "".join(
        f'<line x1="{sun_x + 66 * math.cos(math.radians(a)):.1f}" y1="{sun_y + 66 * math.sin(math.radians(a)):.1f}" '
        f'x2="{sun_x + 88 * math.cos(math.radians(a)):.1f}" y2="{sun_y + 88 * math.sin(math.radians(a)):.1f}" stroke="#FFD84A" stroke-width="5" stroke-linecap="round"/>'
        for a in (0, 30, 60, 90, 120, 150, 180))
    cloud = lambda x, y, s: (f'<g transform="translate({x} {y}) scale({s})"><ellipse cx="0" cy="0" rx="120" ry="38"/><ellipse cx="-40" cy="-30" rx="50" ry="42"/>'
                             '<ellipse cx="30" cy="-44" rx="62" ry="52"/><ellipse cx="80" cy="-14" rx="46" ry="34"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1366 768" preserveAspectRatio="xMidYMin slice">'
            '<defs><radialGradient id="g" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFEFA0" stop-opacity=".95"/><stop offset="1" stop-color="#FFEFA0" stop-opacity="0"/></radialGradient>'
            '<filter id="b" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="7"/></filter></defs>'
            f'<circle cx="{sun_x}" cy="{sun_y}" r="230" fill="url(#g)"/>{rays}<circle cx="{sun_x}" cy="{sun_y}" r="48" fill="#FFD84A"/>'
            f'<g fill="#fff" opacity=".82" filter="url(#b)">{cloud(10, 440, 1.0)}{cloud(1370, 190, 1.15)}{cloud(1380, 760, 1.0)}</g></svg>')


def _sea() -> str:
    hill = lambda x, w, h: f'<ellipse cx="{x}" cy="84" rx="{w}" ry="{h}" fill="#CFE8BE"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1366 130" preserveAspectRatio="none">'
            f'{hill(190, 120, 22)}{hill(680, 80, 12)}{hill(1130, 130, 24)}'
            '<path d="M0 78 C 150 66 260 92 420 80 S 700 68 860 82 S 1160 94 1366 74 L1366 130 L0 130 Z" fill="#B9E0F2"/>'
            '<path d="M0 100 C 170 88 290 112 470 102 S 780 90 960 104 S 1210 112 1366 96 L1366 130 L0 130 Z" fill="#8FCDE8"/></svg>')


CARD = "background: rgba(255,255,255,.80); border: 1.5px solid rgba(255,255,255,.95); border-radius: 28px; box-shadow: 0 14px 34px rgba(70,120,200,.13);"

CSS = f"""
.stApp {{ background: linear-gradient(180deg, #D8EBFF 0%, #E7F1FE 55%, #F2F8FE 100%) !important; }}
.stApp::before {{ content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; background: url({_uri(_sky())}) center top / 100% auto no-repeat; }}
.stApp::after {{ content: ""; position: fixed; left: 0; right: 0; bottom: 0; height: 15vh; min-height: 90px; z-index: 0; pointer-events: none;
  background: url({_uri(_sea())}) center bottom / 100% 100% no-repeat; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ position: relative; z-index: 1; background: transparent !important; }}
.block-container {{ max-width: 1200px !important; padding-bottom: 200px !important; }}
[data-testid="stHorizontalBlock"] {{ gap: 22px; }}

.ln-pill {{ background: rgba(255,255,255,.88); border-color: rgba(255,255,255,.95); box-shadow: 0 8px 20px rgba(70,120,200,.13); }}
.ln-pills .ln-pill:nth-child(2) {{ background: #FFF1B8; border-color: #F2D676; }}
.ln-bar {{ background: rgba(255,255,255,.85); box-shadow: inset 0 1px 3px rgba(60,100,170,.18); }}
.ln-bar > div {{ background: linear-gradient(90deg, #FFD65A, #F5B400); box-shadow: 0 0 14px rgba(245,180,0,.6); }}
.ln-count {{ color: #5B6B8C; }}
.st-key-nav button {{ background: rgba(255,255,255,.88); border-color: rgba(255,255,255,.95); box-shadow: 0 8px 18px rgba(70,120,200,.13); }}
.st-key-nav button[kind="primary"] {{ box-shadow: 0 0 0 5px rgba(47,111,228,.2), 0 8px 18px rgba(47,111,228,.35); }}

.ln-wordcard {{ background: rgba(240,250,234,.84); border: 1.5px solid #CFE8BD; border-radius: 28px; box-shadow: 0 14px 34px rgba(80,140,70,.12);
  padding: 26px 30px; min-height: 354px; flex-wrap: nowrap; gap: 14px; }}
.ln-word {{ font-size: 176px; letter-spacing: -5px; line-height: .9; }}
.ln-word[data-n="3"] {{ font-size: 130px; letter-spacing: -4px; }}
.ln-word[data-n="4"], .ln-word[data-n="5"] {{ font-size: 104px; letter-spacing: -3px; }}
.ln-word .hl {{ text-decoration-thickness: 9px; text-underline-offset: 14px; }}
.ln-circle {{ width: 124px; height: 124px; }}
.ln-circle.empty {{ border: 3px dashed #8F9BB5; background: rgba(255,255,255,.35) !important; }}
.ln-sound {{ background: #E1ECFF; border-radius: 999px; padding: 7px 20px; margin-top: 14px; }}
.ln-cap {{ color: #4A5877 !important; }}
.ln-meaning {{ font-size: 24px; margin-top: 4px; }}

.st-key-toprow [data-testid="stColumn"] > [data-testid="stVerticalBlock"], .st-key-toprow .stElementContainer,
.st-key-toprow [data-testid="stHtml"], .st-key-toprow .ln-wordcard {{ height: 100%; }}
.st-key-mouth {{ {CARD} padding: 24px !important; min-height: 354px; box-shadow: 0 14px 34px rgba(70,120,200,.13); border: 1.5px solid rgba(255,255,255,.95) !important; }}
.ln-checks li {{ background: rgba(255,255,255,.9); border-color: #D8E4F7; border-radius: 18px; }}

[data-baseweb="select"] > div {{ background: rgba(255,255,255,.92) !important; border-color: rgba(255,255,255,.95) !important; border-radius: 999px !important; }}
.st-key-lipbar {{ {CARD} padding: 22px 30px !important; border: 1.5px solid rgba(255,255,255,.95) !important; }}
.st-key-lipbar label p {{ font-size: 18px; }}
.st-key-lipbar label > div:first-of-type {{ background-color: #C9D4E8 !important; }}
.st-key-lipbar label:has(input:checked) > div:first-of-type {{ background-color: #2F6FE4 !important; }}
.st-key-lipbar [data-testid="stCaptionContainer"] {{ padding-left: 54px; }}
.st-key-lipbar [data-testid="stColumn"]:first-child {{ border-right: 2px dashed #CBD7EC; padding-right: 26px; }}
.st-key-lipbar [data-testid="stColumn"]:last-child {{ padding-left: 20px; justify-content: center; }}
"""
