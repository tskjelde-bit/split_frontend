#!/usr/bin/env python3
"""Fjerne-kjede v2: stedsbegrenset (accept-region) + dominant-containment.

v1-kjeden råtnet fordi containment godtok alle endringsklynger uansett
posisjon (kunst/vinduer akkumulerte) og vibrasjon ble bakt inn. v2 låser
aksept til møbleringsregionen og dominant klynge per steg.

Bruk: chain_v2.py <scene1|scene2> [--one]
--one: kjør kun neste manglende steg og avslutt (for korte Bash-kall).
Resume: ferdige steg hoppes over. Region bygges fra furnish/<scene>/masks.npz
(furniture-union, dilatert 60 px) første gang.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PY = sys.executable

Image.MAX_IMAGE_PIXELS = None

CHAINS = {
    "scene1": {
        "full": "scene1-steps/scene1-00-full.png",
        "out": "scene1-steps-v2",
        "steps": [
            ("01-uten-dekor", "all the table decor: the flowers, the vases, the books and small objects on the coffee table and the glass side table"),
            ("02-uten-hvitt-bord", "the white marble coffee table on the rug"),
            ("03-uten-glassbord", "the glass side table between the black armchairs"),
            ("04-uten-stol-fremst", "the black leather armchair closest to the camera on the right"),
            ("05-uten-stol-bak", "the other black leather armchair by the right window"),
            ("06-uten-pledd", "the orange patterned throw blanket draped over the black daybed"),
            ("07-uten-daybed", "the black leather daybed on the left"),
            ("08-uten-lampe", "the table lamp with the white shade on the left"),
            ("09-uten-vase", "the blue and white porcelain jar on top of the blue cabinet"),
            ("10-uten-skap", "the blue patterned cabinet by the right window"),
            ("11-uten-sofa", "the cognac leather sofa with all its pillows"),
            ("12-base", "the large cream area rug and the newspaper lying on the floor, leaving the herringbone wooden floor completely empty"),
        ],
    },
    "scene2": {
        "full": "scene2-steps/scene2-00-full.png",
        "out": "scene2-steps-v2",
        "steps": [
            ("01-uten-dekor", "all the decor on the tables: the flowers, the vase, the books and trays"),
            ("02-uten-hvitt-bord", "the white square coffee table on the rug"),
            ("03-uten-svart-bord", "the small round side table between the armchairs on the right"),
            ("04-uten-lenestol-h", "the cream barrel armchair on the far right"),
            ("05-uten-lenestol-v", "the other cream barrel armchair, to the left of the far-right one"),
            ("06-uten-lamper", "both tall floor lamps with white shades by the windows"),
            ("07-uten-midtsofa", "the large white sofa in the center facing the camera"),
            ("08-uten-venstresofa", "the white sofa on the left side"),
            ("09-base", "the large light area rug, leaving the wooden floor completely empty"),
        ],
    },
}


def ensure_region(scene: str) -> Path:
    out = HERE / "furnish" / scene / "accept-region.png"
    if out.exists():
        return out
    z = np.load(HERE / "furnish" / scene / "masks.npz")
    furn = z["furniture"] > 0
    region = ndimage.distance_transform_edt(~furn) <= 60
    Image.fromarray((region * 255).astype(np.uint8)).save(out)
    print(f"accept-region bygget: {out.name} ({region.mean() * 100:.1f}% av flaten)")
    return out


def main() -> None:
    scene = sys.argv[1]
    one = "--one" in sys.argv
    cfg = CHAINS[scene]
    out_dir = HERE / cfg["out"]
    out_dir.mkdir(exist_ok=True)
    region = ensure_region(scene)
    prev = out_dir / f"{scene}-00-full.png"
    if not prev.exists():
        prev.write_bytes((HERE / cfg["full"]).read_bytes())
    for name, desc in cfg["steps"]:
        dest = out_dir / f"{scene}-{name}.png"
        if dest.exists():
            prev = dest
            continue
        print(f"== {scene}-{name}: {desc[:70]}")
        for attempt in range(3):
            r = subprocess.run(
                [PY, str(HERE / "nb_remove.py"), str(prev), str(dest), desc,
                 f"--accept-region={region}", "--dominant"])
            if r.returncode == 0:
                break
            print(f"  forsøk {attempt + 1} feilet (exit {r.returncode}), prøver igjen")
            dest.unlink(missing_ok=True)
        else:
            sys.exit(f"steg {name} feilet etter 3 forsøk")
        prev = dest
        if one:
            return
    print(f"{scene}: alle steg ferdig")


if __name__ == "__main__":
    main()
