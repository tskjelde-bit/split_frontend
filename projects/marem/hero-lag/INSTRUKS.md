# Hero-lag: produksjon av assets

Input: `00-master.png` (3528×2344, full-res frame fra hero-videoen).

Bruk GPT Image (ChatGPT → last opp 00-master.png → be om edit). Én jobb per
asset. **Kritisk for alle:** samme canvas-størrelse og aspect ratio som
originalen, ingenting flyttes eller skaleres. Lag-PNG-ene skal være
full-canvas med transparens rundt objektet — da ligger alt riktig automatisk.

Lagre filene i denne mappa med navnene under.

---

## 01-bakgrunn.png (tomt rom)

> Remove ALL furniture and objects from this living room: the sofa with
> pillows, the marble coffee table with flowers and books, both floor lamps,
> both small side tables, the armchair on the right, the blue artwork on the
> left wall, and the chandelier. Keep ONLY the empty room: walls, ceiling,
> windows, curtains, and the herringbone parquet floor — all unchanged in
> position, lighting and color. Fill the removed areas naturally and
> photorealistically. Do not move the camera. Same resolution and aspect
> ratio as the input.

(Vanlig PNG/JPG uten transparens.)

## 02-lysekrone.png

> From this image, isolate ONLY the chandelier hanging from the ceiling.
> Output a PNG with fully transparent background at the exact same canvas
> size and aspect ratio as the input, with the chandelier in its exact
> original position and scale. Everything else must be fully transparent.

## 03-kunst.png

> Same task: isolate ONLY the blue artwork hanging on the left wall,
> in its exact original position. Transparent everywhere else. Same canvas.

## 04-lampe-venstre.png

> Same task: isolate ONLY the left floor lamp AND the small round side table
> beneath/next to it, with their soft floor shadows. Exact original
> position. Transparent everywhere else. Same canvas.

## 05-lampe-hoyre.png

> Same task: isolate ONLY the right floor lamp AND the small side table next
> to it, with their soft floor shadows. Exact original position. Transparent
> everywhere else. Same canvas.

## 06-lenestol.png

> Same task: isolate ONLY the armchair at the right edge of the image, with
> its soft floor shadow. Exact original position. Transparent everywhere
> else. Same canvas.

## 07-sofa.png

> Same task: isolate ONLY the sofa with all its pillows, including its legs
> and soft floor shadow. Exact original position. Transparent everywhere
> else. Same canvas.

## 08-bord.png

> Same task: isolate ONLY the marble coffee table with the flower vase,
> books and objects on it, including its soft floor shadow. Exact original
> position. Transparent everywhere else. Same canvas.

---

## Kvalitetssjekk per fil

- Riktig canvas (3:2, helst 3528×2344 — minst 1920 bred)
- Objektet står NØYAKTIG der det står i 00-master.png
- Myk gulvskygge er MED i laget (ikke i bakgrunnen)
- Ingen rester av andre objekter

Når alle 8 ligger her: si fra, så kobler jeg dem inn, finjusterer
posisjoner og deployer.
