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
