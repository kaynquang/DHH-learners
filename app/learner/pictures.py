"""The small drawings of the learners' app: one picture per word for its meaning (the island pictures of the map are the same drawings), and one per sound.
All are drawn here with code (no outside artwork): they are the assistant's, to be replaced if the content owner supplies pictures."""

MEANING = {"see": "看見", "she": "她", "fee": "費用", "me": "我", "bee": "蜜蜂", "pea": "豌豆", "knee": "膝蓋", "cheat": "作弊"}

_INK, _OUT = "#1B2440", "#1B2440"
ART = {
    "sound": f'<rect x="38" y="30" width="24" height="52" rx="3" fill="#fff" stroke="{_OUT}" stroke-width="4"/>'
             '<rect x="38" y="44" width="24" height="9" fill="#E5484D"/><rect x="38" y="62" width="24" height="9" fill="#E5484D"/>'
             f'<rect x="35" y="22" width="30" height="10" rx="2" fill="#F5B400" stroke="{_OUT}" stroke-width="4"/>'
             f'<path d="M 40 22 L 50 10 L 60 22 Z" fill="#E5484D" stroke="{_OUT}" stroke-width="4" stroke-linejoin="round"/>'
             '<path d="M 18 26 L 33 27 M 82 26 L 67 27" stroke="#F5B400" stroke-width="4" stroke-linecap="round"/>',
    "see": f'<path d="M 8 50 C 28 18, 72 18, 92 50 C 72 82, 28 82, 8 50 Z" fill="#fff" stroke="{_OUT}" stroke-width="5" stroke-linejoin="round"/>'
           f'<circle cx="50" cy="50" r="19" fill="#2F6FE4" stroke="{_OUT}" stroke-width="4"/><circle cx="50" cy="50" r="9" fill="{_OUT}"/>'
           '<circle cx="44" cy="43" r="4.5" fill="#fff"/>',
    "she": f'<circle cx="50" cy="54" r="30" fill="#FFD9B8" stroke="{_OUT}" stroke-width="5"/>'
           f'<path d="M 20 52 C 18 20, 82 14, 80 52 C 70 38, 40 34, 20 52 Z" fill="#7A4A2B" stroke="{_OUT}" stroke-width="4" stroke-linejoin="round"/>'
           '<circle cx="76" cy="26" r="9" fill="#F25F9C" stroke="#1B2440" stroke-width="3"/>'
           f'<circle cx="40" cy="56" r="3.6" fill="{_INK}"/><circle cx="60" cy="56" r="3.6" fill="{_INK}"/>'
           f'<path d="M 40 68 C 46 76, 54 76, 60 68" fill="none" stroke="{_INK}" stroke-width="4" stroke-linecap="round"/>',
    "fee": f'<circle cx="50" cy="50" r="36" fill="#F5C242" stroke="{_OUT}" stroke-width="5"/><circle cx="50" cy="50" r="27" fill="none" stroke="#C78B00" stroke-width="3"/>'
           f'<text x="50" y="63" text-anchor="middle" font-family="Arial,sans-serif" font-weight="900" font-size="38" fill="{_INK}">$</text>',
    "me": f'<circle cx="50" cy="54" r="32" fill="#FFB7A1" stroke="{_OUT}" stroke-width="5"/>'
          f'<circle cx="39" cy="50" r="3.6" fill="{_INK}"/><circle cx="61" cy="50" r="3.6" fill="{_INK}"/>'
          '<circle cx="32" cy="62" r="5" fill="#F25F6B" opacity=".6"/><circle cx="68" cy="62" r="5" fill="#F25F6B" opacity=".6"/>'
          f'<path d="M 38 64 C 44 74, 56 74, 62 64" fill="none" stroke="{_INK}" stroke-width="4" stroke-linecap="round"/>'
          f'<polygon points="80,10 84,20 95,21 87,28 89,39 80,33 71,39 73,28 65,21 76,20" fill="#F5B400" stroke="{_OUT}" stroke-width="3" stroke-linejoin="round"/>',
    "bee": f'<ellipse cx="38" cy="30" rx="15" ry="11" fill="#E8F3FF" stroke="{_OUT}" stroke-width="3.5" transform="rotate(-20 38 30)"/>'
           f'<ellipse cx="62" cy="30" rx="15" ry="11" fill="#E8F3FF" stroke="{_OUT}" stroke-width="3.5" transform="rotate(20 62 30)"/>'
           f'<ellipse cx="50" cy="58" rx="30" ry="24" fill="#F5C242" stroke="{_OUT}" stroke-width="5"/>'
           f'<path d="M 38 36 L 38 80 M 52 34 L 52 82 M 66 38 L 66 78" stroke="{_INK}" stroke-width="7"/>'
           f'<circle cx="34" cy="56" r="3" fill="{_INK}"/><path d="M 40 18 L 34 8 M 58 18 L 64 8" stroke="{_INK}" stroke-width="3.5" stroke-linecap="round"/>',
    "pea": f'<path d="M 8 58 C 20 28, 70 24, 94 36 C 84 66, 30 82, 8 58 Z" fill="#6FBF4A" stroke="{_OUT}" stroke-width="5" stroke-linejoin="round"/>'
           f'<circle cx="34" cy="52" r="9" fill="#A9E27F" stroke="{_OUT}" stroke-width="3.5"/><circle cx="55" cy="49" r="9" fill="#A9E27F" stroke="{_OUT}" stroke-width="3.5"/>'
           f'<circle cx="75" cy="46" r="9" fill="#A9E27F" stroke="{_OUT}" stroke-width="3.5"/>',
    "knee": f'<path d="M 36 12 L 62 12 L 62 54 L 82 70 C 90 78, 82 90, 70 88 L 36 86 Z" fill="#CFE0F7" stroke="{_OUT}" stroke-width="5" stroke-linejoin="round"/>'
            '<rect x="36" y="12" width="26" height="12" fill="#C0524F" stroke="#1B2440" stroke-width="4"/>'
            f'<path d="M 36 36 L 62 36 M 36 48 L 62 48" stroke="{_INK}" stroke-width="4"/>',
    "cheat": f'<rect x="16" y="16" width="68" height="68" rx="14" fill="#fff" stroke="{_OUT}" stroke-width="6"/>'
             f'<polygon points="50,28 56,43 72,44 60,54 64,70 50,61 36,70 40,54 28,44 44,43" fill="#fff" stroke="{_OUT}" stroke-width="5" stroke-linejoin="round"/>',
}


