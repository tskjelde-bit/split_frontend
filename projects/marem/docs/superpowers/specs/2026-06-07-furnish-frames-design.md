# Furnish-frames: stykkevis møblering for MAREM-hero

2026-06-07. Status: godkjent design, venter på implementasjonsplan.

## Mål

Hero-animasjon der rommet møblerer seg selv, ett møbel/gruppe om gangen, for scene 1 og
scene 2 (natt, 4K). Krav: ingenting kommer-og-går, ingen avtrykk på tomt gulv, ingen
svevende møbler, siste frame identisk med original full-render. Leveranse: QA-verifiserte
frame-sekvenser + preview-video. Frontend-wiring er egen fase etterpå.

## Diagnose av tidligere forsøk (verifisert 2026-06-07)

1. **Fjerne-kjeden** (`scene{1,2}-steps/`): `contain()` i nb_remove.py aksepterte
   modell-piksler i alle endringsklynger uansett posisjon → modellens re-fantasering av
   veggkunst/vinduer ble bakt inn og akkumulerte gjennom kjeden → psykedelisk base.
   Maskegeometrien og gulv/møbel-pikslene er stort sett rene.
2. **build_frames/compose_frames**: limte møbelpiksler fra FULL → fragmenter av senere
   møbler (okklusjon) i tidlige frames.
3. **Rå one-shot-stadier** (`proof/stages-scene{1,2}/`): uankret + følger ikke
   keep-listene eksakt (f1-rug beholdt daybed/lampe; f2 mistet daybed) → kommer-og-går.

Rotårsak felles: ingen geografisk begrensning på aksepterte modell-piksler, ingen
enkelt pikselkilde per objekt.

## Design

Deterministisk lokal komposisjon — null nye API-genereringer i hovedløpet. Nye scripts i
`new-hero/cut/`: `furnish_frames.py` (komposisjon) og `qa_furnish.py` (gates + preview),
drevet av `groups-scene{1,2}.json`.

### Inputs (ligger på disk)

| Rolle | Fil | Bruk |
|---|---|---|
| full | `scene{1,2}-steps/*-00-full.png` | eneste kilde for alt synlig i sluttbildet |
| kjeden | `scene{1,2}-steps/*-NN-*.png` | maske-geometri + okkluderte rekonstruksjoner |
| base | `proof/stages-scene{1,2}/f0-empty.png` | tomt rom med kunst/hyller intakt |

Base ankres mot full: modell-piksler beholdes kun innenfor møbleringsregionen
(union av gruppemasker, dilatert); alt utenfor = fulls piksler. Kunst, vinduer,
gardiner og vegger blir dermed identiske i samtlige frames.

### Byggerekkefølge (hard regel)

**Byggerekkefølge = reversert kjede-rekkefølge. Grupper må bestå av nabosteg i kjeden.**
Gruppe med fjerningssteg {a..b} (sammenhengende): maske = union av diff(a-1,a)..diff(b-1,b),
debut-bilde = steg a-1 (bildet der nøyaktig gruppe 1..i er til stede). Okklusjon mellom
gruppe i og alt tidligere er da bakt inn i debut-bildets piksler — front/bak kan ikke bli feil.

Scene 1 (kjede 00–12), 8 grupper / 9 frames:

| # | Gruppe | Diffsteg | Debut-bilde |
|---|---|---|---|
| 1 | teppe | d12 | 11-uten-sofa |
| 2 | sofa | d11 | 10-uten-skap |
| 3 | skap+vase | d10, d09 | 08-uten-lampe |
| 4 | lampe | d08 | 07-uten-daybed |
| 5 | daybed+pledd | d07, d06 | 05-uten-stol-bak |
| 6 | stoler | d05, d04 | 03-uten-glassbord |
| 7 | bord | d03, d02 | 01-uten-dekor |
| 8 | dekor | d01 | 00-full |

Scene 2 (kjede 00–09), 7 grupper / 8 frames:

