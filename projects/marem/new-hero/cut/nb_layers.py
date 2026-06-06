#!/usr/bin/env python3
"""Bygg alfa-lag fra en stegvis fjerningsserie (nb_remove-kjeden).

Lag k = det som ble fjernet i steg k = diff(steg k-1, steg k), med piksler
fra steg k-1 (bildet MED objektet) og feathered alfa. Croppes til bbox og
eksporteres som webp (skalert til EXPORT_W-bredde) + manifest.json med
posisjon/størrelse i prosent av full flate.

Bruk:
    nb_layers.py <steps-dir> <out-dir> <scene-navn>
Stegfiler må hete <scene>-NN-*.png (NN stigende, 00 = full, siste = base).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

EXPORT_W = 2560
QUALITY = 88
THRESH = 30


def step_files(d: Path, scene: str) -> list[Path]:
    pat = re.compile(rf"^{re.escape(scene)}-(\d+)-[^.]+\.png$")
    files = [(int(m.group(1)), p) for p in d.iterdir() if (m := pat.match(p.name))]
    return [p for _, p in sorted(files)]


def change_mask(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    core = d > THRESH
    core = ndimage.binary_opening(core, iterations=2)
    core = ndimage.binary_closing(core, iterations=12)
    labels, n = ndimage.label(core)
    keep = np.zeros_like(core)
    if n:
        sizes = ndimage.sum(core, labels, range(1, n + 1))
        min_size = a.shape[0] * a.shape[1] * 5e-5
        for i, sl in enumerate(ndimage.find_objects(labels)):
            if sizes[i] < min_size or sl is None:
                continue
            comp = labels[sl] == i + 1
            # generøs maske er trygg i LAG (ekstra piksler er identiske med
            # underliggende tilstand) — bbox-fyll store klynger så
            # lavkontrast-hull (teppe/sofa) aldri gir gjennomsiktige flekker
            if comp.shape[0] * comp.shape[1] > a.shape[0] * a.shape[1] * 0.05:
                keep[sl] = True
            else:
                keep[sl] |= comp
    return ndimage.binary_fill_holes(keep)


def main() -> None:
    steps_dir, out_dir, scene = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    files = step_files(steps_dir, scene)
    assert len(files) >= 2, "trenger minst 2 steg"
    print(f"{scene}: {len(files)} steg → {len(files) - 1} lag")

    W = H = None
    manifest = {"scene": scene, "base": f"{scene}-base.webp", "layers": []}

    # base = siste steg (tomt rom)
    base = Image.open(files[-1]).convert("RGB")
    W, H = base.size
    scale = EXPORT_W / W
    base.resize((EXPORT_W, round(H * scale)), Image.LANCZOS).save(
        out_dir / manifest["base"], "WEBP", quality=QUALITY
    )

    # lag i byggerekkefølge: siste fjernet = først inn (bakerst i stabelen)
    for k in range(len(files) - 1, 0, -1):
        with_obj = np.asarray(Image.open(files[k - 1]).convert("RGB"))
        without = np.asarray(Image.open(files[k]).convert("RGB"))
        mask = change_mask(with_obj, without)
        if not mask.any():
            print(f"  steg {k}: tom diff — hopper over")
            continue
        # feathered alfa
        alpha = ndimage.binary_dilation(mask, iterations=6).astype(np.float32)
        alpha = ndimage.gaussian_filter(alpha, sigma=4)
        alpha = np.clip(alpha, 0, 1)
        ys, xs = np.nonzero(alpha > 0.01)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgba = np.dstack(
            [with_obj[y0:y1, x0:x1], (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)]
        )
        # navn fra fila objektet forsvant i (steg k): <scene>-NN-<navn>.png
        layer_name = files[k - 1].stem.split("-", 2)[-1] if k > 1 else "topp"
        tag = f"{scene}-lag{len(files) - 1 - k + 1:02d}-{files[k].stem.split('-', 2)[-1]}"
        im = Image.fromarray(rgba)
        im = im.resize(
            (round(im.width * scale), round(im.height * scale)), Image.LANCZOS
        )
        im.save(out_dir / f"{tag}.webp", "WEBP", quality=QUALITY)
        manifest["layers"].append(
            {
                "file": f"{tag}.webp",
                # posisjon/størrelse i % av full flate — uavhengig av visning
                "left": round(x0 / W * 100, 3),
                "top": round(y0 / H * 100, 3),
                "width": round((x1 - x0) / W * 100, 3),
                "height": round((y1 - y0) / H * 100, 3),
            }
        )
        print(f"  lag {tag}: bbox {x1-x0}x{y1-y0} px")

    (out_dir / f"{scene}-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(f"manifest: {out_dir}/{scene}-manifest.json")


if __name__ == "__main__":
    main()
