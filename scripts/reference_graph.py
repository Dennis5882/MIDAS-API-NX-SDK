"""The table graph the contracts' `references` and `recordKey`s describe.

One function, shared by `validate_contracts.py` (which checks it is acyclic and
that Python's `midas_nx.plan.DEPENDENCIES` equals it) and by
`generate_typescript_sdk.py` (which publishes it to npm), so the two SDKs can
only order operations from the same graph.

An edge A -> B says a record of A names a record of B: through a field's
`references`, or because A's records are keyed by B's ids (`recordKey.kind`
node_id or element_id). Self-references are left out.
"""

from __future__ import annotations

from typing import Any, Iterable

RECORD_KEY_TABLES = {"node_id": "/db/NODE", "element_id": "/db/ELEM"}


def _fields(fields: list[dict]) -> Iterable[dict]:
    for field in fields:
        yield field
        yield from _fields(field.get("properties") or [])


def reference_fields(contracts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per field `references`, as both SDKs publish it at run time.

    `field` is the path inside one record: `ITEMS[].LCNAME` for a field of each
    `ITEMS` entry. Only behaviour is kept - `note` and `evidence` stay in the
    contract. Sorted by table, then field.
    """
    rows: list[dict[str, Any]] = []

    def walk(endpoint: str, fields: list[dict], prefix: str) -> None:
        for field in fields:
            path = f"{prefix}{field['key']}"
            ref = field.get("references")
            if ref:
                row: dict[str, Any] = {
                    "table": endpoint,
                    "field": path,
                    "targets": list(ref["tables"]),
                    "by": ref["by"],
                }
                if "nameField" in ref:
                    row["nameField"] = ref["nameField"]
                row["each"] = bool(ref.get("each"))
                row["onMissing"] = ref["onMissing"]
                if "onTargetDelete" in ref:
                    row["onTargetDelete"] = ref["onTargetDelete"]
                if "targetsBy" in ref:
                    row["targetsBy"] = {
                        "path": ref["targetsBy"]["path"],
                        "cases": {k: list(v) for k, v in sorted(ref["targetsBy"]["cases"].items())},
                    }
                rows.append(row)
            nested = field.get("properties") or []
            if nested:
                walk(endpoint, nested, path + ("[]." if field.get("type") == "array" else "."))

    for contract in contracts:
        walk(contract["endpoint"], contract.get("fields", []), "")
    rows.sort(key=lambda row: (row["table"], row["field"]))
    return rows


def key_references(contracts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per table whose Assign key is a node or element id, shaped like a
    `reference_fields` row with `field` "" (the record key). `onMissing` is
    "unverified" where the contract records none. Sorted by table.
    """
    rows: list[dict[str, Any]] = []
    for contract in contracts:
        key = contract.get("recordKey") or {}
        target = RECORD_KEY_TABLES.get(key.get("kind", ""))
        if not target or target == contract["endpoint"]:
            continue
        row: dict[str, Any] = {
            "table": contract["endpoint"],
            "field": "",
            "targets": [target],
            "by": "id",
            "each": False,
            "onMissing": key.get("onMissing", "unverified"),
        }
        if "onTargetDelete" in key:
            row["onTargetDelete"] = key["onTargetDelete"]
        rows.append(row)
    rows.sort(key=lambda row: row["table"])
    return rows


def item_rows(contracts: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """One row per table whose record is a list of entries a PUT merges by id,
    from the contracts' `itemRows`. Sorted by table."""
    rows = [
        {
            "table": c["endpoint"],
            "path": c["itemRows"]["path"],
            "by": c["itemRows"]["by"],
            "caseField": c["itemRows"]["caseField"],
        }
        for c in contracts
        if c.get("itemRows")
    ]
    rows.sort(key=lambda row: row["table"])
    return rows


def key_policies(contracts: Iterable[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Endpoint -> product -> "honoured" or "assigned", from the contracts' `keyPolicy`."""
    return {
        c["endpoint"]: {p: c["keyPolicy"][p] for p in ("gen", "civil") if p in c["keyPolicy"]}
        for c in sorted(contracts, key=lambda c: c["endpoint"])
        if c.get("keyPolicy")
    }


def reference_graph(contracts: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    """Table -> the tables its records name. Only tables with an edge appear."""
    graph: dict[str, set[str]] = {}
    for contract in contracts:
        endpoint = contract["endpoint"]
        targets: set[str] = set()
        for field in _fields(contract.get("fields", [])):
            targets.update((field.get("references") or {}).get("tables", []))
        keyed = RECORD_KEY_TABLES.get((contract.get("recordKey") or {}).get("kind", ""))
        if keyed:
            targets.add(keyed)
        targets.discard(endpoint)
        if targets:
            graph[endpoint] = targets
    return graph
