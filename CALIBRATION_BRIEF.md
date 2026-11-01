# Brief for the calibration mockup (Sound Check)

Read this before drawing. It says what calibration really does in our system, so the mockup matches it. Where this brief says a number or a
text is "not decided", do not invent it: draw a dashed "to be added" placeholder.

## 1. Who it is for
- Children who are deaf or hard of hearing (DHH). **Never rely on sound**: no "Listen again", no "listen to the room", no audio prompts or
  beeps. Everything must be understood by looking (colour, icon, animation, text). A teacher or parent may sit next to the child.
- Text is bilingual: English first, Traditional Chinese under it (pinyin where the lesson screens use it). Keep it short.
- Look and feel: the same as the learner app (blue accent #2F6FE4, Nunito / Noto Sans TC, rounded white cards, big round buttons, calm
  light-blue background). Your mockup already matches this well.

## 2. What calibration is (and is not)
- The app scores sounds in two different ways:
  - **/s/ /ʃ/ /f/ (words see, she, fee)** are fricatives, scored from the spectrum of the "hiss" (mainly its centre of gravity, CoG, in Hz).
    Children's and adults' hisses sit at different frequencies, so calibration learns *this child's* hiss and adjusts the thresholds.
  - **/p/ /b/ /m/ /n/ /tʃ/ (pea, bee, me, knee, cheat)** are scored by a speech-recognition model. They **do not need calibration**.
- Calibration is therefore **optional but recommended**. Without it the app still scores, using default thresholds. So do not say "you must
  calibrate before playing": say it makes the /s/, /ʃ/, /f/ result fairer for this child, and offer "Skip for now".
- It does **not** measure vowels (no F1/F2 baseline, no /a/ sample). Please remove "Baseline /a/ F1-F2" from the teacher panel.

## 3. The real steps (replace the bot's "aaa / sss" step)
**Step 1 – Room check (about 3 s of silence).** Measures how loud the room is.
- The child stays still, the app records exactly 3 s (stops by itself, no stop button needed).
- Result: the room noise level in dBFS (lower = quieter). Show it as a green / yellow / red bar plus a face icon, not as a number.
- Provisional thresholds, still to be tested on real rooms: not decided here, draw the bar zones without numbers for the child.
- Offer "Check again" and "Skip".

**Step 2 – The child says the three words, two times each: see, she, fee** (six recordings, in the order see, she, fee, see, she, fee).
- Each recording is 3 s and stops by itself; the ring / countdown is a good way to show that. The child says the **word**, not a long
  "sss" or "aaa".
- Show the word, its picture/mouth hint if available (to be added if not), and one big record button.
- After each recording the app compares the word's loudness with the room noise (signal-to-noise ratio, SNR) and shows one of three
  states: **good** (green), **a little noisy** (yellow, still fine), **too noisy – record this word again** (red). It only warns; the
  child (or teacher) decides. If no hiss can be found in the recording, show "Let's try again" (red) and record again.
- Progress: 6 dots (1 of 6 ... 6 of 6), not 3 steps.
- Drawing of the word as a spectrogram is for the Dev app only; do not show it to the child.

**Step 3 – Done / Ready.**
- "Calibrated from 6 recordings" and where it was saved: a **named profile** (one per child). The profile is stored on the server and is
  loaded again when that child is chosen. (It is not browser localStorage.)
- Big Start button leading to the lesson map. "Redo calibration" as a smaller button.

## 4. Teacher details (collapsible, off by default)
Only numbers we really measure:
- Room noise (dBFS), word level (dBFS), SNR (dB) for each recording.
- Per recording: word, CoG (Hz), contrast (dB), relative amplitude (dB).
- Profile name.
Do not show: F1/F2, peak/clipping, mic distance. We do not measure them yet. If you want them in the design, mark them "not yet measured".
The tips "one hand from the mic", "close the door", "turn off the fan" are fine as advice (not measured).

## 5. Technical facts the design must respect
- Recording is in the browser with echo cancellation, noise suppression and auto-gain **off** (raw microphone). 3 s per recording.
- The "Space" shortcut for recording and "Esc" for back are already used in the learner app; keep them consistent.
- Nothing is invented: any text, picture or number that is not in this brief is "to be added" (dashed placeholder), and the content owner
  fills it in.

## 6. What to change in your current mockup (checklist)
1. Remove "Listen again" (needs hearing). Use "Check again".
2. Step 2 becomes: say see / she / fee twice (6 recordings), not "aaa" then "sss".
3. Remove the /a/ F1-F2 baseline; keep CoG, contrast, relative amplitude.
4. Remove "Peak / clipping" and "Mic distance OK" or mark them "not yet measured".
5. Say "saved in the child's profile on the server", not localStorage.
6. Add "Skip for now" and the sentence that /p b m n tʃ do not need calibration.
7. Keep: 3-phase header, big colour feedback, face icons, big Start button, teacher details panel, bilingual text.
8. In the paper / demo text: the app can score without calibration (default thresholds); calibration only improves /s/, /ʃ/, /f/.
