# DHH-learners: handoff

Everything needed to continue this work without the previous conversation. State as of **2026-10-28**. The user writes in Vietnamese and expects replies in Vietnamese. The detailed method history (in Vietnamese) is in `app/METHOD_NOTES.md`; read it after this file.

## 1. What this project is

A pronunciation-practice system for deaf and hard-of-hearing (DHH) children learning eight English sounds, one example word each: /s/ see, /ʃ/ she, /f/ fee, /p/ pea, /b/ bee, /m/ me, /n/ knee, /tʃ/ cheat. Interface text is English plus Traditional Chinese (with pinyin on some tips).

Two separate Streamlit apps share one scoring package:

| App | Entry | Port | Purpose |
| --- | --- | --- | --- |
| **Dev app** | `app/streamlit_app.py` | 8501 | The researcher's tool: practice, calibrate, log recordings and flag wrong results, debug scoring. **Not** for learners. |
| **Learner app** | `app/learner_app.py` | 8502 | What the children use, built from the PDF mockup `D:\SCIENCE RESEARCH\SPECTROGRAM\S mockup pdf.pdf` (design export in `S - mockup.zip` next to it). |

Rule from the user: keep them separate. Dev work must not leak into the learner UI.

## 2. Run, test, environment

- Windows 11, PowerShell. Python venv at `.venv` (made with `uv`; there is no `pip` inside it: use `uv pip install --python .venv\Scripts\python.exe <pkg>`).
- Run from `app/`:
  - `..\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501 --server.headless true`
  - `..\.venv\Scripts\python.exe -m streamlit run learner_app.py --server.port 8502 --server.headless true`
  - Learner URLs: `http://localhost:8502/?word=she` (also `me`, `fee`, ...); `&step=2&hold=1` freezes step 2 of a multi-step picture.
- **Streamlit keeps helper modules in memory.** Pages in `app_pages/` reload on change; anything under `fricative/`, `learner/`, `views/` needs a server restart.
- Tests: `.venv\Scripts\python.exe -m pytest app\tests\test_gop.py app\tests\test_learner_lessons.py app\tests\test_stops.py -q` (pass). Many older tests (`test_app.py`, `test_phoneme_check.py`, ...) fail on this machine **only** because the D1 sample recordings are absent (`tests/conftest.py` lists which files need them); that is not a regression.
- Installed software: torch 2.6.0+cu124 (RTX 3050, 4 GB), transformers 5.20.2, **pandas pinned to 2.3.3**, Node.js 24.22.1 (winget), no git.
- **2026-10-29: Smart App Control also blocked `.venv\Scripts\python.exe` itself** (unsigned launcher), so nothing could start from the venv (VS Code too). The interpreter the venv was made from still runs. Use `.\start_apps.ps1` at the project root: it runs that interpreter with the venv's `site-packages` on `PYTHONPATH` (`-Only learner|dev`, `-Test`, `-NoBrowser`; restarts servers already on the port). All imports (streamlit, torch with CUDA, transformers, pandas) work this way and `-Test` passes (51 tests). The user chose this workaround; do not disable Smart App Control.
- **Windows Smart App Control (enforce mode) blocks some unsigned binaries.** pandas 3.1.0 failed with "An Application Control policy has blocked this file" (`dtypes.cp312-win_amd64.pyd`); pandas 2.3.3 loads. If another `.pyd` is blocked, pick a different version of that package. Do not try to disable the policy. Event log: `Microsoft-Windows-CodeIntegrity/Operational`.
- Environment variables: `FRICATIVE_PROFILES` (calibration profile folder, default `app/profiles`), `FRICATIVE_LOGS` (log folder, default `app/logs`), `W2V_DIR` (recogniser checkpoint). Tests set the first two to temp dirs.
- Browser checks used so far: Edge headless through `--screenshot` and a throwaway Playwright venv in the agent scratchpad (`msedge` channel, no browser download). Streamlit pages need about 15-20 s after a restart before a screenshot shows content.

## 3. Repository layout (important files)

