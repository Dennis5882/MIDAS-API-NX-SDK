"""Targeted live checks requested by the MIDAS-API manual maintainers.

Each probe starts from the published manual example and changes precisely one
field.  This is deliberately separate from the SDK CRUD fixture: the purpose
is to measure documentation contradictions, including a server accepting an
unknown field but silently ignoring it.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import harness_save_path
from live_crud_check import _seed_model

from midas_nx import doc
from midas_nx.client import MidasClient
from midas_nx.design.steel_kds import MemberAssignment


def _raw(client: MidasClient, method: str, endpoint: str,
         body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client._session.request(  # noqa: SLF001 - evidence needs HTTP status
        method, client.base_url + endpoint,
        headers={"Content-Type": "application/json", "MAPI-Key": client.mapi_key},
        json=body, timeout=client.timeout,
    )
    try:
        parsed = response.json()
    except ValueError:
        parsed = {"text": response.text}
    return {"status": response.status_code, "body": parsed}


def _empty_members(client: MidasClient) -> dict:
    return MemberAssignment.items(client=client)


def memb_selection_typo(client: MidasClient, checkpoint: str) -> dict:
    """Request 20260918 A-1: ``SELETION_TYPE`` vs ``SELECTION_TYPE``.

    Source payload: MIDAS-API 15_OPE.md, /ope/MEMB English Request Body.
    Elements 2 and 3 are the shared scratch model's collinear beams, replacing
    the article's model-specific 640 and 692 ids.
    """
    doc.new_project(client=client)
    _seed_model(client)
    baseline = {
        "ASSIGN_TYPE": "MANUAL", "SELECTION_TYPE": "SELECTION",
        "ELEM_LIST": [2, 3], "ALLOW_SINGLE": False,
    }
    accepted = client.request("POST", "/ope/MEMB", {"Argument": baseline})
    baseline_read = _empty_members(client)

    # A saved disposable model prevents /doc/NEW from raising NX's save dialog.
    doc.save_as(checkpoint, client=client)
    doc.new_project(client=client)
    _seed_model(client)
    typo = dict(baseline)
    typo["SELETION_TYPE"] = typo.pop("SELECTION_TYPE")
    variant = client.request("POST", "/ope/MEMB", {"Argument": typo})
    variant_read = _empty_members(client)
    return {"baseline": accepted, "baselineGet": baseline_read,
            "variant": variant, "variantGet": variant_read}


def sseis_code_space(client: MidasClient, checkpoint: str) -> dict:
    """Request 20260918 A-2, from 06_DB_Static_Loads.md's KDS example."""
    payload = {
        "SEIS_CODE": "KDS(41-17-00:2019)", "DESC": "X seismic",
        "SCALE_FACTOR_X": 1.0, "SCALE_FACTOR_Y": 0.0,
        "ACCIDENT_ECCEN_X": 0, "ACCIDENT_ECCEN_Y": 2,
        "ACCIDENT_TORSION": True,
        "PARAMETERS": {"SEIS_ZONE": 0, "EPA": 0.22, "SITE_CLASS": 1,
                       "FA": 1.0, "FV": 1.4, "SDS": 0.2933, "SD1": 0.1467,
                       "SEIS_USE_GROUP": 1, "IMPORTANCE_FACTOR": 1.5,
                       "PERIOD_METHOD": 1, "PERIOD_APPR_X": 1.2,
                       "PERIOD_APPR_Y": 1.0, "RESPONSE_MOD_FACTOR_X": 5.0,
                       "RESPONSE_MOD_FACTOR_Y": 5.0},
    }
    doc.new_project(client=client)
    _seed_model(client)
    baseline = client.request("POST", "/db/SSEIS", {"Assign": {1: payload}})
    baseline_get = client.request("GET", "/db/SSEIS/1")
    doc.save_as(checkpoint, client=client)
    doc.new_project(client=client)
    _seed_model(client)
    spaced = dict(payload, SEIS_CODE="KDS(41-17-00: 2019)")
    variant = client.request("POST", "/db/SSEIS", {"Assign": {1: spaced}})
    variant_get = client.request("GET", "/db/SSEIS/1")
    return {"baseline": baseline, "baselineGet": baseline_get,
            "variant": variant, "variantGet": variant_get}


