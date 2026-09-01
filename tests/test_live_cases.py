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


def test_live_case_fixture_carries_manual_sdis_sld_shape() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    sdis = next(case for case in cases if case["endpoint"] == "/db/SDIS")
    payload = sdis["createPayload"]

    assert payload["SDIS_DEV_TYPE"] == "SLD"
    assert payload["SB"] == {
        "AS": 0.05,
        "K0": 100000,
        "QD": 2,
        "Pi_VALUE": 0,
        "MU0": 0.05,
    }
    assert sdis["confirmed"] is True


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


def test_live_case_fixture_carries_complete_manual_splc_and_thms_shapes() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    splc = [case for case in cases if case["endpoint"] == "/db/SPLC"]
    thms = next(case for case in cases if case["endpoint"] == "/db/THMS")

    assert all(case["confirmed"] is True for case in splc)
    assert splc[0]["createPayload"]["aUSEMODE"] == [
        {"bUSE": True, "MSFACTOR": 1},
        {"bUSE": True, "MSFACTOR": 1},
        {"bUSE": True, "MSFACTOR": 1},
    ]
    assert thms["confirmed"] is True
    assert thms["createPayload"]["ITEMS"][0] == {
        "ID": 1, "LCNAME": "THIS_SEED", "ANGLE": 0, "FUNCX": "THFC_SEED",
        "SCALEX": 1.0, "ATIMEX": 0, "FUNCY": "THFC_SEED", "SCALEY": 1.0,
        "ATIMEY": 0, "FUNCZ": "THFC_SEED", "SCALEZ": 0.667, "ATIMEZ": 0,
    }


def test_live_case_fixture_marks_reconfirmed_plane_load_type() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    pnld = next(case for case in cases if case["endpoint"] == "/db/PNLD")

    assert pnld["confirmed"] is True
    assert pnld["id"] == 2
    assert pnld["setup"] == []


def test_live_case_fixture_uses_complete_manual_seismic_damper_examples() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    sdvi = next(case for case in cases if case["endpoint"] == "/db/SDVI")
    sdve = next(case for case in cases if case["endpoint"] == "/db/SDVE")

    assert sdvi["createPayload"]["INPUT_TYPE_EXFN"] == 0
    assert sdvi["confirmed"] is True
    assert set(sdvi["createPayload"]["ITEM"][0]) == {
        "OPT_DOF", "CE", "P1", "C1", "ALPHA1", "K0", "EXFN_PY",
        "EXFN_VY", "EXFN_DE", "EXFN_DC", "OPT_EXFN_CE", "EXFN_CE",
    }
    assert len(sdvi["createPayload"]["ITEM"]) == 6
    assert {
        key: sdve["createPayload"][key]
        for key in (
            "MATERIAL_TYPE", "SHEAR_AREA", "THICKNESS", "MULTIPL", "DIR",
            "FREQ", "STIFF_FACTOR", "DAMP_FACTOR", "REF_T", "LIMIT_DEF",
            "EFF_STIFF", "EQUI_DAMP", "OPT_MOUNT_STIFF", "MOUNT_STIFF",
            "OPT_KINETIC_FRIC", "KINETIC_FRIC",
        )
    } == {
        "MATERIAL_TYPE": "GR100", "SHEAR_AREA": 0.05, "THICKNESS": 0.02,
        "MULTIPL": 1, "DIR": "Dx", "FREQ": 0, "STIFF_FACTOR": 1,
        "DAMP_FACTOR": 1, "REF_T": 20, "LIMIT_DEF": 0.3, "EFF_STIFF": 0,
        "EQUI_DAMP": 0, "OPT_MOUNT_STIFF": True, "MOUNT_STIFF": 1200,
        "OPT_KINETIC_FRIC": False, "KINETIC_FRIC": 0,
    }
    assert sdve["confirmed"] is True


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


def test_live_case_fixture_marks_current_design_round_trips() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    confirmed = {
        case["endpoint"]: case["confirmed"]
        for case in cases
        if case["endpoint"] in {
            "/db/DCON", "/db/DSTL", "/db/LENG", "/db/MEMB",
            "/db/DCTL", "/db/LTSR", "/db/MBTP", "/db/WMAK",
        }
    }

    assert confirmed == {
        "/db/DCON": True,
        "/db/DSTL": False,
        "/db/LENG": True,
        "/db/MEMB": True,
        "/db/DCTL": True,
        "/db/LTSR": True,
        "/db/MBTP": True,
        "/db/WMAK": True,
    }


def test_live_case_fixture_marks_current_heat_source_round_trip() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    hsfc = next(case for case in cases if case["endpoint"] == "/db/HSFC")

    assert hsfc["confirmed"] is True
    assert hsfc["id"] == 92
    assert hsfc["needs"] == ["hsfc_seed"]


def test_live_case_fixture_explicitly_replaces_new_project_baselines() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    material = fixture["seeds"]["ltsr_material"]
    section = fixture["seeds"]["ltsr_section"]
    thickness = fixture["seeds"]["wmak_thickness"]

    assert material["endpoint"] == "/db/MATL"
    assert material["replaceExisting"] is True
    assert material["records"]["1"]["PARAM"][0]["DB"] == "S450"
    assert section["endpoint"] == "/db/SECT"
    assert section["replaceExisting"] is True
    assert thickness["endpoint"] == "/db/THIK"
    assert thickness["replaceExisting"] is True


def test_live_case_fixture_confirms_response_spectrum_load_on_both_products() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    splc = [case for case in cases if case["endpoint"] == "/db/SPLC"]

    assert [(case["products"], case["confirmed"]) for case in splc] == [
        (["civil"], True),
        (["gen"], True),
    ]


def test_live_case_fixture_splits_product_asymmetric_seismic_combination() -> None:
    """Keep Gen's accepted ST shape separate from Civil's manual-shaped RS probe."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seismic = [
        case for case in fixture["cases"]
        if case["endpoint"] == "/db/LCOM-SEISMIC"
    ]

    assert [
        (case["products"], case["confirmed"], case["createPayload"]["vCOMB"])
        for case in seismic
    ] == [
        (["gen"], True, [{"ANAL": "ST", "LCNAME": "DL", "FACTOR": 1.0}]),
        (["civil"], False, [{
            "ANAL": "RS", "LCNAME": "SPLC_LCOM_SEED", "FACTOR": 1.0,
        }]),
    ]
    assert seismic[1]["needs"] == ["lcom_seismic_splc"]
    assert seismic[0]["setup"] == [{"seed": "static_load_cases"}]
    assert seismic[1]["setup"] == [
        {"seed": "lcom_seismic_spfc"},
        {"seed": "lcom_seismic_splc"},
    ]
    assert fixture["seeds"]["lcom_seismic_splc"] == {
        "endpoint": "/db/SPLC",
        "records": {
            "1": {
                "NAME": "SPLC_LCOM_SEED", "DIR": "XY", "SCALE": 1.0,
                "PMFT": 1.0, "aFUNCNAME": ["SPFC_LCOM_SEED"],
            },
        },
    }
