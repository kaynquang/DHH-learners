"""Sound Check: the learner-side set-up (open it with ?page=sound). Built from the Sound Check mockup.

Three phases: 1) the room (3 s of silence gives the noise level), 2) a long "aaa" said twice, from which the size of the child's voice is
measured (fricative/vtl.py), 3) check and save. The child is NOT asked to say the target sounds: for a learner who is deaf or hard of
hearing /s/ /ʃ/ /f/ are the sounds being learned, so they cannot be the reference. The voice size only moves the /s/-/ʃ/ boundary used for
/s/ /ʃ/ /f/; the other sounds are scored without it, so the whole check can be skipped. Nothing here needs hearing: states are colours,
faces and words. Children are kept in the folder the Dev app uses (fricative/calibrated.py).
"""
from __future__ import annotations

from html import escape

import numpy as np
import streamlit as st

from fricative import config as C
from fricative import vtl
from fricative.audio import limit_duration, load
from fricative.calibrated import clean_name, delete_profile, last_profile, list_profiles, load_room, load_voice, remember_profile, save_voice

from . import children
from fricative.noise import ROOM_NOISY_DBFS, ROOM_QUIET_DBFS, check, noise_floor_db, room_verdict

from . import stars
from .mic import mic

PHASES = (("Quiet", "安靜"), ("Voice", "聲音"), ("Ready", "準備好"))
FACE = {"good": "😊", "ok": "😐", "noisy": "😟"}
ROOM_TEXT = {"good": ("Quiet enough!", "夠安靜了！"), "ok": ("A bit noisy, still OK", "有點吵，還可以"),
             "noisy": ("Too noisy. Try a quieter place", "太吵了，換個安靜的地方")}
WORD_TEXT = {"good": ("Clear!", "很清楚！"), "ok": ("A bit noisy, still OK", "有點吵，還可以"),
             "noisy": ("Too noisy. Say it again", "太吵了，再說一次")}

