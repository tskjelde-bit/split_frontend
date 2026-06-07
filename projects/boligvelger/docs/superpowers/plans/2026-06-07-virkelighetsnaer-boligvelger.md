# Virkelighetsnær boligvelger — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 3D-boligvelgeren for Dybwads gate 8 går fra grå gips-kasse til malt arkitektmodell som er umiskjennelig lik det virkelige bygget (laksrosa/hvit/sort, bratt tak, frontespise, detaljerte vinduer, gesimser, innganger, tomt), og alle plantegnings- og etasjegeometri-avvik fra avviksrapporten rettes.

**Architecture:** Tre uavhengige workstreams: (A) eksteriør-3D gjennom den parametriske pipelinen `building.json → build_data.py → geometri.json → R3F-scene`; (B) plantegnings-retting gjennom spec-DSL-en `tools/plantegning/specs/H*.json → plan_dsl.py → SVG → PDF`; (C) etasjegeometri-kalibrering i `tools/velger-data/floors/*.json` + ny per-enhet BRA-validering. Avsluttes med felles QA-gate og deploy.

**Tech Stack:** Vite + React + TypeScript + React Three Fiber/drei + three.js (vitest), Python 3 (pytest), Puppeteer-QA i `tools/velger-qa/`, Cloudflare Worker (wrangler).

**Fasit-dokumenter:**
- Spec: `docs/superpowers/specs/2026-06-07-virkelighetsnaer-boligvelger-design.md`
- Avviksrapport (vedlegg A/B/C): `docs/superpowers/specs/2026-06-07-avviksrapport-dybwads-gate-8.md`
- Render-fasit: `eiendommer/dybwads gate 8/renders utvendig/dybwads_8_sørvest_dag.png` (+ `003090-5.jpg`, `003090-6.jpg`)
- Tegnings-fasit: `eiendommer/dybwads gate 8/fasader/*.pdf`, `arkitekt/Snitt_C.pdf`

---

## Eksekveringsrekkefølge (bølger — kjør tasks i samme bølge parallelt)

| Bølge | Tasks | Parallell? |
|---|---|---|
| 1 | A1 (material-tokens), B0 (DSL-utvidelser), C1 (BRA-validator) | Ja — tre uavhengige subsystemer |
| 2 | A2 (tak), B1–B16 (én agent per enhet), C2+C3 (etasjefiks) | Ja — B-tasks er 16 uavhengige filer; C2/C3 er 4 uavhengige filer |
| 3 | A3 (frontespise), B17 (batch-regen + QA-tabell), C4 (strict-flip + regen) | A3 etter A2 (samme filer); B17 etter B1–16; C4 etter C2/C3 |
| 4 | A4 (vinduer), deretter A5 (gesims/frise) | Sekvensielt — begge rører FloorPlate/Building |
| 5 | A6 (innganger/balkong/blindfelt), deretter A7 (tomt) | Sekvensielt — begge rører building.json/Building/CameraRig |
| 6 | F1 (lys + full QA + sentral review), F2 (deploy + prod-verifikasjon) | Sekvensielt |

Konvensjoner: alle stier er relative til repo-rot `/Users/torbjorntest/projects/boligvelger/` med mindre absolutte. Commit-meldinger på engelsk, presens, ingen emoji. `cd`-kommandoer vises eksplisitt. Stier med mellomrom («dybwads gate 8») må quotes.

**Verifiser-først-prinsipp (gjelder alle B- og C-tasks):** Audit-funnene ble gjort mot genererte SVG-er som kan være eldre enn spec-ene (eksempel: H0204-spec har allerede `ladder`, men auditen meldte den manglende). Hver task skal FØRST regenerere fra dagens spec og sjekke hvert funn mot den nye outputen — kun reelle avvik fikses.

---

# Workstream A — Eksteriør-3D

## Task A1: Material-tokens og per-etasje fasadefarge

**Files:**
- Modify: `tools/velger-data/building.json`
- Modify: `tools/velger-data/build_data.py:108-134` (build_geometry)
- Test: `tools/velger-data/test_build_data.py`
- Modify: `app/src/lib/types.ts`
- Modify: `app/src/scene/FloorPlate.tsx`, `app/src/scene/Roof.tsx`, `app/src/scene/Building.tsx`, `app/src/scene/Windows.tsx`, `app/src/scene/UnitMesh.tsx`

- [ ] **Step 1: Skriv feilende pytest for materials-passthrough**

Legg til i `tools/velger-data/test_build_data.py`:

```python
def test_geometry_emits_materials_and_facade():
    geo = build_data.build_geometry()
    m = geo["materials"]
    assert m["pussRosa"] == "#E4B49C"
    assert m["takSort"] == "#2E3038"
    facade = {f["id"]: f["facade"] for f in geo["floors"]}
    assert facade == {"U": "#E9E6E0", "1": "#E9E6E0", "2": "#E4B49C", "3": "#E4B49C"}
```

- [ ] **Step 2: Kjør testen — forvent FAIL**

```bash
cd tools/velger-data && python3 -m pytest test_build_data.py::test_geometry_emits_materials_and_facade -v
```
Forventet: FAIL med `KeyError: 'materials'`.

- [ ] **Step 3: Legg tokens i building.json**

I `tools/velger-data/building.json`, legg til på toppnivå (etter `"scale"`):

```json
"materials": {
  "pussRosa": "#E4B49C",
  "pussHvit": "#E9E6E0",
  "takSort": "#2E3038",
  "karmSort": "#242424",
  "glassMork": "#35353E",
  "hekkGronn": "#3A5224"
},
```

og utvid `floors`-objektet med `facade`-token per etasje:

```json
"floors": {
  "U": { "label": "Underetasje", "height": 3.0, "facade": "pussHvit" },
  "1": { "label": "1. etasje", "height": 3.6, "facade": "pussHvit" },
  "2": { "label": "2. etasje", "height": 3.6, "facade": "pussRosa" },
  "3": { "label": "3. etasje", "height": 2.7, "facade": "pussRosa" }
}
```

- [ ] **Step 4: Resolv tokens i build_geometry()**

I `tools/velger-data/build_data.py`, i `build_geometry()`: les `materials = b["materials"]`, og per floor legg `"facade": materials[spec["facade"]]` i floor-dicten. Legg `"materials": materials` i retur-dicten (mellom `"scale"` og `"slabThickness"`).

- [ ] **Step 5: Kjør testen — forvent PASS**

```bash
cd tools/velger-data && python3 -m pytest test_build_data.py -v
```
Forventet: alle tester PASS (de gamle skal ikke knekke).

- [ ] **Step 6: Utvid TypeScript-typene**

I `app/src/lib/types.ts`:

```ts
export interface Materials {
  pussRosa: string; pussHvit: string; takSort: string;
  karmSort: string; glassMork: string; hekkGronn: string;
}
```
- `FloorGeo` får `facade?: string;`
- `BuildingGeo` får `materials: Materials;`

- [ ] **Step 7: Konsumer fargene i scenen**

- `FloorPlate.tsx`: veggskall-material `color={floor.facade ?? GIPS_EXT}`. Slab-material: erstatt `GIPS_DARK` med prop `slabColor` (sendes fra Building som `geo.materials.pussHvit`) — den synlige dekkekanten blir det hvite etasjebåndet fra renderen. Common-blokker beholder `GIPS_DARK`.
- `Roof.tsx`: `Roof` får ny prop `materials: Materials`. `SLOPE`/`CHIMNEY` erstattes av `materials.takSort`, `WINDOW` av `materials.glassMork`. `GABLE` (gavlinfill = veggtopp) → `materials.pussRosa`.
- `Windows.tsx`: `NICHE` → `materials.glassMork` (sendes som prop fra Building; full ombygging kommer i A4).
- `UnitMesh.tsx`: uendret (brand-grønn/grå-logikken består).
- `Building.tsx`: send `materials`/`slabColor` ned.

- [ ] **Step 8: Regenerer data, kjør vitest, visuell røyk-test**

```bash
cd tools/velger-data && python3 build_data.py
cd ../../app && npm test && npm run build
npx vite preview --port 4317 --strictPort &   # husk kill etterpå: lsof -ti:4317 | xargs kill
cd ../tools/velger-qa && node shots.mjs http://localhost:4317 /tmp/a1-shots
```
Les `/tmp/a1-shots/landing.png`: rosa 2.–3. etg, hvit U/1. etg, sort tak, hvite dekkebånd.
NB: `build_data.py` kan feile på C1-validatoren i warn-modus — warnings er OK i denne fasen.

- [ ] **Step 9: Commit**

```bash
git add tools/velger-data/building.json tools/velger-data/build_data.py tools/velger-data/test_build_data.py app/src
git commit -m "Add material tokens and per-floor facade colors"
```

---

## Task A2: Takvinkel, takvinduer, piper, recess — og streetedge-dedup

**Files:**
- Modify: `tools/velger-data/building.json`
- Modify: `app/src/lib/roofGeometry.ts` + Test: `app/src/lib/roofGeometry.test.ts`
- Modify: `app/src/lib/types.ts`, `app/src/scene/Roof.tsx`, `app/src/scene/Building.tsx`, `app/src/scene/CameraRig.tsx:130-148`

- [ ] **Step 1: Kalibrer takvinkel mot Snitt_C**

Les `eiendommer/dybwads gate 8/arkitekt/Snitt_C.pdf` (Read-verktøyet). Mål forholdet mønehøyde/halv bygningsbredde i snittet (lengste takflate, NE-siden: bredde = (1660−748)px × 0.012696 × (1−0.4) ≈ 6.95 m). Mål vinkel ≈ 40–45° ⇒ `rise = tan(vinkel) × 6.95 × (skaler til faktisk avlesning)`. Hvis PDF-en er uleselig på mål: bruk 5.0 m (≈ 41° på den slake siden, brattere mot gata) — verifiseres uansett mot fasade-overlay i F1.

- [ ] **Step 2: Oppdater building.json**

I `roof`-objektet:
- `"rise": 1.9` → `5.0` (eller kalibrert verdi fra Step 1)
- `"recess": { ..., "rise": 0.6 }` → `"rise": 0.9` (mindre flat catslide; trinnet mot hovedmassen blir dramatisk når hovedtaket reiser seg)
- Slett hele `"dormers": [...]`-arrayen
- `"chimneys"`: endre begge til `"w": 0.5, "d": 0.5, "above": 1.6`
- Nytt felt etter `"chimneys"`:

