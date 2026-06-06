# 3D-boligvelger Dybwads gate 8 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prosjektnettside med orbitérbar gips-3D-modell av Dybwads gate 8 som eksploderer i svevende etasjeplater, med klikkbare enheter, plantegningspanel, prisliste, statusadmin og Cloudflare-deploy.

**Architecture:** Parametrisk geometri: et Python-tool leser eksisterende enhets-specs (`tools/plantegning/specs/`), priser og autorerte etasje-poly­goner og emitterer `geometri.json` + `units.json` til appen. React Three Fiber ekstruderer polygonene runtime (ingen glTF). Status bor i Cloudflare KV bak en Worker som også serverer de statiske filene og en minimal admin-side.

**Tech Stack:** Vite + React + TypeScript, three.js, @react-three/fiber, @react-three/drei, zustand, vitest, Python 3 (datapipeline, pytest), Cloudflare Workers + KV (wrangler).

**Spec:** `docs/superpowers/specs/2026-06-06-3d-boligvelger-dybwads-gate-8-design.md`

---

## Filstruktur (lås denne)

```
app/                                  # Vite-app (generisk velger)
  src/
    lib/types.ts                      # alle delte typer
    lib/shapes.ts                     # polygon→THREE.Shape, centroid
    lib/format.ts                     # NOK-formatering
    lib/data.ts                       # fetch av geometri/units/site/status
    lib/webgl.ts                      # WebGL-deteksjon
    lib/qa.ts                         # ?qa= URL-param → store-state
    state/store.ts                    # zustand: mode/focus/hover/select/status
    scene/VelgerCanvas.tsx            # <Canvas>, lys, skygger, dpr-clamp
    scene/Building.tsx                # mapper geometri.json → FloorPlate/Roof
    scene/FloorPlate.tsx              # slab + common + UnitMesh, eksplosjons-Y
    scene/UnitMesh.tsx                # ekstrudert enhet, hover/klikk, status-farge
    scene/Roof.tsx                    # autorerte takvolumer
    scene/CameraRig.tsx               # CameraControls, auto-rotate, modus-overganger
    ui/Hud.tsx                        # tittel, hint, FloorChips
    ui/FloorChips.tsx
    ui/UnitTooltip.tsx                # drei <Html> ved hover
    ui/UnitPanel.tsx                  # sidepanel / bottom-sheet
    ui/FallbackList.tsx               # ingen-WebGL-fallback
    ui/InfoSections.tsx               # om / beliggenhet / kontakt
    App.tsx  main.tsx  styles.css
  public/fonts/                       # Sfizia + Engravers (kopiert fra brand)
  public/data/dybwads-gate-8/         # GENERERT av tools/velger-data (gitignores IKKE)
    geometri.json  units.json  site.json
    plan/H0xxx-plan.svg  plan/H0xxx-hems.svg
    pdf/H0xxx.pdf
tools/velger-data/
  prisliste.json                      # autorert fra verdivurdering-docx
  building.json                       # scale, etasjehøyder, tak, vinduer (fra snitt/fasader)
  site.json                           # tittel, kontaktinfo
  floors/etasje-{u,1,2,3}.json        # outline + unit-polys + common-polys
  gen_floors.py                       # skjelett-generator fra specs + crop_px
  qa_overlay.py                       # overlay-HTML: floor-JSON oppå underlag-PNG
  build_data.py                       # validering + emit til app/public/data
  test_build_data.py                  # pytest
tools/velger-qa/
  shots.sh                            # headless screenshots av nøkkeltilstander
  click_units.mjs                     # velger alle 16 enheter, verifiserer panel
worker/
  wrangler.jsonc  package.json  tsconfig.json
  src/index.ts                        # fetch-handler: /api/status, /admin, ASSETS
  src/admin.ts                        # admin-HTML som template-string
  test/api.test.ts                    # vitest med mock-KV
```

Koordinatkonvensjon: alle polygoner i «underlag-px» (samme rom som `crop_px` i `tools/plantegning/units.json`). `building.json.scale` = meter per px, kalibrert i Task 3. I three.js: `x = px*scale`, `z = py*scale`, `y` = høyde. Eksplosjon animerer kun `y` per etasjegruppe.

---

### Task 1: Scaffold app + test-oppsett

**Files:**
- Create: `app/` (Vite-scaffold), `app/src/lib/format.ts`, `app/src/lib/format.test.ts`

- [ ] **Step 1: Scaffold**

```bash
cd /Users/torbjorntest/projects/boligvelger
npm create vite@latest app -- --template react-ts
cd app && npm install
npm i three @react-three/fiber @react-three/drei zustand
npm i -D vitest @types/three
```

- [ ] **Step 2: Legg til test-script**

I `app/package.json` scripts: `"test": "vitest run"`.

- [ ] **Step 3: Failing test for NOK-format**

`app/src/lib/format.test.ts`:
```ts
import { describe, it, expect } from 'vitest';
import { formatNOK } from './format';

describe('formatNOK', () => {
  it('formats millions with thin spaces and em-dash øre', () => {
    expect(formatNOK(6400000)).toBe('6 400 000,—');
  });
  it('formats price per sqm', () => {
    expect(formatNOK(230000)).toBe('230 000,—');
  });
});
```

- [ ] **Step 4: Kjør — forvent FAIL**

Run: `npm test` → FAIL ("Cannot find module './format'")

- [ ] **Step 5: Implementer**

`app/src/lib/format.ts`:
```ts
export function formatNOK(n: number): string {
  return n.toLocaleString('nb-NO').replace(/ /g, ' ') + ',—';
}
```

- [ ] **Step 6: Kjør — forvent PASS**, så commit

```bash
git add app
git commit -m "Scaffold velger app with vite, r3f and vitest"
```

---

### Task 2: Autorerte datakilder (prisliste, site, building)

**Files:**
- Create: `tools/velger-data/prisliste.json`, `tools/velger-data/site.json`, `tools/velger-data/building.json`

- [ ] **Step 1: prisliste.json** — nøyaktig fra «Verdivurdering utsalgspriser Dybwads gate 8.docx» (09.01.26). Etasje for H0201 korrigert til 2 (skrivefeil i docx); etasje følger uansett arkitektdata i build.

```json
{
  "H0101": {"navn": "Leilighet 1",  "braI": 15, "braU": 30, "kvmPris": 230000, "kvmPrisU": 80000, "pris": 5850000},
  "H0102": {"navn": "Leilighet 2",  "braI": 20, "kvmPris": 240000, "pris": 4800000},
  "H0103": {"navn": "Leilighet 3",  "braI": 23, "braU": 33, "kvmPris": 180000, "kvmPrisU": 80000, "pris": 6780000},
  "H0104": {"navn": "Leilighet 4",  "braI": 33, "kvmPris": 180000, "pris": 5940000},
  "H0105": {"navn": "Leilighet 5",  "braI": 30, "kvmPris": 190000, "pris": 5700000},
  "H0201": {"navn": "Leilighet 6",  "braI": 19, "kvmPris": 260000, "pris": 4940000},
  "H0202": {"navn": "Leilighet 7",  "braI": 19, "kvmPris": 260000, "pris": 4940000},
  "H0203": {"navn": "Leilighet 8",  "braI": 27, "kvmPris": 200000, "pris": 5400000},
  "H0204": {"navn": "Leilighet 9",  "braI": 32, "kvmPris": 200000, "pris": 6400000},
  "H0205": {"navn": "Leilighet 10", "braI": 30, "kvmPris": 230000, "pris": 6900000},
  "H0301": {"navn": "Leilighet 11", "braI": 16, "kvmPris": 265000, "pris": 4240000},
  "H0302": {"navn": "Leilighet 12", "braI": 22, "kvmPris": 250000, "pris": 5500000},
  "H0303": {"navn": "Leilighet 13", "braI": 28, "kvmPris": 230000, "pris": 6440000},
  "H0304": {"navn": "Leilighet 14", "braI": 24, "kvmPris": 250000, "pris": 6000000},
  "H0305": {"navn": "Leilighet 15", "braI": 22, "kvmPris": 250000, "pris": 5500000},
  "H0306": {"navn": "Leilighet 16", "braI": 22, "kvmPris": 270000, "pris": 5940000}
}
```

- [ ] **Step 2: site.json**

```json
{
  "tittel": "Dybwads gate 8",
  "undertittel": "16 selveierleiligheter · Majorstuen",
  "ingress": "Totalrenoverte selveierleiligheter med svært god takhøyde i en rolig boliggate ved Majorstuveien. Høy og eksklusiv standard på materialer og utstyr.",
  "kontakt": {
    "navn": "Torbjørn Skjelde",
    "tittel": "Eiendomsmegler MNEF / Partner",
    "telefon": "932 61 665",
    "epost": "t.skjelde@nordvikbolig.no"
  }
}
```

- [ ] **Step 3: building.json (startverdier — kalibreres i Task 3/4)**

Mål etasjehøyder i `eiendommer/dybwads gate 8/arkitekt/Snitt_C.pdf` (åpne, les koter). Startverdier til kalibrering:

```json
{
  "scale": 0.01,
  "floorOrder": ["U", "1", "2", "3"],
  "floors": {
    "U": {"label": "Underetasje", "height": 2.5},
    "1": {"label": "1. etasje", "height": 3.1},
    "2": {"label": "2. etasje", "height": 3.1},
    "3": {"label": "3. etasje", "height": 3.4}
  },
  "slabThickness": 0.3,
  "roof": {"volumes": [{"poly": "FYLLES-I-TASK-3-FRA-ETASJE-3-OUTLINE", "height": 0.6, "inset": 0}]},
  "windows": []
}
```

