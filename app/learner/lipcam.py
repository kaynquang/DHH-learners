"""The lip mirror (prototype): a cartoon mouth that opens and closes with the child's own lips, to show where a sound is made.

For /m/ /p/ /b/ the place is the lips, and unlike the tongue it can be seen: the child sees "lips together" while they hum or hold the sound.
How it works: the camera picture is read in the browser by MediaPipe's face landmark model (files in app/static/mediapipe, no network needed);
only the distance between the upper and the lower inner lip, divided by the height of the face, is used. The picture is not shown, not sent
anywhere and not stored; the child sees a drawing of a mouth instead. It runs only when the person switches it on.

Coach mode (/m/): the microphone is read too, in the same page, and the two are put together. /m/ is "lips together while the voice hums"; lips open
while the voice sounds is another sound (/n/ or a vowel). Three boxes light up: lips together, a hum while they are together, the hum held for
HOLD_S seconds. Nothing is recorded or sent: only the loudness and the share of low pitch in each moment are used.
The limits below are first guesses, to be tuned on real children's faces and voices. See METHOD_NOTES.md.
"""
from __future__ import annotations

import streamlit.components.v2 as components

CLOSED_BELOW = 0.03          # inner lip gap / face height under which the lips count as together (a guess to tune)
HOLD_S = 1.0                 # how long lips together + hum must last (a guess; the same as the 1 s of the Game view)
LOW_SHARE = 0.6              # a hum keeps at least this share of its energy under 1 kHz; a breath or a hiss does not (a guess)
PERIODIC = 0.6               # a voice repeats itself at its pitch: the frame's best self-similarity must be above this (room noise and rumble stay under it; a guess)
QUIET_DBFS = -50.0          # the sound gate when the room noise is not known
N_OPEN_MAX = 0.12                # /n/: the lips are "a little open" when the inner lip gap / face height is above the closed limit and under this (a guess; "ah" is above 0.15)
# /tʃ/, the ghost mouth: the three steps of the lesson (the titles are those of its picture cards), each as a target of the lip width against the relaxed lips and the inner gap / face height.
# The shapes are drawn to be seen (round and small, a small gap, wide and flat), not measured on children: a first guess, to be set from the log.
CH_GHOST = [
    {"title": "Get ready for ch", "titleZh": "準備好，舌尖頂住", "ratio": 0.80, "gap": 0.09,
     "detail": "Put the tip of your tongue up on the bumpy ridge just behind your top front teeth, and let the sides of your tongue touch your top side teeth. Lips a little round. Voice off. Keep the air in.",
     "detailZh": "舌尖頂在上排門牙後面凸起的牙齦上，舌頭兩側碰到上排側邊的牙齒。嘴唇微圓，不要出聲，把氣留住。"},
    {"title": "Release, ch", "titleZh": "放開，噓一下", "ratio": 0.85, "gap": 0.025,
     "detail": "Drop your tongue tip away fast, like a pop, and let a short, quiet \"sh\" of air out through a small gap. Voice still off. Lips stay a little round.",
     "detailZh": "舌尖很快離開，像「啪」一聲，接著讓短短的「嘶」氣從小縫吹出來。還是不要出聲，嘴唇保持微圓。"},
    {"title": "Open into a smile", "titleZh": "微笑，張開", "ratio": 1.35, "gap": 0.035,
     "detail": "Now smile wide, with no stop between. Turn your voice on and keep it going.",
     "detailZh": "接著微笑，不要停，直接發聲。這時打開聲音，並且持續。"}]
# /s/ and /ʃ/ followed by "ee" ("see", "she"): the words are the lesson's own check cards (English and Chinese as the content owner wrote them); the titles "Get ready" and "Hiss: shh" and the shapes are the assistant's.
# s: teeth close, a small smile (lips a little spread); sh: lips a little rounded. Both then open into the same "ee" as above.
_EE = {"title": "Open into a smile", "titleZh": "微笑，張開", "ratio": 1.35, "gap": 0.035, "detail": CH_GHOST[2]["detail"], "detailZh": CH_GHOST[2]["detailZh"]}
S_GHOST = [
    {"title": "Get ready", "titleZh": "準備好", "ratio": 1.15, "gap": 0.02, "detail": "Teeth close, small smile. Tongue tip down by lower teeth.", "detailZh": "牙齒輕碰，微笑。舌尖放在下排牙後面。"},
    {"title": "Hiss: sssss", "titleZh": "嘶嘶聲", "ratio": 1.15, "gap": 0.02, "detail": "Front of tongue up a little, leaving a narrow gap. Voice off: no buzz.", "detailZh": "舌頭前段微微抬高，留窄縫。手摸喉嚨：不要振動。"},
    _EE]
SH_GHOST = [
    {"title": "Get ready", "titleZh": "準備好", "ratio": 0.85, "gap": 0.05, "detail": "Round lips slightly. Tongue up and back.", "detailZh": "嘴唇微圓。舌頭抬高，稍往後。"},
    {"title": "Hiss: shh", "titleZh": "噓～聲", "ratio": 0.85, "gap": 0.05, "detail": "Keep air flowing. Voice off: no buzz.", "detailZh": "持續送氣。聲帶不振動。"},
    _EE]
# /p/ and /b/ followed by "ee" ("pea", "bee"): the titles and the English words are those of the lesson's own picture cards (assets/pea_1-3.jpg, bee_1-3.jpg); the Chinese is the content owner's words
# from the check cards under the same pictures, joined with "；" by the assistant. The shapes are the assistant's: lips together; lips parted a little; lips slightly spread ("Lips slightly spread" is less wide than the "ee" of the hiss sounds).
P_GHOST = [
    {"title": "Close your lips", "titleZh": "雙唇閉合", "ratio": 1.0, "gap": 0.01, "detail": "Close your lips gently. Stop the air briefly. Voice OFF for /p/: no hum yet.", "detailZh": "雙唇閉合；鼻腔通道關閉；聲帶不振動"},
    {"title": "Release a small puff", "titleZh": "輕輕噗一下", "ratio": 1.1, "gap": 0.06, "detail": "Open with a small puff of air. Move straight into a smile. A quick release — do not add ‘uh’.", "detailZh": "雙唇張開；短促氣流；聲帶不振動"},
    {"title": "Smile — pea", "titleZh": "微笑，說 pea", "ratio": 1.25, "gap": 0.035, "detail": "Smile and turn your voice on. Join it smoothly: pea. One word — no pause after /p/.", "detailZh": "嘴唇微微拉開；氣流通過嘴巴；發聲並感受振動"}]
