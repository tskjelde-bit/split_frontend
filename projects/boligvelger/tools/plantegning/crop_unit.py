"""Crop per-enhet PNG fra etasje-underlag. Bruk: crop_unit.py H0101"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand


def main():
    uid = sys.argv[1]
    units = json.loads((Path(__file__).parent / "units.json").read_text())
    u = units[uid]
    x, y, w, h = u["crop_px"]
    src = brand.UNDERLAG / f"etasje-{u['floor']}-plan-1.png"
    out = brand.UNDERLAG / f"{uid}-crop.png"
    subprocess.run(
        ["magick", str(src), "-crop", f"{w}x{h}+{x}+{y}", "+repage", str(out)],
        check=True,
    )
    print(out)


if __name__ == "__main__":
    main()
