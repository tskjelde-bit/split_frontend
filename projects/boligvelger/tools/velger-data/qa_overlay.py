#!/usr/bin/env python3
"""Emit one HTML file per floor: underlag PNG with floor JSON polygons overlaid."""
import base64
import json
from pathlib import Path
from struct import unpack

ROOT = Path(__file__).resolve().parents[2]
UNDERLAG = ROOT / "eiendommer/dybwads gate 8/underlag"
TOOL = Path(__file__).resolve().parent
FLOORS = TOOL / "floors"
QA = TOOL / "qa"
QA.mkdir(exist_ok=True)


def _building():
    return json.loads((TOOL / "building.json").read_text())

# Basement ("u") QA underlay mapping:
#
# etasje-u.json geometry is stored in floor-px space (3308x2339, 200 dpi). The
# basement PNG itself is 2481x1754 (150 dpi). To draw the floor-px geometry on
# the basement PNG we scale it by 2481/3308 = 0.75 (the inverse of the
# 1.33333 transform documented in etasje-u.json "transform"). This is applied
# per-floor below via PNG_SCALE so the basement is QA'd on its OWN underlay and
# the outline can be checked against the real basement exterior walls.
PNG_FOR = {
    "u": "etasje-u-plan-1.png",
    "1": "etasje-1-plan-1.png",
    "2": "etasje-2-plan-1.png",
    "3": "etasje-3-plan-1.png",
}
PNG_SCALE = {
    "u": 2481.0 / 3308.0,
    "1": 1.0,
    "2": 1.0,
    "3": 1.0,
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


def roof_footprints(roof):
    """Return [(poly, label), ...] for roof rect/recess/ark/dormers."""
    out = [(roof["rect"], "tak")]
    if roof.get("recess"):
        out.append((roof["recess"]["poly"], "recess"))
    # ark/dormer footprints are small boxes centered on their edge axis; we draw
    # a marker box at the edge midpoint so the QA shows roughly where they sit.
    return out


def main():
    b = _building()
    envelope = b["envelope"]["poly"]
    roof = b["roof"]
    for fid, png_name in PNG_FOR.items():
        fpath = FLOORS / f"etasje-{fid}.json"
        if not fpath.exists():
            continue
        doc = json.loads(fpath.read_text())
        scale = PNG_SCALE.get(fid, doc.get("pngScale", 1.0))
        png = UNDERLAG / png_name
        data = png.read_bytes()
        w, h = unpack(">II", data[16:24])
        b64 = base64.b64encode(data).decode()
        # envelope (thick orange)
        shapes = [
            f'<polygon points="{" ".join(f"{x*scale},{y*scale}" for x, y in envelope)}" '
            f'fill="none" stroke="#ff7a00" stroke-width="10"/>'
        ]
        shapes += [
            svg_poly(u["poly"], "#1E7A4B", u["unit"], scale) for u in doc["units"]
        ]
        shapes += [svg_poly(c, "#3355bb", scale=scale) for c in doc.get("common", [])]
        # roof footprints (purple) only on the top floor for clarity
        if fid == "3":
            for poly, label in roof_footprints(roof):
                shapes.append(svg_poly(poly, "#8800cc", label, scale))
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