| # | Gruppe | Diffsteg | Debut-bilde |
|---|---|---|---|
| 1 | teppe | d09 | 08-uten-venstresofa |
| 2 | venstresofa | d08 | 07-uten-midtsofa |
| 3 | midtsofa | d07 | 06-uten-lamper |
| 4 | lamper | d06 | 05-uten-lenestol-v |
| 5 | lenestoler | d05, d04 | 03-uten-svart-bord |
| 6 | bord | d03, d02 | 01-uten-dekor |
| 7 | dekor | d01 | 00-full |

Småobjekter som forsvant i samme kjedesteg (f.eks. magasin i teppesteget) følger
steggruppen sin.

### Maskederivasjon per gruppe

diff av nabosteg (>30 maks-kanal) → drift-filter: piksler som endrer seg i >2 kjedesteg
(kunst-/vindustøy) nulles (mekanismen fra nb_layers.py) → opening(2)/closing(12) →
dominant komponent + medkomponenter ≥ 8 % av størst (flerobjekt-steg) → fill_holes →
**skygge-halo**: lavterskel-piksler (>12) i sone rundt kjernen inkluderes → generøs
dilation. Maskene lagres binært; feathering (gaussisk) skjer ved komposittering.
Manglende skyggefangst var årsaken til «svevende» møbler — haloen er fiksen.

### Kilderegel og komposisjon

For gruppe i: `mask_i \ union(senere masker)` hentes fra **full** (objektet er øverst
der); `mask_i ∩ union(senere masker)` hentes fra **debut-bildet** (rekonstruksjon av
f.eks. teppe-under-sofa — usynlig i full, overskrives av senere grupper før slutt).
Iterativ paste i byggerekkefølge på ankret base, float32, full 4K-oppløsning.
Siste frame = full verbatim.

### QA-gates (qa_furnish.py, automatisk rapport)

1. **Plassert-forblir-plassert**: etter debut er `mask_i \ union(senere masker)` identisk
   i alle resterende frames (toleranse ~webp-støy). Den presise kommer-og-går-testen.
2. **Lokalitet**: diff mellom nabo-frames ⊆ gruppens dilaterte maske.
3. **Bakgrunnsinvarians**: utenfor maske-unionen er alle frames eksakt identiske.
4. **Sluttkonvergens**: siste komposit vs full — mean-diff liten og ingen klynge >30 over
   0,05 % av flaten (ellers popper full-swappen).
5. **Alignment-vakt**: per gruppe, debut-piksler vs full i uokkludert del — fanger
   objekter modellen har flyttet/endret i kjeden.
6. Per-gruppe montasje (maske-overlay + crop) + crossfade-preview-video (ffmpeg) i
   reelt tempo per scene.

Terskelverdier settes i implementasjonen og dokumenteres i QA-rapporten.

### Feilhåndtering og kirurgisk regenerering

- Dimensjonsavvik / tom maske / gate-brudd → rapport med region og ferdig kommando.
- nb_remove.py utvides med `--accept-region <maske.png>`: containment aksepterer kun
  modell-piksler innenfor oppgitt region (fiksen som hadde forhindret kjede-råten).
  Brukes kun ved QA-brudd, enkeltsteg — aldri ny batch.

### Leveranser

Per scene: fullres-PNG-frames (arbeidsformat), 2048w webp q82-sekvens (eksport),
manifest (rekkefølge, gruppenavn, bbox-er), QA-rapport, preview-video.
Bruker godkjenner video før frontend-fasen.

## Risiko

- Gulvtone-søm i feather-soner (base-rekonstruksjon vs debut-rekonstruksjon): fanges av
  montasje/video, fikses kirurgisk.
- Korrupte objektpiksler i debut-steg (kjede-drift traff møbel): fanges av gate 5.
- Skygge-halo for aggressiv (tar med naboobjekt): fanges av gate 1/2 + montasje.
