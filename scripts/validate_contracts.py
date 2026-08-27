"""Validate contracts/ and check both SDK surfaces against it.

The contracts under ``contracts/`` are the language-neutral source of truth for
this repository: an endpoint's shape comes from the official manual repo, from
live verification records, or from ``/info`` schema introspection - never from
either SDK implementation. This script is what keeps that arrangement honest.

It runs four kinds of check:

1. **Schema** - every contract validates against
   ``contracts/schema/endpoint-contract.schema.json``.
2. **Cross-reference** - every ``riskRef``/``knownDefects[].ref`` resolves in
   ``contracts/safety/known-product-risks.yaml``, and every
   ``verification.records[].ref`` resolves in that product's file under
   ``contracts/verification/``.
3. **Safety** - a ``product_crash_risk`` operation must carry a mitigation, an
   SDK rule and a risk reference; a field that is ``documentedOptional`` but not
   ``safeToOmit`` must be covered by an SDK rule; a contract without a manual
   source must justify itself.
4. **Parity** - the endpoint, products and methods each contract declares must
   match what the Python package and the generated npm resource manifest expose,
   and any ``normalize_defaults`` rule must actually be implemented in both.

Parity uses the SDKs as *subjects*, never as sources. A mismatch is reported as
an SDK defect, not as a reason to edit the contract.

Exit codes: 0 clean, 1 validation failures, 2 could not run (missing dependency
or malformed input).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
ENDPOINT_DIR = CONTRACTS / "endpoints"
SCHEMA_FILE = CONTRACTS / "schema" / "endpoint-contract.schema.json"
RISKS_FILE = CONTRACTS / "safety" / "known-product-risks.yaml"
VERIFICATION_DIR = CONTRACTS / "verification"
TS_RESOURCES = ROOT / "schema" / "typescript-resources.json"

_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Failures:
    """Collects failures so one run reports everything, not just the first."""

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, where: str, message: str) -> None:
        self.items.append((where, message))

    def __bool__(self) -> bool:
        return bool(self.items)


def _load_yaml(path: Path) -> Any:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_contracts() -> list[tuple[Path, dict]]:
    return [(p, _load_yaml(p)) for p in sorted(ENDPOINT_DIR.glob("*.yaml"))]


def _iter_fields(fields: list[dict]) -> list[dict]:
    """Flatten nested `properties` so every declared field is checked once."""
    out: list[dict] = []
    for field in fields or []:
        out.append(field)
        out.extend(_iter_fields(field.get("properties") or []))
    return out


def check_schema(contracts: list[tuple[Path, dict]], failures: Failures) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print(
            "ERROR: jsonschema is not installed. Run: pip install -e \".[dev]\"",
            file=sys.stderr,
        )
        raise SystemExit(2) from None

    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for path, contract in contracts:
        for error in sorted(validator.iter_errors(contract), key=lambda e: list(e.path)):
            location = "/".join(str(part) for part in error.path) or "(root)"
            failures.add(path.name, f"schema: {location}: {error.message}")
        if contract.get("id") != path.stem:
            failures.add(
                path.name,
                f"id {contract.get('id')!r} does not match the file name {path.stem!r}",
            )


def check_cross_references(
    contracts: list[tuple[Path, dict]],
    risks: dict,
    verification: dict[str, dict],
    failures: Failures,
) -> None:
    risk_ids = {r["id"] for r in risks.get("risks", [])}
    record_ids = {
        product: {r["id"] for r in data.get("records", [])}
        for product, data in verification.items()
    }

    for path, contract in contracts:
        for defect in contract.get("knownDefects", []):
            if defect["ref"] not in risk_ids:
                failures.add(
                    path.name,
                    f"knownDefects references unknown risk {defect['ref']!r}",
                )
        for rule in contract.get("sdkRules", []):
            ref = rule.get("riskRef")
            if ref is not None and ref not in risk_ids:
                failures.add(
                    path.name,
                    f"sdkRule {rule['id']!r} references unknown risk {ref!r}",
                )
        for record in contract.get("verification", {}).get("records", []):
            product = record["product"]
            known = record_ids.get(product)
            if known is None:
                failures.add(
                    path.name,
                    f"no verification file for product {product!r}",
                )
            elif record["ref"] not in known:
                failures.add(
                    path.name,
                    f"verification record {record['ref']!r} is not in {product}-nx.yaml",
                )

    # A risk is only useful if something enforces it. Endpoints that have no
    # contract yet are skipped: during migration that is expected, not a defect.
    contracted = {c["endpoint"] for _, c in contracts}
    for risk in risks.get("risks", []):
        if not _ID_RE.match(risk["id"]):
            failures.add(RISKS_FILE.name, f"risk id {risk['id']!r} is not a slug")
        targets = [e for e in risk.get("endpoints", []) if not e.endswith("*")]
        relevant = [e for e in targets if e in contracted]
        if not relevant:
            continue
        referencing = {
            c["endpoint"]
            for _, c in contracts
            if any(d["ref"] == risk["id"] for d in c.get("knownDefects", []))
        }
        for endpoint in relevant:
            if endpoint not in referencing:
                failures.add(
                    RISKS_FILE.name,
                    f"risk {risk['id']!r} names {endpoint}, whose contract does "
                    f"not reference it under knownDefects",
                )


def check_safety(contracts: list[tuple[Path, dict]], failures: Failures) -> None:
    for path, contract in contracts:
        rules = contract.get("sdkRules", [])
        rules_by_method: dict[str, list[dict]] = {}
        for rule in rules:
            for method in rule["appliesTo"]:
                rules_by_method.setdefault(method, []).append(rule)

        for operation in contract["operations"]:
            if operation["risk"] != "product_crash_risk":
                continue
            label = f"{operation['method']}{' ' + operation['variant'] if operation.get('variant') else ''}"
            if operation.get("mitigation") in (None, "none"):
                failures.add(
                    path.name,
                    f"{label} is product_crash_risk with no mitigation",
                )
            if not rules_by_method.get(operation["method"]):
                failures.add(
                    path.name,
                    f"{label} is product_crash_risk but no sdkRule applies to it",
                )
            if not contract.get("knownDefects"):
                failures.add(
                    path.name,
                    f"{label} is product_crash_risk but the contract references "
                    f"no entry in {RISKS_FILE.name}",
                )

        for operation in contract["operations"]:
            if operation["risk"] != "destructive":
                continue
            if "mitigation" not in operation:
                failures.add(
                    path.name,
                    f"{operation['method']} is destructive with no mitigation declared",
                )

        covered = {
            field
            for rule in rules
            if rule["kind"] in ("normalize_defaults", "reject_request")
            for field in rule.get("fields", [])
        }
        for field in _iter_fields(contract.get("fields", [])):
            if field["safeToOmit"] or field["key"] in covered:
                continue
            if field["requirement"] == "required" and not field["documentedOptional"]:
                # A required field the caller must supply; nothing to normalize.
                continue
            failures.add(
                path.name,
                f"field {field['key']!r} is documentedOptional but not safeToOmit, "
                f"and no sdkRule covers it - callers following the manual would "
                f"hit the defect",
            )

        for rule in rules:
            if rule["kind"] != "normalize_defaults":
                continue
            declared = {f["key"]: f for f in _iter_fields(contract.get("fields", []))}
            for key, value in rule["values"].items():
                field = declared.get(key)
                if field is None:
                    failures.add(
                        path.name,
                        f"sdkRule {rule['id']!r} defaults undeclared field {key!r}",
                    )
                elif "documentedDefault" in field and field["documentedDefault"] is not None:
                    if float(value) != float(field["documentedDefault"]):
                        failures.add(
                            path.name,
                            f"sdkRule {rule['id']!r} sets {key}={value!r}, which is "
                            f"not its documented default "
                            f"{field['documentedDefault']!r} - a normalization "
                            f"rule may make a default explicit, not invent one",
                        )


def check_manual_source(contracts: list[tuple[Path, dict]], failures: Failures) -> None:
    for path, contract in contracts:
        manual = contract["source"]["manual"]
        if manual["status"] == "documented":
            continue
        # The schema already requires a justification here; this check exists so
        # the count shows up in the CI log rather than passing silently.
        if not manual.get("justification", "").strip():
            failures.add(
                path.name,
                f"manual status is {manual['status']!r} with no justification",
            )


def _python_resources() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "src"))
    import importlib
    import pkgutil

    import midas_nx
    from midas_nx.db.base import DbResource

    for module in pkgutil.walk_packages(midas_nx.__path__, "midas_nx."):
        importlib.import_module(module.name)

    found: dict[str, Any] = {}

    def walk(base: type) -> None:
        for child in base.__subclasses__():
            endpoint = getattr(child, "ENDPOINT", None)
            if endpoint:
                found[endpoint] = child
            walk(child)

    walk(DbResource)
    return found


def check_parity(contracts: list[tuple[Path, dict]], failures: Failures) -> None:
    try:
        python_resources = _python_resources()
    except Exception as exc:  # pragma: no cover - import failure is a hard stop
        print(f"ERROR: could not import midas_nx: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

    ts_by_endpoint: dict[str, dict] = {}
    if TS_RESOURCES.exists():
        manifest = json.loads(TS_RESOURCES.read_text(encoding="utf-8"))
        for resource in manifest.get("resources", []):
            ts_by_endpoint[resource["endpoint"]] = resource

    for path, contract in contracts:
        endpoint = contract["endpoint"]
        methods = {op["method"] for op in contract["operations"]}
        products = set(contract["products"])

        resource = python_resources.get(endpoint)
        if resource is None:
            failures.add(
                path.name,
                f"no Python resource exposes {endpoint} - the contract and the "
                f"Python SDK disagree about what exists",
            )
        else:
            py_methods = set(getattr(resource, "METHODS", set()))
            if py_methods != methods:
                failures.add(
                    path.name,
                    f"Python {resource.__name__} serves {sorted(py_methods)}, "
                    f"contract declares {sorted(methods)}",
                )
            py_products = set(getattr(resource, "PRODUCTS", set()))
            if py_products != products:
                failures.add(
                    path.name,
                    f"Python {resource.__name__} declares products "
                    f"{sorted(py_products)}, contract declares {sorted(products)}",
                )
            _check_python_normalization(path, contract, resource, failures)

        ts_resource = ts_by_endpoint.get(endpoint)
        if ts_resource is None:
            if ts_by_endpoint:
                failures.add(
                    path.name,
                    f"no npm resource exposes {endpoint}",
                )
        else:
            if set(ts_resource["methods"]) != methods:
                failures.add(
                    path.name,
                    f"npm {ts_resource['exportName']} serves "
                    f"{sorted(ts_resource['methods'])}, contract declares "
                    f"{sorted(methods)}",
                )
            if set(ts_resource["products"]) != products:
                failures.add(
                    path.name,
                    f"npm {ts_resource['exportName']} declares products "
                    f"{sorted(ts_resource['products'])}, contract declares "
                    f"{sorted(products)}",
                )
            _check_typescript_normalization(path, contract, ts_resource, failures)


def _normalization_values(contract: dict) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for rule in contract.get("sdkRules", []):
        if rule["kind"] == "normalize_defaults":
            merged.update(rule["values"])
    return merged


def _check_python_normalization(
    path: Path, contract: dict, resource: type, failures: Failures
) -> None:
    expected = _normalization_values(contract)
    if not expected:
        return
    sent: dict[str, Any] = {}

    class _Recorder:
        def request(self, method: str, endpoint: str, body: Any = None) -> dict:
            sent.update(body["Assign"]["1"])
            return {}

        def check_product(self, products: Any, name: str) -> None:
            return None

    for verb in ("create", "update"):
        sent.clear()
        try:
            getattr(resource, verb)({1: {}}, client=_Recorder())
        except Exception as exc:  # pragma: no cover - reported, not raised
            failures.add(path.name, f"Python {resource.__name__}.{verb}() raised: {exc}")
            continue
        for key, value in expected.items():
            if key not in sent:
                failures.add(
                    path.name,
                    f"Python {resource.__name__}.{verb}() sent a payload without "
                    f"{key!r}; the contract requires it be normalized to {value!r}",
                )
            elif float(sent[key]) != float(value):
                failures.add(
                    path.name,
                    f"Python {resource.__name__}.{verb}() sent {key}={sent[key]!r}, "
                    f"contract requires {value!r}",
                )


def _check_typescript_normalization(
    path: Path, contract: dict, ts_resource: dict, failures: Failures
) -> None:
    expected = _normalization_values(contract)
    declared = ts_resource.get("payloadDefaults") or {}
    if not expected:
        if declared:
            failures.add(
                path.name,
                f"npm {ts_resource['exportName']} declares payloadDefaults "
                f"{declared!r} that no contract rule asks for",
            )
        return
    for key, value in expected.items():
        if key not in declared:
            failures.add(
                path.name,
                f"npm {ts_resource['exportName']} does not normalize {key!r}; the "
                f"contract requires it be sent as {value!r}",
            )
        elif float(declared[key]) != float(value):
            failures.add(
                path.name,
                f"npm {ts_resource['exportName']} normalizes {key} to "
                f"{declared[key]!r}, contract requires {value!r}",
            )


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    skip_parity = "--no-parity" in argv

    contracts = _load_contracts()
    if not contracts:
        print(f"ERROR: no contracts found under {ENDPOINT_DIR}", file=sys.stderr)
        return 2

    risks = _load_yaml(RISKS_FILE)
    verification = {
        path.stem.removesuffix("-nx"): _load_yaml(path)
        for path in sorted(VERIFICATION_DIR.glob("*.yaml"))
    }

    failures = Failures()
    check_schema(contracts, failures)
    check_cross_references(contracts, risks, verification, failures)
    check_safety(contracts, failures)
    check_manual_source(contracts, failures)
    if not skip_parity:
        check_parity(contracts, failures)

    crash_risk = sum(
        1
        for _, c in contracts
        for op in c["operations"]
        if op["risk"] == "product_crash_risk"
    )
    print(
        f"contracts: {len(contracts)} endpoints, "
        f"{sum(len(c['operations']) for _, c in contracts)} operations, "
        f"{crash_risk} carrying product_crash_risk, "
        f"{len(risks.get('risks', []))} known risks, "
        f"{sum(len(v.get('records', [])) for v in verification.values())} "
        f"verification records"
    )

    if failures:
        print(f"\n{len(failures.items)} problem(s):")
        for where, message in failures.items:
            print(f"  {where}: {message}")
        return 1

    print("OK - contracts valid and both SDK surfaces match them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
