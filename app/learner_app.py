"""The learners' app: one word at a time, built from the design mockup (S mockup pdf.pdf). The Dev tools live in streamlit_app.py.

Run: streamlit run app/learner_app.py --server.port 8502
Open another word with ?word=she (only "see" has its full content so far), or use the buttons above the word to move between sounds.

The record panel on the right is replaced by the result once a recording is scored; "Record again" brings the record button back.
"""
import streamlit as st
from pathlib import Path

from fricative import warmup
from fricative.audio import load
from fricative.noise import log_quality, recording_quality
from fricative.calibrated import last_profile, load_room, voice_scale
from learner import camlog, home, lipcam, map as map_screen, result, screen, sky, sound_check, spectro, stars, tongue
from learner.lessons import LESSONS, ORDER
from learner.mic import affricate_settings as mic_affricate_settings, fricative_settings as mic_fricative_settings, guide_settings as mic_guide_settings, mic
from learner.motion import mouth_motion, mouth_steps

st.set_page_config(page_title="Practice", page_icon=str(Path(__file__).resolve().parent / "learner" / "assets" / "seesound_logo.png"), layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource(show_spinner="Getting ready… 準備中…")
def _ready() -> dict:
    return warmup.warm()


_ready()                                    # every model is loaded before the first screen is used

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
if page == "home" or (page is None and "word" not in st.query_params):     # the app opens on the home page (SeeSound); ?word=she opens a lesson
    home.render()
    st.stop()
if page == "map":                                                           # the map of the eight sounds
    map_screen.render()
    st.stop()
st.html(screen.top_bar(index, len(ORDER), stars.total(last_profile())))


open_all = st.query_params.get("open") == "all"                           # ?open=all: every sound open (for a teacher)
progress = stars.load(last_profile())
is_open = {w: open_all or stars.unlocked(progress, w) for w in ORDER}      # a sound opens when the one before it has a star (learner/stars.py)


def go(target: str) -> None:
    """Move to another sound: it opens with the record button, not with an earlier result."""
    for w in (word, target):
        st.session_state.pop(f"mic_{w}_wav", None)
    st.query_params.clear()
    st.query_params["word"] = target
    if open_all:
        st.query_params["open"] = "all"


with st.container(key="nav", horizontal=True, vertical_alignment="center"):
    nxt = ORDER[min(index, len(ORDER) - 1)]
    st.button("", key="nav_prev", icon=":material/chevron_left:", disabled=index == 1, on_click=go, args=(ORDER[max(index - 2, 0)],))
    for w in ORDER:                                  # the sounds as a row of buttons; the open one is filled; a sound not open yet cannot be pressed
        st.button(LESSONS[w].label, key=f"nav_{w}", type="primary" if w == word else "secondary", on_click=go, args=(w,), disabled=not is_open[w],
                  help=None if is_open[w] else f"First get a star on {LESSONS[ORDER[ORDER.index(w) - 1]].label} · 先在前一個聲音拿到一顆星")
    st.button("", key="nav_next", icon=":material/chevron_right:", disabled=index == len(ORDER) or not is_open[nxt], on_click=go, args=(nxt,))
    st.button("Sound check 聲音檢查", key="nav_sound", icon=":material/tune:", on_click=lambda: st.query_params.update({"page": "sound"}))

if not is_open[word]:                                # opened by its address before its turn: say why, and offer the sound to do now
    here = stars.frontier(progress) or ORDER[0]
    prev = ORDER[ORDER.index(word) - 1]
    st.html(f'<div style="max-width:640px;margin:40px auto;background:#FBF3DC;border:3px solid #1B2440;border-radius:24px;padding:28px 30px;text-align:center;color:#1B2440">'
            f'<div style="font-size:30px;font-weight:900">🔒 Not open yet <span style="font-weight:700;color:#3A4664">還沒打開</span></div>'
            f'<div style="font-size:20px;font-weight:700;margin-top:12px">First get a star on {LESSONS[prev].label} {prev}.<br>'
            f'<span style="color:#3A4664">先在 {LESSONS[prev].label} {prev} 拿到一顆星。</span></div></div>')
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
    live_label = "Meter 長條" if lesson.phone == "f" else "Dot 圓點"
    if lesson.phone in LIVE_CHOICES:                         # /s/ /ʃ/ /f/: what the screen shows while the child speaks (to try, and to go back from)
        choices = LIVE_CHOICES[lesson.phone]
        live_label = st.segmented_control("Live view 即時顯示", choices, default=choices[0], key=f"live_mode_{lesson.phone if lesson.phone == 'f' else 'ss'}", required=True)
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
                st.html(sound_check.recording_problem(problem))
            else:
                live = st.session_state.get(f"mic_{word}_live")                 # a guided practice of a held hiss: the result is made from what the guide found, as the dot and the box show it
                res = result.from_live(live, lesson.phone) if live and lesson.phone in ("s", "sh") else result.score(wav, lesson.phone, scale)
                if fresh:
                    log_quality(word, quality, res.color, res.cog_hz, res.heard, res.notice)      # the notice says why nothing was scored
                earned = stars.stars(res.color, res.closeness)
                if earned is not None and st.session_state.get("stars_logged") != (word, hash(wav)):    # once per recording
                    st.session_state["stars_logged"] = (word, hash(wav))
                    if stars.record(last_profile(), word, earned):
                        st.rerun()                                              # the star count at the top changes
                st.html(result.panel(res, lesson.phone, wav, scale))
            st.button("Record again 再錄一次", key="again", width="stretch", on_click=lambda: st.session_state.pop(store, None))


with st.container(key="toprow"):                            # every lesson has the same layout: the word and the mouth to watch, then the recorder (and the lip mirror)
    top_l, top_r = st.columns([640, 513])
    with top_l:
        st.html(screen.word_card(lesson))
    with top_r:
        mouth_block()
lip_on, coach, vowel = False, False, False
if lip:
    with st.container(key="lipbar"):                      # the camera switch with its privacy note, and the coach switches
        bar_l, bar_r = st.columns([3, 2], gap="large")
        with bar_l:
            lip_on = st.toggle("**Lip mirror** 嘴唇鏡子 :gray[(uses the camera 使用相機)]", key="lip_on")
            st.caption("The camera picture stays on this device and is not saved; you see a drawing of a mouth, not the picture. Use it only with the "
                       "permission of a parent or the school. 相機畫面只留在這台裝置、不會儲存，畫面上只會看到嘴巴的圖。須經家長或學校同意後使用。 "
                       "While testing, numbers about the lips and the sound (not the picture, not the voice) are saved on this computer. 測試期間，唇與聲音的數據（不含畫面與聲音）會存在這台電腦。")
        with bar_r:
            if lesson.phone in ("m", "n"):
                coach = st.toggle("**Coach** 教練 :gray[(lips and voice 嘴唇加聲音)]", key="lip_coach", value=True, disabled=not lip_on) and lip_on
                vowel = st.toggle("**Go on to a smile** 接著微笑", key="lip_vowel", value=True, disabled=not coach) and coach      # "me" = /m/ then /iː/
if lip_on:
    rec_col, mirror_col = st.columns([513, 640])
    with mirror_col:
        lipcam.lip_mirror(f"lip_{word}_{'vowel' if vowel else 'coach' if coach else 'mirror'}", coach=coach, noise_db=load_room(last_profile()), vowel=vowel, sound=lesson.phone,
                           log_url=camlog.url(), word=word)
else:
    _, rec_col, _ = st.columns([1, 1, 1])
with rec_col:
    record_block()
