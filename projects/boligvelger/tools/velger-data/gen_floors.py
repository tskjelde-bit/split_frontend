#!/usr/bin/env python3
"""Generate initial floor JSON skeletons from plantegning specs + crop positions.

Unit polygons = spec envelope translated by crop_px offset. Floor outline =
bbox hull placeholder, to be hand-traced against underlag PNG.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "tools/plantegning/specs"
UNITS = json.loads((ROOT / "tools/plantegning/units.json").read_text())
OUT = Path(__file__).resolve().parent / "floors"
OUT.mkdir(exist_ok=True)


def main():
    floors = {}
    for hnr, u in UNITS.items():
        spec = json.loads((SPECS / f"{hnr}.json").read_text())
        x0, y0, _, _ = u["crop_px"]
        poly = [[round(x0 + px), round(y0 + py)] for px, py in spec["envelope"]]
        floors.setdefault(str(u["floor"]), []).append(
            {"id": hnr, "unit": hnr, "poly": poly}
        )
    for fid, units in floors.items():
        xs = [p[0] for un in units for p in un["poly"]]
        ys = [p[1] for un in units for p in un["poly"]]
        doc = {
            "id": fid,
            "pngScale": 1.0,
            "outline": [
                [min(xs), min(ys)],
                [max(xs), min(ys)],
                [max(xs), max(ys)],
                [min(xs), max(ys)],
            ],
            "units": units,
            "common": [],
        }
        path = OUT / f"etasje-{fid}.json"
        path.write_text(json.dumps(doc, indent=1))
        print(f"wrote {path.name}: {len(units)} units")


if __name__ == "__main__":
    main()
