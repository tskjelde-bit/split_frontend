#!/usr/bin/env python3
"""Fjerne-kjede v3: per-steg beskyttede accept-regioner + dominant-containment.

v1 råtnet (global aksept -> kunst-akkumulering). v2 låste aksept til
møbleringsregionen, men fortsatt-tilstedeværende objekter (vase, puter,
lampe) kunne re-rendres innenfor den. v3 beskytter dem per steg:
  region(steg s) = møbleringsregion
                   minus masker for grupper som fortsatt er fullt til stede
                   (unntatt overlapp med steg-objektets dilaterte maske,
                    så rekonstruksjon bak objektet ikke blokkeres).
Masker hentes fra furnish/<scene>/masks.npz + groups-<scene>.json.

Bruk: chain_v2.py <scene1|scene2> [--one]
--one: kjør kun neste manglende steg og avslutt. Resume: ferdige steg hoppes over.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PY = sys.executable

Image.MAX_IMAGE_PIXELS = None

RECON_RUG = (" Reconstruct the rug seamlessly where it was standing - the rug's"
             " pattern simply continues underneath, with no marks, no debris and"
             " no wooden floor showing through the rug.")
RECON_WALL = (" Reconstruct the wall, curtains and floor behind it cleanly - a"
              " smooth wall with no marks, shadows, outlines or ghosting.")

CHAINS = {
    "scene1": {
        "full": "scene1-steps/scene1-00-full.png",
        "out": "scene1-steps-v2",
        "steps": [
            ("01-uten-dekor", "all the table decor: the flowers, the vases, the books and small objects on the coffee table and the glass side table. Reconstruct the table surfaces cleanly"),
            ("02-uten-hvitt-bord", "the white marble coffee table on the rug." + RECON_RUG),
            ("03-uten-glassbord", "the glass side table between the black armchairs." + RECON_RUG),
            ("04-uten-stol-fremst", "the black leather armchair closest to the camera on the right." + RECON_WALL),
            ("05-uten-stol-bak", "the other black leather armchair by the right window." + RECON_WALL),
            ("06-uten-pledd", "the orange patterned throw blanket draped over the black daybed. Reconstruct the daybed's black leather surface cleanly underneath"),
            ("07-uten-daybed", "the black leather daybed on the left. Keep the table lamp with the white shade exactly as it is." + RECON_RUG),
            ("08-uten-lampe", "the table lamp with the white shade on the left"),
            ("09-uten-vase", "the blue and white porcelain jar on top of the blue cabinet. Reconstruct the cabinet's top surface cleanly"),
            ("10-uten-skap", "the blue patterned cabinet by the right window." + RECON_WALL),
            ("11-uten-sofa", "the cognac leather sofa with all its pillows." + RECON_RUG),
            ("12-base", "the large cream area rug and the newspaper lying on the floor, leaving the herringbone wooden floor completely empty and clean"),
        ],
    },
    "scene2": {
        "full": "scene2-steps/scene2-00-full.png",
        "out": "scene2-steps-v2",
        "steps": [
            ("01-uten-dekor", "all the decor on the tables: the flowers, the vase, the books and trays. Reconstruct the table surfaces cleanly"),
            ("02-uten-hvitt-bord", "the white square coffee table on the rug." + RECON_RUG),
            ("03-uten-svart-bord", "the small round side table between the armchairs on the right." + RECON_RUG),
            ("04-uten-lenestol-h", "the cream barrel armchair on the far right." + RECON_RUG),
            ("05-uten-lenestol-v", "the other cream barrel armchair, to the left of the far-right one." + RECON_RUG),
            ("06-uten-lamper", "both tall floor lamps with white shades by the windows"),
            ("07-uten-midtsofa", "the large white sofa in the center facing the camera." + RECON_RUG),
            ("08-uten-venstresofa", "the white sofa on the left side." + RECON_RUG),
            ("09-base", "the large light area rug, leaving the wooden floor completely empty and clean"),
        ],
    },
}


def step_regions(scene: str) -> dict[int, Path]:
    """Per-steg accept-region: møbleringsregion minus beskyttede grupper.

    Beskyttet ved steg s = grupper der ALLE diff_steps > s (fortsatt fullt
    til stede), minus overlapp med steg-eierens dilaterte maske (ellers
    blokkeres rekonstruksjonen bak objektet, f.eks. teppe under stol).
    """
    cfg = json.loads((HERE / f"groups-{scene}.json").read_text())
    z = np.load(HERE / "furnish" / scene / "masks.npz")
    F = ndimage.distance_transform_edt(~(z["furniture"] > 0)) <= 60
    masks = [z[f"mask_{i:02d}"] > 0 for i in range(len(cfg["groups"]))]
    owner = {}
    for gi, g in enumerate(cfg["groups"]):
        for s in g["diff_steps"]:
            owner[s] = gi
    out = {}
    rdir = HERE / "furnish" / scene
    for s, gi in owner.items():
        allowed = F.copy()
        own = ndimage.binary_dilation(masks[gi], iterations=12)
        for gj, g in enumerate(cfg["groups"]):
            if min(g["diff_steps"]) > s:
                allowed &= ~(masks[gj] & ~own)
        p = rdir / f"region-{s:02d}.png"
        Image.fromarray((allowed * 255).astype(np.uint8)).save(p)
        out[s] = p
    return out


def main() -> None:
    scene = sys.argv[1]
    one = "--one" in sys.argv
    cfg = CHAINS[scene]
    out_dir = HERE / cfg["out"]
    out_dir.mkdir(exist_ok=True)
    regions = step_regions(scene)
    prev = out_dir / f"{scene}-00-full.png"
    if not prev.exists():
        prev.write_bytes((HERE / cfg["full"]).read_bytes())
    for name, desc in cfg["steps"]:
        dest = out_dir / f"{scene}-{name}.png"
        if dest.exists():
            prev = dest
            continue
        s = int(re.match(r"(\d+)", name).group(1))
        print(f"== {scene}-{name}: {desc[:70]}")
        for attempt in range(3):
            r = subprocess.run(
                [PY, str(HERE / "nb_remove.py"), str(prev), str(dest), desc,
                 f"--accept-region={regions[s]}", "--dominant"])
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
