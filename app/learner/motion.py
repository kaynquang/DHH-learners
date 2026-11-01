"""The mouth picture as a short loop of 2-3 steps, drawn on top of the still picture (no new picture is made).

Each step dims the picture except for one lit area, draws moving marks there (pulsing rings, bobbing arrows, flowing air) and shows its
words, then the next step follows and the loop starts again. The learner can pause, jump to a step (the dots) and slow it down. The marks
and the words come from the lesson (learner/lessons.py: Motion), so the content owner can change them without touching this file.
Nothing in the picture itself moves: the tongue is not animated.
"""
from __future__ import annotations

import json

import streamlit.components.v2 as components

from .lessons import ACCENT, Lesson
from .screen import _image_uri

STEP_SECONDS = 3.6

_HTML = """
<div class="mv">
  <div class="stage"><img class="pic" alt=""><svg class="ov"></svg></div>
  <div class="cap"><div class="ico"></div><div class="txt"></div></div>
  <div class="ctl">
    <button type="button" class="pp" aria-label="Pause or play"></button>
    <div class="dots"></div>
    <button type="button" class="spd" aria-label="Speed">1×</button>
  </div>
  <div class="bar"><div></div></div>
</div>
"""

_CSS = f"""
:host {{ display: block; }}
.mv {{ font-family: 'Nunito', 'Noto Sans TC', system-ui, sans-serif; color: #1B2440; display: flex; flex-direction: column; gap: 12px; }}
.stage {{ position: relative; border-radius: 16px; overflow: hidden; line-height: 0; }}
.pic {{ display: block; width: 100%; height: auto; }}
.ov {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.cap {{ display: flex; align-items: center; gap: 14px; min-height: 96px; background: #fff; border: 2px solid {ACCENT}; border-left-width: 10px; border-radius: 16px; padding: 14px 20px; }}
.ico {{ flex: 0 0 auto; }}
.ico:empty {{ display: none; }}
.txt {{ transition: opacity .35s; }}
.txt .en {{ font-size: 28px; font-weight: 800; line-height: 1.25; color: #0F1A3C; }}
.txt .zh {{ font-family: 'Noto Sans TC', sans-serif; font-size: 24px; font-weight: 700; color: {ACCENT}; line-height: 1.35; margin-bottom: 4px; }}
.ctl {{ display: flex; align-items: center; justify-content: center; gap: 14px; }}
.ctl button {{ min-width: 46px; height: 46px; border-radius: 999px; border: 1.5px solid #D5DFF0; background: #fff; color: #1B2440; font: 800 15px inherit;
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 14px; }}
.ctl button:hover {{ border-color: {ACCENT}; }}
.dots {{ display: flex; gap: 10px; }}
.dot {{ width: 34px; height: 34px; border-radius: 50%; border: 2px solid #D5DFF0; background: #fff; font: 800 15px inherit; color: #3A4664; cursor: pointer; padding: 0; }}
.dot.on {{ background: {ACCENT}; border-color: {ACCENT}; color: #fff; }}
.bar {{ height: 6px; border-radius: 999px; background: #DFE6F3; overflow: hidden; }}
.bar > div {{ height: 100%; width: 0; background: {ACCENT}; border-radius: 999px; }}
.layer {{ opacity: 0; transition: opacity .4s; }}
.layer.on {{ opacity: 1; }}
.ring {{ fill: none; stroke: #fff; stroke-width: 9; transform-box: fill-box; transform-origin: center; animation: pulse 1.3s ease-out infinite; }}
.ring-in {{ fill: none; stroke: {ACCENT}; stroke-width: 5; }}
.arrow {{ animation: bob 1.1s ease-in-out infinite alternate; }}
.flow {{ fill: none; stroke: #fff; stroke-width: 13; stroke-linecap: round; stroke-dasharray: 22 30; animation: flow 1.1s linear infinite; opacity: .95; }}
.flow-in {{ fill: none; stroke: {ACCENT}; stroke-width: 6; stroke-linecap: round; stroke-dasharray: 22 30; animation: flow 1.1s linear infinite; }}
.paused .ring, .paused .arrow, .paused .flow, .paused .flow-in {{ animation-play-state: paused; }}
@keyframes pulse {{ 0% {{ transform: scale(.82); opacity: 1; }} 100% {{ transform: scale(1.22); opacity: 0; }} }}
@keyframes bob {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(var(--dx), var(--dy)); }} }}
@keyframes flow {{ to {{ stroke-dashoffset: -52; }} }}
@media (prefers-reduced-motion: reduce) {{ .ring, .arrow, .flow, .flow-in {{ animation: none; }} }}
"""

