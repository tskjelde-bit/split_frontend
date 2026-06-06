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
