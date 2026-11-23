"""Teacher-run data collection (?page=collect): one participant code, all eight words, the same recorder and the same rules for every word.

The child (or the adult being recorded) hears and sees no verdict: the app's judgement is only stored (fricative/collect.py) so that teachers can rate the
recordings independently afterwards (Dev app, page "Rate"). No stars, no locks, no live guidance. Participants are known by a code, never by name.
"""
from __future__ import annotations

import random
from html import escape

import streamlit as st

from fricative import collect, phoneme_check, reclog
from fricative.audio import load
from fricative.noise import recording_quality
from . import result, screen
from .lessons import LESSONS, ORDER
from .mic import mic

CSS = """
.st-key-cl_form { max-width: 760px; margin: 0 auto; }
.cl-card { max-width: 760px; margin: 0 auto 16px; background: rgba(255,255,255,.92); border: 1.5px solid #D5DFF0; border-radius: 24px; padding: 22px 28px; color: #1B2440; }
.cl-h1 { font-size: 30px; font-weight: 900; margin: 0 0 6px; }
.cl-word { font-size: 120px; font-weight: 900; line-height: 1; text-align: center; margin: 6px 0; }
.cl-sub { text-align: center; font-size: 20px; font-weight: 700; color: #3A4664; }
.cl-prog { text-align: center; font-size: 16px; font-weight: 700; color: #3A4664; margin-top: 8px; }
.cl-ok { text-align: center; font-size: 22px; font-weight: 800; color: #1F7A3F; }
.cl-bad { text-align: center; font-size: 18px; font-weight: 800; color: #B4541B; }
"""

AGE = ["under 6", "6-8", "9-12", "13-17", "adult"]
HEAR = ["typical hearing", "hard of hearing (hearing aids)", "deaf (cochlear implant)", "deaf (other / no device)", "unknown / prefer not to say"]
MIC = ["laptop built-in", "headset", "external USB microphone", "tablet / phone"]
ROOM = ["quiet", "some background noise", "noisy"]
PROBLEM_TEXT = {"quiet": "Too quiet. Please say the word a little louder.", "loud": "Too loud. Please move back a little.", "noisy": "Too much noise in the room. Please try again in a quieter place."}


def _setup() -> None:
    st.html('<div class="cl-card"><div class="cl-h1">Recording session 錄音</div>'
            '<div>For teachers. Each participant says the eight words twice (about 4 minutes). No score is shown to the participant. '
            'Use a code (for example S01), never a name. 供老師使用；請用代碼，不要用姓名。</div></div>')
    with st.container(key="cl_form"):
        if not phoneme_check.available():
            st.warning("The phone recogniser model is not installed on this computer: pea, bee, me, knee and cheat will be recorded, but the app cannot score them "
                       "(teachers can still rate the recordings). Use the computer that has the model if the app's verdicts are needed. "
                       "此電腦沒有語音辨識模型：pea、bee、me、knee、cheat 仍會錄音，但程式無法評分。")
        code = st.text_input("Participant code 代碼", key="cl_code", max_chars=20, help="Letters, digits, - and _ only")
        taken = collect.clean_code(code) in collect.participants()
        if taken:
            st.warning(f"The code {collect.clean_code(code)} is already used by another participant. Choose a new code, or continue that participant below. 此代碼已被使用，請換一個，或在下方選擇繼續。")
        by = st.text_input("Your initials 您的姓名縮寫", key="cl_by", max_chars=10)
        st.html('<div class="cl-sub" style="text-align:left;font-size:16px">About the participant and the recording (no names) 參與者與錄音情況（不填姓名）</div>')
        c1, c2 = st.columns(2)
        age = c1.selectbox("Age group 年齡層", AGE, index=None, key="cl_age", placeholder="Choose 請選擇")
        hear = c2.selectbox("Hearing 聽力（可不答）", HEAR, index=None, key="cl_hear", placeholder="Optional 可不選")
        l1 = c1.text_input("First language 母語（可不填）", key="cl_l1", max_chars=30)
        mic_t = c2.selectbox("Microphone 麥克風", MIC, index=None, key="cl_mic", placeholder="Choose 請選擇")
        room = c1.selectbox("Room 房間環境", ROOM, index=None, key="cl_room", placeholder="Choose 請選擇")
        ok = st.checkbox("I confirm that consent was given for this participant (parent/guardian and, where possible, the child) 已取得同意", key="cl_consent")
        audio = st.checkbox("The consent includes keeping the audio recordings (needed for rating by teachers) 同意保存錄音", key="cl_audio", disabled=not ok)
        if st.button("Start 開始", type="primary", key="cl_start", disabled=not (collect.clean_code(code) and by.strip() and ok and age and mic_t and room) or taken):
            words = list(ORDER)
            random.Random(collect.clean_code(code)).shuffle(words)             # a different but reproducible word order for each participant (no order or fatigue effect on one word)
            collect.start_session(code, words, by, bool(audio and ok), age_group=age, hearing=hear or "not given", first_language=l1.strip() or "not given", microphone=mic_t, room=room)
            st.session_state["cl_active"] = collect.clean_code(code)
            st.session_state["cl_bad"] = 0
            st.query_params["p"] = collect.clean_code(code)
            st.rerun()
        existing = collect.participants()
        if existing:
            pick = st.selectbox("Or continue a participant 繼續", [""] + existing, key="cl_continue")
            if pick and st.button("Continue 繼續", key="cl_cont"):
                st.session_state["cl_active"] = pick
                st.session_state["cl_bad"] = 0
                st.query_params["p"] = pick
                st.rerun()