```json
"skylights": [
  { "t": 0.28, "up": 0.55, "width": 0.9, "height": 1.2 }
],
```

I `windows[]`: erstatt de tre `"floor": "3", "edge": 5`-oppføringene med fire (to par til høyre for frontespisen, jf. Fasade Sørvest — t > 0.5 er nordre halvdel):

```json
{"floor": "3", "edge": 5, "t": 0.64, "width": 0.85, "sill": 0.5, "height": 1.1},
{"floor": "3", "edge": 5, "t": 0.72, "width": 0.85, "sill": 0.5, "height": 1.1},
{"floor": "3", "edge": 5, "t": 0.83, "width": 0.85, "sill": 0.5, "height": 1.1},
{"floor": "3", "edge": 5, "t": 0.91, "width": 0.85, "sill": 0.5, "height": 1.1},
```

- [ ] **Step 3: Skriv feilende vitest for skylightOnSlope**

I `app/src/lib/roofGeometry.test.ts` (gjenbruk eksisterende `bbox`-helper og `scale = 0.012696`):

```ts
import { skylightOnSlope } from './roofGeometry';

describe('skylightOnSlope', () => {
  it('sits flush on the west slope between eave and ridge', () => {
    // west slope: eave x=748px y=0, ridge x=748+0.4*(1660-748) px y=rise
    const g = skylightOnSlope(
      { t: 0.28, up: 0.55, width: 0.9, height: 1.2 },
      [748, 1700], [748, 375], 748 * 0.012696, (748 + 0.4 * 912) * 0.012696, 5.0, 0.012696,
    );
    const bb = bbox(g);
    expect(bb.maxY).toBeGreaterThan(0.55 * 5.0 - 1.2); // ligger rundt up*rise
    expect(bb.maxY).toBeLessThan(5.0);                  // under mønet
    expect(bb.maxX - bb.minX).toBeLessThan(1.2);        // tiltet — x-utstrekning < height
  });
});
```

- [ ] **Step 4: Kjør — forvent FAIL** (`skylightOnSlope is not exported`)

```bash
cd app && npx vitest run src/lib/roofGeometry.test.ts
```

- [ ] **Step 5: Implementer skylightOnSlope i roofGeometry.ts**

```ts
export interface SkylightSpec { t: number; up: number; width: number; height: number; }

/** Flat dark box lying ON the west slope plane. `up` = 0 (eave) .. 1 (ridge).
 *  edgeA/edgeB = street edge in px; wxEave/wxRidge = world-x of eave and ridge. */
export function skylightOnSlope(
  spec: SkylightSpec,
  edgeA: [number, number], edgeB: [number, number],
  wxEave: number, wxRidge: number, rise: number, scale: number,
): THREE.BufferGeometry {
  const [, az] = pxToWorld(edgeA[0], edgeA[1], scale);
  const [, bz] = pxToWorld(edgeB[0], edgeB[1], scale);
  const z = az + (bz - az) * spec.t;
  const run = wxRidge - wxEave;                  // > 0: slope rises toward +x
  const theta = Math.atan2(rise, run);           // slope angle from horizontal
  const wx = wxEave + spec.up * run;
  const wy = spec.up * rise;
  const g = new THREE.BoxGeometry(spec.height, 0.06, spec.width); // length up-slope along x
  g.rotateZ(theta);                              // tilt onto the plane
  g.translate(wx, wy + 0.10, z);                 // 10 cm proud of the slope slab
  return g;
}
```

- [ ] **Step 6: Kjør vitest — forvent PASS**

- [ ] **Step 7: Koble inn i Roof.tsx + dedup street-edge**

I `app/src/lib/types.ts`: `RoofGeo` får `skylights?: SkylightSpec[];` (importer typen fra roofGeometry eller flytt den til types.ts — flytt til types.ts og importer i roofGeometry for konsistens med GableSpec).

I `Roof.tsx`:
- Ny prop `envelope: EnvelopeGeo` (sendes fra `Building.tsx`: `<Roof roof={geo.roof} envelope={geo.envelope} materials={geo.materials} ... />`). `buildRoof(roof, envelope, scale)` får envelope som parameter.
- Erstatt hardkodet `streetA`/`streetB` (linje 199-200) med:

```ts
const streetA = envelope.poly[5];
const streetB = envelope.poly[0];
```
- Etter chimneys-løkken (gjenbruk `wxWest`/`wxRidge`/`rise` som allerede finnes i `buildRoof`):

```ts
for (const sk of roof.skylights ?? []) {
  windows.push(skylightOnSlope(sk, streetA, streetB, wxWest, wxRidge, rise, scale));
}
```

I `CameraRig.tsx` (linje 130-131): erstatt hardkodet `streetA`/`streetB` med `geo.envelope.poly[5]` / `geo.envelope.poly[0]`.

- [ ] **Step 8: Regenerer + røyk-test + commit**

```bash
cd tools/velger-data && python3 build_data.py
cd ../../app && npm test && npm run build
```
Screenshot-sjekk som i A1 Step 8 (`/tmp/a2-shots`): bratt sort saltak, synlig trinn ned mot NE-fløyen, ingen kvister, ett takvindu sør for midten, slanke sorte piper.

```bash
git add tools/velger-data/building.json app/src
git commit -m "Steepen roof to match Snitt_C, add skylight, derive street edge from envelope"
```

---

## Task A3: Frontespise (sentral spiss gavl)

**Files:**
- Modify: `tools/velger-data/building.json` (erstatt `ark` med `frontispiece`)
- Modify: `app/src/lib/types.ts`, `app/src/lib/roofGeometry.ts`
- Test: `app/src/lib/roofGeometry.test.ts`
- Modify: `app/src/scene/Roof.tsx`, `app/src/scene/CameraRig.tsx`

- [ ] **Step 1: Definer spec i building.json**

Slett hele `"ark": {...}`-objektet, legg inn:

```json
"frontispiece": {
  "edge": 5, "t": 0.5,
  "width": 3.6, "projection": 0.35, "depth": 1.8,
  "gableBase": 3.2, "apex": 5.8,
  "trim": 0.22,
  "window": { "width": 1.0, "sill": 0.7, "height": 2.2, "peak": 0.5 }
}
```
(`apex` 5.8 > `rise` 5.0 — spissen bryter mønelinjen, jf. render og Fasade Sørvest. Alle høyder er tak-lokale: 0 = gesims/takfot.)

- [ ] **Step 2: Type i types.ts**

```ts
export interface FrontispieceSpec {
  edge: number; t: number; width: number; projection: number; depth: number;
  gableBase: number; apex: number; trim: number;
  window?: { width: number; sill: number; height: number; peak: number };
}
```
`RoofGeo`: `ark?`/`dormers?` beholdes som optional (bakoverkompat, ubrukte), nytt felt `frontispiece?: FrontispieceSpec;`.

- [ ] **Step 3: Skriv feilende vitest**

```ts
import { buildFrontispiece } from './roofGeometry';

describe('buildFrontispiece', () => {
  const spec = {
    edge: 5, t: 0.5, width: 3.6, projection: 0.35, depth: 1.8,
    gableBase: 3.2, apex: 5.8, trim: 0.22,
    window: { width: 1.0, sill: 0.7, height: 2.2, peak: 0.5 },
  };
  it('peaks above the main ridge and stays centred on the street edge', () => {
    const r = buildFrontispiece(spec, [748, 1700], [748, 375], 0.012696);
    expect(bbox(r.body).maxY).toBeCloseTo(spec.gableBase, 1);
    expect(bbox(r.gable).maxY).toBeCloseTo(spec.apex, 1);
    expect(r.window).not.toBeNull();
    const wb = bbox(r.window!.glass);
    expect(wb.minY).toBeCloseTo(spec.window.sill, 1);
    // sentrert: midt på street-edge i z
    const mid = -((1700 + 375) / 2) * 0.012696;
    const gb = bbox(r.body);
    expect((gb.minZ + gb.maxZ) / 2).toBeCloseTo(mid, 1);
  });
  it('builds white trim and a black roof cap', () => {
    const r = buildFrontispiece(spec, [748, 1700], [748, 375], 0.012696);
    expect(r.trim.getAttribute('position').count).toBeGreaterThan(0);
    expect(bbox(r.roofCap).maxY).toBeGreaterThan(spec.apex - 0.1);
  });
});
```

- [ ] **Step 4: Kjør — forvent FAIL** (ikke eksportert)

- [ ] **Step 5: Implementer buildFrontispiece i roofGeometry.ts**