B_GHOST = [
    {"title": "Close your lips", "titleZh": "雙唇閉合", "ratio": 1.0, "gap": 0.01, "detail": "Close your lips gently. Stop the air briefly. Gentle contact.", "detailZh": "雙唇閉合；鼻腔通道關閉；輕輕接觸"},
    {"title": "Release gently", "titleZh": "輕輕張開雙唇", "ratio": 1.1, "gap": 0.05, "detail": "Open your lips gently. Let your voice begin. No strong puff — go straight into a smile.", "detailZh": "輕輕張開雙唇；不要用力吹氣；開始發聲"},
    {"title": "Smile — bee", "titleZh": "微笑，說 bee", "ratio": 1.25, "gap": 0.035, "detail": "Smile and keep your voice on. Join it smoothly: bee. One word — no pause after /b/.", "detailZh": "嘴唇微微拉開；氣流通過嘴巴；發聲並感受振動"}]
GHOSTS = {"tʃ": CH_GHOST, "s": S_GHOST, "sh": SH_GHOST, "p": P_GHOST, "b": B_GHOST}
PB_CLOSE_S = 0.3             # /p/ /b/: the lips must be seen together this long before the first box ticks (a guess)
PB_HOLD_S = 0.5              # /p/ /b/: the spread lips of the "ee" must be held this long (a guess; as the voice of "see" and "she")
# The words under each step of CH_GHOST above are written by the assistant at the user
CH_GHOST_STEP_S = 1.6      # how long the ghost stays at each step
MEASURE_S = 0.6                # the room is listened to for this long after each Start or Restart, before anything counts; its level + ABOVE_NOISE_DB is the one gate
ROOM_MAX_DBFS = -32.0          # a room louder than this (already humming, or a very noisy room) cannot be measured: the window starts again
ARM_QUIET_S = 0.0             # a hum counts only after this much quiet since the turn began (a hum already going when the button was pressed, or a steady sound, does not count)
GATE_MAX_DBFS = -28.0        # the gate never rises above this, however loud the room
ABOVE_NOISE_DB = 7.0        # the sound gate above the room noise from Sound Check
M_HOLD_S = 0.5               # /m/ then /iː/: how long the closed-lips hum must last before the child slides on
SMILE_RATIO = 1.03          # /iː/: the lips are this much wider than this child's closed lips (a guess)
SMILE_GAP_MAX = 0.10        # /iː/: the inner lip gap / face height stays under this, the mouth is small (a guess; "ah" is wider open)

_HTML = """
<div class="lc">
  <div class="state" role="status"></div>
  <div class="body">
    <canvas class="mouth" width="400" height="240" aria-label="A mouth that follows your lips"></canvas>
    <div class="steps">
      <span class="st s1"><i>1</i>Lips together 雙唇閉合</span>
      <span class="st s2"><i>2</i>Hum 哼聲</span>
      <span class="st s3"><i>3</i>Keep going 保持</span>
      <span class="st s4" style="display:none"><i>4</i>Keep going 保持</span>
    </div>
  </div>
  <canvas class="snake" width="800" height="150" aria-label="A snake that grows while you hiss and reaches the flag when you smile"></canvas>
  <div class="detail"></div>
  <div class="bar"><div class="fill"></div></div>
  <div class="btns">
    <button type="button" class="go">Start the lip mirror 開始嘴唇鏡子</button>
    <button type="button" class="both">● Record and mirror together 同時錄音和鏡子</button>
  </div>
  <div class="dbg"></div>
</div>
"""

