#!/usr/bin/env python3
"""Fjern ett objekt fra et bilde med Nano Banana Pro (gemini-3-pro-image).

Bruk:
    nb_remove.py <input.png> <output.png> "<objektbeskrivelse, engelsk>"

- Laster opp input via Files API (4K PNG er for stor for inline)
- Prompt med låst disclaimer (ikke rør noe annet)
- Lagrer output-PNG + diff-visualisering (<output>.diff.png)
- Printer QA-metrikker: endret andel, bbox for endringen, dimensjoner
Exit 1 hvis output-dimensjoner avviker fra input.
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MODEL = "gemini-3-pro-image"
API = "https://generativelanguage.googleapis.com"

PROMPT_TEMPLATE = (
    "Remove the {obj} completely from this photo. "
    "Reconstruct whatever is naturally behind it (floor, rug, wall, window). "
    "Do not change anything else in the image: keep all other furniture and objects, "
    "the lighting, colors, shadows, curtains, windows, walls, ceiling, framing and "
    "camera angle exactly identical to the input. Output the full image at the same "
    "resolution and 16:9 aspect ratio."
)


def api_key() -> str:
    for line in (HERE / ".env").read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("GEMINI_API_KEY mangler i .env")


def upload_file(path: Path, key: str) -> str:
    data = path.read_bytes()
    # resumable upload, ett shot
    start = urllib.request.Request(
        f"{API}/upload/v1beta/files?key={key}",
        method="POST",
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(data)),
            "X-Goog-Upload-Header-Content-Type": "image/png",
            "Content-Type": "application/json",
        },
        data=json.dumps({"file": {"display_name": path.name}}).encode(),
    )
    with urllib.request.urlopen(start) as r:
        upload_url = r.headers["X-Goog-Upload-URL"]
    fin = urllib.request.Request(
        upload_url,
        method="POST",
        headers={
            "X-Goog-Upload-Command": "upload, finalize",
            "X-Goog-Upload-Offset": "0",
            "Content-Length": str(len(data)),
        },
        data=data,
    )
    with urllib.request.urlopen(fin) as r:
        info = json.load(r)["file"]
    # vent til ACTIVE
    name = info["name"]
    while info.get("state") == "PROCESSING":
        time.sleep(1)
        with urllib.request.urlopen(f"{API}/v1beta/{name}?key={key}") as r:
            info = json.load(r)
    return info["uri"]


def generate(file_uri: str, prompt: str, key: str) -> bytes:
    body = {
        "contents": [
            {
                "parts": [
                    {"file_data": {"mime_type": "image/png", "file_uri": file_uri}},
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9", "imageSize": "4K"},
        },
    }
    req = urllib.request.Request(
        f"{API}/v1beta/models/{MODEL}:generateContent?key={key}",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)
    for part in resp["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise SystemExit(f"ingen bildedel i svaret: {json.dumps(resp)[:400]}")


def contain(inp: Path, outp: Path, boxfill: bool = False) -> None:
    """Behold output kun i ekte endringsklynger; input-piksler ellers.

    Dreper subpiksel-drift (lysekronekrystall, hyllekanter) slik at drift
    aldri akkumulerer gjennom kjeden og lagene blir rene.

    boxfill=True: fyll hele bbox-en til store klynger. KUN for lavkontrast-
    fjerning (teppe ~ gulvfarge) der masken ellers får åpne ghost-hull.
    Brukes ikke ellers — bbox-fylling lekker modellens vindus-/detaljstøy
    inn i bildet og gir debris i lagene.
    """
    from scipy import ndimage

    a = np.asarray(Image.open(inp).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(outp).convert("RGB"), dtype=np.int16)
    d = np.abs(a - b).max(axis=2)
    core = d > 30  # ekte endring, ikke re-render-støy
    core = ndimage.binary_opening(core, iterations=2)  # dropp speckles
    # lukk smale gap slik at lavkontrast-områder henger sammen med klyngen
    core = ndimage.binary_closing(core, iterations=12)
    labels, n = ndimage.label(core)
    keep = np.zeros_like(core)
    if n:
        sizes = ndimage.sum(core, labels, range(1, n + 1))
        min_size = a.shape[0] * a.shape[1] * 5e-5
        slices = ndimage.find_objects(labels)
        for i, sl in enumerate(slices):
            if sizes[i] < min_size or sl is None:
                continue
            comp = labels[sl] == i + 1
            box_area = comp.shape[0] * comp.shape[1]
            if boxfill and box_area > a.shape[0] * a.shape[1] * 0.05:
                keep[sl] = True
            else:
                keep[sl] |= comp
    keep = ndimage.binary_fill_holes(keep)  # ingen ghost-hull inne i objektet
    mask = ndimage.binary_dilation(keep, iterations=30)  # ta med myke kanter/skygge
    out = np.where(mask[..., None], b, a).astype(np.uint8)
    Image.fromarray(out).save(outp)
    print(f"contain: beholdt {mask.mean() * 100:.1f}% fra modellen, resten fra input")


def qa(inp: Path, outp: Path) -> None:
    a = np.asarray(Image.open(inp).convert("L"), dtype=np.int16)
    b_img = Image.open(outp).convert("L")
    b = np.asarray(b_img, dtype=np.int16)
    if a.shape != b.shape:
        print(f"QA: DIMENSJONSAVVIK input={a.shape} output={b.shape}")
        sys.exit(1)
    d = np.abs(a - b)
    mask = d > 14
    frac = mask.mean()
    ys, xs = np.nonzero(mask)
    if len(xs):
        bw = (xs.max() - xs.min()) / a.shape[1]
        bh = (ys.max() - ys.min()) / a.shape[0]
    else:
        bw = bh = 0.0
    # diff-visualisering
    vis = np.zeros((*a.shape, 3), dtype=np.uint8)
    vis[..., 0] = np.where(mask, 255, (a // 3).astype(np.uint8))
    vis[..., 1] = (a // 3).astype(np.uint8)
    vis[..., 2] = (a // 3).astype(np.uint8)
    Image.fromarray(vis).resize((a.shape[1] // 4, a.shape[0] // 4)).save(
        str(outp) + ".diff.png"
    )
    print(
        f"QA: endret={frac * 100:.1f}% bbox={bw * 100:.0f}%x{bh * 100:.0f}% "
        f"({'OK' if frac < 0.30 else 'MISTENKELIG STOR ENDRING'})"
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--boxfill"]
    boxfill = "--boxfill" in sys.argv
    inp, outp, obj = Path(args[0]), Path(args[1]), args[2]
    key = api_key()
    print(f"laster opp {inp.name} ...")
    uri = upload_file(inp, key)
    prompt = PROMPT_TEMPLATE.format(obj=obj)
    print(f"fjerner: {obj}")
    t0 = time.time()
    png = generate(uri, prompt, key)
    outp.write_bytes(png)
    im = Image.open(outp)
    print(f"output: {outp.name} {im.size} ({len(png) // 1024} KB, {time.time() - t0:.0f}s)")
    if im.size != Image.open(inp).size:
        print("DIMENSJONSAVVIK — stopper før contain")
        sys.exit(1)
    Path(str(outp) + ".raw.png").write_bytes(png)  # før contain, for feilsøk
    contain(inp, outp, boxfill=boxfill)
    qa(inp, outp)


if __name__ == "__main__":
    main()