```ts
export interface FrontispieceResult {
  body: THREE.BufferGeometry;      // rosa veggfelt (rektangulær del + sider)
  gable: THREE.BufferGeometry;     // rosa gavltrekant
  trim: THREE.BufferGeometry;      // hvite lister: raked kanter + basebånd + vindusomramming
  roofCap: THREE.BufferGeometry;   // sort sadel over gavlen
  window: { frame: THREE.BufferGeometry; glass: THREE.BufferGeometry } | null;
}

export function buildFrontispiece(
  spec: FrontispieceSpec,
  edgeA: [number, number], edgeB: [number, number],
  scale: number,
): FrontispieceResult {
  const [ax, az] = pxToWorld(edgeA[0], edgeA[1], scale);
  const [bx, bz] = pxToWorld(edgeB[0], edgeB[1], scale);
  const px = ax + (bx - ax) * spec.t;
  const pz = az + (bz - az) * spec.t;
  const dx = bx - ax, dz = bz - az;
  const dlen = Math.hypot(dx, dz) || 1;
  const tx = dx / dlen, tz = dz / dlen;     // langs fasaden
  const nx = -dz / dlen, nz = dx / dlen;    // utover
  const at = (along: number, out: number, y: number): V3 => [
    px + tx * along + nx * out, y, pz + tz * along + nz * out,
  ];
  const hw = spec.width / 2;
  const proj = spec.projection;

  // Body: front-plate (full bredde, 0..gableBase) + to sidevegger inn mot taket.
  const bodyGeos: THREE.BufferGeometry[] = [];
  bodyGeos.push(slabFromQuad(at(-hw, proj, 0), at(hw, proj, 0), at(hw, proj, spec.gableBase), at(-hw, proj, spec.gableBase), 0.1));
  bodyGeos.push(polygonGeometry([at(-hw, proj, 0), at(-hw, -spec.depth, 0), at(-hw, -spec.depth, spec.gableBase), at(-hw, proj, spec.gableBase)]));
  bodyGeos.push(polygonGeometry([at(hw, -spec.depth, 0), at(hw, proj, 0), at(hw, proj, spec.gableBase), at(hw, -spec.depth, spec.gableBase)]));

  // Gavltrekant (front) + sidetrekanter bakover.
  const apexF: V3 = at(0, proj, spec.apex);
  const gableGeos: THREE.BufferGeometry[] = [
    prismFromTriangle(at(-hw, proj, spec.gableBase), at(hw, proj, spec.gableBase), apexF, 0.1),
    polygonGeometry([at(-hw, proj, spec.gableBase), at(-hw, -spec.depth, spec.gableBase), at(0, -spec.depth, spec.apex), at(0, proj, spec.apex)]),
    polygonGeometry([at(hw, -spec.depth, spec.gableBase), at(hw, proj, spec.gableBase), at(0, proj, spec.apex), at(0, -spec.depth, spec.apex)]),
  ];

  // Hvit trim: to raked lister langs gavlkantene + basebånd + pilastre.
  const trimGeos: THREE.BufferGeometry[] = [];
  const rakeL = (sgn: 1 | -1) => {
    const a = at(sgn * hw, proj + 0.02, spec.gableBase);
    const b = at(0, proj + 0.02, spec.apex);
    const dir = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
    const len = dir.length();
    const g = new THREE.BoxGeometry(spec.trim, len, 0.08);
    g.translate(0, len / 2, 0);
    const angle = Math.atan2(b[1] - a[1], (sgn === -1 ? 1 : -1) * Math.hypot(b[0] - a[0], b[2] - a[2]));
    g.rotateZ(-(Math.PI / 2 - angle) * (sgn === -1 ? 1 : -1));
    const yaw = Math.atan2(tz, tx);
    g.rotateY(-yaw);
    g.translate(a[0], a[1], a[2]);
    return g;
  };
  trimGeos.push(rakeL(-1), rakeL(1));
  trimGeos.push(slabFromQuad(at(-hw, proj + 0.02, spec.gableBase - 0.22), at(hw, proj + 0.02, spec.gableBase - 0.22), at(hw, proj + 0.02, spec.gableBase), at(-hw, proj + 0.02, spec.gableBase), 0.08));
  trimGeos.push(boxGeometry(...at(-hw + 0.12, proj + 0.02, spec.gableBase / 2), 0.24, spec.gableBase, 0.08));
  trimGeos.push(boxGeometry(...at(hw - 0.12, proj + 0.02, spec.gableBase / 2), 0.24, spec.gableBase, 0.08));

  // Sort sadel: møne fra apexF bakover, to flater ned til gavlbase-hjørnene.
  const ohf = 0.15;
  const apexB: V3 = at(0, -spec.depth, spec.apex);
  const roofGeos = [
    slabFromQuad(apexB, [apexF[0] + nx * ohf, apexF[1], apexF[2] + nz * ohf], at(-hw - ohf, proj + ohf, spec.gableBase - 0.05), at(-hw - ohf, -spec.depth, spec.gableBase - 0.05), 0.08),
    slabFromQuad([apexF[0] + nx * ohf, apexF[1], apexF[2] + nz * ohf], apexB, at(hw + ohf, -spec.depth, spec.gableBase - 0.05), at(hw + ohf, proj + ohf, spec.gableBase - 0.05), 0.08),
  ];

  // Spissbuet vindu: flat femkant (rekt + topp-trekant) + hvit ramme bak.
  let win: FrontispieceResult['window'] = null;
  if (spec.window) {
    const w = spec.window;
    const hww = w.width / 2;
    const pent = (m: number, out: number) => polygonGeometry([
      at(-hww - m, out, w.sill - m),
      at(hww + m, out, w.sill - m),
      at(hww + m, out, w.sill + w.height),
      at(0, out, w.sill + w.height + w.peak + m),
      at(-hww - m, out, w.sill + w.height),
    ]);
    win = { frame: pent(0.12, proj + 0.03), glass: pent(0, proj + 0.05) };
  }

  return {
    body: mergeGeometries(bodyGeos),
    gable: mergeGeometries(gableGeos),
    trim: mergeGeometries(trimGeos),
    roofCap: mergeGeometries(roofGeos),
    window: win,
  };
}
```
NB til utfører: rakeL-rotasjonsmatematikken er den mest sannsynlige feilkilden — verifiser visuelt i Step 8 at de to listene følger gavlkantene; juster fortegn til de gjør det. Testen i Step 3 låser apex/senter/sill, ikke listene.

- [ ] **Step 6: Kjør vitest — forvent PASS**

- [ ] **Step 7: Render i Roof.tsx**

I `buildRoof` (Roof.tsx), erstatt `if (roof.ark) {...}`-blokken og dormers-løkken med:

```ts
let fronti: FrontispieceResult | null = null;
if (roof.frontispiece) {
  fronti = buildFrontispiece(roof.frontispiece, streetA, streetB, scale);
}
```
Returner `fronti` i `RoofParts`, og i komponenten render med materialfargene:
- `fronti.body` + `fronti.gable` → `materials.pussRosa`
- `fronti.trim` + `fronti.window.frame` → `materials.pussHvit`
- `fronti.roofCap` → `materials.takSort`
- `fronti.window.glass` → `materials.glassMork`
(samme mesh-mønster som slopes/gables, `castShadow receiveShadow` på body/gable/roofCap.)

- [ ] **Step 8: CameraRig AABB**

I `assembledBox` (CameraRig.tsx), etter ark/dormers-blokken (linje 147-148 — behold `addDormer` for bakoverkompat):

```ts
if (geo.roof.frontispiece) {
  const f = geo.roof.frontispiece;
  addDormer({ t: f.t, projection: f.projection + 0.2, rise: f.apex });
}
```

- [ ] **Step 9: Regenerer + visuell verifikasjon + commit**

```bash
cd tools/velger-data && python3 build_data.py
cd ../../app && npm test && npm run build
```
Screenshots (`/tmp/a3-shots` via shots.mjs som i A1): sentral rosa spiss gavl med hvite lister, spissbuet mørkt vindu, sort sadel, spiss over mønet. Sammenlign mot `renders utvendig/dybwads_8_sørvest_dag.png` side om side.

```bash
git add tools/velger-data/building.json app/src
git commit -m "Replace ark with full frontispiece gable on street facade"
```

---

## Task A4: Detaljerte vinduer (omramming + karm + glass) med eksplodert-fade

**Files:**
- Rewrite: `app/src/scene/Windows.tsx` (blir per-etasje-komponent `FloorWindows`)
- Modify: `app/src/scene/FloorPlate.tsx`, `app/src/scene/Building.tsx`
- Modify: `app/src/lib/types.ts` (WindowGeo får `kind?`)
- Modify: `tools/velger-data/building.json` (blindfelt-vinduer)

- [ ] **Step 1: Typer og data**

`types.ts`: `WindowGeo` får `kind?: 'window' | 'blind';`.

`building.json` `windows[]`: legg til blindfeltene i midtaksen på sørvest (under frontespisen — hvite panelnisjer, IKKE dør/vindu):

```json
{"floor": "1", "edge": 5, "t": 0.5, "width": 1.3, "sill": 0.3, "height": 2.4, "kind": "blind"},
{"floor": "2", "edge": 5, "t": 0.5, "width": 1.3, "sill": 0.3, "height": 2.4, "kind": "blind"},
```
Fjern de eksisterende vanlige vinduene på `t: 0.5` for floor 1 og 2 edge 5 (midtaksen er blind, jf. render: hvitt panelfelt i midten).

- [ ] **Step 2: Skriv om Windows.tsx til FloorWindows**

Erstatt hele filen med:

```tsx
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { FloorGeo, Materials, WindowGeo } from '../lib/types';
import { useVelger } from '../state/store';

const SURROUND_M = 0.14; // hvit omramming utenfor karmen
const FRAME_M = 0.07;    // sort karm synlig rundt glasset
const PROUD = 0.03;      // omramming står 3 cm proud av fasadelivet

interface Placement {
  x: number; z: number; angle: number; y: number; w: number; h: number; kind: string;
}

/** Vinduer for ÉN etasje, montert inne i FloorPlate-gruppen slik at de følger
 *  eksplosjons-animasjonen. Fades ut i eksplodert visning (veggen krymper til
 *  parapet). Hvert vindu = hvit omramming + sort karm m/midtpost + mørkt glass;
 *  kind=blind = kun hvitt panel. */
export function FloorWindows({ floor, windows, scale, materials }: {
  floor: FloorGeo; windows: WindowGeo[]; scale: number; materials: Materials;
}) {
  const mode = useVelger((s) => s.mode);
  const group = useRef<THREE.Group>(null!);
  const placements: Placement[] = useMemo(() => windows.map((w) => {
    const o = floor.outline;
    const a = o[w.edge], b = o[(w.edge + 1) % o.length];
    const ax = a[0] * scale, az = -(a[1] * scale);
    const bx = b[0] * scale, bz = -(b[1] * scale);
    const x = ax + (bx - ax) * w.t, z = az + (bz - az) * w.t;
    const dx = bx - ax, dz = bz - az;
    const len = Math.hypot(dx, dz) || 1;
    const nx = -dz / len, nz = dx / len; // utover
    return {
      x: x + nx * PROUD, z: z + nz * PROUD,
      angle: Math.atan2(bz - az, bx - ax),
      y: w.sill + w.height / 2, // lokal y — gruppen ligger på slab-nivå i FloorPlate
      w: w.width, h: w.height, kind: w.kind ?? 'window',
    };
  }), [floor, windows, scale]);

  useFrame((_, dt) => {
    const target = mode === 'exploded' ? 0 : 1;
    group.current.children.forEach((c) => {
      c.traverse((m) => {
        const mat = (m as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
        if (mat) {
          mat.opacity = THREE.MathUtils.damp(mat.opacity, target, 6, dt);
          mat.transparent = true;
          m.visible = mat.opacity > 0.02;
        }
      });
    });
  });

  return (
    <group ref={group}>
      {placements.map((p, i) => (
        <group key={i} position={[p.x, p.y, p.z]} rotation={[0, p.angle, 0]}>
          {/* hvit omramming (bakerst, størst) */}
          <mesh>
            <boxGeometry args={[p.w + 2 * SURROUND_M, p.h + 2 * SURROUND_M, 0.06]} />
            <meshStandardMaterial color={materials.pussHvit} roughness={0.85} />
          </mesh>
          {p.kind === 'window' && (
            <>
              <mesh position={[0, 0, 0.02]}>
                <boxGeometry args={[p.w, p.h, 0.05]} />
                <meshStandardMaterial color={materials.karmSort} roughness={0.7} />
              </mesh>
              <mesh position={[-p.w / 4 + FRAME_M / 4, 0, 0.045]}>
                <boxGeometry args={[p.w / 2 - 1.5 * FRAME_M, p.h - 2 * FRAME_M, 0.02]} />
                <meshStandardMaterial color={materials.glassMork} roughness={0.25} metalness={0.1} />
              </mesh>
              <mesh position={[p.w / 4 - FRAME_M / 4, 0, 0.045]}>
                <boxGeometry args={[p.w / 2 - 1.5 * FRAME_M, p.h - 2 * FRAME_M, 0.02]} />
                <meshStandardMaterial color={materials.glassMork} roughness={0.25} metalness={0.1} />
              </mesh>
            </>
          )}
        </group>
      ))}
    </group>
  );
}
```

