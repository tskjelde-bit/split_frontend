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