`windows` fylles fra fasade-PDF-ene i Task 8 (kan stå tom — appen skal tåle tom liste). `roof.volumes[].poly` erstattes med faktisk polygon i Task 3.

- [ ] **Step 4: Commit**

```bash
git add tools/velger-data
git commit -m "Add authored price list, site config and building parameters"
```

---

### Task 3: Etasje-geometri — generator, QA-overlay, autorering

**Files:**
- Create: `tools/velger-data/gen_floors.py`, `tools/velger-data/qa_overlay.py`, `tools/velger-data/floors/etasje-{u,1,2,3}.json`
- Create: `eiendommer/dybwads gate 8/underlag/etasje-u-plan.svg` + PNG

- [ ] **Step 1: Underetasje-underlag**

```bash
cd "/Users/torbjorntest/projects/boligvelger/eiendommer/dybwads gate 8"
pdftocairo -svg arkitekt/Underetasje.pdf underlag/etasje-u-plan.svg
pdftocairo -png -r 150 arkitekt/Underetasje.pdf underlag/etasje-u-plan
```
Expected: `underlag/etasje-u-plan.svg` og `underlag/etasje-u-plan-1.png` finnes.

- [ ] **Step 2: gen_floors.py — skjelett fra eksisterende specs**

```python
#!/usr/bin/env python3
"""Generate initial floor JSON skeletons from plantegning specs + crop positions.

Unit polygons = spec envelope translated by crop_px offset. Floor outline =
convex-ish bbox hull placeholder, to be hand-traced against underlag PNG.
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
        floors.setdefault(str(u["floor"]), []).append({"id": hnr, "unit": hnr, "poly": poly})
    for fid, units in floors.items():
        xs = [p[0] for un in units for p in un["poly"]]
        ys = [p[1] for un in units for p in un["poly"]]
        doc = {
            "id": fid,
            "outline": [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]],
            "units": units,
            "common": [],
        }
        path = OUT / f"etasje-{fid}.json"
        path.write_text(json.dumps(doc, indent=1))
        print(f"wrote {path.name}: {len(units)} units")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Kjør generatoren**

Run: `python3 tools/velger-data/gen_floors.py`
Expected: `etasje-1.json: 5 units`, `etasje-2.json: 5 units`, `etasje-3.json: 6 units`.

- [ ] **Step 4: qa_overlay.py — visuell kontroll mot underlag**

```python
#!/usr/bin/env python3
"""Emit one HTML file per floor: underlag PNG with floor JSON polygons overlaid."""
import base64, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNDERLAG = ROOT / "eiendommer/dybwads gate 8/underlag"
FLOORS = Path(__file__).resolve().parent / "floors"
QA = Path(__file__).resolve().parent / "qa"
QA.mkdir(exist_ok=True)

PNG_FOR = {"u": "etasje-u-plan-1.png", "1": "etasje-1-plan-1.png",
           "2": "etasje-2-plan-1.png", "3": "etasje-3-plan-1.png"}

def svg_poly(poly, color, label=""):
    pts = " ".join(f"{x},{y}" for x, y in poly)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    t = (f'<text x="{cx}" y="{cy}" fill="{color}" font-size="40" '
         f'text-anchor="middle">{label}</text>') if label else ""
    return (f'<polygon points="{pts}" fill="{color}" fill-opacity="0.25" '
            f'stroke="{color}" stroke-width="4"/>{t}')

def main():
    for fid, png_name in PNG_FOR.items():
        fpath = FLOORS / f"etasje-{fid}.json"
        if not fpath.exists():
            continue
        doc = json.loads(fpath.read_text())
        png = UNDERLAG / png_name
        b64 = base64.b64encode(png.read_bytes()).decode()
        shapes = [svg_poly(doc["outline"], "#cc4400")]
        shapes += [svg_poly(u["poly"], "#1E7A4B", u["unit"]) for u in doc["units"]]
        shapes += [svg_poly(c, "#3355bb") for c in doc.get("common", [])]
        # PNG is 150dpi render of same PDF as the SVG user units; scale factor px->png
        html = f"""<!doctype html><meta charset="utf-8">
<style>body{{margin:0}} .wrap{{position:relative}} img{{display:block;width:100%}}
svg{{position:absolute;inset:0;width:100%;height:100%}}</style>
<div class="wrap"><img src="data:image/png;base64,{b64}">
<svg viewBox="0 0 VIEWW VIEWH" preserveAspectRatio="none">{''.join(shapes)}</svg></div>"""
        # determine viewBox from PNG size so polygon space maps 1:1 onto the image
        from struct import unpack
        w, h = unpack(">II", png.read_bytes()[16:24])
        html = html.replace("VIEWW", str(w)).replace("VIEWH", str(h))
        out = QA / f"etasje-{fid}.html"
        out.write_text(html)
        print(f"wrote {out}")

if __name__ == "__main__":
    main()
```

**Merk:** Hvis crop_px-rommet IKKE matcher PNG-pikselrommet 1:1, legg en `"pngScale"`-faktor i hver floor-JSON og multipliser i `qa_overlay.py`. Avgjør empirisk i Step 5 (polygonene skal ligge oppå riktige enheter).

- [ ] **Step 5: Kjør overlay og inspiser i fullskala**

```bash
python3 tools/velger-data/qa_overlay.py
```
Screenshot hver HTML i headless Chrome (1600px bred) og SE på bildene. Sjekkliste per etasje: (1) hver enhets polygon ligger over riktig enhet i arkitektplanen, (2) outline følger yttervegg, (3) ingen overlapp mellom enheter.

- [ ] **Step 6: Trace og juster for hånd**

Juster `floors/etasje-{1,2,3}.json`: outline trace etter yttervegg i underlaget (8–16 punkter per etasje er nok — gips-massing, ikke målebrev). Legg korridor/fellesareal som `common`-polygoner. Author `floors/etasje-u.json` manuelt fra `etasje-u-plan-1.png`: outline + to salgbare volumer `H0101-U` og `H0103-U` (`"unit": "H0101"` / `"H0103"`) + resten som common (boder). Re-kjør Step 5 til overlay er ren.

- [ ] **Step 7: Kalibrer scale + roof**

Mål målestokk-baren i underlaget (kjent meterlengde → px) og sett `building.json.scale`. Sett `roof.volumes[0].poly` = etasje-3-outline (kopiér punktene inn). Sanity: outline-areal for etasje 1 × scale² ≈ 130–160 m².

- [ ] **Step 8: Commit**

```bash
git add tools/velger-data "eiendommer/dybwads gate 8/underlag"
git commit -m "Add floor geometry specs with QA overlay against architect plans"
```

---

### Task 4: build_data.py — validering og emit

**Files:**
- Create: `tools/velger-data/build_data.py`, `tools/velger-data/test_build_data.py`

- [ ] **Step 1: Failing tests**

`tools/velger-data/test_build_data.py`:
```python
import json
from pathlib import Path

import build_data


def test_price_sum_validates():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    errors, _ = build_data.validate_prisliste(prisliste)
    assert errors == []


def test_price_sum_error_on_tamper():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    prisliste["H0101"]["pris"] += 1
    errors, _ = build_data.validate_prisliste(prisliste)
    assert any("91270000" in e for e in errors)


def test_bra_sum_includes_duplex_u():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    assert build_data.bra_sum(prisliste) == 445


def test_units_match_rentegning_and_floors():
    errors = build_data.validate_coverage()
    assert errors == []


def test_build_units_merges_architect_data():
    units = build_data.build_units()
    assert units["H0101"]["pris"] == 5850000
    assert units["H0101"]["etasje"] == 1
    assert units["H0101"]["duplex"] is True
    assert units["H0204"]["braArkitekt"] == 32.4 or units["H0204"]["braArkitekt"] > 0
    assert units["H0201"]["etasje"] == 2  # docx-skrivefeilen skal være overstyrt
```

Run: `cd tools/velger-data && python3 -m pytest -q` → FAIL (no module build_data).

- [ ] **Step 2: Implementer build_data.py**

```python
#!/usr/bin/env python3
"""Validate authored sources and emit app data for the 3D boligvelger."""
import json
import shutil
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
            "etasje": a["floor"],          # arkitektdata er autoritativ for etasje
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
```

- [ ] **Step 3: Kjør testene — forvent PASS** (juster `test_build_units_merges_architect_data` sin braArkitekt-assert til faktisk verdi fra units.json)

Run: `cd tools/velger-data && python3 -m pytest -q` → PASS

- [ ] **Step 4: Kjør build**

Run: `python3 tools/velger-data/build_data.py`
Expected: `OK: wrote .../app/public/data/dybwads-gate-8`, evt. WARN-linjer for BRA-avvik (H0103: 23 vs 26.5 er ventet).

- [ ] **Step 5: Commit**

```bash
git add tools/velger-data app/public/data
git commit -m "Add data build with price and coverage validation"
```

---

### Task 5: Delte typer, shapes og datalasting

**Files:**
- Create: `app/src/lib/types.ts`, `app/src/lib/shapes.ts`, `app/src/lib/shapes.test.ts`, `app/src/lib/data.ts`, `app/src/lib/webgl.ts`

- [ ] **Step 1: types.ts**

```ts
export type FloorId = 'U' | '1' | '2' | '3';
export type UnitStatus = 'ledig' | 'reservert' | 'solgt';

