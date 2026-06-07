#!/usr/bin/env python3
"""Crossfade-preview: furnish-frames -> mp4 i reelt tempo.

Bruk: preview_video.py <out-dir>   (leser f*.png, skriver preview.mp4)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HOLD_S, FADE_S, FPS, W = 0.9, 0.7, 30, 1280


def main() -> None:
    out_dir = Path(sys.argv[1])
    files = sorted(out_dir.glob("f*.png"))
    assert len(files) >= 2, f"fant bare {len(files)} frames i {out_dir}"
    arrs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        h = round(im.height * W / im.width)
        h -= h % 2  # yuv420p krever partall
        arrs.append(np.asarray(im.resize((W, h), Image.LANCZOS), dtype=np.float32))
    tmp = Path(tempfile.mkdtemp())
    idx = 0

    def emit(a):
        nonlocal idx
        Image.fromarray(a.astype(np.uint8)).save(tmp / f"{idx:05d}.png")
        idx += 1

    hold, fade = round(HOLD_S * FPS), round(FADE_S * FPS)
    for k, a in enumerate(arrs):
        for _ in range(hold):
            emit(a)
        if k + 1 < len(arrs):
            for t in range(1, fade + 1):
                w = t / (fade + 1)
                emit(a * (1 - w) + arrs[k + 1] * w)
    out = out_dir / "preview.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(tmp / "%05d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(out)], check=True)
    print(f"{out} ({idx} interp-frames, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
