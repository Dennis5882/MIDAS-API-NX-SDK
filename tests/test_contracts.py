"""Guards for the language-neutral endpoint contracts under contracts/.

Two things are being protected here.

The first is the contracts themselves: they validate against their JSON Schema,
their cross-references resolve, and nothing declared ``product_crash_risk``
sits there without a rule that does something about it.

The second is the reason the contracts exist. ``/db/NMAS``'s crash workaround
was implemented in Python on 2026-07-29 and the npm package shipped a month
later, on 2026-08-26, without it - not through carelessness but because the
workaround is behaviour inside ``NodalMass.create()``, and the Python-to-npm
generator only ever carried metadata and docstrings across. Any caller reaching
``/db/NMAS`` through the npm SDK could still hang and kill a live NX session.
The rule now lives in ``contracts/endpoints/db-nmas.yaml``, and these tests plus
``scripts/validate_contracts.py`` are what make an implementation that ignores
it fail rather than ship.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from midas_nx.db.static_loads import NodalMass

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
ENDPOINT_DIR = CONTRACTS / "endpoints"
RISKS_FILE = CONTRACTS / "safety" / "known-product-risks.yaml"
TS_RESOURCES = ROOT / "schema" / "typescript-resources.json"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _contracts() -> dict[str, dict]:
    return {path.stem: _load(path) for path in sorted(ENDPOINT_DIR.glob("*.yaml"))}


def _normalization_values(contract: dict) -> dict:
    values: dict = {}
    for rule in contract.get("sdkRules", []):
        if rule["kind"] == "normalize_defaults":
            values.update(rule["values"])
    return values


def test_validator_passes():
    """The whole contract suite validates, including SDK parity.

    Run as a subprocess so the test exercises exactly what CI runs.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_contracts.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_contract_declares_a_manual_source():
    for name, contract in _contracts().items():
        manual = contract["source"]["manual"]
        if manual["status"] == "documented":
            assert manual.get("chapterFile"), f"{name} claims a manual source with no chapter"
            assert manual.get("section"), f"{name} claims a manual source with no section"
        else:
            # A contract may depart from the manual - the manual has been wrong
            # about field names, defaults and product support - but it must say
            # why, so a later manual re-sync cannot quietly overwrite the
            # correction.
            assert manual.get("justification", "").strip(), (
                f"{name} has manual status {manual['status']!r} without a justification"
            )


def test_crash_risk_operations_carry_a_mitigation_and_a_rule():
    for name, contract in _contracts().items():
        rule_methods = {
            method for rule in contract.get("sdkRules", []) for method in rule["appliesTo"]
        }
        for operation in contract["operations"]:
            if operation["risk"] != "product_crash_risk":
                continue
            assert operation.get("mitigation") not in (None, "none"), (
                f"{name} {operation['method']} is product_crash_risk with no mitigation"
            )
            assert operation["method"] in rule_methods, (
                f"{name} {operation['method']} is product_crash_risk but no sdkRule applies"
            )
            assert contract.get("knownDefects"), (
                f"{name} {operation['method']} is product_crash_risk but references no "
                f"entry in {RISKS_FILE.name}"
            )


def test_unsafe_optional_fields_are_covered_by_a_rule():
    """documentedOptional and safeToOmit must not be allowed to collapse.

    A field the manual calls optional that is not actually safe to omit is the
    single most dangerous shape in this API, because a caller who reads the
    documentation and follows it is the one who gets hurt. Every such field has
    to be covered by a rule that fixes the payload before it is sent.
    """
    for name, contract in _contracts().items():
        covered = {
            field
            for rule in contract.get("sdkRules", [])
            if rule["kind"] in ("normalize_defaults", "reject_request")
            for field in rule.get("fields", [])
        }
        for field in contract.get("fields", []):
            if field["safeToOmit"] or not field["documentedOptional"]:
                continue
            assert field["key"] in covered, (
                f"{name}: {field['key']} is documented optional but is not safe to "
                f"omit, and no sdkRule covers it"
            )
            assert field.get("omissionEffect", "").strip(), (
                f"{name}: {field['key']} is not safe to omit but does not say what happens"
            )


