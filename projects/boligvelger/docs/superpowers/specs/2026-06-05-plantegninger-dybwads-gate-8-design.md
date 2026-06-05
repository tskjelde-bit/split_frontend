# Plantegningssider — Dybwads gate 8

**Dato:** 2026-06-05
**Status:** Godkjent design
**Scope:** 16 plantegningssider (web + print). Boligvelger-nettsiden er eget, senere prosjekt.

## Mål

Produsere én brandet plantegningsside per leilighet i Dybwads gate 8 (Landlord Eiendom AS, Medvind Arkitektur rev B 08.05.25), i Houeland brand v4, fra arkitektens byggesøknadstegninger.

## Leveranse

16 enheter: H0101–H0105 (1. etg), H0201–H0205 (2. etg), H0301–H0306 (3. etg).

Per enhet, til `eiendommer/dybwads gate 8/plantegninger/`:

| Fil | Format | Bruk |
|---|---|---|
| `H0101.svg` | SVG, vektor | Web / boligvelger |
| `H0101.pdf` | A4 stående | Print / salgsoppgave |

## Sideoppbygging (stil B — «Grønn signatur»)

Valgt etter visuell sammenligning av tre retninger (A galleri-lys, B grønn signatur, C editorial premium).

- **Grønn header-blokk** (#1E3D2B): leilighetsnummer i Sfizia, type + etasje i Engravers Gothic (letterspaced caps), arealoppstilling høyrestilt i krem
- **Hovedplan, full detaljering:** vegger, vinduer, dørslag, kjøkkeninnredning, WC/servant/dusj, flisraster på bad, møblering, rombetegnelser med m² — samme detaljnivå som arkitekttegningene, men uten tekniske annotasjoner
- **Egen hems-tegning** ved siden av hovedplanen for alle enheter med hems (separat liten plan, ikke bare stiplet overlay)
- **Målestokk-bar** (0–5 m) og **nordpil** (nord er rotert iht. arkitektens nordpil)
- **Posisjonsdiagrammer:** mini-etasjeplan med enheten markert i grønt + bygningssnitt med etasjen markert
- **Footer:** «Dybwads gate 8» venstre, «Houeland» høyre, Engravers, tynn delelinje over

Farger: krem bakgrunn #FBFAF6, dyp grønn #1E3D2B, beige romfyll, karamell-tone på hems. Brand-regler: god luft rundt logo, ingen skygger/effekter, rolig layout.

## Produksjonspipeline (hybrid)

1. **Underlag:** `pdftocairo -svg` på `Plan_{1,2,3}_etasje.pdf` + `Boenheter_*.pdf` → eksakt vektorgeometri per etasje
2. **Crop per enhet** med låst målestokk — original er 1:100; alle 16 sider får konsistent skala
3. **Ren omtegning:** ny SVG tegnes oppå underlaget. Tekniske annotasjoner (EI60, 54db, sluk-merker, brannmerknader, snittlinjer) tegnes ikke med
4. **QA per enhet:** visuell overlay-diff mot originalunderlaget + kontroll av arealtall mot Boenheter-tegningene
5. **Mal + data:** felles SVG/HTML-mal, per-enhet datafil (nummer, type, etasje, arealer, posisjonsreferanse) genererer alle sider
6. **PDF-eksport:** headless Chrome `printToPDF` med print-CSS. Overflow-sjekk per side (scrollHeight vs clientHeight), kjent fallgruve fra tidligere print-arbeid

## Datakilder

| Data | Kilde |
|---|---|
| BRA per enhet | `Boenheter_*.pdf` rev B (08.05.25) |
| Rom-arealer | `Plan_*_etasje.pdf` rev B |
| Hems-areal | **Ikke oppgitt av arkitekt** — måles fra tegningsgeometri (1:100), merkes «Hems (ikke målbart): ca X m²». Erstattes med eksakte tall hvis takstmann/arkitekt leverer |
| Type (1-roms/2-roms) | Utledes fra romsammensetning per enhet |
| Snitt til posisjonsdiagram | `Snitt_C.pdf` |

BRA-kontrollsummer: 1. etg 127,5 m², 2. etg 126,6 m², 3. etg 134,5 m² (BRA leiligheter per etasje).

Ingen balkonger observert i tegningene → Sum BRA = BRA-i. Verifiseres per enhet under produksjon; avvik flagges.

## Avgrensninger

- Utvendige/innvendige renderings leveres av Torbjørn — ikke del av dette prosjektet
- Boligvelger-nettsiden (interaktiv velger) er eget, senere prosjekt; SVG-ene her er input til den
- Underetasje (`Underetasje.pdf`) inneholder ingen boenheter på enhetslisten — ingen side produseres
- Tegningene er byggesøknadsfase: sidene merkes ikke med forbehold i denne omgang (kan legges til i footer ved behov)

## Brand-ressurser

- Fonter: `brand houeland 2-0/01 Fonter/` (Sfizia-Regular/Bold, Engravers' Gothic)
- Designmanual: `brand houeland 2-0/03 Designmanual/brand-v4-allmøte.pdf`
- Referanse-layout: `eiendommer/dybwads gate 8/public/eksempel-fil-enkel-plantegning` (AVIF)
- Valgt stilmockup: `.superpowers/brainstorm/89975-1780654479/content/plan-stil.html` (variant B)
