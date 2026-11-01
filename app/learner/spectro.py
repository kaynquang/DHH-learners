"""The sound as a picture, for a child who cannot hear it: a simplified spectrogram with the target zone drawn on it (/s/ and /ʃ/ for now).

Frequency is the height (low at the bottom), time runs left to right, and the more energy, the darker the blue. The three coloured bands are
the same green / yellow / red zones as the /ʃ/–/s/ slider: they come from the same thresholds as the scoring (config.DEFAULT_THRESHOLDS,
the /s/-/ʃ/ boundary and its margin), so a hiss that lies in the green band is the one that scores green. The live version drawn while the
child speaks is in learner/mic.py and takes its numbers from zones() below.
Simplification (provisional, to be tuned with the content owner): three shades of one blue, a smoothed picture, no numbers on the axes.
"""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

from fricative import config as C
from fricative import vtl
from fricative.audio import limit_duration, load
from fricative.segment import SegmentationError, find_boundaries

F_LO, F_HI = 1000.0, 10000.0                # the part of the sound shown, Hz
GREEN, YELLOW, RED = (191, 227, 201), (255, 241, 184), (255, 211, 216)
BLUE = (47, 111, 228)
INK = (27, 36, 64)
SIZE = (640, 420)                           # drawn at twice the size it is shown at


DOT_COG_S_SH_HZ, DOT_MARGIN_HZ = 4240.0, 300.0     # the limit between /s/ and /ʃ/ and half the yellow band, for the centre of gravity the live dot computes (below)
DOT_F_LO, DOT_F_HI = 2000.0, 8000.0                  # the band of the live dot's centre of gravity: power-weighted, 2-8 kHz (CMU ARCTIC is 16 kHz)


def zones(phone: str, scale: float = 1.0, live: bool = False) -> dict | None:
    """The bands for a sound: `lo` and `hi` are the edges of the yellow band; `target` is the end that is green ("s" high, "sh" low).
    `scale` is the child's voice size (fricative/vtl.py), the same one the scoring uses. live=True: the bands of the live dot, which measures the centre of gravity
    its own way (the power of the spectrum between DOT_F_LO and DOT_F_HI of each screen frame), so its limit is not the scoring's: measured on 7104 /s/ and /ʃ/ of four
    ARCTIC voices (explore/pattern_lab/arctic_dot_cog.py, dot_cog_variants.py, METHOD_NOTES 8c.al). live=False: the scoring's bands (Praat measure), used for the picture after a recording."""
    if phone not in ("s", "sh"):
        return None
    if live:
        return {"lo": (DOT_COG_S_SH_HZ - DOT_MARGIN_HZ) * scale, "hi": (DOT_COG_S_SH_HZ + DOT_MARGIN_HZ) * scale, "target": phone, "f_lo": DOT_F_LO, "f_hi": DOT_F_HI}
    th = vtl.thresholds(scale)
    return {"lo": th.cog_s_sh_hz - th.cog_margin_hz, "hi": th.cog_s_sh_hz + th.cog_margin_hz, "target": phone, "f_lo": F_LO, "f_hi": F_HI}


DEFAULT_REF_DB = -28.0       # the level of a child's "aaa" when there is no Sound Check yet (word recordings of the first tries sat near -30 to -21 dBFS)


def meter_levels(phone: str, child: str | None) -> dict | None:
    """The /f/ meter. /f/ is not in a band of pitch: it is the soft one, the hiss more than 15 dB weaker than the vowel after it (the
    scoring cue, config.Thresholds.relamp_f_db and its margin). Live there is no vowel yet, so the child's own "aaa" level from Sound Check
    stands in for it. Bands in dBFS: red above ref - 15, yellow from ref - 18, green from there down to just above the room noise (at most
    ref - 33), grey below (too soft: air but no friction). Returns None for the other sounds."""
    if phone != "f":
        return None
    from fricative.calibrated import load_room, load_voice
    voice = load_voice(child)
    levels = [t["speech_db"] for t in (voice or {}).get("takes", []) if t.get("speech_db") is not None]
    ref = float(np.mean(levels)) if levels else DEFAULT_REF_DB
    noise = load_room(child) if child else None
    th = C.DEFAULT_THRESHOLDS
    green_hi, yellow_hi = ref + th.relamp_f_db - th.relamp_margin_db, ref + th.relamp_f_db
    green_lo = min(max(ref - 33.0, (noise + 8.0) if noise is not None else ref - 45.0), green_hi - 6.0)
    return {"ref": ref, "green_lo": green_lo, "green_hi": green_hi, "yellow_hi": yellow_hi, "default": not levels}


def _y(f: float, h: int) -> float:
    return h * (1 - (min(max(f, F_LO), F_HI) - F_LO) / (F_HI - F_LO))


