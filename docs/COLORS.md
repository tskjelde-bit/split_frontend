# Farger — Brand Guide

## Prinsipp
- Alle farger via CSS custom properties (`--variabel-navn`)
- Aldri hardkodede farger i komponenter
- Light mode er default (`:root`), dark mode via `.dark`-klasse på `<html>`
- Respekter `prefers-color-scheme` for automatisk valg

## Bakgrunner (4 nivåer)

| Navn     | CSS-variabel     | Dark        | Light       | Brukes på                                                     |
|----------|------------------|-------------|-------------|---------------------------------------------------------------|
| Base     | `--bg-base`      | `#0a0f1d`   | `#ffffff`   | Body / hele sidens bakgrunn                                   |
| Surface  | `--bg-surface`   | `#0f172a`   | `#f8fafc`   | Sidebar, nav, kalkulator-form, stat-kort, artikkel-kort       |
| Elevated | `--bg-elevated`  | `#1e293b`   | `#f1f5f9`   | Inaktive knapper, segment-controls, form-inputs, kart-container |
| Overlay  | `--bg-overlay`   | `#334155`   | `#e2e8f0`   | Aktive segment-knapper, tooltip, dropdown-hover               |

**Ingen andre bakgrunnsfarger.** Fjern alle rgba-overlays, semi-transparente bakgrunner og vilkårlige hex-verdier.

## Tekst (3 nivåer)

| Navn    | CSS-variabel      | Dark        | Light       | Brukes på                                  |
|---------|--------------------|-------------|-------------|--------------------------------------------|
| Primær  | `--text-primary`   | `#f1f5f9`   | `#0f172a`   | Overskrifter, stat-verdier, pris-tall      |
| Muted   | `--text-muted`     | `#94a3b8`   | `#475569`   | Brødtekst, beskrivelser, nav-links         |
| Dim     | `--text-dim`       | `#64748b`   | `#94a3b8`   | Labels, metadata, placeholder, form-labels |

## Aksent & Interaksjon

| Navn          | CSS-variabel      | Dark                          | Light                         |
|---------------|--------------------|-------------------------------|-------------------------------|
| Primær aksent | `--accent`         | `#3b82f6`                     | `#2563eb`                     |
| Aksent hover  | `--accent-hover`   | `#2563eb`                     | `#1d4ed8`                     |
| Aksent subtle | `--accent-subtle`  | `rgba(59, 130, 246, 0.12)`    | `rgba(37, 99, 235, 0.08)`    |

## Semantiske farger

| Navn     | CSS-variabel        | Dark        | Light       | Betydning                            |
|----------|----------------------|-------------|-------------|--------------------------------------|
| Positiv  | `--color-positive`   | `#22c55e`   | `#16a34a`   | Over snitt, sterkere vekst, kortere salgstid |
| Varsel   | `--color-warning`    | `#facc15`   | `#ca8a04`   | Under snitt, svakere vekst, lengre salgstid  |
| Negativ  | `--color-negative`   | `#ef4444`   | `#dc2626`   | Feilmeldinger (ALDRI for stat-verdier)       |
| Nøytral  | `--color-neutral`    | `#94a3b8`   | `#64748b`   | Omtrent lik Oslo-snittet                     |

## Borders (2 nivåer)

| Navn    | CSS-variabel       | Dark                          | Light                       |
|---------|--------------------|-------------------------------|-----------------------------|
| Subtle  | `--border-subtle`  | `rgba(255, 255, 255, 0.06)`   | `rgba(0, 0, 0, 0.06)`      |
| Default | `--border-default` | `rgba(255, 255, 255, 0.12)`   | `rgba(0, 0, 0, 0.12)`      |

**Ingen andre border-farger.** Fjern alle #e2e8f0, #e5e7eb, rgba 0.05/0.1/0.2 varianter.

## Regler

### Bakgrunn
- Sidebar og hovedområde skal ha **samme** base-farge — ikke to forskjellige mørke nyanser
- Stat-kort bruker `--bg-surface`, ikke rgba-overlays
- Kalkulator-form: `--bg-surface`. Resultat-panel: `--bg-surface`. Sub-stat kort: `--bg-elevated`

