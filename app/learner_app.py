"""The learners' app: one word at a time, built from the design mockup (S mockup pdf.pdf). The Dev tools live in streamlit_app.py.

Run: streamlit run app/learner_app.py --server.port 8502
Open another word with ?word=she or use the buttons above the word to move between sounds.

The record panel on the right is replaced by the result once a recording is scored; "Record again" brings the record button back.
"""
import uuid

import streamlit as st
from pathlib import Path

from fricative import warmup
from fricative.audio import load
from fricative import reclog
from fricative.noise import log_quality, recording_quality
from fricative.calibrated import last_profile, load_room, voice_scale
from learner import camlog, home, lipcam, progress as progress_page, result, screen, sky, sound_check, spectro, stars, tongue
from learner.lessons import LESSONS, ORDER
from learner.mic import affricate_settings as mic_affricate_settings, fricative_settings as mic_fricative_settings, guide_settings as mic_guide_settings, mic
from learner.motion import mouth_motion, mouth_steps

st.set_page_config(page_title="Practice", page_icon=str(Path(__file__).resolve().parent / "learner" / "assets" / "seesound_logo.png"), layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource(show_spinner="Getting ready… 準備中…")
def _ready() -> dict:
    return warmup.warm()


_ready()                                    # every model is loaded before the first screen is used
sid = st.session_state.setdefault("sid", uuid.uuid4().hex[:8])     # one id per visit, so the research log can tell visits apart

word = st.query_params.get("word", ORDER[0])
if word not in LESSONS:
    word = ORDER[0]
lesson, index = LESSONS[word], ORDER.index(word) + 1
scale = voice_scale(last_profile())          # the size of this child's voice (Sound Check); 1.0 = the adult thresholds
store = f"mic_{word}_wav"         # the recording being scored; removing it brings the record button back

st.html(f"<style>{screen.CSS}{tongue.CSS}{result.CSS}{screen.NAV_CSS}{sound_check.CSS}{sky.CSS}</style>")       # one look for every page: the sky (learner/sky.py)
page = st.query_params.get("page")
if page == "sound":                                         # ?page=sound: the calibration (Sound Check) instead of a lesson
    sound_check.render()
    st.stop()
if page == "collect":                                       # ?page=collect: a teacher records a participant (no feedback shown), see learner/collect.py
    from learner import collect as collect_page
    collect_page.render()
    st.stop()
if page == "stars":                                         # ?page=stars: the stars of every sound ("My Stars" on the home page)
    progress_page.render()
    st.stop()
if page == "home" or "word" not in st.query_params:     # the app opens on the home page (SeeSound); ?word=she opens a lesson; an old ?page=map lands here too
    home.render()
    st.stop()
st.html(screen.top_bar(index, len(ORDER), stars.total(last_profile())))


open_all = st.query_params.get("open") == "all"                           # ?open=all: every sound open (for a teacher)
progress = stars.load(last_profile())
guest = last_profile() is None                                            # no child chosen: nothing can be saved or earned, so nothing is locked (and a banner says so)
is_open = {w: open_all or guest or stars.unlocked(progress, w) for w in ORDER}      # a sound opens when the one before it is passed (learner/stars.py)
if st.session_state.get("_opened") != word:                               # the research log: one line each time a lesson is opened
    st.session_state["_opened"] = word
    reclog.log_event("lesson_open", sid, last_profile(), word=word, unlocked=is_open[word], guest=guest, open_all=open_all, stars=stars.best(progress, word))
if guest:
    st.html('<div class="ln-guest">No child chosen: your stars are not saved. <a href="?page=sound" target="_self">Add a child 新增學生</a> '
            '<span class="zh">尚未選擇學生，星星不會儲存。</span></div>')


def go(target: str) -> None:
    """Move to another sound: it opens with the record button, not with an earlier result."""
    for w in (word, target):
        st.session_state.pop(f"mic_{w}_wav", None)
    st.session_state.pop("celebrate", None)
    st.query_params.clear()
    st.query_params["word"] = target
    if open_all:
        st.query_params["open"] = "all"


with st.container(key="nav", horizontal=True, vertical_alignment="center"):
    nxt = ORDER[min(index, len(ORDER) - 1)]
    st.button("", key="nav_prev", icon=":material/chevron_left:", disabled=index == 1, on_click=go, args=(ORDER[max(index - 2, 0)],))
    for w in ORDER:                                  # the sounds as a row of buttons; the open one is filled; a sound not open yet cannot be pressed
        st.button(LESSONS[w].label, key=f"nav_{w}", type="primary" if w == word else "secondary", on_click=go, args=(w,), disabled=not is_open[w],
                  help=None if is_open[w] else f"Get 2 stars on {LESSONS[ORDER[ORDER.index(w) - 1]].label} first · 先在前一個聲音拿到兩顆星")
    st.button("", key="nav_next", icon=":material/chevron_right:", disabled=index == len(ORDER) or not is_open[nxt], on_click=go, args=(nxt,))
    st.button("Sound check 聲音檢查", key="nav_sound", icon=":material/tune:", on_click=lambda: st.query_params.update({"page": "sound"}))

if not is_open[word]:                                # opened by its address before its turn: say why, and offer the sound to do now
    here = stars.frontier(progress) or ORDER[0]
    prev = ORDER[ORDER.index(word) - 1]
    st.html(f'<div style="max-width:640px;margin:40px auto;background:#FBF3DC;border:3px solid #1B2440;border-radius:24px;padding:28px 30px;text-align:center;color:#1B2440">'
            f'<div style="font-size:30px;font-weight:900">🔒 Not open yet <span style="font-weight:700;color:#3A4664">還沒打開</span></div>'
            f'<div style="font-size:20px;font-weight:700;margin-top:12px">Get 2 stars on {LESSONS[prev].label} {prev} first.<br>'
            f'<span style="color:#3A4664">先在 {LESSONS[prev].label} {prev} 拿到兩顆星。</span></div></div>')
    _, mid, _ = st.columns([1, 1, 1])
    mid.button(f"Go to {LESSONS[here].label} {here} 前往", key="locked_go", type="primary", width="stretch", on_click=go, args=(here,))
    st.stop()

lip = lesson.phone in ("m", "p", "b", "n", "tʃ", "s", "sh")        # the lips can be seen: these lessons have their own layout, the sky page (learner/sky.py)
step = st.query_params.get("step")                      # ?step=2&hold=1 stays on one step (to check it)
start, hold = (int(step) - 1 if step and step.isdigit() else 0), st.query_params.get("hold") == "1"

LIVE_MODES = {"Dot 圓點": "dot", "Game 遊戲": "game", "Picture 圖像": "spectrogram", "Meter 長條": "meter", "Off 關閉": "off"}
LIVE_CHOICES = {"s": ["Dot 圓點", "Game 遊戲", "Picture 圖像", "Off 關閉"], "sh": ["Dot 圓點", "Game 遊戲", "Picture 圖像", "Off 關閉"], "f": ["Meter 長條", "Off 關閉"]}
LIVE_HINT = {"meter": "Soft and steady: keep the bar in the green 輕輕、穩定：讓長條停在綠色", "dot": "Keep the dot in the green 讓圓點留在綠色區域", "game": "Fill the green with sound 用聲音填滿綠色區域"}


def mouth_block() -> None:
    """The mouth picture with its steps or loop: what to watch while saying the sound."""
    if lesson.steps:                                        # a sound made in steps: one picture per step, shown one after another
        with st.container(key="mouth"):
            st.html(screen.mouth_title())
            mouth_steps(lesson, f"steps_{word}", start, hold, compact=True)      # on the sky page the tips are three short boxes (the mockup has no pinyin there)
    elif lesson.motions and lesson.mouth_image:             # the mouth picture as a short loop of steps
        with st.container(key="mouth"):
            st.html(screen.mouth_title())
            mouth_motion(lesson, f"motion_{word}", start, hold)
            st.html(screen.checks_html(lesson))
    else:
        st.html(screen.mouth_card(lesson))


def record_block() -> None:
    """The record button; once a recording is scored, the result in its place."""
    slot = st.empty()
    if st.session_state.get(store) is None:
        with slot.container():
            live = LIVE_MODES.get(live_label, "off" if lesson.phone == "f" else "dot")
            mic(f"mic_{word}", zones=spectro.zones(lesson.phone, scale, live=True), live=live, hint=LIVE_HINT.get(live, ""),
                levels=spectro.meter_levels(lesson.phone, last_profile()),
                guide=mic_guide_settings(load_room(last_profile()), camlog.url(), word, "nnn" if lesson.phone == "n" else "mmm")
                if lesson.phone in ("m", "n") else mic_affricate_settings(camlog.url(), word) if lesson.phone == "tʃ"
                else mic_fricative_settings(camlog.url(), word) if lesson.phone in ("s", "sh") else None,      # "me": mmm then ee, it follows the voice
                theme="sky" if lip else "", log_url=camlog.url(), word=word)
    wav = st.session_state.get(store)       # also set by the line above, when the recording has just arrived
    if wav is not None:
        slot.empty()
        with slot.container(key="result"):
            quality = recording_quality(load(wav, "recording.wav"), st.session_state.get(f"mic_{word}_room"))
            fresh = st.session_state.get("quality_logged") != (word, hash(wav))     # once per recording, not at every redraw
            st.session_state["quality_logged"] = (word, hash(wav))
            problem = quality.problem                                           # a bad recording is not scored: it would only mislead
            if problem:
                if fresh:
                    log_quality(word, quality)
                    reclog.log_event("attempt", sid, last_profile(), word=word, phone=lesson.phone, scored=False, problem=problem, snr_db=round(quality.snr_db, 1), level_dbfs=round(quality.level_db, 1),
                                     room_dbfs=st.session_state.get(f"mic_{word}_room"), voice_scale=round(scale, 3), lip_on=lip_on, coach=coach)
                st.html(sound_check.recording_problem(problem))
            else:
                live = st.session_state.get(f"mic_{word}_live")                 # a guided practice of a held hiss: the result is made from what the guide found, as the dot and the box show it
                res = result.from_live(live, lesson.phone) if live and lesson.phone in ("s", "sh") else result.score(wav, lesson.phone, scale)
                if fresh:
                    log_quality(word, quality, res.color, res.cog_hz, res.heard, res.notice)      # the notice says why nothing was scored
                earned = stars.stars(res.color, res.closeness)
                child = last_profile()
                was_progress = stars.load(child).get(word, {"best": 0, "tries": 0})
                was = was_progress["best"]
                crossed = bool(child) and earned is not None and stars.passed_now(was, earned)
                if fresh:                                                           # the research log: what was scored, how, and what it did to the child's stars
                    reclog.log_event("attempt", sid, child, word=word, phone=lesson.phone, scored=earned is not None, attempt_no=was_progress["tries"] + 1, color=res.color, closeness=res.closeness,
                                     stars=earned, best_before=was, passed_now=crossed, cog_hz=res.cog_hz, heard=res.heard, position=res.position, relamp_db=res.relamp_db, notice=res.notice or None,
                                     snr_db=round(quality.snr_db, 1), level_dbfs=round(quality.level_db, 1), room_dbfs=st.session_state.get(f"mic_{word}_room"), voice_scale=round(scale, 3),
                                     live=live, live_mode=st.session_state.get(f"live_mode_{lesson.phone if lesson.phone == 'f' else 'ss'}"), lip_on=lip_on, coach=coach, pass_stars=stars.PASS_STARS,
                                     affricate=getattr(res.affricate, "__dict__", None) or (str(res.affricate) if res.affricate else None))
                if earned is not None and st.session_state.get("stars_logged") != (word, hash(wav)):    # once per recording
                    st.session_state["stars_logged"] = (word, hash(wav))
                    st.session_state["celebrate"] = (word, ORDER[index] if index < len(ORDER) else None) if crossed else None      # this try opens the next sound: celebrate under the result
                    if stars.record(last_profile(), word, earned):
                        st.rerun()                                              # the star count at the top changes
                st.html(result.panel(res, lesson.phone, wav, scale))
                celebrate = st.session_state.get("celebrate")
                if celebrate and celebrate[0] == word:
                    nxt_word = celebrate[1]
                    if nxt_word:
                        st.html(f'<div class="ln-win">🎉 <b>New sound open!</b> {LESSONS[nxt_word].label} {nxt_word} <span class="zh">新的聲音打開了！</span></div>')
                        st.button(f"Go on to {LESSONS[nxt_word].label} {nxt_word} 前往下一個", key="win_next", type="primary", width="stretch", on_click=go, args=(nxt_word,))
                    else:
                        st.html('<div class="ln-win">🎉 <b>All sounds done!</b> <span class="zh">全部完成！</span></div>')
            st.button("Record again 再錄一次", key="again", width="stretch", on_click=lambda: (reclog.log_event("record_again", sid, last_profile(), word=word), st.session_state.pop(store, None), st.session_state.pop("celebrate", None)))


lip_on = bool(st.session_state.get("lip_on", False)) if lip else False      # the switches are drawn below the mirror, so their values are read from the session first
coach = lesson.phone in ("m", "n") and lip_on and bool(st.session_state.get("lip_coach", True))
vowel = coach and bool(st.session_state.get("lip_vowel", True))                                        # "me" = /m/ then /iː/

live_label = "Meter 長條" if lesson.phone == "f" else "Dot 圓點"
if lesson.phone in LIVE_CHOICES:                             # /s/ /ʃ/ /f/: what the screen shows while the child speaks (to try, and to go back from): a slim line above the row, so the three cards start level
    choices = LIVE_CHOICES[lesson.phone]
    with st.container(key="liverow", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        live_label = st.segmented_control("Live view 即時顯示", choices, default=choices[0], key=f"live_mode_{lesson.phone if lesson.phone == 'f' else 'ss'}", required=True)

with st.container(key="toprow"):                            # one row of three cards of the same height: the recorder | the word | the mouth to watch
    col_rec, col_word, col_mouth = st.columns([1, 1, 1.15])
    with col_rec:
        record_block()
    with col_word:
        with st.container(key="word_solo"):
            st.html(screen.word_card(lesson))
    with col_mouth:
        mouth_block()
if lip:
    with st.container(key="lipbar", horizontal=True, vertical_alignment="center"):      # a slim band under the row: the camera switch, the coach switches, the privacy note
        st.toggle("**Lip mirror** 嘴唇鏡子 :gray[(uses the camera 使用相機)]", key="lip_on")
        if lesson.phone in ("m", "n"):
            st.toggle("**Coach** 教練 :gray[(lips and voice 嘴唇加聲音)]", key="lip_coach", value=True, disabled=not lip_on)
            st.toggle("**Go on to a smile** 接著微笑", key="lip_vowel", value=True, disabled=not coach)
        with st.popover("Privacy 隱私"):
            st.caption("The camera picture stays on this device and is not saved; you see a drawing of a mouth, not the picture. Use it only with the "
                       "permission of a parent or the school. 相機畫面只留在這台裝置、不會儲存，畫面上只會看到嘴巴的圖。須經家長或學校同意後使用。 "
                       "While testing, numbers about the lips and the sound (not the picture, not the voice) are saved on this computer. 測試期間，唇與聲音的數據（不含畫面與聲音）會存在這台電腦。")
    if lip_on:                                                # switching it on is the choice to use the camera: the mirror starts at once and scrolls into view (the browser still asks)
        lipcam.lip_mirror(f"lip_{word}_{'vowel' if vowel else 'coach' if coach else 'mirror'}", coach=coach, noise_db=load_room(last_profile()), vowel=vowel, sound=lesson.phone,
                          log_url=camlog.url(), word=word, autostart=True)
