"""Shadow-run guards for the contract-first npm resource generator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_typescript_sdk as generator  # noqa: E402


def test_contracted_resource_surfaces_match_the_legacy_sdk_anchor():
    """A Stage 3 switch is allowed only when it preserves generated output."""
    resources = {resource["endpoint"]: resource for resource in generator._load_resources()}
    contracts = generator._contract_resource_surfaces(set(resources))

    assert contracts
    for endpoint, surface in contracts.items():
        resource = resources[endpoint]
        assert resource["name"] == surface["name"]
        assert resource["products"] == surface["products"]
        assert resource["methods"] == surface["methods"]
        assert resource["contractManualChapter"] == surface["manualChapter"]


def test_contract_shadow_gate_covers_db_and_design_resources_only():
    assert generator._is_contract_shadow_resource("/db/NODE")
    assert generator._is_contract_shadow_resource("/DESIGN/RC/KDS-41-20-2022/DCO")
    assert not generator._is_contract_shadow_resource("/view/DISPLAY")


def test_resource_shadow_checks_documented_display_names_but_normalizes_dash_typography():
    resource = {
        "name": "Load Combinations - General",
        "products": ["gen"],
        "methods": ["GET"],
        "manual": [{"chapterFile": "13_DB_Load_Combinations.md"}],
    }
    surface = {
        "name": "Load Combinations – General",
        "products": ["gen"],
        "methods": ["GET"],
        "manualChapter": "13_DB_Load_Combinations.md",
    }
    assert generator._contract_resource_mismatches(resource, surface) == []

    surface["name"] = "/db/LCOM-GEN"
    assert generator._contract_resource_mismatches(resource, surface) == [
        "name: SDK has 'Load Combinations - General', contract has '/db/LCOM-GEN'"
    ]

    surface["methods"] = ["POST"]
    assert generator._contract_resource_mismatches(resource, surface) == [
        "name: SDK has 'Load Combinations - General', contract has '/db/LCOM-GEN'",
        "methods: SDK has ['GET'], contract has ['POST']"
    ]


def test_bodf_payload_comes_from_its_manual_contract():
    """The first static-load contract must not silently fall back to Python types."""
    resources = generator._load_resources()
    modules = generator._source_modules()
    resource_keys = {(resource["pythonModule"], resource["className"]) for resource in resources}
    type_keys = generator._collect_type_classes(modules, resource_keys)
    generator._attach_payload_types(resources, type_keys)

    contract_types, supplemental = generator._contract_payload_types(
        resources, generator._contract_payload_fields(), type_keys
    )
    bodf = next(resource for resource in resources if resource["endpoint"] == "/db/BODF")

    assert bodf["payloadTypeName"] == "SelfWeightPayload"
    fields = {
        field["key"]: field
        for field in contract_types[(bodf["pythonModule"], "SelfWeightPayload")]["fields"]
    }
    assert fields["LCNAME"]["requirement"] == "required"
    assert fields["GROUP_NAME"]["documentedDefault"] == ""
    assert fields["FV"] == {
        "key": "FV",
        "description": "Self-Weight Factor [X, Y, Z]",
        "type": "array",
        "items": {"type": "number"},
        "minItems": 3,
        "maxItems": 3,
        "requirement": "required",
        "documentedDefault": None,
        "documentedOptional": False,
        "safeToOmit": "unverified",
        "provenance": "manual",
    }
    assert "SelfWeightPayload" not in supplemental.get(bodf["pythonModule"], {})


def test_contract_variants_render_as_a_discriminated_union():
    rendered = "\n".join(
        generator._contract_payload_type(
            "VariantPayload",
            {
                "fields": [
                    {
                        "key": "OPT_MODE",
                        "type": "boolean",
                        "requirement": "optional",
                    }
                ],
                "variants": [
                    {
                        "when": [{"path": "OPT_MODE", "equals": False}],
                        "fields": [
                            {"key": "OPT_MODE", "type": "boolean", "requirement": "optional"},
                            {"key": "GENERAL", "type": "number", "requirement": "required"}
                        ],
                    },
                    {
                        "when": [{"path": "OPT_MODE", "equals": True}],
                        "fields": [
                            {"key": "OPTIMIZED", "type": "string", "requirement": "required"}
                        ],
                    },
                ],
            },
        )
    )

    assert "export type VariantPayload" in rendered
    assert "OPT_MODE: false;" in rendered
    assert "OPT_MODE: true;" in rendered
    assert "GENERAL: number;" in rendered
    assert "OPTIMIZED: string;" in rendered
    assert rendered.count("OPT_MODE?: boolean;") == 1


def test_contract_shared_variant_table_folds_into_the_branches_it_covers():
    """A multi-value condition is the manual's shared table, not a third branch.

    /db/FBLA documents one table for ``FLOOR_DIST_TYPE = 1`` and another for
    ``= 2``, then a third for ``= 1 or 2``. Emitting the third as its own union
    member would give two members matching ``FLOOR_DIST_TYPE: 1``. Its fields
    belong to both branches instead, which is what the heading says.
    """
    rendered = "\n".join(
        generator._contract_payload_type(
            "SharedPayload",
            {
                "fields": [{"key": "DIST", "type": "integer", "requirement": "required"}],
                "variants": [
                    {
                        "when": [{"path": "DIST", "equals": 1}],
                        "fields": [{"key": "ONLY_ONE", "type": "number", "requirement": "required"}],
                    },
                    {
                        "when": [{"path": "DIST", "equals": 2}],
                        "fields": [{"key": "ONLY_TWO", "type": "number", "requirement": "required"}],
                    },
                    {
                        "when": [{"path": "DIST", "in": [1, 2]}],
                        "fields": [{"key": "SHARED", "type": "string", "requirement": "required"}],
                    },
                ],
            },
        )
    )

    assert rendered.count("DIST: 1;") == 1
    assert rendered.count("DIST: 2;") == 1
    # The shared table contributes to both branches and forms none of its own.
    assert rendered.count("SHARED: string;") == 2
    assert "DIST: 1 | 2;" not in rendered
    assert rendered.count("ONLY_ONE: number;") == 1
    assert rendered.count("ONLY_TWO: number;") == 1


def test_a_variant_attaches_to_the_object_holding_its_discriminator():
    """A branch's fields are siblings of the field it gates on, at any depth.

    /db/SWIND and /db/SSEIS gate on PARAMETERS.INPUT_METHOD and
    PARAMETERS.PERIOD_METHOD; /db/PRES and /db/MCON on a member of an ITEMS
    element. Attaching those unions at the payload root published WIND_SPEED,
    EXP_CATEGORY and PERIOD_APPR_X as top-level members - where the server does
    not look, the same defect the /db/BTMP nesting fix corrected one level down.
    """
    rendered = "\n".join(
        generator._contract_payload_type(
            "NestedGatePayload",
            {
                "fields": [
                    {
                        "key": "PARAMETERS",
                        "type": "object",
                        "requirement": "required",
                        "properties": [
                            {"key": "INPUT_METHOD", "type": "integer", "requirement": "required"}
                        ],
                    }
                ],
                "variants": [
                    {
                        "when": [{"path": "PARAMETERS.INPUT_METHOD", "equals": 0}],
                        "fields": [
                            {"key": "WIND_SPEED", "type": "number", "requirement": "required"}
                        ],
                    },
                    {
                        "when": [{"path": "PARAMETERS.INPUT_METHOD", "equals": 1}],
                        "fields": [
                            {"key": "EXP_CATEGORY", "type": "integer", "requirement": "required"}
                        ],
                    },
                ],
            },
        )
    )

    # The union sits inside PARAMETERS, so the branch fields are indented past
    # it rather than declared beside it.
    parameters = rendered.index("PARAMETERS:")
    assert rendered.index("WIND_SPEED") > parameters
    assert "    } & (" in rendered, rendered
    # And the payload root is a plain object: nothing was intersected there.
    assert not rendered.rstrip().endswith(");")
    assert rendered.rstrip().endswith("};")


def test_a_variant_gating_inside_an_array_attaches_to_the_element():
    """/db/PRES's FACE_EDGE_TYPE lives in ITEMS[], so FORCES does too.

    The manual numbers the branch rows `(11)`, continuing the ITEMS numbering,
    and the section's own JSON request example sends FORCES inside the array
    entry.
    """
    rendered = "\n".join(
        generator._contract_payload_type(
            "ItemGatePayload",
            {
                "fields": [
                    {
                        "key": "ITEMS",
                        "type": "array",
                        "requirement": "required",
                        "properties": [
                            {"key": "KIND", "type": "string", "requirement": "required"}
                        ],
                    }
                ],
                "variants": [
                    {
                        "when": [{"path": "ITEMS.KIND", "equals": "A"}],
                        "fields": [{"key": "ONLY_A", "type": "number", "requirement": "required"}],
                    },
                    {
                        "when": [{"path": "ITEMS.KIND", "equals": "B"}],
                        "fields": [{"key": "ONLY_B", "type": "number", "requirement": "required"}],
                    },
                ],
            },
        )
    )

    # The intersection has to be parenthesised inside Array<>, or the union
    # would bind to the array rather than to its element type.
    assert "ITEMS: Array<({" in rendered, rendered
    assert "ONLY_A: number;" in rendered
    assert rendered.rstrip().endswith("};")


def test_a_multi_value_table_overlapping_nothing_is_a_branch_not_a_shared_table():
    """Overlap decides it, not the plural.

    /db/PRES states one table for ``FACE_EDGE_TYPE = "FACE" or "PRES"`` and
    another for ``= "EDGE"``. Neither covers the other, so both are branches.
    Reading every multi-value table as the /db/FBLA shared kind folded this one
    into branches it does not cover and then dropped it: /db/PRES lost FORCES,
    /db/MVHL lost the South African VEH_ZA, /db/TDME lost four of six.
    """
    rendered = "\n".join(
        generator._contract_payload_type(
            "DisjointPayload",
            {
                "fields": [
                    {
                        "key": "KIND",
                        "type": "string",
                        "requirement": "required",
                        "enum": ["FACE", "PRES", "EDGE"],
                    }
                ],
                "variants": [
                    {
                        "when": [{"path": "KIND", "in": ["FACE", "PRES"]}],
                        "fields": [{"key": "FORCES", "type": "number", "requirement": "required"}],
                    },
                    {
                        "when": [{"path": "KIND", "equals": "EDGE"}],
                        "fields": [{"key": "EDGES", "type": "number", "requirement": "required"}],
                    },
                ],
            },
        )
    )

    assert '"FACE" | "PRES";' in rendered
    assert "FORCES: number;" in rendered
    assert "EDGES: number;" in rendered
    # Every enum member is covered, so no residual `?: never` member is needed.
    assert "?: never" not in rendered


def test_a_variant_gating_on_a_field_the_contract_never_declares_stays_at_the_root():
    """/db/MVLD's LOAD_MODEL is declared inside a sibling variant, not in fields.

    Where the contract says nothing, the branch is left where it already was
    rather than given an invented home - no permitted source states which
    object holds it.
    """
    rendered = "\n".join(
        generator._contract_payload_type(
            "UndeclaredGatePayload",
            {
                "fields": [{"key": "TYPE", "type": "integer", "requirement": "required"}],
                "variants": [
                    {
                        "when": [{"path": "LOAD_MODEL", "equals": 2}],
                        "fields": [{"key": "EXTRA", "type": "number", "requirement": "required"}],
                    }
                ],
            },
        )
    )

    assert rendered.rstrip().endswith(");")
    assert "LOAD_MODEL: 2;" in rendered

def test_contract_fixed_length_arrays_render_as_tuples():
    rendered = generator._contract_field_type(
        {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
        "  ",
    )

    assert rendered == "[number, number, number]"


def test_contract_applies_when_renders_as_member_jsdoc():
    rendered = "\n".join(
        generator._contract_payload_type(
            "ConditionalPayload",
            {
                "fields": [
                    {"key": "BATCH", "type": "boolean", "requirement": "optional"},
                    {
                        "key": "BATCH_LIST",
                        "type": "array",
                        "items": {"type": "string"},
                        "requirement": "conditional",
                        "description": "Output group names.",
                        "appliesWhen": [{"path": "BATCH", "equals": True}],
                    },
                ]
            },
        )
    )

    assert "/** Output group names. Applies when BATCH = true. */" in rendered
    assert "BATCH_LIST?: Array<string>;" in rendered


def test_conflicting_legacy_payload_aliases_receive_distinct_contract_types():
    """One reused Python TypedDict must not overwrite another endpoint contract."""
    resources = generator._load_resources()
    modules = generator._source_modules()
    resource_keys = {(resource["pythonModule"], resource["className"]) for resource in resources}
    type_keys = generator._collect_type_classes(modules, resource_keys)
    generator._attach_payload_types(resources, type_keys)
    contract_fields = generator._contract_payload_fields()

    contract_types, supplemental = generator._contract_payload_types(
        resources, contract_fields, type_keys
    )
    by_endpoint = {resource["endpoint"]: resource for resource in resources}
    dynf = by_endpoint["/db/DYNF"]

    assert by_endpoint["/db/DYFG"]["payloadTypeName"] == "RailwayDynamicFactorPayload"
    assert dynf["payloadTypeName"] == "RailwayDynamicFactorByElementPayload"
    assert contract_types[(dynf["pythonModule"], "RailwayDynamicFactorPayload")] == contract_fields["/db/DYFG"]
    assert supplemental[dynf["pythonModule"]]["RailwayDynamicFactorByElementPayload"] == contract_fields["/db/DYNF"]

    rendered = generator._render_types(modules, type_keys, contract_types, supplemental)
    assert "export interface RailwayDynamicFactorPayload" in rendered
    assert "export interface RailwayDynamicFactorByElementPayload" in rendered


def test_a_contract_with_unmerged_tables_does_not_become_a_payload_type():
    """/db/THIK is contracted, and its payload still comes from the fallback.

    Its manual section has one variant table nobody could merge, so the
    contract records the gap instead of claiming a complete field list.
    Generating a published payload type from that list would narrow
    ThicknessPayload onto fields the manual documents elsewhere, and break
    callers who set them.
    """
    fields = generator._contract_payload_fields()

    assert "/db/THIK" not in fields
    assert "/db/BODF" in fields, "an unqualified contract must still supply its payload"


def test_a_contract_surface_outranks_the_python_class():
    """The contract is the source; the Python class answers what it does not.

    Before the generator was inverted it iterated `DbResource` subclasses and
    let a contract correct the facts it owned, so a contract could never do more
    than annotate something Python had already declared. The precedence lives in
    one function now, and this pins which way round it goes.
    """

    surface = {
        "className": "FromContract",
        "exportName": "fromContract",
        "modulePath": ["db", "fromContract"],
        "name": "From the contract",
        "products": ["gen"],
        "methods": ["GET"],
    }
    fallback = {
        "className": "FromPython",
        "exportName": "fromPython",
        "modulePath": ["db", "fromPython"],
        "name": "From Python",
        "products": ["civil", "gen"],
        "methods": ["DELETE", "GET", "POST", "PUT"],
    }

    assert generator._resource_identity(surface, fallback) == surface
    # An endpoint no contract covers keeps every Python fact.
    assert generator._resource_identity(None, fallback) == fallback
    # A partial surface takes over only what it states.
    partial = generator._resource_identity({"name": "Renamed"}, fallback)
    assert partial["name"] == "Renamed"
    assert partial["className"] == "FromPython"


def test_a_contract_only_resource_needs_no_python_class():
    """A surface that states everything stands without a Python class at all.

    This is the capability the migration is for: today every contracted
    endpoint also has a `DbResource` subclass, so nothing exercises it in the
    real tree, and an untested path is how a migration quietly stops being
    possible.
    """

    surface = {
        "className": "ContractOnly",
        "exportName": "contractOnly",
        "modulePath": ["db", "contractOnly"],
        "name": "Contract only",
        "products": ["gen"],
        "methods": ["GET"],
    }
    assert generator._resource_identity(surface, None) == surface


def test_an_identity_nobody_supplies_is_refused_rather_than_guessed():
    """A missing name is a contract defect, not something to invent."""

    import pytest

    with pytest.raises(KeyError, match="className"):
        generator._resource_identity({"name": "No class name"}, None)

def test_a_field_required_only_in_one_branch_is_not_required_of_every_payload():
    """`requirement: required` plus an `appliesWhen` is a branch's requirement.

    Typed unconditionally required it made `/db/CCFC` demand `COEF` (only under
    TYPE="CONST") alongside `SCALE_FACTOR` and `ITEM` (only under TYPE="USER"),
    so no caller could satisfy the type without sending fields their own branch
    does not have. 49 fields across nine contracts were in that state. The
    condition moves into the doc comment, which is where a requiredness
    TypeScript cannot express belongs.
    """

    rendered = "\n".join(
        generator._contract_payload_type(
            "BranchPayload",
            {
                "fields": [
                    {"key": "TYPE", "type": "string", "requirement": "required"},
                    {
                        "key": "COEF",
                        "type": "number",
                        "requirement": "required",
                        "appliesWhen": [{"path": "TYPE", "equals": "CONST"}],
                    },
                    {
                        "key": "DEN",
                        "type": "number",
                        "requirement": "required",
                        "appliesWhen": [{"path": "P_TYPE", "in": [2, 3]}],
                    },
                ]
            },
        )
    )
    assert "TYPE: string;" in rendered
    assert "COEF?: number;" in rendered
    assert 'Required when TYPE = "CONST".' in rendered
    # `in` is the form the schema has for a field two branch tables document.
    assert "DEN?: number;" in rendered
    assert "Required when P_TYPE is 2 or 3." in rendered