def test_normalized_defaults_match_the_documented_default():
    """A normalization rule may make a default explicit, never invent one."""
    for name, contract in _contracts().items():
        declared = {field["key"]: field for field in contract.get("fields", [])}
        for key, value in _normalization_values(contract).items():
            field = declared[key]
            assert field["documentedDefault"] is not None, (
                f"{name}: {key} is normalized to {value!r} but the manual documents "
                f"no default for it"
            )
            assert float(value) == float(field["documentedDefault"])


# ---------------------------------------------------------------------------
# /db/NMAS - the rule the npm SDK was missing.
# ---------------------------------------------------------------------------


def test_nmas_contract_marks_rotational_fields_unsafe_to_omit():
    contract = _load(ENDPOINT_DIR / "db-nmas.yaml")
    fields = {field["key"]: field for field in contract["fields"]}

    for key in ("rmX", "rmY", "rmZ"):
        assert fields[key]["documentedOptional"] is True
        assert fields[key]["safeToOmit"] is False

    # mY/mZ are documented optional and nobody has omitted them against a live
    # product - the confirmed live payload sends all three translational masses.
    # `unverified` is the honest answer; claiming `true` here would be reading
    # the manual's "Optional" as evidence, which is the mistake rmX punishes.
    for key in ("mY", "mZ"):
        assert fields[key]["safeToOmit"] == "unverified"

    assert _normalization_values(contract) == {"rmX": 0.0, "rmY": 0.0, "rmZ": 0.0}


def test_no_contract_claims_omission_safety_without_evidence():
    """`safeToOmit: true` is a claim about the product and has to cite one."""
    for name, contract in _contracts().items():
        for field in contract.get("fields", []):
            if field["safeToOmit"] is not True:
                continue
            evidence = field.get("omissionEvidence", "")
            assert evidence.strip(), f"{name}: {field['key']} claims safeToOmit with no evidence"
            assert "manual" not in evidence.lower() or "live" in evidence.lower(), (
                f"{name}: {field['key']} cites the manual as omission evidence; the manual "
                f"saying 'Optional' is what documentedOptional already records"
            )


class _RecordingClient:
    """Captures the outgoing body without touching the network."""

    def __init__(self) -> None:
        self.body: dict = {}

    def request(self, method: str, endpoint: str, body=None) -> dict:
        self.body = body
        return {}

    def check_product(self, products, name) -> None:
        return None


@pytest.mark.parametrize("verb", ["create", "update"])
def test_python_nmas_fills_rotational_mass_before_sending(verb):
    """Omitting rmX/rmY/rmZ must never reach the product."""
    client = _RecordingClient()
    getattr(NodalMass, verb)({1: {"mX": 1.0, "mY": 1.0, "mZ": 1.0}}, client=client)

    sent = client.body["Assign"]["1"]
    assert sent == {"mX": 1.0, "mY": 1.0, "mZ": 1.0, "rmX": 0.0, "rmY": 0.0, "rmZ": 0.0}


@pytest.mark.parametrize("verb", ["create", "update"])
def test_python_nmas_keeps_caller_supplied_rotational_mass(verb):
    """Normalizing a default must not overwrite a real value."""
    client = _RecordingClient()
    getattr(NodalMass, verb)({1: {"mX": 1.0, "rmZ": 500.0}}, client=client)

    sent = client.body["Assign"]["1"]
    assert sent["rmZ"] == 500.0
    assert sent["rmX"] == 0.0
    assert sent["rmY"] == 0.0


def test_npm_manifest_carries_the_nmas_normalization():
    """The generated npm surface must carry the rule, not just the Python one.

    This is the assertion that would have failed for the whole of the npm
    package's first month.
    """
    manifest = json.loads(TS_RESOURCES.read_text(encoding="utf-8"))
    nmas = next(r for r in manifest["resources"] if r["endpoint"] == "/db/NMAS")

    assert nmas.get("payloadDefaults") == {"rmX": 0.0, "rmY": 0.0, "rmZ": 0.0}