export interface UnitGeo { id: string; unit: string; poly: [number, number][]; }
export interface FloorGeo {
  id: FloorId; label: string; elevation: number; height: number;
  outline: [number, number][]; units: UnitGeo[]; common: [number, number][][];
}
export interface RoofGeo { elevation: number; volumes: { poly: [number, number][]; height: number }[]; }
export interface WindowGeo { floor: FloorId; edge: number; t: number; width: number; sill: number; height: number; }
export interface BuildingGeo {
  scale: number; slabThickness: number; floors: FloorGeo[]; roof: RoofGeo; windows: WindowGeo[];
}

export interface Rom { name: string; area: number; }
export interface UnitInfo {
  id: string; navn: string; type: string; etasje: number; duplex: boolean;
  braI: number; braU: number | null; braArkitekt: number; hemsCa: number | null;
  rom: Rom[]; pris: number; kvmPris: number; kvmPrisU: number | null;
}

export interface SiteConfig {
  tittel: string; undertittel: string; ingress: string;
  kontakt: { navn: string; tittel: string; telefon: string; epost: string };
}

export interface AppData { geo: BuildingGeo; units: Record<string, UnitInfo>; site: SiteConfig; }
```

- [ ] **Step 2: Failing tests for shapes**

`app/src/lib/shapes.test.ts`:
```ts
import { describe, it, expect } from 'vitest';
import { polyToShape, polyCentroid } from './shapes';

const square: [number, number][] = [[0, 0], [100, 0], [100, 100], [0, 100]];

describe('polyToShape', () => {
  it('scales svg px to meters', () => {
    const shape = polyToShape(square, 0.01);
    const pts = shape.getPoints();
    expect(pts[0].x).toBe(0);
    expect(pts[1].x).toBeCloseTo(1);
    expect(pts[2].y).toBeCloseTo(1);
  });
});

describe('polyCentroid', () => {
  it('finds center of square', () => {
    expect(polyCentroid(square)).toEqual([50, 50]);
  });
});
```

Run: `npm test` → FAIL.

- [ ] **Step 3: shapes.ts**

```ts
import * as THREE from 'three';

export function polyToShape(poly: [number, number][], scale: number): THREE.Shape {
  const s = new THREE.Shape();
  poly.forEach(([x, y], i) => {
    if (i === 0) s.moveTo(x * scale, y * scale);
    else s.lineTo(x * scale, y * scale);
  });
  s.closePath();
  return s;
}

export function polyCentroid(poly: [number, number][]): [number, number] {
  const n = poly.length;
  const sx = poly.reduce((a, p) => a + p[0], 0);
  const sy = poly.reduce((a, p) => a + p[1], 0);
  return [sx / n, sy / n];
}
```

- [ ] **Step 4: Kjør — PASS.**

- [ ] **Step 5: data.ts + webgl.ts (ingen test — tynne wrappere)**

`app/src/lib/data.ts`:
```ts
import type { AppData, UnitStatus } from './types';

const BASE = '/data/dybwads-gate-8';

export async function loadAppData(): Promise<AppData> {
  const [geo, units, site] = await Promise.all([
    fetch(`${BASE}/geometri.json`).then(r => r.json()),
    fetch(`${BASE}/units.json`).then(r => r.json()),
    fetch(`${BASE}/site.json`).then(r => r.json()),
  ]);
  return { geo, units, site };
}

export function planSvgUrl(unitId: string): string { return `${BASE}/plan/${unitId}-plan.svg`; }
export function hemsSvgUrl(unitId: string): string { return `${BASE}/plan/${unitId}-hems.svg`; }
export function pdfUrl(unitId: string): string { return `${BASE}/pdf/${unitId}.pdf`; }

export async function fetchStatus(): Promise<Record<string, UnitStatus>> {
  const r = await fetch('/api/status');
  if (!r.ok) throw new Error(`status ${r.status}`);
  return r.json();
}
```

`app/src/lib/webgl.ts`:
```ts
export function detectWebGL(): boolean {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch {
    return false;
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add app/src/lib
git commit -m "Add shared types, shape helpers and data loaders"
```

---

### Task 6: State store + QA-param

**Files:**
- Create: `app/src/state/store.ts`, `app/src/state/store.test.ts`, `app/src/lib/qa.ts`, `app/src/lib/qa.test.ts`

- [ ] **Step 1: Failing store-tester**

`app/src/state/store.test.ts`:
```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useVelger } from './store';

beforeEach(() => useVelger.getState().reset());

describe('velger store', () => {
  it('starts in landing mode', () => {
    expect(useVelger.getState().mode).toBe('landing');
  });
  it('explode sets mode and focus', () => {
    useVelger.getState().explode('2');
    expect(useVelger.getState().mode).toBe('exploded');
    expect(useVelger.getState().focus).toBe('2');
  });
  it('assemble clears selection and focus', () => {
    useVelger.getState().explode('all');
    useVelger.getState().select('H0204');
    useVelger.getState().assemble();
    const s = useVelger.getState();
    expect(s.mode).toBe('orbit');
    expect(s.selected).toBeNull();
    expect(s.focus).toBe('all');
  });
  it('selecting a unit in landing promotes to exploded', () => {
    useVelger.getState().select('H0101');
    expect(useVelger.getState().mode).toBe('exploded');
  });
});
```

Run: `npm test` → FAIL.

- [ ] **Step 2: store.ts**

```ts
import { create } from 'zustand';
import type { UnitStatus } from '../lib/types';

export type Mode = 'landing' | 'orbit' | 'exploded';
export type FloorFocus = 'all' | 'U1' | '2' | '3';

interface VelgerState {
  mode: Mode;
  focus: FloorFocus;
  hovered: string | null;
  selected: string | null;
  status: Record<string, UnitStatus>;
  setMode: (m: Mode) => void;
  explode: (f: FloorFocus) => void;
  assemble: () => void;
  setHovered: (id: string | null) => void;
  select: (id: string | null) => void;
  setStatus: (s: Record<string, UnitStatus>) => void;
  reset: () => void;
}

const initial = {
  mode: 'landing' as Mode,
  focus: 'all' as FloorFocus,
  hovered: null,
  selected: null,
  status: {},
};

export const useVelger = create<VelgerState>((set, get) => ({
  ...initial,
  setMode: (mode) => set({ mode }),
  explode: (focus) => set({ mode: 'exploded', focus }),
  assemble: () => set({ mode: 'orbit', focus: 'all', selected: null }),
  setHovered: (hovered) => set({ hovered }),
  select: (selected) => {
    if (selected && get().mode !== 'exploded') set({ mode: 'exploded' });
    set({ selected });
  },
  setStatus: (status) => set({ status }),
  reset: () => set(initial),
}));
```

- [ ] **Step 3: Kjør — PASS.**

- [ ] **Step 4: qa.ts + test**

`app/src/lib/qa.test.ts`:
```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { applyQaParam } from './qa';
import { useVelger } from '../state/store';

beforeEach(() => useVelger.getState().reset());

describe('applyQaParam', () => {
  it('exploded → exploded all', () => {
    applyQaParam('exploded');
    expect(useVelger.getState().mode).toBe('exploded');
  });
  it('floor2 → exploded with focus 2', () => {
    applyQaParam('floor2');
    expect(useVelger.getState().focus).toBe('2');
  });
  it('unit-H0204 → selects unit', () => {
    applyQaParam('unit-H0204');
    expect(useVelger.getState().selected).toBe('H0204');
  });
  it('null is a no-op', () => {
    applyQaParam(null);
    expect(useVelger.getState().mode).toBe('landing');
  });
});
```

`app/src/lib/qa.ts`:
```ts
import { useVelger } from '../state/store';

/** Maps ?qa= URL param to store state, for deterministic QA screenshots. */
export function applyQaParam(param: string | null): void {
  if (!param) return;
  const s = useVelger.getState();
  if (param === 'orbit') s.setMode('orbit');
  else if (param === 'exploded') s.explode('all');
  else if (param === 'floorU1') s.explode('U1');
  else if (param === 'floor2') s.explode('2');
  else if (param === 'floor3') s.explode('3');
  else if (param.startsWith('unit-')) s.select(param.slice(5));
}
```

- [ ] **Step 5: Kjør — PASS, commit**

```bash
git add app/src/state app/src/lib/qa.ts app/src/lib/qa.test.ts
git commit -m "Add velger state store and qa url param hook"
```

---

### Task 7: 3D-scenen — Building, FloorPlate, UnitMesh, Roof

**Files:**
- Create: `app/src/scene/VelgerCanvas.tsx`, `app/src/scene/Building.tsx`, `app/src/scene/FloorPlate.tsx`, `app/src/scene/UnitMesh.tsx`, `app/src/scene/Roof.tsx`
- Modify: `app/src/App.tsx`, `app/src/main.tsx`, `app/src/styles.css` (erstatt Vite-demo)

Visuell verifisering (ikke unit-tests) — screenshots i Step 6.

- [ ] **Step 1: Palett og materialer (modulkonstanter i UnitMesh.tsx/FloorPlate.tsx)**

```ts
// shared palette — gips/galleri style
export const GIPS = '#f3f1ea';
export const GIPS_DARK = '#e5e2d6';
export const GREEN = '#1E3D2B';
export const GREEN_HOVER = '#2e5c44';
export const SOLGT_GRAY = '#b9b6ac';
export const CREAM_BG = '#FBFAF6';
```

- [ ] **Step 2: UnitMesh.tsx**

```tsx
import { useMemo } from 'react';
import * as THREE from 'three';
import { useVelger } from '../state/store';
import { polyToShape } from '../lib/shapes';
import type { UnitGeo } from '../lib/types';

export const GIPS = '#f3f1ea';
export const GREEN = '#1E3D2B';
export const GREEN_HOVER = '#2e5c44';
export const SOLGT_GRAY = '#b9b6ac';

interface Props { unit: UnitGeo; scale: number; height: number; dimmed: boolean; }

export function UnitMesh({ unit, scale, height, dimmed }: Props) {
  const hovered = useVelger(s => s.hovered === unit.unit);
  const selected = useVelger(s => s.selected === unit.unit);
  const status = useVelger(s => s.status[unit.unit] ?? 'ledig');
  const setHovered = useVelger(s => s.setHovered);
  const select = useVelger(s => s.select);

  const geometry = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(polyToShape(unit.poly, scale), {
      depth: height, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2); // svg-plan (x,y) -> (x, -z), extrusion -> +y
    return g;
  }, [unit, scale, height]);

  const color = selected || hovered
    ? (selected ? GREEN : GREEN_HOVER)
    : status === 'solgt' ? SOLGT_GRAY : GIPS;

  return (
    <mesh
      geometry={geometry}
      castShadow
      receiveShadow
      onPointerOver={(e) => { e.stopPropagation(); if (status !== 'solgt') setHovered(unit.unit); }}
      onPointerOut={() => setHovered(null)}
      onClick={(e) => { e.stopPropagation(); if (status !== 'solgt') select(unit.unit); }}
    >
      <meshStandardMaterial
        color={color}
        roughness={0.85}
        metalness={0}
        transparent={dimmed}
        opacity={dimmed ? 0.25 : 1}
        emissive={selected || hovered ? GREEN : '#000000'}
        emissiveIntensity={selected ? 0.35 : hovered ? 0.2 : 0}
      />
    </mesh>
  );
}
```

- [ ] **Step 3: FloorPlate.tsx — slab + common + units + eksplosjons-Y**

```tsx
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger, type FloorFocus, type Mode } from '../state/store';
import { polyToShape } from '../lib/shapes';
import { UnitMesh } from './UnitMesh';
import type { FloorGeo } from '../lib/types';