_JS = """
export default function (component) {
  const { parentElement: root, data } = component;
  const NS = "http://www.w3.org/2000/svg";
  const $ = (s) => root.querySelector(s);
  const mv = $(".mv"), svg = $(".ov"), pic = $(".pic"), txt = $(".txt"), ico = $(".ico"), bar = $(".bar > div");
  const W = data.w, H = data.h, steps = data.steps;
  pic.src = data.image;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("preserveAspectRatio", "none");
  svg.innerHTML = "";
  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    (parent || svg).appendChild(e);
    return e;
  };

  // the dimmed picture with a soft lit hole
  const defs = el("defs", {});
  const blur = el("filter", { id: "soft", x: "-30%", y: "-30%", width: "160%", height: "160%" }, defs);
  el("feGaussianBlur", { stdDeviation: 22 }, blur);
  const mask = el("mask", { id: "lit" }, defs);
  el("rect", { width: W, height: H, fill: "#fff" }, mask);
  const hole = el("ellipse", { cx: -999, cy: -999, rx: 10, ry: 10, fill: "#000", filter: "url(#soft)" }, mask);
  const arrowHead = el("marker", { id: "ah", viewBox: "0 0 10 10", refX: 6, refY: 5, markerWidth: 3.2, markerHeight: 3.2, orient: "auto" }, defs);
  el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#2F6FE4" }, arrowHead);

  // the marks of every step, shown only while their step is on
  const layers = steps.map((s) => {
    const g = el("g", { class: "layer" });
    (s.shapes || []).forEach((sh) => {
      if (sh.type === "ring") {
        return;                                           // no lit circles: the words carry the step
      } else if (sh.type === "arrow") {
        const a = el("g", { class: "arrow", style: `--dx:${sh.dx * 0.5}px;--dy:${sh.dy * 0.5}px` }, g);
        const x2 = sh.x + sh.dx, y2 = sh.y + sh.dy;
        el("line", { x1: sh.x, y1: sh.y, x2: x2, y2: y2, stroke: "#fff", "stroke-width": 15, "stroke-linecap": "round" }, a);
        el("line", { x1: sh.x, y1: sh.y, x2: x2, y2: y2, stroke: "#2F6FE4", "stroke-width": 7, "stroke-linecap": "round", "marker-end": "url(#ah)" }, a);
      } else if (sh.type === "flow") {
        el("path", { class: "flow", d: sh.d }, g);
        el("path", { class: "flow-in", d: sh.d }, g);
      }
    });
    return g;
  });

  const ICONS = {
    novoice: '<svg viewBox="0 0 64 40" width="64" height="40" aria-hidden="true"><path d="M 4 20 C 10 4, 16 4, 22 20 S 34 36, 40 20 S 52 4, 60 20" fill="none" stroke="#1B2440" stroke-width="4" stroke-linecap="round"/><path d="M 8 34 L 56 6" stroke="#D9363E" stroke-width="5" stroke-linecap="round"/></svg>',
  };

  // dots, play/pause, speed
  const dots = $(".dots"), pp = $(".pp"), spd = $(".spd");
  dots.innerHTML = "";
  const dotEls = steps.map((_, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "dot"; b.textContent = String(i + 1); b.setAttribute("aria-label", "Step " + (i + 1));
    b.onclick = () => show(i, true);
    dots.appendChild(b);
    return b;
  });
  const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="20" height="20"><rect x="5" y="4" width="5" height="16" rx="1.5" fill="#1B2440"/><rect x="14" y="4" width="5" height="16" rx="1.5" fill="#1B2440"/></svg>';
  const ICON_PLAY = '<svg viewBox="0 0 24 24" width="20" height="20"><path d="M 7 4 L 20 12 L 7 20 Z" fill="#1B2440"/></svg>';

  let cur = -1, timer = null, playing = !data.hold && !window.matchMedia("(prefers-reduced-motion: reduce)").matches, rate = 1, tween = null;
  const lit = { cx: -999, cy: -999, rx: 10, ry: 10 };
  const aim = (s) => {
    cancelAnimationFrame(tween);
    const from = { ...lit }, to = { cx: s.spot[0], cy: s.spot[1], rx: s.spot[2], ry: s.spot[3] };
    if (from.cx < -900) Object.assign(from, to, { rx: 1, ry: 1 });
    const t0 = performance.now();
    const tick = (now) => {
      const k = Math.min(1, (now - t0) / 700), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      for (const key of ["cx", "cy", "rx", "ry"]) lit[key] = from[key] + (to[key] - from[key]) * e;
      for (const key of ["cx", "cy", "rx", "ry"]) hole.setAttribute(key, lit[key]);
      if (k < 1) tween = requestAnimationFrame(tick);
    };
    tween = requestAnimationFrame(tick);
  };
  const progress = (ms) => {
    bar.style.transition = "none"; bar.style.width = "0%";
    void bar.offsetWidth;
    if (playing) { bar.style.transition = `width ${ms}ms linear`; bar.style.width = "100%"; }
  };
  const schedule = () => {
    clearTimeout(timer);
    const ms = data.seconds * 1000 / rate;
    progress(ms);
    if (playing) timer = setTimeout(() => show((cur + 1) % steps.length, false), ms);
  };
  const show = (i, user) => {
    cur = i;
    layers.forEach((g, k) => g.classList.toggle("on", k === i));
    dotEls.forEach((d, k) => d.classList.toggle("on", k === i));
    const s = steps[i];
    txt.style.opacity = 0;
    setTimeout(() => {
      txt.innerHTML = s.caption.map((c) => `<div class="en">${c[0]}</div><div class="zh">${c[1]}</div>`).join("");
      ico.innerHTML = s.icon ? ICONS[s.icon] || "" : "";
      txt.style.opacity = 1;
    }, 180);
    aim(s);
    schedule();
  };
  const setPlaying = (on) => {
    playing = on;
    mv.classList.toggle("paused", !on);
    pp.innerHTML = on ? ICON_PAUSE : ICON_PLAY;
    schedule();
  };
  pp.onclick = () => setPlaying(!playing);
  spd.onclick = () => { rate = rate === 1 ? 0.5 : 1; spd.textContent = rate === 1 ? "1×" : "0.5×"; schedule(); };
  show(Math.min(data.start || 0, steps.length - 1), false);
  setPlaying(playing);
  return () => { clearTimeout(timer); cancelAnimationFrame(tween); };
}
"""

