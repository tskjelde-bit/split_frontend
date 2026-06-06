#!/usr/bin/env python3
"""Validate authored sources and emit app data for the 3D boligvelger."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().parent
EIENDOM = ROOT / "eiendommer" / "dybwads gate 8"
OUT = ROOT / "app" / "public" / "data" / "dybwads-gate-8"

EXPECTED_PRICE_SUM = 91_270_000
EXPECTED_BRA_SUM = 445


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
            "outline": f["outline"],
            "units": f["units"],
            "common": f.get("common", []),
        })
        elevation += spec["height"]
    return {
        "scale": b["scale"],
        "slabThickness": b["slabThickness"],
        "floors": floors,
        "roof": {"elevation": round(elevation, 3), **b["roof"]},
        "windows": b.get("windows", []),
    }


def main():
    prisliste = _load("prisliste.json")
    errors, warnings = validate_prisliste(prisliste)
    errors += validate_coverage()

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