def svg_of(inner: str, label: str) -> str:
    return f'<svg viewBox="0 0 100 100" role="img" aria-label="{label}">{inner}</svg>'


# The picture of the SOUND of each word, for the left circle of the word card ("see" keeps the content owner's snake, in lessons.py): what the sound is like, drawn simply.
SOUND_ART = {
    "she": (f'<path d="M 22 66 C 22 52, 78 52, 78 66 C 78 80, 22 80, 22 66 Z" fill="#F07C86" stroke="{_OUT}" stroke-width="4.5" stroke-linejoin="round"/>'          # lips
            f'<path d="M 26 66 C 40 62, 60 62, 74 66" fill="none" stroke="{_OUT}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<rect x="43" y="14" width="15" height="62" rx="7.5" fill="#FFD9B8" stroke="{_OUT}" stroke-width="4.5"/>'                                           # the finger
            f'<path d="M 18 28 C 10 36, 10 46, 18 54 M 82 28 C 90 36, 90 46, 82 54" fill="none" stroke="{_OUT}" stroke-width="4" stroke-linecap="round"/>',
            "Finger on the lips – hush"),
    "fee": (f'<path d="M 22 82 C 18 50, 42 20, 80 16 C 82 52, 58 82, 22 82 Z" fill="#9ED8F6" stroke="{_OUT}" stroke-width="4.5" stroke-linejoin="round"/>'          # a feather
            f'<path d="M 22 82 L 70 28" fill="none" stroke="{_OUT}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<path d="M 8 40 C 18 34, 26 44, 36 38 M 6 56 C 16 50, 24 60, 34 54" fill="none" stroke="#2F6FE4" stroke-width="4" stroke-linecap="round"/>',
            "Feather in a soft breath"),
    "pea": (f'<rect x="52" y="44" width="14" height="46" rx="4" fill="#fff" stroke="{_OUT}" stroke-width="4.5"/>'                                              # a candle bent by a puff
            f'<path d="M 59 44 L 59 38" stroke="{_OUT}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<path d="M 59 38 C 46 26, 58 14, 66 8 C 72 20, 80 30, 66 38 Z" transform="rotate(18 59 38)" fill="#F5B400" stroke="{_OUT}" stroke-width="3.5" stroke-linejoin="round"/>'
            f'<path d="M 8 52 L 36 52 M 6 64 L 32 64 M 12 76 L 34 76" fill="none" stroke="#2F6FE4" stroke-width="4.5" stroke-linecap="round"/>',
            "A small puff blowing a candle flame"),
    "bee": (f'<ellipse cx="50" cy="42" rx="26" ry="30" fill="#E5484D" stroke="{_OUT}" stroke-width="4.5"/>'                                                  # a balloon that pops
            f'<path d="M 50 72 L 44 80 L 56 80 Z" fill="#B8323A" stroke="{_OUT}" stroke-width="3.5" stroke-linejoin="round"/>'
            f'<path d="M 50 80 C 44 88, 56 92, 50 98" fill="none" stroke="{_OUT}" stroke-width="3" stroke-linecap="round"/>'
            f'<ellipse cx="40" cy="30" rx="6" ry="9" transform="rotate(20 40 30)" fill="#fff" opacity=".7"/>',
            "A balloon"),
    "me": (f'<circle cx="50" cy="56" r="32" fill="#FFD9B8" stroke="{_OUT}" stroke-width="4.5"/>'                                                              # a face humming with the lips shut
           f'<path d="M 30 48 C 34 44, 40 44, 44 48 M 56 48 C 60 44, 66 44, 70 48" fill="none" stroke="{_OUT}" stroke-width="4" stroke-linecap="round"/>'
           f'<path d="M 38 70 L 62 70" stroke="{_OUT}" stroke-width="5" stroke-linecap="round"/>'
           f'<circle cx="82" cy="22" r="6" fill="#2F6FE4"/><path d="M 87 22 L 87 6 L 96 10" fill="none" stroke="#2F6FE4" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
           "A humming face with a music note"),
    "knee": (f'<path d="M 30 70 C 30 40, 40 24, 56 24 C 70 24, 74 40, 66 52 C 62 60, 70 64, 66 74 C 60 86, 34 88, 30 70 Z" fill="#FFD9B8" stroke="{_OUT}" stroke-width="4.5" stroke-linejoin="round"/>'   # a nose
             f'<circle cx="46" cy="72" r="4" fill="{_OUT}"/><circle cx="60" cy="74" r="4" fill="{_OUT}"/>'
             f'<path d="M 14 80 C 14 66, 20 58, 28 56 M 20 34 C 14 26, 18 16, 28 14" fill="none" stroke="#2F6FE4" stroke-width="4" stroke-linecap="round"/>'
             f'<circle cx="84" cy="22" r="6" fill="#2F6FE4"/><path d="M 89 22 L 89 6 L 98 10" fill="none" stroke="#2F6FE4" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
             "A nose with a hum"),
    "cheat": (f'<rect x="16" y="46" width="52" height="30" rx="6" fill="#2F6FE4" stroke="{_OUT}" stroke-width="4.5"/>'                                        # a train that goes choo-choo
              f'<rect x="52" y="30" width="22" height="20" rx="3" fill="#6B94EA" stroke="{_OUT}" stroke-width="4"/>'
              f'<rect x="20" y="30" width="12" height="18" rx="2" fill="{_OUT}"/>'
              f'<circle cx="30" cy="80" r="9" fill="{_OUT}"/><circle cx="58" cy="80" r="9" fill="{_OUT}"/>'
              f'<circle cx="22" cy="18" r="7" fill="#fff" stroke="#9AA6BD" stroke-width="3.5"/><circle cx="12" cy="8" r="5" fill="#fff" stroke="#9AA6BD" stroke-width="3"/>'
              f'<path d="M 78 60 L 94 60" stroke="{_OUT}" stroke-width="5" stroke-linecap="round"/>',
              "A train going choo-choo"),
}
# what is written under the two circles of each word card (English, Chinese): the Chinese is made to be easy for a child
SOUND_CAPTION = {"see": ("Hiss: sssss", "嘶嘶聲"), "she": ("Hush: shhh", "噓～安靜聲"), "fee": ("Soft air: fff", "輕輕吹氣聲"), "pea": ("Small puff: p", "噗！小小的氣"),
                 "bee": ("Pop: b", "啵！輕輕張開"), "me": ("Hum: mmm", "閉嘴哼哼聲"), "knee": ("Hum: nnn", "鼻子哼哼聲"), "cheat": ("Choo-choo: ch", "嗤！火車聲")}
