"""Parametrisk plantegnings-generator.

Enheter beskrives som ren geometri-data (JSON-spec i cm), og denne modulen
genererer korrekt SVG: veggmasse som én even-odd-fylt polygon (alle hjørner
lukker per konstruksjon), parametriske dørslag, vinduer og innredning.

Spec-format (alle koordinater i cm, origo = ytre NV-hjørne):
{
  "envelope": [[x,y], ...],                 # ytre omriss, polygon med klokka
  "rooms": [
    {"name": "Stue/sov", "area": "10,9", "poly": [[x,y],...], "kind": "rom"},
    {"name": "Bad", "area": "3,4", "poly": [...], "kind": "bad"}
  ],
  "openings": [                              # dør-/passasjeåpninger gjennom vegg
    {"rect": [x,y,w,h],                      # rect som dekker veggtverrsnittet
     "door": {"hinge": [x,y], "width": 80,   # utelat "door" for åpen passasje
              "angle": 0, "sweep": 1}}       # angle: 0=blad mot øst, 90=sør osv.
  ],
  "windows": [ {"rect": [x,y,w,h]} ],        # rect = vindusfelt i yttervegg
  "fixtures": [ {"sym": "wc", "x": 0, "y": 0, "rot": 0} ],
  "extras": [ {"type": "bench", "rect": [x,y,w,h]},          # kjøkkenbenk o.l.
              {"type": "ladder", "rect": [x,y,w,h]},         # stige til hems
              {"type": "dashed", "poly": [[x,y],...]},       # hems-avgrensning
              {"type": "label", "text": "Kjøkken", "x": 0, "y": 0, "rot": 0} ],
  "labels": [ {"name": "Gang", "area": "2,9", "x": 83, "y": 110} ],
  "hems": {"poly": [[x,y],...], "area": "3,5",                # egen hems-tegning
           "hatch": [[x,y],...] }                             # valgfri luke (stiplet)
}
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand

INK = brand.INK
ROOM = brand.ROOM_FILL
BAD = brand.TILE_FILL
CREAM = brand.CREAM
HEMS = brand.HEMS_FILL


def _pts(poly):
    return " ".join(f"{x:.0f},{y:.0f}" for x, y in poly)


def _path(poly):
    d = f"M {poly[0][0]:.0f} {poly[0][1]:.0f} "
    d += " ".join(f"L {x:.0f} {y:.0f}" for x, y in poly[1:])
    return d + " Z"


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _point_in_poly(pt, poly):
    x, y = pt
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


SYM_SIZE = {  # (w, h) i cm for validering
    "wc": (40, 65), "servant": (50, 40), "dusj": (90, 90), "seng140": (140, 200),
    "sofa": (160, 85), "bord2": (120, 115), "komfyr": (60, 60), "kvask": (60, 60),
    "skap": (60, 60), "rundbord90": (90, 90), "sofabord60": (60, 60),
    "lenestol": (70, 70), "stol": (45, 45),
}


def validate(spec: dict) -> list[str]:
    """Returner liste med problemer. Tom liste = OK."""
    issues = []
    env = spec["envelope"]
    ex0, ey0, ex1, ey1 = _bbox(env)
    for room in spec["rooms"]:
        for pt in room["poly"]:
            if not (ex0 - 1 <= pt[0] <= ex1 + 1 and ey0 - 1 <= pt[1] <= ey1 + 1):
                issues.append(f"rom '{room['name']}': punkt {pt} utenfor envelope")
    for f in spec.get("fixtures", []):
        w, h = SYM_SIZE.get(f["sym"], (0, 0))
        cx, cy = f["x"] + w / 2, f["y"] + h / 2
        if f.get("rot"):
            a = math.radians(f["rot"])
            ox, oy = f["x"], f["y"]
            cx = ox + (w / 2) * math.cos(a) - (h / 2) * math.sin(a)
            cy = oy + (w / 2) * math.sin(a) + (h / 2) * math.cos(a)
        if not any(_point_in_poly((cx, cy), r["poly"]) for r in spec["rooms"]):
            issues.append(f"fixture '{f['sym']}' senter ({cx:.0f},{cy:.0f}) er ikke i noe rom")
    for o in spec.get("openings", []):
        x, y, w, h = o["rect"]
        if w <= 0 or h <= 0:
            issues.append(f"opening med ugyldig rect {o['rect']}")
        if "door" in o:
            d = o["door"]
            if d["width"] < 50 or d["width"] > 120:
                issues.append(f"dør med urealistisk bredde {d['width']}")
    return issues


def _door_svg(door: dict) -> str:
    """Parametrisk dørslag: blad i åpen posisjon + kvartsirkelbue.

    hinge = hengselpunkt. angle = retning (grader) dørbladet peker i ÅPEN
    posisjon (0=øst, 90=sør, 180=vest, 270=nord). sweep = 1/0 for buens retning
    fra åpen til lukket posisjon.
    """
    hx, hy = door["hinge"]
    w = door["width"]
    a = math.radians(door["angle"])
    tipx, tipy = hx + w * math.cos(a), hy + w * math.sin(a)
    sweep = door.get("sweep", 1)
    closed_a = a + (math.pi / 2 if sweep else -math.pi / 2)
    cx, cy = hx + w * math.cos(closed_a), hy + w * math.sin(closed_a)
    return (
        f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{tipx:.0f}" y2="{tipy:.0f}" '
        f'stroke="{INK}" stroke-width="3"/>'
        f'<path d="M {tipx:.0f} {tipy:.0f} A {w} {w} 0 0 {sweep} {cx:.0f} {cy:.0f}" '
        f'fill="none" stroke="{INK}" stroke-width="0.8"/>'
    )


def _window_svg(rect: list) -> str:
    """Vindu: hvitt felt i veggmassen + to karmlinjer langs lengste akse."""
    x, y, w, h = rect
    parts = [f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{CREAM}"/>']
    if w >= h:  # horisontal vegg
        for fy in (y + h * 0.25, y + h * 0.75):
            parts.append(
                f'<line x1="{x:.0f}" y1="{fy:.0f}" x2="{x + w:.0f}" y2="{fy:.0f}" '
                f'stroke="{INK}" stroke-width="2"/>'
            )
    else:
        for fx in (x + w * 0.25, x + w * 0.75):
            parts.append(
                f'<line x1="{fx:.0f}" y1="{y:.0f}" x2="{fx:.0f}" y2="{y + h:.0f}" '
                f'stroke="{INK}" stroke-width="2"/>'
            )
    return "".join(parts)


def render_plan(spec: dict) -> str:
    env = spec["envelope"]
    ex0, ey0, ex1, ey1 = _bbox(env)
    W, H = ex1 - ex0, ey1 - ey0

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}">']

    # 1. Romflater
    for room in spec["rooms"]:
        fill = BAD if room["kind"] == "bad" else ROOM
        parts.append(f'<polygon points="{_pts(room["poly"])}" fill="{fill}"/>')

    # 2. Flisraster i bad (clip-path per rom -> aldri utenfor)
    for i, room in enumerate(spec["rooms"]):
        if room["kind"] != "bad":
            continue
        bx0, by0, bx1, by1 = _bbox(room["poly"])
        parts.append(f'<clipPath id="bad{i}"><polygon points="{_pts(room["poly"])}"/></clipPath>')
        grid = [f'<g clip-path="url(#bad{i})" stroke="{INK}" stroke-width="0.35" opacity="0.5">']
        gx = bx0 - (bx0 % 20) + 20
        while gx < bx1:
            grid.append(f'<line x1="{gx:.0f}" y1="{by0:.0f}" x2="{gx:.0f}" y2="{by1:.0f}"/>')
            gx += 20
        gy = by0 - (by0 % 20) + 20
        while gy < by1:
            grid.append(f'<line x1="{bx0:.0f}" y1="{gy:.0f}" x2="{bx1:.0f}" y2="{gy:.0f}"/>')
            gy += 20
        grid.append("</g>")
        parts.append("".join(grid))

    # 3. Veggmasse: envelope minus alle rom, even-odd -> hjørner lukker alltid
    wall_d = _path(env) + " " + " ".join(_path(r["poly"]) for r in spec["rooms"])
    parts.append(f'<path d="{wall_d}" fill="{INK}" fill-rule="evenodd"/>')

    # 4. Åpninger (kutter veggmassen) + dørslag
    for o in spec.get("openings", []):
        x, y, w, h = o["rect"]
        parts.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{ROOM}"/>'
        )
        if "door" in o:
            parts.append(_door_svg(o["door"]))

    # 5. Vinduer
    for win in spec.get("windows", []):
        parts.append(_window_svg(win["rect"]))

    # 6. Innredning og ekstra-elementer
    for f in spec.get("fixtures", []):
        t = f'translate({f["x"]} {f["y"]})'
        if f.get("rot"):
            t += f' rotate({f["rot"]})'
        parts.append(f'<use href="#{f["sym"]}" transform="{t}"/>')
    for e in spec.get("extras", []):
        if e["type"] == "bench":
            x, y, w, h = e["rect"]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="none" stroke="{INK}" stroke-width="1"/>'
            )
        elif e["type"] == "ladder":
            x, y, w, h = e["rect"]
            lad = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="0.9"/>']
            if w >= h:
                n = max(2, int(w // 15))
                for i in range(1, n):
                    fx = x + i * w / n
                    lad.append(f'<line x1="{fx:.0f}" y1="{y}" x2="{fx:.0f}" y2="{y + h}" stroke="{INK}" stroke-width="0.9"/>')
            else:
                n = max(2, int(h // 15))
                for i in range(1, n):
                    fy = y + i * h / n
                    lad.append(f'<line x1="{x}" y1="{fy:.0f}" x2="{x + w}" y2="{fy:.0f}" stroke="{INK}" stroke-width="0.9"/>')
            parts.append("".join(lad))
        elif e["type"] == "dashed":
            parts.append(
                f'<polygon points="{_pts(e["poly"])}" fill="none" stroke="{INK}" '
                f'stroke-width="1.2" stroke-dasharray="6 4"/>'
            )
        elif e["type"] == "label":
            rot = f' transform="rotate({e["rot"]} {e["x"]} {e["y"]})"' if e.get("rot") else ""
            parts.append(
                f'<text x="{e["x"]}" y="{e["y"]}" font-family="Helvetica" font-size="11" '
                f'fill="{INK}" text-anchor="middle"{rot}>{e["text"]}</text>'
            )

    # 7. Rom-labels
    for lb in spec.get("labels", []):
        parts.append(
            f'<g font-family="Helvetica" fill="{INK}" text-anchor="middle">'
            f'<text x="{lb["x"]}" y="{lb["y"]}" font-size="13">{lb["name"]}</text>'
            f'<text x="{lb["x"]}" y="{lb["y"] + 17}" font-size="10" opacity="0.65">{lb["area"]} m²</text></g>'
        )

    parts.append("</svg>")
    return "".join(parts)


def render_hems(spec: dict):
    hems = spec.get("hems")
    if not hems:
        return None
    poly = hems["poly"]
    x0, y0, x1, y1 = _bbox(poly)
    pad = 11
    W, H = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    shifted = [[x - x0 + pad, y - y0 + pad] for x, y in poly]
    if hems.get("label_xy"):  # for ikke-rektangulære hems der bbox-senteret faller utenfor
        cx, cy = hems["label_xy"][0] - x0 + pad, hems["label_xy"][1] - y0 + pad
    else:
        cx, cy = W / 2, H / 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}">',
        f'<polygon points="{_pts(shifted)}" fill="{HEMS}"/>',
        f'<polygon points="{_pts(shifted)}" fill="none" stroke="{INK}" stroke-width="8"/>',
    ]
    if hems.get("hatch"):
        hatch = [[x - x0 + pad, y - y0 + pad] for x, y in hems["hatch"]]
        parts.append(
            f'<polygon points="{_pts(hatch)}" fill="none" stroke="{INK}" '
            f'stroke-width="1" stroke-dasharray="4 3"/>'
        )
    parts.append(
        f'<g font-family="Helvetica" fill="{INK}" text-anchor="middle">'
        f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="13">Hems</text>'
        f'<text x="{cx:.0f}" y="{cy + 17:.0f}" font-size="10" opacity="0.65">ca {hems["area"]} m²</text></g>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main():
    uid = sys.argv[1]
    spec_path = Path(__file__).parent / "specs" / f"{uid}.json"
    spec = json.loads(spec_path.read_text())
    issues = validate(spec)
    if issues:
        print(f"VALIDERING FEILET for {uid}:")
        for i in issues:
            print(f"  - {i}")
        sys.exit(1)
    plan = render_plan(spec)
    (brand.RENTEGNING / f"{uid}-plan.svg").write_text(plan)
    out = [f"{uid}-plan.svg OK"]
    hems = render_hems(spec)
    if hems:
        (brand.RENTEGNING / f"{uid}-hems.svg").write_text(hems)
        out.append(f"{uid}-hems.svg OK")
    print(", ".join(out))


if __name__ == "__main__":
    main()
