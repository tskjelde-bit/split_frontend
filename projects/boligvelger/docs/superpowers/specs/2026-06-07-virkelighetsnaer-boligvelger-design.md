# Virkelighetsnær boligvelger — Dybwads gate 8

**Dato:** 2026-06-07
**Status:** Godkjent design
**Scope:** Visuell oppgradering av 3D-boligvelgeren til «malt arkitektmodell» som er umiskjennelig lik det virkelige bygget, pluss retting av alle avvik funnet i plantegninger og etasjegeometri. Bygger på spec 2026-06-06 (3D-boligvelger) og avviksrapporten 2026-06-07.

## Mål

3D-modellen skal gå fra abstrakt gips-kasse til malt arkitektmodell med virkelige farger, sorte vindusrammer og korrekt silhuett — «veldig lik» renderne av ferdig bygg. Samtidig rettes alle plantegnings-avvik som villeder kjøper, og etasjegeometrien kalibreres mot arkitekt-fasit. Interaksjonsdesignet (orbit → eksplosjon → enhetspanel, brand-grønn valgt-glød) er uendret.

## Visuell fasit

- `eiendommer/dybwads gate 8/renders utvendig/dybwads_8_sørvest_dag.png` — sørvest-fasaden (gate)
- `eiendommer/dybwads gate 8/renders utvendig/003090-5.jpg`, `003090-6.jpg` — hjørner/gavler
- `eiendommer/dybwads gate 8/fasader/*.pdf` + `arkitekt/Fasade_*.pdf`, `Snitt_C.pdf` — geometri-fasit
- Avviksrapport: `docs/superpowers/specs/2026-06-07-avviksrapport-dybwads-gate-8.md`

Byggets karakter: 1890-talls historisme-villa. Laksrosa puss på 2.–3. etasje, hvit rustisert 1. etasje og sokkel, hvite vindusomramminger med kornisjer, tannsnittfrise og kraftige hvite gesimser, sentral spiss frontespise mot gaten, sort sinktak, sorte vinduskarmer, smijernsgjerde på lav hvit mur med hekk.

## Vedtatte valg

| Valg | Beslutning |
|---|---|
| Stilnivå | Malt modell + enkel tomt: virkelige flate farger, ingen foto-teksturer/normal maps |
| Vindusrammer | Sorte karmer med mørkt glass, hvit omramming på rosa felt (per render-fasit) |
| Tomt | Gateplan med fall, lav hvit mur + sort smijernsgjerde + hekk-volumer; dempes i eksplodert modus |
| Plantegninger | Alle mønster-avvik og harde feil rettes i alle 16 enheter, PDF-er regenereres |
| Etasjegeometri | Vest-gap, korridor, U-etasje-BRA og enhetsgrenser kalibreres; per-enhet BRA-validering i build |
| Pipeline | Fortsatt parametrisk (building.json → build_data.py → geometri.json → R3F). Ingen Blender/glTF |

## 1. Eksteriør-geometri (`tools/velger-data/building.json` + scene)

- **Takvinkel:** `roof.rise: 1.9 → ~5.0` m (≈41°; kalibreres eksakt mot Snitt_C). `ridgeOffset: 0.4` beholdes.
- **Frontespise** erstatter dagens mini-ark: ny `frontispiece`-gren i `app/src/lib/roofGeometry.ts` — flush vegg-gavl sentralt på sørvest-fasaden (edge 5), bredde ~3,6 m, spiss gavltopp nær mønehøyde, høyt vindu med spiss topp (rektangel + trekant), hvit omramming/dekor som lister.
- **`roof.dormers[]` fjernes.** Fasadetegningen viser flate kneveggsvinduer i 3. etg-båndet (to par til høyre for frontespisen) + takvindu — ikke utstikkende kvister. 3. etg-vinduene i `windows[]` justeres til tegningens rytme; takvinduer som flate mørke rektangler på takflaten.
- **NE-fløy (recess):** senkes tydeligere så trinnet i mønelinjen leses fra sørøst (lavere gesims + møne enn i dag; høydene kalibreres mot Fasade Sørøst-PDF).
- **Gesimser:** hvit utkraget etasjegesims over 1. og 2. etasje + takfotgesims med tannsnittfrise (rad av dentil-bokser, ren geometri — ingen relieff-tekstur).
- **Innganger** (`entrances[]` i building.json + ny `Entrance.tsx`): hoveddør med overlys + trapp på SØ-fløyen, bakdør NØ med 3 trinn. Midtaksen på sørvest-fasaden er **blindfelt** (hvit panelnisje), ikke dør.
- **Fransk smijernsbalkong** (sort) på gavlen 2. etg (`balconies[]` + enkel spile-geometri).
- **Piper:** slankere og høyere enn i dag, sorte (sinkkledde).
- **Kuttes:** takrenner/nedløp (cosmetic, visuell støy på liten modell).
- Gotcha som ryddes samtidig: street-edge-koordinatene er hardkodet dobbelt (`Roof.tsx:199-200`, `CameraRig.tsx:131-132`) — avledes fra `envelope.poly` ett sted.