CSS = """
.st-key-sc_top button { min-height: 44px; border-radius: 999px; border: 1.5px solid var(--line); background: #fff; color: var(--ink); font-weight: 800; padding: 0 16px; }
[class*="st-key-sc_"] button[kind="primary"] { background: #2F6FE4; border-color: #2F6FE4; color: #fff; font-weight: 800; min-height: 46px; border-radius: 999px; box-shadow: 0 4px 0 #1F4FB0; }
[class*="st-key-sc_"] button[kind="primary"]:disabled { background: #fff; border-color: var(--line); color: #8A96B0; box-shadow: none; }
[class*="st-key-sc_"] button[kind="secondary"] { min-height: 46px; border-radius: 999px; border: 1.5px solid var(--line); background: #fff; color: var(--ink); font-weight: 800; }
.sc-chip { white-space: nowrap; padding: 10px 18px; border-radius: 999px; background: #FFF3C4; border: 1.5px solid #F2B705; color: var(--ink); font-weight: 700; font-size: 15px; }
.sc-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; color: var(--ink); }
.sc-title { font-size: 20px; font-weight: 900; line-height: 1.1; } .sc-title span { display: block; font-size: 14px; font-weight: 500; color: var(--ink2); }
.sc-pills { display: flex; gap: 8px; }
.sc-pill { display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; border: 1.5px solid var(--line); background: #fff;
  font-size: 13px; font-weight: 800; color: var(--ink2); line-height: 1.1; }
.sc-pill b { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--line); display: grid; place-items: center; font-size: 13px; }
.sc-pill.on { background: #FFF3C4; border-color: #F2B705; color: var(--ink); } .sc-pill.on b { border-color: #F2B705; background: #fff; }
.sc-pill.done b { background: #1FA45B; border-color: #1FA45B; color: #fff; }
.sc-h1 { font-size: 36px; font-weight: 900; color: var(--ink); line-height: 1.15; margin: 8px 0 0; }
.sc-h1 .zh { display: block; font-size: 22px; font-weight: 600; color: var(--ink2); }
.sc-p { font-size: 16px; color: var(--ink); margin: 6px 0 0; } .sc-p .zh { color: var(--ink2); }
.sc-card { background: #fff; border: 1.5px solid var(--line); border-radius: 20px; box-shadow: 0 4px 0 var(--line); padding: 18px 20px; color: var(--ink); }
.sc-bar { height: 28px; border-radius: 999px; position: relative; overflow: visible;
  background: linear-gradient(90deg, #BFE3C9 0 33%, #FFF1B8 33% 66%, #FFD3D8 66% 100%); border: 1.5px solid var(--line); }
.sc-bar i { position: absolute; top: -6px; width: 6px; height: 38px; border-radius: 3px; background: var(--ink); transform: translateX(-50%); }
.sc-bar-l { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-top: 8px; color: var(--ink2); }
.sc-state { display: flex; align-items: center; gap: 14px; border-radius: 20px; padding: 16px 20px; border: 2px solid; font-size: 22px; font-weight: 900; color: var(--ink); }
.sc-state .zh { display: block; font-size: 16px; font-weight: 500; color: var(--ink2); } .sc-state .f { font-size: 34px; }
.sc-state.good { background: #EAF7EE; border-color: #1FA45B; } .sc-state.ok { background: #FFF8DC; border-color: #F2B705; } .sc-state.noisy { background: #FDECEE; border-color: #D9363E; }
.sc-tips { border: 2px dashed var(--line); border-radius: 20px; padding: 28px 16px; text-align: center; color: var(--ink2); font-weight: 700; }
.sc-words { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.sc-word { background: #fff; border: 2px solid var(--line); border-radius: 18px; padding: 10px; text-align: center; color: var(--ink); }
.sc-word.on { background: #FFF3C4; border-color: #F2B705; }
.sc-word .pic { border: 2px dashed var(--line); border-radius: 12px; font-size: 12px; color: var(--ink2); padding: 18px 4px; margin-bottom: 8px; }
.sc-word b { display: block; font-size: 30px; font-weight: 900; }
.sc-dots { display: flex; gap: 10px; justify-content: center; margin: 4px 0 10px; }
.sc-dots i { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--line); background: #fff; display: grid; place-items: center; font-style: normal; font-weight: 800; font-size: 13px; color: var(--ink2); }
.sc-dots i.done { background: #1FA45B; border-color: #1FA45B; color: #fff; } .sc-dots i.on { background: #F2B705; border-color: #F2B705; color: var(--ink); }
.sc-ok { display: flex; gap: 12px; align-items: center; font-size: 20px; font-weight: 900; color: var(--ink); }
.sc-ok .tick { width: 44px; height: 44px; border-radius: 50%; background: #1FA45B; color: #fff; display: grid; place-items: center; font-size: 26px; }
.sc-ok .zh { display: block; font-size: 14px; font-weight: 500; color: var(--ink2); }
.sc-tbl { width: 100%; border-collapse: collapse; font-size: 13px; color: var(--ink); } .sc-tbl th, .sc-tbl td { text-align: right; padding: 5px 6px; border-bottom: 1px solid var(--line); }
.sc-tbl th:first-child, .sc-tbl td:first-child { text-align: left; } .sc-note { font-size: 12px; color: var(--ink2); margin-top: 8px; }
"""


def _bil(en: str, zh: str) -> str:
    return f'{escape(en)} <span class="zh">{escape(zh)}</span>'


def _header(phase: int) -> str:
    pills = "".join(f'<div class="sc-pill {"on" if i == phase else "done" if i < phase else ""}"><b>{"✓" if i < phase else i + 1}</b>'
                    f'<span>{en}<br>{zh}</span></div>' for i, (en, zh) in enumerate(PHASES))
    return f'<div class="sc-head"><div class="sc-title">Sound Check<span>聲音檢查</span></div><div class="sc-pills">{pills}</div></div>'


def _room_bar(noise_db: float | None) -> str:
    marker = ""
    if noise_db is not None:                                   # the bar spans -70 dBFS .. -30 dBFS, split at the two room limits
        pos = min(max((noise_db + 70) / 40, 0.02), 0.98) * 100
        marker = f'<i style="left:{pos:.0f}%"></i>'
    zones = f"linear-gradient(90deg, #BFE3C9 0 {(ROOM_QUIET_DBFS + 70) / 40 * 100:.0f}%, #FFF1B8 0 {(ROOM_NOISY_DBFS + 70) / 40 * 100:.0f}%, #FFD3D8 0)"
    return (f'<div class="sc-card"><div class="sc-bar" style="background:{zones}">{marker}</div>'
            f'<div class="sc-bar-l"><span>Quiet 安靜</span><span>A bit noisy 有點吵</span><span>Too noisy 太吵</span></div></div>')


