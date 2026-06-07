#!/usr/bin/env python3
"""Bygg furnish-frames for én scene fra groups-JSON.

Bruk: furnish_frames.py <groups-sceneN.json>
Output i cfg["out_dir"]: f00..fNN.png (fullres), f00..fNN.webp (2048w),
comp-final.png (siste komposit FØR full-swap, til gate 4), masks.npz, manifest.json.
Siste frame = full verbatim.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import furnishlib as fl

EXPORT_W = 2048
WEBP_Q = 82


def validate(cfg: dict, n_steps: int) -> None:
    used = []
    for g in cfg["groups"]:
        ds = sorted(g["diff_steps"], reverse=True)
        assert ds == list(range(ds[0], ds[-1] - 1, -1)), \
            f"{g['name']}: diff_steps må være sammenhengende kjedesteg"
        used += ds
    assert sorted(used) == list(range(1, n_steps)), \
        f"alle kjedesteg 1..{n_steps - 1} må brukes nøyaktig én gang (fikk {sorted(used)})"
    order = sorted(cfg["groups"], key=lambda g: -max(g["diff_steps"]))
    assert [g["name"] for g in order] == [g["name"] for g in cfg["groups"]], \
        "grupper må stå i reversert kjede-rekkefølge (okklusjonsgarantien)"


def main() -> None:
    here = Path(__file__).resolve().parent
    cfg = json.loads(Path(sys.argv[1]).read_text())
    scene = cfg["scene"]
    out_dir = here / cfg["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    files = fl.chain_files(here / cfg["steps_dir"], scene)
    keys = sorted(files)
    assert keys == list(range(len(keys))), f"hull i kjeden: {keys}"
    validate(cfg, len(keys))

    print(f"{scene}: laster {len(keys)} kjedesteg ...")
    arrs = {k: fl.load_rgb(files[k]) for k in keys}
    full = arrs[0]
    H, W = full.shape[:2]

    noise = fl.drift_mask([arrs[k] for k in keys])
    print(f"  drift-maske: {noise.mean() * 100:.1f}%")

    masks, debuts = [], []
    for g in cfg["groups"]:
        m = fl.group_mask(arrs, g["diff_steps"], noise)
        assert m.any(), f"{g['name']}: tom maske — sjekk diff_steps"
        debut_step = min(g["diff_steps"]) - 1
        masks.append(m)
        debuts.append(arrs[debut_step])
        print(f"  {g['name']}: maske {m.mean() * 100:.1f}%, debut=steg {debut_step:02d}")

    furniture = np.zeros((H, W), bool)
    for m in masks:
        furniture |= m

    empty = fl.load_rgb(here / cfg["base_empty"])
    if empty.shape != full.shape:
        assert abs(empty.shape[1] / empty.shape[0] - W / H) < 0.01, \
            f"base har feil aspekt: {empty.shape} vs {full.shape}"
        print(f"  base resamples {empty.shape[1]}x{empty.shape[0]} -> {W}x{H}")
        empty = np.asarray(Image.fromarray(empty).resize((W, H), Image.LANCZOS))
    base = fl.anchor_base(empty, full, furniture)

    frames = fl.composite(base, full, list(zip(masks, debuts)))
    comp_final = frames[-1]
    frames[-1] = full  # siste frame = full verbatim; gate 4 måler comp_final vs full

    Image.fromarray(comp_final).save(out_dir / "comp-final.png")
    np.savez_compressed(out_dir / "masks.npz", noise=noise, furniture=furniture,
                        **{f"mask_{i:02d}": m for i, m in enumerate(masks)})

    scale = EXPORT_W / W
    eh = round(H * scale)
    manifest = {"scene": scene, "groups": [g["name"] for g in cfg["groups"]],
                "frames": [], "bboxes": []}
    total = 0
    for i, fr in enumerate(frames):
        im = Image.fromarray(fr)
        im.save(out_dir / f"f{i:02d}.png")
        wp = out_dir / f"f{i:02d}.webp"
        im.resize((EXPORT_W, eh), Image.LANCZOS).save(
            wp, "WEBP", quality=WEBP_Q, method=6)
        total += wp.stat().st_size
        manifest["frames"].append(wp.name)
    for g, m in zip(cfg["groups"], masks):
        ys, xs = np.nonzero(m)
        manifest["bboxes"].append({
            "group": g["name"],
            "left": round(float(xs.min()) / W * 100, 2),
            "top": round(float(ys.min()) / H * 100, 2),
            "width": round(float(xs.max() - xs.min()) / W * 100, 2),
            "height": round(float(ys.max() - ys.min()) / H * 100, 2)})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{scene}: {len(frames)} frames -> {out_dir} (webp totalt {total // 1024} KB)")


if __name__ == "__main__":
    main()
