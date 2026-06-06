# Furnish-frames Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministisk lokal pipeline som bygger QA-verifiserte «rommet møblerer seg selv»-frames for MAREM-hero scene 1 og 2, fra eksisterende kjede-/stage-bilder — null nye API-genereringer i hovedløpet.

**Architecture:** Kjernebibliotek (`furnishlib.py`) med maskederivasjon fra fjerne-kjeden (drift-filter + skygge-halo), base-ankring mot full, og okklusjonssikker iterativ komposisjon (kilderegel: full der øverst, debut-steg der okkludert). CLI-driver per scene fra `groups-*.json`, QA-script med 5 harde gates + montasjer, og crossfade-preview-video. `nb_remove.py` får `--accept-region` for kirurgisk regenerering ved QA-brudd.

**Tech Stack:** Python (numpy, PIL, scipy.ndimage, pytest) i venv `/Users/torbjorntest/projects/marem/figma-make-export/scripts/.venv`, ffmpeg (libx264) for preview.

**Spec:** `/Users/torbjorntest/projects/marem/docs/superpowers/specs/2026-06-07-furnish-frames-design.md`

**Arbeidskatalog:** `/Users/torbjorntest/projects/marem/new-hero/cut/` (heretter `cut/`). Git-rot er `/Users/torbjorntest`. Alle kommandoer antar:

```bash
cd /Users/torbjorntest/projects/marem/new-hero/cut
PY=/Users/torbjorntest/projects/marem/figma-make-export/scripts/.venv/bin/python
```

**Filstruktur:**

| Fil | Ansvar |
|---|---|
| `cut/furnishlib.py` (ny) | kjedeoppslag, drift-maske, gruppemasker m/halo, ankring, komposisjon |
| `cut/furnish_frames.py` (ny) | CLI: groups-JSON → frames (PNG fullres + 2048w webp) + manifest + masks.npz |
| `cut/qa_furnish.py` (ny) | gates 1–5, per-gruppe montasjer, qa-report.txt, exit-kode |
| `cut/preview_video.py` (ny) | crossfade-mp4 i reelt tempo |
| `cut/groups-scene1.json`, `cut/groups-scene2.json` (ny) | gruppedefinisjoner (rekkefølge + diffsteg) |
| `cut/nb_remove.py` (endres) | `--accept-region=<maske.png>` på containment |
| `cut/tests/` (ny) | conftest + syntetiske enhetstester |
| `cut/furnish/scene{1,2}/` (output, gitignored) | frames, manifest, QA-artefakter, preview.mp4 |

**Kjedefakta (verifisert på disk):** scene1-steps har steg 00–12 (`scene1-00-full.png` … `scene1-12-base.png`), scene2-steps har 00–09. Full = 5504×3072. Basene `proof/stages-scene{1,2}/f0-empty.png` er også 5504×3072. ffmpeg finnes i `/opt/homebrew/bin`. pytest mangler i venv (installeres i Task 1).

---

### Task 1: Test-oppsett

**Files:**
- Create: `cut/tests/conftest.py`
- Create: `cut/.gitignore`

- [ ] **Step 1: Installer pytest i venv**

```bash
$PY -m pip install pytest
$PY -m pytest --version
```
Expected: `pytest 8.x`

- [ ] **Step 2: Skriv conftest og gitignore**

`cut/tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

`cut/.gitignore`:
```
furnish/
__pycache__/
.pytest_cache/
```

- [ ] **Step 3: Verifiser at pytest kjører (0 tester er OK)**

```bash
$PY -m pytest tests/ -q
```
Expected: `no tests ran`

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py .gitignore
git commit -m "Add pytest scaffolding for furnish-frames

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: furnishlib — kjedeoppslag og drift-maske

**Files:**
- Create: `cut/furnishlib.py`
- Test: `cut/tests/test_furnishlib.py`

- [ ] **Step 1: Skriv feilende tester**

`cut/tests/test_furnishlib.py`:
```python
import numpy as np

