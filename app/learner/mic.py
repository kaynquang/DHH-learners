"""The big record button of the learner screen: tap it (or press Space), say the word, and it stops by itself after a few seconds.

Same recording method as the Dev app (raw microphone: no echo cancelling, noise suppression or auto gain; WAV made in the browser), with
the look from the design mockup. While it records the button only changes visually (a red stop square and a pulsing ring); the mockup
has no other recording state, so no new wording is added.
"""
from __future__ import annotations

import base64

import streamlit as st
import streamlit.components.v2 as components

from .lessons import ACCENT

RECORD_SECONDS = 3.0
# guided recording ("me": mmm, then ee): it follows the child's voice and stops by itself. All first guesses, to tune on real voices.
GUIDE_END_SILENCE_S = 1.5     # stops this long after the child has gone quiet (once at least 0.6 s of sound was heard)
GUIDE_MAX_S = 12.0            # the longest recording
GUIDE_WAIT_S = 10.0           # stops if nothing at all was heard in this time
GUIDE_STEP_S = 0.4            # a sound counts as said after this long
GUIDE_EE_REL_DB = -25.0       # energy at 2-3.5 kHz relative to 0.1-1 kHz at or above this: "ee" (a hum is far below)
GUIDE_VOWEL_JUMP_DB = 4.0     # any vowel after the hum: the high/low ratio rises this much above the child's own hum (first log: hum -21 dB, vowel -15 to -17 dB) ...
GUIDE_VOWEL_F_JUMP_DB = 6.0   # ... or the energy at 300-600 Hz against 1-1.5 kHz rises this much (first log: the hum -4 to +2 dB, the vowel +8 to +14 dB; a lone speaker)
GUIDE_VOWEL_LOUDER_DB = 6.0  # ... or the sound is this much louder than the hum (a vowel is louder than a nasal hum)
GUIDE_PERIODIC = 0.6          # a voice repeats itself at its pitch (0.77-1.0 in the first log); a steady hum of a fan can too, so the gate follows the room as well
GUIDE_EE_MARGIN_DB = 4.0      # the voice of the "ee" after a hiss must be this far over the room (the user's "ee" is only 3-8 dB over a room of -46 dB, log of 01:46); the pitch-repeat test keeps noise out
GUIDE_NOISE_MARGIN_DB = 7.0   # the sound gate is this far above the room noise measured during the recording itself (first log: room -38 dB, voice -22 to -30 dB)
GUIDE_QUIET_DBFS = -50.0
GUIDE_MEASURE_S = 0.6         # the room is listened to for this long after the tap, before anything counts; its level + the margin below is the one gate
GUIDE_ROOM_MAX_DBFS = -32.0   # a room louder than this (already humming, or a very noisy room) cannot be measured: the window starts again (first logs: room -38 dB, hum -22 dB)
GUIDE_AFTER_VOWEL_S = 1.0    # the recording stops this long after the vowel was heard (a guess)
GUIDE_GATE_MAX_DBFS = -28.0   # the gate never rises above this, however loud the room (the first log: a voice at -22 to -30 dB)
GUIDE_ABOVE_NOISE_DB = 10.0


TRAIN_BRIDGE_S = 2.0          # /tʃ/: the voice (the vowel) must start within this long after the hiss ends, else the rail is shown broken. A guess, wide on purpose: deaf children's
                              # transitions are slower and less even (METHOD_NOTES 8c.y); to be tightened from the "gap" in the log
TRAIN_HOLD_VOICE_S = 0.5      # how long the voice must go on for the train to reach the flag


def affricate_settings(log_url: str | None = None, word: str = "") -> dict:
    """The live /tʃ/ guide (two lamps, "t" and "sh"): the limits are those of learner/affricate_check.py, which scores the same two things after the recording."""
    from . import affricate_check as A
    return {"kind": "ch", "logUrl": log_url, "word": word, "first": "t", "second": "sh", "measureS": 0.6, "roomMaxDb": GUIDE_ROOM_MAX_DBFS,
            "startDb": 12.0, "minPeakDb": 20.0, "popAfterMs": 30, "endDb": A.END_DB, "quietDb": 8.0, "endQuietS": 1.5, "waitS": 8.0, "maxS": 8.0,
            "periodic": GUIDE_PERIODIC, "quietDb2": GUIDE_QUIET_DBFS, "voiceMarginDb": GUIDE_EE_MARGIN_DB, "voiceAfterMs": 40, "smileGapMax": 0.10,
            "bridgeS": TRAIN_BRIDGE_S, "holdVoiceS": TRAIN_HOLD_VOICE_S, "afterWinS": 1.0,
            "slopeOk": A.SLOPE_OK_DB_MS, "slopeAlmost": A.SLOPE_ALMOST_DB_MS, "hissOk": A.HISS_OK_MS, "hissAlmost": A.HISS_ALMOST_MS}


def fricative_settings(log_url: str | None = None, word: str = "") -> dict:
    """The live /s/ and /ʃ/ guide with "ee" after the hiss ("see", "she"): the dot of the live view and the steps of the lip mirror (learner/lipcam.py). The zone comes from the zones passed to the recorder."""
    return {"kind": "fric", "logUrl": log_url, "word": word, "first": "", "measureS": 0.6, "roomMaxDb": GUIDE_ROOM_MAX_DBFS, "startDb": 12.0, "endMarginDb": 6.0, "endHoldMs": 150, "minHissMs": 300,
            "inZoneMs": 400, "quietDb": 8.0, "endQuietS": 1.5, "waitS": 8.0, "maxS": 10.0, "periodic": GUIDE_PERIODIC, "quietDb2": GUIDE_QUIET_DBFS, "voiceMarginDb": GUIDE_EE_MARGIN_DB,
            "smileGapMax": 0.10, "bridgeS": TRAIN_BRIDGE_S, "holdVoiceS": TRAIN_HOLD_VOICE_S, "afterWinS": 1.0}


def guide_settings(noise_db: float | None, log_url: str | None = None, word: str = "", first: str = "mmm") -> dict:
    """The settings of the guided recording; the sound gate follows the room noise from Sound Check when it is known."""
    gate = GUIDE_QUIET_DBFS if noise_db is None else max(GUIDE_QUIET_DBFS, noise_db + GUIDE_ABOVE_NOISE_DB)
    return {"gateDb": gate, "endSilenceS": GUIDE_END_SILENCE_S, "maxS": GUIDE_MAX_S, "waitS": GUIDE_WAIT_S, "stepS": GUIDE_STEP_S, "eeRelDb": GUIDE_EE_REL_DB,
            "logUrl": log_url, "word": word, "first": first, "afterVowelS": GUIDE_AFTER_VOWEL_S, "measureS": GUIDE_MEASURE_S, "roomMaxDb": GUIDE_ROOM_MAX_DBFS, "quietDb": GUIDE_QUIET_DBFS, "gateMaxDb": GUIDE_GATE_MAX_DBFS, "noiseMarginDb": GUIDE_NOISE_MARGIN_DB, "periodic": GUIDE_PERIODIC, "fJumpDb": GUIDE_VOWEL_F_JUMP_DB, "jumpDb": GUIDE_VOWEL_JUMP_DB, "louderDb": GUIDE_VOWEL_LOUDER_DB}

_HTML = """
<div class="panel">
  <div class="ring"><button type="button" class="mic" aria-label="Record: tap and say the word">
    <svg class="i-mic" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="9" y="2.5" width="6" height="11.5" rx="3" fill="#fff"/>
      <path d="M 5.5 11 C 5.5 15, 8.5 17.5, 12 17.5 C 15.5 17.5, 18.5 15, 18.5 11 M 12 17.5 L 12 21 M 8.5 21 L 15.5 21" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <svg class="i-stop" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2.5" fill="#fff"/></svg>
  </button></div>
  <canvas class="spec" width="600" height="380" aria-label="Your sound as a picture"></canvas>
  <div class="prog" role="progressbar" aria-label="How much of the green you have filled"><div></div></div>
  <div class="guide" aria-label="The sounds in the order to say them"><span class="g g1">mmm</span><span class="arrow">→</span><span class="g g2">smile</span></div>
  <div class="gs" role="status"></div>
  <div class="t1">Tap and say it</div>
  <div class="t2">按一下說說看</div>
  <div class="t3">Click the mic or press <kbd>Space</kbd> · <span>點麥克風或按空白鍵</span></div>
</div>
"""