- [ ] **Step 3: Monter i FloorPlate, fjern global Windows**

- `FloorPlate.tsx`: ny prop `windows: WindowGeo[]` og `materials: Materials`; render `<FloorWindows floor={floor} windows={windows} scale={scale} materials={materials} />` direkte i den YTRE animerte gruppen (`<group ref={ref} position-y={floor.elevation}>`), IKKE i `<group position-y={slab}>`-undergruppen. Da er vinduenes `y = sill + height/2` målt fra etasjens elevation — nøyaktig samme verdi som dagens globale Windows brukte (`floor.elevation + sill + height/2`), så sill-kalibreringen i building.json består uendret.
- `Building.tsx`: fjern `<Windows geo={geo} />`; send `windows={data.geo.windows.filter(w => w.floor === f.id)}` og `materials` inn i hver `FloorPlate`.

- [ ] **Step 4: Verifiser + commit**

```bash
cd tools/velger-data && python3 build_data.py && cd ../../app && npm test && npm run build
```
Screenshots (`/tmp/a4-shots`): hvite omramminger + sorte karmer + mørkt glass på alle fasader; midtakse = hvite blindfelt; eksplodert visning: vinduer fader pent ut.

```bash
git add app/src tools/velger-data/building.json
git commit -m "Replace window niches with framed windows and blind center panels"
```

---

## Task A5: Gesimser og tannsnittfrise

**Files:**
- Create: `app/src/scene/Cornices.tsx`
- Modify: `app/src/lib/shapes.ts` (outset-støtte) + Test: `app/src/lib/shapes.test.ts`
- Create: `app/src/lib/facade.ts` (dentil-plasseringer) + Test: `app/src/lib/facade.test.ts`
- Modify: `app/src/scene/Building.tsx`

- [ ] **Step 1: Feilende test — insetPolygon med negativ d (outset)**

I `app/src/lib/shapes.test.ts`:

```ts
it('offsets outward with negative inset distance', () => {
  const rect: [number, number][] = [[0, 0], [100, 0], [100, 50], [0, 50]];
  const out = insetPolygon(rect, -10);
  const xs = out.map((p) => p[0]);
  const ys = out.map((p) => p[1]);
  expect(Math.min(...xs)).toBeCloseTo(-10, 5);
  expect(Math.max(...xs)).toBeCloseTo(110, 5);
  expect(Math.min(...ys)).toBeCloseTo(-10, 5);
});
```
Kjør `npx vitest run src/lib/shapes.test.ts`. Matematikk-en i `insetPolygon` er fortegnssymmetrisk, så denne forventes å PASSE direkte — hvis FAIL: fiks normalberegningen for negativ d. Uansett: testen låser oppførselen gesimsen avhenger av.

- [ ] **Step 2: Feilende test — dentil-plasseringer**

`app/src/lib/facade.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { edgeDentils } from './facade';

describe('edgeDentils', () => {
  it('emits evenly spaced placements along each edge with outward angle', () => {
    const rect: [number, number][] = [[0, 0], [1000, 0], [1000, 500], [0, 500]];
    const d = edgeDentils(rect, 0.012696, 0.5);
    expect(d.length).toBeGreaterThan(20);
    const first = d[0];
    expect(first).toHaveProperty('x');
    expect(first).toHaveProperty('z');
    expect(first).toHaveProperty('angle');
    // alle plasseringer ligger på en av kantene (x eller z konstant for rektangelet)
  });
});
```

- [ ] **Step 3: Implementer facade.ts**

```ts
export interface DentilPlacement { x: number; z: number; angle: number; }

/** Jevnt fordelte plasseringer langs alle kanter av outline (px), i world-koord.
 *  spacing i meter. angle = kantens retning (for rotateY). */
export function edgeDentils(
  outline: [number, number][], scale: number, spacing: number,
): DentilPlacement[] {
  const out: DentilPlacement[] = [];
  const n = outline.length;
  for (let i = 0; i < n; i++) {
    const a = outline[i], b = outline[(i + 1) % n];
    const ax = a[0] * scale, az = -(a[1] * scale);
    const bx = b[0] * scale, bz = -(b[1] * scale);
    const len = Math.hypot(bx - ax, bz - az);
    const count = Math.floor(len / spacing);
    const angle = Math.atan2(bz - az, bx - ax);
    for (let k = 1; k < count; k++) {
      const t = k / count;
      out.push({ x: ax + (bx - ax) * t, z: az + (bz - az) * t, angle });
    }
  }
  return out;
}
```
Kjør begge testene — PASS.

- [ ] **Step 4: Cornices.tsx**

```tsx
import { useMemo } from 'react';
import * as THREE from 'three';
import { polyToRingShape, insetPolygon } from '../lib/shapes';
import { edgeDentils } from '../lib/facade';
import type { BuildingGeo } from '../lib/types';

const BAND_H = 0.18;   // gesimsbåndets høyde
const BAND_OUT = 0.12; // utkraging utenfor fasadelivet
const DENTIL = { w: 0.18, h: 0.14, d: 0.10, spacing: 0.42 };

/** Hvite etasjegesimser (over 1. og 2. etg) + takfotgesims med tannsnitt.
 *  Statisk i montert visning; skjules i exploded (etasjeplatene er helten). */
export function Cornices({ geo }: { geo: BuildingGeo }) {
  const mats = geo.materials;
  const bands = useMemo(() => {
    const outline = geo.envelope.poly;
    const outer = insetPolygon(outline, -BAND_OUT / geo.scale);
    const ring = polyToRingShape(outer, outline, geo.scale);
    const mk = (y: number) => {
      // ExtrudeGeometry(depth) + rotateX(-PI/2) spenner y ∈ [0, BAND_H] (samme
      // mønster som FloorPlate slabGeo) — translate med båndets UNDERKANT.
      const g = new THREE.ExtrudeGeometry(ring, { depth: BAND_H, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      g.translate(0, y, 0);
      return g;
    };
    // y = topp av etasje N (elevation + height) minus båndhøyden
    const tops = geo.floors.filter((f) => f.id === '1' || f.id === '2')
      .map((f) => f.elevation + f.height - BAND_H);
    const eave = geo.roof.elevation - BAND_H; // takfot
    return [...tops, eave].map(mk);
  }, [geo]);

  const dentils = useMemo(
    () => edgeDentils(geo.envelope.poly, geo.scale, DENTIL.spacing),
    [geo],
  );
  const dentilY = geo.roof.elevation - BAND_H - DENTIL.h / 2;

  return (
    <group>
      {bands.map((g, i) => (
        <mesh key={i} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color={mats.pussHvit} roughness={0.85} />
        </mesh>
      ))}
      {dentils.map((d, i) => (
        <mesh key={`d${i}`} position={[d.x, dentilY, d.z]} rotation={[0, d.angle, 0]}>
          <boxGeometry args={[DENTIL.w, DENTIL.h, DENTIL.d * 2]} />
          <meshStandardMaterial color={mats.pussHvit} roughness={0.85} />
        </mesh>
      ))}
    </group>
  );
}
```
Monter i `Building.tsx` (inne i sentrerings-gruppen), med samme synlighets-/fade-mønster som tomta vil bruke: `const mode = useVelger(s => s.mode); if (mode === 'exploded') return null;` — for v1 er hard skjuling OK (gesimsen sitter på veggskallet som uansett krymper).

- [ ] **Step 5: Verifiser + commit**

`npm test && npm run build`, screenshots (`/tmp/a5-shots`): hvite bånd over 1. og 2. etg + takfotbånd med tannsnitt rundt hele bygget. Sjekk at gesims ikke z-fighter veggen (juster BAND_OUT ved behov).

```bash
git add app/src
git commit -m "Add white story cornices and dentil frieze"
```

---

## Task A6: Innganger, gavlbalkong

**Files:**
- Modify: `tools/velger-data/building.json`, `tools/velger-data/build_data.py` (passthrough), `app/src/lib/types.ts`
- Create: `app/src/scene/Entrances.tsx`
- Modify: `app/src/scene/Building.tsx`, `app/src/scene/CameraRig.tsx`

- [ ] **Step 1: Data**

`building.json`, nye toppnivå-felt (kalibrer t-verdier mot fasade-PDF-ene i QA):

```json
"entrances": [
  { "edge": 4, "t": 0.14, "width": 1.5, "height": 2.6, "overlys": true, "steps": 3,
    "doc": "Hovedinngang SØ-fløy mot Ole Fladagers gate, tofløyet m/overlys (Fasade Sørøst)" },
  { "edge": 3, "t": 0.50, "width": 1.1, "height": 2.2, "overlys": false, "steps": 3,
    "doc": "Bakdør NØ mot gårdsplass (foto 003090-4)" },
  { "edge": 0, "t": 0.35, "width": 1.4, "height": 2.5, "overlys": true, "steps": 2,
    "doc": "Inngang NV gavl mot parkering (render 003090-6)" }
],
"balconies": [
  { "edge": 4, "t": 0.64, "floor": "2", "width": 1.8, "depth": 0.45,
    "doc": "Fransk smijernsbalkong på SØ-gavlen 2. etg (render 003090-5)" }
],
```
`build_data.py` `build_geometry()`: legg `"entrances": b.get("entrances", [])` og `"balconies": b.get("balconies", [])` i retur-dicten. Pytest-utvidelse i `test_build_data.py`:

```python
def test_geometry_emits_entrances_and_balconies():
    geo = build_data.build_geometry()
    assert len(geo["entrances"]) == 3
    assert geo["balconies"][0]["floor"] == "2"
```
(Kjør rød → grønn som i A1.)