_component = components.component("mouth_motion", html=_HTML, css=_CSS, js=_JS)


def mouth_motion(lesson: Lesson, key: str, start: int = 0, hold: bool = False) -> None:
    """Show the lesson's mouth picture as a loop of its motions. `start` and `hold` (stay on that step) are for checking one step."""
    from PIL import Image
    width, height = Image.open(lesson.mouth_image).size
    steps = [{"caption": [list(c) for c in m.caption], "spot": list(m.spot), "shapes": list(m.shapes), "icon": m.icon} for m in lesson.motions]
    _component(key=key, data={"image": _image_uri(str(lesson.mouth_image)), "w": width, "h": height, "steps": steps, "seconds": STEP_SECONDS,
                              "start": start, "hold": hold})


# ---------------------------------------------------------------------------------------------------------------------------------
# Lessons made of several pictures (learner/lessons.py: Step), for sounds made in steps such as /m/: close the lips, hum, open.
# ---------------------------------------------------------------------------------------------------------------------------------
_STEPS_HTML = """
<div class="sv">
  <div class="stage"><img class="a" alt=""><img class="b" alt=""><svg class="ov"></svg></div>
  <ul class="checks"></ul>
  <div class="ctl">
    <button type="button" class="pp" aria-label="Pause or play"></button>
    <div class="dots"></div>
    <button type="button" class="spd" aria-label="Speed">1×</button>
  </div>
  <div class="bar"><div></div></div>
</div>
"""

