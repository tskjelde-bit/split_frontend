import json
from pathlib import Path

import build_data


def test_price_sum_validates():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    errors, _ = build_data.validate_prisliste(prisliste)
    assert errors == []


def test_price_sum_error_on_tamper():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    prisliste["H0101"]["pris"] += 1
    errors, _ = build_data.validate_prisliste(prisliste)
    assert any("91270000" in e for e in errors)


def test_bra_sum_includes_duplex_u():
    prisliste = json.loads((Path(__file__).parent / "prisliste.json").read_text())
    assert build_data.bra_sum(prisliste) == 445


def test_units_match_rentegning_and_floors():
    errors = build_data.validate_coverage()
    assert errors == []


def test_build_units_merges_architect_data():
    units = build_data.build_units()
    assert units["H0101"]["pris"] == 5850000
    assert units["H0101"]["etasje"] == 1
    assert units["H0101"]["duplex"] is True
    assert units["H0204"]["braArkitekt"] > 0
    assert units["H0201"]["etasje"] == 2  # docx floor typo must be overridden by architect data


def test_all_units_inside_envelope():
    assert build_data.validate_envelope_containment() == []


def test_geometry_emits_envelope_and_stacked_elevations():
    geo = build_data.build_geometry()
    assert "envelope" in geo
    assert "poly" in geo["envelope"]
    # every floor outline is the canonical envelope
    for f in geo["floors"]:
        assert f["outline"] == geo["envelope"]["poly"]
    elevations = [f["elevation"] for f in geo["floors"]]
    assert elevations == [0.0, 3.0, 6.6, 10.2]
    assert geo["roof"]["elevation"] == 12.9
    assert geo["roof"]["type"] == "saltak"


def test_poly_area_m2():
    # 100x100 px ved scale 0.012696 = 1.612 m²
    assert abs(build_data.poly_area_m2([[0, 0], [100, 0], [100, 100], [0, 100]]) - 1.612) < 0.01


def test_unit_area_validator_flags_mismatch():
    floors = {"2": {"units": [{"id": "HX", "unit": "HX", "poly": [[0, 0], [100, 0], [100, 100], [0, 100]]}]}}
    arch = {"HX": {"bra": 30.0}}          # polygon er 1.6 m² — langt unna
    errors, warnings = build_data.validate_unit_areas(floors, arch, {}, strict=True)
    assert any("HX" in e for e in errors)
    errors2, warnings2 = build_data.validate_unit_areas(floors, arch, {}, strict=False)
    assert not errors2 and any("HX" in w for w in warnings2)


def test_unit_area_validator_passes_within_tolerance():
    floors = {"2": {"units": [{"id": "HX", "unit": "HX", "poly": [[0, 0], [1364, 0], [1364, 1364], [0, 1364]]}]}}
    arch = {"HX": {"bra": 300.0}}         # 1364² px ≈ 299.9 m²
    errors, _ = build_data.validate_unit_areas(floors, arch, {}, strict=True)
    assert errors == []


def test_duplex_u_polygons_checked_against_braU():
    floors = {"u": {"units": [{"id": "HX-U", "unit": "HX", "poly": [[0, 0], [100, 0], [100, 100], [0, 100]]}]}}
    prisliste = {"HX": {"braU": 30}}
    errors, _ = build_data.validate_unit_areas(floors, {}, prisliste, strict=True)
    assert any("HX-U" in e or "HX" in e for e in errors)


def test_geometry_emits_materials_and_facade():
    geo = build_data.build_geometry()
    m = geo["materials"]
    assert m["pussRosa"] == "#E4B49C"
    assert m["takSort"] == "#2E3038"
    facade = {f["id"]: f["facade"] for f in geo["floors"]}
    assert facade == {"U": "#E9E6E0", "1": "#E9E6E0", "2": "#E4B49C", "3": "#E4B49C"}
