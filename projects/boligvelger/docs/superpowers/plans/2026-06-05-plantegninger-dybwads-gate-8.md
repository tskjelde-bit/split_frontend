# Plantegningssider Dybwads gate 8 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce 16 branded floor plan pages (SVG + PDF, one per apartment) for Dybwads gate 8 from the architect's vector PDFs, in Houeland brand v4 style B ("grønn signatur").

**Architecture:** Hybrid pipeline — extract exact vector/raster underlay from architect PDFs, hand-trace each unit as a clean SVG fragment in real-world cm coordinates, then assemble final A4 SVG pages from a shared template + per-unit JSON data. PDF export via isolated headless Chrome.

**Tech Stack:** Python 3 (stdlib only), poppler (`pdftocairo`, `pdftoppm`, `pdfinfo`), ImageMagick (`magick`), headless Chrome. No web framework, no npm.

**Spec:** `docs/superpowers/specs/2026-06-05-plantegninger-dybwads-gate-8-design.md`

---

## File Structure

```
tools/plantegning/
  brand.py              # brand constants, font base64/CSS, shared paths
  fixtures.py           # SVG <defs> symbol library (WC, servant, dusj, seng, sofa, bord, kjøkken)
  extract_underlay.py   # arkitekt-PDF → per-etasje SVG + 200dpi PNG underlag
  crop_unit.py          # crop per-enhet PNG fra etasje-PNG (bbox fra units.json)
  build_pages.py        # rentegning + units.json + posisjon → ferdig A4 side-SVG
  make_qa.py            # QA-overlay HTML (rentegning over original-crop, 50% opacity)
  export_pdf.py         # side-SVG → A4 PDF via headless Chrome, 1-side-sjekk
  units.json            # all per-enhet data
  posisjon/
    etasje-1.svg        # forenklet mini-etasjeplan, én path per enhet med id="H01xx"
    etasje-2.svg
    etasje-3.svg
    snitt.svg           # forenklet bygningssnitt, bånd per etasje med id="floor-N"

eiendommer/dybwads gate 8/
  underlag/             # generert: etasje-SVG/PNG + per-enhet crops (gitignored)
  rentegning/           # håndtegnede rene plan-fragmenter: H0101-plan.svg, H0101-hems.svg
  plantegninger/        # FERDIG OUTPUT: H0101.svg + H0101.pdf … (16 × 2 filer)
  qa/                   # QA-overlays + screenshots (gitignored)
```

**Koordinatsystem (gjelder alle rentegning-filer):** 1 SVG-enhet = 1 cm virkelig verden. En leilighet på 5,2 m × 3,9 m får `viewBox="0 0 520 390"`. Sidemalen skalerer til 1:50 på A4: `k = (794/21)/50 = 0.7562` px per virkelig cm. Målestokk-baren blir dermed eksakt.

**Måle-prosedyre fra underlag-PNG (200 dpi, original 1:100):** 1 papir-tomme = 200 px = 2,54 cm papir = 2,54 m virkelig → **1 px = 1,27 cm virkelig**. Mål piksel-koordinater i crop-PNG-en, multipliser med 1,27, rund til nærmeste cm. Kontroller mot oppgitte rom-arealer (±5 %) før rentegning godkjennes.

---

### Task 0: Mappestruktur og gitignore

**Files:**
- Create: `tools/plantegning/posisjon/` (dir)
- Create: `.gitignore`

- [ ] **Step 1: Opprett mapper**

```bash
cd /Users/torbjorntest/projects/boligvelger
mkdir -p tools/plantegning/posisjon \
  "eiendommer/dybwads gate 8/underlag" \
  "eiendommer/dybwads gate 8/rentegning" \
  "eiendommer/dybwads gate 8/plantegninger" \
  "eiendommer/dybwads gate 8/qa"
```

- [ ] **Step 2: Skriv `.gitignore`**

```gitignore
.DS_Store
.superpowers/
eiendommer/*/underlag/
eiendommer/*/qa/
```

- [ ] **Step 3: Verifiser verktøy**

```bash
which pdftocairo pdftoppm pdfinfo magick && \
ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```
Expected: alle fire paths + Chrome-binæren. Hvis `pdfinfo` mangler: `brew install poppler` (men pdftoppm finnes allerede, så poppler er installert).

- [ ] **Step 4: Commit**

```bash
git add .gitignore && git commit -m "Add plantegning project structure and gitignore"
```

---

### Task 1: brand.py — konstanter og fonter

**Files:**
- Create: `tools/plantegning/brand.py`

- [ ] **Step 1: Skriv `brand.py`**

