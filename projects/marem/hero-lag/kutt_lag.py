#!/usr/bin/env python3
"""Cut furniture layers locally from the master frame.

For each object: crop its bounding box from 00-master.png, run rembg
(salient object matting) on the crop, paste the result into a full-canvas
transparent PNG. Pixels are the master's own — position and look are exact.
"""
import os

from PIL import Image
from rembg import remove, new_session

HERE = os.path.dirname(os.path.abspath(__file__))
master = Image.open(os.path.join(HERE, "00-master.png")).convert("RGBA")
W, H = master.size
print("master:", W, "x", H)

session = new_session("isnet-general-use")

# name -> bbox as fractions (x0, y0, x1, y1) of the master canvas
LAYERS = {
    "02-lysekrone": (0.40, 0.00, 0.60, 0.30),
    "03-kunst": (0.000, 0.18, 0.105, 0.80),
    "04-lampe-venstre": (0.115, 0.48, 0.245, 0.88),
    "05-lampe-hoyre": (0.745, 0.48, 0.885, 0.88),
    "06-lenestol": (0.885, 0.64, 1.000, 0.95),
    "07-sofa": (0.300, 0.56, 0.725, 0.87),
    "08-bord": (0.395, 0.655, 0.665, 0.99),
}

for name, (fx0, fy0, fx1, fy1) in LAYERS.items():
    x0, y0, x1, y1 = int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H)
    crop = master.crop((x0, y0, x1, y1))
    cut = remove(crop, session=session)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(cut, (x0, y0), cut)
    # downscale to web size (1920w) to keep payload sane
    canvas = canvas.resize((1920, int(1920 * H / W)), Image.LANCZOS)
    canvas.save(os.path.join(HERE, f"{name}.png"))
    print("cut", name)

print("done")
