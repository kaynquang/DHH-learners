"""Builds the pictures of the home page from the image bot's two mockups in this folder, so that the page can show each child's own progress while keeping the bot's drawing:
 home_first_time.png  -> app/static/home_first.jpg    the first time (no child): used as it is, only sharpened
 home_returning.png   -> app/static/home_ret.jpg      a NEUTRAL picture: every node grey (the "START" on /sh/, the check on /s/ and the star on /m/ are taken out, using the
                                                      other mockup, which has the same layout), no "first time" tag on Sound Check
                      -> app/static/home_parts/*.png  pieces cut from the bot's drawing, put back by the page when they are true: the START ribbon, the /sh/ START node,
                                                      a star, the boy and girl faces, the "first time" tag, and each node lit (done: yellow) or ready (next: light blue)
 home_parts.json      where each piece goes, in the mockups' 1024 x 572 pixels (read by learner/home.py)
Every picture is enlarged 2x and its soft edges sharpened (unsharp mask); the backgrounds are repeated at their left and right edges for wide windows.
Run: python make_home_parts.py   (needs numpy, scipy, Pillow)"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__))
app = os.path.abspath(os.path.join(here, "..", "..", ".."))
parts_dir = os.path.join(app, "static", "home_parts")
os.makedirs(parts_dir, exist_ok=True)
R = np.asarray(Image.open(os.path.join(here, "home_returning.png")).convert("RGB")).astype(float)
F = np.asarray(Image.open(os.path.join(here, "home_first_time.png")).convert("RGB")).astype(float)
h, w, _ = R.shape
yy, xx = np.mgrid[0:h, 0:w]
lum = lambda a: 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
sat = lambda a: a.max(axis=2) - a.min(axis=2)
sky_like = lambda a: (a[..., 2] - a[..., 0] > 18) & (a[..., 2] - a[..., 0] < 70) & (a[..., 0] > 190) & (a[..., 1] > 205)
sky_rows = np.array([np.median(R[y][sky_like(R)[y]], axis=0) if sky_like(R)[y].sum() > 30 else [218, 235, 253] for y in range(h)])


def refine(cx, cy, r0, img):
    """The centre and radius of a node's dark outline near (cx, cy, r0): where a circle is darkest."""
    L = lum(img)
    best = None
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            for r in range(r0 - 5, r0 + 6):
                t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
                px = np.clip((cx + dx + r * np.cos(t)).round().astype(int), 0, w - 1)
                py = np.clip((cy + dy + r * np.sin(t)).round().astype(int), 0, h - 1)
                v = L[py, px].mean()
                if best is None or v < best[0]:
                    best = (v, cx + dx, cy + dy, r)
    return tuple(int(v) for v in best[1:])


# where the nodes are (refined on the returning mockup; /sh/ and /s/ on the first-time one, where they are plain)
guess = {"see": (523, 418, 40), "she": (449, 260, 63), "fee": (598, 165, 42), "me": (598, 312, 42), "bee": (765, 190, 42), "pea": (787, 365, 42),
         "knee": (918, 312, 42), "cheat": (918, 163, 42)}
nodes = {wd: refine(*g, F if wd in ("see", "she") else R) for wd, g in guess.items()}
print("nodes", nodes)

# the first-time mockup is a little lighter: map its colours to the returning one, fitted on nodes drawn the same in both
fit = np.zeros((h, w), bool)
for wd in ("fee", "bee", "cheat", "knee", "pea"):
    cx, cy, r = nodes[wd]
    fit |= (xx - cx) ** 2 + (yy - cy) ** 2 <= (r - 3) ** 2
coef = [np.polyfit(F[..., c][fit], R[..., c][fit], 1) for c in range(3)]
Fm = np.stack([np.clip(coef[c][0] * F[..., c] + coef[c][1], 0, 255) for c in range(3)], axis=2)
print("colour map first->returning", [(round(a, 3), round(b, 1)) for a, b in coef])