```python
"""Houeland brand v4 constants and font embedding for plantegning pipeline."""
import base64
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EIENDOM = REPO / "eiendommer" / "dybwads gate 8"
ARKITEKT = EIENDOM / "arkitekt"
UNDERLAG = EIENDOM / "underlag"
RENTEGNING = EIENDOM / "rentegning"
OUTPUT = EIENDOM / "plantegninger"
QA = EIENDOM / "qa"
FONT_DIR = REPO / "brand houeland 2-0" / "01 Fonter"

# Farger (stil B — grønn signatur)
GREEN = "#1E3D2B"
BRICK = "#8A3324"
CARAMEL = "#C58B53"
CREAM = "#FBFAF6"
BEIGE = "#EFE9DC"
INK = "#1A1A18"
ROOM_FILL = "#F4F1E8"
HEMS_FILL = "#E5D3BC"
TILE_FILL = "#DCE2D6"
MUTED = "#8C8678"
LIGHT_LINE = "#DDD7C8"
HEADER_TEXT = "#F2EFE8"
HEADER_MUTED = "#C9C2AE"

# Skala: A4-side er 794x1123 px (96dpi). 1:50 → 1 virkelig cm = 0.7562 px.
A4_W, A4_H = 794, 1123
PX_PER_CM = (A4_W / 21.0) / 50.0  # 0.75619...


def _font_b64(filename: str) -> str:
    return base64.b64encode((FONT_DIR / filename).read_bytes()).decode()


def font_css() -> str:
    """@font-face-blokk med base64-embeddede brand-fonter."""
    sfizia = _font_b64("Sfizia-Regular.otf")
    engravers = _font_b64("Engravers' Gothic Regular.otf")
    return (
        "@font-face{font-family:'Sfizia';"
        f"src:url(data:font/otf;base64,{sfizia}) format('opentype');}}\n"
        "@font-face{font-family:'Engravers';"
        f"src:url(data:font/otf;base64,{engravers}) format('opentype');}}"
    )
```

- [ ] **Step 2: Verifiser**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import sys; sys.path.insert(0, 'tools/plantegning')
import brand
css = brand.font_css()
assert 'Sfizia' in css and 'Engravers' in css and len(css) > 80000, len(css)
assert brand.ARKITEKT.is_dir(), brand.ARKITEKT
print('OK', round(brand.PX_PER_CM, 4))"
```
Expected: `OK 0.7562`

- [ ] **Step 3: Commit**

```bash
git add tools/plantegning/brand.py && git commit -m "Add brand constants and font embedding for plantegning pipeline"
```

---

### Task 2: extract_underlay.py — underlag fra arkitekt-PDF

**Files:**
- Create: `tools/plantegning/extract_underlay.py`

- [ ] **Step 1: Skriv `extract_underlay.py`**

```python
"""Ekstraher vektor-SVG og 200dpi PNG underlag fra arkitekt-PDFene."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand

SOURCES = {
    1: ["Plan_1_etasje.pdf", "Boenheter_1etasje.pdf"],
    2: ["Plan_2_etasje.pdf", "Boenheter_2_etasje.pdf"],
    3: ["Plan_3_etasje.pdf", "Boenheter_3_etasje.pdf"],
}


def main():
    brand.UNDERLAG.mkdir(exist_ok=True)
    for floor, files in SOURCES.items():
        for pdf_name in files:
            src = brand.ARKITEKT / pdf_name
            stem = f"etasje-{floor}-{'plan' if pdf_name.startswith('Plan') else 'boenheter'}"
            svg_out = brand.UNDERLAG / f"{stem}.svg"
            png_prefix = brand.UNDERLAG / stem
            subprocess.run(["pdftocairo", "-svg", str(src), str(svg_out)], check=True)
            subprocess.run(
                ["pdftoppm", "-png", "-r", "200", str(src), str(png_prefix)],
                check=True,
            )
            print(f"{stem}: svg={svg_out.stat().st_size}b")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Kjør og verifiser**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 tools/plantegning/extract_underlay.py && \
ls -la "eiendommer/dybwads gate 8/underlag/"
```
Expected: 6 SVG-filer + 6 PNG-filer (`etasje-{1,2,3}-{plan,boenheter}.svg` og `...-1.png`), alle > 50 KB. pdftoppm legger til `-1`-suffiks (side 1).

- [ ] **Step 3: Visuell sjekk av én PNG**

Les `eiendommer/dybwads gate 8/underlag/etasje-1-boenheter-1.png` med Read-verktøyet. Expected: tydelig etasjeplan med H01xx-merking, høy nok oppløsning til å måle vegger.

- [ ] **Step 4: Commit**

```bash
git add tools/plantegning/extract_underlay.py && git commit -m "Add underlay extraction from architect PDFs"
```

---

### Task 3: units.json — datagrunnlag for alle 16 enheter

**Files:**
- Create: `tools/plantegning/units.json`

- [ ] **Step 1: Skriv `units.json` med BRA fra Boenheter-tegningene (rev B)**

Felter som fylles ut senere (under rentegning per enhet) står som `null`/`[]`.
`crop_px` er `[x, y, bredde, høyde]` i piksler i etasje-boenheter-PNG-en.

```json
{
  "H0101": {"floor": 1, "bra": 17.8, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0102": {"floor": 1, "bra": 20.6, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0103": {"floor": 1, "bra": 26.5, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0104": {"floor": 1, "bra": 32.9, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0105": {"floor": 1, "bra": 30.0, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0201": {"floor": 2, "bra": 18.5, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0202": {"floor": 2, "bra": 19.3, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0203": {"floor": 2, "bra": 26.8, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0204": {"floor": 2, "bra": 31.8, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0205": {"floor": 2, "bra": 30.2, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0301": {"floor": 3, "bra": 16.4, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0302": {"floor": 3, "bra": 22.0, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0303": {"floor": 3, "bra": 27.5, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0304": {"floor": 3, "bra": 24.2, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0305": {"floor": 3, "bra": 22.2, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null},
  "H0306": {"floor": 3, "bra": 22.2, "type": null, "rooms": [], "hems": null, "north_deg": null, "crop_px": null}
}
```

- [ ] **Step 2: Valider kontrollsummer**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import json
u = json.load(open('tools/plantegning/units.json'))
for f, expected in [(1, 127.5), (2, 126.6), (3, 134.5)]:
    s = round(sum(v['bra'] for v in u.values() if v['floor'] == f), 1)
    print(f'etasje {f}: {s} (tegning: {expected})', 'OK' if s == expected else 'AVVIK')
assert len(u) == 16"
```
Expected: etasje 2 og 3 OK. **Etasje 1 gir 127,8 mot tegningens 127,5 — kjent avvik i arkitektens egne tall.** Per-enhet-verdiene er autoritative (de skal stå på sidene); avviket noteres i commit-meldingen og verifiseres mot PNG-underlaget under pilot-tracingen (Task 6) — sjekk om H0101 faktisk leser 17,5 i tegningen.

- [ ] **Step 3: Commit**

```bash
git add tools/plantegning/units.json && \
git commit -m "Add unit data skeleton for all 16 apartments

Floor 1 per-unit BRA sums to 127.8 vs architect's stated 127.5 control
sum. Per-unit values kept as drawn; verify H0101 against underlay during
pilot tracing."
```

---

### Task 4: fixtures.py — symbolbibliotek for møblering

**Files:**
- Create: `tools/plantegning/fixtures.py`

Alle symboler tegnes i cm-koordinater (1 enhet = 1 cm) med naturlig størrelse, origo øverst til venstre. Plasseres i rentegning med `<use href="#wc" transform="translate(x y) rotate(d cx cy)"/>`.

- [ ] **Step 1: Skriv `fixtures.py`**

```python
"""SVG <defs>-symboler for møblering og fast innredning. Alle mål i cm."""

INK = "#1A1A18"

DEFS = f"""<defs>
  <!-- WC: 40x65cm -->
  <g id="wc">
    <rect x="5" y="0" width="30" height="20" rx="3" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <ellipse cx="20" cy="42" rx="16" ry="21" fill="none" stroke="{INK}" stroke-width="1.2"/>
  </g>
  <!-- Servant: 50x40cm -->
  <g id="servant">
    <rect x="0" y="0" width="50" height="40" rx="4" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <ellipse cx="25" cy="20" rx="16" ry="11" fill="none" stroke="{INK}" stroke-width="1"/>
    <circle cx="25" cy="7" r="2" fill="{INK}"/>
  </g>
  <!-- Dusj: 90x90cm med diagonal og sluk -->
  <g id="dusj">
    <rect x="0" y="0" width="90" height="90" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <line x1="0" y1="90" x2="90" y2="0" stroke="{INK}" stroke-width="0.6" stroke-dasharray="4 3"/>
    <circle cx="45" cy="45" r="3" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Seng 140: 140x200cm -->
  <g id="seng140">
    <rect x="0" y="0" width="140" height="200" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <rect x="8" y="8" width="58" height="40" rx="6" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <rect x="74" y="8" width="58" height="40" rx="6" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <line x1="0" y1="60" x2="140" y2="60" stroke="{INK}" stroke-width="0.6"/>
  </g>
  <!-- Sofa 2-seter: 160x85cm -->
  <g id="sofa">
    <rect x="0" y="0" width="160" height="85" rx="10" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <line x1="14" y1="22" x2="146" y2="22" stroke="{INK}" stroke-width="0.7"/>
    <line x1="80" y1="22" x2="80" y2="85" stroke="{INK}" stroke-width="0.7"/>
  </g>
  <!-- Spisebord m/2 stoler: 120x75cm bord -->
  <g id="bord2">
    <rect x="0" y="20" width="120" height="75" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <rect x="32" y="0" width="45" height="16" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <rect x="32" y="99" width="45" height="16" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Kjøkkenbenk-segment 60cm dyp, 60cm bred m/komfyrtopp -->
  <g id="komfyr">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <circle cx="18" cy="18" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="42" cy="18" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="18" cy="42" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="42" cy="42" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Kjøkkenvask-segment 60x60cm -->
  <g id="kvask">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <rect x="12" y="12" width="36" height="36" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="30" cy="8" r="2" fill="{INK}"/>
  </g>
  <!-- Garderobeskap-segment 60x60cm -->
  <g id="skap">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <line x1="0" y1="0" x2="60" y2="60" stroke="{INK}" stroke-width="0.5"/>
  </g>