import furnishlib as fl


def test_chain_files_finds_numbered_steps(tmp_path):
    for name in ["scene1-00-full.png", "scene1-01-uten-dekor.png",
                 "scene1-01-uten-dekor.png.diff.png", "scene1-02-x.png.raw.png",
                 "scene1-12-base.png", "annet.png"]:
        (tmp_path / name).touch()
    files = fl.chain_files(tmp_path, "scene1")
    assert sorted(files) == [0, 1, 12]
    assert files[12].name == "scene1-12-base.png"


def test_drift_mask_flags_vibrating_pixels():
    base = np.full((100, 100, 3), 100, np.uint8)
    arrs = []
    for k in range(5):
        a = base.copy()
        a[10:30, 10:30] = 100 + (k % 2) * 60   # vibrerer i hvert steg = drift
        if k >= 2:
            a[60:80, 60:80] = 200               # ekte objekt: endres i ett steg
        arrs.append(a)
    noise = fl.drift_mask(arrs)
    assert noise[20, 20]
    assert not noise[70, 70]
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: FAIL/ERROR med `ModuleNotFoundError: No module named 'furnishlib'`

- [ ] **Step 3: Implementer**

`cut/furnishlib.py`:
```python
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
```

- [ ] **Step 4: Kjør — skal passere**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add furnishlib.py tests/test_furnishlib.py
git commit -m "Add furnishlib chain loading and drift mask

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: furnishlib — gruppemasker med skygge-halo

**Files:**
- Modify: `cut/furnishlib.py` (append)
- Test: `cut/tests/test_furnishlib.py` (append)

- [ ] **Step 1: Skriv feilende tester**

Append til `cut/tests/test_furnishlib.py`:
```python
def scene_pair(H=240, W=320):
    """Gulv + objekt med myk skygge (delta 18: > SHADOW_LO, < THRESH)."""
    rng = np.random.default_rng(7)
    floor = rng.integers(70, 90, (H, W, 3)).astype(np.uint8)
    with_obj = floor.copy()
    with_obj[120:180, 100:180] = (200, 60, 30)
    sh = floor[185:210, 95:185].astype(np.int16) - 18
    with_obj[185:210, 95:185] = np.clip(sh, 0, 255).astype(np.uint8)
    return with_obj, floor


def test_step_core_finds_object_excludes_drift():
    a, b = scene_pair()
    noise = np.zeros(a.shape[:2], bool)
    noise[10:60, 10:60] = True
    a2 = a.copy()
    a2[10:60, 10:60] = 255          # stor endring i drift-region
    core = fl.step_core(a2, b, noise)
    assert core[150, 140]            # objektet funnet
    assert not core[30, 30]          # drift ekskludert
    assert not core[200, 140]        # myk skygge er under kjerneterskel


def test_shadow_halo_includes_soft_shadow():
    a, b = scene_pair()
    noise = np.zeros(a.shape[:2], bool)
    core = fl.step_core(a, b, noise)
    full_mask = fl.add_shadow_halo(core, a, b, noise)
    assert full_mask[200, 140]       # skyggen er med


def test_group_mask_unions_steps_and_dilates():
    a, b = scene_pair()
    noise = np.zeros(a.shape[:2], bool)
    c = b.copy()
    c[20:50, 200:260] = (10, 200, 10)  # annet objekt i neste steg
    arrs = {0: a, 1: b, 2: c}
    m = fl.group_mask(arrs, [1, 2], noise)
    assert m[150, 140] and m[35, 230]  # begge objekter i unionen
    assert m[118, 98]                   # dilatert utover objektkanten
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 2 passed (Task 2), 3 failed med `AttributeError: ... 'step_core'`

- [ ] **Step 3: Implementer**

Append til `cut/furnishlib.py`:
```python
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
```

- [ ] **Step 4: Kjør — skal passere**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add furnishlib.py tests/test_furnishlib.py
git commit -m "Add group mask derivation with shadow halo

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: furnishlib — feather og base-ankring

**Files:**
- Modify: `cut/furnishlib.py` (append)
- Test: `cut/tests/test_furnishlib.py` (append)

- [ ] **Step 1: Skriv feilende tester**

Append til `cut/tests/test_furnishlib.py`:
```python
def test_feather_is_soft_and_clipped():
    m = np.zeros((100, 100), bool)
    m[40:60, 40:60] = True
    a = fl.feather(m)
    assert a.max() <= 1.0 and a.min() >= 0.0
    assert a[50, 50] > 0.99          # kjernen er solid
    assert 0.0 < a[50, 67] < 1.0     # myk kant utenfor masken
    assert a[5, 5] == 0.0            # langt unna: eksakt null


