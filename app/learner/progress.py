"""The "My Stars" page (?page=stars): every sound of the child with its stars, how it stands and a way in. The stars are what the lessons earned (learner/stars.py);
a sound shows as locked until the one before it is passed. Nothing is drawn here that the child has not earned."""
from __future__ import annotations

from html import escape

import streamlit as st

from fricative.calibrated import last_profile
from . import stars
from .lessons import LESSONS, ORDER

CSS = """
.pg-wrap { max-width: 760px; margin: 0 auto; padding-bottom: 150px; color: #1B2440; }
.pg-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.pg-h1 { font-size: 34px; font-weight: 900; margin: 0; }
.pg-h1 .zh { font-size: 20px; font-weight: 600; color: #3A4664; margin-left: 10px; }
.pg-total { display: inline-flex; gap: 8px; align-items: center; background: #FFF4C9; border: 2px solid #E8B93A; border-radius: 999px; padding: 6px 18px; font-size: 22px; font-weight: 800; }
.pg-row { display: flex; align-items: center; gap: 16px; background: rgba(255,255,255,.9); border: 1.5px solid #D8E4F7; border-radius: 20px; padding: 12px 18px; margin-bottom: 10px;
  text-decoration: none !important; color: #1B2440 !important; }
a.pg-row:hover { border-color: #2F6FE4; }
.pg-row.locked { opacity: .55; }
.pg-snd { font-size: 24px; font-weight: 900; min-width: 64px; }
.pg-word { flex: 1; font-size: 18px; font-weight: 700; }
.pg-word small { display: block; font-size: 14px; font-weight: 600; color: #3A4664; }
.pg-stars { font-size: 28px; letter-spacing: 2px; color: #D5DDEC; white-space: nowrap; }
.pg-stars b { color: #F2B21B; font-weight: 400; }
.pg-back { display: inline-flex; align-items: center; min-height: 46px; padding: 0 20px; border-radius: 999px; background: #fff; border: 1.5px solid #D8E4F7; font-weight: 800; color: #1B2440 !important; text-decoration: none !important; }
"""

STATE_TEXT = {"done": ("Done", "完成"), "in progress": ("Keep going", "繼續加油"), "not started": ("Not started", "還沒開始")}


def render() -> None:
    child = last_profile()
    progress = stars.load(child)
    rows = ""
    for w in ORDER:
        best = stars.best(progress, w)
        open_ = stars.unlocked(progress, w) or child is None
        en, zh = ("Locked", "未開放") if not open_ else STATE_TEXT[stars.status(progress, w)]
        tries = progress.get(w, {}).get("tries", 0)
        note = f"{en} {escape(zh)}" + (f" · {tries}×" if tries else "")
        body = (f'<span class="pg-snd">{escape(LESSONS[w].label)}</span><span class="pg-word">{escape(w)}<small>{note}</small></span>'
                f'<span class="pg-stars" aria-label="{best} of {stars.MAX_STARS} stars"><b>{"★" * best}</b>{"★" * (stars.MAX_STARS - best)}</span>')
        rows += f'<a class="pg-row" href="?word={w}" target="_self">{body}</a>' if open_ else f'<div class="pg-row locked">{body}</div>'
    who = escape(child) if child else "No child chosen"
    st.html(f"<style>{CSS}</style><div class='pg-wrap'><div class='pg-top'><a class='pg-back' href='?page=home' target='_self'>← Home 首頁</a>"
            f"<span class='pg-total'>★ {stars.total(child)} <span style='font-size:16px;font-weight:700'>{who}</span></span></div>"
            f"<h1 class='pg-h1'>My Stars<span class='zh'>我的星星</span></h1><p style='font-weight:700;color:#3A4664'>Pass a sound with {stars.PASS_STARS} stars to open the next one. "
            f"<span style='font-weight:500'>拿到 {stars.PASS_STARS} 顆星就能打開下一個聲音。</span></p>{rows}</div>")
