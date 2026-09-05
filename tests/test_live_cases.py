"""The npm live harness must consume the current Python case fixture."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "schema" / "live-cases.json"


@pytest.mark.parametrize(
    "endpoint,code",
    [("/db/LLANch", "CHINA"), ("/db/SLANch", "CHINA"),
     ("/db/LLANid", "INDIA"), ("/db/LLANtr", "TRANS"),
     ("/db/LLANop", "KSCE-LSD15"), ("/db/SLAN", "KSCE-LSD15"),
     ("/db/SLANop", "KSCE-LSD15")],
)
def test_manual_lane_fixture_keeps_its_own_code_and_model_references(endpoint, code) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    case = next(c for c in fixture["cases"] if c["endpoint"] == endpoint)
    seed = fixture["seeds"][f"lane_code_{code}"]
    assert seed["records"]["1"]["CODE"] == code
    assert case["setup"] == [{"seed": f"lane_code_{code}"}]
    if endpoint in {"/db/LLANch", "/db/LLANid"}:
        assert "LL_NAME" not in case["createPayload"]
        assert case["createPayload"]["COMMON"]["LL_NAME"]
    if endpoint.startswith("/db/SLAN"):
        payload = case["createPayload"]
        items = payload.get("ITEMS", payload.get("LANE_ITEMS"))
        assert {p.get("NODE_KEY", p.get("NODE")) for p in items} <= {5, 6, 7, 8}


@pytest.mark.parametrize(
    "endpoint,seed_names",
    [
        ("/db/TDMT", ["tdmt_seed"]),
        ("/db/TDME", ["tdme_seed"]),
        ("/db/GSTP", ["spring_types"]),
        ("/db/THFC", ["thfc_seed", "thfc_force_seed"]),
        ("/db/SPLC", ["spfc_seed"]),
    ],
    ids=["creep-sequential-ids", "strength-sequential-id", "spring-sequential-ids",
         "time-history-two-functions", "spectrum-function-reference"],
)
def test_shared_fixture_includes_required_tier_seeds(endpoint, seed_names) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = [case for case in fixture["cases"] if case["endpoint"] == endpoint]
    assert cases
    for case in cases:
        assert case["setup"] == [{"seed": name} for name in seed_names]
        assert all(name in case["needs"] for name in seed_names)
        for name in seed_names:
            assert fixture["seeds"][name]["records"]


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

    assert fixture["version"] == 5
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
    # This used to assert an empty setup, which recorded the old emitter's
    # behaviour rather than the case's: /db/PNLD declares pnld_seed and the
    # Python runner has always built it. The npm harness gets it too now.
    assert pnld["needs"] == ["pnld_seed"]
    assert pnld["setup"] == [{"seed": "pnld_seed"}]


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


def test_no_ledger_entry_contradicts_its_own_level() -> None:
    """A `live_verified` entry's prose and its `level` must say the same thing.

    Both halves are edited by hand, on different lines, and a batch touches
    several entries at once - so an update can land on the neighbouring
    endpoint. That happened: `/db/HPCE` was raised to `write` while its own
    method text still ended "Not resolved as a fixture problem. Left at level:
    read", and `/db/THMS` kept `read` under a method describing a completed
    round trip that persisted `SCALEX` 1.0 to 1.5.

    Neither needs outside evidence to catch. The entry disagrees with itself.
    """

    says_read = re.compile(
        r"(?:left at level: read|remains read-level|stays read-level)", re.IGNORECASE
    )
    says_write = re.compile(
        r"(?:full write round trip confirmed|write-round-trip confirmed)", re.IGNORECASE
    )
    problems: list[str] = []

    def visit(node: object) -> None:
        if isinstance(node, dict):
            verified = node.get("live_verified")
            endpoint = node.get("endpoint")
            if endpoint and isinstance(verified, dict):
                method = verified.get("method", "")
                level = verified.get("level")
                if says_read.search(method) and level == "write":
                    problems.append(f"{endpoint}: method says read-level, level is write")
                if says_write.search(method) and level != "write":
                    problems.append(
                        f"{endpoint}: method describes a write round trip, level is {level!r}"
                    )
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(json.loads((ROOT / "docs" / "coverage.json").read_text(encoding="utf-8")))
    assert not problems, "\n".join(problems)


def test_unknown_endpoint_selection_is_refused_before_any_product_call() -> None:
    """`--endpoints` must reject a name the way `--tier` does.

    The filter is applied inside the tier loop, which runs after `/doc/NEW`
    has already discarded whatever the caller had open. A typo there used to
    leave the run with zero cases: the document was gone and nothing was
    tested. Both refusals must happen before the client is even built.
    """

    for arguments, expected in (
        (["--endpoints", "/db/NOPE"], "No live case for endpoint /db/NOPE"),
        (
            ["--tier", "extras5", "--endpoints", "/db/NODE"],
            "/db/NODE has no case in the selected tier(s)",
        ),
    ):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/live_crud_check.py",
                "--product",
                "gen",
                "--mapi-key",
                "not-a-real-key",
                *arguments,
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert expected in result.stderr, result.stderr
        # Nothing may have reached the product.
        assert "mapikey/verify" not in result.stderr


def test_both_harnesses_build_the_same_base_model() -> None:
    """The fixture must carry the model, not just the cases that attach to it.

    Python built the base model by calling typed resources with inline literals
    inside ``_seed_model``, so only Python could replay it. The npm harness
    starts from a genuinely empty ``/doc/NEW``, which is why thirteen cases
    confirmed here reported ``REGRESS`` there against preconditions no one had
    created. A base model only one harness can build is a hole in this file's
    claim to be the language-neutral source both read.
    """
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    steps = fixture["baseModel"]

    assert steps, "the fixture must carry the base model every case attaches to"
    for step in steps:
        assert step["endpoint"].startswith("/db/"), step
        assert step["method"] in {"POST", "PUT"}, step
        assert step["records"], f"{step['endpoint']}: a step with no records builds nothing"

    # Order is load-bearing: an element cannot reference a node, a material or a
    # section that a later step creates.
    order = [step["endpoint"] for step in steps]
    for earlier, later in (("/db/NODE", "/db/ELEM"),
                           ("/db/MATL", "/db/ELEM"),
                           ("/db/SECT", "/db/ELEM"),
                           ("/db/STLD", "/db/BODF")):
        assert order.index(earlier) < order.index(later), (
            f"{earlier} must be built before {later}"
        )


def test_the_npm_harness_reads_the_base_model_from_the_fixture() -> None:
    """It may replay the emitted steps and may not carry its own copy.

    A hand-written second copy is how the two harnesses would drift back apart,
    and a payload written into a harness rather than measured is the mistake
    this repository has paid for more than once.
    """
    source = (ROOT / "packages" / "typescript" / "scripts" / "live-crud.mjs").read_text(
        encoding="utf-8"
    )

    assert "fixture.baseModel" in source, "the npm harness must build the emitted base model"
    assert "buildBaseModel(client)" in source, "and must call it before running any case"

    built = source.index("await buildBaseModel(client);")
    first_case = source.index("for (const liveCase of cases)")
    assert built < first_case, "the base model must be built before the first case runs"


def test_every_declared_need_resolves_to_a_seed_or_a_stated_reason() -> None:
    """A need that resolves to nothing is worse than one that cannot be met.

    The npm harness used to receive only the seeds an emitter happened to
    export, and dropped the rest with no record, so a case ran with its setup
    silently shortened and failed exactly the way an SDK defect fails. Every
    name must land in one of two places: the seeds the fixture can replay, or
    the seeds it cannot, each with the reason it cannot.
    """
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seeds = set(fixture["seeds"])
    unsupported = fixture["unsupportedSeeds"]

    unresolved = {
        (case["endpoint"], name)
        for case in fixture["cases"]
        for name in case["needs"]
        if name not in seeds and name not in unsupported
    }
    assert not unresolved, f"needs resolving to nothing: {sorted(unresolved)}"

    for name, reason in unsupported.items():
        assert reason.strip(), f"{name} is unsupported without saying why"

    for case in fixture["cases"]:
        expected = [name for name in case["needs"] if name in unsupported]
        assert case["blockedSeeds"] == expected, case["endpoint"]


def test_a_seed_is_excluded_only_because_it_cannot_be_replayed() -> None:
    """The boundary is the harness's own vocabulary, not a hand-picked list.

    live-crud.mjs replays a prerequisite as a sequence of Assign POSTs, so a
    seed that reads state back or deletes a record cannot be expressed and
    every other seed can. An exclusion for any other reason is someone's
    convenience, and the count is here to make that visible.
    """
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    unsupported = fixture["unsupportedSeeds"]

    assert set(unsupported) == {"pjcf_unlock", "solid11_seed", "stage11_seed"}
    for name, reason in unsupported.items():
        assert "is not an Assign POST" in reason, f"{name}: {reason}"

    multi_step = {name for name, seed in fixture["seeds"].items() if "steps" in seed}
    assert multi_step, "a seed built from several POSTs must still be exported"


def test_the_npm_harness_blocks_a_case_it_cannot_seed() -> None:
    """It must refuse such a case, and must not read the refusal as a regression.

    scripts/live_crud_check.py calls a case whose seed step failed BLOCKED and
    exits 3, because that result says nothing about the endpoint under test.
    The npm harness had no such class, so a missing seed record was reported as
    a package regression on a confirmed case.
    """
    source = (ROOT / "packages" / "typescript" / "scripts" / "live-crud.mjs").read_text(
        encoding="utf-8"
    )
    support = (
        ROOT / "packages" / "typescript" / "scripts" / "live-harness-support.mjs"
    ).read_text(encoding="utf-8")

    assert "liveCase.blockedSeeds" in source, "the npm harness must read the blocked list"
    assert "fixture.unsupportedSeeds" in source, "and must report why the seed is missing"
    assert "classifyResult" in source and "exitCodeFor" in source

    # The two decisions Python already makes, in one place npm can test.
    assert 'return "BLOCK"' in support
    assert "result.confirmed && !result.blocked" in support


def test_the_npm_harness_pins_the_fixture_version() -> None:
    """A stale checkout must fail loudly, not build an older model in silence."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    source = (ROOT / "packages" / "typescript" / "scripts" / "live-crud.mjs").read_text(
        encoding="utf-8"
    )
    pinned = re.search(r"const EXPECTED_FIXTURE_VERSION = (\d+);", source)
    assert pinned, "live-crud.mjs must pin the fixture version it was written for"
    assert int(pinned.group(1)) == fixture["version"]