def test_anchor_base_keeps_full_outside_furniture():
    full = np.full((200, 200, 3), 120, np.uint8)
    empty = np.full((200, 200, 3), 60, np.uint8)
    furn = np.zeros((200, 200), bool)
    furn[80:120, 80:120] = True
    base = fl.anchor_base(empty, full, furn)
    assert (base[0:10] == 120).all()           # utenfor sonen: fulls piksler eksakt
    assert (base[95:105, 95:105] == 60).all()  # inni: empty-rekonstruksjonen
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 5 passed, 2 failed med `AttributeError: ... 'feather'`

- [ ] **Step 3: Implementer**

Append til `cut/furnishlib.py`:
```python
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
```

- [ ] **Step 4: Kjør — skal passere**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add furnishlib.py tests/test_furnishlib.py
git commit -m "Add base anchoring and feathered masks

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: furnishlib — okklusjonssikker komposisjon (kilderegelen)

**Files:**
- Modify: `cut/furnishlib.py` (append)
- Test: `cut/tests/test_furnishlib.py` (append)

- [ ] **Step 1: Skriv feilende test — dette er kjernetesten for hele designet**

Append til `cut/tests/test_furnishlib.py`:
```python
def test_composite_occluded_parts_come_from_debut():
    """Teppe under sofa: frame 1 skal vise DEBUT-rekonstruksjonen (190),
    aldri fulls piksler (sofa, 30). Frame 2 skal vise sofaen."""
    H, W = 200, 200
    base = np.full((H, W, 3), 50, np.uint8)
    full = base.copy()
    full[100:160, 40:160] = (200, 200, 200)   # teppe i full
    full[100:160, 80:120] = (30, 30, 30)      # sofa OPPÅ teppet i full
    debut_rug = base.copy()
    debut_rug[100:160, 40:160] = (190, 190, 190)  # teppe alene, rekonstruert tone
    rug_mask = np.zeros((H, W), bool)
    rug_mask[100:160, 40:160] = True
    sofa_mask = np.zeros((H, W), bool)
    sofa_mask[100:160, 80:120] = True
    frames = fl.composite(base, full, [(rug_mask, debut_rug), (sofa_mask, full)])
    assert len(frames) == 3
    assert (frames[0] == base).all()
    f1 = frames[1].astype(int)
    assert (np.abs(f1[130, 100] - 190) <= 2).all()  # under-sofa: fra DEBUT
    assert (np.abs(f1[130, 60] - 200) <= 2).all()   # uokkludert: fra FULL
    f2 = frames[2].astype(int)
    assert (np.abs(f2[130, 100] - 30) <= 2).all()   # sofa på plass
    assert (np.abs(f2[130, 60] - 200) <= 2).all()   # teppet uendret


def test_composite_untouched_pixels_are_bit_identical():
    """Piksler utenfor en gruppes feather-sone skal være BIT-identiske
    mellom nabo-frames — grunnlaget for gate 1/2/3."""
    H, W = 200, 200
    base = np.full((H, W, 3), 50, np.uint8)
    full = base.copy()
    full[100:140, 100:140] = (200, 60, 30)
    m = np.zeros((H, W), bool)
    m[100:140, 100:140] = True
    frames = fl.composite(base, full, [(m, full)])
    d = np.abs(frames[1].astype(np.int16) - frames[0].astype(np.int16)).max(2)
    far = np.ones((H, W), bool)
    far[100 - fl.QA_PAD:140 + fl.QA_PAD, 100 - fl.QA_PAD:140 + fl.QA_PAD] = False
    assert d[far].max() == 0
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 7 passed, 2 failed med `AttributeError: ... 'composite'`

- [ ] **Step 3: Implementer**

Append til `cut/furnishlib.py`:
```python
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
```

- [ ] **Step 4: Kjør — skal passere**

```bash
$PY -m pytest tests/test_furnishlib.py -v
```
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add furnishlib.py tests/test_furnishlib.py
git commit -m "Add occlusion-aware composite with source rule

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: nb_remove.py — `--accept-region`

**Files:**
- Modify: `cut/nb_remove.py` (contain-funksjonen, linje ~111–150, og main, linje ~183)
- Test: `cut/tests/test_nb_remove.py`

- [ ] **Step 1: Skriv feilende test**

`cut/tests/test_nb_remove.py`:
```python
import numpy as np
from PIL import Image

