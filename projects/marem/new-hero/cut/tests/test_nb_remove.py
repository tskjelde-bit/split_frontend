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
