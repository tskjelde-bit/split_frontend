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