`types.ts`:

```ts
export interface EntranceSpec { edge: number; t: number; width: number; height: number; overlys: boolean; steps: number; doc?: string; }
export interface BalconySpec { edge: number; t: number; floor: FloorId; width: number; depth: number; doc?: string; }
```
`BuildingGeo` får `entrances: EntranceSpec[]; balconies: BalconySpec[];`.

- [ ] **Step 2: Entrances.tsx (dører + trapper + balkong)**

```tsx
import { useVelger } from '../state/store';
import type { BuildingGeo, EntranceSpec, BalconySpec } from '../lib/types';

/** Posisjon/utovernormal på en envelope-kant — samme konvensjon som FloorWindows. */
function onEdge(geo: BuildingGeo, edge: number, t: number) {
  const o = geo.envelope.poly;
  const a = o[edge], b = o[(edge + 1) % o.length];
  const ax = a[0] * geo.scale, az = -(a[1] * geo.scale);
  const bx = b[0] * geo.scale, bz = -(b[1] * geo.scale);
  const dx = bx - ax, dz = bz - az;
  const len = Math.hypot(dx, dz) || 1;
  return {
    x: ax + dx * t, z: az + dz * t,
    nx: -dz / len, nz: dx / len,
    angle: Math.atan2(dz, dx),
  };
}

export function Entrances({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);
  if (mode === 'exploded') return null;
  const m = geo.materials;
  const ground = geo.floors.find((f) => f.id === '1')!.elevation;
  return (
    <group>
      {geo.entrances.map((e: EntranceSpec, i: number) => {
        const p = onEdge(geo, e.edge, e.t);
        const lysH = e.overlys ? 0.4 : 0;
        return (
          <group key={i} position={[p.x, ground, p.z]} rotation={[0, p.angle, 0]}>
            <mesh position={[0, (e.height + lysH) / 2 + 0.06, 0.05]}>
              <boxGeometry args={[e.width + 0.24, e.height + lysH + 0.12, 0.06]} />
              <meshStandardMaterial color={m.pussHvit} roughness={0.85} />
            </mesh>
            <mesh position={[0, e.height / 2, 0.09]}>
              <boxGeometry args={[e.width, e.height, 0.08]} />
              <meshStandardMaterial color={m.karmSort} roughness={0.6} />
            </mesh>
            {e.overlys && (
              <mesh position={[0, e.height + lysH / 2, 0.09]}>
                <boxGeometry args={[e.width, lysH, 0.04]} />
                <meshStandardMaterial color={m.glassMork} roughness={0.25} />
              </mesh>
            )}
            {Array.from({ length: e.steps }, (_, k) => (
              <mesh key={k} position={[0, -0.08 - 0.16 * k, 0.15 + 0.3 * k]}>
                <boxGeometry args={[e.width + 0.4, 0.16, 0.3]} />
                <meshStandardMaterial color={m.pussHvit} roughness={0.9} />
              </mesh>
            ))}
          </group>
        );
      })}
      {geo.balconies.map((b: BalconySpec, i: number) => {
        const p = onEdge(geo, b.edge, b.t);
        const fl = geo.floors.find((f) => f.id === b.floor)!;
        const bars = Math.floor(b.width / 0.12);
        return (
          <group key={`b${i}`} position={[p.x, fl.elevation + 1.0, p.z]} rotation={[0, p.angle, 0]}>
            <mesh position={[0, 0, b.depth / 2]}>
              <boxGeometry args={[b.width, 0.08, b.depth]} />
              <meshStandardMaterial color={m.pussHvit} roughness={0.9} />
            </mesh>
            <mesh position={[0, 0.5, b.depth]}>
              <boxGeometry args={[b.width, 0.04, 0.04]} />
              <meshStandardMaterial color={m.karmSort} roughness={0.6} />
            </mesh>
            {Array.from({ length: bars }, (_, k) => (
              <mesh key={k} position={[-b.width / 2 + (k + 0.5) * 0.12, 0.27, b.depth]}>
                <boxGeometry args={[0.025, 0.5, 0.025]} />
                <meshStandardMaterial color={m.karmSort} roughness={0.6} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}
```
NB: gruppene står i Building-gruppens lokale rom (samme som FloorWindows-konvensjonen); rotasjonen legger boksenes z-akse langs utovernormalen via `rotation=[0, p.angle, 0]` — verifiser i screenshot at dører vender UT (flip fortegn på angle hvis ikke). Monter i `Building.tsx`: `<Entrances geo={geo} />`.

- [ ] **Step 3: CameraRig**

I `assembledBox`: trapper/balkong stikker maks ~1.0 m utenfor fasadelivet — utvid boksen generisk i stedet for per-element:

```ts
// Entrances/balconies/gesims stikker < 1.0 m utenfor fasadelivet.
if (geo.entrances?.length || geo.balconies?.length) box.expandByScalar(0.5);
```
(`expandByScalar` på Box3 utvider alle sider 0.5 m — konservativt og enkelt.)

- [ ] **Step 4: Verifiser + commit**

Regenerer data, `npm test`, build, screenshots (`/tmp/a6-shots`) fra flere vinkler (`facade.mjs` tar sørvest + sørøst): dører med hvite omramminger og trapper på SØ/NØ/NV, sort smijernsbalkong på gavlen.

```bash
git add tools/velger-data app/src
git commit -m "Add entrances with steps and wrought-iron gable balcony"
```

---

## Task A7: Tomt (bakkeplan, mur + gjerde + hekk)

**Files:**
- Modify: `tools/velger-data/building.json`, `build_data.py`, `app/src/lib/types.ts`
- Create: `app/src/scene/Site.tsx`
- Modify: `app/src/scene/Building.tsx`, `app/src/scene/CameraRig.tsx`, `app/src/scene/VelgerCanvas.tsx`

- [ ] **Step 1: Data**

`building.json`:

```json
"site": {
  "groundMargin": { "sw": 4.5, "se": 2.5, "ne": 2.5, "nw": 2.5 },
  "groundY": { "nw": 2.3, "se": 1.3 },
  "hedgeEdges": [5, 4],
  "fenceEdges": [5, 4],
  "doc": "Bakkeplan med fall NV->SE langs gata (fasade-PDF terrenglinje). groundY = world-y for bakkeplanet i NV- og SE-enden; hekk+smijernsgjerde langs sørvest (gate) og sørøst."
}
```
Passthrough i `build_geometry()` (`"site": b.get("site")`), type i `types.ts`:

```ts
export interface SiteGeo {
  groundMargin: { sw: number; se: number; ne: number; nw: number };
  groundY: { nw: number; se: number };
  hedgeEdges: number[]; fenceEdges: number[]; doc?: string;
}
```
`BuildingGeo` får `site?: SiteGeo;`.

- [ ] **Step 2: Site.tsx**

```tsx
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useVelger } from '../state/store';
import { slabFromQuad, type V3 } from '../lib/roofGeometry';
import { insetPolygon } from '../lib/shapes';
import { edgeDentils } from '../lib/facade';
import type { BuildingGeo } from '../lib/types';

const GROUND = '#D9D5CC';

/** Tomt: skrånende bakkeplate + hekk + mur/smijernsgjerde. Fades i exploded. */
export function Site({ geo }: { geo: BuildingGeo }) {
  const mode = useVelger((s) => s.mode);
  const group = useRef<THREE.Group>(null!);
  const site = geo.site;

  const parts = useMemo(() => {
    if (!site) return null;
    const s = geo.scale;
    const xs = geo.envelope.poly.map((p) => p[0] * s);
    const ys = geo.envelope.poly.map((p) => p[1] * s);
    // px-rom: x øker mot NE-siden, y øker mot SE (Ole Fladagers gate).
    // world: x = px·s, z = −py·s. SW-kant (gata) = min(x)-siden (edge 5).
    const xMin = Math.min(...xs) - site.groundMargin.sw;
    const xMax = Math.max(...xs) + site.groundMargin.ne;
    const yMin = Math.min(...ys) - site.groundMargin.nw; // NV-ende (py lav)
    const yMax = Math.max(...ys) + site.groundMargin.se; // SE-ende (py høy)
    const yAt = (py: number) => {
      const t = (py - Math.min(...ys)) / (Math.max(...ys) - Math.min(...ys));
      return site.groundY.nw + t * (site.groundY.se - site.groundY.nw);
    };
    // Fire hjørner (world): z = −py·s, fall langs py-aksen.
    const c = (x: number, py: number): V3 => [x, yAt(py), -py];
    const ground = slabFromQuad(c(xMin, yMin), c(xMax, yMin), c(xMax, yMax), c(xMin, yMax), 0.25);

    // Hekk + gjerde: plasseringer langs outset-kopier av envelope.
    const hedgeLine = insetPolygon(geo.envelope.poly, -1.1 / s);
    const fenceLine = insetPolygon(geo.envelope.poly, -1.9 / s);
    const hedgeRuns = site.hedgeEdges.map((e) => ({
      a: hedgeLine[e], b: hedgeLine[(e + 1) % hedgeLine.length],
    }));
    const fencePosts = site.fenceEdges.flatMap((e) => {
      const sub: [number, number][] = [fenceLine[e], fenceLine[(e + 1) % fenceLine.length]];
      return edgeDentils([sub[0], sub[1], sub[1], sub[0]], s, 0.14)
        .filter((_, i, arr) => i < arr.length / 2); // én retning av det degenererte "polygonet"
    });
    const fenceRuns = site.fenceEdges.map((e) => ({
      a: fenceLine[e], b: fenceLine[(e + 1) % fenceLine.length],
    }));
    return { ground, hedgeRuns, fenceRuns, fencePosts, yAt, s };
  }, [geo, site]);

  useFrame((_, dt) => {
    if (!group.current) return;
    const target = mode === 'exploded' ? 0 : 1;
    group.current.traverse((m) => {
      const mat = (m as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
      if (mat) {
        mat.opacity = THREE.MathUtils.damp(mat.opacity, target, 5, dt);
        mat.transparent = true;
        (m as THREE.Mesh).visible = mat.opacity > 0.02;
      }
    });
  });

  if (!site || !parts) return null;
  const m = geo.materials;
  const runMesh = (a: [number, number], b: [number, number], h: number, d: number, color: string, lift: number) => {
    const ax = a[0] * parts.s, az = -(a[1] * parts.s);
    const bx = b[0] * parts.s, bz = -(b[1] * parts.s);
    const len = Math.hypot(bx - ax, bz - az);
    const y = parts.yAt(((a[1] + b[1]) / 2) * parts.s) + lift + h / 2;
    return (
      <mesh position={[(ax + bx) / 2, y, (az + bz) / 2]} rotation={[0, Math.atan2(bz - az, bx - ax), 0]}>
        <boxGeometry args={[len - 2, h, d]} />
        <meshStandardMaterial color={color} roughness={1} />
      </mesh>
    );
  };
  return (
    <group ref={group}>
      <mesh geometry={parts.ground} receiveShadow>
        <meshStandardMaterial color={GROUND} roughness={1} />
      </mesh>
      {parts.hedgeRuns.map((r, i) => (
        <group key={`h${i}`}>{runMesh(r.a, r.b, 1.1, 0.7, m.hekkGronn, 0)}</group>
      ))}
      {parts.fenceRuns.map((r, i) => (
        <group key={`f${i}`}>
          {runMesh(r.a, r.b, 0.4, 0.18, m.pussHvit, 0)}
          {runMesh(r.a, r.b, 0.04, 0.04, m.karmSort, 0.9)}
        </group>
      ))}
      {parts.fencePosts.map((p, i) => (
        <mesh key={`p${i}`} position={[p.x, parts.yAt(-p.z) + 0.65, p.z]}>
          <boxGeometry args={[0.02, 0.5, 0.02]} />
          <meshStandardMaterial color={m.karmSort} roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}
```
NB til utfører: (1) `slabFromQuad`-winding avgjør om platens topp peker opp — flip hjørnerekkefølge hvis platen ser sort/feilbelyst ut. (2) `fencePosts`-konstruksjonen via degenerert polygon er et hack — hvis den gir doble/rare punkter, skriv en liten `edgePoints(a, b, scale, spacing)`-variant i `lib/facade.ts` (samme logikk som edgeDentils, én kant). (3) `yAt` tar py i meter-rom — hold enheter konsistente (py·s). Verifiser fallretningen mot fasade-PDF (lavest mot SE/Ole Fladagers gate). Monter i `Building.tsx`: `<Site geo={geo} />`.