const GIPS_DARK = '#e5e2d6';
const EXPLODE_GAP = 2.2; // extra meters of air per floor index when exploded

export function explodedY(mode: Mode, elevation: number, index: number): number {
  return mode === 'exploded' ? elevation + index * EXPLODE_GAP : elevation;
}

export function floorIsFocused(focus: FloorFocus, floorId: string): boolean {
  if (focus === 'all') return true;
  if (focus === 'U1') return floorId === 'U' || floorId === '1';
  return focus === floorId;
}

interface Props { floor: FloorGeo; index: number; scale: number; slab: number; }

export function FloorPlate({ floor, index, scale, slab }: Props) {
  const ref = useRef<THREE.Group>(null!);
  const mode = useVelger(s => s.mode);
  const focus = useVelger(s => s.focus);
  const dimmed = mode === 'exploded' && !floorIsFocused(focus, floor.id);

  const slabGeo = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(polyToShape(floor.outline, scale), {
      depth: slab, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2);
    return g;
  }, [floor, scale, slab]);

  const commonGeos = useMemo(() => floor.common.map(poly => {
    const g = new THREE.ExtrudeGeometry(polyToShape(poly, scale), {
      depth: floor.height - slab, bevelEnabled: false,
    });
    g.rotateX(-Math.PI / 2);
    return g;
  }), [floor, scale, slab]);

  useFrame((_, dt) => {
    const target = explodedY(mode, floor.elevation, index);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, target, 3.5, dt);
  });

  return (
    <group ref={ref} position-y={floor.elevation}>
      <mesh geometry={slabGeo} castShadow receiveShadow>
        <meshStandardMaterial color={GIPS_DARK} roughness={0.9} transparent={dimmed} opacity={dimmed ? 0.25 : 1} />
      </mesh>
      <group position-y={slab}>
        {commonGeos.map((g, i) => (
          <mesh key={i} geometry={g} receiveShadow>
            <meshStandardMaterial color={GIPS_DARK} roughness={0.9} transparent={dimmed} opacity={dimmed ? 0.2 : 0.6} />
          </mesh>
        ))}
        {floor.units.map(u => (
          <UnitMesh key={u.id} unit={u} scale={scale} height={floor.height - slab} dimmed={dimmed} />
        ))}
      </group>
    </group>
  );
}
```

**Merk:** `ExtrudeGeometry` + `rotateX(-π/2)` gir y opp og svg-y langs −z; det speiler plan-geometrien. Sjekk i Step 6-screenshot at bygget ikke er speilvendt mot situasjonsplanen — hvis speilet, negér z i `polyToShape`-kallet ved å bruke en `flipY`-variant: `s.lineTo(x*scale, -y*scale)`. Velg én variant og bruk den konsekvent i alle tre geometri-stedene (slab, common, unit, roof).

- [ ] **Step 4: Roof.tsx + Building.tsx**

`app/src/scene/Roof.tsx`:
```tsx
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';
import { polyToShape } from '../lib/shapes';
import { explodedY } from './FloorPlate';
import type { RoofGeo } from '../lib/types';