def _font(size: int, bold: bool = True):
    for name in ("arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _bands(draw: ImageDraw.ImageDraw, w: int, h: int, z: dict) -> None:
    top_green = z["target"] == "s"
    cols = (GREEN, YELLOW, RED) if top_green else (RED, YELLOW, GREEN)       # from the top: high band, middle band, low band
    ys = (0, _y(z["hi"], h), _y(z["lo"], h), h)
    for i, c in enumerate(cols):
        draw.rectangle([0, ys[i], w, ys[i + 1]], fill=c)


def _spectrogram(sound, t0: float, t1: float, ref: tuple[float, float]):
    """Energy (0 to 1) of the part t0..t1 of the sound: rows from F_HI (top) down to F_LO, one column per 5 ms. The darkest shade is the
    loudest part of `ref` (the hiss that was measured), so a click or a vowel outside it cannot wash the hiss out."""
    fs = sound.sampling_frequency
    x = np.asarray(sound.values, dtype=float).reshape(-1)
    nfft, hop = 1024, max(1, int(fs * 0.005))
    win = np.hanning(nfft)
    a, b = max(0, int(t0 * fs)), min(len(x), int(t1 * fs))
    seg = x[a:b]
    if len(seg) < nfft:
        seg = np.pad(seg, (0, nfft - len(seg)))
    starts = range(0, len(seg) - nfft + 1, hop)
    mag = np.array([np.abs(np.fft.rfft(seg[s:s + nfft] * win)) for s in starts]).T
    freqs = np.fft.rfftfreq(nfft, 1 / fs)
    keep = (freqs >= F_LO) & (freqs <= min(F_HI, fs / 2))
    db = 20 * np.log10(np.maximum(mag[keep], 1e-9))
    centres = t0 + (np.arange(db.shape[1]) * hop + nfft / 2) / fs
    inside = (centres >= ref[0]) & (centres <= ref[1])
    top = db[:, inside].max() if inside.any() else db.max()
    lvl = np.clip((db - (top - 30)) / 30, 0, 1)
    lvl = gaussian_filter(lvl, sigma=(2.0, 1.5))
    return lvl[::-1], freqs[keep][::-1]


def render(wav: bytes, phone: str, cog_hz: float | None = None, scale: float = 1.0) -> str | None:
    """The simplified spectrogram of a recording with the target zone, as an <img> tag (None when there is no hiss to show)."""
    z = zones(phone, scale)
    if z is None:
        return None
    try:
        sound, _ = limit_duration(load(wav, "recording.wav"))
        b = find_boundaries(sound)
    except (ValueError, SegmentationError):
        return None
    t0, t1 = sound.xmin, sound.xmax              # the whole recording, on the same time axis as the live picture; the measured hiss is marked below
    w, h = SIZE
    img = Image.new("RGB", SIZE, "white")
    d = ImageDraw.Draw(img)
    _bands(d, w, h, z)
    lvl, freqs = _spectrogram(sound, t0, t1, (b.onset_s, b.offset_s))
    shades = np.digitize(lvl, [0.35, 0.6, 0.8])                         # 0 nothing, 1 light, 2 medium, 3 strong
    alpha = np.array([0.0, 0.5, 0.78, 1.0])[shades]
    # place the rows on the frequency axis (the rows are not evenly spaced in Hz at the edges, so draw them as they are)
    rgba = np.zeros((h, lvl.shape[1], 4), dtype=np.uint8)
    rows_y = np.array([_y(f, h) for f in freqs])
    for r in range(len(freqs)):
        y0 = int(rows_y[r])
        y1 = int(rows_y[r + 1]) if r + 1 < len(freqs) else h
        if y1 <= y0:
            y1 = y0 + 1
        rgba[y0:y1, :, :3] = BLUE
        rgba[y0:y1, :, 3] = (alpha[r] * 255).astype(np.uint8)
    layer = Image.fromarray(rgba, "RGBA").resize((w, h), Image.BILINEAR)
    img.paste(layer, (0, 0), layer)
    veil = Image.new("RGBA", SIZE, (255, 255, 255, 0))                          # what was not measured is faded: the child sees what the score is about
    vd = ImageDraw.Draw(veil)
    xa, xb = (b.onset_s - t0) / (t1 - t0) * w, (b.offset_s - t0) / (t1 - t0) * w
    vd.rectangle([0, 0, xa, h], fill=(255, 255, 255, 150))
    vd.rectangle([xb, 0, w, h], fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    d = ImageDraw.Draw(img)
    d.line([xa, 0, xa, h], fill=INK, width=3)
    d.line([xb, 0, xb, h], fill=INK, width=3)
    if cog_hz:                                                              # where the child's hiss sits (its centre of gravity)
        y = _y(cog_hz, h)
        x0, x1 = xa, xb
        d.line([x0, y, x1, y], fill="white", width=14)
        d.line([x0, y, x1, y], fill=INK, width=7)
        d.ellipse([x1 - 13, y - 13, x1 + 13, y + 13], fill="#FF8A00", outline="white", width=4)
    f = _font(40)
    top, bottom = ("s", "sh") if z["target"] == "s" else ("s", "sh")
    d.text((w - 20, 16), top, font=f, fill=INK, anchor="ra")
    d.text((w - 20, h - 16), bottom, font=f, fill=INK, anchor="rd")
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return (f'<img alt="Your sound as a picture" style="width:100%;height:auto;display:block;border-radius:16px;border:1.5px solid #D5DFF0" '
            f'src="data:image/png;base64,{base64.b64encode(out.getvalue()).decode("ascii")}">')
