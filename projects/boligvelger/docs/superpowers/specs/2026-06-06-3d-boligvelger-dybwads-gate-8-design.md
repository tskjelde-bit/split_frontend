# 3D-boligvelger — Dybwads gate 8

**Dato:** 2026-06-06
**Status:** Godkjent design
**Scope:** Prosjektnettside med interaktiv 3D-boligvelger for Dybwads gate 8 (16 enheter). Bygger videre på plantegnings-pipelinen fra 2026-06-05.

## Mål

En «vilt fet» svevende 3D-boligvelger: hele bygget som orbitérbar gips-modell som eksploderer i svevende etasjeplater, der kjøper finner sin enhet, ser plantegning og pris, og kontakter megler. Wow-faktor er eksplisitt prioritert. Mobil (QR fra prospekt/visning) er førsteklasses.

## Vedtatte valg

| Valg | Beslutning |
|---|---|
| Arketype | Hybrid: orbitérbar bygningsmodell → eksploderer til svevende etasjeplater |
| Visuell stil | Galleri/arkitektmodell: matt gips-hvit modell, krem bakgrunn (#FBFAF6), brand-grønn glød (#1E3D2B) på valgt enhet, myke kontaktskygger. Houeland brand v4, samme univers som plantegningssidene |
| Leveranse | Egen prosjektside (one-pager) med velgeren som hero + fullskjermsopplevelse. Embedbar modul er ikke et krav |
| Salgsdata | Full prisliste: pris, kvm-pris og status (ledig/reservert/solgt) per enhet |
| Admin | Minimal: én passordbeskyttet side som setter status per enhet. Bygges ut senere |
| Hosting | Cloudflare Worker (static assets + KV), midlertidig workers.dev-URL. Domene avgjøres senere |
| Teknologi | Vite + React + TypeScript, React Three Fiber + drei. Runtime-ekstrudering fra spec-JSON — ingen glTF/Blender |

## Opplevelsesflyt (godkjent storyboard)

1. **Landing** — gips-modellen svever og auto-roterer sakte på krem bakgrunn. Sfizia-tittel «Dybwads gate 8», underlinje «16 selveierleiligheter · Majorstuen». Ett interaksjonshint. Ingen meny i veien.
2. **Orbit + etasjevalg** — fri 360°-rotasjon (drag/touch). Etasje-chips nederst: 1. etg / 2. etg / 3. etg / Alle 16.
3. **Eksplosjon** — etasjeplatene glir fra hverandre med spring-easing. Hover/tap på enhet gir tooltip: H-nr, areal, pris. Solgte enheter dempes (grå), hovret/valgt enhet gløder brand-grønt.
4. **Enhetspanel** — klikk åpner sidepanel: plantegnings-SVG (zoombar), arealoppstilling, pris, status, «Kontakt megler»-CTA og PDF-nedlasting. Scenen dimmes bak. Duplex-enhetene viser begge plan.
5. **Mobil** — samme scene med touch-orbit; panelet blir bottom-sheet, chips blir touch-mål, redusert skyggekvalitet og DPR-clamp.

Rundt velgeren: slank one-pager — kort om prosjektet, beliggenhet (Majorstuen), kontakt/megler. Velgeren er helten.

## Geometri-pipeline (parametrisk)

Samme filosofi som plantegnings-DSL-en: agenter/scripts leverer data, ikke frihånds-3D.

- **Spec-JSON per etasje:** omriss-polygon for etasjeplaten + ett polygon per enhet. Kilde: vektorgeometrien i `eiendommer/dybwads gate 8/underlag/` og enhetsgrensene i `Boenheter_*.pdf`. Samme koordinatsystem og låste målestokk som rentegningene (1:100).
- **Etasjehøyder og takform** fra `Snitt_C.pdf`. Forenklet bygningsskall (yttervegger, takvolum, vindusåpninger som innfelte nisjer) fra fasade-PDF-ene. Gips-stilen krever ingen materialfasit.
- **Runtime-ekstrudering** med Three.js `ExtrudeGeometry` direkte fra JSON. Hele bygget er ~20 ekstruderte polygoner.
- **Duplex H0101/H0103:** U-delene modelleres som egne volumer i underetasjeplaten, koblet til samme enhets-ID. Underetasjen vises som egen plate under 1. etasje i eksplodert visning — ingen egen etasje-chip, den følger 1. etg-valget, og kun duplex-volumene markeres som salgbare.

## Datamodell

- **`units.json`** (statisk, bygges av tool-script): H-nr, navn, type, etasje, BRA-i, hems, duplex-deler, pris, kvm-pris, plantegnings-referanser.
  - Kilde pris: «Verdivurdering utsalgspriser Dybwads gate 8.docx» (09.01.26) — 16 enheter, totalt 91 270 000, 445 m² BRA-i.
  - Kjent avvik som korrigeres mot arkitektdata: prislisten oppgir H0201 som etasje 1 (skrivefeil — H0201 er 2. etasje); BRA-tall kryssjekkes mot Boenheter-tegningene.
- **Status** (ledig/reservert/solgt) i Cloudflare KV. `GET /api/status` returnerer alle. Alt annet er statisk.
- **Admin:** `/admin`, passord fra Worker-secret, tre statusknapper per enhet, skriver til KV.

## Arkitektur og struktur

```
app/                      # generisk velger-app (Vite + React + R3F)
  src/
  public/data/dybwads-gate-8/   # generert: geometri.json, units.json, plantegnings-SVG-er
tools/velger-data/        # leser underlag + prisliste + rentegninger → datasett
worker/                   # CF Worker: static assets, /api/status, /admin, KV-binding
```

Neste eiendom = nytt datasett gjennom samme tool-script, samme app.

## Feilhåndtering

- **Ingen WebGL / svak GPU:** statisk fallback — etasjeliste med plantegninger, arealer og priser (samme data, null 3D). QR-koden møter aldri en blank side.
- **Status-API nede:** enheter vises uten status-badge, resten fungerer.
- **Byggvalidering (stopper builden ved avvik):** sum BRA-i = 445 m², sum pris = 91 270 000, enhets-ID-er matcher de 16 rentegningene i `eiendommer/dybwads gate 8/rentegning/`.

## QA

- **Geometri-fidelity:** ortografisk topp-render av hver 3D-etasje diffes mot original underlag-SVG (samme overlay-metode som plantegnings-QA).
- **Fullskala screenshot-review** i headless Chrome: landing, orbit, eksplodert visning, enhetspanel, mobil-viewport (390×844). Påkrevd før noe kalles ferdig.
- **Interaksjonstest:** klikk hver av de 16 enhetene headless, verifiser at riktig panel åpner med riktige data.
- **Ytelse:** DPR-clamp, redusert geometri/skygge på mobil; manuell test på midrange-mobil før lansering.

## Avgrensninger

- Embedbar modul, CMS, megler-dashboard og budsignal er ikke i scope — admin er bevisst minimal.
- Fotorealistiske renders (leveres senere av Torbjørn) erstatter ikke 3D-modellen; de kan legges inn i one-pageren som galleri i en senere iterasjon.
- Domene og DNS er utsatt beslutning; alt bygges deploy-klart på workers.dev.
- SEO utover tittel/OG-tags er ikke prioritert i denne versjonen.

## Referanser

- Plantegnings-spec: `docs/superpowers/specs/2026-06-05-plantegninger-dybwads-gate-8-design.md`
- Prisliste: `eiendommer/dybwads gate 8/Verdivurdering utsalgspriser Dybwads gate 8.docx`
- Storyboard og stilvalg: `.superpowers/brainstorm/*/content/` (3d-arketype, visuell-stil, storyboard)
- Brand: `brand houeland 2-0/` (Sfizia, Engravers' Gothic, designmanual v4)