## 2. Farger og materialer

Hardkodede gips-konstanter i `FloorPlate.tsx`, `Roof.tsx`, `Windows.tsx`, `UnitMesh.tsx` erstattes av `materials`-tokens i `geometri.json` (kilde: `building.json`), samplet fra render-fasit:

| Token | Verdi | Brukes på |
|---|---|---|
| `pussRosa` | `#E4B49C` | 2.–3. etg alle pussfasader |
| `pussHvit` | `#E9E6E0` | 1. etg, sokkel, gesimser, omramminger, frontespise-dekor |
| `takSort` | `#2E3038` | takflater, piper |
| `karmSort` | `#242424` | vinduskarmer, dører, smijern |
| `glassMork` | `#35353E` | glassflater (svak env-refleks) |
| `hekkGronn` | `#3A5224` | hekk-volumer |

- **Vinduer:** `Windows.tsx` bygges om fra boks-nisje til detaljert vindu: hvit ytre omramming + sort karm med midtpost + mørk glassplate. I eksplodert visning fades vinduene mykt ut sammen med veggskallet (skallet krymper til parapet — vinduer uten vegg ville svevd); i montert visning er de alltid synlige.
- **Per-etasje fasadefarge** i `floors[]` i geometri.json, lest av `FloorPlate.tsx` (U + 1. etg hvit, 2.–3. rosa).
- Valgt/hover/solgt-logikk i `UnitMesh.tsx` uendret (brand-grønn `#1E3D2B` / grå).
- Lys: dagens rigg i `VelgerCanvas.tsx` beholdes, intensitet rebalanseres mot mørkt tak (skyggesiden må fortsatt lese).

## 3. Tomt (enkel)

- Bakkeplate med gatefall langs sørvest (terrenget faller mot sørøst, jf. fasade-PDF), lav hvit mur med sort smijernsgjerde (instansierte spiler) og hekk-volumer (avrundede bokser) langs sørvest og sørøst, flat gårdsplass mot NØ.
- I eksplodert modus dempes tomta (opacity, samme mønster som vinduene i dag) så etasjeplatene forblir helten.
- Ingen trær, biler eller gatemøbler.

## 4. Plantegninger — retting av alle 16 enheter

Rentegning-SVG-ene i `eiendommer/dybwads gate 8/rentegning/` rettes, PDF-er regenereres via eksisterende pipeline (`tools/plantegning/`). Full detaljliste per enhet: avviksrapporten vedlegg B.

- **Mønster A (alle enheter):** stige til hems tegnes inn + tekst «Stige til hems skyves ut etter behov» (arkitektens formulering).
- **Mønster B (alle hems-SVG):** åpent-ned-markering/skravur så hems leses som åpen mezzanin.
- **Mønster C:** dusj (med diagonal) og sluk tegnes inn i bad som mangler: H0101, H0102, H0104, H0105, H0202, H0203, H0204, H0205, H0306.
- **Harde feil:** H0202 (gang vest 3,5 m² + inngangsdør vest), H0205 (BK-polygon 1,0 → 2,3 m²), H0203 (BRA 26,8 → 25,8 m²), H0103 + H0305 (manglende baddør), H0105 (inngangsdør), slagretninger (H0102, H0105, H0204, H0303, H0306).
- **Proporsjonsfeil** polygon-vs-egen-arealtekst rettes: H0101, H0102, H0103, H0201, H0203, H0205, H0306.
- **Annoteringer:** rømningsvindu-NB (H0101, H0201, H0301, H0306), «ikke vindu» (H0102, H0202), EI60/54db (H0102, H0306), kjøkken-m² konsistent på alle, enhets-ID i H0301.
- QA-gaten (`tools/plantegning/compare.py` + `qa_score.py`) kjøres på nytt for alle 16; full-skala review per memory-krav.