def _state(kind: str, text: tuple[str, str]) -> str:
    return f'<div class="sc-state {kind}"><span class="f">{FACE[kind]}</span><span>{escape(text[0])}<span class="zh">{escape(text[1])}</span></span></div>'


RECORDING_PROBLEM = {"noisy": ("Too noisy. Find a quieter place and try again", "太吵了，換個安靜的地方再試一次"),
                     "quiet": ("Too quiet. Say it a little louder", "聲音太小，再大聲一點"),
                     "loud": ("Too loud. Move a little away from the microphone", "聲音太大，離麥克風遠一點")}


def recording_problem(problem: str) -> str:
    """What the child sees instead of a score when the recording cannot be trusted (see fricative/noise.py: recording_quality)."""
    return f'<div style="padding:8px 0">{_state("noisy", RECORDING_PROBLEM[problem])}</div>'


def leave() -> None:
    """Back to the map."""
    st.query_params.clear()
    st.query_params["page"] = "map"


FLOW_KEYS = ("sc_phase", "sc_noise", "sc_tokens", "sc_attempt", "sc_cal")


def _reset_flow() -> None:
    """Forget the recordings of the check in progress (the saved profiles stay as they are)."""
    for k in list(st.session_state):
        if k in FLOW_KEYS or k.startswith("sc_mic_"):
            del st.session_state[k]


def _start_draft(name: str, gender: str | None = None) -> None:
    """Record this child now. Nothing is written to the list until the last step's Save."""
    _reset_flow()
    st.session_state["sc_draft"] = name
    st.session_state["sc_draft_gender"] = gender
    st.session_state.pop("sc_confirm", None)


GENDER_LABELS = {"boy": "👦 Boy 男生", "girl": "👧 Girl 女生"}          # the face next to the name on the home page


def _cancel_draft() -> None:
    _reset_flow()
    st.session_state.pop("sc_draft", None)


def _taken(name: str) -> bool:
    return name.casefold() in {n.casefold() for n in list_profiles()}


def _profile_picker() -> str | None:
    """The saved children and the button that adds a new one (a name already in the list is refused)."""
    names = list_profiles()
    current = last_profile()
    name = (st.selectbox("Child 學生", names, index=names.index(current) if current in names else 0, key="sc_profile",
                         label_visibility="collapsed", width=260) if names else None)
    with st.popover("＋ Child 新增學生"):
        new = st.text_input("Name 名字", key="sc_newname")
        gender = st.radio("Boy or girl 男生或女生", list(GENDER_LABELS), format_func=GENDER_LABELS.get, index=None, horizontal=True, key="sc_newgender")
        if st.button("Add and record 新增並錄製", key="sc_add"):
            cleaned = clean_name(new)
            if not cleaned:
                st.error("Please type a name · 請輸入名字")
            elif _taken(cleaned):
                st.error(f"“{cleaned}” is already in the list · 這個名字已被使用")
            elif gender is None:
                st.error("Please choose boy or girl · 請選擇男生或女生")
            else:
                _start_draft(cleaned, gender)
                st.rerun()
    return name


def _next_attempt() -> int:
    return st.session_state.setdefault("sc_attempt", 0)


def _again() -> None:
    st.session_state["sc_attempt"] = _next_attempt() + 1