_STEPS_CSS = f"""
:host {{ display: block; }}
.sv {{ font-family: 'Nunito', 'Noto Sans TC', system-ui, sans-serif; color: #1B2440; display: flex; flex-direction: column; gap: 14px; }}
.stage {{ position: relative; width: 100%; border-radius: 16px; overflow: hidden; background: #F6F9FE; }}
.stage img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity .45s ease; }}
.stage img.on {{ opacity: 1; }}
.stage img {{ object-position: top; }}
.ov {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }}
.layer {{ opacity: 0; transition: opacity .4s; }}
.layer.on {{ opacity: 1; }}
.ring {{ fill: none; stroke: #fff; stroke-width: 9; transform-box: fill-box; transform-origin: center; animation: pulse 1.3s ease-out infinite; }}
.ring-in {{ fill: none; stroke-width: 5; }}
.arrow {{ animation: bob 1.1s ease-in-out infinite alternate; }}
.flow {{ fill: none; stroke: #fff; stroke-width: 13; stroke-linecap: round; stroke-dasharray: 22 30; animation: flow 1.1s linear infinite; opacity: .95; }}
.flow-in {{ fill: none; stroke-width: 6; stroke-linecap: round; stroke-dasharray: 22 30; animation: flow 1.1s linear infinite; }}
.wave {{ fill: none; stroke-width: 7; stroke-linecap: round; transform-box: fill-box; transform-origin: center; animation: wave 1.2s ease-out infinite; }}
.paused .ring, .paused .arrow, .paused .flow, .paused .flow-in, .paused .wave {{ animation-play-state: paused; }}
@keyframes pulse {{ 0% {{ transform: scale(.82); opacity: 1; }} 100% {{ transform: scale(1.22); opacity: 0; }} }}
@keyframes bob {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(var(--dx), var(--dy)); }} }}
@keyframes flow {{ to {{ stroke-dashoffset: -52; }} }}
@keyframes wave {{ 0% {{ transform: scale(.7); opacity: .95; }} 100% {{ transform: scale(1.25); opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .ring, .arrow, .flow, .flow-in, .wave {{ animation: none; }} }}
.checks {{ margin: 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }}
.checks li {{ display: flex; gap: 10px; align-items: flex-start; background: #F6F9FE; border: 1.5px solid #E1E9F6; border-radius: 16px; padding: 12px; }}
.checks svg {{ width: 22px; height: 22px; flex: 0 0 22px; }}
.checks .en {{ font-size: 18px; font-weight: 800; line-height: 1.3; color: #0F1A3C; }}
.checks .zh {{ font-size: 18px; font-weight: 700; color: {ACCENT}; line-height: 1.35; }}
.checks .py {{ font-size: 15px; font-weight: 400; color: #3A4664; line-height: 1.35; }}
.checks .zh {{ font-family: 'Noto Sans TC', sans-serif; }}
.ctl {{ display: flex; align-items: center; justify-content: center; gap: 14px; }}
.ctl button {{ min-width: 46px; height: 46px; border-radius: 999px; border: 1.5px solid #D5DFF0; background: #fff; color: #1B2440; font: 800 15px inherit;
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 14px; }}
.ctl button:hover {{ border-color: {ACCENT}; }}
.dots {{ display: flex; gap: 10px; }}
.dot {{ width: 34px; height: 34px; border-radius: 50%; border: 2px solid #D5DFF0; background: #fff; font: 800 15px inherit; color: #3A4664; cursor: pointer; padding: 0; }}
.dot.on {{ background: {ACCENT}; border-color: {ACCENT}; color: #fff; }}
.bar {{ height: 6px; border-radius: 999px; background: #DFE6F3; overflow: hidden; }}
.bar > div {{ height: 100%; width: 0; background: {ACCENT}; border-radius: 999px; }}
.sv.compact .checks {{ grid-template-columns: repeat(3, 1fr); gap: 8px; }}
.sv.compact .checks li {{ padding: 9px; gap: 7px; }}
.sv.compact .en, .sv.compact .zh {{ font-size: 14.5px; }}
.sv.compact .py {{ display: none; }}
"""