B = R.copy()
# /sh/: the START node goes, the plain grey node of the first-time mockup comes (its left edge, under that mockup's speech bubble, is the mirror of its right edge)
cx, cy, r = nodes["she"]
box = (yy >= 108) & (yy <= 362) & (xx >= 358) & (xx <= 536)
inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r + 3) ** 2
mir = Fm[yy, np.clip(2 * cx - xx, 0, w - 1)]
B = np.where((box & inside & (xx < cx - 40))[..., None], mir, B)
B = np.where((box & inside & (xx >= cx - 40))[..., None], Fm, B)
outside = box & ~inside
keep_f = outside & (yy >= 326) & ~sky_like(F)                     # the dotted path below the node
B = np.where((outside & ~keep_f)[..., None], sky_rows[:, None, :], B)
B = np.where(keep_f[..., None], F, B)
# /s/: the check goes, the plain grey node comes, without its "NEXT" ribbon (the top of its ring is the mirror of the bottom)
cx, cy, r = nodes["see"]
mcx, mcy, mr = nodes["me"]
inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r + 3) ** 2
ribbon = (yy >= 338) & (yy <= cy) & (xx >= cx - 36) & (xx <= cx + 38)
box = (((xx - cx) ** 2 + (yy - cy) ** 2 <= (r + 9) ** 2) | ribbon) & ((xx - mcx) ** 2 + (yy - mcy) ** 2 > (mr + 8) ** 2) & (yy <= cy + r + 6)
top = inside & (yy < cy - 0.62 * r)
B = np.where((box & inside & ~top)[..., None], Fm, B)
B = np.where((box & top)[..., None], Fm[np.clip(2 * cy - yy, 0, h - 1), xx], B)
outside = box & ~inside
B = np.where((outside & (yy < cy - 4))[..., None], sky_rows[:, None, :], B)
B = np.where((outside & (yy >= cy - 4))[..., None], F, B)
# /m/: its little star goes (the mirror of the other side of the node; the centre as drawn, x = 598)
cx, cy = 598, nodes["me"][1]
star = (xx >= cx + 16) & (xx <= cx + 48) & (yy >= cy + 12) & (yy <= cy + 42)
B = np.where(star[..., None], B[yy, np.clip(2 * cx - xx, 0, w - 1)], B)
# Sound Check keeps its "first time" tag and its check as the bot drew them (taking the tag out left a visible patch over the box's corner)


def sharpen2x(img):
    im = Image.fromarray(np.clip(img, 0, 255).astype("uint8")) if isinstance(img, np.ndarray) else img
    return im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.8, percent=110, threshold=2))


def background(img, name):
    arr = np.asarray(sharpen2x(img))
    wide = np.concatenate([np.repeat(arr[:, :1], arr.shape[1], axis=1), arr, np.repeat(arr[:, -1:], arr.shape[1], axis=1)], axis=1)
    Image.fromarray(wide).save(os.path.join(app, "static", name), quality=93, optimize=True)


background(B, "home_ret.jpg")
background(F, "home_first.jpg")
Image.fromarray(B.astype("uint8")).resize((w * 2, h * 2), Image.LANCZOS).save(os.path.join(here, "preview_neutral.png"))

meta = {"nodes": {}}


def piece(arr, alpha, x0, y0, name):
    """Save a cut piece (RGB + alpha, 2x, sharpened) and where it goes."""
    rgba = np.dstack([np.clip(arr, 0, 255), np.clip(alpha, 0, 1) * 255]).astype("uint8")
    im = Image.fromarray(rgba, "RGBA")
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.8, percent=110, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(im.split()[3])
    out.save(os.path.join(parts_dir, name + ".png"), optimize=True)
    return {"x": x0, "y": y0, "w": arr.shape[1], "h": arr.shape[0]}


