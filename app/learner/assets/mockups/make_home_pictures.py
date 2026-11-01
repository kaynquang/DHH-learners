"""Builds the two pictures of the home page from the image bot's mockups in this folder, WITHOUT changing what is drawn on them (the user: "keep everything, only redraw where it is blurred"):
 home_returning.png   -> app/static/home_ret.jpg     (a child is saved)
 home_first_time.png  -> app/static/home_first.jpg   (no child yet, the first time)
Each picture is enlarged 2x and its soft edges are sharpened (unsharp mask); then its left and right edge columns are repeated, outside the picture, so that a wide
window shows no bars. Nothing inside the picture is moved, removed or added: the app only puts invisible tap areas on it (learner/home.py).
Run: python make_home_pictures.py   (needs numpy, Pillow)"""
import os

import numpy as np
from PIL import Image, ImageFilter

here = os.path.dirname(os.path.abspath(__file__))
app = os.path.abspath(os.path.join(here, "..", "..", ".."))
for name, out in (("home_returning.png", "home_ret.jpg"), ("home_first_time.png", "home_first.jpg")):
    src = Image.open(os.path.join(here, name)).convert("RGB")
    w, h = src.size
    sharp = src.resize((w * 2, h * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.8, percent=110, threshold=2))
    arr = np.asarray(sharp)
    wide = np.concatenate([np.repeat(arr[:, :1], w * 2, axis=1), arr, np.repeat(arr[:, -1:], w * 2, axis=1)], axis=1)
    Image.fromarray(wide).save(os.path.join(app, "static", out), quality=93, optimize=True)
    print(out, wide.shape[1], "x", wide.shape[0])