def _story_payload() -> dict[str, Any]:
    common = {
        "WIND_FLOOR_WIDTH_X": 36, "WIND_FLOOR_WIDTH_Y": 27.6,
        "WIND_CENTER_X": 18, "WIND_CENTER_Y": 13.8,
        "WIND_ECCENT_X": 5.4, "WIND_ECCENT_Y": 4.14,
        "SEIS_ACC_ECCENT_X": 1.8, "SEIS_ACC_ECCENT_Y": 1.38,
        "SEIS_INHERENT_ECCENT_X": 0, "SEIS_INHERENT_ECCENT_Y": 0,
        "SEIS_TORSIONAL_AMP_FACTOR_X": 1, "SEIS_TORSIONAL_AMP_FACTOR_Y": 1,
    }
    return {"Assign": {
        1: dict(common, STORY_NAME="1F", STORY_LEVEL=0, bFLOOR_DIAPHRAGM=False),
        2: dict(common, STORY_NAME="2F", STORY_LEVEL=5, bFLOOR_DIAPHRAGM=True,
                WIND_FLOOR_WIDTH_Y=29.1, WIND_CENTER_Y=14.55,
                WIND_ECCENT_Y=4.365, SEIS_ACC_ECCENT_Y=1.455),
    }}


def _user_sseis_payload(field: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "SEIS_CODE": "USER TYPE", "DESC": "", "SCALE_FACTOR_X": 1,
        "SCALE_FACTOR_Y": 1, "ACCIDENT_ECCEN_X": 0,
        "ACCIDENT_ECCEN_Y": 0, "ACCIDENT_TORSION": False,
        "SEISMIC_FORCE": [
            {"STORY_NAME": "2F", "FORCE_X": 1250.5, "FORCE_Y": 1180.75},
        ],
    }
    record[field] = True
    return {"Assign": {1: record}}


def sseis_torsion_typos(client: MidasClient, checkpoint: str,
                        extension: str) -> dict:
    """Request 20260918 B-1: normal and two documented typo spellings."""
    results: dict[str, Any] = {}
    for index, field in enumerate(("INHERENT_TORSION", "IINHERENT_TORSION",
                                    "NHERENT_TORSION")):
        doc.new_project(client=client)
        _seed_model(client)
        _raw(client, "POST", "/db/STOR", _story_payload())
        results[field] = {
            "post": _raw(client, "POST", "/db/SSEIS", _user_sseis_payload(field)),
            "get": _raw(client, "GET", "/db/SSEIS/1"),
        }
        if index < 2:
            # The extension is the product's own: /doc/SAVEAS rejects the
            # other product's spelling, and a guard save that never lands
            # leaves the next /doc/NEW to raise a save-changes dialog, which
            # blocks the whole API session until a human dismisses it.
            doc.save_as(f"{checkpoint}-{index}.{extension}", client=client)
    return results


def _seed_tendon_element_model(client: MidasClient, element_start: int) -> dict[str, Any]:
    """Build the documented TDNA example's 30 m element chain.

    The geometry and element ids mirror the official online TDNA example.  A
    documented steel material is added as id 2 for the official TDNT Magura
    property; the shared base model already owns material and section id 1.
    """
    _seed_model(client)
    node_start = element_start * 10
    setup = {
        "steelMaterial": _raw(client, "POST", "/db/MATL", {"Assign": {2: {
            "TYPE": "STEEL", "NAME": "SS400", "bMASS_DENS": False,
            "DAMP_RAT": 0.02, "HE_SPEC": 0, "HE_COND": 0, "PLMT": 0,
            "P_NAME": "", "PARAM": [{"P_TYPE": 1, "STANDARD": "KS21(S)",
                                        "CODE": "", "DB": "SS400",
                                        "bELAST": False}],
        }}}),
        "nodes": _raw(client, "POST", "/db/NODE", {"Assign": {
            node_start + index: {"X": index, "Y": 10, "Z": 0}
            for index in range(31)
        }}),
        "elements": _raw(client, "POST", "/db/ELEM", {"Assign": {
            element_start + index: {
                "TYPE": "BEAM", "MATL": 1, "SECT": 1,
                "NODE": [node_start + index, node_start + index + 1],
            }
            for index in range(30)
        }}),
        "tendonGroup": _raw(client, "POST", "/db/TDGR", {
            "Assign": {1: {"NAME": "TGR1"}},
        }),
        "tendonProperty": _raw(client, "POST", "/db/TDNT", {"Assign": {1: {
            "NAME": "In_Pre_Magura", "TYPE": "INTERNAL", "MATL": 2,
            "AREA": 0.00504, "D_AREA": 0.0152, "RM": 0, "RV": 45,
            "US": 1860000, "YS": 1570000, "LT": "PRE",
        }}}),
    }
    return setup