def _room_step() -> None:
    attempt = _next_attempt()
    key = f"sc_mic_room_{attempt}"
    left, right = st.columns([640, 360], gap="large")
    with right:
        slot = st.empty()
        wav = st.session_state.get(f"{key}_wav")
        if wav is None:
            with slot.container():
                mic(key)
            wav = st.session_state.get(f"{key}_wav")
        if wav is not None:
            slot.empty()
    with left:
        st.html(f'<div class="sc-h1">Shh... is it quiet?<span class="zh">噓...這裡安靜嗎？</span></div>'
                f'<div class="sc-p">Stay still and quiet for 3 seconds. <span class="zh">不動不說 3 秒。</span></div>')
        noise = noise_floor_db(load(wav, "recording.wav")) if wav is not None else None
        st.html(_room_bar(noise))
        if noise is not None:
            kind = room_verdict(noise)
            st.html(_state(kind, ROOM_TEXT[kind]))
        else:
            st.html('<div class="sc-tips">Tap the microphone, then stay quiet · 按麥克風，然後保持安靜</div>')
        a, b = st.columns(2)
        a.button("Check again 再檢查", key="sc_room_again", width="stretch", on_click=_again, disabled=noise is None)
        if b.button("Next 下一步", key="sc_room_next", type="primary", width="stretch", disabled=noise is None):
            st.session_state["sc_noise"] = noise
            st.session_state["sc_phase"] = 1
            st.session_state["sc_attempt"] = 0
            st.rerun()
        st.html('<div class="sc-tips">Setup tips / picture<br>設定提示／圖片<br>— to be added 待補 —</div>')


def _measure(wav: bytes, noise_db: float):
    """(vowel, room check) for a recording of a long "aaa", or (None, None) when no steady voiced vowel can be found in it."""
    sound, _ = limit_duration(load(wav, "recording.wav"))
    return vtl.measure_vowel(sound), check(noise_db, sound)


N_TAKES = 2          # "aaa" is said this many times; the voice size is the middle of them


def _voice_step() -> None:
    takes = st.session_state.setdefault("sc_tokens", [])
    n = len(takes)
    attempt = _next_attempt()
    key = f"sc_mic_voice_{n}_{attempt}"
    noise_db = st.session_state.get("sc_noise")
    left, right = st.columns([640, 360], gap="large")
    with left:
        st.html('<div class="sc-h1">Say “aaa”<span class="zh">說長長的「啊」</span></div>'
                '<div class="sc-p">Press <b>Space</b>, then say a long “aaa”. Do it 2 times. <span class="zh">按空白鍵，說一個長長的「啊」。說 2 次。</span></div>')
        st.html('<div class="sc-words"><div class="sc-word on" style="grid-column: 1 / -1"><div class="pic">picture<br>to be added 待補</div><b>aaa</b></div></div>')
        st.html('<div class="sc-dots">' + "".join(f'<i class="{"done" if i < n else "on" if i == n else ""}">{i + 1}</i>' for i in range(N_TAKES)) + "</div>")
    with right:
        slot = st.empty()
        wav = st.session_state.get(f"{key}_wav")
        if wav is None:
            with slot.container():
                mic(key)
            wav = st.session_state.get(f"{key}_wav")
        if wav is not None:
            slot.empty()
    if wav is None:
        return
    with left:
        vowel, room = _measure(wav, noise_db if noise_db is not None else -90.0)
        if vowel is None:                        # no steady voiced sound: not an "aaa" to measure the voice from
            st.html(_state("noisy", ("Let's try again", "再試一次")))
        elif noise_db is None:
            st.html(_state("good", ("Got it!", "收到了！")))
        else:
            st.html(_state(room.verdict, WORD_TEXT[room.verdict]))
        a, b = st.columns(2)
        a.button("Say again 再說一次", key=f"sc_voice_again_{n}", width="stretch", on_click=_again)
        if b.button("Next 下一步", key=f"sc_voice_next_{n}", type="primary", width="stretch", disabled=vowel is None):
            takes.append(dict(f3_hz=vowel.f3_hz, speech_db=room.speech_db, snr=room.snr_db if noise_db is not None else None))
            st.session_state["sc_attempt"] = 0
            if len(takes) == N_TAKES:
                st.session_state["sc_phase"] = 2
            st.rerun()