_CSS = f"""
:host {{ display: block; height: 100%; }}
.panel {{ box-sizing: border-box; min-height: 660px; height: 100%; background: #fff; border: 1.5px solid #D5DFF0; border-radius: 24px;
  box-shadow: 0 4px 0 #D5DFF0; padding: 32px 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px;
  font-family: 'Nunito', 'Noto Sans TC', system-ui, sans-serif; color: #1B2440; }}
.ring {{ width: 228px; height: 228px; border-radius: 50%; background: #DCE6FB; display: flex; align-items: center; justify-content: center; position: relative; }}
.mic {{ width: 200px; height: 200px; border-radius: 50%; border: none; background: {ACCENT}; box-shadow: inset 0 -8px 0 rgba(0,0,0,0.18);
  display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; position: relative; z-index: 1; }}
.mic svg {{ width: 92px; height: 92px; }}
.spec {{ display: none; width: 100%; max-width: 300px; height: auto; aspect-ratio: 600 / 380; border-radius: 16px; border: 1.5px solid #D5DFF0; }}
.has-spec .spec {{ display: block; }}
.prog {{ display: none; width: 100%; max-width: 300px; height: 16px; border-radius: 999px; background: #DFE6F3; overflow: hidden; }}
.prog > div {{ height: 100%; width: 0; background: {ACCENT}; border-radius: 999px; transition: width .1s linear; }}
.has-spec .ring {{ width: 170px; height: 170px; }} .has-spec .mic {{ width: 148px; height: 148px; }} .has-spec .mic svg {{ width: 68px; height: 68px; }}
.has-spec .t1 {{ margin-top: 4px; }}
.i-stop {{ display: none; }}
.recording .mic {{ background: #D9363E; }}
.recording .i-mic {{ display: none; }}
.recording .i-stop {{ display: block; }}
.recording .ring {{ animation: pulse 1.1s ease-in-out infinite; }}
@keyframes pulse {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(217,54,62,.35); }} 50% {{ box-shadow: 0 0 0 16px rgba(217,54,62,0); }} }}
.panel.sky {{ background: rgba(255,255,255,.84); border: 1.5px solid rgba(255,255,255,.95); border-radius: 28px; box-shadow: 0 14px 34px rgba(70,120,200,.13);
  min-height: 560px; }}
.sky .ring {{ background: radial-gradient(circle, rgba(47,111,228,.20) 0%, rgba(47,111,228,.08) 68%, rgba(47,111,228,0) 100%); width: 250px; height: 250px;
  box-shadow: 0 0 46px rgba(47,111,228,.32); }}
.sky .mic {{ width: 190px; height: 190px; background: radial-gradient(circle at 35% 28%, #78AEF7 0%, {ACCENT} 62%); box-shadow: inset 0 -8px 0 rgba(0,0,0,.14), 0 10px 26px rgba(47,111,228,.4); }}
.sky.recording .mic {{ background: radial-gradient(circle at 35% 28%, #F07880 0%, #D9363E 62%); }}
.sky .t1 {{ margin-top: 6px; }}
.guide {{ display: none; align-items: center; gap: 12px; margin-top: 6px; }}
.guided .guide {{ display: flex; }}
.g {{ font-size: 30px; font-weight: 900; padding: 6px 24px; border-radius: 999px; background: #EEF2FA; color: #6B7896; border: 3px solid transparent; }}
.g.on {{ background: #DCE6FB; color: #1B2440; border-color: {ACCENT}; }}
.g.ok {{ background: #E3F6EA; color: #14793F; border-color: #1FA45B; }}
.g.ok::after {{ content: " \\2713"; }}
.arrow {{ font-size: 26px; color: #6B7896; }}
.ch .guide, .ch .arrow {{ display: none !important; }}
.ch .g {{ width: 104px; height: 104px; padding: 0; border-radius: 50%; display: grid; place-items: center; font-size: 40px; }}
.ch .g.on {{ background: #EEF2FA; color: #1B2440; border-color: {ACCENT}; }}
.ch .g.lamp-green {{ background: #3E8E3A; color: #fff; border-color: #2F6B2C; box-shadow: inset 0 -6px 0 rgba(0,0,0,.18), 0 0 18px rgba(62,142,58,.5); }}
.ch .g.lamp-yellow {{ background: #E0A100; color: #fff; border-color: #B88200; box-shadow: inset 0 -6px 0 rgba(0,0,0,.18); }}
.ch .g.lamp-red {{ background: #D9363E; color: #fff; border-color: #B02A31; box-shadow: inset 0 -6px 0 rgba(0,0,0,.18); }}
.ch .g.ok::after {{ content: ""; }}
.gs {{ display: none; min-height: 30px; font-size: 22px; font-weight: 800; text-align: center; }}
.guided .gs {{ display: block; }}
.gs .zh {{ font-weight: 600; font-size: 17px; color: #3A4664; }}
.t1 {{ font-size: 34px; font-weight: 900; margin-top: 18px; }}
.t2 {{ font-family: 'Noto Sans TC', sans-serif; font-size: 22px; color: #3A4664; }}
.t3 {{ font-size: 15px; color: #3A4664; text-align: center; }}
.t3 span {{ font-family: 'Noto Sans TC', sans-serif; }}
kbd {{ font-family: inherit; font-size: 12px; font-weight: 800; border: 1.5px solid #3A4664; border-radius: 6px; padding: 1px 6px; }}
"""