def _finish(code: str) -> None:
    st.html(f'<div class="cl-card"><div class="cl-h1">All done 完成 ✓</div><div>Participant <b>{escape(code)}</b> has said every word. Thank you! 謝謝！</div></div>')
    st.download_button("Download this participant's data (zip) 下載資料", collect.export_zip([code]), file_name=f"{code}_data.zip", mime="application/zip", key="cl_dl")
    if st.button("Next participant 下一位", key="cl_next_p", type="primary"):
        st.session_state.pop("cl_active", None)
        st.query_params.pop("p", None)
        st.rerun()
    if st.button("Undo the last recording 取消上一筆錄音", key="cl_undo_done"):
        collect.delete_last_take(code)
        st.rerun()


def render() -> None:
    st.html(f"<style>{CSS}</style>")
    code = st.session_state.get("cl_active")
    if not code:
        back = collect.clean_code(st.query_params.get("p", ""))           # a reload keeps ?p=CODE, so the session is picked up again
        if back and collect.session(back):
            st.session_state["cl_active"] = code = back
            st.session_state["cl_bad"] = 0
    if not code:
        _setup()
        return
    s = collect.session(code)
    item = collect.next_item(code)
    if not s:
        st.session_state.pop("cl_active", None)
        st.rerun()
    if item is None:
        _finish(code)
        return
    word, n = item
    lesson = LESSONS[word]
    total = len(s["words"]) * s["takes_per_word"]
    flash = st.session_state.pop("cl_flash", None)
    if flash:
        st.html(f'<div class="cl-ok">{escape(flash)}</div>')
    pic = screen._figure(lesson.meaning_svg, "#CFE3FF", "", "Picture") if lesson.meaning_svg else ""
    st.html(f'<div class="cl-card"><div class="cl-sub">Please say 請說</div><div class="cl-word">{escape(word)}</div><div style="display:flex;justify-content:center">{pic}</div>'
            f'<div class="cl-prog">{sum(collect.done(code).values()) + 1} / {total} · take {n} of {s["takes_per_word"]}</div></div>')
    alert = st.container()                                           # a refused recording is explained here, above the recorder, where it is seen
    key = f"col_{code}_{word}_{n}_{st.session_state.get('cl_bad', 0)}"
    left, mid, right = st.columns([1, 1, 1])
    with mid:
        wav = mic(key, zones=None, live="off", hint="", word=word, theme="sky")
    if wav is not None:
        sound, _ = (None, None)
        try:
            from fricative.audio import limit_duration
            sound, _ = limit_duration(load(wav, "recording.wav"))
        except ValueError:
            pass
        q = recording_quality(sound, st.session_state.get(f"{key}_room")) if sound is not None else None
        if q is None or q.problem:
            problem = (q.problem if q else "quiet")
            reclog.log_event("collect_bad_take", st.session_state.get("sid", ""), code, word=word, take=n, problem=problem)
            collect.add_rejected(code, word, n, problem)
            st.session_state["cl_bad"] = st.session_state.get("cl_bad", 0) + 1
            with alert:
              st.html(f'<div class="cl-bad">{escape(PROBLEM_TEXT.get(problem, "Please try again."))}<br>'
                      '(Only the sound quality is checked here, not whether the word was said well. 這裡只檢查錄音品質，不評斷念得好不好。)</div>')
              _l, _m, _r = st.columns([1, 1, 1])
              _m.button("Try again 再試一次", key=f"cl_retry_{key}", type="primary", width="stretch")
              if st.session_state["cl_bad"] >= 3:                     # three refused recordings in a row: do not leave the participant stuck
                if _m.button("Skip this word 略過這個字", key=f"cl_skip_{key}", width="stretch"):
                    collect.add_skip(code, word, lesson.phone, f"{problem} x3")
                    st.session_state["cl_bad"] = 0
                    st.rerun()
            return
        res = result.score(wav, lesson.phone, 1.0)
        collect.add_take(code, word, lesson.phone, wav, {"problem": None, "snr_db": round(q.snr_db, 1), "level_dbfs": round(q.level_db, 1)},
                         {"color": res.color, "closeness": res.closeness, "heard": res.heard, "cog_hz": res.cog_hz, "notice": res.notice or None})
        reclog.log_event("collect_take", st.session_state.get("sid", ""), code, word=word, take=n)
        st.session_state["cl_bad"] = 0
        st.session_state["cl_flash"] = "Saved ✓ 已儲存"
        st.rerun()
    st.html('<div class="cl-prog">Press the blue microphone button, say the word, then wait. 按藍色麥克風鍵說出字，然後稍等。</div>')
    with st.container(key="cl_tools", horizontal=True):
        if collect.takes(code) and st.button("Undo the last recording 取消上一筆錄音", key="cl_undo"):
            collect.delete_last_take(code)
            st.session_state["cl_bad"] = st.session_state.get("cl_bad", 0) + 1       # a fresh recorder
            st.rerun()
        if st.button("Stop this participant 結束", key="cl_stop"):
            st.session_state.pop("cl_active", None)
            st.query_params.pop("p", None)
            st.rerun()
