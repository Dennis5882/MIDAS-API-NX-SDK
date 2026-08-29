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
    contracts = generator._contract_resource_surfaces()

    assert contracts
    for endpoint, surface in contracts.items():
        resource = resources[endpoint]
        assert resource["name"] == surface["name"]
        assert resource["products"] == surface["products"]
        assert resource["methods"] == surface["methods"]
        assert resource["contractManualChapter"] == surface["manualChapter"]


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
                        "when": {"field": "OPT_MODE", "equals": False},
                        "fields": [
                            {"key": "OPT_MODE", "type": "boolean", "requirement": "optional"},
                            {"key": "GENERAL", "type": "number", "requirement": "required"}
                        ],
                    },
                    {
                        "when": {"field": "OPT_MODE", "equals": True},
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