import nb_remove as nb


def test_contain_accept_region(tmp_path):
    """Med region: modell-endringer UTENFOR regionen reverteres til input."""
    inp = np.full((120, 120, 3), 100, np.uint8)
    out = inp.copy()
    out[10:40, 10:40] = 200    # endring A — utenfor region (skal reverteres)
    out[70:100, 70:100] = 220  # endring B — innenfor region (skal beholdes)
    region = np.zeros((120, 120), np.uint8)
    region[60:110, 60:110] = 255
    p_in, p_out, p_reg = tmp_path / "in.png", tmp_path / "out.png", tmp_path / "r.png"
    Image.fromarray(inp).save(p_in)
    Image.fromarray(out).save(p_out)
    Image.fromarray(region).save(p_reg)
    nb.contain(p_in, p_out, region_path=str(p_reg))
    res = np.asarray(Image.open(p_out).convert("RGB"))
    assert (res[10:40, 10:40] == 100).all()
    assert (res[80:90, 80:90] == 220).all()
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_nb_remove.py -v
```
Expected: FAIL med `TypeError: contain() got an unexpected keyword argument 'region_path'`

- [ ] **Step 3: Implementer**

I `cut/nb_remove.py`, endre contain-signaturen og legg inn region-klipp rett etter dilation:

```python
def contain(inp: Path, outp: Path, boxfill: bool = False,
            region_path: str | None = None) -> None:
```

og etter linjen `mask = ndimage.binary_dilation(keep, iterations=30)  # ta med myke kanter/skygge`:

```python
    if region_path:
        region = np.asarray(
            Image.open(region_path).convert("L").resize(
                (a.shape[1], a.shape[0]), Image.NEAREST)
        ) > 127
        mask &= region
```

I `main()`, erstatt arg-parsingen (de to første linjene) med:

```python
    region = None
    for arg in sys.argv[1:]:
        if arg.startswith("--accept-region="):
            region = arg.split("=", 1)[1]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    boxfill = "--boxfill" in sys.argv
```

og endre contain-kallet nederst i main til:

```python
    contain(inp, outp, boxfill=boxfill, region_path=region)
```

Oppdater docstring-bruken øverst i fila til:
```
    nb_remove.py <input.png> <output.png> "<objektbeskrivelse, engelsk>" [--boxfill] [--accept-region=maske.png]
```

- [ ] **Step 4: Kjør — skal passere (alle tester)**

```bash
$PY -m pytest tests/ -v
```
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add nb_remove.py tests/test_nb_remove.py
git commit -m "Add accept-region restriction to nb_remove containment

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: groups-configs + furnish_frames.py-driver, kjør scene 1

**Files:**
- Create: `cut/groups-scene1.json`
- Create: `cut/groups-scene2.json`
- Create: `cut/furnish_frames.py`

- [ ] **Step 1: Skriv configene**

