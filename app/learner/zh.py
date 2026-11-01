"""Traditional Chinese for the words of the result panel. The scoring package (app/fricative) is shared with the Dev app and writes its labels, messages and tips in English;
the learners' screen shows each of them with its Chinese beside it. The Chinese is written by the assistant, to be easy for a child (short, everyday words): to be reviewed by the
content owner. A text with no translation here is shown in English alone, never invented."""
from __future__ import annotations

import re

from fricative import affricate, classify, nasals, stops

LABEL = {"Correct": "正確", "Almost": "快對了", "Not yet": "還沒有"}

_TIP = {
    classify.TIPS["s"]: "舌尖放在上排牙齒後面一點點，嘴唇微微向兩旁拉開，吹出又細又有力的氣。",
    classify.TIPS["sh"]: "舌頭往後縮一點，嘴唇圓圓地往前，氣比 /s/ 吹得更寬一點。",
    classify.TIPS["f"]: "上排牙齒輕輕碰下嘴唇，從小縫隙輕輕吹氣。",
    stops.TIPS["p"]: "嘴唇閉起來，把氣留住，再「噗」一下放開，像吹蠟燭，然後才說後面的音。",
    stops.TIPS["b"]: "嘴唇閉起來，放開的時候馬上出聲，前面不要噗氣。",
    nasals.TIPS["m"]: "兩片嘴唇閉起來，讓聲音從鼻子哼出來，然後再張開。",
    nasals.TIPS["n"]: "舌尖頂在上排牙齒後面，嘴唇微微打開，讓聲音從鼻子哼出來。",
    affricate.TIP: "舌頭先頂住上顎，突然放開，變成短短的「噓」聲，嘴唇圓圓的。",
}
_EXACT = {
    "Well done. Keep the same tongue and lip position.": "做得好！保持同樣的舌頭和嘴唇位置。",
    "Well done. Keep the same movement.": "做得好！保持同樣的動作。",
    "Well done. Keep the same lip release.": "做得好！保持同樣的嘴唇放開方式。",
    "Well done. Keep the same lip and tongue position.": "做得好！保持同樣的嘴唇和舌頭位置。",
    "Well done. Keep the abrupt start.": "做得好！保持這個突然的開頭。",
    "The sound seems to go through the nose. Keep the nose closed and let the air burst out of the lips. ": "聽起來聲音從鼻子跑出去了。把鼻子關起來，讓氣從嘴唇噗出去。",
    "No vowel after the hiss, so /f/ could not be checked.": "嘶聲後面沒有聽到母音，所以還不能檢查 /f/。",
    "No speech was heard in this recording.": "這次錄音裡沒有聽到聲音。",
    "Not sure which sound this was.": "聽不出這是哪個音。",
    "This sound cannot be scored yet.": "這個音還不能評分。",
    "No consonant was heard at the start.": "開頭沒有聽到子音。",
    "The hiss is too short to measure.": "嘶聲太短，量不到。",
    "No hiss was found.": "沒有聽到嘶聲。",
    "No hiss found": "沒有聽到嘶聲。",
    "No burst found": "沒有聽到「噗」的氣。",
    "No voicing after the burst": "「噗」之後沒有聽到聲音。",
    "The recogniser did not confirm this sound, so it cannot be green.": "電腦沒有確認這個聲音，所以不能給綠色。",
    "No /s ʃ f/ sound was heard in the hiss.": "嘶聲裡沒有聽到 /s ʃ f/。",
    "Not yet: keep the dot in the green": "還沒到：讓圓點留在綠色裡",
}
_PATTERN = [
    (re.compile(r"^You said (/.+/)$"), r"你說的是 \1"),
    (re.compile(r"^You held (/.+/)$"), r"你把 \1 說得很穩"),
    (re.compile(r"^Nearly: hold (/.+/) a little longer$"), r"快好了：\1 再撐久一點"),
    (re.compile(r"^([\d.]+) s of hiss, ([\d.]+) s in the green(; then the smile)?$"), lambda m: f"嘶聲 {m[1]} 秒，其中 {m[2]} 秒在綠色裡" + ("；然後微笑" if m[3] else "")),
    (re.compile(r"^A different kind of sound was heard at the start \((.+)\)\.$"), r"開頭聽到的是別種聲音（\1）。"),
    (re.compile(r"^The sound before the vowel lasts (\d+) ms, which is a long hiss rather than a stop burst\.?$"), r"母音前的聲音拖了 \1 毫秒，比較像長長的嘶聲，不像「噗」。"),
]


def translate(text: str) -> str:
    """The Chinese of a result text, or "" when there is none (the English then stands alone)."""
    if not text:
        return ""
    t = text.strip()
    if t in LABEL:
        return LABEL[t]
    if text in _EXACT:
        return _EXACT[text]
    if t in _EXACT:
        return _EXACT[t]
    if t in _TIP:
        return _TIP[t]
    if t.startswith("Close. ") and t[len("Close. "):] in _TIP:
        return "很接近了。" + _TIP[t[len("Close. "):]]
    for rule, out in _PATTERN:
        if rule.match(t):
            return rule.sub(out, t)
    for en, zh in _EXACT.items():                      # a tip that starts with a known sentence (the nose warning in front of a tip)
        if en.endswith(" ") and t.startswith(en.strip()):
            rest = t[len(en.strip()):].strip()
            return zh + (_TIP.get(rest, ""))
    return ""