```
app/
  streamlit_app.py          Dev app shell: profile picker, navigation
  app_pages/practice.py     Dev Practice page (scoring UI, logging, views)
  app_pages/calibrate.py    six recordings (see/she/fee x2) -> personal calibration
  app_pages/log.py          Log page: list, listen, flag, delete
  fricative/                scoring package (shared by both apps)
    config.py               word->sound tables, thresholds, PHONE_LABEL
    pipeline.py             score_fricative(): the Dev fricative pipeline as one function
    gop.py                  goodness-of-pronunciation for b p m n tʃ
    phoneme_check.py        wav2vec2 phone recogniser (GPU), gate, reconcile, log_posteriors
    calibrated.py           calibration model, save/load/list profiles
    reclog.py               recording log (audio + json), flag/delete
    classify.py measure.py segment.py patterns.py stops.py nasals.py affricate.py ...
  views/autorecord.py       Dev record button (3 s, stop, waveform playback)
  learner_app.py            learner app entry
  learner/
    lessons.py              ALL learner content (Lesson, Step, Motion; see section 6)
    screen.py               HTML/CSS of top bar, word card, mouth card, nav (NAV_CSS)
    mic.py                  big record button component (3 s, Space key)
    result.py               scoring wrapper + result panel (+ zone logic, CSS)
    motion.py               mouth_motion() highlight animation, mouth_steps() multi-picture viewer
    tongue.py               cartoon head + /ʃ/-/s/ slider (3 colour zones)
    assets/                 mouth_s.jpg mouth_sh.jpg mouth_f.jpg me_1..3.jpg (+ mouth_s_old.jpg, unused)
  assets/model/             calibrated_lda.json ch_probe.json pb_probe.json other_lda.json; w2v_phone/ (1.2 GB checkpoint, git-ignored)
  profiles/                 saved calibrations (one json per profile, _last.txt)
  logs/                     audio/ and entries/ of logged recordings (the user's voice)
  METHOD_NOTES.md           method history, Vietnamese
  tests/
HANDOFF.md                  this file
```

## 4. Scoring methods (what runs when)