_CSS = """
:host { display: block; }
.lc { box-sizing: border-box; min-height: 560px; font-family: 'Nunito', 'Noto Sans TC', system-ui, sans-serif; color: #1B2440; display: flex; flex-direction: column;
  align-items: stretch; justify-content: flex-start; gap: 14px; background: rgba(255,255,255,.84); border: 1.5px solid rgba(255,255,255,.95); border-radius: 28px;
  padding: 28px 30px; box-shadow: 0 14px 34px rgba(70,120,200,.13); }
.btns { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }
.lc:not(.on) .btns { margin: auto; flex-direction: column; align-items: center; }
.go, .both { min-height: 52px; border-radius: 999px; border: none; color: #fff; font-weight: 800; font-size: 15px; padding: 0 18px; cursor: pointer; }
.go { background: linear-gradient(180deg, #5C97F2, #2F6FE4); box-shadow: inset 0 -4px 0 rgba(0,0,0,.14), 0 8px 22px rgba(47,111,228,.35); }
.both { background: linear-gradient(180deg, #F07880, #D9363E); box-shadow: inset 0 -4px 0 rgba(0,0,0,.14), 0 8px 22px rgba(217,54,62,.3); }
.go:disabled, .both:disabled { opacity: .6; cursor: default; }
.body { display: none; gap: 20px; align-items: center; }
.on .body { display: flex; }
.mouth { flex: 0 0 38%; width: 38%; height: auto; border-radius: 22px; background: linear-gradient(180deg, #E6F0FF, #D6E6FD); }
.state { font-size: 28px; font-weight: 900; min-height: 38px; line-height: 1.2; }
.state .zh { font-weight: 600; color: #3A4664; font-size: 20px; }
.steps { flex: 1 1 auto; display: none; flex-direction: column; gap: 10px; }
.on.coaching .steps { display: flex; }
.on:not(.coaching) .mouth { flex-basis: 70%; width: 70%; margin: 0 auto; }
.st { display: flex; align-items: center; gap: 12px; font-size: 15.5px; font-weight: 700; color: #5B6B8C; padding: 10px 12px; border-radius: 16px; background: rgba(240,245,253,.95);
  border: 1.5px solid #E1E9F6; }
.st i { font-style: normal; width: 26px; height: 26px; border-radius: 50%; background: #D5DFF0; color: #fff; display: grid; place-items: center; font-weight: 900; }
.st.ok { color: #14793F; background: #E3F6EA; }
.st.bad { color: #B02A31; background: #FDE8EA; border-color: #F2B8BD; }
.st.bad i { background: #D9363E; }
.st.bad i::before { content: "!"; }
.st.bad i { font-size: 0; }
.st.bad i::before { font-size: 15px; }
.st.ok i { background: #1FA45B; }
.st.ok i::before { content: "\\2713"; }
.st.ok i { font-size: 0; }
.st.ok i::before { font-size: 15px; }
.snake { display: none; width: 100%; height: auto; border-radius: 18px; background: linear-gradient(180deg, #E4F2FF 0%, #E4F2FF 70%, #D3EBC4 70%); }
.on.snk .snake { display: block; }
.detail { display: none; font-size: 16px; line-height: 1.45; font-weight: 700; color: #1B2440; background: rgba(255,255,255,.7); border: 1.5px solid #D8E4F7; border-radius: 16px; padding: 12px 14px; }
.detail .zh { display: block; margin-top: 4px; font-weight: 600; color: #3A4664; font-size: 15px; }
.on.coaching.chd .detail { display: block; }
.bar { display: none; height: 16px; border-radius: 999px; background: rgba(214,226,246,.85); overflow: hidden; }
.on.coaching .bar { display: block; }
.fill { height: 100%; width: 0; background: linear-gradient(90deg, #4FC98A, #1FA45B); border-radius: 999px; transition: width .04s linear; box-shadow: 0 0 12px rgba(31,164,91,.5); }
.dbg { display: none; font-size: 12px; color: #8A96B0; border-top: 1.5px dashed #D5DFF0; padding-top: 10px; font-family: ui-monospace, Consolas, monospace; }
.on .dbg { display: block; }
"""

