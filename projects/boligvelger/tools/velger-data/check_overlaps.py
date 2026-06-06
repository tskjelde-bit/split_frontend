#!/usr/bin/env python3
"""Overlap / containment checker for per-floor unit polygons.

Reports the worst overlapping pair per floor and verifies units stay inside
the floor outline. Exits non-zero if any unit pair overlaps more than
MAX_OVERLAP_M2 or any unit pokes out of the outline by more than the same
threshold.

Polygon area + pairwise intersection are computed analytically via
Sutherland-Hodgman clipping (units are convex-ish simple polygons; the
clipper is exact for convex clip polygons and a close approximation for the
mildly-concave L-shapes used here, more than good enough for a 0.5 m2 gate).
No third-party deps required (shapely optional and used if present).
"""
import json
import sys
from pathlib import Path

SCALE = 0.00878  # m per crop-px (building.json)
MAX_OVERLAP_M2 = 0.5
FLOORS = Path(__file__).resolve().parent / "floors"

try:
    from shapely.geometry import Polygon  # type: ignore

    HAVE_SHAPELY = True
except Exception:
    HAVE_SHAPELY = False


def shoelace(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _ensure_ccw(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return poly if a >= 0 else poly[::-1]


def clip_area(subject, clip):
    """Area of subject ∩ clip via Sutherland-Hodgman (clip treated convex)."""
    clip = _ensure_ccw(list(clip))
    output = list(subject)
    n = len(clip)
    for i in range(n):
        if not output:
            return 0.0
        a = clip[i]
        b = clip[(i + 1) % n]
        edge = (b[0] - a[0], b[1] - a[1])

        def inside(p):
            return edge[0] * (p[1] - a[1]) - edge[1] * (p[0] - a[0]) >= 0

        def isect(p, q):
            d1 = edge[0] * (p[1] - a[1]) - edge[1] * (p[0] - a[0])
            d2 = edge[0] * (q[1] - a[1]) - edge[1] * (q[0] - a[0])
            t = d1 / (d1 - d2)
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

        new = []
        for j in range(len(output)):
            cur = output[j]
            prv = output[j - 1]
            if inside(cur):
                if not inside(prv):
                    new.append(isect(prv, cur))
                new.append(cur)
            elif inside(prv):
                new.append(isect(prv, cur))
        output = new
    if len(output) < 3:
        return 0.0
    return shoelace(output)


def intersect_area_m2(p, q):
    if HAVE_SHAPELY:
        pp, qq = Polygon(p), Polygon(q)
        if not pp.is_valid:
            pp = pp.buffer(0)
        if not qq.is_valid:
            qq = qq.buffer(0)
        return pp.intersection(qq).area * SCALE * SCALE
    return clip_area(p, q) * SCALE * SCALE


def area_outside_m2(poly, outline):
    """Area of poly that falls outside the outline."""
    full = shoelace(poly) * SCALE * SCALE
    inside = intersect_area_m2(poly, outline)
    return max(0.0, full - inside)


def main():
    fail = False
    for fid in ["u", "1", "2", "3"]:
        fpath = FLOORS / f"etasje-{fid}.json"
        if not fpath.exists():
            continue
        doc = json.loads(fpath.read_text())
        units = doc["units"]
        outline = doc["outline"]

        worst_pair = (None, 0.0)
        pairs = []
        for i in range(len(units)):
            for j in range(i + 1, len(units)):
                a = intersect_area_m2(units[i]["poly"], units[j]["poly"])
                pairs.append((units[i]["id"], units[j]["id"], a))
                if a > worst_pair[1]:
                    worst_pair = ((units[i]["id"], units[j]["id"]), a)

        worst_out = (None, 0.0)
        for u in units:
            out = area_outside_m2(u["poly"], outline)
            if out > worst_out[1]:
                worst_out = (u["id"], out)

        wp = worst_pair[0]
        print(
            f"floor {fid}: worst overlap "
            f"{wp[0] + '↔' + wp[1] if wp else 'none'} = {worst_pair[1]:.2f} m²"
            f"  | worst outside-outline {worst_out[0] or 'none'} = {worst_out[1]:.2f} m²"
        )
        for a_id, b_id, a in sorted(pairs, key=lambda t: -t[2]):
            if a > 0.05:
                flag = "  OVER" if a > MAX_OVERLAP_M2 else ""
                print(f"    {a_id}↔{b_id}: {a:.2f} m²{flag}")
        if worst_pair[1] > MAX_OVERLAP_M2:
            fail = True
        if worst_out[1] > MAX_OVERLAP_M2:
            fail = True

    print("shapely" if HAVE_SHAPELY else "shapely not installed - using built-in clipper")
    if fail:
        print("FAIL: overlaps or outline excursions exceed 0.5 m²")
        sys.exit(1)
    print("OK: all unit pairs ≤ 0.5 m² and within outline")


if __name__ == "__main__":
    main()
