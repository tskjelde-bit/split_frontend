#!/usr/bin/env python3
"""Kjernebibliotek for furnish-frames: stykkevis møblering fra fjerne-kjeden.

All komposisjon er deterministisk og lokal (numpy/PIL/scipy) — ingen API-kall.
Design: docs/superpowers/specs/2026-06-07-furnish-frames-design.md
"""
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

THRESH = 30        # kjerneterskel for reell endring (maks-kanal)
SHADOW_LO = 12     # lavterskel for skygge-halo
SHADOW_REACH = 25  # halo-sone rundt kjernen (dilation-iterasjoner)
MASK_DILATE = 10   # generøs utvidelse av ferdig gruppemaske
FEATHER_DILATE = 6
FEATHER_SIGMA = 4.0
QA_PAD = 24        # QA-margin for å holde seg klar av feather-soner
RESIDUAL_REMOVAL_MIN = 45  # ekte fjerning (objekt->bakgrunn) vs render-varians (~37)

Image.MAX_IMAGE_PIXELS = None


def chain_files(steps_dir: Path, scene: str) -> dict[int, Path]:
    """Kjedesteg {NN: path}. Hopper over .diff.png/.raw.png."""
    pat = re.compile(rf"^{re.escape(scene)}-(\d+)-[^.]+\.png$")
    out = {}
    for p in Path(steps_dir).iterdir():
        if (m := pat.match(p.name)):
            out[int(m.group(1))] = p
    return out


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def raw_change(a: np.ndarray, b: np.ndarray, thresh: int = THRESH) -> np.ndarray:
    return np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2) > thresh


def drift_mask(arrs: list) -> np.ndarray:
    """Piksler som endrer seg i >2 kjedesteg = kunst-/vindustøy, ikke objekter."""
    freq = np.zeros(arrs[0].shape[:2], dtype=np.int16)
    for k in range(1, len(arrs)):
        freq += raw_change(arrs[k - 1], arrs[k]).astype(np.int16)
    return ndimage.binary_dilation(freq > 2, iterations=3)


