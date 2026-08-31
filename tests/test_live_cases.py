"""The npm live harness must consume the current Python case fixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "schema" / "live-cases.json"


def test_live_case_fixture_matches_python_source() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/live_crud_check.py", "--check-cases"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_live_case_fixture_carries_confirmed_nmas_setup() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    nmas = next(case for case in cases if case["endpoint"] == "/db/NMAS")

    assert nmas["confirmed"] is True
    assert nmas["createPayload"] == {"mX": 1.0, "mY": 1.0, "mZ": 1.0}
    assert nmas["setup"] == [{"endpoint": "/db/NODE", "id": 3}]


def test_live_case_fixture_carries_static_load_case_seed() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    stld = next(case for case in fixture["cases"] if case["endpoint"] == "/db/STLD")

    assert fixture["version"] == 3
    assert fixture["seeds"]["static_load_cases"] == {
        "endpoint": "/db/STLD",
        "records": {
            "1": {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"},
            "2": {"NAME": "LC_SCRATCH", "TYPE": "L", "DESC": "crud fixture"},
        },
    }
    assert stld["setup"] == [{"seed": "static_load_cases"}]


def test_live_case_fixture_carries_skew_node_seed() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    skew = next(case for case in fixture["cases"] if case["endpoint"] == "/db/SKEW")

    assert fixture["seeds"]["skew_node"] == {
        "endpoint": "/db/NODE",
        "records": {"2": {"X": 0, "Y": 0, "Z": 3.2}},
    }
    assert skew["setup"] == [{"seed": "skew_node"}]


def test_live_case_fixture_carries_design_element_setup() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    element_cases = [
        next(case for case in fixture["cases"] if case["endpoint"] == endpoint)
        for endpoint in ("/db/LENG", "/db/LTSR", "/db/MBTP")
    ]

    for case in element_cases:
        assert case["id"] == 2
        assert case["setup"] == [
            {"seed": "ltsr_material"},
            {"seed": "ltsr_section"},
            {"seed": "ltsr_nodes"},
            {"seed": "ltsr_beam"},
        ]
    assert fixture["seeds"]["ltsr_beam"] == {
        "endpoint": "/db/ELEM",
        "records": {"2": {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [2, 3]}},
    }


def test_live_case_fixture_carries_design_member_setup() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    memb = next(case for case in fixture["cases"] if case["endpoint"] == "/db/MEMB")

    assert memb["setup"] == [
        {"seed": "ltsr_material"},
        {"seed": "ltsr_section"},
        {"seed": "ltsr_nodes"},
        {"seed": "ltsr_beam"},
        {"seed": "member_node"},
        {"seed": "member_beam"},
    ]
    assert fixture["seeds"]["member_beam"] == {
        "endpoint": "/db/ELEM",
        "records": {"3": {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [3, 4]}},
    }


def test_live_case_fixture_carries_wall_mark_plate_setup() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    wmak = next(case for case in fixture["cases"] if case["endpoint"] == "/db/WMAK")

    assert wmak["setup"] == [
        {"seed": "ltsr_material"},
        {"seed": "wmak_thickness"},
        {"seed": "wmak_nodes"},
        {"seed": "wmak_plate"},
    ]
    assert fixture["seeds"]["wmak_plate"] == {
        "endpoint": "/db/ELEM",
        "records": {
            "4": {
                "TYPE": "PLATE", "MATL": 1, "SECT": 1,
                "NODE": [1, 2, 4, 3], "ANGLE": 0, "STYPE": 1,
            },
        },
    }


def test_live_case_fixture_carries_manual_sdis_lrb_shape() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    sdis = next(case for case in cases if case["endpoint"] == "/db/SDIS")
    lrb = sdis["createPayload"]["LRB"]

    assert lrb["K0"] == 20000
    assert lrb["DX"] == {
        "OPT_CONS_NONL": False,
        "BETA": 0.1,
        "ALPHA": 0.5,
        "SIGMA_V": 3000,
    }


def test_live_case_fixture_carries_manual_sdst_bl2_shape() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    sdst = next(case for case in cases if case["endpoint"] == "/db/SDST")

    assert {
        key: sdst["createPayload"][key]
        for key in ("K0", "P1", "ALPHA1", "KB", "BL2")
    } == {
        "K0": 1000,
        "P1": 100,
        "ALPHA1": 0.2,
        "KB": 2000,
        "BL2": {"BETA": 0},
    }
    assert sdst["confirmed"] is True


def test_live_case_fixture_marks_reconfirmed_plane_load_type() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    pnld = next(case for case in cases if case["endpoint"] == "/db/PNLD")

    assert pnld["confirmed"] is True
    assert pnld["id"] == 2
    assert pnld["setup"] == []


def test_live_case_fixture_marks_reconfirmed_civil_analysis_cases() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    civil_cases = {
        case["endpoint"]: case
        for case in cases
        if case["products"] == ["civil"]
        and case["endpoint"] in {"/db/EIGV", "/db/BCCT"}
    }

    assert set(civil_cases) == {"/db/EIGV", "/db/BCCT"}
    assert all(case["confirmed"] is True for case in civil_cases.values())
