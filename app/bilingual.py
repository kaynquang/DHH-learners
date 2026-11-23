"""Traditional Chinese (Taiwan) next to the English of the Dev/teacher app.

The learner app writes its two languages by hand. For the Dev app, whose pages are many and whose texts are short labels, one table (ZH below) maps an English
text to its Chinese; install(st) wraps the Streamlit calls that show text so that a text found in the table is shown as "English 中文". A text that is not in
the table (long technical explanations, texts built from numbers) is shown as it is. Options of a choice keep their English value (the code compares them);
only their label shows both languages.

The Chinese was written by the assistant and has not been reviewed by a native speaker.
"""
from __future__ import annotations

ZH = {
    # navigation and sidebar
    "Practice": "練習", "Teacher view": "教師檢視", "Calibrate": "校正", "Log": "紀錄", "Rate": "評分", "Camera log": "相機紀錄", "How it works": "運作原理",
    "Profile": "個人檔案", "Add profile": "新增個人檔案", "Profile name": "檔案名稱", "Create": "建立", "Delete this profile": "刪除此個人檔案",
    # practice
    "Fricative practice": "摩擦音練習", "Say one word. See where your hiss lands.": "念一個單字，看看你的噓聲落在哪裡。",
    "Input": "輸入", "Record": "錄音", "Upload": "上傳", "Sample": "範例", "View": "檢視", "Compare": "比較", "Patterns": "模式", "Detectors": "偵測器",
    "Phoneme check": "音素檢查", "Spectrogram": "頻譜圖", "Frication boundaries (s)": "摩擦段邊界（秒）", "Target sounds": "目標音", "Target sound": "目標音",
    "Save recordings to the log": "將錄音存入紀錄", "Scoring settings": "評分設定", "Use my voice calibration": "使用我的聲音校正",
    "Press record and say the word right away. It stops by itself after 3 seconds. For the best result, use a quiet room and keep the microphone close to your mouth.":
        "按下錄音後立刻念出單字，3 秒後自動停止。為求最佳結果，請在安靜的房間，並讓麥克風靠近嘴巴。",
    "Record or upload a word to begin.": "請錄音或上傳一個單字開始。",
    "The recording is longer than 5 seconds; only the first 5 seconds are used.": "錄音超過 5 秒，只使用前 5 秒。",
    "The selected hiss is too short to measure (< 30 ms). Widen the slider.": "所選的噓聲太短無法測量（< 30 毫秒），請拉寬滑桿。",
    "CoG": "重心頻率（CoG）", "Relative amplitude": "相對振幅", "Peak (Fm)": "峰值頻率（Fm）", "Duration": "長度", "SNR (est.)": "訊噪比（估計）",
    "Saved in the log.": "已存入紀錄。", "Discard": "捨棄", "CoG threshold /s/–/ʃ/ (Hz)": "/s/–/ʃ/ 的 CoG 門檻（Hz）",
    "Relative amplitude threshold /f/ (dB)": "/f/ 的相對振幅門檻（dB）", "Yellow margin, CoG (Hz)": "黃色範圍，CoG（Hz）",
    "Yellow margin, relative amplitude (dB)": "黃色範圍，相對振幅（dB）", "Reset to defaults": "恢復預設值",
    "Provisional values from the two D1 voices. Changes last for this session only.": "暫定值，取自兩位 D1 的聲音；更改只在本次使用中有效。",
    "Upload a wav or mp3 file": "上傳 wav 或 mp3 檔", "D1 sample": "D1 範例",
    "No speech was heard in this recording, so it is not scored. Say the word right after you press Record, in a quiet room and close to the microphone.":
        "這段錄音沒有聽到說話，因此不評分。請在按下錄音後立刻念，並在安靜的房間、靠近麥克風。",
    "Rise time": "上升時間", "Steepest climb": "最陡上升", "Hiss length": "噓聲長度", "VOT": "嗓音起始時間（VOT）", "Burst at": "爆破時間點", "Voicing starts": "發聲開始",
    "This recording is not in the log.": "這段錄音不在紀錄中。", "Keep in log": "存入紀錄", "Said it right but the result is wrong?": "念對了但結果錯誤？",
    "What happened?": "發生了什麼事？", "Save to the log": "存入紀錄", "Already flagged. You can change the note.": "已標記，可修改備註。",
    "Saved. Open the Log page to see it.": "已儲存，請到「紀錄」頁查看。", "Tip: the Calibrate page tunes the scoring to your voice.": "提示：「校正」頁可讓評分貼近你的聲音。",
    "An affricate starts abruptly (about 36 ms to reach full strength in the data) and a plain /ʃ/ fades in (about 66 ms).": "塞擦音起音很突然（資料中約 36 毫秒達到最大強度），單純的 /ʃ/ 則逐漸變強（約 66 毫秒）。",
    # teacher view
    "See the sound the child just made, for every sound, with the numbers behind the score.": "查看孩子剛發出的每個聲音，以及評分背後的數值。",
    "Voice size ×": "聲音大小", "What the child saw": "孩子看到的畫面", "Recording quality": "錄音品質", "Louder than the room by": "比房間音量大",
    "Level": "音量", "Verdict": "判定", "Numbers behind the verdict": "判定背後的數值", "How likely each sound is, over time": "各個聲音隨時間的可能性",
    "Upload a wav or mp3 file (for example a recording from the Log page)": "上傳 wav 或 mp3 檔（例如來自「紀錄」頁的錄音）",
    "No Sound Check for the chosen profile: voice size ×1.00 (pick a profile in the sidebar, or type a value).": "所選個人檔案沒有聲音檢查：聲音大小 ×1.00（可在側邊欄選檔案，或直接輸入數值）。",
    # calibrate
    "Start over": "重新開始", "Redo calibration": "重新校正", "### Room check: stay silent": "### 房間檢查：請保持安靜", "Skip the room check": "略過房間檢查",
    "Use this recording": "使用這段錄音", "Demo: use the UK dictionary voice": "示範：使用英式字典錄音", "Room noise": "房間噪音", "Use this level": "使用此音量",
    # log
    "Only flagged": "只看已標記", "Sound": "聲音", "Details": "詳細資料", "Nothing logged yet. Record a word on the Practice page.": "尚無紀錄。請在「練習」頁錄一個單字。",
    "Delete logs": "刪除紀錄", "This removes the recordings and their notes from this computer. It cannot be undone.": "這會從此電腦刪除錄音及其備註，無法復原。",
    "I am sure I want to delete everything": "我確定要全部刪除", "Recordings": "錄音數", "Flagged as wrong": "標記為判錯", "Nothing yet.": "目前沒有。",
    "Download events as CSV": "下載事件（CSV）", "Note": "備註", "What the app measured and the settings used:": "程式測得的數值與使用的設定：",
    "Save note and flag": "儲存備註並標記", "Delete": "刪除", "Remove flag": "取消標記",
    # camera log
    "The lip mirror and the recorder of the learner app, measured at the same moments. Numbers only: no picture of the face, no sound.": "孩子端程式的嘴唇鏡子與錄音器，在同一時刻的測量。只有數字，沒有臉部影像，也沒有聲音。",
    "Download camera.jsonl": "下載 camera.jsonl", "Settings written with these turns": "這些回合所用的設定", "The log file is empty.": "紀錄檔是空的。",
    # patterns / views
    "Reference voice": "參考聲音", "Your numbers": "你的數值", "How much data is behind this?": "這背後有多少資料？", "Experimental": "實驗性",
    "Compared with the D1 voices": "與 D1 的聲音比較", "CoG against relative amplitude. Dotted lines are the current thresholds.": "重心頻率對相對振幅。虛線是目前的門檻。",
    "Ablation studies": "消融實驗", "Frication detectors": "摩擦段偵測器",
    "No vowel after the hiss, so only spectral contrast could be used.": "噓聲後沒有母音，因此只能使用頻譜對比。",
    "How much can this be trusted?": "這個結果可以相信到什麼程度？", "It cannot confirm the verdict above.": "它無法確認上述判定。",
    "Experimental. A multilingual phone recogniser listens to the same recording and reports which sound it hears at the hiss. It is a second opinion and does not change the verdict.":
        "實驗性。多語言音素辨識器聆聽同一段錄音，並回報在噓聲處聽到的聲音。這是第二意見，不會改變判定。",
    # rate (static labels)
    "Agreement": "一致性", "Export and delete": "匯出與刪除", "Your rater code (initials)": "您的評分者代碼（姓名縮寫）",
    "Enter your rater code to start.": "請輸入評分者代碼開始。", "No ratings yet.": "目前還沒有評分。", "I am not sure": "我不確定", "Note (optional)": "備註（可不填）",
    "Rate only the first recording of each word (half the work; recommended for the pilot)": "每個字只評第一次錄音（工作量減半；建議用於前導研究）",
    "Import data exported from another computer (zip)": "匯入從另一台電腦匯出的資料（zip）", "Import": "匯入", "Download all data (zip)": "下載全部資料（zip）",
    "Delete one participant (the right to have data deleted)": "刪除一位參與者（資料刪除權）",
    "I am sure; this removes their recordings, takes and ratings from this computer": "我確定；這會從此電腦刪除其錄音、各次錄製與評分",
    "No recordings with audio yet.": "目前沒有含錄音的資料。", "You have rated every recording.": "您已評完所有錄音。",
    "Does the first sound of this word sound right for the word? Rate only the first consonant.": "這個字的第一個聲音聽起來對嗎？只評第一個子音。",
    "Correct": "正確", "Almost": "差不多", "Not yet": "還沒",
}