### Kart
- Dark mode: bruk mørke kart-tiles (CartoDB Dark Matter: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`)
- Light mode: behold lyse tiles
- Bytt tiles dynamisk basert på brukerens tema-valg
- Legg til `border-radius: 12px` og `border: 1px solid var(--border-default)` rundt kart-containeren

### CTA-knapper
- **Primær CTA** (verdivurdering = hovedkonvertering): `--color-positive` (grønn) bakgrunn, hvit tekst
- **Sekundær CTA** (beregn verdi, se alle, les mer): `--accent` (blå) bakgrunn, hvit tekst
- Aldri blande — grønn er alltid primær, blå er alltid sekundær

### Stat-verdier (fargekode)
- Over snitt: `--color-positive` (grønn)
- Under snitt: `--color-warning` (gul)
- På snitt (± liten margin): `--color-neutral` (grå)
- Default (ingen bydel valgt): `--text-primary` (hvit/mørk)
- ALDRI bruk `--color-negative` (rød) for stat-verdier

### Badge (MARKEDSINNSIKT)
- Bakgrunn: `--accent-subtle`
- Tekst: `--accent`

### Theme toggle
- Lagre valg i `localStorage`
- Respekter `prefers-color-scheme` som default
- Toggle legger til/fjerner `.dark` på `<html>`

## CSS-variabler (kopier inn)

```css
:root {
  --bg-base: #ffffff;
  --bg-surface: #f8fafc;
  --bg-elevated: #f1f5f9;
  --bg-overlay: #e2e8f0;
  --text-primary: #0f172a;
  --text-muted: #475569;
  --text-dim: #94a3b8;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-subtle: rgba(37, 99, 235, 0.08);
  --color-positive: #16a34a;
  --color-warning: #ca8a04;
  --color-negative: #dc2626;
  --color-neutral: #64748b;
  --border-subtle: rgba(0, 0, 0, 0.06);
  --border-default: rgba(0, 0, 0, 0.12);
}

.dark {
  --bg-base: #0a0f1d;
  --bg-surface: #0f172a;
  --bg-elevated: #1e293b;
  --bg-overlay: #334155;
  --text-primary: #f1f5f9;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --accent-subtle: rgba(59, 130, 246, 0.12);
  --color-positive: #22c55e;
  --color-warning: #facc15;
  --color-negative: #ef4444;
  --color-neutral: #94a3b8;
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.12);
}
```

## Komponent → farge-mapping

| Komponent               | Bakgrunn                  | Tekst                                          | Border              |
|-------------------------|---------------------------|-------------------------------------------------|---------------------|
| Body                    | `--bg-base`               | —                                               | —                   |
| Navbar                  | `--bg-base`               | `--text-muted` (links), `--accent` (aktiv)      | `--border-subtle`   |
| Hero-seksjon            | `--bg-surface`            | `--text-primary` (H1), `--text-muted` (sub)     | —                   |
| Kart-container          | `--bg-elevated`           | —                                               | `--border-default`  |
| Stat-kort (default)     | `--bg-base`               | `--text-primary` (tall), `--text-dim` (labels)  | —                   |
| Stat-kort (utvidet)     | `--bg-surface`            | Semantisk farge (tall), `--text-dim` (labels)   | `--border-subtle`   |
| CTA-bar                 | `--accent`                | `#ffffff`                                       | —                   |
| Sidebar                 | `--bg-surface`            | `--text-primary` (titler), `--text-dim` (meta)  | `--border-subtle`   |
| Artikkel-kort           | `--bg-surface`            | `--text-primary`                                | `--border-subtle`   |
| Badge                   | `--accent-subtle`         | `--accent`                                      | —                   |
| Kalkulator-form         | `--bg-surface`            | `--text-dim` (labels), `--accent` (input)       | `--border-default`  |
| Kalkulator-resultat     | `--bg-surface`            | `--text-primary` (pris), `--text-dim` (labels)  | `--border-default`  |
| Sub-stat (PRIS/M²)      | `--bg-elevated`           | `--text-dim` (label), `--text-primary` (verdi)  | `--border-subtle`   |
| CTA primær              | `--color-positive`        | `#ffffff`                                       | —                   |
| CTA sekundær            | `--accent`                | `#ffffff`                                       | —                   |
| Segment-knapper         | `--bg-elevated`/`overlay` | `--text-dim` / `--text-primary`                 | `--border-subtle`   |
| Nyhetsbrev-input        | `--bg-elevated`           | `--text-dim` (placeholder)                      | `--border-default`  |
| Kart-zoom knapper       | `--bg-surface`            | `--text-muted`                                  | `--border-default`  |
