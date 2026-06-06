#!/usr/bin/env python3
"""Emit one HTML file per floor: underlag PNG with floor JSON polygons overlaid."""
import base64
import json
from pathlib import Path
from struct import unpack

ROOT = Path(__file__).resolve().parents[2]
UNDERLAG = ROOT / "eiendommer/dybwads gate 8/underlag"
FLOORS = Path(__file__).resolve().parent / "floors"
QA = Path(__file__).resolve().parent / "qa"
QA.mkdir(exist_ok=True)

# etasje-u geometry is stored in floor crop-px space (transformed from the
# basement render), so its overlay is drawn on the floor-1 PNG for reference.
PNG_FOR = {
    "u": "etasje-1-plan-1.png",
    "1": "etasje-1-plan-1.png",
    "2": "etasje-2-plan-1.png",
    "3": "etasje-3-plan-1.png",
}


def svg_poly(poly, color, label="", scale=1.0):
    pts = " ".join(f"{x * scale},{y * scale}" for x, y in poly)
    cx = sum(p[0] for p in poly) / len(poly) * scale
    cy = sum(p[1] for p in poly) / len(poly) * scale
    t = (
        f'<text x="{cx}" y="{cy}" fill="{color}" font-size="40" '
        f'text-anchor="middle">{label}</text>'
        if label
        else ""
    )
    return (
        f'<polygon points="{pts}" fill="{color}" fill-opacity="0.25" '
        f'stroke="{color}" stroke-width="4"/>{t}'
    )


def main():
    for fid, png_name in PNG_FOR.items():
        fpath = FLOORS / f"etasje-{fid}.json"
        if not fpath.exists():
            continue
        doc = json.loads(fpath.read_text())
        scale = doc.get("pngScale", 1.0)
        png = UNDERLAG / png_name
        data = png.read_bytes()
        w, h = unpack(">II", data[16:24])
        b64 = base64.b64encode(data).decode()
        shapes = [svg_poly(doc["outline"], "#cc4400", scale=scale)]
        shapes += [
            svg_poly(u["poly"], "#1E7A4B", u["unit"], scale) for u in doc["units"]
        ]
        shapes += [svg_poly(c, "#3355bb", scale=scale) for c in doc.get("common", [])]
        shapes_str = "".join(shapes)
        html = (
            '<!doctype html><meta charset="utf-8">\n'
            "<style>body{margin:0} .wrap{position:relative} img{display:block;width:100%}\n"
            "svg{position:absolute;inset:0;width:100%;height:100%}</style>\n"
            f'<div class="wrap"><img src="data:image/png;base64,{b64}">\n'
            f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none">{shapes_str}</svg></div>'
        )
        out = QA / f"etasje-{fid}.html"
        out.write_text(html)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
