#!/usr/bin/env python3
"""Validate authored sources and emit app data for the 3D boligvelger."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import check_overlaps

ROOT = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().parent
EIENDOM = ROOT / "eiendommer" / "dybwads gate 8"
OUT = ROOT / "app" / "public" / "data" / "dybwads-gate-8"

EXPECTED_PRICE_SUM = 91_270_000
EXPECTED_BRA_SUM = 445

SCALE = 0.012696
AREA_TOL = 0.12  # 12 % — polygonene følger innvendige vegglinjer, BRA inkluderer innervegger


def poly_area_m2(poly, scale=SCALE):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2 * scale * scale


def validate_unit_areas(floors, arch, prisliste, strict=False, scale=None):
    """Polygon-areal per enhet vs arkitekt-BRA (hoveddel) og braU (duplex-U)."""
    if scale is None:
        scale = _load("building.json")["scale"]
    errors, warnings = [], []
    sink = errors if strict else warnings
    main_area, u_area = {}, {}
    for fid, f in floors.items():
        for u in f["units"]:
            tgt = u_area if fid.lower() == "u" else main_area
            tgt[u["unit"]] = tgt.get(u["unit"], 0.0) + poly_area_m2(u["poly"], scale)
    for hnr, a in arch.items():
        if hnr in main_area:
            got, want = main_area[hnr], a["bra"]
            if want and abs(got - want) / want > AREA_TOL:
                sink.append(f"{hnr}: polygon {got:.1f} m² vs arkitekt BRA-i {want} m² (avvik > {AREA_TOL:.0%})")
    for hnr, got in u_area.items():
        want = (prisliste.get(hnr) or {}).get("braU")
        if want and abs(got - want) / want > AREA_TOL:
            sink.append(f"{hnr}-U: polygon {got:.1f} m² vs braU {want} m² (avvik > {AREA_TOL:.0%})")
    return errors, warnings


def _load(name):
    return json.loads((TOOL / name).read_text())


def _load_arch():
    return json.loads((ROOT / "tools/plantegning/units.json").read_text())


def _load_floors():
    return {p.stem.replace("etasje-", ""): json.loads(p.read_text())
            for p in sorted((TOOL / "floors").glob("etasje-*.json"))}


def bra_sum(prisliste):
    return sum(u["braI"] + u.get("braU", 0) for u in prisliste.values())


def validate_prisliste(prisliste):
    errors, warnings = [], []
    total = sum(u["pris"] for u in prisliste.values())
    if total != EXPECTED_PRICE_SUM:
        errors.append(f"price sum {total} != {EXPECTED_PRICE_SUM}")
    if bra_sum(prisliste) != EXPECTED_BRA_SUM:
        errors.append(f"BRA sum {bra_sum(prisliste)} != {EXPECTED_BRA_SUM}")
    arch = _load_arch()
    for hnr, p in prisliste.items():
        if hnr in arch and abs(p["braI"] - arch[hnr]["bra"]) > 2.5:
            warnings.append(f"{hnr}: prisliste BRA-I {p['braI']} vs arkitekt {arch[hnr]['bra']}")
    return errors, warnings


def validate_coverage():
    errors = []
    prisliste = _load("prisliste.json")
    arch = _load_arch()
    rentegning = {p.stem.replace("-plan", "")
                  for p in (EIENDOM / "rentegning").glob("H*-plan.svg")}
    if set(prisliste) != rentegning:
        errors.append(f"prisliste vs rentegning mismatch: {set(prisliste) ^ rentegning}")
    if set(prisliste) != set(arch):
        errors.append(f"prisliste vs arkitekt-units mismatch: {set(prisliste) ^ set(arch)}")
    floor_units = {u["unit"] for f in _load_floors().values() for u in f["units"]}
    missing = set(prisliste) - floor_units
    if missing:
        errors.append(f"units missing 3D polygon: {sorted(missing)}")
    return errors


def validate_envelope_containment():
    """Every unit + common polygon of every floor must lie inside the envelope."""
    errors = []
    envelope = _load("building.json")["envelope"]["poly"]
    for fid, f in _load_floors().items():
        polys = [(u["id"], u["poly"]) for u in f["units"]]
        polys += [(f"common[{i}]", c) for i, c in enumerate(f.get("common", []))]
        for pid, poly in polys:
            out = check_overlaps.area_outside_m2(poly, envelope)
            if out > check_overlaps.MAX_OVERLAP_M2:
                errors.append(
                    f"floor {fid}: {pid} pokes {out:.2f} m² outside envelope"
                )
    return errors


def build_units():
    prisliste = _load("prisliste.json")
    arch = _load_arch()
    units = {}
    for hnr, p in prisliste.items():
        a = arch[hnr]
        units[hnr] = {
            "id": hnr,
            "navn": p["navn"],
            "type": a["type"],
            "etasje": a["floor"],          # architect data is authoritative for floor
            "duplex": "braU" in p,
            "braI": p["braI"],
            "braU": p.get("braU"),
            "braArkitekt": a["bra"],
            "hemsCa": a.get("hems", {}).get("area_ca"),
            "rom": a["rooms"],
            "pris": p["pris"],
            "kvmPris": p["kvmPris"],
            "kvmPrisU": p.get("kvmPrisU"),
        }
    return units


def build_geometry():
    b = _load("building.json")
    envelope = b["envelope"]
    materials = b["materials"]
    floors_raw = _load_floors()
    floors = []
    elevation = 0.0
    for fid in b["floorOrder"]:
        f = floors_raw[fid.lower()] if fid.lower() in floors_raw else floors_raw[fid]
        spec = b["floors"][fid]
        floors.append({
            "id": fid,
            "label": spec["label"],
            "elevation": round(elevation, 3),
            "height": spec["height"],
            "facade": materials[spec["facade"]],
            "outline": envelope["poly"],   # canonical envelope shared by all floors
            "units": f["units"],
            "common": f.get("common", []),
        })
        elevation += spec["height"]
    return {
        "scale": b["scale"],
        "materials": materials,
        "slabThickness": b["slabThickness"],
        "envelope": envelope,
        "floors": floors,
        "roof": {"elevation": round(elevation, 3), **b["roof"]},
        "windows": b.get("windows", []),
        "entrances": b.get("entrances", []),
        "balconies": b.get("balconies", []),
    }


def main():
    prisliste = _load("prisliste.json")
    errors, warnings = validate_prisliste(prisliste)
    errors += validate_coverage()
    errors += validate_envelope_containment()

    strict_areas = os.environ.get("VELGER_STRICT_AREAS", "1") == "1"
    area_errors, area_warnings = validate_unit_areas(_load_floors(), _load_arch(), prisliste, strict=strict_areas)
    errors += area_errors
    warnings += area_warnings

    r = subprocess.run([sys.executable, str(TOOL / "check_overlaps.py")], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        errors.append("geometry overlap check failed")

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "units.json").write_text(json.dumps(build_units(), ensure_ascii=False, indent=1))
    (OUT / "geometri.json").write_text(json.dumps(build_geometry(), ensure_ascii=False, indent=1))
    (OUT / "site.json").write_text((TOOL / "site.json").read_text())

    plan_dir = OUT / "plan"
    pdf_dir = OUT / "pdf"
    plan_dir.mkdir(exist_ok=True)
    pdf_dir.mkdir(exist_ok=True)
    for svg in (EIENDOM / "rentegning").glob("H*.svg"):
        shutil.copy(svg, plan_dir / svg.name)
    for pdf in (EIENDOM / "plantegninger").glob("H*.pdf"):
        shutil.copy(pdf, pdf_dir / pdf.name)
    print(f"OK: wrote {OUT}")


if __name__ == "__main__":
    main()