- [ ] **Step 3: CameraRig — inkluder tomta i AABB**

I `assembledBox`, etter floors-løkken:

```ts
if (geo.site) {
  const m = geo.site.groundMargin;
  const env = geo.envelope.poly;
  const xs = env.map((p) => p[0] * geo.scale);
  const zs = env.map((p) => -(p[1] * geo.scale));
  const gy = Math.min(geo.site.groundY.nw, geo.site.groundY.se) - 0.3;
  box.expandByPoint(v.set(Math.min(...xs) - cx - m.sw, gy, Math.min(...zs) + cz - m.se));
  box.expandByPoint(v.set(Math.max(...xs) - cx + m.ne, gy, Math.max(...zs) + cz + m.nw));
}
```
NB: world-z = cz − py·scale; verifiser min/max-mapping mot resten av funksjonen ved implementering (NV = +z).

- [ ] **Step 4: Verifiser + commit**

Regenerer, test, build, screenshots (`/tmp/a7-shots`, alle states + mobil): bygget står på skrånende plate, hekk + gjerde langs gata, sokkel mest synlig mot SE-hjørnet, tomta fader bort i eksplodert, fit-check-marginer fortsatt fornuftige (kjør `node fit-check.mjs http://localhost:4317 /tmp/a7-fit` og `node measure.mjs /tmp/a7-fit` — alle PASS).

```bash
git add tools/velger-data app/src
git commit -m "Add sloping ground plane with hedge and iron fence"
```

---

# Workstream B — Plantegninger

## Task B0: DSL-utvidelser (åpent ned, skravur, sluk, hems-stige)

**Files:**
- Modify: `tools/plantegning/plan_dsl.py` (render_hems), `tools/plantegning/fixtures.py`
- Create: `tools/plantegning/test_plan_dsl.py`

- [ ] **Step 1: Skriv feilende pytest**

`tools/plantegning/test_plan_dsl.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fixtures
import plan_dsl


def _hems_spec(**kw):
    base = {"envelope": [[0, 0], [400, 0], [400, 300], [0, 300]],
            "rooms": [{"name": "Stue", "area": "10,0", "kind": "rom",
                       "poly": [[20, 20], [380, 20], [380, 280], [20, 280]]}],
            "hems": {"poly": [[0, 0], [200, 0], [200, 150], [0, 150]], "area": "3,0", **kw}}
    return base


def test_sluk_symbol_exists():
    assert 'id="sluk"' in fixtures.DEFS
    assert plan_dsl.SYM_SIZE["sluk"] == (12, 12)


def test_hems_open_edge_renders_label_and_dash():
    svg = plan_dsl.render_hems(_hems_spec(open={"edge": [[0, 150], [200, 150]], "label": "Åpent ned"}))
    assert "Åpent ned" in svg
    assert "stroke-dasharray" in svg


def test_hems_skravur_renders_diagonals():
    svg = plan_dsl.render_hems(_hems_spec(skravur=[[0, 0], [100, 0], [100, 80], [0, 80]]))
    assert svg.count("<line") >= 4          # diagonale skravurlinjer
    assert "clip-path" in svg               # klippes til skravur-polygonet


def test_hems_ladder_renders():
    svg = plan_dsl.render_hems(_hems_spec(ladder=[150, 100, 40, 12]))
    assert svg.count("<line") >= 2          # stige-trinn
```

```bash
cd tools/plantegning && python3 -m pytest test_plan_dsl.py -v
```
Forventet: 4 FAIL.

- [ ] **Step 2: Implementer**

`fixtures.py` — nytt symbol i DEFS (før `</defs>`):

```python
  <!-- Sluk: 12x12cm -->
  <g id="sluk">
    <circle cx="6" cy="6" r="5" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <line x1="2" y1="6" x2="10" y2="6" stroke="{INK}" stroke-width="0.5"/>
    <line x1="6" y1="2" x2="6" y2="10" stroke="{INK}" stroke-width="0.5"/>
  </g>
```
`plan_dsl.py`: `SYM_SIZE["sluk"] = (12, 12)`.

`render_hems()` — etter `hatch`-blokken, før labels (alle koordinater shiftes med `-x0+pad` som hatch gjør):

```python
    if hems.get("skravur"):
        sp = [[x - x0 + pad, y - y0 + pad] for x, y in hems["skravur"]]
        sx0, sy0, sx1, sy1 = _bbox(sp)
        parts.append(f'<clipPath id="skr"><polygon points="{_pts(sp)}"/></clipPath>')
        lines = [f'<g clip-path="url(#skr)" stroke="{INK}" stroke-width="0.6" opacity="0.6">']
        c = sx0 - (sy1 - sy0)
        while c < sx1:
            lines.append(f'<line x1="{c:.0f}" y1="{sy1:.0f}" x2="{c + (sy1 - sy0):.0f}" y2="{sy0:.0f}"/>')
            c += 14
        lines.append("</g>")
        parts.append("".join(lines))
    if hems.get("open"):
        op = hems["open"]
        (x1, y1), (x2, y2) = op["edge"]
        x1, y1, x2, y2 = x1 - x0 + pad, y1 - y0 + pad, x2 - x0 + pad, y2 - y0 + pad
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{INK}" stroke-width="1.4" stroke-dasharray="8 5"/>'
        )
        lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 6
        parts.append(
            f'<text x="{lx:.0f}" y="{ly:.0f}" font-family="Helvetica" font-size="10" '
            f'fill="{INK}" text-anchor="middle">{op.get("label", "Åpent ned")}</text>'
        )
    if hems.get("ladder"):
        lx, ly, lw, lh = hems["ladder"]
        lx, ly = lx - x0 + pad, ly - y0 + pad
        lad = [f'<rect x="{lx:.0f}" y="{ly:.0f}" width="{lw:.0f}" height="{lh:.0f}" fill="none" stroke="{INK}" stroke-width="0.9"/>']
        n = max(2, int(max(lw, lh) // 15))
        if lw >= lh:
            for i in range(1, n):
                fx = lx + i * lw / n
                lad.append(f'<line x1="{fx:.0f}" y1="{ly:.0f}" x2="{fx:.0f}" y2="{ly + lh:.0f}" stroke="{INK}" stroke-width="0.9"/>')
        else:
            for i in range(1, n):
                fy = ly + i * lh / n
                lad.append(f'<line x1="{lx:.0f}" y1="{fy:.0f}" x2="{lx + lw:.0f}" y2="{fy:.0f}" stroke="{INK}" stroke-width="0.9"/>')
        parts.append("".join(lad))
```

- [ ] **Step 3: Kjør pytest — forvent PASS. Commit**

```bash
cd tools/plantegning && python3 -m pytest test_plan_dsl.py -v
git add tools/plantegning
git commit -m "Add sluk symbol and hems open-edge, skravur and ladder rendering"
```

---

## Tasks B1–B16: Rett avvik per enhet (16 parallelle tasks)

**Files per task (X = enhets-ID, f.eks. H0101):**
- Modify: `tools/plantegning/specs/X.json`
- Regenerert output: `eiendommer/dybwads gate 8/rentegning/X-plan.svg` (+ `X-hems.svg`), `eiendommer/dybwads gate 8/plantegninger/X.svg` + `X.pdf`, `eiendommer/dybwads gate 8/qa/X-compare.html`

**Felles prosedyre (gjelder alle 16, kjør for din enhet X):**

- [ ] **Step 1: Regenerer fra dagens spec og verifiser funnene**

```bash
cd tools/plantegning
python3 plan_dsl.py X
```
Les `eiendommer/dybwads gate 8/rentegning/X-plan.svg` og `X-hems.svg` (SVG = tekst), les `eiendommer/dybwads gate 8/underlag/X-crop.png` (bilde) og relevant `arkitekt/Boenheter_*.pdf`. Gå gjennom HVERT funn for X i avviksrapporten vedlegg B (`docs/superpowers/specs/2026-06-07-avviksrapport-dybwads-gate-8.md`) og klassifiser: reelt / allerede løst / feilobservasjon. Funn under «Standard-sjekkliste» og «Enhetsspesifikke fikser» nedenfor SKAL adresseres hvis reelle.

- [ ] **Step 2: Fiks spec-JSON**