def soft_disk(cx, cy, r, x0, y0, x1, y1):
    d = np.sqrt((xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2)
    return np.clip(r + 0.5 - d, 0, 1)


def recolour(region, light, dark):
    """The grey of a node's disk becomes a colour (light where it was light), its navy lines stay."""
    L, S = lum(region), sat(region)
    disk = (S < 60) & (L > 118)
    t = np.clip((L - 118) / (200 - 118), 0, 1)[..., None]
    col = np.array(dark) * (1 - t) + np.array(light) * t
    return np.where(disk[..., None], col, region)


for wd, (cx, cy, r) in nodes.items():
    rr = r + 4
    x0, y0, x1, y1 = cx - rr, cy - rr, cx + rr + 1, cy + rr + 1
    region = B[y0:y1, x0:x1]
    a = soft_disk(cx, cy, rr, x0, y0, x1, y1)
    meta["nodes"][wd] = {"cx": cx, "cy": cy, "r": r,
                         "lit": piece(recolour(region, (255, 236, 150), (238, 190, 60)), a, x0, y0, f"lit_{wd}"),
                         "ready": piece(recolour(region, (214, 230, 255), (150, 186, 245)), a, x0, y0, f"ready_{wd}")}

# the START ribbon of the /sh/ node, and that whole node as the bot drew it
cx, cy, r = nodes["she"]
x0, y0, x1, y1 = 360, 112, 536, 214
reg = R[y0:y1, x0:x1]
a = (~sky_like(reg)).astype(float) * (((xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2) > (r + 6) ** 2)
a = ndi.gaussian_filter(ndi.binary_opening(a > 0, iterations=1).astype(float), 0.6)
meta["start"] = piece(reg, a, x0, y0, "start")
x0, y0, x1, y1 = 356, 112, 538, 330
reg = R[y0:y1, x0:x1]
a = ndi.gaussian_filter(ndi.binary_fill_holes(ndi.binary_closing(~sky_like(reg), iterations=2)).astype(float), 0.6)
meta["she_start"] = piece(reg, a, x0, y0, "she_start")
# a star (the first of the three under the /sh/ node)
reg_box = R[326:360, 400:440]
yel = (reg_box[..., 0] > 180) & (reg_box[..., 1] > 140) & (reg_box[..., 2] < 120)
lab, n = ndi.label(ndi.binary_dilation(yel, iterations=2))
first = lab == lab[np.nonzero(yel)[0][0], np.nonzero(yel)[1][0]]
ys_, xs_ = np.nonzero(first)
sx0, sy0, sx1, sy1 = 400 + xs_.min(), 326 + ys_.min(), 400 + xs_.max() + 1, 326 + ys_.max() + 1
reg = R[sy0:sy1, sx0:sx1]
a = ndi.gaussian_filter((first[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1] & ~sky_like(reg)).astype(float), 0.5)
meta["star"] = piece(reg, a, sx0, sy0, "star")
# the boy in the banner, and a girl made from the girl of the /sh/ node on the same round face
ax, ay, ar = refine(388, 40, 30, R)
x0, y0, x1, y1 = ax - ar - 3, ay - ar - 3, ax + ar + 4, ay + ar + 4
boy = R[y0:y1, x0:x1]
a = soft_disk(ax, ay, ar + 3, x0, y0, x1, y1)
meta["boy"] = piece(boy, a, x0, y0, "boy")
face = boy.copy()
inner = ((xx[y0:y1, x0:x1] - ax) ** 2 + (yy[y0:y1, x0:x1] - ay) ** 2) <= (ar - 3) ** 2
cream = np.median(boy[inner & (lum(boy) > 200) & (sat(boy) < 60)], axis=0)
face[inner] = cream
gx0, gy0, gx1, gy1 = 404, 198, 496, 300
girl = R[gy0:gy1, gx0:gx1]
disk = (girl[..., 2] - girl[..., 0] > 60) & (girl[..., 2] > 150)
ga = (~disk).astype(float)
gimg = Image.fromarray(np.dstack([girl, ga * 255]).astype("uint8"), "RGBA")
size = int((ar - 3) * 2 * 0.98)
gimg = gimg.resize((size, int(size * gimg.height / gimg.width)), Image.LANCZOS)
base = Image.fromarray(face.astype("uint8")).convert("RGBA")
base.alpha_composite(gimg, (int(ax - x0 - size / 2), int(ay - y0 - ar + 6)))
gface = np.asarray(base.convert("RGB")).astype(float)
gface = np.where(inner[..., None], gface, boy)
meta["girl"] = piece(gface, a, x0, y0, "girl")
# colours the page needs for its patches
meta["banner_rgb"] = [int(v) for v in np.median(R[30:50, 560:585].reshape(-1, 3), axis=0)]
meta["card_rgb"] = [int(v) for v in np.median(R[512:528, 80:105].reshape(-1, 3), axis=0)]
meta["box_rgb"] = [int(v) for v in np.median(R[506:520, 760:780].reshape(-1, 3), axis=0)]
json.dump(meta, open(os.path.join(here, "..", "..", "home_parts.json"), "w"), indent=1, default=int)
print("pieces", sorted(os.listdir(parts_dir)))
print("banner", meta["banner_rgb"], "card", meta["card_rgb"], "box", meta["box_rgb"])
