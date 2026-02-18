# Typografi — Brand Guide

## Font
- Font: Inter (allerede i bruk)
- Aldri bruk px for font-size — kun **rem** (1rem = 16px)
- Minimum font-size: 0.625rem (10px), og kun for micro-labels

## Type Scale (11 stiler)

| Navn         | Størrelse        | Vekt | Letter-spacing | Case      | Bruk                                          |
|--------------|------------------|------|----------------|-----------|-----------------------------------------------|
| Hero         | 3rem (48px)      | 800  | -1px           | sentence  | Hero-overskrift (Montserrat font)             |
| Display      | 3rem (48px)      | 700  | -0.03em        | sentence  | Kalkulator-resultat (pris)                    |
| H1           | 2.25rem (36px)   | 700  | -0.02em        | sentence  | Kalkulator-tittel, seksjons-overskrifter      |
| Stat         | 2rem (32px)      | 700  | -0.03em        | —         | Stat-tall i kart (+2.4%, 5.8M, 19 dager)     |
| H2           | 1.375rem (22px)  | 700  | -0.01em        | sentence  | Artikkel-titler, seksjons-overskrifter        |
| H3           | 1.0625rem (17px) | 600  | normal         | sentence  | Kort-overskrifter, nyhetsbrev                 |
| Body / CTA   | 1rem (16px)      | 400/700 | normal      | sentence  | Kalkulator-subtittel, CTA-spørsmål            |
| Body small   | 0.9375rem (15px) | 400  | normal         | sentence  | Brødtekst, hero-subtittel                     |
| Nav / Input  | 0.875rem (14px)  | 500  | normal         | title     | Navigasjon, form-input, sub-stat verdier      |
| Meta         | 0.8125rem (13px) | 400  | normal         | sentence  | Metadata, datoer, stat-beskrivelser, CTA-body |
| Label        | 0.6875rem (11px) | 600  | 0.08em         | UPPERCASE | Stat-labels, form-labels, badges, knapper     |
| Micro        | 0.625rem (10px)  | 600  | 0.06em         | UPPERCASE | Sub-stat labels (PRIS/M², TREND) — kun i trange komponenter |

## Font Pairing

### Hero-overskrifter
- Font: **Montserrat**
- Weight: **800** (Extra Bold)
- Letter-spacing: **-1px**
- Bruk: Kun hero-overskrifter på landingssider og hovedseksjoner
- Import: `@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&display=swap');`

### Body og UI
- Font: **Inter** (fortsatt brukes for alt annet)
- Se eksisterende type scale for detaljer

## Regler

### Uppercase
- UPPERCASE **kun** på: labels, badges, knapper, seksjonstitler (korte ord)
- ALDRI uppercase på: overskrifter, artikkel-titler, CTA-setninger, beskrivelser, brødtekst
- Feil: `BOLIGPRISER OSLO 2026-2028: ANALYSE AV FERSKE PROGNOSER`
- Riktig: `Boligpriser Oslo 2026–2028: Analyse av ferske prognoser`

### Font-weight
- Kun 3 vekter for Inter: **400** (body/beskrivelser), **600** (labels/knapper), **700** (overskrifter/verdier)
- Montserrat bruker **800** (Extra Bold) — kun for hero-overskrifter
- Aldri bruk 300, 500 eller 900

### Letter-spacing
- Positiv letter-spacing (0.06–0.1em) **kun** på UPPERCASE-tekst
- Negativ letter-spacing (-0.01 til -0.03em) på store overskrifter (H1, Display, Stat)
- Aldri letter-spacing på body-tekst

### Line-height
- H1/Display: 1.1–1.2 (stramt)
- H2/H3: 1.25–1.3
- Body: 1.6–1.7 (luftig)

### Tekstfarge (3 nivåer)
- **Primær** `text-slate-200` (#e2e8f0): overskrifter, stat-verdier
- **Muted** `text-slate-400` (#94a3b8): brødtekst, beskrivelser
- **Dim** `text-slate-500` (#64748b): labels, metadata, placeholder

### Stat-tall (kart)
- Stat-verdier er alltid 2rem/w700, uansett om det er Oslo-totalt eller valgt bydel
- Fargekode (gul/grønn) brukes i utvidet visning — størrelsen endres aldri
- Labels alltid 0.6875rem/w600/uppercase
- Beskrivelser alltid 0.8125rem/w400

### Kalkulator
- Pris-resultat: 3rem/w700, «kr»-enhet 60% av tallstørrelse med w400
- Form-labels: 0.6875rem (11px) — aldri under dette
- CTA: sentence case, 1rem/w700 — aldri uppercase på setninger
- Badge («BEREGNING KLAR»): 0.6875rem/w600/uppercase — matche label-stilen

## Responsiv (mobil)

Bruk `clamp()` for flytende skalering:

```css
/* Eksempler */
--font-hero: clamp(2rem, 5vw, 3rem);         /* 32px → 48px (Montserrat 800) */
--font-stat: clamp(1.5rem, 3vw, 2rem);       /* 24px → 32px */
--font-display: clamp(2.25rem, 5vw, 3rem);    /* 36px → 48px */
--font-h1: clamp(1.75rem, 4vw, 2.25rem);      /* 28px → 36px */
```

| Element           | Desktop          | Mobil            | Font          |
|-------------------|------------------|------------------|---------------|
| Hero-overskrift   | 3rem (48px)      | 2rem (32px)      | Montserrat 800|
| Stat-verdi        | 2rem (32px)      | 1.5rem (24px)    | Inter 700     |
| Stat-label        | 0.6875rem (11px) | 0.625rem (10px)  | Inter 600     |
| Stat-beskrivelse  | 0.8125rem (13px) | 0.75rem (12px)   | Inter 400     |
| Kalkulator-tittel | 2.25rem (36px)   | 1.75rem (28px)   | Inter 700     |
| Pris (resultat)   | 3rem (48px)      | 2.25rem (36px)   | Inter 700     |

**Aldri forkort tekst for å spare plass** («19 D» i stedet for «19 dager»). Skalér størrelsen ned i stedet.