Standard-sjekkliste (mønster A/B/C — gjelder alle enheter):
1. **Stige:** `extras` skal ha `{"type": "ladder", "rect": [...]}` plassert der arkitekt-croppen viser stigen, + `{"type": "label", "text": "Stige til hems", ...}` ved siden av (rotér med `rot` hvis trangt).
2. **Hems-markering i plan:** stiplet `dashed`-polygon over hems-sonen + `{"type": "label", "text": "Hems", ...}` hvis croppen viser det.
3. **Hems-SVG:** `hems.open` (åpen kant mot rommet under, jf. crop) + `hems.skravur` der arkitekten skraverer (lavt under tak) + `hems.ladder` der stigen treffer hemsen (nye B0-felt).
4. **Bad:** `{"sym": "dusj", ...}` (inkluderer sluk) der croppen viser dusjsone; frittstående `{"sym": "sluk", ...}` der arkitekten viser sluk utenfor dusjen.
5. **Annotasjoner:** `extras`-labels for «NB! Rømningsvindu», «Ikke vindu», «EI60»/«54db» der arkitekten har dem.
6. **Kjøkken-areal:** `labels` for kjøkken skal ha `area` der arkitekten oppgir det; ellers konsistent uten.
7. **Areal-konsistens:** `rooms[].area` == `labels[].area` for samme rom; rompolygon-areal (px² → m² via croppens målestokk) skal stemme med arealteksten innenfor ±8 %.

Enhetsspesifikke fikser (fra avviksrapporten — verifiser først, jf. Step 1):

| Task | Enhet | Må fikses (critical/major) |
|---|---|---|
| B1 | H0101 | «NB! Rømningsvindu»-note; gang-polygon ~22 % for liten (juster grense gang/bad); «Stige til hems»-tekst; «Påforing. Tilpasses soil og innebygget sisterne»-note i bad; hems: «Åpent ned»-label; sluk i bad (SØ-hjørne) |
| B2 | H0102 | Gang ~11 % for bred / stue ~13 % for liten (flytt skillevegg); stige + tekst; «Hems»-tekst i plan; «Ikke vindu»- og EI60/54db-noter; sluk |
| B3 | H0103 | **Baddør mangler** (opening + door inn til bad); bad-polygon ~22 % for stor; hems-SVG: stige + åpent-ned; BRA-tekst konsistens (26,5) |
| B4 | H0104 | Dusj i bad; stige + tekst (begge SVG-er); stiplet hems-sone i plan dekker bare SV-hjørnet — utvid til arkitektens utstrekning; hems: åpent-ned |
| B5 | H0105 | **Inngangsdør mangler** (sør i gang, mot felleskorridor); baddør slagretning (buen skal inn i bad: juster `angle`/`sweep`); rømningsvindu på nordvegg + NB-note |
| B6 | H0201 | Hems-polygon 23 px utenfor østvegg (klipp til x=409); stue/bad-proporsjon (~12 %); dusj flyttes til SØ-hjørne; stige + tekst; hems vestgrense x=179→186 |
| B7 | H0202 | **Gang vest 3,5 m² mangler** (nytt rom + label); **hoveddør vest** (flytt fra nord); baddør fra gang øst; dusj; stige/trapp + tekst; hems-polygon ~40 % for stor vs 4,4 m²; «Ikke vindu» + EI60/54db |
| B8 | H0203 | **BRA 26,8 → 25,8** (alle arealtekster); bad-polygon ~12 % for liten; dusj; stige + tekst |
| B9 | H0204 | «Nisje over benk»-label i kjøkken; skyvedør-markering inngang (tegn uten slagbue: opening uten door + label «Skyvedør»); bad SV-hjørne-geometri mot crop; sluk; hems: åpent-ned + forklar stiplet boks (stige-ankomst: bruk hems.ladder) |
| B10 | H0205 | **BK-polygon 1,0 → 2,3 m²** (flytt vegg; oppdater tilstøtende rom); dusj; BK-dør bue ≥ 60 cm; hems: åpent-ned; stige som ordentlig ladder-extras (ikke diagonal strek) |
| B11 | H0301 | Stige + «Stige til hems»-tekst; hems: åpent-ned + skravur over bad-sonen; rømningsvindu-NB; østvindu: ett vindu (fjern dobbel); kjøkken langs nordvegg (flytt fixtures); enhets-ID-tekst i SVG (label «H0301») |
| B12 | H0302 | Hems-stipling + «Hems»-tekst over stue/sov; stige + tekst (NV i stue/sov); slagbue eller åpen-passasje-avklaring gang↔stue (jf. crop) |
| B13 | H0303 | Hems: åpent-ned-markering; stige + tekst (øst i rommet, sør for bad); kjøkkenbenk mot nordvegg justeres mot crop |
| B14 | H0304 | Stige + tekst; hems: skravur; gap gang/bad-polygon 27 px (lukk mot arkitektens vegglinje) |
| B15 | H0305 | **Baddør mangler** (gang→bad, slår inn i bad); dusj; hems: åpent-opp-markering + stige; stige + tekst i plan (østvegg stue/sov) |
| B16 | H0306 | **Dusj mangler**; baddør slagretning (inn i bad); hems: «Åpent ned»-label; stige-label + flytt stigen til arkitektens posisjon; rømningsvindu-NB på vestvindu |

- [ ] **Step 3: Regenerer og valider**

```bash
cd tools/plantegning
python3 plan_dsl.py X && python3 build_pages.py X && python3 export_pdf.py X
python3 compare.py X
python3 qa_score.py X 0 0 --search
```
Gate: `edge-precision ≥ 0.80` OG ikke dårligere enn før endringen (kjør qa_score FØR Step 2 og noter baseline). Les compare-HTML-ens overlay (screenshot via `shot.py` eller les SVG/PNG direkte) og bekreft visuelt at fiksene matcher croppen.

- [ ] **Step 4: Commit**

```bash
git add "tools/plantegning/specs/X.json" "eiendommer/dybwads gate 8/rentegning" "eiendommer/dybwads gate 8/plantegninger" "eiendommer/dybwads gate 8/qa"
git commit -m "Fix X floor plan deviations against architect drawings"
```

---

## Task B17: Batch-regenerering + QA-tabell for alle 16

**Files:** alle outputs fra B1–B16 + `eiendommer/dybwads gate 8/qa/`

- [ ] **Step 1: Full regenerering**

```bash
cd tools/plantegning
for uid in H0101 H0102 H0103 H0104 H0105 H0201 H0202 H0203 H0204 H0205 H0301 H0302 H0303 H0304 H0305 H0306; do
  python3 plan_dsl.py $uid || exit 1
done
python3 build_pages.py && python3 export_pdf.py
```

- [ ] **Step 2: QA-score-tabell**

```bash
for uid in H0101 H0102 H0103 H0104 H0105 H0201 H0202 H0203 H0204 H0205 H0301 H0302 H0303 H0304 H0305 H0306; do
  python3 qa_score.py $uid 0 0 --search
done
```
Alle ≥ 0.80 edge-precision. Enheter under: tilbake til sin B-task.

- [ ] **Step 3: Sentral fullskala-review (påkrevd per prosjektregel)**

Orkestratoren (hovedsesjonen) leser alle 16 `qa/X-compare.html`-overlays / genererte PDF-er i full skala og godkjenner. Ikke deleger denne.

- [ ] **Step 4: Commit**

```bash
git add "eiendommer/dybwads gate 8" && git commit -m "Regenerate all floor plans and QA artifacts"
```

---

# Workstream C — Etasjegeometri og validering

## Task C1: Per-enhet BRA-validator i build_data.py

**Files:**
- Modify: `tools/velger-data/build_data.py`
- Test: `tools/velger-data/test_build_data.py`

- [ ] **Step 1: Skriv feilende tester**

```python
def test_poly_area_m2():
    # 100x100 px ved scale 0.012696 = 1.612 m²
    assert abs(build_data.poly_area_m2([[0, 0], [100, 0], [100, 100], [0, 100]]) - 1.612) < 0.01


def test_unit_area_validator_flags_mismatch():
    floors = {"2": {"units": [{"id": "HX", "unit": "HX", "poly": [[0, 0], [100, 0], [100, 100], [0, 100]]}]}}
    arch = {"HX": {"bra": 30.0}}          # polygon er 1.6 m² — langt unna
    errors, warnings = build_data.validate_unit_areas(floors, arch, {}, strict=True)
    assert any("HX" in e for e in errors)
    errors2, warnings2 = build_data.validate_unit_areas(floors, arch, {}, strict=False)
    assert not errors2 and any("HX" in w for w in warnings2)


def test_unit_area_validator_passes_within_tolerance():
    floors = {"2": {"units": [{"id": "HX", "unit": "HX", "poly": [[0, 0], [1364, 0], [1364, 1364], [0, 1364]]}]}}
    arch = {"HX": {"bra": 300.0}}         # 1364² px ≈ 299.9 m²
    errors, _ = build_data.validate_unit_areas(floors, arch, {}, strict=True)
    assert errors == []


def test_duplex_u_polygons_checked_against_braU():
    floors = {"u": {"units": [{"id": "HX-U", "unit": "HX", "poly": [[0, 0], [100, 0], [100, 100], [0, 100]]}]}}
    prisliste = {"HX": {"braU": 30}}
    errors, _ = build_data.validate_unit_areas(floors, {}, prisliste, strict=True)
    assert any("HX-U" in e or "HX" in e for e in errors)
```
Kjør — forvent FAIL (`poly_area_m2` finnes ikke).

- [ ] **Step 2: Implementer i build_data.py**

```python
SCALE = 0.012696
AREA_TOL = 0.12  # 12 % — polygonene følger innvendige vegglinjer, BRA inkluderer innervegger


def poly_area_m2(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2 * SCALE * SCALE


def validate_unit_areas(floors, arch, prisliste, strict=False):
    """Polygon-areal per enhet vs arkitekt-BRA (hoveddel) og braU (duplex-U)."""
    errors, warnings = [], []
    sink = errors if strict else warnings
    main_area, u_area = {}, {}
    for fid, f in floors.items():
        for u in f["units"]:
            tgt = u_area if fid.lower() == "u" else main_area
            tgt[u["unit"]] = tgt.get(u["unit"], 0.0) + poly_area_m2(u["poly"])
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
```
I `main()`, etter `validate_envelope_containment()`:

```python
    import os
    strict_areas = os.environ.get("VELGER_STRICT_AREAS") == "1"
    area_errors, area_warnings = validate_unit_areas(_load_floors(), _load_arch(), prisliste, strict=strict_areas)
    errors += area_errors
    warnings += area_warnings
```

- [ ] **Step 3: Kjør tester — PASS. Kjør build i warn-modus og noter status quo**

