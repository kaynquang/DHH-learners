"""A record button that stops by itself after a couple of seconds, so the learner never has to press stop."""
import streamlit as st
import streamlit.components.v2 as components

RECORD_SECONDS = 3.0

_JS = """
export default function (component) {
  const { parentElement, data, setTriggerValue } = component;
  const btn = parentElement.querySelector("button");
  const note = parentElement.querySelector(".note");
  const stopBtn = parentElement.querySelector(".stop");
  let busy = false, stopNow = null;
  stopBtn.onclick = () => { if (stopNow) stopNow(); };

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

  btn.onclick = async () => {
    if (busy) return;
    busy = true; btn.disabled = true;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        // raw microphone: auto gain clips the loud vowel and noise suppression erases the quiet start of /b/ and /p/
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
      });
      const rec = new MediaRecorder(stream), chunks = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      const stopped = new Promise((r) => (rec.onstop = r));
      rec.start();
      const t0 = performance.now(), ms = data.seconds * 1000;
      const tick = setInterval(() => {
        note.textContent = "Recording… " + Math.max(0, (ms - (performance.now() - t0)) / 1000).toFixed(1) + " s";
      }, 100);
      stopBtn.hidden = false;
      await new Promise((r) => { stopNow = r; setTimeout(r, ms); });
      stopBtn.hidden = true; stopNow = null;
      rec.stop(); clearInterval(tick);
      await stopped;
      stream.getTracks().forEach((t) => t.stop());
      note.textContent = "Processing…";
      const ctx = new AudioContext();
      const audio = await ctx.decodeAudioData(await new Blob(chunks).arrayBuffer());
      ctx.close();
      setTriggerValue("wav", toWav(audio));
      note.textContent = "Done. Press to record again.";
    } catch (err) {
      note.textContent = "Could not use the microphone: " + (err && err.message ? err.message : err);
    }
    busy = false; btn.disabled = false;
  };
}
"""

_HTML = """
<div class="rec"><button type="button">● Record</button> <button type="button" class="stop" hidden>■ Stop</button> <span class="note"></span></div>
"""

_CSS = """
.rec { display: flex; align-items: center; gap: 0.75rem; font-family: inherit; }
.rec button { padding: 0.5rem 1rem; border-radius: 0.5rem; border: 1px solid rgba(128,128,128,.5);
  background: transparent; color: inherit; font: inherit; cursor: pointer; }
.rec button:disabled { opacity: .6; cursor: default; }
.rec .note { opacity: .75; }
.rec .stop { border-color: #c0432e; color: #c0432e; }
"""

_component = components.component("auto_record", html=_HTML, css=_CSS, js=_JS)


_PLAY_JS = """
export default function (component) {
  const { parentElement, data } = component;
  const audio = parentElement.querySelector("audio"), cv = parentElement.querySelector("canvas");
  const tag = data.b64.length + ":" + data.b64.slice(-32);
  if (audio.dataset.tag !== tag) { audio.dataset.tag = tag; audio.src = "data:" + data.mime + ";base64," + data.b64; }
  const ink = getComputedStyle(cv).color || "#2b2b2b";     // parentElement is a shadow root, not an Element
  let peaks = null;

  const draw = () => {
    const w = cv.clientWidth, h = cv.clientHeight, dpr = window.devicePixelRatio || 1;
    cv.width = w * dpr; cv.height = h * dpr;
    const g = cv.getContext("2d"); g.scale(dpr, dpr); g.clearRect(0, 0, w, h);
    if (peaks) {
      g.fillStyle = ink; g.globalAlpha = 0.55;
      const bw = w / peaks.length;
      peaks.forEach((p, i) => g.fillRect(i * bw, h / 2 - p * h / 2, Math.max(bw - 0.5, 0.5), Math.max(p * h, 1)));
      g.globalAlpha = 1;
    }
    const d = audio.duration;
    if (d > 0) {
      const x = (audio.currentTime / d) * w;
      g.fillStyle = "#c0432e"; g.fillRect(x - 1, 0, 2, h);
    }
  };

  (async () => {
    const bin = atob(data.b64), bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    try {
      const ctx = new AudioContext();
      const buf = await ctx.decodeAudioData(bytes.buffer);
      ctx.close();
      const ch = buf.getChannelData(0), n = 300, step = Math.max(1, Math.floor(ch.length / n));
      peaks = Array.from({ length: n }, (_, i) => {
        let m = 0;
        for (let j = i * step; j < Math.min((i + 1) * step, ch.length); j++) m = Math.max(m, Math.abs(ch[j]));
        return m;
      });
      const top = Math.max(...peaks, 1e-6);
      peaks = peaks.map((p) => p / top);
    } catch (e) { /* no waveform, the player still works */ }
    draw();
  })();

  let raf = null;
  const loop = () => { draw(); if (!audio.paused) raf = requestAnimationFrame(loop); };
  audio.onplay = () => { cancelAnimationFrame(raf); loop(); };
  audio.onpause = audio.onended = audio.onseeked = draw;
  cv.onclick = (e) => {
    const d = audio.duration;
    if (d > 0) { audio.currentTime = (e.offsetX / cv.clientWidth) * d; draw(); }
  };
  window.addEventListener("resize", draw);
}
"""

_PLAY_HTML = '<div class="play"><canvas></canvas><audio controls></audio></div>'
_PLAY_CSS = """
.play { display: flex; flex-direction: column; gap: 0.25rem; color: #2b2b2b; }
.play canvas { width: 100%; height: 90px; cursor: pointer; background: rgba(128,128,128,.08); border-radius: 0.5rem; }
.play audio { width: 100%; }
"""

_playback = components.component("playback_waveform", html=_PLAY_HTML, css=_PLAY_CSS, js=_PLAY_JS)


def playback(audio: bytes, key: str, name: str = "recording.wav") -> None:
    """The recorded audio as a waveform with a red line that sweeps across it while it plays (click the waveform to jump)."""
    import base64
    mime = "audio/mpeg" if name.lower().endswith(".mp3") else "audio/wav"
    _playback(key=key, data={"b64": base64.b64encode(audio).decode("ascii"), "mime": mime})


def auto_record(key: str, seconds: float = RECORD_SECONDS) -> bytes | None:
    """Show a record button that captures `seconds` of audio, then stops on its own. Returns the latest WAV bytes, or None."""
    import base64
    result = _component(key=key, data={"seconds": seconds}, on_wav_change=lambda: None)
    wav = getattr(result, "wav", None)
    store = f"{key}_wav"
    if wav:
        st.session_state[store] = base64.b64decode(wav)
    return st.session_state.get(store)
