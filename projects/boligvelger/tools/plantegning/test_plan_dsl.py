import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fixtures
import plan_dsl


def _hems_spec(**kw):
    base = {"envelope": [[0, 0], [400, 0], [400, 300], [0, 300]],
            "rooms": [{"name": "Stue", "area": "10,0", "kind": "rom",
                       "poly": [[20, 20], [380, 20], [380, 280], [20, 280]]}],
            "hems": {"poly": [[0, 0], [200, 0], [200, 150], [0, 150]], "area": "3,0", **kw}}
    return base


def test_sluk_symbol_exists():
    assert 'id="sluk"' in fixtures.DEFS
    assert plan_dsl.SYM_SIZE["sluk"] == (12, 12)


def test_hems_open_edge_renders_label_and_dash():
    svg = plan_dsl.render_hems(_hems_spec(open={"edge": [[0, 150], [200, 150]], "label": "Åpent ned"}))
    assert "Åpent ned" in svg
    assert "stroke-dasharray" in svg


def test_hems_skravur_renders_diagonals():
    svg = plan_dsl.render_hems(_hems_spec(skravur=[[0, 0], [100, 0], [100, 80], [0, 80]]))
    assert svg.count("<line") >= 4          # diagonale skravurlinjer
    assert "clip-path" in svg               # klippes til skravur-polygonet


def test_hems_ladder_renders():
    svg = plan_dsl.render_hems(_hems_spec(ladder=[150, 100, 40, 12]))
    assert svg.count("<line") >= 2          # stige-trinn
