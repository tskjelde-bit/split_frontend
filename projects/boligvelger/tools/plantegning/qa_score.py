"""Objektiv geometri-score: hvor godt dekker rentegningens vegger arkitektens?

Renderer rentegning-SVG i crop-skala og måler:
  recall    = andel av arkitektens mørke piksler dekket av rentegningen
  precision = andel av rentegningens mørke piksler som treffer arkitekten

Arkitekt-croppen inneholder tekst/annotasjoner/nabo-enheter som rentegningen
bevisst utelater, så recall < 1 er ventet; presisjonen er hovedsignalet for
"vegger på feil sted". Bruk: qa_score.py H0101 OFFX OFFY

Skala-notat: rentegningens SVG renderes til eksakt crop-dimensjoner (fra
units.json crop_px[2] × crop_px[3]) slik at 1 spec-enhet = crop_px / spec_units
piksler — samme skala som arkitektens PNG-crop. Fallback ved manglende
units.json-entry: gammel formel PNG_PX_PER_CM ≈ 1.0.

Toleranse: Disk:12 (≈12 px ≈ 12 cm ved 1:100-skala). Denne toleransen
kompenserer for: (1) specens senterlinje-vegger vs. arkitektens veggflate,
(2) møblement/skravur i rentegningen som gir edge-piksler uten fasit i
arkitekt-PNG, (3) nabo-enhets-kanter i cropens randsone. Gate ≥ 0.80 er
oppnåelig for korrekt kalibrerte specs med denne toleransen.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand
import build_pages
import fixtures
from shot import shot

# Fallback-skala (brukes kun hvis uid ikke finnes i units.json).
PNG_PX_PER_CM = 1.2696 * 200 / 2.54 / 100

_UNITS_CACHE = None


def _load_units() -> dict:
    global _UNITS_CACHE
    if _UNITS_CACHE is None:
        _UNITS_CACHE = json.loads((Path(__file__).parent / "units.json").read_text())
    return _UNITS_CACHE


def render_plan_png(uid: str, out: Path) -> tuple[int, int]:
    plan = brand.RENTEGNING / f"{uid}-plan.svg"
    vb, inner = build_pages.load_fragment(plan)
    units = _load_units()
    if uid in units and "crop_px" in units[uid]:
        # Skaler SVG til eksakt crop-dimensjoner for nøyaktig pixel-sammenligning.
        w, h = units[uid]["crop_px"][2], units[uid]["crop_px"][3]
    else:
        w, h = round(vb[2] * PNG_PX_PER_CM), round(vb[3] * PNG_PX_PER_CM)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {vb[2]:.0f} {vb[3]:.0f}">'
        f'<rect width="{vb[2]:.0f}" height="{vb[3]:.0f}" fill="white"/>'
        f"{fixtures.DEFS}{inner}</svg>"
    )
    html = f'<!DOCTYPE html><html><body style="margin:0">{svg}</body></html>'
    tmp = Path(tempfile.mkstemp(suffix=".html")[1])
    tmp.write_text(html)
    shot(str(tmp), str(out), f"{w},{h}")
    tmp.unlink()
    return w, h


def fx_mean(*magick_args) -> float:
    res = subprocess.run(
        ["magick", *magick_args, "-format", "%[fx:mean]", "info:"],
        capture_output=True, text=True, check=True,
    )
    return float(res.stdout.strip())


# Toleranse i piksler for edge-precision-scoring.
# Disk:12 ≈ 12 cm ved 1:100-skala (1 px ≈ 1 cm): kompenserer for veggsenterlinjer,
# møblement-edges og nabo-enhets-kanter i croppen.
EDGE_DILATE_RADIUS = 12


def score_at(td: Path, crop: Path, mine_mask: Path, mine_edges: Path,
             w: int, h: int, offx: int, offy: int) -> float:
    arch_region = td / f"arch-{offx}-{offy}.png"
    subprocess.run(
        ["magick", str(crop), "-crop", f"{w}x{h}+{offx}+{offy}", "+repage",
         "-colorspace", "gray", "-threshold", "55%", "-negate",
         "-morphology", "Dilate", f"Disk:{EDGE_DILATE_RADIUS}", str(arch_region)],
        check=True,
    )
    edge_total = fx_mean(str(mine_edges))
    hit = fx_mean(str(mine_edges), str(arch_region), "-compose", "Multiply", "-composite")
    arch_region.unlink()
    return hit / edge_total if edge_total else 0


def search(uid: str, offx: int, offy: int):
    """Grid-søk ±32px rundt antatt offset; rapporter beste."""
    crop = brand.UNDERLAG / f"{uid}-crop.png"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        mine_png = td / "mine.png"
        w, h = render_plan_png(uid, mine_png)
        mine_mask = td / "mine-mask.png"
        subprocess.run(
            ["magick", str(mine_png), "-colorspace", "gray", "-threshold", "55%",
             "-negate", str(mine_mask)], check=True)
        mine_edges = td / "mine-edges.png"
        subprocess.run(
            ["magick", str(mine_mask), "-morphology", "Edge", "Diamond:1", str(mine_edges)],
            check=True)
        best = (0.0, offx, offy)
        for dy in range(-32, 33, 8):
            for dx in range(-32, 33, 8):
                s = score_at(td, crop, mine_mask, mine_edges, w, h, offx + dx, offy + dy)
                if s > best[0]:
                    best = (s, offx + dx, offy + dy)
        # finsøk rundt beste
        s0, bx, by = best
        for dy in range(-4, 5, 4):
            for dx in range(-4, 5, 4):
                s = score_at(td, crop, mine_mask, mine_edges, w, h, bx + dx, by + dy)
                if s > best[0]:
                    best = (s, bx + dx, by + dy)
        print(f"{uid}: best-precision={best[0]:.3f} at offset [{best[1]},{best[2]}]")


def main():
    uid = sys.argv[1]
    offx, offy = int(sys.argv[2]), int(sys.argv[3])
    if len(sys.argv) > 4 and sys.argv[4] == "--search":
        # Bruk crop_offset som søkesenter hvis tilgjengelig og offset-arg er [0,0].
        if offx == 0 and offy == 0:
            units = _load_units()
            co = units.get(uid, {}).get("crop_offset")
            if co:
                offx, offy = co[0], co[1]
        search(uid, offx, offy)
        return
    crop = brand.UNDERLAG / f"{uid}-crop.png"

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        mine_png = td / "mine.png"
        w, h = render_plan_png(uid, mine_png)

        # Arkitekt-masken beskjæres til rentegningens område (+litt margin)
        arch_region = td / "arch.png"
        subprocess.run(
            ["magick", str(crop), "-crop", f"{w}x{h}+{offx}+{offy}", "+repage",
             "-colorspace", "gray", "-threshold", "55%", "-negate", str(arch_region)],
            check=True,
        )
        mine_mask = td / "mine-mask.png"
        subprocess.run(
            ["magick", str(mine_png), "-colorspace", "gray", "-threshold", "55%",
             "-negate", str(mine_mask)],
            check=True,
        )
        # Kanter av min veggmasse = veggliv; de skal ligge på arkitektens streker
        mine_edges = td / "mine-edges.png"
        subprocess.run(
            ["magick", str(mine_mask), "-morphology", "Edge", "Diamond:1", str(mine_edges)],
            check=True,
        )
        arch_dil = td / "arch-dil.png"
        mine_mass_dil = td / "mine-mass-dil.png"
        subprocess.run(["magick", str(arch_region), "-morphology", "Dilate", f"Disk:{EDGE_DILATE_RADIUS}", str(arch_dil)], check=True)
        subprocess.run(["magick", str(mine_mask), "-morphology", "Dilate", f"Disk:{EDGE_DILATE_RADIUS}", str(mine_mass_dil)], check=True)

        edge_total = fx_mean(str(mine_edges))
        arch_total = fx_mean(str(arch_region))
        # presisjon: mine veggliv-kanter som treffer arkitekt-strek (±EDGE_DILATE_RADIUS px)
        prec_hit = fx_mean(str(mine_edges), str(arch_dil), "-compose", "Multiply", "-composite")
        # recall: arkitekt-innhold dekket av min masse (tekst/annotasjoner trekker ned)
        rec_hit = fx_mean(str(arch_region), str(mine_mass_dil), "-compose", "Multiply", "-composite")

        precision = prec_hit / edge_total if edge_total else 0
        recall = rec_hit / arch_total if arch_total else 0
        print(f"{uid}: edge-precision={precision:.3f} recall={recall:.3f} "
              f"({w}x{h}+{offx}+{offy})")


if __name__ == "__main__":
    main()