**Fricatives /s/ /ʃ/ /f/** (`fricative/pipeline.py::score_fricative`, identical to Dev `practice.py`):
recogniser first-sound gate -> find hiss boundaries -> measure (CoG, relative amplitude, ...) -> rule verdict with fixed thresholds (`config.DEFAULT_THRESHOLDS`, CoG 4340 Hz, margin 300 Hz) -> calibrated verdict if a profile exists -> recogniser check over the hiss and `reconcile`. No hiss / not the right kind of sound -> not scored. The learner app loads the last-used profile (`last_profile()`), as the Dev app does on start. Verified: 31/31 logged fricative recordings give the same label in both apps.

**Stops, nasals, affricate /p b m n tʃ**: **GOP** (`fricative/gop.py`), needs the recogniser:
- wav2vec2-xlsr-53-espeak (CTC). Take the first 0.45 s of speech (from the first frame where blank prob < 0.9, minus 3 frames).
- For each candidate consonant in a confusable set (b: b p m d v; p: p b m t f; m: m n b p; n: n m d t l; tʃ: tʃ ʃ t s d) compute the CTC likelihood of `[consonant, any vowel]`, sum over vowels, normalise: P(candidate).
- Verdict: P(target) >= 0.80 green; 0.50-0.80 and target is top -> yellow; another candidate top with P >= 0.60 -> red ("You said /x/"); else not scored. **Thresholds are provisional.**
- Vowel-independent on purpose (learners also say "bu", "ba").
- Without the recogniser the old acoustic rules run (VOT for p/b, rise time for tʃ, "needs recogniser" for m/n). VOT/rise-time are unreliable in a noisy room (shown in the logs).

**Recording quality lesson:** browsers apply auto gain, echo cancellation and noise suppression by default, which clipped the signal and erased quiet starts. Both record buttons now request a raw microphone. Rooms are still noisy (about 20 dB SNR in the 1.5-7.5 kHz band).

## 5. Dev app features

Practice page (word picker shows the eight sounds), 3 s auto-stop recording with Stop button and waveform with a moving playhead, calibration profiles (sidebar: choose, add, delete, last one remembered), recording log with flag ("said it right but the result is wrong") and notes, keep/discard per recording and a global "save to log" switch, Log page (filters, listen, JSON of measurements, delete unflagged / delete all), GOP debug plot (candidate probabilities over time) and decoded phones.

## 6. Learner app

**Screen** (matches the mockup closely): top bar (Map button, star count 0, progress "Word n / 8"), a row of buttons to switch sounds (prev, one per sound, next; not in the mockup, added at the user's request), word card (green: sound picture, word with highlighted letters, Chinese meaning, "Sound /x/ 目標音", meaning picture), "Watch the mouth" card, and on the right the record panel. After recording, the record panel is **replaced by the result** with a "Record again" button.

**Result panel** (`learner/result.py`): mark and label (Correct / Almost / Not yet, from the Dev rules), "You said /x/", a tip (English text from the Dev rules), and for /s/ and /ʃ/ only a cartoon head with the learner's tongue (solid) and target (dashed) plus a slider /ʃ/ - /s/ with **green (target end), yellow (middle, "Almost") and red zones**; the marker is always kept inside the zone of the verdict. Position comes from the calibrated model's probability of the target, else from CoG distance to the threshold.

**Content status** (all content lives in `learner/lessons.py`; nothing is invented: missing pieces show a dashed "to be added" box):

| Word | Mouth picture | Tips (EN/ZH/pinyin) | Sound pic | Meaning pic + zh | Motion |
| --- | --- | --- | --- | --- | --- |
| see /s/ | yes | yes (no pinyin) | snake | eye + 看見 | 3-step highlight animation (`Motion`) |
| she /ʃ/ | yes | yes | missing | missing | none |
| fee /f/ | yes | yes | missing | missing | none |
| me /m/ | 3 pictures (`Step`): close lips, hum, open into ee | yes, per step | missing | missing | marks move on each step; steps auto-play (4 s, 5 s, 4 s), pause, jump, 0.5x |
| pea, bee, knee, cheat | none | none | none | none | none |

Mouth pictures come from the user's image generator (photoreal, with baked-in labels); they were cropped from screenshots the user pasted (so they are slightly low resolution). "knee": which letters to highlight is undecided (silent k), so none is highlighted.

**Components** use Streamlit components v2 (`streamlit.components.v2`). Gotchas that cost time:
- `st.html` strips inline `<svg>`; icons are embedded as `<img src="data:image/svg+xml;base64,...">` (`screen.svg_img`).
- A v2 component's `parentElement` is a **shadow root** (no `getComputedStyle` on it); query children with `parentElement.querySelector`.
- Component JS may return a cleanup function; it is called before each re-run.
- `st.session_state` keys: `mic_<word>_wav` holds the recording being scored; removing it brings the mic back. `st.cache_data` wraps `result.score`.
- Global CSS sets Nunito on `.stApp *`; Material icon spans need `font-family: Material Symbols Rounded` (done in `NAV_CSS`).

## 7. User preferences and standing rules

1. **Ask, never invent content.** Words, translations, tips, button labels (EN or ZH), star rules: if the user has not given them, show a "to be added" placeholder or ask. Text I added on my own and that still needs approval: "Record again", "You", "Target", the "No hiss was found..." notices, the nav buttons.
2. **Dev app and learner app are separate** (see section 1).
3. **Follow `design-taste-frontend`** (taste-skill, installed at `C:\Users\tuank\.claude\skills\design-taste-frontend`; its scripts need Node, now installed) for every design decision. The PDF mockup wins where it applies; say where the skill and the mockup disagree. The full skill run is heavy (30-45 min); apply its principles on small changes.
4. The user also asked for **Superpowers** (`/plugin install superpowers@claude-plugins-official`, to be run by the user); not installed yet as far as I know.
5. Do not install software or change system settings without asking (Node was installed after an explicit "cài node").
6. Be honest about limits: ratings of what is verified (tests, screenshots) versus not tried with a real microphone.

## 8. Known issues and limitations

- The recogniser often hears the user's /b/ as /m/ (also "mu" as /n/): both models tried (xlsr, lv-60) agree, so it may be the signal or the user's speech; nobody else has listened. Unresolved.
- GOP thresholds, the slider anchors (2000 Hz and 10400 Hz) and the CoG zone widths are provisional, tuned on **one speaker and one microphone**. Not evaluated on children or DHH speech.
- Tongue and lips inside the photos do not move; only marks on top of them animate. Real motion needs in-between pictures.
- The tongue in /m/ step 3 (/i:/) is drawn relaxed, anatomically wrong for /i:; kept on purpose for the consonant stage, to be replaced when vowels are taught.
- The Dev page `app_pages/practice.py` still has its own copy of the fricative pipeline; it should call `score_fricative`.
- Dead code from superseded approaches remains (`stops.classify_stop_heard`, `classify_stop_probe`, `phoneme_check.first_vowel`, `is_ee`, `probability_p`, `nasal_reading`).
- Recordings of the user's own voice are stored in `app/logs/audio` (private; do not commit or share).

## 9. Open tasks, in rough priority

1. **/m/ connecting picture** between step 2 (hum) and step 3 (open). The user will either generate 1-3 in-between pictures with their image tool (a ready prompt was offered: keep everything identical, only lips half-open, soft palate partly raised, arrows shifting from nose to mouth) or accept a code-drawn vector transition. Waiting for the user's choice and the name of their image tool.
2. Missing content for she / fee / me (sound picture, meaning picture, Chinese meaning) and complete lessons for pea, bee, knee, cheat (mouth picture, tips, steps if the sound is made in steps, e.g. /p/ /b/ closure then release).
3. Result screen design decisions: star rules, the "next word" flow, the Map screen, Chinese text for new labels.
4. Calibrate the GOP thresholds and the slider anchors on public data (L2-ARCTIC or similar) and on child/DHH speech; get a second listener to label the /b/-heard-as-/m/ recordings.
5. A recording-quality gate that does not depend on the speaker (SNR of the leading silence, level, clipping) with a "record again" message.
6. Make the Dev page call `score_fricative`; remove dead code; re-run the full test suite when the D1 samples are available.
7. Install Superpowers and git if wanted (git is needed for `npx skills add` to work).

## 10. Where things are documented

- `app/METHOD_NOTES.md`: chronological method notes and evidence from the logs (Vietnamese).
- This file: orientation.
- Assistant memory notes for this project: `C:\Users\tuank\.claude\projects\c--Users-tuank-Projects-DHH-learners\memory\` (`MEMORY.md` index; `dev-vs-user-app`, `use-superpowers`, `use-taste-skill`, `session-status`).