## 5. Etasjegeometri-kalibrering (`tools/velger-data/floors/*.json`)

- **Vest-gap:** ~0,7–1,5 m uforklart gap mot vestfasaden i alle etasjer kalibreres mot underlag (mer enn veggtykkelse 0,30 m skal ikke forekomme uten arkitekt-belegg).
- **Etasje 1:** manglende korridor (~14,9 m²) inn i `common[]`; H0101-nordgrense (y=1400 → y=1340, +3,0 m²).
- **Etasje 2:** H0201 (−trappelanding, 21,0 → 18,5 m²), H0202 (+2,2 m², høyregrense), H0205 (−innervegger i L-form).
- **Etasje 3:** skillevegg H0302/H0303 (x=1223 ~30 px vest).
- **Etasje U:** BOD omklassifiseres fra `common[]` til duplex-polygonene (H0101-U, H0103-U) så braU-visningen stemmer; sørveggbuffer 0,13 → 0,30 m.
- **`build_data.py`:** per-enhet BRA-validering mot arkitekt-fasit med toleranse (i dag valideres kun summer) — builden stopper ved enhetsavvik.

## 6. Feilhåndtering

- Uendret fra forrige spec: WebGL-fallback, status-API-degradering.
- Nye geometrifelt (`frontispiece`, `entrances`, `balconies`, `materials`, tomt) valideres i `build_data.py`; manglende felt gir byggfeil, ikke runtime-feil.
- Tomt og vinduer i eksplodert modus: opacity-demping, aldri fjerning av klikkflater for enheter.

## 7. QA og akseptkriterier

- **Fasade-diff:** `tools/velger-qa/facade.mjs` ortho-shots (sørvest + sørøst) diffes mot fasade-PDF-ene og render-fasit. Akseptkriterium: takvinkel, frontespise-posisjon/-proporsjon og vindusrytme matcher tegning; farger matcher render-tokens.
- **Regresjon:** `fit-check.mjs` (5 viewports × 3 modes) og `click_units.mjs` (alle 16 enheter) grønne.
- **Fullskala screenshot-review** i headless Chrome (landing, orbit, eksplodert, panel, mobil 390×844) før noe kalles ferdig.
- **Plantegninger:** qa_score-gate per enhet + visuell overlay mot underlag-crop.
- **Geometri:** `qa_overlay.py`-HTML-ene regenereres etter kalibrering; per-enhet BRA-validering i build.

## Avgrensninger

- Ingen teksturer/normal maps/UV-arbeid, ingen trær/biler, ingen fotorealistisk himmel.
- Ornament-relieffene i frisene antydes geometrisk (tannsnitt), ikke modellert/teksturert.
- Interiør-3D, admin, worker og one-pager-innhold røres ikke.
- Takrenner/nedløp utelates bevisst.

## Referanser

- Avviksrapport (full): `docs/superpowers/specs/2026-06-07-avviksrapport-dybwads-gate-8.md`
- Forrige spec: `docs/superpowers/specs/2026-06-06-3d-boligvelger-dybwads-gate-8-design.md`
- Plantegnings-spec: `docs/superpowers/specs/2026-06-05-plantegninger-dybwads-gate-8-design.md`
- Kode-fasit for utvidelsespunkter: `app/src/scene/*` (FloorPlate/Roof/Windows/UnitMesh/VelgerCanvas), `app/src/lib/roofGeometry.ts`, `tools/velger-data/build_data.py`, QA-verktøy i `tools/velger-qa/`