# long or partly dynamic texts, found by how they start (the Chinese says the same as the whole sentence)
ZH_PREFIX = [
    ("Say see, she and fee, twice each.", "請分別念 see、she、fee 各兩次。程式用這六段錄音先了解你的聲音，再進行判定。約需一分鐘，關閉頁面後不會保存任何資料。"),
    ("Press record and say nothing for 3 seconds", "按下錄音並保持安靜 3 秒，讓程式測量房間的噪音；若單字在靠近噪音處錄音，程式會用它來提醒你。"),
    ("Press record and say “", "按下錄音並念出單字，3 秒後自動停止。"),
    ("Say the word “", "請念出這個單字。"),
    ("Say “", "請念出單字，3 秒後自動停止。"),
    ("Child “", "孩子的聲音檢查數值（F3、聲音大小）。"),
    ("Provisional values from the two D1 voices", "暫定值，取自兩位 D1 的聲音；更改只在本次使用中有效。"),
    ("Every recording that gets a result", "每一段有結果的錄音都會連同程式的測量與判定存放在這裡。請標記你念對但程式判錯的錄音，再用它們找出原因。"),
    ("Each time a child's Sound Check", "每次孩子的聲音檢查被儲存、重錄或刪除時：新數值與被取代的數值（只有數字，沒有聲音）。"),
    ("Everything a child does in the learner app", "孩子在孩子端程式中的所有操作，每行一筆：開啟課程、嘗試（評分內容、星星、過關線、錄音品質、即時引導的數值）、重新錄音。只有數字與選擇，絕不含聲音或相機影像。請與聲音檢查紀錄和相機紀錄一起閱讀。"),
    ("Nothing logged yet. Open the learner app on a lip sound", "尚無紀錄。請在孩子端程式開啟唇音課程（例如 ?word=me），打開嘴唇鏡子並按「同時錄音與鏡子」；回合結束或按重新開始後，數字會出現在這裡。"),
    ("What the app does with a recording", "程式如何處理一段錄音，逐步說明，以及每一步為何這樣設計。"),
    ("The step-by-step illustration needs", "逐步圖示需要 D1 字典錄音（SOUNDS/ 與 boundaries.csv），這些不在本專案儲存庫中。"),
    ("The lip mirror and the recorder", "孩子端程式的嘴唇鏡子與錄音器，在同一時刻的測量。只有數字，沒有臉部影像，也沒有聲音。"),
]