def _tdna_2d_round_payload() -> dict[str, Any]:
    """Official 2D Round/Element example from article 35954555962137."""
    return {
        "NAME": "2D/Round/Element", "TDN_PROP": 1,
        "ELEM": list(range(1201, 1231)), "BELENG": 0, "ELENG": 0,
        "CURVE": "ROUND", "INPUT": "2D", "TDN_GRUP": 1,
        "LENG_OPT": "AUTO2", "bTP": False, "DeBondBLEN": 0.2,
        "DeBondELEN": 0.2, "SHAPE": "ELEMENT", "INS_PT": "END-I",
        "INS_ELEM": 1201, "AXIS_IJ": "I-J", "XAR_ANGLE": 0,
        "bPJ": True, "OFF_YZ": [0, 0],
        "PROFY": [
            {"PT": [0, -0.5], "RADIUS": 0, "OPT": "LEFT", "ANGLE": 1,
             "HEIGHT": 1, "RADIUS2": 20},
            {"PT": [15, -0.5], "RADIUS": 20, "OPT": "NONE"},
            {"PT": [30, -0.5], "RADIUS": 0, "OPT": "RIGHT", "ANGLE": 1,
             "HEIGHT": 1, "RADIUS2": 20},
        ],
        "PROFZ": [
            {"PT": [0, -0.6], "RADIUS": 0, "OPT": "LEFT", "ANGLE": 1,
             "HEIGHT": 1, "RADIUS2": 20, "bBOTZ": False},
            {"PT": [15, -0.6], "RADIUS": 20, "OPT": "NONE",
             "bBOTZ": False},
            {"PT": [30, -0.6], "RADIUS": 0, "OPT": "RIGHT", "ANGLE": 1,
             "HEIGHT": 1, "RADIUS2": 20, "bBOTZ": False},
        ],
    }


def _tdna_3d_round_payload() -> dict[str, Any]:
    """Official 3D Round/Element example from article 35954555962137."""
    return {
        "NAME": "3D/Round/Element", "TDN_PROP": 1,
        "ELEM": list(range(1401, 1431)), "BELENG": 0, "ELENG": 0,
        "CURVE": "ROUND", "INPUT": "3D", "TDN_GRUP": 1,
        "LENG_OPT": "AUTO2", "bTP": True, "CNT": 10,
        "DeBondBLEN": 0.5, "DeBondELEN": 0.5, "SHAPE": "ELEMENT",
        "INS_PT": "END-I", "INS_ELEM": 1401, "AXIS_IJ": "I-J",
        "XAR_ANGLE": 0, "bPJ": True, "OFF_YZ": [0, -0.6],
        "PROF": [
            {"PT": [0, -0.5, 0], "bFIX": False, "RADIUS": 0},
            {"PT": [15, -0.5, 0], "bFIX": False, "RADIUS": 20},
            {"PT": [30, -0.5, 0], "bFIX": False, "RADIUS": 0},
        ],
    }


def _tdna_radius_cases() -> list[tuple[str, int, dict[str, Any]]]:
    """Return two official baselines and their one-field type variants."""
    two_d = _tdna_2d_round_payload()
    two_d_bool = copy.deepcopy(two_d)
    two_d_bool["PROFY"][1]["RADIUS"] = False
    three_d = _tdna_3d_round_payload()
    three_d_array = copy.deepcopy(three_d)
    three_d_array["PROF"][1]["RADIUS"] = [0, 20]
    return [
        ("2d-number", 1201, two_d),
        ("2d-boolean", 1201, two_d_bool),
        ("3d-number", 1401, three_d),
        ("3d-array", 1401, three_d_array),
    ]


def tdna_radius_types(client: MidasClient, checkpoint: str,
                      extension: str) -> dict[str, Any]:
    """Request 20260918 A-3: numeric, Boolean and array RADIUS values."""
    results: dict[str, Any] = {}
    for label, element_start, payload in _tdna_radius_cases():
        doc.new_project(client=client)
        setup = _seed_tendon_element_model(client, element_start)
        results[label] = {
            "setup": setup,
            "post": _raw(client, "POST", "/db/TDNA", {"Assign": {1: payload}}),
            "get": _raw(client, "GET", "/db/TDNA/1"),
        }
        doc.save_as(f"{checkpoint}-{label}.{extension}", client=client)
    return results


def _matd_payload(**extra: Any) -> dict[str, Any]:
    """Documented MATD PUT shape, adapted to the scratch C24 material."""
    payload: dict[str, Any] = {
        "TYPE": "CONC", "NAME": "C24",
        "DATA1": {"CODENAME": "KS01(RC)", "CODEMATLNAME": "C24"},
        "REBAR_CODENAME": "", "MAINREBAR_REBARNAME": "",
        "SUBREBAR_REBARNAME": "", "MAINREBAR_B_FY": 500000,
        "SUBREBAR_B_FY": 600000,
    }
    payload.update(extra)
    return payload


def _spfc_b2_payload() -> dict[str, Any]:
    """Documented response-spectrum function used by the SPLC example."""
    return {
        "NAME": "SPFC_B2", "iTYPE": 2, "iMETHOD": 0, "SCALE": 1,
        "GRAV": 9.806, "DRATIO": 0.05, "DESC": "",
        "aFUNC": [
            {"PERIOD": 0.1, "VALUE": 0.5},
            {"PERIOD": 0.5, "VALUE": 1},
            {"PERIOD": 1, "VALUE": 0.3},
        ],
    }