_JS = """
export default function (component) {
  const { parentElement: root, data } = component;
  const $ = (s) => root.querySelector(s);
  const detailEl = $(".detail"), box = $(".lc"), btn = $(".go"), cv = $(".mouth"), ctx = cv.getContext("2d"), stateEl = $(".state"), dbg = $(".dbg");
  const steps = [$(".s1"), $(".s2"), $(".s3"), $(".s4")], fill = $(".fill");
  const coach = !!data.coach, isN = data.sound === "n", isCh = ["tʃ", "s", "sh"].includes(data.sound), isPb = ["p", "b"].includes(data.sound);          // /p/ and /b/ ("pea", "bee"): the same three boxes and ghost mouth, from the camera alone; a hiss followed by "ee": the three boxes, the ghost mouth and the spread lips of the "ee" (tʃ: with the train; s and sh: with the live dot)            // /n/: the lips stay a little apart while humming (/m/ shuts them)
  if (isCh || isPb) {                                                   // /tʃ/: the three boxes are the three steps of the lesson (its card titles), lit from what the recorder's train has found and the lips
    [0, 1, 2].forEach((i) => { $(".s" + (i + 1)).lastChild.textContent = `${data.ghost[i].title} ${data.ghost[i].titleZh || ""}`; });
  } else if (data.vowel) {                                            // /m/ then /iː/: three boxes, the smile comes straight after the hum (the "open, keep the sound" step is gone)
    $(".s1").lastChild.textContent = data.sound === "n" ? "Hum with lips a little open 嘴唇微開哼聲" : "Hum with lips together 閉唇哼聲"; $(".s2").style.display = "none";
    $(".s3").lastChild.textContent = "Smile, small mouth 微笑，嘴小"; $(".s3").firstChild.textContent = "2";
    $(".s4").style.display = "flex"; $(".s4").firstChild.textContent = "3";
  }
  let stream = null, raf = 0, landmarker = null, stopped = false, audio = null, running = false, resetTurn = () => {}, baseW = null, baseStart = null, baseSamples = [], ghostT0 = null, snap = null;
  const both = $(".both");
  // the numbers of each turn go to the testing log (learner/camlog.py): lips and sound, ten a second, on the same clock as the recorder's numbers
  const frames = []; let turnId = Date.now(), together = false, flushed = false, recAt = 0, gateV = null;
  const flush = (reason) => {
    if (!data.logUrl || !frames.length) return;
    const body = JSON.stringify({ src: "mirror", word: data.word, vowel: !!data.vowel, coach, together, turn: turnId, reason, closedBelow: data.closedBelow, gate: gateV,
      periodic: data.periodic, smileRatio: data.smileRatio, smileGapMax: data.smileGapMax, frames });
    frames.length = 0; turnId = Date.now(); fetch(data.logUrl, { method: "POST", mode: "no-cors", body }).catch(() => {});
  };
  const say = (en, zh, colour) => { stateEl.innerHTML = `<span style="color:${colour || "#1B2440"}">${en}</span> <span class="zh">${zh}</span>`; };

  const draw = (gap, width, closed) => {                       // a mouth: closed = one line, open = an ellipse as tall as the lips are apart
    ctx.clearRect(0, 0, cv.width, cv.height);
    const cx = cv.width / 2, cy = cv.height / 2, w = Math.min(150, 60 + width * 380), h = Math.max(2, Math.min(110, gap * 650));   // 650: a small smile (gap ~0.04) is a thin mouth, "ah" (~0.15+) is tall
    if (coach && !closed && data.sound !== "n") {                // where the lips should go (for /m/; /n/ keeps them a little apart): a dashed line to close the mouth onto
      ctx.save(); ctx.setLineDash([10, 10]); ctx.strokeStyle = "#1FA45B"; ctx.lineWidth = 4; ctx.beginPath();
      ctx.moveTo(cx - w, cy); ctx.lineTo(cx + w, cy); ctx.stroke(); ctx.restore();
    }
    ctx.fillStyle = "#E5484D"; ctx.strokeStyle = "#B8323A"; ctx.lineWidth = 6; ctx.lineCap = "round";
    if (closed) {
      ctx.beginPath(); ctx.ellipse(cx, cy - 7, w, 16, 0, Math.PI, 0); ctx.ellipse(cx, cy + 7, w, 16, 0, 0, Math.PI); ctx.fill();
      ctx.beginPath(); ctx.moveTo(cx - w, cy); ctx.lineTo(cx + w, cy); ctx.stroke();
    } else {
      ctx.beginPath(); ctx.ellipse(cx, cy, w, h / 2 + 9, 0, 0, 7); ctx.fill();
      ctx.fillStyle = "#4A1B20"; ctx.beginPath(); ctx.ellipse(cx, cy, w - 12, Math.max(1.5, h / 2 - 1), 0, 0, 7); ctx.fill();
    }
  };

  const drawCh = (gap, ratio, closed, ghost) => {                     // /tʃ/: both mouths on the scale "relaxed lips = 90", so that a rounded mouth is narrower and a spread one wider
    ctx.clearRect(0, 0, cv.width, cv.height);
    const cx = cv.width / 2, cy = cv.height / 2, hOf = (g) => Math.max(2, Math.min(110, g * 650));
    if (ghost) {
      ctx.save(); ctx.setLineDash([10, 10]); ctx.lineWidth = 4; ctx.strokeStyle = ghost.ok ? "#1FA45B" : "#7C8CAA"; ctx.fillStyle = ghost.ok ? "rgba(31,164,91,.14)" : "rgba(124,140,170,.10)";
      ctx.beginPath(); ctx.ellipse(cx, cy, Math.min(170, 90 * ghost.ratio), hOf(ghost.gap) / 2 + 9, 0, 0, 7); ctx.fill(); ctx.stroke(); ctx.restore();
    }
    const w = Math.max(40, Math.min(170, 90 * ratio)), h = hOf(gap);
    ctx.fillStyle = "#E5484D"; ctx.strokeStyle = "#B8323A"; ctx.lineWidth = 6; ctx.lineCap = "round";
    if (closed) { ctx.beginPath(); ctx.ellipse(cx, cy - 7, w, 16, 0, Math.PI, 0); ctx.ellipse(cx, cy + 7, w, 16, 0, 0, Math.PI); ctx.fill(); ctx.beginPath(); ctx.moveTo(cx - w, cy); ctx.lineTo(cx + w, cy); ctx.stroke(); }
    else { ctx.beginPath(); ctx.ellipse(cx, cy, w, h / 2 + 9, 0, 0, 7); ctx.fill(); ctx.fillStyle = "#4A1B20"; ctx.beginPath(); ctx.ellipse(cx, cy, Math.max(2, w - 12), Math.max(1.5, h / 2 - 1), 0, 0, 7); ctx.fill(); }
  };

  const listen = (stream) => {                                  // the voice, read only as loudness and as the share of low pitch
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    const an = ac.createAnalyser(); an.fftSize = 2048; an.smoothingTimeConstant = 0;
    ac.createMediaStreamSource(stream).connect(an);
    if (ac.state === "suspended") ac.resume();
    const td = new Float32Array(an.fftSize), fd = new Float32Array(an.frequencyBinCount), hz = ac.sampleRate / an.fftSize;
    const lowBins = Math.floor(1000 / hz);
    const lagLo = Math.floor(ac.sampleRate / 500), lagHi = Math.ceil(ac.sampleRate / 80);
    const periodicity = (x) => {                                // how well the frame repeats itself at a pitch of 80-500 Hz: a voice does (about 0.8+), room noise and rumble do not
      let m = 0; for (let i = 0; i < x.length; i++) m += x[i]; m /= x.length;
      let r0 = 0; for (let i = 0; i < x.length; i++) r0 += (x[i] - m) * (x[i] - m);
      if (r0 < 1e-9) return 0;
      const n = x.length - lagHi; let best = 0;
      for (let lag = lagLo; lag <= lagHi; lag += 2) {
        let s = 0; for (let i = 0; i < n; i++) s += (x[i] - m) * (x[i + lag] - m);
        best = Math.max(best, s / (r0 * n / x.length));
      }
      return best;
    };
    let cache = null, cacheAt = -1;
    return { ac, read: () => {
      const n = performance.now(); if (cache && n - cacheAt < 8) return cache;               // measured once per picture, however often it is asked
      an.getFloatTimeDomainData(td); an.getFloatFrequencyData(fd);
      let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i];
      const db = 10 * Math.log10(s / td.length + 1e-12);
      let low = 0, all = 0; for (let i = 1; i < fd.length; i++) { const p = Math.pow(10, fd[i] / 10); all += p; if (i < lowBins) low += p; }
      cache = { db, low: all > 0 ? low / all : 0, per: db > -70 ? periodicity(td) : 0 }; cacheAt = n;
      return cache;
    } };
  };

  const start = async () => {
    if (running) return;
    btn.disabled = true; both.disabled = true; say("Loading… 載入中", "");
    try {
      const base = `${location.origin}/app/static/mediapipe`;
      const { FilesetResolver, FaceLandmarker } = await import(`${base}/vision_bundle.mjs`);
      const fileset = await FilesetResolver.forVisionTasks(`${base}/wasm`);
      landmarker = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: `${base}/face_landmarker.task`, delegate: "CPU" }, runningMode: "VIDEO", numFaces: 1 });
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: 320, height: 240 },
        audio: coach ? { echoCancellation: false, noiseSuppression: false, autoGainControl: false } : false });
      if (coach) audio = listen(stream);
    } catch (err) {
      btn.disabled = false; both.disabled = false; say("The camera could not start", "無法啟動相機", "#D9363E"); dbg.textContent = String(err && err.message || err); return;
    }
    const video = document.createElement("video");                  // never put on the page: the picture is only read, not shown
    video.muted = true; video.playsInline = true; video.srcObject = stream; await video.play();
    box.classList.add("on"); if (coach || isCh || isPb) box.classList.add("coaching"); if (isCh || isPb) box.classList.add("chd");
    const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    const gate = data.noiseDb == null ? data.quietDb : Math.max(data.quietDb, data.noiseDb + data.aboveNoiseDb);
    let closed = false, held = 0, lastGood = 0, doneAt = 0, last = performance.now(), stage = 0, baseW = null, lastVoice = 0;
    const mark = (i, on) => steps[i].classList.toggle("ok", !!on);
    // nothing starts or restarts by itself: a turn begins with Start (or "together") and goes again only with Restart
    gateV = gate; let gateNow = gate, noiseEst = null, armed = true, quietAt = null, measuring = true, measureStart = null, roomFrames = [], roomTooLoud = false;
    // a hum counts only after a quiet moment since the turn began: a hum that was already going when Start or Restart was pressed (or a steady sound in the room) does not tick the box by itself
    const arm = (voiced, now) => { if (data.armQuietS <= 0) return; if (armed) return; if (voiced) quietAt = null; else { if (quietAt === null) quietAt = now; if (now - quietAt > data.armQuietS * 1000) armed = true; } };
    const readSnap = () => { const T = window.__lnTrain; if (T && T.on && performance.now() - T.t < 600) snap = T; };       // what the recorder's train or guide has found (learner/mic.py); the last of it stays on the screen
    const paintBoxes = () => {
      const s2 = snap && snap.hissEnded && snap.pop && snap.hiss ? (snap.pop !== "red" && snap.hiss !== "red" ? "ok" : "bad") : null;
      mark(0, baseW !== null); steps[1].classList.toggle("ok", s2 === "ok"); steps[1].classList.toggle("bad", s2 === "bad"); mark(2, !!(snap && snap.win));
      fill.style.width = `${snap ? (snap.win ? 100 : Math.round(100 * snap.progress)) : 0}%`;
    };
    // /s/ and /ʃ/: a snake drawn from the same numbers as the boxes and the bar (the assistant's own picture, not the content owner's). It grows while the hiss is held in the zone (the dot green or yellow),
    // up to the middle; the "ee" brings its head on to the flag, as far as the bar. Its colour is the dot's. The count of the hiss only goes up, so the snake does not shrink; out of the zone it stops and turns red.
    const snakeOn = data.sound === "s" || data.sound === "sh", sn = $(".snake"), snx = sn.getContext("2d");
    let snLen = 0.04, snPh = 0;
    if (snakeOn) box.classList.add("snk");
    const drawSnake = (now) => {
      const W = sn.width, H = sn.height, c = snx, tailX = 36, endX = W - 84, midY = 92;
      const dot = window.__lnDot, dc = dot && now - dot.t < 300 ? dot.color : null;
      const T = snap, need = T && T.need ? T.need : 400;
      const hissPart = T ? Math.min(1, (T.inZone || 0) / need) : 0, eePart = T ? (T.win ? 1 : T.progress || 0) : 0;
      const target = T && T.win ? 1 : 0.04 + 0.46 * hissPart + 0.5 * eePart;
      snLen += (target - snLen) * (target > snLen ? 0.4 : 0.1);
      const hissing = !!(T && T.listening && T.hissMs > 0 && !T.hissEnded) || !!(T && T.listening && T.hissMs > 0 && dc);
      if ((hissing && target - snLen > 0.001) || (T && eePart > 0 && !T.win)) snPh += 0.2; else if (T && T.win) snPh += 0.08;
      const green = "#1FA45B", col = T && (T.win || eePart > 0 || (T.hissEnded && T.hiss === "green")) ? green : !T ? "#9CB7A0" : dc === "red" ? "#D9363E" : dc === "yellow" ? "#E0A81A" : dc === "green" ? green : T.hissEnded ? "#D9363E" : "#9CB7A0";
      c.clearRect(0, 0, W, H);
      const flagX = W - 40;                                                     // the flag at the end, as the train's: grey until "ee" has been held
      c.strokeStyle = "#5B6B8C"; c.lineWidth = 5; c.lineCap = "round"; c.beginPath(); c.moveTo(flagX, 112); c.lineTo(flagX, 34); c.stroke();
      c.fillStyle = T && T.win ? green : "#B6C0D4"; c.beginPath(); c.moveTo(flagX, 34); c.lineTo(flagX + 30, 46 + (T && T.win ? 5 * Math.sin(now / 120) : 0)); c.lineTo(flagX, 60); c.fill();
      const headX = tailX + snLen * (endX - tailX), pts = [];
      for (let x = tailX; x <= headX; x += 5) pts.push([x, midY + 18 * Math.sin(x * 0.05 - snPh)]);
      pts.push([headX, midY + 18 * Math.sin(headX * 0.05 - snPh)]);
      c.lineJoin = "round"; c.lineCap = "round";
      for (const [w, s] of [[34, "#1B2440"], [24, col]]) { c.strokeStyle = s; c.lineWidth = w; c.beginPath(); pts.forEach((p, i) => (i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]))); c.stroke(); }
      const [hx, hy] = pts[pts.length - 1];
      if (hissing || (T && T.win)) { c.strokeStyle = "#D9363E"; c.lineWidth = 3; c.beginPath(); c.moveTo(hx + 18, hy); c.lineTo(hx + 34 + 4 * Math.sin(now / 60), hy); c.moveTo(hx + 34, hy); c.lineTo(hx + 41, hy - 5); c.moveTo(hx + 34, hy); c.lineTo(hx + 41, hy + 5); c.stroke(); }
      c.fillStyle = col; c.strokeStyle = "#1B2440"; c.lineWidth = 5; c.beginPath(); c.ellipse(hx + 4, hy, 22, 19, 0, 0, 7); c.fill(); c.stroke();
      c.fillStyle = "#fff"; c.beginPath(); c.arc(hx + 6, hy - 6, 6.5, 0, 7); c.fill(); c.fillStyle = "#1B2440"; c.beginPath(); c.arc(hx + 8, hy - 6, 3.2, 0, 7); c.fill();
    };
    if (isCh) { const ui = (now) => { if (stopped) return; readSnap(); paintBoxes(); if (snakeOn) drawSnake(now); requestAnimationFrame(ui); }; requestAnimationFrame(ui); }      // every screen frame, whatever the face detector takes: the bar follows the voice at once
    resetTurn = () => { baseW = null; baseStart = null; baseSamples = []; ghostT0 = null; snap = null; flush("restart"); flushed = false; together = false; closed = false; held = 0; lastGood = 0; doneAt = 0; stage = 0; armed = true; quietAt = null; measuring = true; measureStart = null; roomFrames = []; roomTooLoud = false; lastVoice = performance.now(); steps.forEach((el) => el.classList.remove("ok")); fill.style.width = "0"; };
    running = true; btn.disabled = false; both.disabled = false;
    btn.textContent = "Restart 重新開始"; btn.onclick = () => resetTurn();
    resetTurn();
    const tick = () => {
      if (stopped) return;
      const now = performance.now(), dt = now - last; last = now;
      const res = landmarker.detectForVideo(video, now);
      const lm = res.faceLandmarks && res.faceLandmarks[0];
      const a0 = coach && audio ? audio.read() : null, logNow = now - recAt >= 100 && frames.length < 6000;
      if (a0 && measuring) {                                       // ONE threshold, measured first: the room is listened to for measureS after each Start/Restart, its level + a margin is the gate
        if (measureStart === null) measureStart = now;            // (the same as the recorder's; if the room is louder than roomMaxDb the window starts again)
        if (a0.db > -100) roomFrames.push(a0.db);
        if (now - measureStart >= data.measureS * 1000) {
          const sorted = roomFrames.slice().sort((x, y) => x - y), room = sorted.length >= 3 ? sorted[Math.floor(sorted.length / 2)] : null;
          if (room === null) { measureStart = now; roomFrames = []; }
          else if (room > data.roomMaxDb) { measureStart = now; roomFrames = []; roomTooLoud = true; }
          else { gateNow = Math.min(data.gateMaxDb, Math.max(data.quietDb, room + data.aboveNoiseDb)); measuring = false; roomTooLoud = false; }
        }
      }
      const logIt = (extra) => {
        if (!logNow) return;
        recAt = now;
        frames.push(Object.assign({ t: Math.round(performance.timeOrigin + now), stage, meas: measuring ? 1 : 0, gate: +gateNow.toFixed(1), face: 0, db: a0 ? +a0.db.toFixed(1) : null, low: a0 ? +a0.low.toFixed(2) : null,
          per: a0 ? +a0.per.toFixed(2) : null, voiced: a0 ? (!measuring && a0.db > gateNow && a0.low > data.lowShare && a0.per > data.periodic ? 1 : 0) : null }, extra));
        if (frames.length >= 600) flush("chunk");
      };
      if (doneAt && !flushed && now - doneAt > 1500) { flushed = true; flush("done"); }
      if (!lm) { if (isCh) window.__lnLips = { on: true, face: false, t: now, spread: false }; logIt({}); ctx.clearRect(0, 0, cv.width, cv.height); say("I cannot see your face", "看不到你的臉", "#8A96B0"); dbg.textContent = ""; }
      else {
        const face = dist(lm[10], lm[152]), gap = dist(lm[13], lm[14]) / face, width = dist(lm[78], lm[308]) / face;
        closed = closed ? gap < data.closedBelow * 1.4 : gap < data.closedBelow;              // a little hysteresis so it does not flicker
        const lipsOk = isN ? (!closed && gap < data.openMax) : closed;                       // the lips as this sound wants them while it is hummed
        logIt({ face: 1, gap: +gap.toFixed(4), width: +width.toFixed(4), closed: closed ? 1 : 0, ratio: baseW ? +(width / baseW).toFixed(3) : null });
        if (!isCh && !isPb) draw(gap, width, closed);
        if (isPb) {                                                  // /p/ /b/ + "ee": lips together, then open, then spread; the camera alone (the sound is not read here). stage 0 waiting for the lips to close, 1 closed long enough, 2 opened, 3 spread (held), 4 done
          if (closed) baseW = baseW == null ? width : 0.9 * baseW + 0.1 * width;                      // the width of this child's closed lips: the spread of the "ee" is measured against it (as for "me")
          const ratio = baseW ? width / baseW : 1, spread = baseW !== null && ratio >= data.smileRatio && gap < data.smileGapMax;
          if (stage === 0) { held = closed ? held + dt : 0; if (held >= data.pbCloseS * 1000) { stage = 1; held = 0; } }
          else if (stage === 1) { if (!closed) stage = 2; }
          if (stage === 2 && spread) { stage = 3; held = 0; lastGood = now; }
          else if (stage === 3) {
            if (spread) lastGood = now;
            held = spread ? held + dt : (now - lastGood < 200 ? held : 0);
            if (!spread && now - lastGood > 400) { stage = 2; held = 0; }
            if (held >= data.pbHoldS * 1000) { stage = 4; doneAt = now; }
          }
          steps.forEach((el, i) => el.classList.toggle("ok", i === 0 ? stage >= 1 : i === 1 ? stage >= 2 : i === 2 ? stage >= 4 : false));
          fill.style.width = `${stage === 4 ? 100 : stage === 3 ? Math.min(100, held / (data.pbHoldS * 1000) * 100) : 0}%`;
          const step = stage <= 1 ? 0 : stage === 2 ? 1 : 2, g = data.ghost[step], ghost = { ratio: g.ratio, gap: g.gap, ok: Math.abs(ratio - g.ratio) / 0.12 + Math.abs(gap - g.gap) / 0.025 <= 1.5 };
          drawCh(gap, ratio, closed, ghost);
          say(stage === 4 ? "Well done ✓" : g.title + (ghost.ok ? " ✓" : ""), stage === 4 ? "做得好" : (g.titleZh || ""), stage === 4 || ghost.ok ? "#1FA45B" : "#1B2440");
          detailEl.innerHTML = `${g.detail}<span class="zh">${g.detailZh}</span>`;
          dbg.textContent = `gap ${gap.toFixed(3)} (closed < ${data.closedBelow}) · width ${width.toFixed(3)} (closed lips ${baseW === null ? "?" : baseW.toFixed(3)}, ratio ${ratio.toFixed(2)}, spread from ×${data.smileRatio}) · stage ${stage}`;
        } else if (isCh) {                                                  // /tʃ/ (the train, in the recorder): the lips relaxed while the room is listened to are the baseline; "spread" is the same test as the smile of "me"
          if (baseStart === null) baseStart = now;
          if (baseW === null) { baseSamples.push(width); if (now - baseStart >= data.measureS * 1000 + 200) { const s = baseSamples.slice().sort((x, y) => x - y); baseW = s[Math.floor(s.length / 2)]; } }
          const ratio = baseW ? width / baseW : 1, spread = baseW !== null && ratio >= data.smileRatio && gap < data.smileGapMax;
          window.__lnLips = { on: true, face: true, t: now, ratio, gap, spread };
          // the ghost mouth: a dashed mouth that moves through the three steps of the lesson, slowly; the real mouth is drawn over it, the ghost turns green where they agree (it only shows, nothing waits for it)
          readSnap(); paintBoxes();
          let ghost = null, step = -1;
          if (baseW !== null) {
            if (ghostT0 === null) ghostT0 = now;
            step = snap ? (snap.win || snap.voiceAt ? 2 : snap.popAt ? 1 : 0)                              // the ghost goes on when the child does
                        : Math.min(data.ghost.length - 1, Math.floor((now - ghostT0) / (data.ghostStepS * 1000)));
            const g = data.ghost[step], near = Math.abs(ratio - g.ratio) / 0.12 + Math.abs(gap - g.gap) / 0.025 <= 1.5;
            ghost = { ratio: g.ratio, gap: g.gap, ok: near };
          }
          drawCh(gap, ratio, closed, ghost);
          if (baseW === null) { say("Wait, stay quiet", "請稍等，先不要出聲", "#2F6FE4"); detailEl.innerHTML = `${data.ghost[0].detail}<span class="zh">${data.ghost[0].detailZh}</span>`; }
          else say(data.ghost[step].title + (ghost.ok ? " ✓" : ""), data.ghost[step].titleZh || "", ghost.ok ? "#1FA45B" : "#1B2440");
          const gd = data.ghost[step < 0 ? 0 : step];                                 // what to do with the tongue, the air and the lips at this step
          detailEl.innerHTML = `${gd.detail}<span class="zh">${gd.detailZh}</span>`;
          dbg.textContent = `width ${width.toFixed(3)} (relaxed ${baseW === null ? "?" : baseW.toFixed(3)}, ratio ${ratio.toFixed(2)}, smile from ×${data.smileRatio}) · gap ${gap.toFixed(3)} (small < ${data.smileGapMax})`;
        } else if (!coach) {
          if (closed) say("Lips together ✓", "雙唇閉合", "#1FA45B"); else say("Lips open", "雙唇張開", "#1B2440");
          dbg.textContent = `gap ${gap.toFixed(3)} · limit ${data.closedBelow}`;
        } else if (data.vowel) {                                      // /m/ then /iː/: hum closed, slide open without a break, smile small, hold
          const a = audio.read(), voiced = !measuring && a.db > gateNow && a.low > data.lowShare && a.per > data.periodic;
          if (closed || (data.sound === "n" && stage === 0)) baseW = baseW == null ? width : 0.9 * baseW + 0.1 * width;                  // this child's width of the closed lips: the smile is measured against it
          const smile = baseW != null && width >= baseW * data.smileRatio && gap < data.smileGapMax;
          if (voiced) lastVoice = now;
          arm(voiced, now);
          if (stage === 0) {
            const good = lipsOk && voiced && armed;
            if (good) lastGood = now;
            held = good ? held + dt : (now - lastGood < 200 ? held : 0);
            if (held >= data.mHoldS * 1000) { stage = 2; held = 0; lastGood = now; }              // straight on to the smile: there is no step in between
          } else if (stage === 1) { if (voiced && !closed) stage = 2; }
          else if (stage === 2) { if (voiced && smile) { stage = 3; held = 0; lastGood = now; } }
          else if (stage === 3) {
            const good = voiced && smile;
            if (good) lastGood = now;
            held = good ? held + dt : (now - lastGood < 200 ? held : 0);
            if (!smile && now - lastGood > 400) { stage = 2; held = 0; }
            if (held >= data.holdS * 1000) { stage = 4; doneAt = now; }
          }
          steps.forEach((el, i) => el.classList.toggle("ok", stage > i));
          fill.style.width = `${stage === 4 ? 100 : stage === 3 ? Math.min(100, held / (data.holdS * 1000) * 100) : 0}%`;
          if (stage === 4) say("Well done ✓", "做得好", "#1FA45B");
          else if (stage === 0) { if (measuring) say(roomTooLoud ? "Please be quiet for a moment" : "Wait, stay quiet", roomTooLoud ? "請先安靜一下" : "請稍等，先不要出聲", roomTooLoud ? "#C2410C" : "#2F6FE4");
            else if (voiced && !lipsOk) say(isN ? "Lips a little open, then hum" : "Close your lips and hum", isN ? "嘴唇微開，再哼" : "閉上嘴唇再哼", "#C2410C");
            else if (lipsOk && !voiced) say("Now hum  " + (isN ? "nnn" : "mmm"), "現在哼「嗯」", "#2F6FE4");
            else if (lipsOk) say("Keep humming", "繼續哼", "#1FA45B"); else say(isN ? "Lips a little open, then hum" : "Lips together, then hum", isN ? "嘴唇微開，再哼" : "先閉上嘴唇，再哼", "#1B2440"); }
          else if (stage === 1) say("Open your lips, keep the sound going", "張開嘴唇，聲音不要停", "#2F6FE4");
          else if (!voiced) say("Don't stop, keep the sound", "別停，繼續出聲", "#C2410C");
          else if (stage === 2 && gap >= data.smileGapMax) say("Make your mouth small", "嘴巴小一點", "#C2410C");
          else if (stage === 2) say("Smile wide", "笑開一點", "#2F6FE4");
          else say("Keep smiling and singing", "保持微笑與聲音", "#1FA45B");
          if (stage >= 1 && stage < 4) {                                                         // the smile to reach: a dashed, wide, flat mouth
            ctx.save(); ctx.setLineDash([10, 10]); ctx.strokeStyle = "#1FA45B"; ctx.lineWidth = 4; ctx.beginPath();
            ctx.ellipse(cv.width / 2, cv.height / 2, 180, 36, 0, 0, 7); ctx.stroke(); ctx.restore();
          }
          dbg.textContent = `gap ${gap.toFixed(3)} (small < ${data.smileGapMax}) · width ${width.toFixed(3)} (closed ${baseW == null ? "?" : baseW.toFixed(3)}, smile ≥ ×${data.smileRatio}) · sound ${a.db.toFixed(0)} dB (gate ${gateNow.toFixed(0)}) · low ${(a.low * 100).toFixed(0)}% · voice ${a.per.toFixed(2)} (needs ${data.periodic})`;
        } else {
          const a = audio.read(), voiced = !measuring && a.db > gateNow && a.low > data.lowShare && a.per > data.periodic; arm(voiced, now); const good = lipsOk && voiced && armed;
          if (good) lastGood = now;
          held = good ? held + dt : (now - lastGood < 200 ? held : 0);                         // a gap shorter than 0.2 s does not break the hum
          if (held >= data.holdS * 1000 && !doneAt) doneAt = now;
          mark(0, lipsOk); mark(1, good || doneAt); mark(2, doneAt);
          fill.style.width = `${Math.min(100, (doneAt ? 1 : held / (data.holdS * 1000)) * 100)}%`;
          if (doneAt) say("Well done ✓", "做得好", "#1FA45B");
          else if (measuring) say(roomTooLoud ? "Please be quiet for a moment" : "Wait, stay quiet", roomTooLoud ? "請先安靜一下" : "請稍等，先不要出聲", roomTooLoud ? "#C2410C" : "#2F6FE4");
          else if (voiced && !lipsOk) say(isN ? "Lips a little open, then hum" : "Close your lips and hum", isN ? "嘴唇微開，再哼" : "閉上嘴唇再哼", "#C2410C");
          else if (lipsOk && !voiced) say("Now hum  " + (isN ? "nnn" : "mmm"), "現在哼「嗯」", "#2F6FE4");
          else if (good) say("Keep humming", "繼續哼", "#1FA45B");
          else say(isN ? "Lips a little open, then hum" : "Lips together, then hum", isN ? "嘴唇微開，再哼" : "先閉上嘴唇，再哼", "#1B2440");
          dbg.textContent = `gap ${gap.toFixed(3)} (limit ${data.closedBelow}) · sound ${a.db.toFixed(0)} dB (gate ${gateNow.toFixed(0)}) · low ${(a.low * 100).toFixed(0)}% (needs ${data.lowShare * 100}%)`;
        }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
  };
  btn.onclick = start;
  both.onclick = async () => {                                  // one press: the mirror turn and the recording begin together
    if (!running) await start(); else resetTurn();
    together = true;
    const m = window.__lnMic;                                   // the record button (learner/mic.py) shares this page
    if (running && m && m.run && !(m.busy && m.busy())) m.run();
  };
  return () => { window.__lnLips = { on: false }; snap = null; flush("closed"); stopped = true; cancelAnimationFrame(raf); if (stream) stream.getTracks().forEach((t) => t.stop());
    if (audio) audio.ac.close(); if (landmarker) landmarker.close(); };
}
"""

