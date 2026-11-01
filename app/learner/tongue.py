"""A friendly side view of the head for /s/ and /ʃ/, with a tongue that sits between the two poses according to the sound that was said.

This shows "where the learner's sound lies between /ʃ/ and /s/", drawn from one number. With a calibration it is the calibrated model's
share of /s/ against /ʃ/; without one it is the centre of gravity (CoG) of the hiss. It is an index of the SOUND, not a measurement of the
tongue: lip rounding and the microphone also move the CoG. The poses are a simplified drawing, not an anatomical record.
"""
from __future__ import annotations

from fricative import config as C

from .lessons import ACCENT

SH_ANCHOR_HZ = 2000.0      # CoG at or below which the picture shows the full /ʃ/ pose (provisional)
S_ANCHOR_HZ = 10400.0      # CoG at or above which it shows the full /s/ pose (about the median of "see" in the Dev log)
MIN_HISS_COG_HZ = 1000.0   # below this there is no hiss to place

INK = "#1B2440"
# Tongue outline, clockwise from the back of the mouth floor. Same number of points in both poses so they can be blended.
TONGUE_S = [(168, 346), (166, 310), (206, 284), (272, 272), (342, 274), (402, 284), (440, 304), (438, 322), (402, 334), (334, 345), (246, 358)]
TONGUE_SH = [(172, 346), (170, 298), (214, 254), (284, 226), (352, 222), (396, 232), (418, 254), (412, 274), (380, 292), (324, 318), (246, 354)]
LIP_SHIFT_SH = 14          # the lips push forward this many pixels for /ʃ/ (rounded lips)


def position(cog_hz: float) -> float:
    """0 = the /ʃ/ pose, 1 = the /s/ pose, from the CoG of the hiss. The middle (0.5) is the threshold the Dev app uses to tell /s/ from
    /ʃ/, so the picture and the verdict always agree about which side the sound is on."""
    mid = C.DEFAULT_THRESHOLDS.cog_s_sh_hz
    if cog_hz >= mid:
        return min(1.0, 0.5 + 0.5 * (cog_hz - mid) / (S_ANCHOR_HZ - mid))
    return max(0.0, 0.5 * (cog_hz - SH_ANCHOR_HZ) / (mid - SH_ANCHOR_HZ))


def _blend(t: float) -> list[tuple[float, float]]:
    return [(a[0] * t + b[0] * (1 - t), a[1] * t + b[1] * (1 - t)) for a, b in zip(TONGUE_S, TONGUE_SH)]


def _smooth(points: list[tuple[float, float]], closed: bool = True) -> str:
    """A smooth curve through the points (Catmull-Rom turned into cubic Béziers)."""
    n = len(points)
    at = (lambda i: points[i % n]) if closed else (lambda i: points[max(0, min(n - 1, i))])
    d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C {c1[0]:.1f} {c1[1]:.1f}, {c2[0]:.1f} {c2[1]:.1f}, {p2[0]:.1f} {p2[1]:.1f}"
    return d + (" Z" if closed else "")


def mouth_svg(t: float, target_t: float) -> str:
    """A head in side view with the learner's tongue (solid) and the target tongue (dashed), t and target_t in 0..1 (0 = /ʃ/, 1 = /s/)."""
    you, goal = _blend(t), _blend(target_t)
    dx = (1 - t) * LIP_SHIFT_SH                     # lips pushed forward and rounded for /ʃ/
    squeeze = (1 - t) * 5                           # and a little closer together
    tip_you, tip_goal = you[6], goal[6]
    jet = tip_you[1] - 12
    wide = 6 + (1 - t) * 8                          # a wider air channel for /ʃ/
    arrows = "".join(
        f'<path d="M {tip_you[0] + 4:.0f} {jet + o:.0f} C {tip_you[0] + 50:.0f} {jet + o * 0.4:.0f}, {500 + dx:.0f} {282 + o:.0f}, {548 + dx:.0f} {282 + o * 1.5:.0f}" '
        f'fill="none" stroke="#7FB2F5" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 11" marker-end="url(#ah)"/>'
        for o in (-wide, 0, wide))
    top = you[1:6]                                  # the upper edge of the tongue, for the soft highlight
    return f"""<svg viewBox="0 0 600 450" role="img" aria-label="Side view of the head with the tongue" style="width:100%;height:auto;display:block">
<defs><marker id="ah" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7FB2F5"/></marker></defs>
<rect width="600" height="450" rx="18" fill="#F6F9FE"/>
<g stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
<path d="M 250 20 C 340 10 424 44 450 104 C 460 130 464 148 472 172 C 482 190 498 206 514 224 C 522 234 512 246 498 246 L 482 248 C 478 256 481 262 487 266 L 486 322 C 484 338 480 352 472 368 C 466 386 450 400 430 412 L 402 446 L 150 446 C 120 390 60 340 42 256 C 22 150 100 34 250 20 Z" fill="#F7D6C0"/>
<path d="M 468 268 L 448 242 C 404 204 306 190 226 206 C 186 214 150 242 150 296 C 150 346 196 378 300 372 C 384 366 444 334 466 300 Z" fill="#EE9A94"/>
<path d="M 448 242 C 404 204 306 190 226 206 C 190 214 162 232 156 266" fill="none" stroke="#D9747D" stroke-width="12"/>
<rect x="447" y="236" width="24" height="52" rx="9" fill="#fff"/>
<rect x="450" y="296" width="24" height="44" rx="9" fill="#fff"/>
</g>
<path d="{_smooth(goal)}" fill="none" stroke="{ACCENT}" stroke-width="4" stroke-dasharray="8 7" stroke-linecap="round"/>
<path d="{_smooth(you)}" fill="#E9605F" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
<path d="{_smooth(top, closed=False)}" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="0.4" transform="translate(0 7)"/>
<g stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
<path d="M 470 252 C {500 + dx:.0f} {240 + squeeze:.0f}, {520 + dx:.0f} {262 + squeeze:.0f}, {512 + dx:.0f} {284 + squeeze:.0f} L 474 288 Z" fill="#E9837D"/>
<path d="M 474 292 C {516 + dx:.0f} {292 - squeeze:.0f}, {522 + dx:.0f} {322 - squeeze:.0f}, {496 + dx:.0f} {334 - squeeze:.0f} C 480 336, 474 326, 474 292 Z" fill="#E9837D"/>
</g>
{arrows}
<circle cx="{tip_goal[0]:.0f}" cy="{tip_goal[1]:.0f}" r="10" fill="#fff" stroke="{ACCENT}" stroke-width="4"/>
<circle cx="{tip_you[0]:.0f}" cy="{tip_you[1]:.0f}" r="10" fill="{ACCENT}" stroke="#fff" stroke-width="4"/>
<circle cx="408" cy="128" r="9" fill="#fff" stroke="{INK}" stroke-width="3.5"/><circle cx="411" cy="128" r="4.5" fill="{INK}"/>
</svg>"""