</defs>"""


def door(x: float, y: float, width: float, angle: float = 0, sweep: int = 1) -> str:
    """Dørslag: åpning ved (x,y), dørblad-bredde i cm, rotasjon i grader.

    Tegner karmlinje + kvartsirkelbue. sweep=1 høyrehengslet, 0 venstre.
    """
    end_x, end_y = (x + width, y) if sweep else (x - width, y)
    arc_y = y + width
    d = f"M {x} {arc_y} A {width} {width} 0 0 {sweep} {end_x} {end_y}"
    return (
        f'<g transform="rotate({angle} {x} {y})">'
        f'<line x1="{x}" y1="{y}" x2="{x}" y2="{arc_y}" stroke="{INK}" stroke-width="1"/>'
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="0.7"/></g>'
    )
```

- [ ] **Step 2: Verifiser at symbolene rendrer**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import sys; sys.path.insert(0, 'tools/plantegning')
import fixtures
uses = ''.join(f'<use href=\"#{s}\" x=\"{i*180}\" y=\"20\"/>' for i, s in enumerate(
    ['wc','servant','dusj','seng140','sofa','bord2','komfyr','kvask','skap']))
svg = f'<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1700 260\" style=\"background:#FBFAF6\">{fixtures.DEFS}{uses}{fixtures.door(100, 240, 80)}</svg>'
open('/tmp/fixtures-test.svg', 'w').write(svg)
print('OK')" && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --user-data-dir=/tmp/chrome-plantegning --screenshot=/tmp/fixtures-test.png \
  --window-size=1700,260 file:///tmp/fixtures-test.svg 2>/dev/null && echo screenshot OK
```
Expected: `OK` + `screenshot OK`. Les `/tmp/fixtures-test.png` med Read-verktøyet — alle 9 symboler + dørslag synlige og proporsjonale.

- [ ] **Step 3: Commit**

```bash
git add tools/plantegning/fixtures.py && git commit -m "Add SVG fixture symbol library for floor plan furniture"
```

---

### Task 5: Posisjonsdiagrammer — etasje-minis og snitt

**Files:**
- Create: `tools/plantegning/posisjon/etasje-1.svg`
- Create: `tools/plantegning/posisjon/etasje-2.svg`
- Create: `tools/plantegning/posisjon/etasje-3.svg`
- Create: `tools/plantegning/posisjon/snitt.svg`

Disse tegnes manuelt (forenklet) med Boenheter-PNG-ene som visuell referanse. Format: SVG-fragment med `viewBox`, bygningsomriss i `#B4AE9F` strek, én `<path>`/`<rect>` per enhet med `id="H0101"` osv., `fill="none"`. Byggets L-form mot Dybwads gate / Ole Fladagers gate skal være gjenkjennelig — nøyaktighet på romnivå er ikke nødvendig.

- [ ] **Step 1: Les referanse-PNG for 1. etasje**

Les `eiendommer/dybwads gate 8/underlag/etasje-1-boenheter-1.png`. Noter enhetenes omtrentlige posisjon i bygningskroppen.

- [ ] **Step 2: Tegn `etasje-1.svg`**

Skjelett (juster polygon-koordinater etter PNG-en — byggets fotavtrykk og enhetsgrensene skal stemme visuelt):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120">
  <path d="M 8 4 L 78 4 L 78 50 L 92 50 L 92 116 L 8 116 Z"
        fill="none" stroke="#B4AE9F" stroke-width="1.5"/>
  <path id="H0105" d="M 8 4 L 45 4 L 45 38 L 8 38 Z" fill="none"/>
  <path id="H0104" d="M 8 38 L 45 38 L 45 72 L 8 72 Z" fill="none"/>
  <path id="H0103" d="M 8 72 L 40 72 L 40 116 L 8 116 Z" fill="none"/>
  <path id="H0102" d="M 40 72 L 64 72 L 64 116 L 40 116 Z" fill="none"/>
  <path id="H0101" d="M 64 72 L 92 72 L 92 116 L 64 116 Z" fill="none"/>
</svg>
```

- [ ] **Step 3: Gjenta for etasje 2 og 3**

Les `etasje-2-boenheter-1.png` og `etasje-3-boenheter-1.png`, tegn `etasje-2.svg` (H0201–H0205) og `etasje-3.svg` (H0301–H0306) etter samme mønster. 3. etasje har 6 enheter.

- [ ] **Step 4: Tegn `snitt.svg`**

Les `eiendommer/dybwads gate 8/arkitekt/Snitt_C.pdf` (Read-verktøyet) for fasong. Forenklet snitt med skråtak og ett bånd per etasje:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 90">
  <path d="M 6 28 L 30 8 L 54 28 L 54 84 L 6 84 Z"
        fill="none" stroke="#B4AE9F" stroke-width="1.5"/>
  <rect id="floor-3" x="6" y="28" width="48" height="14" fill="none"/>
  <rect id="floor-2" x="6" y="42" width="48" height="14" fill="none"/>
  <rect id="floor-1" x="6" y="56" width="48" height="14" fill="none"/>
  <rect id="floor-u" x="6" y="70" width="48" height="14" fill="none"/>
  <line x1="6" y1="42" x2="54" y2="42" stroke="#B4AE9F" stroke-width="0.8"/>
  <line x1="6" y1="56" x2="54" y2="56" stroke="#B4AE9F" stroke-width="0.8"/>
  <line x1="6" y1="70" x2="54" y2="70" stroke="#B4AE9F" stroke-width="0.8"/>
</svg>
```

- [ ] **Step 5: Visuell sjekk**

```bash
cd /Users/torbjorntest/projects/boligvelger/tools/plantegning/posisjon && \
for f in etasje-1 etasje-2 etasje-3 snitt; do
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
    --user-data-dir=/tmp/chrome-plantegning --screenshot=/tmp/pos-$f.png \
    --window-size=300,400 "file://$PWD/$f.svg" 2>/dev/null
done && echo OK
```
Les de fire PNG-ene. Expected: gjenkjennelig L-formet fotavtrykk per etasje, snitt med 4 bånd.

- [ ] **Step 6: Commit**

```bash
git add tools/plantegning/posisjon/ && git commit -m "Add position diagram fragments for floors and section"
```

---

### Task 6: build_pages.py — sidemal med dummy-plan

**Files:**
- Create: `tools/plantegning/build_pages.py`

- [ ] **Step 1: Skriv `build_pages.py`**

```python
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


def scale_bar(x: float, y: float) -> str:
    seg = 100 * brand.PX_PER_CM  # 1 m
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
    etasje = (POSISJON / f"etasje-{floor}.svg").read_text()
    etasje = etasje.replace(f'id="{unit_id}" ', f'id="{unit_id}" fill="{brand.GREEN}" opacity="0.85" ').replace(
        f'id="{unit_id}"\n', f'id="{unit_id}" fill="{brand.GREEN}" opacity="0.85"\n')
    snitt = (POSISJON / "snitt.svg").read_text()
    snitt = snitt.replace(f'id="floor-{floor}"', f'id="floor-{floor}" fill="{brand.GREEN}" opacity="0.85"')

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
    k = brand.PX_PER_CM

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

    # Hovedplan, sentrert i plansonen (y 210-820), 1:50
    plan_svg, pw, ph = place(plan_path, 0, 0, k)
    hems = None
    if hems_path.exists():
        hems = place(hems_path, 0, 0, k)
    total_w = pw + (hems[1] + 40 if hems else 0)
    px = (brand.A4_W - total_w) / 2
    py = 210 + (610 - ph) / 2
    plan_svg, _, _ = place(plan_path, px, py, k)
    parts.append(plan_svg)
    if hems:
        hx = px + pw + 40
        hy = py + ph - hems[2]  # bunnjustert mot hovedplan
        hems_svg, hw, hh = place(hems_path, hx, hy, k)
        parts.append(hems_svg)
        parts.append(
            f'<text x="{hx + hw / 2:.0f}" y="{hy - 10:.0f}" font-family="Engravers" '
            f'font-size="8.5" letter-spacing="2" fill="{brand.MUTED}" '
            f'text-anchor="middle">HEMS</text>'
        )

    # Målestokk + nordpil
    parts.append(scale_bar(MARGIN, 855))
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
```

- [ ] **Step 2: Lag dummy-rentegning for test**

Skriv `eiendommer/dybwads gate 8/rentegning/TEST-plan.svg` (4,8 m × 4,0 m boks med ett rom):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 400">
  <rect x="0" y="0" width="480" height="400" fill="#F4F1E8"/>
  <rect x="0" y="0" width="480" height="400" fill="none" stroke="#1A1A18" stroke-width="10"/>
  <use href="#seng140" x="20" y="20"/>
  <text x="240" y="220" font-family="Helvetica" font-size="13" text-anchor="middle" fill="#1A1A18">Stue/sov</text>
  <text x="240" y="238" font-family="Helvetica" font-size="10" text-anchor="middle" fill="#1A1A18" opacity="0.65">15,0 m²</text>
</svg>
```

Og en testoppføring — kjør med midlertidig TEST-enhet i units.json **eller** test via Python direkte:

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import sys, json; sys.path.insert(0, 'tools/plantegning')
import build_pages, brand
u = {'floor': 1, 'bra': 17.8, 'type': '1-roms', 'rooms': [], 'hems': None, 'north_deg': 135, 'crop_px': None}
svg = build_pages.render_page('TEST', u)
(brand.OUTPUT / 'TEST.svg').write_text(svg)
print('OK', len(svg))"
```
Expected: `OK` + tall > 100000 (fontene er embeddet).

- [ ] **Step 3: Screenshot og visuell sjekk**

```bash
cd /Users/torbjorntest/projects/boligvelger && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --user-data-dir=/tmp/chrome-plantegning --screenshot=/tmp/page-test.png \
  --window-size=794,1123 "file://$PWD/eiendommer/dybwads gate 8/plantegninger/TEST.svg" 2>/dev/null && echo OK
```
Les `/tmp/page-test.png`. Expected: grønn header med "TEST" i Sfizia, dummy-plan sentrert, målestokk, nordpil, posisjonsdiagrammer (H-markering vil mangle for TEST — OK), footer. **Sfizia og Engravers skal synlig være brand-fontene, ikke fallback.**

- [ ] **Step 4: Rydd og commit**

```bash
cd /Users/torbjorntest/projects/boligvelger && \
rm "eiendommer/dybwads gate 8/rentegning/TEST-plan.svg" "eiendommer/dybwads gate 8/plantegninger/TEST.svg" && \
git add tools/plantegning/build_pages.py && \
git commit -m "Add page builder with style B template"
```

---

### Task 7: crop_unit.py og make_qa.py — verktøy for tracing-løkka

**Files:**
- Create: `tools/plantegning/crop_unit.py`
- Create: `tools/plantegning/make_qa.py`

- [ ] **Step 1: Skriv `crop_unit.py`**

```python
"""Crop per-enhet PNG fra etasje-underlag. Bruk: crop_unit.py H0101"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand


