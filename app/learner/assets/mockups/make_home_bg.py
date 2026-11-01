"""Builds app/static/home_bg.jpg (the background of the home page) from the image bot's home picture home_v5_path.png (1024 x 572) in this folder.
(The earlier version, from the bot's clean plate bg_bot_v4.png with a spectrogram mark, is make_home_bg_v4.py.)

What the app draws itself is taken out of the picture: the contents of the top banner (flat banner colour), the path, nodes, labels and stars (the sky of each row),
the two quick buttons (the right hill is drawn again), the "Continue" button and the words under it (card colour). The mascot is kept whole: every pixel of it and of its
outline is protected while the button under its feet is taken away, so that its feet keep their lines. The picture is then repeated at its left and right edges
(a wide window has no bars) and doubled in size.
SPECTROGRAM = True replaces the eye of the logo by a small spectrogram mark (the user asked for it once; off: this picture is used as it is).
Run: python make_home_bg.py   (needs numpy, scipy, Pillow)"""
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SPECTROGRAM = False
here = os.path.dirname(os.path.abspath(__file__))
app = os.path.abspath(os.path.join(here, "..", "..", ".."))
src = Image.open(os.path.join(here, "home_v5_path.png")).convert("RGB")
orig = np.asarray(src).astype(float)
a = orig.copy()
h, w, _ = a.shape
R, G, B = orig[..., 0], orig[..., 1], orig[..., 2]

# 1. the banner keeps its shape, loses what is written on it
banner = np.median(orig[15:50, 700:790].reshape(-1, 3), axis=0)
a[4:73, 350:1018] = banner

# 2. the sky behind the path, nodes, labels and quick buttons: the colour of the sky of each row (it only changes from top to bottom)
sky_like = (B - R > 18) & (B - R < 70) & (R > 190) & (G > 205)
field = np.zeros((h, w), bool)
for x0, y0, x1, y1 in ((335, 92, 900, 452), (900, 92, 1024, 428), (470, 380, 585, 505), (640, 444, 1024, 540)):
    field[y0:y1, x0:x1] = True
use = sky_like & ~field
use[:, :330] = False
rows = np.full((h, 3), np.nan)
for y in range(h):
    px = orig[y][use[y]]
    if len(px) > 30:
        rows[y] = np.median(px, axis=0)
ok = ~np.isnan(rows[:, 0])
ys = np.arange(h)
for c in range(3):
    rows[:, c] = np.interp(ys, ys[ok], rows[ok, c])
rows = ndi.gaussian_filter1d(rows, 6, axis=0)
a = np.where(field[..., None], rows[:, None, :], a)

# 3. the card: the button and the words under it become card colour, but not the mascot. The mascot is its light blue (not the darker blue of the button),
#    with the holes of its eyes and mouth filled, grown by 3 pixels so that its navy outline is part of it.
cream = np.median(orig[300:340, 60:90].reshape(-1, 3), axis=0)
body = (B - R > 60) & (G > 110) & (R < 185)
body[:, :40] = False
body[:, 330:] = False
body[:225, :] = False
body[445:, :] = False
lab, n = ndi.label(body)
sizes = ndi.sum(body, lab, range(1, n + 1))
mascot = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 40])
mascot = ndi.binary_fill_holes(ndi.binary_closing(mascot, iterations=2))
keep = ndi.binary_dilation(mascot, iterations=3)
card = np.zeros((h, w), bool)
card[416:531, 50:320] = True                                                # the card's own bottom line (y 533-540) stays
a[card & ~keep] = cream

img = Image.fromarray(a.astype("uint8"))
S = 4
big = img.resize((w * S, h * S), Image.LANCZOS)
dr = ImageDraw.Draw(big)

# 4. the right hill is drawn again over the sky colour that replaced the quick buttons
hill_green = tuple(int(v) for v in np.median(orig[436:470, 990:1020].reshape(-1, 3), axis=0))
pts = [(600, 548), (690, 516), (780, 480), (870, 452), (940, 433), (1024, 428)]
dr.polygon([(x * S, y * S) for x, y in pts] + [(1024 * S, 540 * S), (600 * S, 540 * S)], fill=hill_green)
dr.line([(x * S, y * S) for x, y in pts], fill=(27, 36, 64), width=3 * S)

# 5. (optional) the spectrogram mark in place of the eye
if SPECTROGRAM:
    sky = tuple(int(v) for v in rows[60])
    dr.rectangle([118 * S, 22 * S, 196 * S, 104 * S], fill=sky)
    x0, y0, x1, y1 = 104, 30, 196, 100
    dr.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=12 * S, fill=(27, 36, 64))
    xs = np.linspace(x0 + 10, x1 - 10, 100)
    for mid, amp, fr, ph, col in ((18, 5, 0.1, 0.0, (255, 200, 0)), (36, 6, 0.08, 1.6, (127, 181, 245)), (54, 4, 0.12, 3.1, (240, 124, 134))):
        yv = y0 + mid + amp * np.sin(xs * fr + ph)
        dr.line([(float(x) * S, float(y) * S) for x, y in zip(xs, yv)], fill=col, width=4 * S, joint="curve")

img = big.resize((w, h), Image.LANCZOS)

# 6. wider than the picture (edge columns repeated left and right), twice the pixels
arr = np.asarray(img)
wide = Image.fromarray(np.concatenate([np.repeat(arr[:, :1], w, axis=1), arr, np.repeat(arr[:, -1:], w, axis=1)], axis=1)).resize((w * 6, h * 2), Image.LANCZOS)
os.makedirs(os.path.join(app, "static"), exist_ok=True)
wide.save(os.path.join(app, "static", "home_bg.jpg"), quality=92, optimize=True)
img.resize((w * 2, h * 2), Image.LANCZOS).save(os.path.join(here, "preview_bg.png"))
img.crop((30, 230, 340, 545)).resize((930, 945), Image.LANCZOS).save(os.path.join(here, "preview_card.png"))
print("plate", wide.size, "mascot pixels kept", int(keep.sum()))