`cut/groups-scene1.json` (byggerekkefølge = reversert kjede; debut utledes som min(diff_steps)-1):
```json
{
  "scene": "scene1",
  "steps_dir": "scene1-steps",
  "base_empty": "proof/stages-scene1/f0-empty.png",
  "out_dir": "furnish/scene1",
  "groups": [
    {"name": "teppe", "diff_steps": [12]},
    {"name": "sofa", "diff_steps": [11]},
    {"name": "skap-vase", "diff_steps": [10, 9]},
    {"name": "lampe", "diff_steps": [8]},
    {"name": "daybed-pledd", "diff_steps": [7, 6]},
    {"name": "stoler", "diff_steps": [5, 4]},
    {"name": "bord", "diff_steps": [3, 2]},
    {"name": "dekor", "diff_steps": [1]}
  ]
}
```

`cut/groups-scene2.json`:
```json
{
  "scene": "scene2",
  "steps_dir": "scene2-steps",
  "base_empty": "proof/stages-scene2/f0-empty.png",
  "out_dir": "furnish/scene2",
  "groups": [
    {"name": "teppe", "diff_steps": [9]},
    {"name": "venstresofa", "diff_steps": [8]},
    {"name": "midtsofa", "diff_steps": [7]},
    {"name": "lamper", "diff_steps": [6]},
    {"name": "lenestoler", "diff_steps": [5, 4]},
    {"name": "bord", "diff_steps": [3, 2]},
    {"name": "dekor", "diff_steps": [1]}
  ]
}
```

- [ ] **Step 2: Skriv driveren**

`cut/furnish_frames.py`:
```python
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
```

- [ ] **Step 3: Kjør scene 1 (tar noen minutter — 13 stk 4K-bilder + morfologi)**

```bash
$PY furnish_frames.py groups-scene1.json
```
(Bash-timeout: 600000 ms.)
Expected output (verdier vil variere):
```
scene1: laster 13 kjedesteg ...
  drift-maske: ~2-15%
  teppe: maske ~8-14%, debut=steg 11
  sofa: maske ~5-9%, debut=steg 10
  ... (8 grupper)
scene1: 9 frames -> .../furnish/scene1 (webp totalt ...)
```
Sanity-krav: ingen assertion-feil; ingen gruppe med maske >25% eller <0.05%. Hvis en maske er mistenkelig stor/liten: STOPP og rapporter tallene i stedet for å fortsette.

- [ ] **Step 4: Commit (scripts + configs — output er gitignored)**

```bash
git add groups-scene1.json groups-scene2.json furnish_frames.py
git commit -m "Add furnish_frames driver and scene group configs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: qa_furnish.py — gates + montasjer, QA av scene 1

**Files:**
- Create: `cut/qa_furnish.py`
- Test: `cut/tests/test_qa.py`

- [ ] **Step 1: Skriv feilende test — QA-detektoren skal fange kommer-og-går**

`cut/tests/test_qa.py`:
```python
import numpy as np

import qa_furnish as qa


def test_gate1_detects_come_and_go():
    H, W = 100, 100
    base = np.zeros((H, W, 3), np.uint8)
    m = np.zeros((H, W), bool)
    m[40:60, 40:60] = True
    f1 = base.copy()
    f1[40:60, 40:60] = 200          # gruppen plassert i frame 1
    f2 = base.copy()                 # ... og FORSVUNNET i frame 2
    res = qa.gate1([base, f1, f2], [m, np.zeros((H, W), bool)], ["obj", "tom"])
    assert res[0]["worst"] >= 200    # bruddet fanges


def test_gate1_passes_when_placed_stays():
    H, W = 100, 100
    base = np.zeros((H, W, 3), np.uint8)
    m = np.zeros((H, W), bool)
    m[40:60, 40:60] = True
    f1 = base.copy()
    f1[40:60, 40:60] = 200
    res = qa.gate1([base, f1, f1.copy()], [m, np.zeros((H, W), bool)], ["obj", "tom"])
    assert res[0]["worst"] == 0