def test_risks_referenced_by_contracts_exist():
    risks = {risk["id"] for risk in _load(RISKS_FILE)["risks"]}
    for name, contract in _contracts().items():
        for defect in contract.get("knownDefects", []):
            assert defect["ref"] in risks, f"{name} references unknown risk {defect['ref']}"
        for rule in contract.get("sdkRules", []):
            if "riskRef" in rule:
                assert rule["riskRef"] in risks, (
                    f"{name}: rule {rule['id']} references unknown risk {rule['riskRef']}"
                )


def test_client_rules_document_timeout_semantics():
    """A timeout stops the SDK waiting; it does not roll the product back.

    Kept as an explicit test because it is the invariant most likely to be
    softened into something reassuring and wrong.
    """
    rules = {rule["id"]: rule for rule in _load(RISKS_FILE)["clientRules"]}

    assert "timeout-is-not-rollback" in rules
    statement = rules["timeout-is-not-rollback"]["statement"].lower()
    assert "does not cancel" in statement
    assert "roll back" in statement or "rollback" in statement


# ---------------------------------------------------------------------------
# The second layer: 89 result tables behind one route.
# ---------------------------------------------------------------------------

TABLE_DIR = CONTRACTS / "tables"


def _tables() -> dict[str, dict]:
    return {path.stem: _load(path) for path in sorted(TABLE_DIR.glob("*.yaml"))}


def test_every_table_routes_through_a_contracted_endpoint():
    """A table cannot describe how it departs from a request shape nobody wrote."""
    endpoints = {contract["endpoint"] for contract in _contracts().values()}

    for name, table in _tables().items():
        assert table["endpoint"] in endpoints, (
            f"{name} routes through {table['endpoint']}, which has no endpoint contract"
        )


def test_table_types_are_named_in_both_sdks():
    """A TABLE_TYPE only one language names is a table only its users will find."""
    python_source = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "src" / "midas_nx" / "post").glob("*.py")
    )
    npm_source = (
        ROOT / "packages" / "typescript" / "src" / "generated" / "tables.ts"
    ).read_text(encoding="utf-8")

    for name, table in _tables().items():
        for entry in table["tableTypes"]:
            value = entry["value"]
            assert f'"{value}"' in python_source, f"{name}: {value} unnamed in the Python SDK"
            assert f'"{value}"' in npm_source, f"{name}: {value} unnamed in the npm SDK"


def test_unresolved_manual_contradictions_stay_unresolved():
    """Where the manual disagrees with itself, say so instead of picking a winner.

    /post/TABLE has two live examples: the manual's schema, table and example
    disagree about `REACTIONSURFACESPRING` and about `BEAMFORCESTP`. Each
    contract declares the majority spelling *and* records that nobody has asked
    the server which one it accepts.
    """
    unresolved = [
        (name, defect)
        for name, table in _tables().items()
        for defect in table.get("manualDefects", [])
        if defect.get("resolved") is False
    ]

    assert unresolved, "the two known /post/TABLE spelling contradictions should be recorded"
    for name, defect in unresolved:
        assert defect["evidence"].strip(), f"{name}: unresolved defect with no evidence"
        assert "not " in defect["actual"].lower() or "unknown" in defect["actual"].lower(), (
            f"{name}: an unresolved contradiction must say what is still unknown"
        )


def test_post_table_response_key_is_declared_unstable():
    """The one thing an SDK must not do to this endpoint is index it by key name."""
    contract = _load(ENDPOINT_DIR / "post-table.yaml")
    response = next(op for op in contract["operations"] if op["method"] == "POST")["response"]
    rule = next(rule for rule in contract["sdkRules"] if rule["id"] == "post-table-unwrap-by-shape")

    assert response["keyStability"] == "unstable"
    assert "empty" in response["keyNote"]
    assert rule["kind"] == "unwrap_table_by_shape"
    assert set(rule["responseCases"]) == {
        "table_name",
        "result_table",
        "empty_with_table",
        "no_table",
    }
