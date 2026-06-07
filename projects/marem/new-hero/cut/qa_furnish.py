#!/usr/bin/env python3
"""QA-gates for furnish-frames (spec 2026-06-07).

Bruk: qa_furnish.py <out-dir> <groups-sceneN.json>
Gates:
  1 plassert-forblir-plassert  2 lokalitet  3 bakgrunnsinvarians
  4 sluttkonvergens (comp-final vs full)  5 alignment (debut vs full)
Skriver qa-report.txt + qa-group-NN-<navn>.jpg-montasjer. Exit 1 ved FAIL.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import furnishlib as fl

Image.MAX_IMAGE_PIXELS = None


def dil_fast(m: np.ndarray, r: int) -> np.ndarray:
    """Rask dilation med radius r via distansetransform."""
    if not m.any():
        return m.copy()
    return ndimage.distance_transform_edt(~m) <= r


def later_unions(masks: list) -> tuple[list, np.ndarray]:
    acc = np.zeros(masks[0].shape, bool)
    out = [None] * len(masks)
    for i in range(len(masks) - 1, -1, -1):
        out[i] = acc.copy()
        acc |= masks[i]
    return out, acc


def gate1(seq: list, masks: list, names: list) -> list:
    """Etter debut skal gruppens uokkluderte region være BIT-identisk i alle
    senere komposit. Den presise kommer-og-går-testen."""
    later, _ = later_unions(masks)
    res = []
    for i, m in enumerate(masks):
        region = m & ~dil_fast(later[i], fl.QA_PAD)
        if not region.any():
            res.append({"group": names[i], "worst": 0, "note": "helt okkludert"})
            continue
        ref = np.asarray(seq[i + 1], np.int16)
        worst = 0
        for k in range(i + 2, len(seq)):
            d = np.abs(np.asarray(seq[k], np.int16) - ref).max(2)
            worst = max(worst, int(d[region].max()))
        res.append({"group": names[i], "worst": worst})
    return res


def main() -> None:
    out_dir = Path(sys.argv[1])
    cfg = json.loads(Path(sys.argv[2]).read_text())
    here = Path(__file__).resolve().parent
    man = json.loads((out_dir / "manifest.json").read_text())
    names = man["groups"]
    n = len(names)
    frames = [np.asarray(Image.open(out_dir / f"f{i:02d}.png").convert("RGB"))
              for i in range(n + 1)]
    comp_final = np.asarray(Image.open(out_dir / "comp-final.png").convert("RGB"))
    z = np.load(out_dir / "masks.npz")
    masks = [z[f"mask_{i:02d}"] > 0 for i in range(n)]
    full = frames[-1]
    H, W = full.shape[:2]
    seq = frames[:-1] + [comp_final]   # rene komposit (uten full-swappen)
    later, union = later_unions(masks)
    rep, fails = [], []

    for r in gate1(seq, masks, names):
        ok = r["worst"] == 0
        note = f", {r['note']}" if r.get("note") else ""
        rep.append(f"gate1 {r['group']}: {'OK' if ok else 'FAIL'} (maks {r['worst']}{note})")
        if not ok:
            fails.append(f"gate1:{r['group']}")

    for k in range(1, len(seq)):
        d = np.abs(np.asarray(seq[k], np.int16)
                   - np.asarray(seq[k - 1], np.int16)).max(2) > 8
        frac = float((d & ~dil_fast(masks[k - 1], fl.QA_PAD)).mean())
        ok = frac < 1e-5
        rep.append(f"gate2 {names[k - 1]}: {'OK' if ok else 'FAIL'} (utenfor-andel {frac:.2e})")
        if not ok:
            fails.append(f"gate2:{names[k - 1]}")

    bg = ~dil_fast(union, 48)
    worst = 0
    for k in range(1, n + 1):
        d = np.abs(frames[k].astype(np.int16) - frames[0].astype(np.int16)).max(2)
        worst = max(worst, int(d[bg].max()))
    ok = worst == 0
    rep.append(f"gate3 bakgrunn: {'OK' if ok else 'FAIL'} (maks {worst})")
    if not ok:
        fails.append("gate3")

    d = np.abs(comp_final.astype(np.int16) - full.astype(np.int16)).max(2)
    lab, nn = ndimage.label(d > 30)
    maxcl = float(ndimage.sum(d > 30, lab, range(1, nn + 1)).max() / (H * W)) if nn else 0.0
    ok = d.mean() < 3.0 and maxcl < 5e-4
    rep.append(f"gate4 slutt-vs-full: {'OK' if ok else 'FAIL'} "
               f"(mean {d.mean():.2f}, største klynge {maxcl * 100:.3f}%)")
    if not ok:
        fails.append("gate4")

    steps = fl.chain_files(here / cfg["steps_dir"], cfg["scene"])
    for i, g in enumerate(cfg["groups"]):
        if "debut_override" in g:
            debut = fl.load_rgb(here / g["debut_override"])
            if debut.shape != full.shape:
                debut = np.asarray(Image.fromarray(debut).resize((W, H), Image.LANCZOS))
        else:
            debut = fl.load_rgb(steps[min(g["diff_steps"]) - 1])
        U = masks[i] & ~later[i]
        if U.any():
            m = float(np.abs(debut.astype(np.int16)
                             - full.astype(np.int16)).max(2)[U].mean())
            status = "OK" if m < 6 else ("WARN" if m < 12 else "FAIL")
            rep.append(f"gate5 {names[i]}: {status} (mean {m:.2f})")
            if status == "FAIL":
                fails.append(f"gate5:{names[i]}")
        else:
            rep.append(f"gate5 {names[i]}: (helt okkludert)")
        ys, xs = np.nonzero(masks[i])
        my = (ys.max() - ys.min()) // 10 + 1
        mx = (xs.max() - xs.min()) // 10 + 1
        y0, y1 = max(ys.min() - my, 0), min(ys.max() + my, H)
        x0, x1 = max(xs.min() - mx, 0), min(xs.max() + mx, W)
        ov = debut[y0:y1, x0:x1].copy()
        sel = masks[i][y0:y1, x0:x1]
        ov[sel] = (ov[sel] * 0.55 + np.array([255, 40, 40]) * 0.45).astype(np.uint8)
        strip = np.concatenate([full[y0:y1, x0:x1], debut[y0:y1, x0:x1], ov], axis=1)
        im = Image.fromarray(strip)
        im.thumbnail((2400, 520))
        im.save(out_dir / f"qa-group-{i:02d}-{names[i]}.jpg", quality=85)

    txt = "\n".join(rep) + ("\n\nFAILS: " + ", ".join(fails) if fails
                            else "\n\nALLE GATES OK")
    (out_dir / "qa-report.txt").write_text(txt + "\n")
    print(txt)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