def _details(takes: list[dict], noise: float | None, voice: dict | None = None) -> None:
    """The measured numbers (for the teacher)."""
    with st.expander("Teacher details 老師用數據", expanded=False):
        f3 = float(np.median([t["f3_hz"] for t in takes])) if takes else None
        scale = vtl.scale_from(f3) if f3 else None
        def cell(v, fmt="{:.1f}"):
            return fmt.format(v) if v is not None else "–"
        rows = [("Noise level (dBFS) 噪音", [cell(noise)] * len(takes)),
                ("Voice level (dBFS) 音量", [cell(t.get("speech_db")) for t in takes]),
                ("SNR (dB) 訊噪比", [cell(t.get("snr")) for t in takes]),
                ("F3 of “aaa” (Hz) 第三共振峰", [cell(t["f3_hz"], "{:.0f}") for t in takes])]
        head = "<tr><th>Measure</th>" + "".join(f"<th>#{i + 1}</th>" for i in range(len(takes))) + "</tr>"
        body = "".join(f"<tr><td>{escape(name)}</td>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>" for name, cells in rows)
        st.html(f'<table class="sc-table sc-tbl">{head}{body}</table>'
                f'<div class="sc-note"><b>Voice size 聲音大小: ×{cell(scale, "{:.2f}")}</b> (F3 {cell(f3, "{:.0f}")} Hz ÷ {vtl.REF_F3_HZ:.0f} Hz adult reference). '
                f'It moves the /s/–/ʃ/ boundary from {C.DEFAULT_THRESHOLDS.cog_s_sh_hz:.0f} Hz to {C.DEFAULT_THRESHOLDS.cog_s_sh_hz * (scale or 1):.0f} Hz. '
                'The child is not asked to say /s/ /ʃ/ /f/ correctly. This scale is provisional (not yet checked on children). '
                'Peak / clipping and mic distance: not yet measured 尚未測量。</div>')


def _tick_cards(noise: float | None, n_takes: int) -> None:
    quiet = noise is not None and room_verdict(noise) != "noisy"
    st.html('<div class="sc-card"><div class="sc-ok"><span class="tick">✓</span><span>'
            + (_bil("Room is quiet", "房間已檢查") if quiet else _bil("Room check skipped or noisy", "房間未檢查或太吵")) + "</span></div></div>")
    st.html(f'<div class="sc-card"><div class="sc-ok"><span class="tick">✓</span><span>{_bil(f"Voice recorded ({n_takes}×)", f"已錄聲音（{n_takes} 次）")}</span></div></div>')


def _save(name: str) -> None:
    """The last step: only now is the child written to the list (a re-recorded child replaces the old numbers)."""
    ss = st.session_state
    save_voice(name, ss["sc_tokens"], ss.get("sc_noise"))
    if ss.get("sc_draft_gender"):                   # a new child; a child recorded again keeps what was chosen before
        children.set_gender(name, ss["sc_draft_gender"])
    remember_profile(name)
    ss["sc_just_saved"] = name
    ss.pop("sc_profile", None)                  # the picker opens on the child just saved
    _cancel_draft()


def _start_play(name: str) -> None:
    remember_profile(name)                      # the lessons use this child's voice size
    leave()


def _ready_step(draft: str) -> None:
    takes = st.session_state["sc_tokens"]
    noise = st.session_state.get("sc_noise")
    st.html(f'<div class="sc-h1">Check your recordings<span class="zh">請確認錄音</span></div>'
            f'<div class="sc-p">Child 學生: <b>{escape(draft)}</b></div>')
    left, right = st.columns([640, 360], gap="large")
    with left:
        _tick_cards(noise, len(takes))
        st.button("💾 Save 儲存", key="sc_save", type="primary", width="stretch", on_click=_save, args=(draft,))
        st.button("Record again 再錄一次", key="sc_redo", width="stretch", on_click=_start_draft, args=(draft,))
        st.caption("Not in the list until you press Save · 按「儲存」後才會加入名單")
    with right:
        _details(takes, noise)

def _delete(name: str) -> None:
    delete_profile(name)
    stars.forget(name)
    children.forget(name)
    if last_profile() is None:                  # the child just deleted was the one in use
        remember_profile(None)
    for k in ("sc_profile", "sc_confirm", "sc_confirm_del", "sc_just_saved"):
        st.session_state.pop(k, None)