_JS = """
export default function (component) {
  const { parentElement, data, setTriggerValue } = component;
  const panel = parentElement.querySelector(".panel"), btn = parentElement.querySelector(".mic");
  const state = (window.__lnMic = window.__lnMic || {});
  state.run = null;                      // set below; the Space handler always calls the latest one
  if (data.theme) panel.classList.add(data.theme);

  const toWav = (buf) => {
    const ch = buf.getChannelData(0), rate = buf.sampleRate;
    const out = new DataView(new ArrayBuffer(44 + ch.length * 2));
    const str = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
    str(0, "RIFF"); out.setUint32(4, 36 + ch.length * 2, true); str(8, "WAVEfmt ");
    out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 1, true);
    out.setUint32(24, rate, true); out.setUint32(28, rate * 2, true); out.setUint16(32, 2, true); out.setUint16(34, 16, true);
    str(36, "data"); out.setUint32(40, ch.length * 2, true);
    for (let i = 0; i < ch.length; i++) out.setInt16(44 + i * 2, Math.max(-1, Math.min(1, ch[i])) * 0x7fff, true);
    let bin = "";
    const bytes = new Uint8Array(out.buffer);
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  };

  // the sound as a live picture while the child speaks (only for sounds that have a target zone, see learner/spectro.py):
  // height = pitch of the hiss (high at the top), left to right = time, darker blue = more energy, the bands are the scoring zones
  const z = data.zones, spec = parentElement.querySelector(".spec"), sctx = (z || data.levels) ? spec.getContext("2d") : null;
  const yOf = (f) => spec.height * (1 - (Math.min(Math.max(f, z.f_lo), z.f_hi) - z.f_lo) / (z.f_hi - z.f_lo));
  const drawBands = () => {
    const W = spec.width, H = spec.height, cols = z.target === "s" ? ["#BFE3C9", "#FFF1B8", "#FFD3D8"] : ["#FFD3D8", "#FFF1B8", "#BFE3C9"];
    const ys = [0, yOf(z.hi), yOf(z.lo), H];
    cols.forEach((c, i) => { sctx.fillStyle = c; sctx.fillRect(0, ys[i], W, ys[i + 1] - ys[i]); });
    sctx.fillStyle = "#1B2440"; sctx.font = "800 40px Nunito, sans-serif"; sctx.textAlign = "right";
    sctx.fillText("s", W - 14, 44); sctx.fillText("sh", W - 14, H - 16);
  };
  const mode = data.live || "spectrogram";               // "spectrogram" (the scrolling picture), "dot" (one dot to keep in the green) or "off"
  const meter = !!data.levels && mode === "meter";       // /f/: a level meter (see learner/spectro.py: meter_levels)
  const live = (z && mode !== "off") || meter;
  const L = data.levels;
  const lvlLo = meter ? L.ref - 50 : 0, lvlHi = meter ? L.ref + 6 : 1;
  const lvlY = (db) => spec.height * (1 - (Math.min(Math.max(db, lvlLo), lvlHi) - lvlLo) / (lvlHi - lvlLo));
  const meterBands = () => {                                  // the bands of the /f/ meter, top (too strong) to bottom (too soft)
    const W = spec.width;
    [[lvlHi, L.yellow_hi, "#FFD3D8"], [L.yellow_hi, L.green_hi, "#FFF1B8"], [L.green_hi, L.green_lo, "#BFE3C9"], [L.green_lo, lvlLo, "#E3E8F2"]]
      .forEach(([a, b, c]) => { sctx.fillStyle = c; sctx.fillRect(0, lvlY(a), W, lvlY(b) - lvlY(a)); });
    sctx.fillStyle = "#1B2440"; sctx.font = "800 28px Nunito, sans-serif"; sctx.textAlign = "right";
    sctx.fillText("too strong 太強", W - 14, 36); sctx.fillText("too soft 太輕", W - 14, spec.height - 14);
  };
  if (meter) {
    panel.classList.add("has-spec"); meterBands();
    if (data.hint) parentElement.querySelector(".t3").textContent = data.hint;
  }
  if (live && !meter) {
    panel.classList.add("has-spec"); drawBands();
    if ((mode === "dot" || mode === "game") && data.hint) parentElement.querySelector(".t3").textContent = data.hint;
    if (mode === "game") parentElement.querySelector(".prog").style.display = "block";
  }

  // "game": the green zone is the thing to light up. The sound is drawn as bars (one per pitch row, as long as it is strong): bars in the
  // green zone are green, in the yellow zone yellow, in the red zone red. The meter below fills while most of the sound is in the green.
  const startGame = (stream) => {
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 2048; an.smoothingTimeConstant = 0.5;
    actx.createMediaStreamSource(stream).connect(an);
    const bins = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize;
    const W = spec.width, H = spec.height, rows = 40, goal = data.goal || 1.0, bar = parentElement.querySelector(".prog > div");
    const kind = (f) => {                                        // "good" in the target zone, "mid" in the yellow, "bad" in the far zone
      const hi = f >= z.hi, lo = f < z.lo, towardsS = z.target === "s";
      return (hi ? towardsS : lo && !towardsS) ? "good" : (hi || lo) ? "bad" : "mid";
    };
    const COL = { good: "#1FA45B", mid: "#F2B705", bad: "#D9363E" };
    let raf = 0, last = performance.now(), filled = 0, peakSeen = -90;
    bar.style.width = "0%"; bar.style.background = "#2F6FE4";
    const tick = (now) => {
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      an.getFloatFrequencyData(bins);
      const lin = [];
      let total = 0, inGood = 0, peak = -200;
      for (let r = 0; r < rows; r++) {
        const f1 = z.f_hi - (z.f_hi - z.f_lo) * r / rows, f0 = z.f_hi - (z.f_hi - z.f_lo) * (r + 1) / rows, fc = (f0 + f1) / 2;
        let m = -200;
        for (let b = Math.floor(f0 / hz); b <= Math.min(bins.length - 1, Math.ceil(f1 / hz)); b++) m = Math.max(m, bins[b]);
        peak = Math.max(peak, m);
        const a = Math.pow(10, m / 20);
        lin.push({ a, fc });
        total += a; if (kind(fc) === "good") inGood += a;
      }
      const heard = peak > -75;                                  // something clearly being said, not just the room
      if (heard) peakSeen = Math.max(peakSeen, peak);
      drawBands();
      sctx.globalAlpha = 0.9;
      if (heard) lin.forEach((p, r) => {
        const len = Math.min(1, p.a / Math.pow(10, peakSeen / 20)) * (W - 40);
        sctx.fillStyle = COL[kind(p.fc)];
        sctx.fillRect(0, r * H / rows + 1, len, H / rows - 2);
      });
      sctx.globalAlpha = 1;
      if (heard && total > 0 && inGood / total >= 0.6) filled = Math.min(1, filled + dt / goal);
      bar.style.width = `${(filled * 100).toFixed(0)}%`;
      bar.style.background = filled >= 1 ? "#1FA45B" : "#2F6FE4";
      if (filled >= 1) { sctx.font = "120px sans-serif"; sctx.textAlign = "center"; sctx.fillText("🎉", W / 2, H / 2 + 40); }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); actx.close(); };
  };

  // one dot at the height of the sound now (the centre of gravity of the hiss), green / yellow / red as the band it is in, with a short tail
  const startDot = (stream) => {
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 2048; an.smoothingTimeConstant = 0.5;
    actx.createMediaStreamSource(stream).connect(an);
    const bins = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize;
    const W = spec.width, X = W * 0.5, STEP = 9, tail = [];
    const zoneColour = (f) => {
      const hi = f >= z.hi, lo = f < z.lo, towardsS = z.target === "s";
      return (hi ? towardsS : lo && !towardsS) ? "#1FA45B" : (hi || lo) ? "#D9363E" : "#F2B705";
    };
    let raf = 0, f = null;
    const tick = () => {
      an.getFloatFrequencyData(bins);
      let sw = 0, s = 0, peak = -200;
      for (let b = Math.ceil(z.f_lo / hz); b <= Math.min(bins.length - 1, Math.floor(z.f_hi / hz)); b++) {
        peak = Math.max(peak, bins[b]);
        const m = Math.pow(10, bins[b] / 10); sw += m; s += m * b * hz;           // the power of the spectrum (not its magnitude): it keeps /s/ and /ʃ/ apart better (METHOD_NOTES 8c.al)
      }
      const heard = peak > -85 && sw > 0;                 // something is being said (not just the room)
      if (heard) { const c = s / sw; f = f === null ? c : f * 0.6 + c * 0.4; } else { f = null; }
      tail.unshift(f === null ? null : { y: yOf(f), c: zoneColour(f) });
      window.__lnDot = { t: performance.now(), f, color: f === null ? null : (tail[0].c === "#1FA45B" ? "green" : tail[0].c === "#D9363E" ? "red" : "yellow") };   // what the dot shows now: the guide of "see" and "she" reads it, so that the box and the dot never disagree
      if (tail.length > 24) tail.pop();
      drawBands();
      tail.forEach((p, i) => {
        if (!p) return;
        sctx.globalAlpha = Math.max(0.05, 0.5 - i * 0.02);
        sctx.fillStyle = p.c; sctx.beginPath(); sctx.arc(X - i * STEP, p.y, i === 0 ? 0 : 14 - i * 0.3, 0, 7); sctx.fill();
      });
      sctx.globalAlpha = 1;
      if (tail[0]) {                                      // the dot itself
        sctx.fillStyle = "#fff"; sctx.beginPath(); sctx.arc(X, tail[0].y, 30, 0, 7); sctx.fill();
        sctx.fillStyle = tail[0].c; sctx.beginPath(); sctx.arc(X, tail[0].y, 23, 0, 7); sctx.fill();
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); actx.close(); window.__lnDot = null; };
  };

  // /f/ meter: how strong the air is now, against the child's own vowel level. Green = soft but with friction, the way /f/ is said
  const startMeter = (stream) => {
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 2048;
    actx.createMediaStreamSource(stream).connect(an);
    const buf = new Float32Array(an.fftSize), W = spec.width, H = spec.height, lo = lvlLo, y = lvlY;
    const zoneOf = (db) => db > L.yellow_hi ? "#D9363E" : db > L.green_hi ? "#F2B705" : db > L.green_lo ? "#1FA45B" : "#9AA6BD";
    let raf = 0, db = lo;
    const tick = () => {
      an.getFloatTimeDomainData(buf);
      let s = 0; for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i];
      const now = 20 * Math.log10(Math.sqrt(s / buf.length) + 1e-7);
      db = db * 0.6 + Math.max(lo, now) * 0.4;
      meterBands();
      const top = y(db), bw = 120, x0 = (W - bw) / 2;
      sctx.fillStyle = "#fff"; sctx.fillRect(x0 - 5, top - 5, bw + 10, H - top + 5);
      sctx.fillStyle = zoneOf(db); sctx.fillRect(x0, top, bw, H - top);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); actx.close(); };
  };

  // The testing log (learner/camlog.py), fine version: one row per screen frame (about 60 a second, a 1024-sample window) of the level and the energy in 8 bands up to 9 kHz,
  // to see what tells /tʃ/ from /ʃ/ and /t/: the silence before, the rise time, the length of the hiss and its pitch (centre of gravity). Numbers only, no sound.
  const FINE_EDGES = [[100, 300], [300, 600], [600, 1000], [1000, 1500], [1500, 2500], [2500, 4000], [4000, 6000], [6000, 9000]];
  const startFineLog = (stream) => {
    if (!data.logUrl) return () => {};
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 1024; an.smoothingTimeConstant = 0;
    actx.createMediaStreamSource(stream).connect(an);
    const td = new Float32Array(an.fftSize), fd = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize, rows = [], t0 = performance.now();
    const band = (a, b) => { let s = 0; for (let i = Math.ceil(a / hz); i <= Math.min(fd.length - 1, Math.floor(b / hz)); i++) s += Math.pow(10, fd[i] / 10); return s + 1e-20; };
    let raf = 0;
    const tick = () => {
      an.getFloatTimeDomainData(td); an.getFloatFrequencyData(fd);
      let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i];
      if (rows.length < 3000) rows.push([Math.round(performance.timeOrigin + performance.now()), +(10 * Math.log10(s / td.length + 1e-12)).toFixed(1), ...FINE_EDGES.map(([a, b]) => +(10 * Math.log10(band(a, b))).toFixed(0))]);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf); actx.close();
      if (rows.length) fetch(data.logUrl, { method: "POST", mode: "no-cors", body: JSON.stringify({ src: "mic-fine", word: data.word, tap: Math.round(performance.timeOrigin + t0), rate: Math.round(actx.sampleRate), edges: FINE_EDGES, rows }) }).catch(() => {});
    };
  };

  const startLive = (stream) => {
    if (!live) return () => {};
    if (meter) return startMeter(stream);
    if (mode === "dot") return startDot(stream);
    if (mode === "game") return startGame(stream);
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 2048; an.smoothingTimeConstant = 0.2;
    actx.createMediaStreamSource(stream).connect(an);
    const bins = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize, t0 = performance.now();
    const H = spec.height, rows = 60, colW = Math.max(4, spec.width / (data.seconds * 30));
    drawBands();
    let raf = 0, peak = -90;                      // peak: the loudest bin so far, so the shades do not depend on how loud the child is
    const tick = () => {
      const x = Math.min(spec.width - colW, (performance.now() - t0) / 1000 / data.seconds * spec.width);
      an.getFloatFrequencyData(bins);
      const lv = [];
      for (let r = 0; r < rows; r++) {
        const f0 = z.f_hi - (z.f_hi - z.f_lo) * r / rows, f1 = z.f_hi - (z.f_hi - z.f_lo) * (r + 1) / rows;
        let m = -200;
        for (let b = Math.floor(f1 / hz); b <= Math.min(bins.length - 1, Math.ceil(f0 / hz)); b++) m = Math.max(m, bins[b]);
        lv.push(m); peak = Math.max(peak, m);
      }
      lv.forEach((m, r) => {
        const rel = m - peak, a = m < -85 ? 0 : rel > -9 ? 0.95 : rel > -18 ? 0.65 : rel > -27 ? 0.35 : 0;     // three shades of one blue
        if (a) { sctx.fillStyle = `rgba(47,111,228,${a})`; sctx.fillRect(x, r * H / rows, colW + 1, H / rows + 1); }
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); actx.close(); };
  };

  // guided recording ("me" = mmm, then ee): the recorder knows what is to be said, follows the child's own voice, lights the sound that is
  // being said and stops by itself a moment after the child has finished, not after a fixed time. /m/ is a hum with little energy above 2 kHz;
  // /iː/ has a high F2, so the energy at 2-3.5 kHz against the energy at 0.1-1 kHz tells them apart (a first guess, see lipcam.py for the same idea)
  const guided = !!data.guide, gStep = [parentElement.querySelector(".g1"), parentElement.querySelector(".g2")], gStatus = parentElement.querySelector(".gs");
  const t3Idle = parentElement.querySelector(".t3").innerHTML;
  if (guided) { panel.classList.add("guided"); gStep[0].classList.add("on"); gStep[0].textContent = data.guide.first || "mmm"; if (data.guide.second) gStep[1].textContent = data.guide.second; if (data.guide.kind === "ch" || data.guide.kind === "fric") panel.classList.add("ch"); }
  const say = (en, zh, colour) => { gStatus.innerHTML = en ? `<span style="color:${colour || "#1B2440"}">${en}</span> <span class="zh">${zh}</span>` : ""; };
  let guideSummary = null;               // what the live guide of a held hiss ("see", "she") found: the child sees it, so the result is made from it (learner/result.py: from_live)
  let guideNoise = null;                 // the room level (dBFS) the guided recorder measured, sent with the WAV so the quality check does not take the voice for the room
  const startGuide = (stream, finish) => {
    const actx = new AudioContext(), an = actx.createAnalyser();
    an.fftSize = 2048; an.smoothingTimeConstant = 0;
    actx.createMediaStreamSource(stream).connect(an);
    const td = new Float32Array(an.fftSize), fd = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize;
    const band = (a, b) => { let s = 0; for (let i = Math.ceil(a / hz); i <= Math.min(fd.length - 1, Math.floor(b / hz)); i++) s += Math.pow(10, fd[i] / 10); return s + 1e-20; };
    const lagLo = Math.floor(actx.sampleRate / 500), lagHi = Math.ceil(actx.sampleRate / 80);
    const periodicity = (x) => {                                  // does the frame repeat itself at a pitch of 80-500 Hz? a voice does, room noise and rumble do not
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
    const BANDS = [[100, 300], [300, 600], [600, 1000], [1000, 1500], [1500, 2000], [2000, 3000], [3000, 4500]];     // energy per band (dB) in the log: to find what tells the hum from a vowel
    let per = 0, recAt = 0, reason = "tap";
    const frames = [];
    const flush = () => {
      if (!data.guide.logUrl || !frames.length) return;
      const body = JSON.stringify({ src: "mic", word: data.guide.word, tap: Math.round(performance.timeOrigin + t0), reason, gate: data.guide.gateDb, periodic: data.guide.periodic,
        jump: data.guide.jumpDb, louder: data.guide.louderDb, fJump: data.guide.fJumpDb, humHi, humDb, humF, frames });
      frames.length = 0; fetch(data.guide.logUrl, { method: "POST", mode: "no-cors", body }).catch(() => {});
    };
    const t0 = performance.now(); let last = t0, raf = 0, lastVoice = 0, voiced = 0, mT = 0, eeT = 0, hiRel = -60, humHi = null, humDb = null, noiseEst = null, hiInit = false, gateNow = data.guide.gateDb, fSm = 0, fInit = false, humF = null, eeDoneAt = null, armed = true, quietAt = null, measuring = true, measureStart = t0, roomFrames = [], roomTooLoud = false;
    gStep.forEach((el) => el.classList.remove("ok", "on")); gStep[0].classList.add("on"); say("Wait, stay quiet", "請稍等，先不要出聲", "#2F6FE4");
    const tick = (now) => {
      const dt = now - last; last = now;
      an.getFloatTimeDomainData(td); an.getFloatFrequencyData(fd);
      let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i];
      const db = 10 * Math.log10(s / td.length + 1e-12);
      // ONE threshold, measured first: for the first measureS seconds after the tap the room is listened to (the child waits, quiet); its level plus a margin is then the gate.
      // If the room is louder than roomMaxDb (the child is already humming, or the room is noisy) the window starts again; nothing counts as a hum until the room is known.
      if (measuring) {
        if (db > -100) roomFrames.push(db);
        if (now - measureStart >= data.guide.measureS * 1000) {
          const sorted = roomFrames.slice().sort((a, b) => a - b), room = sorted.length >= 3 ? sorted[Math.floor(sorted.length / 2)] : null;
          if (room === null) { measureStart = now; roomFrames = []; }                           // the microphone has not delivered yet
          else if (room > data.guide.roomMaxDb) { measureStart = now; roomFrames = []; roomTooLoud = true; }
          else { gateNow = Math.min(data.guide.gateMaxDb, Math.max(data.guide.quietDb, room + data.guide.noiseMarginDb)); guideNoise = room; measuring = false; roomTooLoud = false; }
        }
      }
      const loud0 = !measuring && db > gateNow;
      per = loud0 ? periodicity(td) : 0;
      const loud = loud0 && per > data.guide.periodic;                  // a voice, not just noise above the gate
      if (loud) {
        lastVoice = now; voiced += dt;
        const hr = 10 * Math.log10(band(2000, 3500) / band(100, 1000));
        hiRel = hiInit ? 0.7 * hiRel + 0.3 * hr : hr; hiInit = true;
        // 300-600 Hz against 1-1.5 kHz: a nasal hum with the lips shut keeps more at 1 kHz, an open vowel more at 300-600 Hz (the first log: -4 to +2 dB in the hum, +8 to +14 dB in the vowel)
        const fr = 10 * Math.log10(band(300, 600) / band(1000, 1500));
        fSm = fInit ? 0.5 * fSm + 0.5 * fr : fr; fInit = true;
        if (!armed) { /* wait for the quiet moment first */ }
        else if (mT < data.guide.stepS * 1000) {                          // the hum: its level and its ratios are the child's own baseline (any voice counts, whatever its ratio)
          mT += dt; humHi = humHi === null ? hiRel : 0.9 * humHi + 0.1 * hiRel; humDb = humDb === null ? db : 0.9 * humDb + 0.1 * db; humF = humF === null ? fSm : 0.9 * humF + 0.1 * fSm;
        } else if (hiRel >= humHi + data.guide.jumpDb || db >= humDb + data.guide.louderDb || fSm >= humF + data.guide.fJumpDb) eeT += dt;   // any vowel: not like the hum
        else eeT = Math.max(0, eeT - 2 * dt);                             // a vowel has to last: a single frame that looks like one does not stay counted
      }
      const mOk = mT >= data.guide.stepS * 1000, eeOk = eeT >= data.guide.stepS * 1000;
      gStep[0].classList.toggle("ok", mOk); gStep[0].classList.toggle("on", !mOk);
      gStep[1].classList.toggle("ok", eeOk); gStep[1].classList.toggle("on", mOk && !eeOk);
      if (eeOk) say("Well done", "做得好", "#1FA45B");
      else if (mOk) say("Now smile", "接著微笑", "#2F6FE4");
      else if (measuring) say(roomTooLoud ? "Please be quiet for a moment" : "Wait, stay quiet", roomTooLoud ? "請先安靜一下" : "請稍等，先不要出聲", roomTooLoud ? "#C2410C" : "#2F6FE4");
      else if (loud) say("Keep humming  " + data.guide.first, "繼續哼「嗯」", "#1FA45B");
      else say("Now hum  " + data.guide.first, "現在哼「嗯」", "#2F6FE4");
      parentElement.querySelector(".t3").textContent = `${db.toFixed(0)} dB (gate ${gateNow.toFixed(0)}) · voice ${per.toFixed(2)} (needs ${data.guide.periodic}) · high/low ${hiRel.toFixed(0)} dB (hum ${humHi === null ? "?" : humHi.toFixed(0)}, vowel ≥ hum+${data.guide.jumpDb} dB) · 0.3-0.6k vs 1-1.5k ${fSm.toFixed(0)} dB (hum ${humF === null ? "?" : humF.toFixed(0)}, vowel ≥ hum+${data.guide.fJumpDb}) · or louder ≥ +${data.guide.louderDb} dB`;
      if (now - recAt >= 100 && frames.length < 6000) {                 // the numbers for the testing log (learner/camlog.py), ten a second
        recAt = now; frames.push({ t: Math.round(performance.timeOrigin + now), db: +db.toFixed(1), per: +per.toFixed(2), hi: +hiRel.toFixed(1), f: +fSm.toFixed(1), loud: loud ? 1 : 0, meas: measuring ? 1 : 0, m: Math.round(mT), ee: Math.round(eeT), gate: +gateNow.toFixed(1),
          bands: BANDS.map(([a, b]) => +(10 * Math.log10(band(a, b))).toFixed(0)) });
      }
      const endSilence = voiced > 600 && now - lastVoice > data.guide.endSilenceS * 1000, tooLong = now - t0 > data.guide.maxS * 1000, nothing = voiced === 0 && now - t0 > data.guide.waitS * 1000;
      if (eeOk && eeDoneAt === null) eeDoneAt = now;
      const allDone = eeDoneAt !== null && now - eeDoneAt > data.guide.afterVowelS * 1000;       // both sounds heard: no need to go on (a 12 s recording of one long note, as in the log of 18:48)
      if (endSilence || tooLong || nothing || allDone) { reason = allDone ? "done" : endSilence ? "silence" : tooLong ? "max" : "nosound"; finish(); return; }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); actx.close(); flush(); };
  };

  // /tʃ/ ("cheat"), live: two lamps, "t" (does the hiss burst in?) and "sh" (does it last?). The band of 2.5-7.9 kHz is measured every millisecond in an AudioWorklet
  // (a 5 ms envelope, as learner/affricate_check.py does after the recording). After the room has been listened to, the first strong stretch of hiss is followed as it happens:
  // the steepest climb since its start gives the "t" lamp, its length so far gives the "sh" lamp (it turns green the moment it has lasted long enough).
  const WORKLET = `
    class BandEnv extends AudioWorkletProcessor {
      constructor() {
        super();
        const sr = sampleRate, bq = (type, f, q) => {
          const w = 2 * Math.PI * Math.min(f, sr * 0.45) / sr, al = Math.sin(w) / (2 * q), c = Math.cos(w);
          const b = type === "hp" ? [(1 + c) / 2, -(1 + c), (1 + c) / 2] : [(1 - c) / 2, 1 - c, (1 - c) / 2], a0 = 1 + al;
          return { b0: b[0] / a0, b1: b[1] / a0, b2: b[2] / a0, a1: -2 * c / a0, a2: (1 - al) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
        };
        this.f = [bq("hp", 2500, 0.707), bq("hp", 2500, 0.707), bq("lp", 7900, 0.707), bq("lp", 7900, 0.707)];
        this.win = Math.round(sr * 0.005); this.hop = Math.round(sr * 0.001);
        this.bufHi = new Float64Array(this.win); this.bufFull = new Float64Array(this.win); this.k = 0; this.n = 0; this.sumHi = 0; this.sumFull = 0;
      }
      process(inputs) {
        const x = inputs[0] && inputs[0][0];
        if (!x) return true;
        const out = [];
        for (let i = 0; i < x.length; i++) {
          let v = x[i];
          for (const f of this.f) { const y = f.b0 * v + f.b1 * f.x1 + f.b2 * f.x2 - f.a1 * f.y1 - f.a2 * f.y2; f.x2 = f.x1; f.x1 = v; f.y2 = f.y1; f.y1 = y; v = y; }
          const hi = v * v, full = x[i] * x[i];
          this.sumHi += hi - this.bufHi[this.k]; this.bufHi[this.k] = hi; this.sumFull += full - this.bufFull[this.k]; this.bufFull[this.k] = full;
          this.k = (this.k + 1) % this.win; this.n++;
          if (this.n % this.hop === 0) out.push(10 * Math.log10(Math.max(this.sumHi, 0) / this.win + 1e-12), 10 * Math.log10(Math.max(this.sumFull, 0) / this.win + 1e-12));
        }
        if (out.length) this.port.postMessage(out);
        return true;
      }
    }
    registerProcessor("band-env", BandEnv);`;
  const trainState = () => ({ camSpreadMs: 0, camNoSpreadMs: 0, pop: null, popAt: 0, hissEndAt: null, voiceAt: null, voiceMs: 0, lastVoiceAt: 0, broken: false, progress: 0, win: false, gap: null, puffs: [] });
  const cctx = data.guide && data.guide.kind === "ch" ? spec.getContext("2d") : null;
  const drawTrain = (S, now) => {
    const c = cctx, W = spec.width, H = spec.height;
    c.clearRect(0, 0, W, H);
    c.fillStyle = "#E4EEFF"; c.fillRect(0, 0, W, H);
    c.fillStyle = "#CDE8C0"; c.fillRect(0, 292, W, H - 292);                                 // the ground
    const railY = 330;
    c.strokeStyle = "#8A96B0"; c.lineWidth = 6; c.lineCap = "round";
    const gapX = [150, 215];
    c.beginPath(); c.moveTo(20, railY); c.lineTo(S.broken ? gapX[0] : W - 20, railY); c.stroke();
    if (S.broken) { c.beginPath(); c.moveTo(gapX[1], railY); c.lineTo(W - 20, railY); c.stroke(); c.strokeStyle = "#D9363E"; c.lineWidth = 6; c.beginPath(); c.moveTo(168, railY - 14); c.lineTo(198, railY + 14); c.moveTo(198, railY - 14); c.lineTo(168, railY + 14); c.stroke(); }
    c.strokeStyle = "#B6C0D4"; c.lineWidth = 3; for (let x = 36; x < W - 20; x += 34) { if (S.broken && x > gapX[0] - 6 && x < gapX[1] + 6) continue; c.beginPath(); c.moveTo(x, railY + 8); c.lineTo(x, railY + 22); c.stroke(); }
    // the station (the smoke comes from its chimney)
    c.fillStyle = "#F2A65A"; c.fillRect(34, 236, 84, 56); c.fillStyle = "#C2410C"; c.beginPath(); c.moveTo(26, 238); c.lineTo(76, 200); c.lineTo(126, 238); c.fill();
    c.fillStyle = "#8A5A3C"; c.fillRect(96, 186, 16, 36);
    const chim = { x: 104, y: 180 };
    // the flag at the end of the track
    c.strokeStyle = "#5B6B8C"; c.lineWidth = 5; c.beginPath(); c.moveTo(W - 56, railY - 6); c.lineTo(W - 56, 232); c.stroke();
    c.fillStyle = S.win ? "#1FA45B" : "#B6C0D4"; c.beginPath(); const wv = S.win ? 6 * Math.sin(now / 120) : 0; c.moveTo(W - 56, 232); c.lineTo(W - 12, 246 + wv); c.lineTo(W - 56, 262); c.fill();
    // the train: on the rail, runs to the flag while the voice goes on
    const tx = 150 + S.progress * (W - 330);
    c.fillStyle = "#2F6FE4"; c.fillRect(tx, 270, 74, 44); c.fillRect(tx + 40, 250, 34, 22); c.fillStyle = "#1B2440"; c.fillRect(tx + 6, 250, 14, 22);
    c.fillStyle = "#6B94EA"; c.fillRect(tx + 80, 280, 56, 34); c.fillStyle = "#1B2440"; c.fillRect(tx + 74, 296, 8, 6);
    for (const wx of [tx + 14, tx + 52, tx + 96, tx + 124]) { c.beginPath(); c.arc(wx, 316, 9, 0, 7); c.fill(); }
    // the smoke
    for (const p of S.puffs) {
      const age = now - p.born; if (age < 0) continue;
      if (age > 2200) continue;
      c.globalAlpha = Math.max(0, 1 - age / 2200);
      if (p.ribbon) {                                                                    // a fade-in: one flat grey ribbon, not puffs
        c.strokeStyle = "#9AA6BD"; c.lineWidth = 14; c.lineCap = "round"; c.beginPath();
        for (let i = 0; i <= 40; i++) { const x = chim.x + i * 9, y = chim.y - 4 * Math.sin(i / 3 + age / 200); if (i === 0) c.moveTo(x, y); else c.lineTo(x, y); }
        c.stroke();
      } else {
        const px = chim.x + p.vx * age * 1.3, py = chim.y + p.vy * age * 1.6, r = p.r * (1 + age / 900);
        c.fillStyle = p.grey ? "#B7C0D3" : "#FFFFFF"; c.strokeStyle = "#B7C0D3"; c.lineWidth = 3;
        c.beginPath(); c.arc(px, py, r, 0, 7); c.fill(); c.stroke();
      }
      c.globalAlpha = 1;
    }
  };

  if (cctx) { panel.classList.add("has-spec"); drawTrain(trainState(), performance.now()); }                  // the scene is there before the first tap

  const startChGuide = (stream, finish) => {
    const G = data.guide, actx = new AudioContext(), t0 = performance.now();
    let node = null, closed = false, reason = "tap";
    let phase = "measure", ms = 0, hiRoom = [], fullRoom = [], roomHi = 0, roomFull = 0;
    let last3 = [-200, -200, -200], ev = null, quietMs = 0, sawEvent = false, done = false;
    // the voice after the hiss (the vowel), read with an analyser of its own: loudness and "does it repeat itself at a pitch" (as in startGuide)
    const an = actx.createAnalyser(); an.fftSize = 2048; an.smoothingTimeConstant = 0;
    actx.createMediaStreamSource(stream).connect(an);
    const td = new Float32Array(an.fftSize), lagLo = Math.floor(actx.sampleRate / 500), lagHi = Math.ceil(actx.sampleRate / 80);
    const periodicity = (x) => {
      let m = 0; for (let i = 0; i < x.length; i++) m += x[i]; m /= x.length;
      let r0 = 0; for (let i = 0; i < x.length; i++) r0 += (x[i] - m) * (x[i] - m);
      if (r0 < 1e-9) return 0;
      const n = x.length - lagHi; let best = 0;
      for (let lag = lagLo; lag <= lagHi; lag += 2) { let s = 0; for (let i = 0; i < n; i++) s += (x[i] - m) * (x[i + lag] - m); best = Math.max(best, s / (r0 * n / x.length)); }
      return best;
    };
    // what the scene shows: the smoke from the chimney (puffs when the hiss bursts in, a flat ribbon when it fades in), the train that runs while the voice goes on
    const S = trainState();
    const rows = [], median = (a) => { const s = a.slice().sort((p, q) => p - q); return s[Math.floor(s.length / 2)]; };
    const level = (v, ok, almost) => (v >= ok ? "green" : v >= almost ? "yellow" : "red");
    const flush = () => {
      if (!G.logUrl || !rows.length) return;
      const body = JSON.stringify({ src: "mic-ch", word: G.word, tap: Math.round(performance.timeOrigin + t0), reason, roomHi, roomFull,
        limits: [G.slopeOk, G.slopeAlmost, G.hissOk, G.hissAlmost, G.bridgeS], event: ev && { start: ev.start, slope: ev.slope, hiss: ev.hiss, peak: ev.peak, gap: S.gap, voice: Math.round(S.voiceMs), camSpread: Math.round(S.camSpreadMs), camNoSpread: Math.round(S.camNoSpreadMs) }, rows });
      rows.length = 0; fetch(G.logUrl, { method: "POST", mode: "no-cors", body }).catch(() => {});
    };
    const pct = (a, q) => { const s = a.slice().sort((p, r) => p - r); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; };
    let blkHi = [], blkFull = [];
    const trackRoom = (hi, full) => {                                      // every 200 ms: if the quiet of the last 200 ms is lower than the room taken so far, the room is lower (never higher)
      blkHi.push(hi); blkFull.push(full);
      if (blkHi.length >= 200) {
        const mh = pct(blkHi, 0.5), mf = pct(blkFull, 0.5);
        if (mh < roomHi - 3) roomHi = Math.max(-80, mh);
        if (mf < roomFull - 3) { roomFull = Math.max(-70, mf); guideNoise = roomFull; }
        blkHi = []; blkFull = [];
      }
    };
    const listenMs = (hi, full) => {
      if (!ev) {
        if (hi > roomHi + G.startDb) ev = { start: ms, hi: [last3[0], last3[1]], ended: false, slope: 0, hiss: 0, peak: hi, begin: 0 };
        else { if (sawEvent && full < roomFull + G.quietDb) quietMs++; else quietMs = 0; return; }
      }
      if (!ev.ended) {
        ev.hi.push(hi);
        const n = ev.hi.length, win = Math.min(n, 250);
        let pi = 0; for (let i = 1; i < win; i++) if (ev.hi[i] > ev.hi[pi]) pi = i;                    // the peak of the first 250 ms
        const peak = ev.hi[pi], thr = peak - 20;                                                   // 10 % of the peak amplitude
        let b = 0; while (b < pi && ev.hi[b] < thr) b++;
        let sl = 0; for (let i = Math.max(1, b - 1); i <= pi; i++) sl = Math.max(sl, ev.hi[i] - ev.hi[i - 1]);
        ev.peak = peak; ev.slope = sl; ev.begin = b; ev.hiss = n - b;
        if (n - 1 > pi && hi < peak - G.endDb) { ev.ended = true; ev.hiss = n - 1 - b; }
        if (ev.ended && peak < roomHi + G.minPeakDb) { ev = null; return; }                       // a click, not a hiss
        const real = peak >= roomHi + G.minPeakDb;
        sawEvent = sawEvent || real;
        if (real) {
          // the verdict on the start waits until the peak has held for 25 ms (a slow fade-in reaches its peak late: its early steps look steep against the peak so far)
          if ((n - 1 - pi >= G.popAfterMs || ev.ended) && S.pop === null) S.pop = level(ev.slope, G.slopeOk, G.slopeAlmost);
          if (S.pop && !S.popAt) S.popAt = performance.now();
          if (ev.ended && S.hissEndAt === null) { S.hissEndAt = performance.now(); S.hissLevel = level(ev.hiss, G.hissOk, G.hissAlmost); }
        }
      } else {
        if (full < roomFull + G.quietDb) quietMs++; else quietMs = 0;
        if ((quietMs > G.endQuietS * 1000 || (S.win && performance.now() - S.winAt > G.afterWinS * 1000)) && !done) { done = true; reason = S.win ? "done" : "silence"; finish(); }
      }
    
    };
    const onMs = (hi, full) => {
      ms++;
      if (rows.length < 6000 && ms % 4 === 0) rows.push([Math.round(performance.timeOrigin + performance.now()), +full.toFixed(1), +hi.toFixed(1)]);
      last3.shift(); last3.push(hi);
      if (phase === "measure") {                                           // listen to the room first: the one threshold of the turn (the quiet quarter of the window, so that a child who has already begun to speak does not raise it)
        hiRoom.push(hi); fullRoom.push(full);
        if (ms >= G.measureS * 1000) {
          {                                                                // no retry any more: a child who hisses from the tap (log of 01:46) is not asked to be quiet; the room is capped, and falls to the quietest 200 ms seen (trackRoom)
            roomHi = Math.max(-80, Math.min(-58, pct(hiRoom, 0.25)));      // capped: a window that is all hiss (-39 dB there) must not become "the room"; floored: a digitally silent microphone must not make every breath an event
            roomFull = Math.max(-70, Math.min(-40, pct(fullRoom, 0.25)));
            guideNoise = roomFull; phase = "listen"; say("Now say it", "現在說", "#2F6FE4");
            const h = hiRoom, f = fullRoom;                                // what was said while the room was being listened to is not lost: the window is played through the detector (log of 00:37, the "ch" began before "Now say it")
            for (let i = 0; i < h.length; i++) { last3 = [h[Math.max(0, i - 2)], h[Math.max(0, i - 1)], h[i]]; listenMs(h[i], f[i]); }
            hiRoom = []; fullRoom = [];
          }
        }
        return;
      }
      trackRoom(hi, full);
      listenMs(hi, full);
    };
    (async () => {
      try {
        await actx.audioWorklet.addModule(URL.createObjectURL(new Blob([WORKLET], { type: "application/javascript" })));
        if (closed) return;
        node = new AudioWorkletNode(actx, "band-env");
        node.port.onmessage = (e) => { const a = e.data; for (let i = 0; i + 1 < a.length; i += 2) onMs(a[i], a[i + 1]); };
        actx.createMediaStreamSource(stream).connect(node);
        if (actx.state === "suspended") await actx.resume();
      } catch (err) { say("", ""); setTimeout(() => { if (!done) { done = true; finish(); } }, 3000); }   // no worklet here: an ordinary recording of 3 s
    })();
    say("Wait, stay quiet", "請稍等，先不要出聲", "#2F6FE4");
    // ---- the picture, one frame per screen frame
    let raf = 0, lastT = performance.now();
    const frame = (now) => {
      const dt = now - lastT; lastT = now;
      if (ev && S.popAt && !S.puffed) {                                       // the smoke starts with the hiss: puffs for a burst, a ribbon for a fade-in
        S.puffed = true;
        if (S.pop === "red") S.puffs.push({ ribbon: true, born: now });
        else for (let k = 0; k < 3; k++) S.puffs.push({ x: 0, y: 0, vx: 0.03 + 0.02 * k, vy: -0.02 - 0.01 * k, r: (S.pop === "green" ? 26 : 16) + 6 * k, born: now + 90 * k, grey: S.pop !== "green" });
      }
      // the voice after the hiss: loudness and pitch-repeat, starting from the moment the hiss began
      an.getFloatTimeDomainData(td);
      let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i];
      const db = 10 * Math.log10(s / td.length + 1e-12);
      if (ev && phase === "listen" && !S.win) {
        const voice = db > Math.max(G.quietDb2, roomFull + G.voiceMarginDb) && periodicity(td) > G.periodic && now - S.popAt > G.voiceAfterMs;
        // with the lip mirror on (learner/lipcam.py publishes window.__lnLips), the train runs only while the lips are spread as well, as in "me"; no mirror or no face: the voice alone
        const lips = window.__lnLips, cam = !!(lips && lips.on && lips.face && now - lips.t < 600);
        if (voice && cam) { if (lips.spread) S.camSpreadMs += dt; else S.camNoSpreadMs += dt; }
        const voiced = voice && (!cam || lips.spread);
        if (voice && cam && !lips.spread) say(lips.gap >= G.smileGapMax ? "Make your mouth small" : "Smile wide", lips.gap >= G.smileGapMax ? "嘴巴小一點" : "笑開一點", "#C2410C");
        if (voiced) {
          if (S.voiceAt === null) { S.voiceAt = now; S.gap = S.hissEndAt === null ? 0 : Math.max(0, Math.round(now - S.hissEndAt)); }
          S.voiceMs += dt; S.lastVoiceAt = now;
        } else if (S.voiceAt !== null && now - S.lastVoiceAt > 250) S.voiceMs = Math.max(0, S.voiceMs - 2 * dt);          // a stop of more than a quarter second slows the train down again
        const late = S.hissEndAt !== null && (S.voiceAt === null ? now - S.hissEndAt : S.gap) > G.bridgeS * 1000;
        S.broken = late;                                                                   // the voice came too late: the rail is broken
        S.progress = S.broken ? 0 : Math.min(1, S.voiceMs / (G.holdVoiceS * 1000));
        if (S.progress >= 1 && !S.win) { S.win = true; S.winAt = now; say("Well done", "做得好", "#1FA45B"); }
      }
      window.__lnTrain = { on: true, t: now, listening: phase === "listen", pop: S.pop, hiss: S.hissLevel || null, hissEnded: S.hissEndAt !== null, popAt: S.popAt > 0, voiceAt: S.voiceAt !== null, progress: S.progress, win: S.win, broken: S.broken };   // read by the lip mirror (learner/lipcam.py) for its three boxes
      drawTrain(S, now);
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    const timer = setInterval(() => {
      const t = performance.now() - t0;
      if (!done && ((phase === "listen" && !sawEvent && t > G.waitS * 1000) || t > G.maxS * 1000)) { done = true; reason = sawEvent ? "max" : "nosound"; finish(); }
    }, 200);
    return () => { closed = true; clearInterval(timer); cancelAnimationFrame(raf); if (window.__lnTrain) window.__lnTrain.on = false; try { node && node.disconnect(); } catch (e) {} actx.close(); flush(); };
  };

  // /s/ and /ʃ/ with "ee" after them ("see", "she"), live. Steps as for "cheat" (the lip mirror shows them, learner/lipcam.py): get ready; hold the hiss in the right zone (the dot of the live view, see startDot,
  // is drawn at the same time); open into "ee". The room is listened to first (the quiet quarter of the first 0.6 s, as in startChGuide); a hiss is the 2.5-7.9 kHz band standing 12 dB over it; the part of it in the
  // target zone is counted from the centre of gravity of the frame (the same measure as the dot); "ee" is voice after the hiss, with the lips spread when the mirror is on.
  const startFricGuide = (stream, finish) => {
    const G = data.guide, actx = new AudioContext(), t0 = performance.now(), target = z.target;
    let node = null, closed = false, reason = "tap";
    let phase = "measure", ms = 0, hiRoom = [], fullRoom = [], roomHi = 0, roomFull = 0, done = false;
    let active = false, belowMs = 0, hissMs = 0, inZoneMs = 0, ended = false, sawHiss = false, quietMs = 0;
    const an = actx.createAnalyser(); an.fftSize = 2048; an.smoothingTimeConstant = 0.5;
    actx.createMediaStreamSource(stream).connect(an);
    const td = new Float32Array(an.fftSize), bins = new Float32Array(an.frequencyBinCount), hz = actx.sampleRate / an.fftSize;
    const lagLo = Math.floor(actx.sampleRate / 500), lagHi = Math.ceil(actx.sampleRate / 80);
    const periodicity = (x) => {
      let m = 0; for (let i = 0; i < x.length; i++) m += x[i]; m /= x.length;
      let r0 = 0; for (let i = 0; i < x.length; i++) r0 += (x[i] - m) * (x[i] - m);
      if (r0 < 1e-9) return 0;
      const n = x.length - lagHi; let best = 0;
      for (let lag = lagLo; lag <= lagHi; lag += 2) { let s = 0; for (let i = 0; i < n; i++) s += (x[i] - m) * (x[i + lag] - m); best = Math.max(best, s / (r0 * n / x.length)); }
      return best;
    };
    let cog = null, inZoneNow = false;                                       // the centre of gravity of the frame, as in startDot (null when nothing is heard in the band); inZoneNow: the dot is in the target zone or next to it
    const S = { voiceAt: null, voiceMs: 0, lastVoiceAt: 0, progress: 0, win: false, winAt: 0, gap: null, hissEndAt: null, camSpreadMs: 0, camNoSpreadMs: 0, zoneOk: null };
    const rows = [], pct = (a, q) => { const s = a.slice().sort((p, r) => p - r); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; };
    let blkHi = [], blkFull = [];
    const trackRoom = (hi, full) => {                                      // every 200 ms: if the quiet of the last 200 ms is lower than the room taken so far, the room is lower (never higher)
      blkHi.push(hi); blkFull.push(full);
      if (blkHi.length >= 200) {
        const mh = pct(blkHi, 0.5), mf = pct(blkFull, 0.5);
        if (mh < roomHi - 3) roomHi = Math.max(-80, mh);
        if (mf < roomFull - 3) { roomFull = Math.max(-70, mf); guideNoise = roomFull; }
        blkHi = []; blkFull = [];
      }
    };
    const flush = () => {
      if (!G.logUrl || !rows.length) return;
      const body = JSON.stringify({ src: "mic-fric", word: G.word, target, tap: Math.round(performance.timeOrigin + t0), reason, roomHi, roomFull,
        limits: [G.inZoneMs, G.minHissMs, G.bridgeS], event: { hiss: hissMs, inZone: inZoneMs, gap: S.gap, voice: Math.round(S.voiceMs), camSpread: Math.round(S.camSpreadMs), camNoSpread: Math.round(S.camNoSpreadMs) }, rows });
      rows.length = 0; fetch(G.logUrl, { method: "POST", mode: "no-cors", body }).catch(() => {});
    };
    const good = (f) => (target === "s" ? f >= z.hi : f < z.lo);
    const listenMs = (hi, full) => {
      if (!active && hi > roomHi + G.startDb) { active = true; belowMs = 0; }
      if (active && !ended) {
        if (hi > roomHi + G.endMarginDb) { belowMs = 0; hissMs++; if (inZoneNow) inZoneMs++; }
        else if (++belowMs > G.endHoldMs) {
          if (hissMs >= G.minHissMs) { ended = true; S.hissEndAt = performance.now(); sawHiss = true; }
          else { active = false; hissMs = 0; inZoneMs = 0; }                       // a blip, not a hiss
        }
        if (hissMs >= G.minHissMs) sawHiss = true;
      } else if (ended) { if (full < roomFull + G.quietDb) quietMs++; else quietMs = 0; }
    };
    const onMs = (hi, full) => {
      ms++;
      if (rows.length < 6000 && ms % 4 === 0) rows.push([Math.round(performance.timeOrigin + performance.now()), +full.toFixed(1), +hi.toFixed(1), cog === null ? null : Math.round(cog), window.__lnDot ? window.__lnDot.color : null]);      // the centre of gravity and the colour of the dot are logged too
      if (phase === "measure") {
        hiRoom.push(hi); fullRoom.push(full);
        if (ms >= G.measureS * 1000) {
          {                                                                // no retry any more (see the guide of "cheat")
            roomHi = Math.max(-80, Math.min(-58, pct(hiRoom, 0.25)));      // capped and floored as in the guide of "cheat"
            roomFull = Math.max(-70, Math.min(-40, pct(fullRoom, 0.25)));
            guideNoise = roomFull; phase = "listen"; say("Now say it", "現在說", "#2F6FE4");
            const h = hiRoom, f = fullRoom; hiRoom = []; fullRoom = [];
            for (let i = 0; i < h.length; i++) listenMs(h[i], f[i]);               // what was said while the room was listened to is not lost
          }
        }
        return;
      }
      trackRoom(hi, full);
      listenMs(hi, full);
    };
    (async () => {
      try {
        await actx.audioWorklet.addModule(URL.createObjectURL(new Blob([WORKLET], { type: "application/javascript" })));
        if (closed) return;
        node = new AudioWorkletNode(actx, "band-env");
        node.port.onmessage = (e) => { const a = e.data; for (let i = 0; i + 1 < a.length; i += 2) onMs(a[i], a[i + 1]); };
        actx.createMediaStreamSource(stream).connect(node);
        if (actx.state === "suspended") await actx.resume();
      } catch (err) { say("", ""); setTimeout(() => { if (!done) { done = true; finish(); } }, 3000); }
    })();
    say("Wait, stay quiet", "請稍等，先不要出聲", "#2F6FE4");
    let raf = 0, lastT = performance.now();
    const frame = (now) => {
      const dt = now - lastT; lastT = now;
      an.getFloatFrequencyData(bins);
      let sw = 0, sm = 0, peak = -200;
      for (let b = Math.ceil(z.f_lo / hz); b <= Math.min(bins.length - 1, Math.floor(z.f_hi / hz)); b++) { peak = Math.max(peak, bins[b]); const m = Math.pow(10, bins[b] / 10); sw += m; sm += m * b * hz; }
      cog = peak > -85 && sw > 0 ? sm / sw : null;
      const dot = window.__lnDot;                                              // the dot of the live view, when it is running: the box follows what the child sees (green = in the zone, yellow = next to it)
      inZoneNow = dot && now - dot.t < 300 ? (dot.color === "green" || dot.color === "yellow") : (cog !== null && good(cog));
      let zoneNow = null;
      if (phase === "listen" && (ended || inZoneMs >= G.inZoneMs) && !S.win) {  // "ee": voice after the hiss (or once the hiss has been held long enough: the vowel often begins before the hiss has died away, and waiting for its end was a delay), with the lips spread when the mirror is on
        an.getFloatTimeDomainData(td);
        let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i];
        const db = 10 * Math.log10(s / td.length + 1e-12);
        const voice = db > Math.max(G.quietDb2, roomFull + G.voiceMarginDb) && periodicity(td) > G.periodic;
        const lips = window.__lnLips, cam = !!(lips && lips.on && lips.face && now - lips.t < 600);
        if (voice && cam) { if (lips.spread) S.camSpreadMs += dt; else S.camNoSpreadMs += dt; }
        const voiced = voice && (!cam || lips.spread);
        if (voice && cam && !lips.spread) say(lips.gap >= G.smileGapMax ? "Make your mouth small" : "Smile wide", lips.gap >= G.smileGapMax ? "嘴巴小一點" : "笑開一點", "#C2410C");
        if (voiced) { if (S.voiceAt === null) { S.voiceAt = now; S.gap = S.hissEndAt === null ? 0 : Math.max(0, Math.round(now - S.hissEndAt)); } S.voiceMs += dt; S.lastVoiceAt = now; }
        else if (S.voiceAt !== null && now - S.lastVoiceAt > 250) S.voiceMs = Math.max(0, S.voiceMs - 2 * dt);
        const late = S.hissEndAt !== null && (S.voiceAt === null ? now - S.hissEndAt : S.gap) > G.bridgeS * 1000;
        S.progress = late ? 0 : Math.min(1, S.voiceMs / (G.holdVoiceS * 1000));
        if (S.progress >= 1) { S.win = true; S.winAt = now; say("Well done", "做得好", "#1FA45B"); }
      }
      // what the mirror's boxes show (the keys are those of the "cheat" train: learner/lipcam.py reads both the same way)
      const held = inZoneMs >= G.inZoneMs, zoneOk = held ? "green" : (ended ? "red" : null);      // the box lights as soon as the hiss has been held in the zone long enough, not only when it has ended (a child can hold "shhh" for seconds: log of 01:26)
      window.__lnTrain = { on: true, t: now, listening: phase === "listen", pop: "green", hiss: zoneOk, hissEnded: ended || held, popAt: hissMs > 0, voiceAt: S.voiceAt !== null, progress: S.progress, win: S.win, broken: false,
        inZone: inZoneMs, hissMs, need: G.inZoneMs };
      if (!done && ended && (quietMs > G.endQuietS * 1000 || (S.win && now - S.winAt > G.afterWinS * 1000))) { done = true; reason = S.win ? "done" : "silence"; finish(); }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    const timer = setInterval(() => {
      const t = performance.now() - t0;
      if (!done && ((phase === "listen" && !sawHiss && t > G.waitS * 1000) || t > G.maxS * 1000)) { done = true; reason = sawHiss ? "max" : "nosound"; finish(); }
    }, 200);
    return () => { closed = true; clearInterval(timer); cancelAnimationFrame(raf); try { node && node.disconnect(); } catch (e) {} actx.close(); if (window.__lnTrain) window.__lnTrain.on = false;
      guideSummary = { hiss: hissMs, inZone: inZoneMs, gap: S.gap, voice: Math.round(S.voiceMs), win: S.win, target }; flush(); };
  };

  let busy = false, stopNow = null;
  state.busy = () => busy;               // the lip mirror's "record and mirror together" button asks this
  const toggle = async () => {
    if (busy) { if (stopNow) stopNow(); return; }       // tapping again while recording stops it
    busy = true; panel.classList.add("recording");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      const rec = new MediaRecorder(stream), chunks = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      const stopped = new Promise((r) => (rec.onstop = r));
      rec.start();
      let stopLive = () => {};
      const stopLog = guided ? () => {} : startFineLog(stream);               // the fine numbers of this recording for the testing log (not for the guided "me"/"knee", which logs its own)
      await new Promise((r) => { stopNow = r; if (guided && data.guide.kind === "fric") { const a = startLive(stream), b = startFricGuide(stream, r); stopLive = () => { a(); b(); }; } else if (guided) stopLive = (data.guide.kind === "ch" ? startChGuide : startGuide)(stream, r); else { stopLive = startLive(stream); setTimeout(r, data.seconds * 1000); } });
      stopNow = null; stopLive(); stopLog(); rec.stop(); await stopped;
      stream.getTracks().forEach((t) => t.stop());
      const ctx = new AudioContext();
      const audio = await ctx.decodeAudioData(await new Blob(chunks).arrayBuffer());
      ctx.close();
      setTriggerValue("wav", (guided && guideNoise !== null ? `${guideNoise.toFixed(1)}|${guideSummary ? JSON.stringify(guideSummary) : ""}|` : "") + toWav(audio));      // the room level the recorder measured goes in front of the WAV
    } catch (err) { /* no microphone or permission refused: the button simply returns to its idle look */ }
    stopNow = null; busy = false; panel.classList.remove("recording"); if (guided) { say("", ""); parentElement.querySelector(".t3").innerHTML = t3Idle; }
  };
  btn.onclick = toggle;
  state.run = toggle;
  if (!state.bound) {                    // one Space handler for the page, whichever render created it
    state.bound = true;
    window.addEventListener("keydown", (e) => {
      const tag = (e.target && e.target.tagName || "").toLowerCase();
      if (e.code === "Space" && !e.repeat && !["input", "textarea", "select", "button"].includes(tag) && state.run) { e.preventDefault(); state.run(); }
    });
  }
}
"""

