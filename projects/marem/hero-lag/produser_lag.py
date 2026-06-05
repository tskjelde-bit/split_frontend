#!/usr/bin/env python3
"""Produce hero assembly layers via gpt-image-1 edits API.

Reads 00-master.png, runs one edit job per asset (parallel), saves PNGs here.
Background plate is opaque; all object layers get transparent background.
"""
import base64
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "00-master.png")
KEY = subprocess.run(
    ["security", "find-generic-password", "-s", "OPENAI_API_KEY", "-w"],
    capture_output=True, text=True,
).stdout.strip()
if not KEY:
    sys.exit("no OPENAI_API_KEY in keychain")

CUTOUT = (
    "From this image, isolate ONLY {obj}. Output the exact same canvas size and "
    "aspect ratio as the input, with {obj} in its exact original position and "
    "scale, completely unchanged in appearance and lighting{shadow}. Everything "
    "else in the image must be removed and fully transparent."
)

JOBS = [
    (
        "01-bakgrunn.png",
        "Remove ALL furniture and objects from this living room: the sofa with "
        "pillows, the marble coffee table with flowers and books, both floor "
        "lamps, both small side tables, the armchair on the right, the small "
        "stool in the left corner, the blue artwork on the left wall, and the "
        "chandelier. Keep ONLY the empty room: walls, ceiling, windows, "
        "curtains, and the herringbone parquet floor — all unchanged in "
        "position, lighting and color. Fill the removed areas naturally and "
        "photorealistically. Do not move the camera. Same resolution and "
        "aspect ratio as the input.",
        False,
    ),
    ("02-lysekrone.png", CUTOUT.format(obj="the chandelier hanging from the ceiling", shadow=""), True),
    ("03-kunst.png", CUTOUT.format(obj="the blue artwork hanging on the left wall", shadow=""), True),
    ("04-lampe-venstre.png", CUTOUT.format(obj="the LEFT floor lamp and the small side table beneath it", shadow=", including their soft floor shadows"), True),
    ("05-lampe-hoyre.png", CUTOUT.format(obj="the RIGHT floor lamp and the small side table beneath it", shadow=", including their soft floor shadows"), True),
    ("06-lenestol.png", CUTOUT.format(obj="the armchair at the right edge of the image", shadow=", including its soft floor shadow"), True),
    ("07-sofa.png", CUTOUT.format(obj="the sofa with all its pillows and legs", shadow=", including its soft floor shadow"), True),
    ("08-bord.png", CUTOUT.format(obj="the marble coffee table with the flower vase, books and objects on it", shadow=", including its soft floor shadow"), True),
]


def produce(name: str, prompt: str, transparent: bool) -> str:
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1536x1024",
        "quality": "high",
        "n": "1",
    }
    if transparent:
        data["background"] = "transparent"
    with open(MASTER, "rb") as f:
        r = requests.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {KEY}"},
            data=data,
            files={"image": ("master.png", f, "image/png")},
            timeout=600,
        )
    if r.status_code != 200:
        return f"FAIL {name}: {r.status_code} {r.text[:200]}"
    b64 = r.json()["data"][0]["b64_json"]
    with open(os.path.join(HERE, name), "wb") as out:
        out.write(base64.b64decode(b64))
    return f"OK   {name}"


if __name__ == "__main__":
    only = sys.argv[1:]  # optionally pass filenames to (re)produce
    jobs = [j for j in JOBS if not only or j[0] in only]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(produce, *j): j[0] for j in jobs}
        for fut in as_completed(futs):
            print(fut.result(), flush=True)
    print("done")