```

- [ ] **Step 2: Kjør — skal feile**

```bash
$PY -m pytest tests/test_qa.py -v
```
Expected: FAIL/ERROR med `ModuleNotFoundError: No module named 'qa_furnish'`

- [ ] **Step 3: Implementer**

`cut/qa_furnish.py`:
```python
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
```

- [ ] **Step 4: Kjør testene — skal passere**

```bash
$PY -m pytest tests/ -v
```
Expected: 12 passed

- [ ] **Step 5: Kjør QA på scene 1**

```bash
$PY qa_furnish.py furnish/scene1 groups-scene1.json
```
(Bash-timeout: 600000 ms.)
Expected: gate-rapport per gruppe. Gate 1–3 skal være OK (de holder per konstruksjon — brudd = bug i composite/QA, gå tilbake til Task 5). Gate 4/5 kan gi WARN/FAIL på reelle dataavvik — det er informasjon, ikke nødvendigvis bug: noter hvilke grupper, fortsett til visuell inspeksjon.

- [ ] **Step 6: Visuell inspeksjon (utføres med Read på bildene)**

```bash
$PY - <<'EOF'
from PIL import Image
import glob
Image.MAX_IMAGE_PIXELS = None
for f in sorted(glob.glob("furnish/scene1/f*.png")):
    im = Image.open(f).convert("RGB"); im.thumbnail((1000, 1000))
    im.save(f"/tmp/insp-{f.split('/')[-1][:-4]}.jpg", quality=85)
EOF
```
Les deretter med Read-verktøyet: alle `furnish/scene1/qa-group-*.jpg` (full/debut/maske-overlay per gruppe) og `/tmp/insp-f00.jpg` … `/tmp/insp-f08.jpg`. Sjekkliste per frame: (a) kun den nye gruppen er kommet til, (b) ingen fragmenter av senere møbler, (c) ingen avtrykk på tomt gulv, (d) kunst/hyller/vinduer identiske hele veien, (e) møbler står på gulvet med skygge (svever ikke). Avvik dokumenteres med frame-nummer og region.

- [ ] **Step 7: Commit**

```bash
git add qa_furnish.py tests/test_qa.py
git commit -m "Add furnish QA gates and montages

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: preview_video.py + scene 1-video

**Files:**
- Create: `cut/preview_video.py`

- [ ] **Step 1: Skriv scriptet**

`cut/preview_video.py`:
```python
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
```

- [ ] **Step 2: Kjør for scene 1**

```bash
$PY preview_video.py furnish/scene1
```
Expected: `furnish/scene1/preview.mp4 (~400 interp-frames, ...)`

- [ ] **Step 3: Verifiser videoen teknisk + visuelt**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 furnish/scene1/preview.mp4
ffmpeg -y -loglevel error -i furnish/scene1/preview.mp4 -vf "select=not(mod(n\,90))" -vsync vfr /tmp/vid-%02d.jpg
```
Expected duration: ~13–14 s (9 frames × 0.9 s hold + 8 × 0.7 s fade). Les 3–4 av `/tmp/vid-*.jpg` med Read og bekreft progressiv møblering uten artefakter.

- [ ] **Step 4: Commit**

```bash
git add preview_video.py
git commit -m "Add crossfade preview video generator

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Scene 2 ende-til-ende

**Files:** ingen nye — kjører eksisterende scripts på scene 2.

- [ ] **Step 1: Bygg frames**

```bash
$PY furnish_frames.py groups-scene2.json
```
(Bash-timeout: 600000 ms.)
Expected: `scene2: 8 frames -> .../furnish/scene2`

- [ ] **Step 2: QA**

```bash
$PY qa_furnish.py furnish/scene2 groups-scene2.json
```
Expected: gate-rapport; gate 1–3 OK, noter gate 4/5-avvik.

- [ ] **Step 3: Preview-video**

```bash
$PY preview_video.py furnish/scene2
```