RED_Q_MAX = 0.5       # closeness to the target below this is "Not yet" (red)
YELLOW_Q_MAX = 0.8    # from here up it is "Correct" (green); in between it is "Almost" (yellow)
GREEN, YELLOW, RED = "#A6DC8F", "#F5C84B", "#F29B94"


def _track_background(target_t: float) -> str:
    """The track in three zones, with the green one at the target's end: green (correct), yellow (almost, the middle), red (not yet)."""
    q_to_x = (lambda q: q * 100) if target_t >= 0.5 else (lambda q: (1 - q) * 100)
    stops = [(0, RED_Q_MAX, RED), (RED_Q_MAX, YELLOW_Q_MAX, YELLOW), (YELLOW_Q_MAX, 1.0, GREEN)]
    parts = []
    for a, b, colour in stops:
        x0, x1 = sorted((q_to_x(a), q_to_x(b)))
        parts.append(f"{colour} {x0:.1f}% {x1:.1f}%")
    return "linear-gradient(90deg, " + ", ".join(sorted(parts, key=lambda p: float(p.split()[1].rstrip('%')))) + ")"


def slider_html(t: float, target_t: float) -> str:
    """The line from /ʃ/ (left) to /s/ (right) with a marker for the learner's sound and one for the target. The line has a green zone at
    the target's end, a yellow one in the middle ("Almost") and a red one at the far end, so the marker's place matches the verdict."""
    return f"""<div class="tg-slider">
<div class="tg-end"><b>/ʃ/</b></div>
<div class="tg-track" style="background:{_track_background(target_t)}"><div class="tg-target" style="left:{target_t * 100:.0f}%"></div><div class="tg-you" style="left:{t * 100:.0f}%"></div></div>
<div class="tg-end"><b>/s/</b></div>
</div>
<div class="tg-legend"><span><i class="tg-you-key"></i>You</span><span><i class="tg-target-key"></i>Target</span></div>"""


CSS = f"""
.tg-card {{ background: #FFF; border: 1.5px solid #D5DFF0; border-radius: 24px; box-shadow: 0 4px 0 #D5DFF0; padding: 22px; margin-top: 20px; color: #1B2440; }}
.tg-grid {{ display: flex; flex-wrap: wrap; gap: 24px; align-items: center; }}
.tg-grid > div:first-child {{ flex: 1 1 420px; min-width: 0; }}
.tg-grid > div:last-child {{ flex: 1 1 320px; min-width: 0; }}
.tg-slider {{ display: flex; align-items: center; gap: 14px; font-size: 22px; }}
.tg-track {{ position: relative; flex: 1; margin: 0 16px; height: 14px; border-radius: 999px; background: linear-gradient(90deg, #CFE3FF, #A6DC8F); }}
.tg-you, .tg-target {{ position: absolute; top: 50%; width: 30px; height: 30px; margin: -15px 0 0 -15px; border-radius: 50%; box-sizing: border-box; }}
.tg-you {{ background: {ACCENT}; border: 4px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,.35); }}
.tg-target {{ background: #fff; border: 4px dashed {ACCENT}; }}
.tg-legend {{ display: flex; gap: 22px; justify-content: center; margin-top: 16px; font-size: 15px; font-weight: 800; }}
.tg-legend i {{ display: inline-block; width: 16px; height: 16px; border-radius: 50%; margin-right: 8px; vertical-align: -3px; box-sizing: border-box; }}
.tg-you-key {{ background: {ACCENT}; }}
.tg-target-key {{ border: 3px dashed {ACCENT}; background: #fff; }}
"""
