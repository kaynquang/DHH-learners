"""Builds app/static/home_bg.jpg and app/learner/assets/mascot_wave.png from the image bot's files in this folder:
 bg_bot_v4.png   the home picture with the empty zones asked for (1024 x 572), with its eye logo replaced here by a spectrogram mark (the user's wish) and its small thinking mascot taken out
 mascot_bot_v4.png  the waving mascot on white (1024 x 1024), made transparent here
Run: python make_home_bg.py   (needs numpy, scipy, Pillow)"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__))
app = os.path.abspath(os.path.join(here, "..", "..", ".."))
bg = Image.open(os.path.join(here, "bg_bot_v4.png")).convert("RGB")
a = np.asarray(bg).astype(float)
h, w, _ = a.shape
SKY = np.array([218, 235, 253.0])

# 1. the eye of the logo goes: plain sky
a[10:115, 192:318] = SKY
a[104:118, 205:300] = SKY

# 2. the small thinking mascot goes: the columns of the clean card edge at the right of it are repeated over it (sky above, the card's top line, cream below)
src0, src_n = 250, 40
CREAM = np.array([248, 240, 217.0])
a[224:260, 58:246] = SKY
a[263:402, 58:246] = CREAM
a[260:263, 58:246] = a[260:263, 250:251]                                       # the card's top line is drawn again below, over a clean strip

img = Image.fromarray(a.astype("uint8"))

# 3. the new mark: a small spectrogram (dark panel, three formant tracks and the faint frequency grid), drawn at 6x and reduced
S = 6
big = img.resize((w * S, h * S), Image.LANCZOS)
dr = ImageDraw.Draw(big)
x0, y0, x1, y1 = 198, 20, 310, 100
dr.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=14 * S, fill=(27, 36, 64))
for gy in (36, 50, 64, 78):                                                    # the frequency grid
    dr.line([(x0 + 10) * S, gy * S, (x1 - 10) * S, gy * S], fill=(52, 66, 106), width=2 * S // 2)
xs = np.linspace(x0 + 12, x1 - 12, 120)
tracks = ((22, 6, 0.085, 0.0, (255, 200, 0)), (42, 7, 0.07, 1.6, (127, 181, 245)), (62, 5, 0.1, 3.1, (240, 124, 134)))      # (mean height, swing, frequency, phase, colour)
for mid, amp, fr, ph, col in tracks:
    ys = y0 + mid + amp * np.sin(xs * fr + ph) + 0.35 * amp * np.sin(xs * fr * 2.3 + ph)
    pts = [(float(x) * S, float(y) * S) for x, y in zip(xs, ys)]
    dr.line(pts, fill=col, width=int(4.2 * S), joint="curve")
    for p in (pts[0], pts[-1]):
        dr.ellipse([p[0] - 2.1 * S, p[1] - 2.1 * S, p[0] + 2.1 * S, p[1] + 2.1 * S], fill=col)
dr.line([(56 * S, 261.3 * S), (246 * S, 261.3 * S)], fill=(27, 36, 64), width=int(2.6 * S))
img = big.resize((w, h), Image.LANCZOS)

# 4. wider than the picture: its edge columns go on to the left and to the right (a wide window has no bars); twice the pixels
arr = np.asarray(img)
left = np.repeat(arr[:, :1], w, axis=1)
right = np.repeat(arr[:, -1:], w, axis=1)
wide = Image.fromarray(np.concatenate([left, arr, right], axis=1)).resize((w * 6, h * 2), Image.LANCZOS)
os.makedirs(os.path.join(app, "static"), exist_ok=True)
wide.save(os.path.join(app, "static", "home_bg.jpg"), quality=92, optimize=True)
print("plate", wide.size)

# 5. the mascot: the white around it becomes transparent (what is white inside it, the eyes, stays)
m = Image.open(os.path.join(here, "mascot_bot_v4.png")).convert("RGB")
ma = np.asarray(m).astype(int)
near_white = (ma.min(axis=2) > 236)
lab, n = ndi.label(near_white)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
outside = np.isin(lab, list(border))
alpha = Image.fromarray(((~outside) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.1))
rgba = m.convert("RGBA")
rgba.putalpha(alpha)
rgba = rgba.crop(rgba.getbbox())
rgba.thumbnail((720, 720), Image.LANCZOS)
rgba.save(os.path.join(app, "learner", "assets", "mascot_wave.png"), optimize=True)
print("mascot", rgba.size)
img.resize((w * 2, h * 2), Image.LANCZOS).save(os.path.join(here, "preview_bg.png"))
