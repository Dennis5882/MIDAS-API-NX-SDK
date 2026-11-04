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