_component = components.component("learner_mic", html=_HTML, css=_CSS, js=_JS)


def mic(key: str, seconds: float = RECORD_SECONDS, zones: dict | None = None, live: str = "dot", hint: str = "", goal: float = 1.0,
        levels: dict | None = None, guide: dict | None = None, theme: str = "", log_url: str | None = None, word: str = "") -> bytes | None:
    """The record panel. Returns the latest recording (WAV bytes) made on this screen, or None.
    `zones` (learner/spectro.py: zones()) adds the live view with the target zone on it. `live` picks it: "dot" (one dot to keep in the green),
    "spectrogram" (the scrolling picture) or "off". `hint` replaces the small line under the button in the "dot" view."""
    result = _component(key=key, data={"seconds": seconds, "zones": zones, "live": live, "hint": hint, "goal": goal, "levels": levels, "guide": guide, "theme": theme, "logUrl": log_url, "word": word}, on_wav_change=lambda: None)
    wav = getattr(result, "wav", None)
    store = f"{key}_wav"
    if wav:
        room, _, payload = wav[:16].partition("|") if "|" in wav[:16] else ("", "", wav)
        st.session_state.pop(f"{key}_live", None)
        if room:            # "-38.4|{summary}|<WAV>": the room level the guided recorder measured (the quality check uses it, fricative/noise.py: recording_quality)
            _, _, rest = wav.partition("|")                                  # and, for a held hiss, what the live guide found (learner/result.py: from_live)
            summary, _, wav = rest.partition("|")
            st.session_state[f"{key}_room"] = float(room)
            if summary:
                import json
                st.session_state[f"{key}_live"] = json.loads(summary)
        else:
            st.session_state.pop(f"{key}_room", None)
        st.session_state[store] = base64.b64decode(wav)
    return st.session_state.get(store)
