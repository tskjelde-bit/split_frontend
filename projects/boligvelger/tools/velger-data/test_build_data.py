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