_STEPS_JS = """
export default function (component) {
  const { parentElement: root, data } = component;
  const $ = (s) => root.querySelector(s);
  const imgs = [$(".a"), $(".b")], stage = $(".stage"), list = $(".checks"), dots = $(".dots"), pp = $(".pp"), spd = $(".spd"), bar = $(".bar > div");
  const steps = data.steps;
  if (data.compact) $(".sv").classList.add("compact");
  stage.style.aspectRatio = `${data.w} / ${data.h}`;
  steps.forEach((s) => { const i = new Image(); i.src = s.image; });          // load them all, so the change is instant

  // the moving marks of every step, drawn on the picture and shown only while their step is on
  const NS = "http://www.w3.org/2000/svg", svg = $(".ov"), mv = $(".sv");
  svg.setAttribute("viewBox", `0 0 ${data.w} ${data.h}`);
  svg.setAttribute("preserveAspectRatio", "none");
  svg.innerHTML = "";
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); (parent || svg).appendChild(e); return e; };
  const defs = el("defs", {});
  const markers = {};
  const marker = (colour) => {
    if (markers[colour]) return markers[colour];
    const id = "ah" + Object.keys(markers).length;
    const m = el("marker", { id, viewBox: "0 0 10 10", refX: 6, refY: 5, markerWidth: 3.2, markerHeight: 3.2, orient: "auto" }, defs);
    el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: colour }, m);
    return (markers[colour] = id);
  };
  const layers = steps.map((s) => {
    const g = el("g", { class: "layer" });
    (s.shapes || []).forEach((sh) => {
      const colour = sh.color || "#2F6FE4";
      if (sh.type === "ring") {
        return;                                           // no lit circles: the words carry the step
      } else if (sh.type === "wave") {                    // a ring that spreads out and fades, like a vibration
        el("circle", { class: "wave", cx: sh.cx, cy: sh.cy, r: sh.r, stroke: colour }, g);
        el("circle", { class: "wave", cx: sh.cx, cy: sh.cy, r: sh.r, stroke: colour, style: "animation-delay:.6s" }, g);
      } else if (sh.type === "arrow") {
        const a = el("g", { class: "arrow", style: `--dx:${sh.dx * 0.5}px;--dy:${sh.dy * 0.5}px` }, g);
        const x2 = sh.x + sh.dx, y2 = sh.y + sh.dy;
        el("line", { x1: sh.x, y1: sh.y, x2: x2, y2: y2, stroke: "#fff", "stroke-width": 15, "stroke-linecap": "round" }, a);
        el("line", { x1: sh.x, y1: sh.y, x2: x2, y2: y2, stroke: colour, "stroke-width": 7, "stroke-linecap": "round", "marker-end": `url(#${marker(colour)})` }, a);
      } else if (sh.type === "flow") {
        el("path", { class: "flow", d: sh.d }, g);
        el("path", { class: "flow-in", d: sh.d, stroke: colour }, g);
      }
    });
    return g;
  });

  const CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#2F6FE4"/><path d="M 7 12.5 L 10.5 16 L 17 8.5" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="20" height="20"><rect x="5" y="4" width="5" height="16" rx="1.5" fill="#1B2440"/><rect x="14" y="4" width="5" height="16" rx="1.5" fill="#1B2440"/></svg>';
  const ICON_PLAY = '<svg viewBox="0 0 24 24" width="20" height="20"><path d="M 7 4 L 20 12 L 7 20 Z" fill="#1B2440"/></svg>';

  dots.innerHTML = "";
  const dotEls = steps.map((_, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "dot"; b.textContent = String(i + 1); b.setAttribute("aria-label", "Step " + (i + 1));
    b.onclick = () => show(i);
    dots.appendChild(b);
    return b;
  });

  let cur = -1, front = 0, timer = null, playing = !data.hold && !window.matchMedia("(prefers-reduced-motion: reduce)").matches, rate = 1;
  const progress = (ms) => {
    bar.style.transition = "none"; bar.style.width = "0%";
    void bar.offsetWidth;
    if (playing) { bar.style.transition = `width ${ms}ms linear`; bar.style.width = "100%"; }
  };
  const schedule = () => {
    clearTimeout(timer);
    const ms = steps[cur].seconds * 1000 / rate;
    progress(ms);
    if (playing) timer = setTimeout(() => show((cur + 1) % steps.length), ms);
  };
  const show = (i) => {
    if (i !== cur) {
      const back = 1 - front;
      imgs[back].src = steps[i].image;
      imgs[back].classList.add("on"); imgs[front].classList.remove("on");
      front = back;
      list.innerHTML = steps[i].checks.map((c) =>
        `<li>${CHECK}<span><span class="en">${esc(c[0])}</span><br><span class="zh">${esc(c[1])}</span>${c[2] ? `<br><span class="py">${esc(c[2])}</span>` : ""}</span></li>`).join("");
    }
    cur = i;
    layers.forEach((g, k) => g.classList.toggle("on", k === i));
    dotEls.forEach((d, k) => d.classList.toggle("on", k === i));
    schedule();
  };
  const setPlaying = (on) => { playing = on; mv.classList.toggle("paused", !on); pp.innerHTML = on ? ICON_PAUSE : ICON_PLAY; schedule(); };
  pp.onclick = () => setPlaying(!playing);
  spd.onclick = () => { rate = rate === 1 ? 0.5 : 1; spd.textContent = rate === 1 ? "1×" : "0.5×"; schedule(); };
  show(Math.min(data.start || 0, steps.length - 1));
  setPlaying(playing);
  return () => clearTimeout(timer);
}
"""

_steps_component = components.component("mouth_steps", html=_STEPS_HTML, css=_STEPS_CSS, js=_STEPS_JS)


def mouth_steps(lesson: Lesson, key: str, start: int = 0, hold: bool = False, compact: bool = False) -> None:
    """Show the lesson's pictures one after another (they play by themselves, in a loop, and can be paused or jumped to)."""
    from PIL import Image
    width, height = Image.open(lesson.steps[0].image).size
    height = lesson.steps[0].display_height or height
    steps = [{"image": _image_uri(str(s.image)), "checks": [list(c) for c in s.checks], "seconds": s.seconds, "shapes": list(s.shapes)} for s in lesson.steps]
    _steps_component(key=key, data={"w": width, "h": height, "steps": steps, "start": start, "hold": hold, "compact": compact})
