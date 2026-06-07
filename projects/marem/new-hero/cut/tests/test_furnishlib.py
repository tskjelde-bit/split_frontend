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


def test_residual_holes_finds_leaked_fragment():
    H, W = 200, 200
    empty = np.full((H, W, 3), 80, np.uint8)
    full = empty.copy()
    full[100:140, 60:120] = (200, 60, 30)    # objekt
    full[105:115, 130:150] = (220, 220, 40)  # «pute» som drift åt av masken
    union = np.zeros((H, W), bool)
    union[95:145, 55:125] = True             # maske dekker objektet, ikke puten
    comps = fl.residual_holes(full, empty, union)
    assert len(comps) == 1
    assert comps[0][110, 140]
    assert not (comps[0] & union).any()


def test_split_residual_assigns_per_pixel_by_magnitude():
    H, W = 200, 200
    floor = np.full((H, W, 3), 80, np.uint8)
    s0 = floor.copy()
    s0[100:130, 60:90] = (220, 220, 40)     # objekt A (fjernes i steg 2)
    s0[100:130, 95:125] = (10, 200, 200)    # objekt B (fjernes i steg 1)
    s1 = s0.copy()
    s1[100:130, 95:125] = 80
    s2 = s1.copy()
    s2[100:130, 60:90] = 80
    arrs = {0: s0, 1: s1, 2: s2}
    comp = np.zeros((H, W), bool)
    comp[100:130, 60:125] = True
    parts = fl.split_residual(comp, arrs, [[2], [1]])
    got = {gi: p for gi, p in parts}
    assert set(got) == {0, 1}
    assert got[0][115, 75] and not got[0][115, 110]
    assert got[1][115, 110] and not got[1][115, 75]


def test_residual_metrics_separates_fragment_from_variance():
    H, W = 200, 200
    floor = np.full((H, W, 3), 80, np.uint8)
    s0 = floor.copy()
    s0[100:130, 60:90] = (220, 220, 40)    # pute (fjernes i steg 1)
    s0[20:50, 150:180] = (200, 60, 30)     # «kunst» (vibrerer bare)
    s1 = s0.copy()
    s1[100:130, 60:90] = 80                 # fjerning: objekt -> gulv
    s1[20:50, 150:180] = (210, 70, 40)      # svak vibrasjon
    arrs = {0: s0, 1: s1}
    union = np.zeros((H, W), bool)
    union[95:135, 40:65] = True             # maske rett ved puta
    pute = np.zeros((H, W), bool)
    pute[100:130, 60:90] = True
    kunst = np.zeros((H, W), bool)
    kunst[20:50, 150:180] = True
    near_p, rem_p = fl.residual_metrics(pute, arrs, union)
    near_k, rem_k = fl.residual_metrics(kunst, arrs, union)
    assert near_p and rem_p >= fl.RESIDUAL_REMOVAL_MIN  # ekte fragment
    assert (not near_k) or rem_k < fl.RESIDUAL_REMOVAL_MIN  # varians: avvises


def test_stage_pair_mask_fills_low_contrast_holes():
    H, W = 300, 300
    floor = np.full((H, W, 3), 200, np.uint8)   # lys parkett
    rug = floor.copy()
    rug[100:250, 50:250] = 185                   # lyst teppe, lav kontrast
    rug[100:250, 50:55] = 120                    # kontrastkant venstre
    rug[100:250, 245:250] = 120                  # kontrastkant høyre
    rug[100:105, 50:250] = 120                   # topp
    rug[245:250, 50:250] = 120                   # bunn
    m = fl.stage_pair_mask(rug, floor, [0, 0, 300, 300])
    assert m[175, 150]   # MIDTEN er med (hull-fylt) selv om diff < terskel der
    assert not m[20, 20]