def test_a_hand_curated_base_seed_wins_a_name_collision() -> None:
    """One name exists in both places and they are not the same record.

    ``lcom_seismic_splc`` is a base-model seed holding the SPLC record, and
    also a tier seed step that creates SPFC *and* SPLC. Merging the exported
    tier seeds over the base ones replaced a record cases reference by name
    with a two-step composite, which duplicated the SPFC create for the one
    case that already spells out both halves. The hand-curated record wins,
    and a second collision must be looked at rather than merged.
    """
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seed = fixture["seeds"]["lcom_seismic_splc"]

    assert seed["endpoint"] == "/db/SPLC"
    assert "steps" not in seed, "the base-model record must survive the merge"
    assert set(seed["records"]) == {"1"}

    seismic = [case for case in fixture["cases"] if case["endpoint"] == "/db/LCOM-SEISMIC"]
    for case in seismic:
        seeds = [step["seed"] for step in case["setup"] if "seed" in step]
        assert len(seeds) == len(set(seeds)), f"{case['endpoint']} seeds a record twice"


def _live_crud_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "live_crud_check_under_test", ROOT / "scripts" / "live_crud_check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_case_whose_id_a_seed_already_owns_is_blocked_not_regressed() -> None:
    """A taken id says nothing about the endpoint, so it cannot be a regression.

    Confirmed live on Civil 2026-09-05: extras4's Civil-only lcom_seismic_splc
    seed creates /db/SPLC id 1 and extras5's Civil /db/SPLC case owns the same
    id, so selecting both tiers answered `Key Already Exist` for a shape both
    products accept whenever either tier runs alone. That printed REGRESS and
    exited 1 -- "treat as an SDK defect" -- for a collision inside the fixture.
    Asking for a different id is not the fix: this load-case family renumbers a
    requested key to the next free slot, so a case asking for 2 lands at 1 when
    the other tier was not selected.
    """
    live = _live_crud_module()

    class _Resource:
        ENDPOINT = "/db/FAKE"
        NAME = "Fake"
        METHODS = frozenset({"POST", "PUT", "DELETE"})

        @staticmethod
        def items(client=None):
            return {1: {"NAME": "taken by a seed"}}

        @staticmethod
        def create(records, client=None):
            raise AssertionError("a case must not POST over a record it does not own")

    case = live.Case(
        _Resource, {"NAME": "x"}, {"NAME": "y"},
        lambda payload: payload.get("NAME"), "x", "y",
        item_id=1, confirmed=True,
    )
    row = live._run_case(case, client=None)

    assert row["classification"] == live.BLOCKED
    assert row["ok"] is False
    assert "already exists" in row["steps"]["create"]["error"]