def main():
    uid = sys.argv[1]
    units = json.loads((Path(__file__).parent / "units.json").read_text())
    u = units[uid]
    x, y, w, h = u["crop_px"]
    src = brand.UNDERLAG / f"etasje-{u['floor']}-plan-1.png"
    out = brand.UNDERLAG / f"{uid}-crop.png"
    subprocess.run(
        ["magick", str(src), "-crop", f"{w}x{h}+{x}+{y}", "+repage", str(out)],
        check=True,
    )
    print(out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Skriv `make_qa.py`**

```python
"""QA-overlay: rentegning (50% opacity) over original-crop. Bruk: make_qa.py H0101"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand
import fixtures

# 200dpi-render av 1:100-tegning: 1 px = 1.27 cm virkelig -> 1 cm = 0.7874 px
PNG_PX_PER_CM = 200 / 2.54 / 100


def main():
    uid = sys.argv[1]
    crop = brand.UNDERLAG / f"{uid}-crop.png"
    plan = brand.RENTEGNING / f"{uid}-plan.svg"
    html = f"""<!DOCTYPE html><html><head><style>
body {{ margin: 0; background: #888; }}
.stack {{ position: relative; display: inline-block; }}
.stack img {{ display: block; }}
.stack svg {{ position: absolute; left: 0; top: 0; opacity: 0.55; }}
</style></head><body><div class="stack">
<img src="file://{crop}">
<svg xmlns="http://www.w3.org/2000/svg" style="transform-origin: 0 0;">
{fixtures.DEFS}
<g transform="scale({PNG_PX_PER_CM:.4f})">{plan.read_text()}</g>
</svg>
</div></body></html>"""
    out = brand.QA / f"{uid}-overlay.html"
    out.write_text(html)
    print(out)


if __name__ == "__main__":
    main()
```

**NB:** `plan.read_text()` legger et helt `<svg viewBox=…>`-fragment inni en `<g>` — nested SVG er gyldig og arver skalering fra `transform`. Rentegningens cm-koordinater × 0.7874 ≈ crop-PNG-ens piksler. Avvik > ~2 px på veggliv = mål på nytt.

- [ ] **Step 3: Commit**

```bash
git add tools/plantegning/crop_unit.py tools/plantegning/make_qa.py && \
git commit -m "Add unit crop and QA overlay tools"
```

---

### Task 8: PILOT — H0101 komplett (tracing → QA → side → brukersjekk)

**Files:**
- Create: `eiendommer/dybwads gate 8/rentegning/H0101-plan.svg`
- Create: `eiendommer/dybwads gate 8/rentegning/H0101-hems.svg` (hvis H0101 har hems)
- Modify: `tools/plantegning/units.json` (H0101-feltene)

Dette er pilot-enheten som kalibrerer metode og smak. **Ikke fortsett til Task 9 før brukeren har godkjent pilot-siden.**

- [ ] **Step 1: Finn H0101 i underlaget og sett crop_px**

Les `underlag/etasje-1-boenheter-1.png` — H0101 ligger i sørøst-hjørnet (nederst til høyre på tegningen, mot Ole Fladagers gate). Noter bounding box i piksler med ~60 px margin. Oppdater `units.json`: `"crop_px": [x, y, w, h]`.

- [ ] **Step 2: Crop og les detaljene**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 tools/plantegning/crop_unit.py H0101
```
Les `underlag/H0101-crop.png`. Identifiser: yttervegg-liv, innervegger, vindusplasseringer, dørslag, kjøkkenplassering, bad-innredning (WC/servant/dusj), hems-utstrekning, rombetegnelser med arealer. Sjekk samtidig BRA-tallet i tegningen (17,8 eller 17,5 — jf. Task 3-avviket); korriger `units.json` hvis tegningen viser noe annet.

- [ ] **Step 3: Mål geometrien**

Mål pikselkoordinater for alle hjørner/åpninger i crop-PNG-en, konverter med **1 px = 1,27 cm**, rund til hele cm. Veggtykkelser: yttervegg typisk 25–40 cm, innervegg 10–15 cm — bruk målt verdi. Kontroller: beregnet rom-areal (innvendige mål) skal treffe tegningens oppgitte areal ±5 %.

- [ ] **Step 4: Tegn `H0101-plan.svg`**

Konvensjoner (gjelder alle enheter):
- `viewBox="0 0 W H"` i cm, origo = yttervegg-hjørne øverst-venstre, samme orientering som arkitekttegningen
- Romflater: `<rect>`/`<path>` med `fill="#F4F1E8"`, bad med `fill="#DCE2D6"` + flisraster (linjer 20×20 cm, `stroke-width="0.35"` `opacity="0.5"`)
- Vegger: `fill="none" stroke="#1A1A18"`, `stroke-width` = veggtykkelse i cm (yttervegg ~30, innervegg ~12) på senterlinje
- Vinduer: hvit brytning i veggstrek + to tynne karmlinjer (`stroke-width="1.4"`)
- Dører: `fixtures.door(...)`-output limt inn som path/line (kopiér genererte elementer, eller skriv tilsvarende manuelt)
- Innredning: `<use href="#wc">` osv. fra fixtures-biblioteket, rotert/plassert iht. tegningen; kjøkkenbenk som rect-segmenter med `#komfyr`/`#kvask`
- Hems-avgrensning på hovedplan: stiplet linje `stroke-dasharray="4 3"` (hemsen får i tillegg egen tegning)
- Rom-labels: `font-family="Helvetica"` 13 cm-enheter, navn + areal på to linjer, areal med `opacity="0.65"`, norsk desimalkomma

- [ ] **Step 5: QA-overlay**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 tools/plantegning/make_qa.py H0101 && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --user-data-dir=/tmp/chrome-plantegning --screenshot=/tmp/qa-H0101.png \
  --window-size=1200,1200 "file://$PWD/eiendommer/dybwads gate 8/qa/H0101-overlay.html" 2>/dev/null && echo OK
```
Les `/tmp/qa-H0101.png`. Expected: rentegningens vegger ligger oppå originalens innenfor ~2 px. Juster koordinater og gjenta til det stemmer.

- [ ] **Step 6: Tegn hems (hvis H0101 har hems) og fyll units.json**

`H0101-hems.svg` etter samme konvensjoner (hems-flate `fill="#E5D3BC"`). Beregn hems-areal fra målt geometri → `"hems": {"area_ca": X.X}`. Fyll også `"type"` (1-roms hvis ett kombinert oppholdsrom), `"rooms"` med navn+areal fra tegningen, og `"north_deg"` (mål arkitektens nordpil-retning på etasjetegningen; samme verdi for alle enheter).

- [ ] **Step 7: Bygg siden og screenshot**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 tools/plantegning/build_pages.py H0101 && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --user-data-dir=/tmp/chrome-plantegning --screenshot=/tmp/side-H0101.png \
  --window-size=794,1123 "file://$PWD/eiendommer/dybwads gate 8/plantegninger/H0101.svg" 2>/dev/null && echo OK
```
Les `/tmp/side-H0101.png` og sjekk mot stil B-mockupen.

- [ ] **Step 8: CHECKPOINT — vis brukeren**

Vis pilot-siden til brukeren (screenshot eller fil). **Vent på godkjenning/justeringer før Task 9.** Justeringer i mal/stil gjøres nå, mens kostnaden er én enhet.

- [ ] **Step 9: Commit**

```bash
git add "eiendommer/dybwads gate 8/rentegning/" tools/plantegning/units.json \
  "eiendommer/dybwads gate 8/plantegninger/H0101.svg" && \
git commit -m "Add H0101 pilot floor plan page"
```

---

### Task 9: export_pdf.py — PDF-eksport, verifisert på piloten

**Files:**
- Create: `tools/plantegning/export_pdf.py`

PDF tas i bruk rett etter piloten slik at font-/render-problemer oppdages før 15 enheter til er tegnet.

- [ ] **Step 1: Skriv `export_pdf.py`**

```python
"""Eksporter side-SVG til A4 PDF via isolert headless Chrome. Bruk: export_pdf.py [H0101 ...]"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def wrap_html(svg_path: Path) -> Path:
    html = f"""<!DOCTYPE html><html><head><style>
@page {{ size: A4; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
svg {{ display: block; width: 210mm; height: 297mm; }}
</style></head><body>{svg_path.read_text()}</body></html>"""
    out = Path("/tmp") / f"{svg_path.stem}-print.html"
    out.write_text(html)
    return out


def main():
    targets = sys.argv[1:] or sorted(p.stem for p in brand.OUTPUT.glob("H*.svg"))
    for uid in targets:
        svg = brand.OUTPUT / f"{uid}.svg"
        html = wrap_html(svg)
        pdf = brand.OUTPUT / f"{uid}.pdf"
        subprocess.run(
            [CHROME, "--headless=new", "--user-data-dir=/tmp/chrome-plantegning",
             "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{html}"],
            check=True, capture_output=True,
        )
        pages = subprocess.run(
            ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
        ).stdout
        n = [l for l in pages.splitlines() if l.startswith("Pages:")][0].split()[-1]
        assert n == "1", f"{uid}: {n} sider!"
        print(f"{uid}.pdf OK (1 side, {pdf.stat().st_size}b)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Kjør på piloten og verifiser visuelt**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 tools/plantegning/export_pdf.py H0101 && \
pdftoppm -png -r 100 "eiendommer/dybwads gate 8/plantegninger/H0101.pdf" /tmp/pdf-H0101
```
Expected: `H0101.pdf OK (1 side, …)`. Les `/tmp/pdf-H0101-1.png` — identisk med SVG-screenshot, **brand-fonter rendret (ikke fallback)**, ingen avkutting i kantene.

- [ ] **Step 3: Commit**

```bash
git add tools/plantegning/export_pdf.py "eiendommer/dybwads gate 8/plantegninger/H0101.pdf" && \
git commit -m "Add PDF export via headless Chrome, verified on pilot"
```

---

### Task 10: Rentegning 1. etasje — H0102–H0105

**Files:**
- Create: `eiendommer/dybwads gate 8/rentegning/H010{2,3,4,5}-plan.svg` (+ `-hems.svg` der hems finnes)
- Modify: `tools/plantegning/units.json`

- [ ] **Step 1: Per enhet H0102, H0103, H0104, H0105 — kjør tracing-løkka**

For hver enhet, nøyaktig samme prosedyre som piloten (Task 8 steg 1–7):
1. Sett `crop_px` i units.json (les `etasje-1-boenheter-1.png`)
2. `python3 tools/plantegning/crop_unit.py <UID>` + les crop-PNG
3. Mål geometri (1 px = 1,27 cm), valider mot oppgitte rom-arealer
4. Tegn `<UID>-plan.svg` (+ `<UID>-hems.svg`) etter konvensjonene i Task 8 steg 4
5. `python3 tools/plantegning/make_qa.py <UID>` + screenshot + les — vegger innenfor ~2 px
6. Fyll `type`, `rooms`, `hems` i units.json
7. `python3 tools/plantegning/build_pages.py <UID>` + screenshot + les

**Enhetene er uavhengige — dispatch gjerne 4 parallelle subagenter, én per enhet.** Hver subagent trenger: enhets-ID, denne planens Task 8-konvensjoner, og beskjed om å skrive kun egne filer (`<UID>-*.svg`) + eget units.json-felt (merge-konflikt unngås ved at orkestratoren samler units.json-oppdateringene).

- [ ] **Step 2: Kontroller etasjen samlet**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import json
u = json.load(open('tools/plantegning/units.json'))
f1 = {k: v for k, v in u.items() if v['floor'] == 1}
assert all(v['type'] and v['rooms'] for v in f1.values()), 'mangler data'
print('OK', round(sum(v['bra'] for v in f1.values()), 1), 'm2')"
ls "eiendommer/dybwads gate 8/plantegninger/" | grep -c '^H01.*svg'
```
Expected: `OK 127.8 m2` (eller korrigert verdi fra Task 8 steg 2) og `5` SVG-er.

- [ ] **Step 3: Commit**

```bash
git add "eiendommer/dybwads gate 8/rentegning/" "eiendommer/dybwads gate 8/plantegninger/" \
  tools/plantegning/units.json && \
git commit -m "Add floor 1 plan pages H0102-H0105"
```

---

### Task 11: Rentegning 2. etasje — H0201–H0205

**Files:**
- Create: `eiendommer/dybwads gate 8/rentegning/H020{1..5}-plan.svg` (+ `-hems.svg`)
- Modify: `tools/plantegning/units.json`

- [ ] **Step 1: Samme tracing-løkke som Task 10, for H0201–H0205**

Underlag: `etasje-2-boenheter-1.png` / `etasje-2-plan-1.png`. 5 parallelle subagenter. NB: 2. etasje har «Sittebenk»-detalj i H0205 — tegn den som enkel rect.

- [ ] **Step 2: Kontroller etasjen**

Samme kontrollscript som Task 10 steg 2 med `floor == 2`. Expected: `OK 126.6 m2` og 5 SVG-er (`grep -c '^H02.*svg'`).

- [ ] **Step 3: Commit**

```bash
git add "eiendommer/dybwads gate 8/rentegning/" "eiendommer/dybwads gate 8/plantegninger/" \
  tools/plantegning/units.json && \
git commit -m "Add floor 2 plan pages H0201-H0205"
```

---

### Task 12: Rentegning 3. etasje — H0301–H0306

**Files:**
- Create: `eiendommer/dybwads gate 8/rentegning/H030{1..6}-plan.svg` + `-hems.svg` (alle 6 har hems)
- Modify: `tools/plantegning/units.json`

- [ ] **Step 1: Samme tracing-løkke, for H0301–H0306**

Underlag: `etasje-3-boenheter-1.png` / `etasje-3-plan-1.png`. 6 parallelle subagenter. Alle enheter har hems → alle får `-hems.svg` og hems-arealfelt.

- [ ] **Step 2: Kontroller etasjen**

Samme kontrollscript med `floor == 3`. Expected: `OK 134.5 m2` og 6 SVG-er. I tillegg: `assert all(v['hems'] for v in f3.values())`.

- [ ] **Step 3: Commit**

```bash
git add "eiendommer/dybwads gate 8/rentegning/" "eiendommer/dybwads gate 8/plantegninger/" \
  tools/plantegning/units.json && \
git commit -m "Add floor 3 plan pages H0301-H0306"
```

---

### Task 13: Full eksport og sluttkontroll

**Files:**
- Create: `eiendommer/dybwads gate 8/plantegninger/H*.pdf` (alle 16)

- [ ] **Step 1: Bygg alle sider på nytt og eksporter alle PDF-er**

```bash
cd /Users/torbjorntest/projects/boligvelger && \
python3 tools/plantegning/build_pages.py && \
python3 tools/plantegning/export_pdf.py
```
Expected: 16 × `… -> …H0xxx.svg` og 16 × `H0xxx.pdf OK (1 side, …)`.

- [ ] **Step 2: Filtelling og navnekontroll**

```bash
cd "/Users/torbjorntest/projects/boligvelger/eiendommer/dybwads gate 8/plantegninger" && \
ls H0*.svg | wc -l && ls H0*.pdf | wc -l && ls
```
Expected: `16` og `16`, navn nøyaktig `H0101`–`H0306`.

- [ ] **Step 3: Visuell sluttkontroll av alle 16**

Screenshot alle sidene (loop over `--screenshot`) og les hver PNG. Sjekkliste per side: riktig enhetsnummer og etasje, arealer matcher units.json, hems-tegning til stede der `hems != null`, riktig enhet markert grønt i posisjonsdiagrammet, riktig etasje markert i snittet, målestokk til stede, ingen tekstkollisjoner, ingen avkuttede elementer.

- [ ] **Step 4: Kontrollsummer mot arkitekttegningene**

```bash
cd /Users/torbjorntest/projects/boligvelger && python3 -c "
import json
u = json.load(open('tools/plantegning/units.json'))
for f in (1, 2, 3):
    s = round(sum(v['bra'] for v in u.values() if v['floor'] == f), 1)
    n = sum(1 for v in u.values() if v['floor'] == f)
    print(f'etasje {f}: {n} enheter, {s} m2')
print('totalt:', len(u), 'enheter')"
```
Expected: 5+5+6 enheter, summer iht. tegning (med dokumentert etasje 1-avvik hvis uavklart).

- [ ] **Step 5: Commit**

```bash
git add "eiendommer/dybwads gate 8/plantegninger/" && \
git commit -m "Add final PDF exports for all 16 floor plan pages"
```

---

## Avhengigheter og parallellisering

```
Task 0 → 1 → 2 → 3 ─┬→ 6 (template; trenger 4 og 5) → 8 PILOT → 9 PDF → ┬→ 10 (4 subagenter)
                    ├→ 4 (fixtures)                    [BRUKERSJEKK]     ├→ 11 (5 subagenter)
                    └→ 5 (posisjon)                                      └→ 12 (6 subagenter)
                                                                              → 13 sluttkontroll
```

- Task 4 og 5 er uavhengige og kan kjøres parallelt etter Task 3; Task 7 krever Task 4 (importerer fixtures)
- Task 10–12 kan kjøres parallelt (15 enheter totalt, uavhengige) etter pilot-godkjenning — men units.json-skrivinger må merges av orkestratoren
- Pilot-checkpointen (Task 8 steg 8) er eneste obligatoriske stopp