export function Roof({ roof, scale, index }: { roof: RoofGeo; scale: number; index: number }) {
  const ref = useRef<THREE.Group>(null!);
  const mode = useVelger(s => s.mode);
  const geos = useMemo(() => roof.volumes.map(v => {
    const g = new THREE.ExtrudeGeometry(polyToShape(v.poly, scale), { depth: v.height, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
  }), [roof, scale]);
  useFrame((_, dt) => {
    const target = explodedY(mode, roof.elevation, index);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, target, 3.5, dt);
  });
  return (
    <group ref={ref} position-y={roof.elevation}>
      {geos.map((g, i) => (
        <mesh key={i} geometry={g} castShadow>
          <meshStandardMaterial color="#efece1" roughness={0.9} />
        </mesh>
      ))}
    </group>
  );
}
```

`app/src/scene/Building.tsx`:
```tsx
import { useMemo } from 'react';
import { polyCentroid } from '../lib/shapes';
import { FloorPlate } from './FloorPlate';
import { Roof } from './Roof';
import type { BuildingGeo } from '../lib/types';

export function Building({ geo }: { geo: BuildingGeo }) {
  // center the model on origin using ground floor outline centroid
  const [cx, cz] = useMemo(() => {
    const [px, py] = polyCentroid(geo.floors[0].outline);
    return [px * geo.scale, py * geo.scale];
  }, [geo]);
  return (
    <group position={[-cx, 0, cz]}>
      {geo.floors.map((f, i) => (
        <FloorPlate key={f.id} floor={f} index={i} scale={geo.scale} slab={geo.slabThickness} />
      ))}
      <Roof roof={geo.roof} scale={geo.scale} index={geo.floors.length} />
    </group>
  );
}
```

(Fortegnet på `cz` følger flip-valget fra Step 3 — verifiseres visuelt.)

- [ ] **Step 5: VelgerCanvas.tsx + App.tsx**

`app/src/scene/VelgerCanvas.tsx`:
```tsx
import { Canvas } from '@react-three/fiber';
import { ContactShadows, Environment } from '@react-three/drei';
import { Building } from './Building';
import { CameraRig } from './CameraRig';
import type { AppData } from '../lib/types';

const CREAM_BG = '#FBFAF6';

export function VelgerCanvas({ data }: { data: AppData }) {
  return (
    <Canvas
      shadows
      dpr={[1, Math.min(2, window.devicePixelRatio)]}
      camera={{ position: [18, 12, 18], fov: 35 }}
      style={{ background: CREAM_BG }}
    >
      <ambientLight intensity={0.55} />
      <directionalLight position={[12, 20, 8]} intensity={1.1} castShadow
        shadow-mapSize={[1024, 1024]} />
      <Environment preset="city" environmentIntensity={0.25} />
      <Building geo={data.geo} />
      <ContactShadows position={[0, -0.01, 0]} opacity={0.35} scale={45} blur={2.2} far={12} resolution={512} />
      <CameraRig />
    </Canvas>
  );
}
```

`app/src/App.tsx` (midlertidig CameraRig-stub i denne tasken):
```tsx
import { useEffect, useState } from 'react';
import { VelgerCanvas } from './scene/VelgerCanvas';
import { loadAppData } from './lib/data';
import { applyQaParam } from './lib/qa';
import type { AppData } from './lib/types';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  useEffect(() => { loadAppData().then(setData); }, []);
  useEffect(() => {
    if (data) applyQaParam(new URLSearchParams(location.search).get('qa'));
  }, [data]);
  if (!data) return null;
  return (
    <section className="hero">
      <VelgerCanvas data={data} />
    </section>
  );
}
```

`app/src/scene/CameraRig.tsx` (stub, erstattes i Task 8):
```tsx
import { OrbitControls } from '@react-three/drei';
export function CameraRig() {
  return <OrbitControls makeDefault enableDamping />;
}
```

`app/src/styles.css` (erstatt alt):
```css
* { box-sizing: border-box; margin: 0; }
html, body, #root { height: 100%; }
body { background: #FBFAF6; color: #1E3D2B; font-family: Georgia, serif; }
.hero { position: relative; height: 100vh; height: 100dvh; }
.hero canvas { touch-action: none; }
```

Sørg for at `main.tsx` importerer `./styles.css` og fjern Vite-demofilene (`App.css`, logoer).

- [ ] **Step 6: Visuell verifisering i fullskala**

```bash
cd app && npm run dev &
sleep 3
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --screenshot=/tmp/velger-orbit.png --window-size=1440,900 --virtual-time-budget=8000 \
  --user-data-dir=/tmp/velger-chrome "http://localhost:5173/?qa=orbit"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --screenshot=/tmp/velger-exploded.png --window-size=1440,900 --virtual-time-budget=8000 \
  --user-data-dir=/tmp/velger-chrome2 "http://localhost:5173/?qa=exploded"
```
LES bildene i full størrelse. Sjekkliste: bygget sentrert, ikke speilvendt (sammenlign med `Situasjonsplan.pdf`), etasjene stables tett i orbit, sprer seg i exploded, enheter synlige som volumer, myk skygge under.

- [ ] **Step 7: Commit**

```bash
git add app/src
git commit -m "Add 3d building scene with exploding floor plates"
```

---

### Task 8: CameraRig — landing/orbit/eksplosjon-koreografi + vinduer

**Files:**
- Create: `app/src/scene/Windows.tsx`
- Modify: `app/src/scene/CameraRig.tsx` (erstatt stub), `app/src/scene/Building.tsx`, `tools/velger-data/building.json`

- [ ] **Step 1: CameraRig med CameraControls**

```tsx
import { useEffect, useRef } from 'react';
import { CameraControls } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';

const VIEWS = {
  landing: { pos: [16, 9, 16], target: [0, 5, 0] },
  orbit: { pos: [16, 9, 16], target: [0, 5, 0] },
  exploded: { pos: [14, 16, 14], target: [0, 8, 0] },
} as const;

export function CameraRig() {
  const ref = useRef<CameraControls>(null!);
  const mode = useVelger(s => s.mode);
  const setMode = useVelger(s => s.setMode);

  // slow auto-rotate while landing; first user interaction promotes to orbit
  useFrame((_, dt) => {
    if (mode === 'landing') ref.current.azimuthAngle += dt * 0.12;
  });

  useEffect(() => {
    const v = VIEWS[mode];
    ref.current.setLookAt(v.pos[0], v.pos[1], v.pos[2], v.target[0], v.target[1], v.target[2], true);
  }, [mode]);

  useEffect(() => {
    const c = ref.current;
    const onStart = () => { if (useVelger.getState().mode === 'landing') setMode('orbit'); };
    c.addEventListener('controlstart', onStart);
    return () => c.removeEventListener('controlstart', onStart);
  }, [setMode]);

  return (
    <CameraControls
      ref={ref}
      makeDefault
      minDistance={8}
      maxDistance={45}
      maxPolarAngle={Math.PI / 2.05}
      smoothTime={0.4}
    />
  );
}
```

- [ ] **Step 2: Vinduer fra fasade-PDF-ene**

Les `Fasade_mot_Dybwads_gate.pdf`, `Fasade_soeroest.pdf`, `Fasade_soervest.pdf`. Tell vinduer per fasade per etasje og fyll `building.json.windows` med poster `{floor, edge, t, width, sill, height}` der `edge` er indeks i etasjens outline (kant nr.) og `t` er 0–1-posisjon langs kanten. Eksempel:

```json
"windows": [
  {"floor": "1", "edge": 0, "t": 0.18, "width": 1.1, "sill": 0.9, "height": 1.6},
  {"floor": "1", "edge": 0, "t": 0.38, "width": 1.1, "sill": 0.9, "height": 1.6}
]
```

- [ ] **Step 3: Windows.tsx — innfelte nisjer**

```tsx
import { useMemo } from 'react';
import * as THREE from 'three';
import type { BuildingGeo, WindowGeo } from '../lib/types';

const NICHE = '#d6d2c4';

/** Window niches: thin dark boxes positioned along an outline edge, slightly
 *  inset into the facade so they read as openings on the gips model. */
export function Windows({ geo }: { geo: BuildingGeo }) {
  const boxes = useMemo(() => geo.windows.map((w: WindowGeo) => {
    const floor = geo.floors.find(f => f.id === w.floor)!;
    const o = floor.outline;
    const a = o[w.edge];
    const b = o[(w.edge + 1) % o.length];
    const ax = a[0] * geo.scale, az = a[1] * geo.scale;
    const bx = b[0] * geo.scale, bz = b[1] * geo.scale;
    const x = ax + (bx - ax) * w.t;
    const z = az + (bz - az) * w.t;
    const angle = Math.atan2(bz - az, bx - ax);
    return { x, z, angle, y: floor.elevation + w.sill + w.height / 2, w: w.width, h: w.height, floorId: w.floor };
  }), [geo]);
  return (
    <group>
      {boxes.map((b, i) => (
        <mesh key={i} position={[b.x, b.y, b.z]} rotation={[0, -b.angle, 0]}>
          <boxGeometry args={[b.w, b.h, 0.12]} />
          <meshStandardMaterial color={NICHE} roughness={1} />
        </mesh>
      ))}
    </group>
  );
}
```

Monter `<Windows geo={geo} />` i `Building.tsx` (innenfor samme sentrerings-group). **Kjent begrensning:** nisjene følger ikke etasjeplatene i eksplodert visning i denne versjonen — de hører til fasademassen og kan skjules når mode === 'exploded': hent mode fra store og returner `null`.

- [ ] **Step 4: Visuell verifisering** — samme screenshots som Task 7 Step 6 (`?qa=orbit`, `?qa=exploded`) + ett uten param (landing, auto-rotert litt). Sjekk: kamera-overgang gir mening, vinduer ser ut som nisjer, vinduer borte i exploded.

- [ ] **Step 5: Commit**

```bash
git add app/src tools/velger-data/building.json
git commit -m "Add camera choreography and facade window niches"
```

---

### Task 9: HUD — tittel, hint, etasje-chips, tooltip

**Files:**
- Create: `app/src/ui/Hud.tsx`, `app/src/ui/FloorChips.tsx`, `app/src/ui/UnitTooltip.tsx`
- Modify: `app/src/App.tsx`, `app/src/scene/Building.tsx`, `app/src/styles.css`

- [ ] **Step 1: Kopier brand-fonter**

```bash
mkdir -p app/public/fonts
# finn eksakte filnavn først:
ls "brand houeland 2-0/01 Fonter/"
# kopier Sfizia Regular/Bold og Engravers Gothic (woff2/otf) inn:
cp "brand houeland 2-0/01 Fonter/"Sfizia* "brand houeland 2-0/01 Fonter/"*Engravers* app/public/fonts/
```

`styles.css` (legg til, juster filnavn til de faktiske):
```css
@font-face { font-family: 'Sfizia'; src: url('/fonts/Sfizia-Regular.otf'); font-weight: 400; }
@font-face { font-family: 'Sfizia'; src: url('/fonts/Sfizia-Bold.otf'); font-weight: 700; }
@font-face { font-family: 'Engravers'; src: url('/fonts/EngraversGothic.otf'); }
```

- [ ] **Step 2: FloorChips.tsx**

```tsx
import { useVelger, type FloorFocus } from '../state/store';

const CHIPS: { id: FloorFocus | 'assemble'; label: string }[] = [
  { id: 'U1', label: '1. etg' },
  { id: '2', label: '2. etg' },
  { id: '3', label: '3. etg' },
  { id: 'all', label: 'Alle 16' },
  { id: 'assemble', label: 'Samle bygget' },
];

export function FloorChips() {
  const mode = useVelger(s => s.mode);
  const focus = useVelger(s => s.focus);
  const explode = useVelger(s => s.explode);
  const assemble = useVelger(s => s.assemble);
  return (
    <nav className="chips">
      {CHIPS.map(c => {
        if (c.id === 'assemble') {
          if (mode !== 'exploded') return null;
          return <button key={c.id} className="chip" onClick={assemble}>{c.label}</button>;
        }
        const active = mode === 'exploded' && focus === c.id;
        return (
          <button key={c.id} className={`chip${active ? ' active' : ''}`}
            onClick={() => explode(c.id as FloorFocus)}>{c.label}</button>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 3: Hud.tsx**

```tsx
import { useVelger } from '../state/store';
import { FloorChips } from './FloorChips';
import type { AppData } from '../lib/types';

export function Hud({ data }: { data: AppData }) {
  const mode = useVelger(s => s.mode);
  return (
    <div className="hud">
      <header className={`hud-title${mode === 'landing' ? '' : ' compact'}`}>
        <h1>{data.site.tittel}</h1>
        <p>{data.site.undertittel}</p>
      </header>
      {mode === 'landing' && <p className="hint">Dra for å utforske</p>}
      <FloorChips />
    </div>
  );
}
```

- [ ] **Step 4: UnitTooltip.tsx (rendres INNE i Canvas via drei Html)**

```tsx
import { Html } from '@react-three/drei';
import { useVelger } from '../state/store';
import { formatNOK } from '../lib/format';
import { polyCentroid } from '../lib/shapes';
import type { AppData, FloorGeo } from '../lib/types';

export function UnitTooltip({ data }: { data: AppData }) {
  const hovered = useVelger(s => s.hovered);
  if (!hovered) return null;
  const info = data.units[hovered];
  const floor = data.geo.floors.find((f: FloorGeo) => f.units.some(u => u.unit === hovered));
  if (!info || !floor) return null;
  const unitGeo = floor.units.find(u => u.unit === hovered)!;
  const [cx, cz] = polyCentroid(unitGeo.poly);
  return (
    <Html position={[cx * data.geo.scale, floor.elevation + floor.height + 0.4, cz * data.geo.scale]}
      center distanceFactor={18} style={{ pointerEvents: 'none' }}>
      <div className="tooltip">
        <strong>{info.id} · {info.braI} m²</strong>
        <span>{formatNOK(info.pris)}</span>
      </div>
    </Html>
  );
}
```

**Posisjonskoordinatene må bruke samme sentrering/flip som `Building.tsx`** — monter derfor `<UnitTooltip>` som barn av samme `<group>` i Building (send `data` ned), ikke som søsken i Canvas.

- [ ] **Step 5: CSS for hud/chips/tooltip (legg til i styles.css)**

```css
.hud { position: absolute; inset: 0; pointer-events: none; display: flex; flex-direction: column; align-items: center; }
.hud-title { margin-top: 7vh; text-align: center; transition: all .5s; }
.hud-title h1 { font-family: 'Sfizia', Georgia, serif; font-weight: 400; font-size: clamp(2rem, 5vw, 3.5rem); letter-spacing: .12em; }
.hud-title p { font-family: 'Engravers', Georgia, serif; letter-spacing: .25em; font-size: .8rem; margin-top: .5rem; text-transform: uppercase; }
.hud-title.compact { margin-top: 2.5vh; transform: scale(.62); }
.hint { position: absolute; bottom: 14vh; font-style: italic; opacity: .6; animation: pulse 2.5s infinite; }
@keyframes pulse { 50% { opacity: .25; } }
.chips { position: absolute; bottom: 4vh; display: flex; gap: .6rem; pointer-events: auto; }
.chip { font-family: 'Engravers', Georgia, serif; letter-spacing: .12em; font-size: .75rem;
  padding: .55rem 1.1rem; border-radius: 999px; border: 1px solid #1E3D2B; background: transparent;
  color: #1E3D2B; cursor: pointer; }
.chip.active, .chip:hover { background: #1E3D2B; color: #FBFAF6; }
.tooltip { background: #1E3D2B; color: #FBFAF6; padding: .5rem .8rem; border-radius: 6px;
  display: flex; flex-direction: column; font-size: .8rem; white-space: nowrap; }
.tooltip span { color: #e8c87a; }
```

- [ ] **Step 6: Monter komponentene**

`App.tsx`: `<Hud data={data} />` som søsken til `<VelgerCanvas>`. Tooltipen skal inn i Buildings sentrerings-group (samme koordinatrom) — endre `Building.tsx` til å ta `data`:

```tsx
import { UnitTooltip } from '../ui/UnitTooltip';
import type { AppData } from '../lib/types';

export function Building({ data }: { data: AppData }) {
  const geo = data.geo;
  // ...uendret sentrering og floors/roof-mapping...
  return (
    <group position={[-cx, 0, cz]}>
      {/* floors + roof som før */}
      <UnitTooltip data={data} />
    </group>
  );
}
```
Oppdater kallet i `VelgerCanvas.tsx` til `<Building data={data} />`.

Visuell verifisering: screenshots `?qa=orbit` (tittel + chips) og `?qa=floor2` (fokusert etasje, andre dimmet). Hover kan ikke screenshotes headless — verifiseres i click-testen (Task 13).

- [ ] **Step 7: Commit**

```bash
git add app/src app/public/fonts app/src/styles.css
git commit -m "Add hud with title, floor chips and unit tooltip"
```

---

### Task 10: UnitPanel + status-integrasjon

**Files:**
- Create: `app/src/ui/UnitPanel.tsx`
- Modify: `app/src/App.tsx`, `app/src/styles.css`

- [ ] **Step 1: UnitPanel.tsx**

```tsx
import { useVelger } from '../state/store';
import { formatNOK } from '../lib/format';
import { planSvgUrl, hemsSvgUrl, pdfUrl } from '../lib/data';
import type { AppData } from '../lib/types';

const STATUS_LABEL = { ledig: 'Ledig', reservert: 'Reservert', solgt: 'Solgt' } as const;

export function UnitPanel({ data }: { data: AppData }) {
  const selected = useVelger(s => s.selected);
  const status = useVelger(s => (selected ? s.status[selected] ?? 'ledig' : 'ledig'));
  const select = useVelger(s => s.select);
  if (!selected) return null;
  const u = data.units[selected];
  const k = data.site.kontakt;
  return (
    <aside className="panel" data-testid="unit-panel">
      <header className="panel-head">
        <div>
          <h2 data-testid="panel-id">{u.id}</h2>
          <p>{u.type} · {u.etasje}. etasje · <span className={`badge ${status}`}>{STATUS_LABEL[status]}</span></p>
        </div>
        <button className="close" onClick={() => select(null)} aria-label="Lukk">×</button>
      </header>
      <div className="panel-body">
        <a href={planSvgUrl(u.id)} target="_blank" rel="noreferrer" title="Åpne i full størrelse">
          <img className="plan" src={planSvgUrl(u.id)} alt={`Plantegning ${u.id}`} />
        </a>
        {u.hemsCa != null && <img className="plan hems" src={hemsSvgUrl(u.id)} alt={`Hems ${u.id}`} />}
        <dl>
          <dt>BRA-i</dt><dd>{u.braI} m²{u.braU ? ` + ${u.braU} m² (U)` : ''}</dd>
          {u.hemsCa != null && <><dt>Hems (ikke målbart)</dt><dd>ca {u.hemsCa} m²</dd></>}
          <dt>Pris</dt><dd data-testid="panel-pris">{formatNOK(u.pris)}</dd>
          <dt>Pris/m²</dt><dd>{formatNOK(u.kvmPris)}</dd>
        </dl>
        {u.duplex && <p className="duplex-note">Duplex: egen del i underetasjen med uteplass og parkering.</p>}
      </div>
      <footer className="panel-foot">
        <a className="cta" href={`mailto:${k.epost}?subject=${encodeURIComponent(`Dybwads gate 8 – ${u.id}`)}`}>Kontakt megler</a>
        <a className="cta ghost" href={pdfUrl(u.id)} download>Plantegning PDF</a>
        <p className="kontakt">{k.navn} · {k.telefon}</p>
      </footer>
    </aside>
  );
}
```

- [ ] **Step 2: Panel-CSS inkl. mobil bottom-sheet (legg til i styles.css)**

```css
.panel { position: absolute; top: 0; right: 0; height: 100%; width: min(420px, 92vw);
  background: #fff; border-left: 1px solid #d8d4c8; display: flex; flex-direction: column;
  box-shadow: -12px 0 40px rgba(30, 61, 43, .08); }
.panel-head { background: #1E3D2B; color: #FBFAF6; padding: 1.1rem 1.3rem; display: flex; justify-content: space-between; }
.panel-head h2 { font-family: 'Sfizia', serif; font-weight: 400; letter-spacing: .08em; }
.panel-head p { font-family: 'Engravers', serif; font-size: .65rem; letter-spacing: .2em; text-transform: uppercase; margin-top: .3rem; }
.badge.ledig { color: #9fd4b6; } .badge.reservert { color: #e8c87a; } .badge.solgt { color: #c4c0b2; }
.close { background: none; border: 0; color: #FBFAF6; font-size: 1.4rem; cursor: pointer; }
.panel-body { flex: 1; overflow-y: auto; padding: 1.2rem; }
.plan { width: 100%; background: #FBFAF6; border: 1px solid #eee9dd; border-radius: 4px; }
.plan.hems { width: 55%; margin-top: .6rem; }
.panel-body dl { display: grid; grid-template-columns: auto 1fr; gap: .35rem 1rem; margin-top: 1rem; }
.panel-body dt { opacity: .6; } .panel-body dd { text-align: right; }
.duplex-note { margin-top: .8rem; font-style: italic; font-size: .85rem; opacity: .75; }
.panel-foot { padding: 1.1rem 1.3rem; border-top: 1px solid #eee9dd; display: grid; gap: .5rem; }
.cta { display: block; text-align: center; padding: .8rem; background: #1E3D2B; color: #FBFAF6;
  text-decoration: none; font-family: 'Engravers', serif; letter-spacing: .18em; font-size: .7rem; text-transform: uppercase; }
.cta.ghost { background: transparent; color: #1E3D2B; border: 1px solid #1E3D2B; }
.kontakt { text-align: center; font-size: .8rem; opacity: .65; }
@media (max-width: 768px) {
  .panel { top: auto; bottom: 0; height: 72vh; width: 100%; border-left: 0;
    border-top: 1px solid #d8d4c8; border-radius: 16px 16px 0 0; }
  .chips { bottom: 2vh; flex-wrap: wrap; justify-content: center; padding: 0 1rem; }
}
```

- [ ] **Step 3: Status-fetch i App.tsx**

Legg til i `App.tsx` (graceful fail — catch er tom med vilje):
```tsx
import { fetchStatus } from './lib/data';
import { useVelger } from './state/store';
import { UnitPanel } from './ui/UnitPanel';
// inne i App():
useEffect(() => {
  fetchStatus().then(s => useVelger.getState().setStatus(s)).catch(() => { /* status er valgfritt */ });
}, []);
// i JSX, inne i .hero:
<UnitPanel data={data} />
```

- [ ] **Step 4: Visuell verifisering** — screenshot `?qa=unit-H0204` desktop (1440×900) og mobil (390×844, `--window-size=390,844`): panel åpent med plantegning, pris `6 400 000,—`, bottom-sheet på mobil.

- [ ] **Step 5: Commit**

```bash
git add app/src
git commit -m "Add unit panel with floor plan, price and status"
```

---

### Task 11: Fallback uten WebGL + one-pager-seksjoner

**Files:**
- Create: `app/src/ui/FallbackList.tsx`, `app/src/ui/InfoSections.tsx`
- Modify: `app/src/App.tsx`, `app/src/styles.css`

- [ ] **Step 1: FallbackList.tsx**

```tsx
import { formatNOK } from '../lib/format';
import { planSvgUrl, pdfUrl } from '../lib/data';
import { useVelger } from '../state/store';
import type { AppData } from '../lib/types';

export function FallbackList({ data }: { data: AppData }) {
  const status = useVelger(s => s.status);
  const byFloor = [1, 2, 3].map(e => ({
    etasje: e,
    units: Object.values(data.units).filter(u => u.etasje === e),
  }));
  return (
    <main className="fallback">
      <h1>{data.site.tittel}</h1>
      <p>{data.site.undertittel}</p>
      {byFloor.map(f => (
        <section key={f.etasje}>
          <h2>{f.etasje}. etasje</h2>
          {f.units.map(u => (
            <article key={u.id} className="f-unit">
              <img src={planSvgUrl(u.id)} alt={`Plantegning ${u.id}`} loading="lazy" />
              <div>
                <h3>{u.id} · {u.braI} m²</h3>
                <p>{formatNOK(u.pris)} · {status[u.id] ?? 'ledig'}</p>
                <a href={pdfUrl(u.id)} download>Plantegning PDF</a>
              </div>
            </article>
          ))}
        </section>
      ))}
    </main>
  );
}
```

- [ ] **Step 2: InfoSections.tsx**

```tsx
import type { SiteConfig } from '../lib/types';

export function InfoSections({ site }: { site: SiteConfig }) {
  return (
    <>
      <section className="info">
        <h2>Om prosjektet</h2>
        <p>{site.ingress}</p>
      </section>
      <section className="info alt">
        <h2>Beliggenhet</h2>
        <p>Rolig boliggate ved Majorstuveien med kort gangavstand til Bogstadveien,
           Majorstuen stasjon og byens beste utvalg av kaféer og service.</p>
      </section>
      <section className="info">
        <h2>Kontakt</h2>
        <p>{site.kontakt.navn}<br />{site.kontakt.tittel}<br />
          <a href={`tel:${site.kontakt.telefon.replace(/ /g, '')}`}>{site.kontakt.telefon}</a> ·{' '}
          <a href={`mailto:${site.kontakt.epost}`}>{site.kontakt.epost}</a></p>
      </section>
    </>
  );
}
```

CSS (legg til):
```css
.info { padding: 14vh 8vw; max-width: 720px; margin: 0 auto; text-align: center; }
.info h2 { font-family: 'Sfizia', serif; font-weight: 400; font-size: 1.8rem; letter-spacing: .1em; margin-bottom: 1.2rem; }
.info p { line-height: 1.7; opacity: .85; }
.info.alt { background: #f3f1ea; max-width: none; }
.info.alt p { max-width: 720px; margin: 0 auto; }
.fallback { padding: 8vh 6vw; max-width: 880px; margin: 0 auto; }
.fallback h2 { margin: 2.5rem 0 1rem; font-family: 'Sfizia', serif; font-weight: 400; }
.f-unit { display: grid; grid-template-columns: 180px 1fr; gap: 1.2rem; padding: 1rem 0; border-bottom: 1px solid #e5e2d6; align-items: center; }
.f-unit img { width: 100%; }
```

- [ ] **Step 3: Koble inn i App.tsx (endelig form)**

```tsx
import { useEffect, useState } from 'react';
import { VelgerCanvas } from './scene/VelgerCanvas';
import { Hud } from './ui/Hud';
import { UnitPanel } from './ui/UnitPanel';
import { FallbackList } from './ui/FallbackList';
import { InfoSections } from './ui/InfoSections';
import { loadAppData, fetchStatus } from './lib/data';
import { detectWebGL } from './lib/webgl';
import { applyQaParam } from './lib/qa';
import { useVelger } from './state/store';
import type { AppData } from './lib/types';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [webgl] = useState(detectWebGL);
  useEffect(() => { loadAppData().then(setData); }, []);
  useEffect(() => {
    fetchStatus().then(s => useVelger.getState().setStatus(s)).catch(() => { /* valgfritt */ });
  }, []);
  useEffect(() => {
    if (data) applyQaParam(new URLSearchParams(location.search).get('qa'));
  }, [data]);
  if (!data) return null;
  if (!webgl) return <FallbackList data={data} />;
  return (
    <>
      <section className="hero">
        <VelgerCanvas data={data} />
        <Hud data={data} />
        <UnitPanel data={data} />
      </section>
      <InfoSections site={data.site} />
    </>
  );
}
```

- [ ] **Step 4: Verifiser fallback** — i headless: `--use-gl=disabled` er upålitelig for å tvinge WebGL av; test heller med midlertidig `?qa=`-uavhengig override: kjør `npm test` + visuell sjekk ved å midlertidig hardkode `webgl=false` lokalt (ikke commit). Screenshot fallback-listen.

- [ ] **Step 5: Sett `<title>` og OG-tags i `app/index.html`**

```html
<title>Dybwads gate 8 — 16 selveierleiligheter på Majorstuen</title>
<meta property="og:title" content="Dybwads gate 8 — boligvelger" />
<meta property="og:description" content="Utforsk 16 totalrenoverte selveierleiligheter i 3D." />
```

- [ ] **Step 6: Commit**

```bash
git add app
git commit -m "Add webgl fallback list and one-pager info sections"
```

---

### Task 12: Worker — status-API, admin, static assets

**Files:**
- Create: `worker/package.json`, `worker/wrangler.jsonc`, `worker/tsconfig.json`, `worker/src/index.ts`, `worker/src/admin.ts`, `worker/test/api.test.ts`

- [ ] **Step 1: Scaffold**

```bash
mkdir -p worker/src worker/test && cd worker
npm init -y
npm i -D wrangler vitest typescript @cloudflare/workers-types
```
`worker/package.json` scripts: `"test": "vitest run", "dev": "wrangler dev", "deploy": "wrangler deploy"`.

- [ ] **Step 2: Failing API-tester**

`worker/test/api.test.ts`:
```ts
import { describe, it, expect } from 'vitest';
import worker from '../src/index';

function mockEnv(initial: Record<string, string> = {}) {
  const store = new Map<string, string>([['units', JSON.stringify(initial)]]);
  return {
    ADMIN_PASSWORD: 'hemmelig',
    STATUS: {
      get: async (k: string, _t?: string) => {
        const v = store.get(k);
        return v ? JSON.parse(v) : null;
      },
      put: async (k: string, v: string) => { store.set(k, v); },
    },
    ASSETS: { fetch: async () => new Response('asset') },
  } as never;
}

describe('/api/status', () => {
  it('GET returns stored status', async () => {
    const env = mockEnv({ H0101: 'solgt' });
    const res = await worker.fetch(new Request('https://x/api/status'), env);
    expect(await res.json()).toEqual({ H0101: 'solgt' });
  });
  it('POST without password is 401', async () => {
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST', body: JSON.stringify({ unit: 'H0101', status: 'solgt' }),
    }), mockEnv());
    expect(res.status).toBe(401);
  });
  it('POST with password updates status', async () => {
    const env = mockEnv();
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST',
      headers: { 'x-admin-password': 'hemmelig' },
      body: JSON.stringify({ unit: 'H0204', status: 'reservert' }),
    }), env);
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ H0204: 'reservert' });
  });
  it('POST rejects invalid unit or status', async () => {
    const env = mockEnv();
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST',
      headers: { 'x-admin-password': 'hemmelig' },
      body: JSON.stringify({ unit: 'DROP TABLE', status: 'solgt' }),
    }), env);
    expect(res.status).toBe(400);
  });
  it('/admin serves html', async () => {
    const res = await worker.fetch(new Request('https://x/admin'), mockEnv());
    expect(res.headers.get('content-type')).toContain('text/html');
  });
  it('other paths go to assets', async () => {
    const res = await worker.fetch(new Request('https://x/'), mockEnv());
    expect(await res.text()).toBe('asset');
  });
});
```

Run: `npm test` → FAIL.

- [ ] **Step 3: src/index.ts**

```ts
import { ADMIN_HTML } from './admin';

export interface Env {
  ASSETS: Fetcher;
  STATUS: KVNamespace;
  ADMIN_PASSWORD: string;
}

const VALID_STATUS = new Set(['ledig', 'reservert', 'solgt']);
const UNIT_RE = /^H0[1-3]0[1-6]$/;

async function getAll(env: Env): Promise<Record<string, string>> {
  return (await env.STATUS.get('units', 'json')) ?? {};
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === '/api/status') {
      if (req.method === 'GET') {
        return Response.json(await getAll(env), {
          headers: { 'cache-control': 'no-store' },
        });
      }
      if (req.method === 'POST') {
        if (req.headers.get('x-admin-password') !== env.ADMIN_PASSWORD) {
          return new Response('unauthorized', { status: 401 });
        }
        let body: { unit?: string; status?: string };
        try { body = await req.json(); } catch { return new Response('bad json', { status: 400 }); }
        if (!body.unit || !UNIT_RE.test(body.unit) || !body.status || !VALID_STATUS.has(body.status)) {
          return new Response('bad request', { status: 400 });
        }
        const all = await getAll(env);
        all[body.unit] = body.status;
        await env.STATUS.put('units', JSON.stringify(all));
        return Response.json(all);
      }
      return new Response('method not allowed', { status: 405 });
    }

    if (url.pathname === '/admin') {
      return new Response(ADMIN_HTML, { headers: { 'content-type': 'text/html;charset=utf-8' } });
    }

    return env.ASSETS.fetch(req);
  },
};
```

- [ ] **Step 4: src/admin.ts**

```ts
export const ADMIN_HTML = `<!doctype html><html lang="no"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Admin — Dybwads gate 8</title>
<style>
body{font-family:Georgia,serif;background:#FBFAF6;color:#1E3D2B;max-width:640px;margin:3rem auto;padding:0 1rem}
h1{font-weight:400;letter-spacing:.1em}
input{padding:.5rem;border:1px solid #d8d4c8;width:100%;margin:.8rem 0 1.5rem}
table{width:100%;border-collapse:collapse}
td,th{padding:.5rem;border-bottom:1px solid #e5e2d6;text-align:left}
button{padding:.35rem .8rem;border:1px solid #1E3D2B;background:none;color:#1E3D2B;cursor:pointer;border-radius:999px;margin-right:.3rem}
button.on{background:#1E3D2B;color:#FBFAF6}
#msg{margin-top:1rem;font-style:italic}
</style>
<h1>Dybwads gate 8 — status</h1>
<input id="pw" type="password" placeholder="Admin-passord">
<table id="t"><tr><th>Enhet</th><th>Status</th></tr></table>
<p id="msg"></p>
<script>
const UNITS = ["H0101","H0102","H0103","H0104","H0105","H0201","H0202","H0203","H0204","H0205","H0301","H0302","H0303","H0304","H0305","H0306"];
const STATES = ["ledig","reservert","solgt"];
const pw = document.getElementById('pw');
pw.value = sessionStorage.getItem('pw') || '';
pw.onchange = () => sessionStorage.setItem('pw', pw.value);
let current = {};
async function load(){
  current = await (await fetch('/api/status')).json();
  render();
}
function render(){
  const t = document.getElementById('t');
  t.innerHTML = '<tr><th>Enhet</th><th>Status</th></tr>' + UNITS.map(u => '<tr><td>'+u+'</td><td>' +
    STATES.map(s => '<button class="'+((current[u]||'ledig')===s?'on':'')+'" onclick="setStatus(\\''+u+'\\',\\''+s+'\\')">'+s+'</button>').join('') +
    '</td></tr>').join('');
}
async function setStatus(unit, status){
  const r = await fetch('/api/status', { method:'POST',
    headers: {'x-admin-password': pw.value, 'content-type':'application/json'},
    body: JSON.stringify({unit, status}) });
  document.getElementById('msg').textContent = r.ok ? unit+' → '+status : 'Feil: '+r.status+' (sjekk passord)';
  if (r.ok) { current = await r.json(); render(); }
}
load();
</script></html>`;
```

- [ ] **Step 5: Kjør tester — PASS.**

- [ ] **Step 6: wrangler.jsonc + KV + secret**

```bash
cd worker && npx wrangler kv namespace create STATUS
```
Ta `id` fra outputen og skriv `worker/wrangler.jsonc`:
```jsonc
{
  "name": "boligvelger-dybwadsgate8",
  "main": "src/index.ts",
  "compatibility_date": "2026-05-01",
  "assets": { "directory": "../app/dist", "binding": "ASSETS", "not_found_handling": "single-page-application" },
  "kv_namespaces": [{ "binding": "STATUS", "id": "<id-fra-kommandoen-over>" }]
}
```
```bash
npx wrangler secret put ADMIN_PASSWORD   # interaktivt — Torbjørn velger passordet
```

- [ ] **Step 7: Commit**

```bash
git add worker
git commit -m "Add cloudflare worker with status api and admin page"
```

---

### Task 13: QA-harness — screenshots, topp-diff, klikktest

**Files:**
- Create: `tools/velger-qa/shots.sh`, `tools/velger-qa/click_units.mjs`
- Modify: `app/src/App.tsx` (window.__velger-eksponering), `app/src/lib/qa.ts`

- [ ] **Step 1: Eksponer test-API i appen**

I `App.tsx`, etter at data er lastet:
```tsx
useEffect(() => {
  if (!data) return;
  (window as never as Record<string, unknown>).__velger = {
    select: (id: string) => useVelger.getState().select(id),
    explode: (f: string) => useVelger.getState().explode(f as never),
    state: () => useVelger.getState(),
  };
}, [data]);
```

- [ ] **Step 2: shots.sh**

```bash
#!/bin/zsh
# Headless screenshots of all key states. Usage: shots.sh [base-url] [outdir]
set -e
BASE=${1:-http://localhost:4173}
OUT=${2:-/tmp/velger-qa}
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p "$OUT"
shot() {  # name url width height
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --screenshot="$OUT/$1.png" --window-size=$3,$4 --virtual-time-budget=9000 \
    --user-data-dir="$OUT/profile-$1" "$2" 2>/dev/null
  echo "$OUT/$1.png"
}
shot landing      "$BASE/"                 1440 900
shot orbit        "$BASE/?qa=orbit"        1440 900
shot exploded     "$BASE/?qa=exploded"     1440 900
shot floor2       "$BASE/?qa=floor2"       1440 900
shot panel        "$BASE/?qa=unit-H0204"   1440 900
shot mobil        "$BASE/?qa=exploded"     390  844
shot mobil-panel  "$BASE/?qa=unit-H0204"   390  844
```

- [ ] **Step 3: click_units.mjs (puppeteer-core mot system-Chrome)**

```bash
cd app && npm i -D puppeteer-core
```

```js
#!/usr/bin/env node
// Programmatically selects all 16 units and verifies the panel shows correct data.
import puppeteer from 'puppeteer-core';
import { readFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:4173';
const units = JSON.parse(readFileSync(new URL('../../app/public/data/dybwads-gate-8/units.json', import.meta.url)));

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: 'new',
});
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
await page.goto(BASE, { waitUntil: 'networkidle0' });
await page.waitForFunction('window.__velger !== undefined');

let failures = 0;
for (const [id, u] of Object.entries(units)) {
  await page.evaluate(i => window.__velger.select(i), id);
  await page.waitForSelector('[data-testid="unit-panel"]');
  const shownId = await page.$eval('[data-testid="panel-id"]', el => el.textContent);
  const shownPris = await page.$eval('[data-testid="panel-pris"]', el => el.textContent);
  const expectedPris = u.pris.toLocaleString('nb-NO').replace(/ /g, ' ') + ',—';
  const ok = shownId === id && shownPris === expectedPris;
  if (!ok) failures++;
  console.log(`${ok ? 'OK ' : 'FAIL'} ${id}: panel=${shownId} pris=${shownPris}`);
}
await browser.close();
if (failures) { console.error(`${failures} failures`); process.exit(1); }
console.log('All 16 units verified.');
```

- [ ] **Step 4: Kjør hele harnessen**

```bash
cd app && npm run build && npm run preview &   # port 4173
sleep 2
zsh tools/velger-qa/shots.sh
node tools/velger-qa/click_units.mjs
```
Expected: 7 PNG-er + `All 16 units verified.`

- [ ] **Step 5: Fullskala-review av alle screenshots** — LES hvert bilde i full størrelse (lærdom fra plantegningsprosjektet: småskala-review slipper gjennom feil). Sjekkliste: typografi (Sfizia laster), ingen overlappende UI, eksplosjonen leselig, panelet komplett, mobil-layout ikke knust, ingen z-fighting i geometrien.

- [ ] **Step 6: Topp-ortho-diff mot underlag** — manuell verifisering: screenshot `?qa=floor2` rett ovenfra er ikke implementert som egen kameramodus; bruk i stedet qa_overlay-HTML-ene fra Task 3 som geometri-fasit (de validerer polygonene som er identiske med dem 3D bruker). Noter i commit-melding at 3D-geometri == overlay-validerte polygoner.

- [ ] **Step 7: Commit**

```bash
git add tools/velger-qa app
git commit -m "Add qa harness with state screenshots and 16-unit click test"
```

---

### Task 14: Deploy + røyk-test

- [ ] **Step 1: Bygg og deploy**

```bash
cd app && npm run build
cd ../worker && npx wrangler deploy
```
Expected: workers.dev-URL i output.

- [ ] **Step 2: Røyk-test mot prod-URL**

```bash
URL=https://boligvelger-dybwadsgate8.<subdomain>.workers.dev
curl -s -o /dev/null -w "%{http_code}\n" $URL            # 200
curl -s $URL/api/status                                   # {} eller status-objekt
curl -s -o /dev/null -w "%{http_code}\n" $URL/admin       # 200
curl -s -X POST $URL/api/status -H 'x-admin-password: feil' -d '{}' -o /dev/null -w "%{http_code}\n"  # 401
zsh tools/velger-qa/shots.sh $URL /tmp/velger-prod
node tools/velger-qa/click_units.mjs $URL
```

- [ ] **Step 3: Sett én enhet via admin i ekte browser** (Torbjørn eller CDP): åpne `/admin`, sett H0101 → reservert, reload hovedsiden, verifiser badge.

- [ ] **Step 4: Final commit + melding til Torbjørn med URL**

```bash
git add -A app worker tools
git commit -m "Deploy boligvelger to workers.dev"
```

---

## Self-review-notater (innarbeidet)

- Prisliste-etasjekolonnen i docx er upålitelig (H0201 «1», H0104 «U») — `build_units()` bruker arkitektdata (`tools/plantegning/units.json`) som autoritativ etasjekilde. Avvik BRA prisliste↔arkitekt er WARN, ikke ERROR (forventet: H0101 15 vs 17.8, H0103 23 vs 26.5).
- Speil/flip-risiko i SVG→three-konvertering er flagget i Task 7 Step 3 med eksplisitt verifisering mot situasjonsplan.
- `UnitTooltip` må monteres i Buildings sentrerings-group, ikke i Canvas-rot (koordinatrom).
- Vindusnisjer skjules i eksplodert visning (bevisst forenkling v1).
- Hover-tilstand kan ikke verifiseres i statiske screenshots — dekkes av click-testens select() + visuell review av selected-state i panel-screenshot.