def step_core(a: np.ndarray, b: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """Kjernemaske for ett kjedesteg: dominant komponent + store medkomponenter."""
    H, W = a.shape[:2]
    core = raw_change(a, b) & ~noise
    core = ndimage.binary_opening(core, iterations=2)
    core = ndimage.binary_closing(core, iterations=12)
    labels, n = ndimage.label(core)
    keep = np.zeros_like(core)
    if not n:
        return keep
    sizes = ndimage.sum(core, labels, range(1, n + 1))
    min_size = max(H * W * 1.2e-4, sizes.max() * 0.08)
    for i, sl in enumerate(ndimage.find_objects(labels)):
        if sizes[i] < min_size or sl is None:
            continue
        keep[sl] |= labels[sl] == i + 1
    return ndimage.binary_fill_holes(keep)


def add_shadow_halo(keep: np.ndarray, a: np.ndarray, b: np.ndarray,
                    noise: np.ndarray) -> np.ndarray:
    """Ta med myke skygger: lavterskel-endring i sonen rundt kjernen.

    Manglende skyggefangst ga «svevende» møbler — dette er fiksen.
    """
    if not keep.any():
        return keep
    soft = raw_change(a, b, SHADOW_LO) & ~noise
    near = ndimage.binary_dilation(keep, iterations=SHADOW_REACH)
    out = keep | (soft & near)
    out = ndimage.binary_closing(out, iterations=6)
    return ndimage.binary_fill_holes(out)


def group_mask(arrs_by_step: dict, diff_steps: list, noise: np.ndarray) -> np.ndarray:
    """Binær maske for én byggegruppe = union av stegmasker + halo + dilation.

    diff_steps: kjedesteg-numre; maske for steg s = diff(arrs[s-1], arrs[s]).
    """
    m = None
    for s in diff_steps:
        core = step_core(arrs_by_step[s - 1], arrs_by_step[s], noise)
        core = add_shadow_halo(core, arrs_by_step[s - 1], arrs_by_step[s], noise)
        m = core if m is None else (m | core)
    return ndimage.binary_dilation(m, iterations=MASK_DILATE)


def feather(mask: np.ndarray, dilate: int = FEATHER_DILATE,
            sigma: float = FEATHER_SIGMA) -> np.ndarray:
    """Binær maske → myk alfa. Gaussisk støtte er endelig (truncate=4σ),
    så piksler lenger unna enn dilate + 4σ er eksakt 0 — det er forutsetningen
    for QA_PAD-marginene i qa_furnish."""
    a = ndimage.binary_dilation(mask, iterations=dilate).astype(np.float32)
    return np.clip(ndimage.gaussian_filter(a, sigma), 0.0, 1.0)


def anchor_base(empty: np.ndarray, full: np.ndarray,
                furniture: np.ndarray) -> np.ndarray:
    """Base = empty-rekonstruksjon kun i møbleringsregionen, fulls piksler ellers.

    Kunst/vinduer/gardiner blir dermed identiske med full i samtlige frames.
    Innflytelsesradius = 15 + 4*8 = 47 px; gate 3 bruker 48 px margin.
    """
    a = feather(furniture, dilate=15, sigma=8.0)[..., None]
    out = empty.astype(np.float32) * a + full.astype(np.float32) * (1 - a)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def residual_holes(full: np.ndarray, empty: np.ndarray, union: np.ndarray,
                   min_frac: float = 2e-5) -> list:
    """Møbelpiksler i full som gruppemaskene ikke dekker.

    Kjede-drift kan ha «spist» objektdeler ut av maskene (puter/skap som
    vibrerte i mange steg havner i drift-masken). Da lekker fulls piksler
    inn i basen som frittsvevende fragmenter. Denne finner dem: klynger i
    diff(full, tomt rom) utenfor maske-unionen.
    """
    H, W = full.shape[:2]
    holes = raw_change(full, empty) & ~union
    holes = ndimage.binary_opening(holes, iterations=2)
    holes = ndimage.binary_closing(holes, iterations=8)
    holes = ndimage.binary_fill_holes(holes)
    labels, n = ndimage.label(holes)
    comps = []
    if not n:
        return comps
    for i, sl in enumerate(ndimage.find_objects(labels)):
        if sl is None:
            continue
        comp = np.zeros((H, W), bool)
        comp[sl] = labels[sl] == i + 1
        if comp.sum() >= H * W * min_frac:
            comps.append(comp)
    return comps


def residual_metrics(comp: np.ndarray, arrs_by_step: dict, union: np.ndarray,
                     prox: int = 50) -> tuple[bool, float]:
    """Skill ekte drift-spiste fragmenter fra render-varians (kunst/gardiner).

    Ekte fragment: nær eksisterende maske OG har et fjerningssteg i kjeden
    (stor én-stegs endring, objekt → bakgrunn). Varians: langt unna masker
    eller bare svak vibrasjon. Returnerer (nær_union, største stegmiddel).
    """
    ys, xs = np.nonzero(comp)
    H, W = comp.shape
    y0, y1 = max(ys.min() - prox, 0), min(ys.max() + prox + 1, H)
    x0, x1 = max(xs.min() - prox, 0), min(xs.max() + prox + 1, W)
    sl = (slice(y0, y1), slice(x0, x1))
    near = bool((ndimage.binary_dilation(comp[sl], iterations=prox) & union[sl]).any())
    sub = comp[sl]
    best = 0.0
    for s in sorted(arrs_by_step)[1:]:
        a = arrs_by_step[s - 1][sl].astype(np.int16)
        b = arrs_by_step[s][sl].astype(np.int16)
        best = max(best, float(np.abs(a - b).max(axis=2)[sub].mean()))
    return near, best


def split_residual(comp: np.ndarray, masks: list, build_margin: int = 30,
                   min_px: int = 200) -> list:
    """Per-piksel tilordning av residual til NÆRMESTE gruppemaske.

    Kjede-magnitude er upålitelig i korrupte regioner (psykedelisk drift
    slår fjerningssignalet). Nærhet er robust: puter ligger inntil sofa-
    masken, stolrygg inntil stolmasken. Ved (nesten) likt nær flere masker
    velges SENESTE gruppe i byggerekkefølgen — innhold som dukker opp
    sammen med/etter støtten sin er trygt, før er det artefakt.
    Returnerer [(gruppeindeks, delmaske), ...].
    """
    ys, xs = np.nonzero(comp)
    H, W = comp.shape
    pad = 400
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, H)
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, W)
    sl = (slice(y0, y1), slice(x0, x1))
    sub = comp[sl]
    dists = []
    for m in masks:
        msub = m[sl]
        if msub.any():
            dists.append(ndimage.distance_transform_edt(~msub).astype(np.float32))
        else:
            dists.append(np.full(sub.shape, np.inf, np.float32))
    D = np.stack(dists)
    dmin = D.min(axis=0)
    owner = np.full(sub.shape, -1, np.int32)
    for gi in range(len(masks)):  # stigende: senere grupper overskriver i tvilssonen
        owner[D[gi] <= dmin + build_margin] = gi
    parts = []
    for gi in range(len(masks)):
        part_sub = sub & (owner == gi)
        part_sub = ndimage.binary_opening(part_sub, iterations=2)
        part_sub = ndimage.binary_closing(part_sub, iterations=4)
        if part_sub.sum() >= min_px:
            part = np.zeros(comp.shape, bool)
            part[sl] = part_sub
            parts.append((gi, part))
    return parts


def composite(base: np.ndarray, full: np.ndarray, groups: list) -> list:
    """Iterativ paste i byggerekkefølge. groups = [(maske, debut_arr), ...].

    Kilderegel: full der gruppen er øverst i stabelen; debut-bildet der
    senere grupper okkluderer i full (f.eks. teppe-under-sofa). Returnerer
    frames [base, etter gruppe 1, ..., etter gruppe n] som uint8.
    """
    n = len(groups)
    later = [None] * n
    acc = np.zeros(base.shape[:2], dtype=bool)
    for i in range(n - 1, -1, -1):
        later[i] = acc.copy()
        acc |= groups[i][0]
    frames = [base.copy()]
    comp = base.astype(np.float32)
    full_f = full.astype(np.float32)
    for i, (mask, debut) in enumerate(groups):
        occ = feather(mask & later[i], dilate=2, sigma=3.0)[..., None]
        src = full_f * (1 - occ) + debut.astype(np.float32) * occ
        a = feather(mask)[..., None]
        comp = src * a + comp * (1 - a)
        frames.append(np.clip(comp + 0.5, 0, 255).astype(np.uint8))
    return frames
