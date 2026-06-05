"""Bygg ferdige A4 plantegningssider (SVG) fra rentegning + units.json."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand
import fixtures

POSISJON = Path(__file__).parent / "posisjon"
MARGIN = 56
HEADER_H = 170


def load_fragment(path: Path) -> tuple[tuple[float, float, float, float], str]:
    """Returner (viewBox, inner-SVG) fra et SVG-fragment."""
    text = path.read_text()
    m = re.search(r'viewBox="([\d. -]+)"', text)
    vb = tuple(float(v) for v in m.group(1).split())
    inner = re.sub(r"^.*?<svg[^>]*>", "", text, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    return vb, inner


def place(path: Path, x: float, y: float, scale: float) -> tuple[str, float, float]:
    """Plasser fragment ved (x,y) med gitt skala. Returner (svg, bredde, høyde) på siden."""
    vb, inner = load_fragment(path)
    w, h = vb[2] * scale, vb[3] * scale
    svg = f'<g transform="translate({x:.1f} {y:.1f}) scale({scale:.4f})">{inner}</g>'
    return svg, w, h


def scale_bar(x: float, y: float, k: float = brand.PX_PER_CM) -> str:
    seg = 100 * k  # 1 m
    parts = [f'<g transform="translate({x} {y})">']
    for i in range(5):
        fill = brand.GREEN if i % 2 == 0 else "none"
        parts.append(
            f'<rect x="{i * seg:.1f}" y="0" width="{seg:.1f}" height="5" '
            f'fill="{fill}" stroke="{brand.GREEN}" stroke-width="0.8"/>'
        )
    for i in range(6):
        parts.append(
            f'<text x="{i * seg:.1f}" y="18" font-family="Engravers" font-size="8" '
            f'letter-spacing="1" fill="{brand.MUTED}" text-anchor="middle">{i}</text>'
        )
    parts.append(
        f'<text x="{5 * seg + 16:.1f}" y="18" font-family="Engravers" font-size="8" '
        f'letter-spacing="1" fill="{brand.MUTED}">M</text></g>'
    )
    return "".join(parts)


def north_arrow(x: float, y: float, deg: float) -> str:
    return (
        f'<g transform="translate({x} {y}) rotate({deg})">'
        f'<circle r="14" fill="none" stroke="{brand.GREEN}" stroke-width="1"/>'
        f'<line x1="0" y1="12" x2="0" y2="-5" stroke="{brand.GREEN}" stroke-width="1"/>'
        f'<polygon points="0,-13 -4,-4 4,-4" fill="{brand.GREEN}"/>'
        f'<text y="-17" font-family="Engravers" font-size="9" fill="{brand.GREEN}" '
        f'text-anchor="middle" transform="rotate({-deg})">N</text></g>'
    )


def position_diagrams(unit_id: str, floor: int, x: float, y: float) -> str:
    """Etasje-mini + snitt, med enhet/etasje markert i grønt."""
    def highlight(text: str, elem_id: str) -> str:
        return re.sub(
            rf'(<[^>]*id="{elem_id}"[^>]*?)fill="none"',
            rf'\1fill="{brand.GREEN}" opacity="0.85"',
            text,
            count=1,
        )

    etasje = highlight((POSISJON / f"etasje-{floor}.svg").read_text(), unit_id)
    snitt = highlight((POSISJON / "snitt.svg").read_text(), f"floor-{floor}")

    out = []
    for i, (frag_text, label) in enumerate([(etasje, f"{floor}. etasje"), (snitt, "Snitt")]):
        tmp = Path(f"/tmp/_pos{i}.svg")
        tmp.write_text(frag_text)
        vb, inner = load_fragment(tmp)
        s = 110 / vb[3]  # høyde 110px
        ox = x + i * 105
        out.append(f'<g transform="translate({ox} {y}) scale({s:.3f})">{inner}</g>')
        out.append(
            f'<text x="{ox + vb[2] * s / 2:.0f}" y="{y + 126}" font-family="Engravers" '
            f'font-size="7.5" letter-spacing="1.5" fill="{brand.MUTED}" '
            f'text-anchor="middle">{label.upper()}</text>'
        )
    return "".join(out)


def areal_lines(u: dict) -> list[str]:
    lines = [f"BRA-i {u['bra']:.1f} m²".replace(".", ",")]
    if u["hems"]:
        lines.append(f"Hems (ikke målbart) ca {u['hems']['area_ca']:.1f} m²".replace(".", ","))
    lines.append(f"Sum BRA {u['bra']:.1f} m²".replace(".", ","))
    return lines


def render_page(unit_id: str, u: dict) -> str:
    plan_path = brand.RENTEGNING / f"{unit_id}-plan.svg"
    hems_path = brand.RENTEGNING / f"{unit_id}-hems.svg"

    # 1:50 som standard; fit-skalering for brede/høye enheter.
    # Målestokk-baren tegnes med samme k og forblir dermed sann.
    GAP = 40
    avail_w = brand.A4_W - 2 * MARGIN
    avail_h = 610
    plan_vb, _ = load_fragment(plan_path)
    hems_vb = load_fragment(hems_path)[0] if hems_path.exists() else None
    total_cm_w = plan_vb[2] + (hems_vb[2] if hems_vb else 0)
    max_cm_h = max(plan_vb[3], hems_vb[3] if hems_vb else 0)
    k = min(
        brand.PX_PER_CM,
        (avail_w - (GAP if hems_vb else 0)) / total_cm_w,
        avail_h / max_cm_h,
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{brand.A4_W}" height="{brand.A4_H}" '
        f'viewBox="0 0 {brand.A4_W} {brand.A4_H}">',
        f"<style>{brand.font_css()}</style>",
        fixtures.DEFS,
        f'<rect width="{brand.A4_W}" height="{brand.A4_H}" fill="{brand.CREAM}"/>',
        # Header
        f'<rect width="{brand.A4_W}" height="{HEADER_H}" fill="{brand.GREEN}"/>',
        f'<text x="{MARGIN}" y="96" font-family="Sfizia" font-size="56" '
        f'fill="{brand.HEADER_TEXT}">{unit_id}</text>',
        f'<text x="{MARGIN}" y="132" font-family="Engravers" font-size="13" '
        f'letter-spacing="3" fill="{brand.HEADER_MUTED}">'
        f'{u["type"].upper()} · {u["floor"]}. ETASJE</text>',
    ]
    for i, line in enumerate(areal_lines(u)):
        parts.append(
            f'<text x="{brand.A4_W - MARGIN}" y="{72 + i * 24}" font-family="Helvetica" '
            f'font-size="13" fill="{brand.HEADER_MUTED}" text-anchor="end">{line}</text>'
        )

    # Hovedplan, sentrert i plansonen (y 210-820)
    pw, ph = plan_vb[2] * k, plan_vb[3] * k
    hems_dims = (hems_vb[2] * k, hems_vb[3] * k) if hems_vb else None
    total_w = pw + (hems_dims[0] + GAP if hems_dims else 0)
    px = MARGIN + (avail_w - total_w) / 2
    py = 210 + (avail_h - ph) / 2
    plan_svg, _, _ = place(plan_path, px, py, k)
    parts.append(plan_svg)
    if hems_dims:
        hx = px + pw + GAP
        hy = py + ph - hems_dims[1]  # bunnjustert mot hovedplan
        hems_svg, hw, hh = place(hems_path, hx, hy, k)
        parts.append(hems_svg)
        parts.append(
            f'<text x="{hx + hw / 2:.0f}" y="{hy - 10:.0f}" font-family="Engravers" '
            f'font-size="8.5" letter-spacing="2" fill="{brand.MUTED}" '
            f'text-anchor="middle">HEMS</text>'
        )

    # Målestokk + nordpil
    parts.append(scale_bar(MARGIN, 855, k))
    parts.append(north_arrow(brand.A4_W - MARGIN - 16, 862, u["north_deg"]))
    # Posisjonsdiagrammer
    parts.append(position_diagrams(unit_id, u["floor"], brand.A4_W - 290, 905))
    # Footer
    parts.append(
        f'<line x1="{MARGIN}" y1="1058" x2="{brand.A4_W - MARGIN}" y2="1058" '
        f'stroke="{brand.LIGHT_LINE}" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{MARGIN}" y="1082" font-family="Engravers" font-size="9" '
        f'letter-spacing="2.5" fill="{brand.MUTED}">DYBWADS GATE 8</text>'
    )
    parts.append(
        f'<text x="{brand.A4_W - MARGIN}" y="1082" font-family="Engravers" font-size="9" '
        f'letter-spacing="2.5" fill="{brand.GREEN}" text-anchor="end">HOUELAND</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main():
    units = json.loads((Path(__file__).parent / "units.json").read_text())
    targets = sys.argv[1:] or [
        uid for uid in units if (brand.RENTEGNING / f"{uid}-plan.svg").exists()
    ]
    brand.OUTPUT.mkdir(exist_ok=True)
    for uid in targets:
        out = brand.OUTPUT / f"{uid}.svg"
        out.write_text(render_page(uid, units[uid]))
        print(f"{uid} -> {out}")


if __name__ == "__main__":
    main()