def bi(text: str, sep: str = " ") -> str:
    """English text followed by its Chinese when the table has it (else the text as it is)."""
    zh = ZH.get(text.strip()) or next((z for pre, z in ZH_PREFIX if text.strip().startswith(pre)), None)
    return f"{text}{sep}{zh}" if zh and zh not in text else text


def _opt_format(options, fmt=None):
    base = fmt or (lambda o: o)
    return lambda o: bi(str(base(o))) if isinstance(o, str) or fmt else base(o)


def install(st) -> None:
    """Wrap the Streamlit calls that show text, both st.xxx and the same calls on columns, containers and the sidebar. Idempotent."""
    if getattr(st, "_bilingual_installed", False):
        return
    st._bilingual_installed = True
    from streamlit.delta_generator import DeltaGenerator
    main_dg = st._main

    def patch(name, make):
        orig = getattr(DeltaGenerator, name)
        setattr(DeltaGenerator, name, make(orig))
        setattr(st, name, getattr(main_dg, name))                         # st.xxx must point at the wrapped method too

    for name in ("title", "header", "subheader", "info", "warning", "error", "success", "toast"):
        patch(name, lambda o: lambda self, body, *a, **k: o(self, bi(body) if isinstance(body, str) else body, *a, **k))
    for name in ("caption", "markdown", "write"):
        patch(name, lambda o: lambda self, body, *a, **k: o(self, bi(body, "  \n") if isinstance(body, str) else body, *a, **k))
    for name in ("button", "toggle", "checkbox", "text_input", "text_area", "number_input", "slider", "metric", "download_button", "file_uploader", "expander", "popover"):
        patch(name, lambda o: lambda self, label, *a, **k: o(self, bi(label) if isinstance(label, str) else label, *a, **k))
    for name in ("selectbox", "segmented_control", "radio", "pills"):
        def make(o):
            def wrapped(self, label, options, *a, **k):
                k["format_func"] = _opt_format(options, k.get("format_func"))
                return o(self, bi(label) if isinstance(label, str) else label, options, *a, **k)
            return wrapped
        patch(name, make)
    patch("tabs", lambda o: lambda self, labels, *a, **k: o(self, [bi(x) if isinstance(x, str) else x for x in labels], *a, **k))