- [ ] **Step 4: Visuell inspeksjon som i Task 8 Step 6 / Task 9 Step 3** (montasjer + frames + videosamples for scene 2, samme sjekkliste).

- [ ] **Step 5: Ingen commit nødvendig** (kun gitignored output). Hvis scripts måtte justeres: commit endringen med beskrivende melding + Co-Authored-By-linje.

---

### Task 11: Funn-håndtering og leveranse

**Files:** situasjonsavhengig.

- [ ] **Step 1: Samle QA-status for begge scener**

Les `furnish/scene1/qa-report.txt` og `furnish/scene2/qa-report.txt`. Tre utfall per funn:

1. **Gate 1–3-brudd** → bug i composite/QA-logikk. Ikke datafiks — tilbake til Task 5/8, reproduser med syntetisk test først.
2. **Gate 4-brudd** (klynge som popper ved full-swap) → masken bommet på noe (f.eks. magasin, myk skygge). Fiks: utvid aktuell gruppes maske — legg det savnede kjedesteget i gruppen eller juster SHADOW_REACH/MASK_DILATE i furnishlib (én endring, kjør furnish+qa på nytt). Dokumenter valget i commit-meldingen.
3. **Gate 5-FAIL eller visuelt stygg region** (objekt flyttet/korrupt i kjeden, stygg rekonstruksjon) → kirurgisk regenerering, prosedyre:

```bash
# 3a: eksporter gruppens maske som accept-region
$PY - <<'EOF'
import numpy as np
from PIL import Image
z = np.load("furnish/scene1/masks.npz")
i = 0  # <gruppeindeks fra qa-rapporten>
Image.fromarray((z[f"mask_{i:02d}"] * 255).astype(np.uint8)).save("/tmp/region.png")
EOF
# 3b: regenerer det aktuelle kjedesteget, kun aksept innenfor regionen
$PY nb_remove.py scene1-steps/scene1-<NN-1>-<navn>.png scene1-steps/scene1-<NN>-<navn>.png \
  "the <objektbeskrivelse>" --accept-region=/tmp/region.png
# 3c: bygg og QA på nytt
$PY furnish_frames.py groups-scene1.json && $PY qa_furnish.py furnish/scene1 groups-scene1.json
```
Maks 1–2 kirurgiske kall per scene; flere enn det = eskaler til bruker med funnene.

- [ ] **Step 2: Sluttverifisering**

```bash
$PY -m pytest tests/ -q
ls furnish/scene1/ furnish/scene2/
```
Expected: alle tester grønne; begge scener har f*.png, f*.webp, manifest.json, masks.npz, comp-final.png, qa-report.txt, qa-group-*.jpg, preview.mp4.

- [ ] **Step 3: Presenter for bruker**

Rapportér: QA-status per gate per scene (ærlig — inkluder WARN), stier til `furnish/scene1/preview.mp4` og `furnish/scene2/preview.mp4` for godkjenning, og at frontend-wiring (figma-make-export-hero) er neste fase etter godkjent video.

---

## Self-review (utført)

- **Spec-dekning:** masker m/drift+halo (T3), base-ankring (T4), kilderegel/okklusjon (T5), reversert-kjede-validering (T7), siste frame = full verbatim (T7), gates 1–5 (T8), montasjer (T8), preview-video (T9), `--accept-region` (T6), kirurgisk prosedyre (T11), webp+manifest-leveranse (T7), begge scener (T7+T10). Ingen gap.
- **Placeholder-scan:** all kode komplett, ingen TBD.
- **Typekonsistens:** `fl.QA_PAD`/`chain_files`/`load_rgb`/`drift_mask`/`step_core`/`add_shadow_halo`/`group_mask`/`feather`/`anchor_base`/`composite` definert i T2–T5, brukt med samme signaturer i T7–T8. `qa.gate1` definert i T8, testet i T8 Step 1. `nb.contain(..., region_path=)` definert i T6, brukt i T6-test og T11.