def _delete_controls(name: str) -> None:
    """Delete this child from the list, after a yes."""
    if st.session_state.get("sc_confirm_del") == name:
        st.html(f'<div class="sc-state noisy"><span class="f">🗑️</span><span>Delete “{escape(name)}”?'
                '<span class="zh">要刪除這位學生嗎？刪除後無法復原。</span></span></div>')
        a, b = st.columns(2)
        a.button("Yes, delete 是，刪除", key="sc_del_yes", type="primary", width="stretch", on_click=_delete, args=(name,))
        b.button("No, keep 否，保留", key="sc_del_no", width="stretch", on_click=lambda: st.session_state.pop("sc_confirm_del", None))
    else:
        st.button("🗑️ Delete child 刪除學生", key="sc_del_ask", width="stretch", on_click=lambda: st.session_state.update(sc_confirm_del=name))


def _gender_control(name: str) -> None:
    """Boy or girl, for a saved child (the face on the home page); it can be changed at any time."""
    key = f"sc_gender_{name}"
    st.segmented_control("Boy or girl 男生或女生", list(GENDER_LABELS), format_func=GENDER_LABELS.get, default=children.gender(name), key=key,
                         on_change=lambda: children.set_gender(name, st.session_state.get(key)))


def _view(name: str | None) -> None:
    """A saved child: the numbers are fixed. Recording again needs a yes."""
    if name is None:
        st.html('<div class="sc-h1">Add a child to begin<span class="zh">新增學生以開始</span></div>'
                '<div class="sc-p">Press “＋ Child” above. <span class="zh">按上方「＋ Child」。</span></div>')
        return
    data = load_voice(name)
    if data is None:                                         # a profile made elsewhere that was never recorded
        st.html(f'<div class="sc-h1">{escape(name)}<span class="zh">還沒有錄音</span></div>'
                '<div class="sc-p">No recordings yet. <span class="zh">尚未錄音。</span></div>')
        st.button("Record 開始錄製", key="sc_record_new", type="primary", on_click=_start_draft, args=(name,))
        _delete_controls(name)
        return
    tokens = data["takes"]
    noise = load_room(name)
    st.html(f'<div class="sc-h1">{escape(name)}<span class="zh">已儲存的聲音檢查</span></div>')
    if st.session_state.get("sc_just_saved") == name:
        st.success("Saved to the list · 已加入名單")
    left, right = st.columns([640, 360], gap="large")
    with left:
        _tick_cards(noise, len(tokens))
        _gender_control(name)
        st.button("▶ Start 開始", key="sc_start", type="primary", width="stretch", on_click=_start_play, args=(name,))
        if st.session_state.get("sc_confirm") == name:
            st.html('<div class="sc-state ok"><span class="f">❓</span><span>Record this child again?'
                    '<span class="zh">要重新錄製這位學生嗎？舊的數據會在你按「儲存」後被取代。</span></span></div>')
            a, b = st.columns(2)
            a.button("Yes, record again 是，重新錄製", key="sc_yes", type="primary", width="stretch", on_click=_start_draft, args=(name,))
            b.button("No, keep it 否，保留", key="sc_no", width="stretch", on_click=lambda: st.session_state.pop("sc_confirm", None))
        else:
            st.button("Record again 再錄一次", key="sc_again_ask", width="stretch", on_click=lambda: st.session_state.update(sc_confirm=name))
        _delete_controls(name)
    with right:
        _details(tokens, noise)


def render() -> None:
    draft = st.session_state.get("sc_draft")
    selected = None
    with st.container(key="sc_top", horizontal=True, vertical_alignment="center"):
        st.button("← Map 地圖", key="sc_back", on_click=leave)
        if draft:
            st.html(f'<div class="sc-chip">Recording 錄製中: <b>{escape(draft)}</b></div>')
            st.button("Cancel 取消", key="sc_cancel", on_click=_cancel_draft)
        else:
            selected = _profile_picker()
        st.button("Skip for now 先跳過", key="sc_skip", on_click=leave)
    if not draft:
        for k in ("sc_confirm", "sc_confirm_del"):      # a question belongs to the child it was asked about
            if st.session_state.get(k) not in (None, selected):
                st.session_state.pop(k, None)
        _view(selected)
        return
    phase = st.session_state.setdefault("sc_phase", 0)
    st.html(_header(phase))
    (_room_step, _voice_step)[phase]() if phase < 2 else _ready_step(draft)