_component = components.component("lip_mirror", html=_HTML, css=_CSS, js=_JS)


def lip_mirror(key: str, coach: bool = False, noise_db: float | None = None, vowel: bool = False, sound: str = "m", log_url: str | None = None, word: str = "") -> None:
    """The lip mirror. It asks for the camera (and, as a coach, the microphone) only when its own button is pressed; the browser asks the person once more.
    noise_db: the room noise from Sound Check, for the sound gate."""
    _component(key=key, data={"closedBelow": CLOSED_BELOW, "coach": coach, "holdS": HOLD_S, "lowShare": LOW_SHARE, "quietDb": QUIET_DBFS,
                              "aboveNoiseDb": ABOVE_NOISE_DB, "noiseDb": noise_db, "vowel": vowel, "sound": sound, "ghost": GHOSTS.get(sound, CH_GHOST), "ghostStepS": CH_GHOST_STEP_S, "openMax": N_OPEN_MAX, "periodic": PERIODIC, "armQuietS": ARM_QUIET_S, "measureS": MEASURE_S, "roomMaxDb": ROOM_MAX_DBFS, "logUrl": log_url, "word": word, "gateMaxDb": GATE_MAX_DBFS,
                              "mHoldS": M_HOLD_S, "pbCloseS": PB_CLOSE_S, "pbHoldS": PB_HOLD_S, "smileRatio": SMILE_RATIO, "smileGapMax": SMILE_GAP_MAX})
