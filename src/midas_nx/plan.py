"""Order ``/db/*`` writes so a record is sent after the records it names.

Offline and pure: nothing here calls NX. :data:`DEPENDENCIES` is the table graph
the contracts record - a field's ``references`` and a record keyed by node or
element ids - and ``scripts/validate_contracts.py`` fails if it differs from
them, as it does for npm's copy. Only measured references are in it (2026-11-04,
Gen NX and Civil NX); a table no contract gives a reference to ranks with the
tables that name nothing.

What the product does when the order is wrong, measured the same day: a missing
node, load case or group name is refused, but an element naming a material or
section that does not exist is stored as an orphan, and ``/db/GRUP`` and
``/db/ELNK`` drop a missing entry silently. The other way round, a per-id DELETE
of a node removes the elements on it, and of a load case the loads in it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence

#: Table -> the tables its records name. Written here rather than read at run
#: time because the wheel ships no contracts; ``validate_contracts.py`` holds it
#: equal to them.
DEPENDENCIES: Dict[str, FrozenSet[str]] = {
    "/db/BMLD": frozenset({"/db/ELEM", "/db/LDGR", "/db/STLD"}),
    "/db/CNLD": frozenset({"/db/LDGR", "/db/NODE", "/db/STLD"}),
    "/db/CONS": frozenset({"/db/BNGR", "/db/NODE"}),
    "/db/ELEM": frozenset({"/db/MATL", "/db/NODE", "/db/SECT", "/db/THIK"}),
    "/db/ELNK": frozenset({"/db/BNGR", "/db/NODE"}),
    "/db/FRLS": frozenset({"/db/BNGR", "/db/ELEM"}),
    "/db/GRUP": frozenset({"/db/ELEM", "/db/NODE"}),
    "/db/LCOM-GEN": frozenset({"/db/STLD"}),
    "/db/NMAS": frozenset({"/db/NODE"}),
    "/db/PRES": frozenset({"/db/ELEM", "/db/LDGR", "/db/STLD"}),
}

WRITE_METHODS = ("POST", "PUT")


@dataclass(frozen=True)
class Operation:
    """One request to one table. ``records`` for POST/PUT, ``ids`` for DELETE."""

    endpoint: str  # "/db/NODE"
    method: str  # "POST", "PUT" or "DELETE"
    records: Optional[Mapping[str, Any]] = None
    ids: Optional[Sequence[Any]] = None
    label: Optional[str] = None  # the caller's name for it


def dependencies() -> Dict[str, FrozenSet[str]]:
    """A copy of :data:`DEPENDENCIES`."""
    return dict(DEPENDENCIES)


def rank(endpoint: str) -> int:
    """0 for a table that names nothing, else one more than its deepest target."""
    seen: Dict[str, int] = {}

    def depth(table: str) -> int:
        if table not in seen:
            seen[table] = 1 + max((depth(t) for t in DEPENDENCIES.get(table, ())), default=-1)
        return seen[table]

    return depth(endpoint)


def order(operations: Sequence[Operation]) -> List[Operation]:
    """Deletes first, dependents before what they name; then writes, the reverse.

    Stable: operations of equal rank keep the caller's order, so a ``/db/UNIT``
    change placed first stays first. Raises ``ValueError`` on a method other
    than POST, PUT or DELETE.
    """
    for op in operations:
        if op.method.upper() not in WRITE_METHODS + ("DELETE",):
            raise ValueError(f"{op.endpoint}: cannot order a {op.method} (POST, PUT or DELETE only)")

    def key(item: "tuple[int, Operation]") -> "tuple[int, int, int]":
        index, op = item
        r = rank(op.endpoint)
        if op.method.upper() == "DELETE":
            return (0, -r, index)
        return (1, r, index)

    return [op for _, op in sorted(enumerate(operations), key=key)]