def _splc_along_payload(along: float) -> dict[str, Any]:
    """Official SPLC base shape plus its schema-only ALONG member."""
    return {
        "NAME": "SPLC_B2", "DIR": "XY", "ANGLE": 0, "SCALE": 1,
        "PMFT": 1, "bDAMP": False, "INTERP": "LOG", "DESC": "",
        "COMTYPE": "CQC", "bADDSIGN": True, "iSIGNTYPE": 0,
        "bMODE": True, "aFUNCNAME": ["SPFC_B2"],
        "aUSEMODE": [
            {"bUSE": True, "MSFACTOR": 1},
            {"bUSE": True, "MSFACTOR": 1},
            {"bUSE": True, "MSFACTOR": 1},
        ],
        "bACCECC": True, "bACCECC_AUTO": False, "ACCECC_PERCENT": 5,
        "bACCECC_CONSIDER_GL": False,
        "bACCECC_MINIMUM_TORSION": False,
        "aACCECC_ECCEN_LIST": [
            {"STORY": "2F", "CROSS": 1.5, "ALONG": along},
        ],
    }


def missing_specification_fields(client: MidasClient, checkpoint: str,
                                 extension: str, product: str) -> dict[str, Any]:
    """Request 20260918 B-2: prove four schema-only fields by round trip."""
    results: dict[str, Any] = {"MATD": {}}
    matd_cases = (
        ("baseline", {}),
        ("bSERVCHECK", {"bSERVCHECK": True}),
        ("dSHORTTERM", {"dSHORTTERM": 1.25}),
        ("dLONGTERM", {"dLONGTERM": 1.5}),
        ("combined", {"bSERVCHECK": True, "dSHORTTERM": 1.25,
                      "dLONGTERM": 1.5}),
    )
    for label, extra in matd_cases:
        doc.new_project(client=client)
        _seed_model(client)
        results["MATD"][label] = {
            "put": _raw(client, "PUT", "/db/MATD", {
                "Assign": {1: _matd_payload(**extra)},
            }),
            "get": _raw(client, "GET", "/db/MATD/1"),
        }
        doc.save_as(f"{checkpoint}-matd-{label}.{extension}", client=client)

    if product == "gen":
        doc.new_project(client=client)
        _seed_model(client)
        setup = {
            "story": _raw(client, "POST", "/db/STOR", _story_payload()),
            "spectrumFunction": _raw(client, "POST", "/db/SPFC", {
                "Assign": {1: _spfc_b2_payload()},
            }),
        }
        created = _raw(client, "POST", "/db/SPLC", {
            "Assign": {1: _splc_along_payload(2.5)},
        })
        created_get = _raw(client, "GET", "/db/SPLC/1")
        updated = _raw(client, "PUT", "/db/SPLC", {
            "Assign": {1: _splc_along_payload(3.5)},
        })
        updated_get = _raw(client, "GET", "/db/SPLC/1")
        results["SPLC"] = {
            "setup": setup, "post": created, "postGet": created_get,
            "put": updated, "putGet": updated_get,
        }
        doc.save_as(f"{checkpoint}-splc.{extension}", client=client)
    else:
        results["SPLC"] = {
            "skipped": "ALONG belongs to the manual's GEN NX-only accidental-eccentricity block",
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("gen", "civil"), required=True)
    parser.add_argument("--case", choices=("a1", "a2", "a3", "b1", "b2"),
                        default="a1")
    parser.add_argument("--out", required=True)
    harness_save_path.add_arguments(parser, waivable=False)
    args = parser.parse_args()
    harness_save_path.require(parser, args)
    client = MidasClient(product=args.product, timeout=60)
    extension = harness_save_path.PRODUCT_EXTENSION[args.product]
    # The stem rather than a finished path: this harness writes a checkpoint
    # per probe, each with its own suffix, and those files are the evidence.
    checkpoint = harness_save_path.checkpoint_prefix(
        args.save_dir, f"manual-feedback-{args.case}", args.product,
    )
    doc.save_as(f"{checkpoint}-before.{extension}", client=client)
    if args.case == "a1":
        result = memb_selection_typo(client, f"{checkpoint}-baseline.{extension}")
    elif args.case == "a2":
        result = sseis_code_space(client, f"{checkpoint}-baseline.{extension}")
    elif args.case == "a3":
        result = tdna_radius_types(client, checkpoint, extension)
    elif args.case == "b1":
        result = sseis_torsion_typos(client, checkpoint, extension)
    else:
        result = missing_specification_fields(
            client, checkpoint, extension, args.product,
        )
    doc.save_as(f"{checkpoint}-after.{extension}", client=client)
    doc.new_project(client=client)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