```bash
cd tools/velger-data && python3 -m pytest test_build_data.py -v
python3 build_data.py   # forvent WARN-linjer for enhetene C2/C3 skal fikse (bl.a. H0101, braU)
```

- [ ] **Step 4: Commit**

```bash
git add tools/velger-data
git commit -m "Add per-unit polygon area validation against architect BRA"
```

---

## Task C2: Kalibrer etasje 1, 2 og 3 (tre parallelle del-tasks: C2a/C2b/C2c)

**Files:** `tools/velger-data/floors/etasje-1.json`, `etasje-2.json`, `etasje-3.json`

**Felles prosedyre per etasje:**

- [ ] **Step 1: Undersøk vest-gapet FØR endring**

```bash
cd tools/velger-data && python3 qa_overlay.py
```
Les `tools/velger-data/qa/etasje-N.html` (base64-PNG med polygon-overlay) og relevant `eiendommer/dybwads gate 8/underlag/etasje-N-plan-1.png`. Mål vestveggens tykkelse på underlaget der enhetene starter (etasje 1: x=865, etasje 2: x=827, etasje 3: x=828; outline x=748). Hvis arkitekten viser at enhetsflater går nærmere fasaden: flytt vestgrensene tilsvarende. Hvis veggen/sjakter reelt er så tykke: IKKE flytt (BRA-summer stemmer i dag — blind flytting blåser opp arealene). Dokumenter konklusjonen i commit-meldingen.

- [ ] **Step 2: Konkrete grensefiks (verifiser hver mot overlay før endring)**

**C2a — etasje-1.json:**
- H0101: `[[1690,1400],...]` → nordgrense y=1400 → **1340** (areal 14,5 → 17,4 m²; arkitekt 17,8).
- Korridor: legg ny common-polygon `[[1257,1093],[1664,1093],[1664,1340],[1257,1340]]` (juster kantene mot naboflatene til `check_overlaps.py` er grønn).
- H0105-notch: i `common[0]`, erstatt segmentet `...[1491,913],[1267,913]]` med `...[1491,913],[1233,913],[1233,640],[1267,640]]` slik at gapet x=[1233,1267], y=[640,905] dekkes (speiler H0105s L-form).

**C2b — etasje-2.json:**
- H0201: toppkant y=1240 → **1300** (21,0 → 18,2 m²; arkitekt 18,5 — trappelanding ut av enheten).
- H0202: østgrense x=1512 → **1547**; `common[2]` vestgrense 1512 → 1547 tilsvarende.
- H0205: mål L-formens innervegger på overlay; juster polygonet til ~30,2 m² ±10 % (arkitekt-BRA). Typisk: trekk veggsonene mellom H0205/H0204 og rundt bod ut av polygonet.

**C2c — etasje-3.json:**
- Skillevegg H0302/H0303: x=1223 → **1193** i begge polygoner (H0302 ≈ 22,0, H0303 ≈ 25,2 m²).
- H0306 nordgap y=[375,425]: sjekk underlag — hvis korridor/fellesareal: ny common-polygon `[[748,375],[1216,375],[1216,425],[748,425]]`; hvis yttervegg-sone: la stå og dokumenter.

- [ ] **Step 3: Valider**

```bash
cd tools/velger-data
python3 check_overlaps.py && python3 qa_overlay.py && python3 build_data.py
```
Les qa/etasje-N.html på nytt: grønne polygoner følger arkitektens vegger. `build_data.py`: WARN-listen for denne etasjen skal være tom (eller dokumentert akseptert).

- [ ] **Step 4: Commit (per etasje)**

```bash
git add tools/velger-data/floors tools/velger-data/qa
git commit -m "Calibrate floor N unit boundaries against architect plan"
```

---

## Task C3: Etasje U — duplex-BRA og buffere

**Files:** `tools/velger-data/floors/etasje-u.json`

- [ ] **Step 1: Les fasit**

Les `eiendommer/dybwads gate 8/arkitekt/Underetasje.pdf` + `tools/velger-data/qa/etasje-u.html` + `underlag/etasje-u-plan-1.png`. Identifiser hvilke BOD-/disponible rom som tilhører H0101 (braU = 30) og H0103 (braU = 33) — i dag dekker polygonene bare 14,5 og 22,9 m²; resten ligger feilaktig i `common[]`.

- [ ] **Step 2: Fiks polygoner**

- H0103-U: vestgrense x=865 → **772** (dekk BOD-stripen; 748 + 24 px vegg).
- Begge enheter: sørgrense y=1690 → **1676** (0,30 m veggbuffer).
- H0103-U østsøm: x=1262 → **1280** (lukk 0,23 m gap mot common).
- H0101-U: utvid polygonet (eller legg til oppføring nr. 2 med `"id": "H0101-U2", "unit": "H0101"`) til å dekke H0101s boder per Underetasje.pdf, mål: polygonsum ≈ 30 m² ±12 %. Tilsvarende common-polygoner krympes.

- [ ] **Step 3: Valider + commit**

```bash
cd tools/velger-data && python3 check_overlaps.py && python3 qa_overlay.py && python3 build_data.py
```
WARN-linjene for `H0101-U`/`H0103-U` borte. Les qa/etasje-u.html og bekreft mot PDF.

```bash
git add tools/velger-data/floors tools/velger-data/qa
git commit -m "Reclassify basement storage into duplex unit polygons"
```

---

## Task C4: Strict-flip + full regenerering

**Files:** `tools/velger-data/build_data.py`, `tools/velger-data/test_build_data.py`

- [ ] **Step 1: Flip default**

I `main()`: `strict_areas = os.environ.get("VELGER_STRICT_AREAS", "1") == "1"` (strict er nå default; `VELGER_STRICT_AREAS=0` gir escape-luke). Oppdater pytest:

```python
def test_real_data_passes_strict_area_validation():
    errors, _ = build_data.validate_unit_areas(
        build_data._load_floors(), build_data._load_arch(),
        build_data._load("prisliste.json"), strict=True)
    assert errors == []
```

- [ ] **Step 2: Kjør alt + commit**

```bash
cd tools/velger-data && python3 -m pytest test_build_data.py -v && python3 build_data.py
git add tools/velger-data
git commit -m "Make per-unit area validation strict by default"
```

---

# Final — QA-gate og deploy

## Task F1: Lys-rebalansering + full QA-suite + sentral review

**Files:**
- Modify (ved behov): `app/src/scene/VelgerCanvas.tsx`
- QA-artefakter: `/tmp/f1-*`

- [ ] **Step 1: Full build**

```bash
cd tools/velger-data && python3 build_data.py
cd ../../app && npm test && npm run build
npx vite preview --port 4317 --strictPort &
```

- [ ] **Step 2: Full QA-suite**

```bash
cd tools/velger-qa
node shots.mjs http://localhost:4317 /tmp/f1-shots
node facade.mjs http://localhost:4317 /tmp/f1-facade
node fit-check.mjs http://localhost:4317 /tmp/f1-fit && node measure.mjs /tmp/f1-fit
node click_units.mjs http://localhost:4317
```
Krav: click_units alle 16 grønne; measure alle PASS; facade-shots sammenlignes mot `ref-sorvest-1.png`/`ref-soroest-1.png` (fasade-PDF-raster) — takvinkel, frontespise-posisjon og vindusrytme skal treffe tegningen.

- [ ] **Step 3: Lys-rebalansering**

Les `/tmp/f1-shots/*.png`. Hvis sort tak/skyggesider drukner: juster i `VelgerCanvas.tsx` — `ambientLight intensity` 0.55 → 0.65–0.75 og/eller `directionalLight intensity` 1.1 → 1.3, `environmentIntensity` 0.25 → 0.35. Re-shoot til taket leser med form (mønelinje synlig mot bakgrunn) og rosa/hvit-kontrasten matcher renderen.

- [ ] **Step 4: Sentral fullskala-review (orkestrator — ikke deleger)**

Les i full skala: landing, orbit, exploded, panel, mobil, mobil-panel + facade-par, side om side med `renders utvendig/dybwads_8_sørvest_dag.png` og `003090-5.jpg`/`003090-6.jpg`. Sjekkliste: silhuett (takvinkel + frontespise over møne), fargefasit, vindusrytme 5 akser m/blind midtakse, gesims/tannsnitt, gavlbalkong, innganger, tomt-fall, eksplodert visning fortsatt ren og lesbar, brand-grønn glød intakt. Fiks-forward ved avvik (mindre justeringer direkte; større → tilbake til riktig A-task).

- [ ] **Step 5: Kill preview + commit eventuelle justeringer**

```bash
lsof -ti:4317 | xargs kill
git add app/src && git commit -m "Rebalance lighting for painted model" || true
```

## Task F2: Deploy + prod-verifikasjon

- [ ] **Step 1: Deploy**

```bash
cd worker && npx wrangler deploy
```
Noter prod-URL fra output (workers.dev).

- [ ] **Step 2: Prod-røyk**

```bash
cd ../tools/velger-qa
node shots.mjs https://<prod-url> /tmp/f2-prod
node click_units.mjs https://<prod-url>
```
Les landing + exploded + panel-shots: identisk med lokal QA. `/api/status` svarer (curl).

- [ ] **Step 3: Oppsummer**

Rapportér til bruker: hva som er deployet, QA-status, gjenstående kjente avvik (om noen).

---

## Self-review-notater (utført ved planskriving)

- **Spec-dekning:** Tak/frontespise/farger (A1–A3), vinduer/blindfelt (A4), gesims/tannsnitt (A5), innganger/balkong (A6), tomt (A7), street-edge-dedup (i A2), plantegnings-mønstre + harde feil (B0–B17), etasjegeometri + per-enhet-validering (C1–C4), QA-kriterier + fullskala-review (F1), feilhåndtering (nye felt går gjennom build_data → manglende felt feiler bygget; `?.`-guards i scene-koden for optionale felt). Avgrensninger respektert: ingen teksturer, ingen takrenner, ingen trær.
- **Bevisste avvik fra spec:** «NE-fløy senkes» løses via brattere hovedtak + recess.rise 0.9 (trinnet blir dramatisk uten å klippe 3.-etasjeveggene i fløyen) — kalibreres visuelt i F1 mot Fasade Sørøst; vinduer fades i eksplodert (spec oppdatert 2026-06-07).
- **Kjent risiko:** rakeL-trim-rotasjonen i A3 og site-AABB-fortegnene i A7 er flagget med eksplisitte verifiseringssteg.
