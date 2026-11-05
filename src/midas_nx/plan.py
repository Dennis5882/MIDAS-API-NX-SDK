"""Order ``/db/*`` writes so a record is sent after the records it names.

Offline and pure: nothing here calls NX. :data:`DEPENDENCIES` is the table graph
the contracts record - a field's ``references`` and a record keyed by node or
element ids - and :data:`REFERENCES` is the field-level list behind it, with
what the product does when the named record is missing or deleted.
``scripts/validate_contracts.py`` fails if either differs from the contracts, as
it does for npm's copies. Only measured references are in them (2026-11-04,
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
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

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
class Reference:
    """One field that names a record of another table.

    ``field`` is the path inside one record: ``ITEMS[].LCNAME`` is a field of
    each ``ITEMS`` entry. ``on_missing`` is what the product did with a value
    naming no record - ``refused`` (the write fails), ``stored`` (kept, an
    orphan), ``dropped`` (kept without the value, silently) or ``unverified``.
    ``on_target_delete`` is what a per-id DELETE of the named record did to
    this one - ``deleted`` or ``orphaned`` - and ``None`` where not measured.
    """

    table: str
    field: str
    targets: Tuple[str, ...]
    by: str  # "id" = the target's Assign key; "name" = its name_field
    name_field: Optional[str] = None
    each: bool = False  # the field is an array and each element is a reference
    on_missing: str = "unverified"
    on_target_delete: Optional[str] = None


#: Every field reference the contracts record, sorted by table and field.
#: Held equal to them, and to npm's ``referenceFields``, by ``validate_contracts.py``.
REFERENCES: Tuple[Reference, ...] = (
    Reference("/db/BMLD", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/BMLD", "ITEMS[].LCNAME", ("/db/STLD",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/CNLD", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name", name_field="NAME", on_missing="refused"),
    Reference(
        "/db/CNLD", "ITEMS[].LCNAME", ("/db/STLD",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="deleted",
    ),
    Reference("/db/CONS", "ITEMS[].GROUP_NAME", ("/db/BNGR",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/ELEM", "MATL", ("/db/MATL",), "id", on_missing="stored", on_target_delete="orphaned"),
    Reference("/db/ELEM", "NODE", ("/db/NODE",), "id", each=True, on_missing="refused", on_target_delete="deleted"),
    Reference("/db/ELEM", "SECT", ("/db/SECT", "/db/THIK"), "id", on_missing="stored", on_target_delete="orphaned"),
    Reference("/db/ELNK", "BNGR_NAME", ("/db/BNGR",), "name", name_field="NAME", on_missing="dropped"),
    Reference("/db/ELNK", "NODE", ("/db/NODE",), "id", each=True, on_missing="refused"),
    Reference("/db/FRLS", "ITEMS[].GROUP_NAME", ("/db/BNGR",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/GRUP", "E_LIST", ("/db/ELEM",), "id", each=True, on_missing="dropped"),
    Reference("/db/GRUP", "N_LIST", ("/db/NODE",), "id", each=True, on_missing="dropped"),
    Reference("/db/LCOM-GEN", "vCOMB[].LCNAME", ("/db/STLD",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/PRES", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name", name_field="NAME", on_missing="refused"),
    Reference("/db/PRES", "ITEMS[].LCNAME", ("/db/STLD",), "name", name_field="NAME", on_missing="refused"),
)


#: Where a POST lands when its Assign key is not the next free one, per product:
#: ``"honoured"`` = under the requested key; ``"assigned"`` = the product picks
#: the key itself (one past the highest), so read the table back to learn it.
#: A table or product absent was not measured (2026-11-05, Gen NX Build
#: 10/17/2026 and Civil NX Build 10/31/2026). Held equal to the contracts'
#: ``keyPolicy`` and to npm's ``keyPolicies`` by ``validate_contracts.py``.
KEY_POLICY: Dict[str, Dict[str, str]] = {
    "/DESIGN/RC/KDS-41-20-2022/BEMW": {"gen": "honoured"},
    "/DESIGN/RC/KDS-41-20-2022/WMAK": {"gen": "honoured", "civil": "honoured"},
    "/DESIGN/STEEL/KDS-41-30-2022/SLRS": {"gen": "honoured", "civil": "honoured"},
    "/db/BCGA-M1": {"civil": "assigned"},
    "/db/BCGD-M1": {"civil": "honoured"},
    "/db/BNGR": {"gen": "honoured", "civil": "honoured"},
    "/db/CAMB": {"civil": "assigned"},
    "/db/CCFC": {"gen": "honoured", "civil": "honoured"},
    "/db/CGLP": {"gen": "assigned", "civil": "assigned"},
    "/db/CJFG": {"civil": "assigned"},
    "/db/CLDR": {"gen": "honoured", "civil": "honoured"},
    "/db/CLWP": {"gen": "honoured", "civil": "honoured"},
    "/db/CMCS": {"civil": "honoured"},
    "/db/CNLD": {"gen": "honoured", "civil": "honoured"},
    "/db/CONS": {"gen": "honoured", "civil": "honoured"},
    "/db/CRGR": {"civil": "assigned"},
    "/db/CUTL": {"gen": "honoured", "civil": "honoured"},
    "/db/EFCT": {"gen": "assigned", "civil": "assigned"},
    "/db/ELNK": {"gen": "honoured", "civil": "honoured"},
    "/db/EPMT": {"gen": "honoured", "civil": "honoured"},
    "/db/ETFC": {"gen": "honoured", "civil": "honoured"},
    "/db/EXLD": {"gen": "assigned", "civil": "assigned"},
    "/db/FBLD": {"gen": "assigned", "civil": "assigned"},
    "/db/FIBR": {"gen": "honoured", "civil": "honoured"},
    "/db/FIMP": {"gen": "assigned", "civil": "honoured"},
    "/db/GCMB": {"civil": "assigned"},
    "/db/GRDP": {"gen": "assigned", "civil": "assigned"},
    "/db/GRUP": {"gen": "honoured", "civil": "honoured"},
    "/db/GSBG": {"civil": "honoured"},
    "/db/GSPR": {"gen": "honoured", "civil": "honoured"},
    "/db/GSTP": {"gen": "assigned", "civil": "honoured"},
    "/db/HHCT": {"gen": "assigned"},
    "/db/HSFC": {"gen": "honoured", "civil": "honoured"},
    "/db/HSPT": {"gen": "honoured", "civil": "honoured"},
    "/db/IEHC": {"gen": "assigned", "civil": "assigned"},
    "/db/IELC": {"gen": "assigned", "civil": "assigned"},
    "/db/INMF": {"gen": "honoured", "civil": "honoured"},
    "/db/LCOM-CONC": {"gen": "honoured", "civil": "honoured"},
    "/db/LCOM-GEN": {"gen": "honoured", "civil": "honoured"},
    "/db/LCOM-SEISMIC": {"gen": "honoured"},
    "/db/LCOM-SRC": {"gen": "honoured", "civil": "honoured"},
    "/db/LCOM-STEEL": {"gen": "honoured", "civil": "honoured"},
    "/db/LCOM-STLCOMP": {"gen": "honoured", "civil": "honoured"},
    "/db/LDGR": {"gen": "honoured", "civil": "honoured"},
    "/db/LLANch": {"civil": "honoured"},
    "/db/LLANid": {"civil": "honoured"},
    "/db/LLANop": {"civil": "honoured"},
    "/db/LLANtr": {"gen": "honoured", "civil": "honoured"},
    "/db/LTOM": {"gen": "assigned", "civil": "assigned"},
    "/db/MADO": {"gen": "honoured", "civil": "honoured"},
    "/db/MEMB": {"gen": "honoured", "civil": "honoured"},
    "/db/MLFC": {"gen": "honoured", "civil": "honoured"},
    "/db/MLSP": {"gen": "assigned", "civil": "assigned"},
    "/db/MLSR": {"gen": "honoured", "civil": "honoured"},
    "/db/MVCT": {"gen": "assigned", "civil": "assigned"},
    "/db/MVCTbs": {"gen": "assigned", "civil": "assigned"},
    "/db/MVCTid": {"civil": "assigned"},
    "/db/MVCTtr": {"gen": "assigned", "civil": "assigned"},
    "/db/MVHLtr": {"gen": "honoured", "civil": "honoured"},
    "/db/MVLDch": {"civil": "assigned"},
    "/db/MVLDeu": {"gen": "honoured", "civil": "honoured"},
    "/db/MVLDid": {"civil": "assigned"},
    "/db/MVLDtr": {"gen": "honoured", "civil": "honoured"},
    "/db/NBOF": {"gen": "honoured", "civil": "honoured"},
    "/db/NLCT": {"gen": "assigned"},
    "/db/NLLP": {"gen": "assigned", "civil": "assigned"},
    "/db/NLNK": {"gen": "honoured", "civil": "honoured"},
    "/db/NLNK-M1": {"civil": "honoured"},
    "/db/NMAS": {"gen": "honoured", "civil": "honoured"},
    "/db/NODE": {"gen": "honoured", "civil": "honoured"},
    "/db/NPLN": {"gen": "honoured", "civil": "honoured"},
    "/db/NSPR": {"gen": "honoured", "civil": "honoured"},
    "/db/NTMP": {"gen": "honoured", "civil": "honoured"},
    "/db/PJCF": {"gen": "assigned", "civil": "assigned"},
    "/db/PNLA": {"gen": "assigned", "civil": "assigned"},
    "/db/PNLD": {"gen": "assigned", "civil": "assigned"},
    "/db/POGD": {"civil": "assigned"},
    "/db/POLC": {"gen": "honoured", "civil": "honoured"},
    "/db/POLC-M1": {"civil": "honoured"},
    "/db/POSL": {"gen": "honoured", "civil": "honoured"},
    "/db/POSP": {"gen": "honoured", "civil": "honoured"},
    "/db/PSLT": {"gen": "assigned", "civil": "assigned"},
    "/db/SBDO": {"civil": "honoured"},
    "/db/SDHY": {"gen": "honoured"},
    "/db/SDIS": {"gen": "honoured"},
    "/db/SDSP": {"gen": "honoured", "civil": "honoured"},
    "/db/SDST": {"gen": "honoured", "civil": "honoured"},
    "/db/SDVE": {"gen": "honoured", "civil": "honoured"},
    "/db/SDVI": {"gen": "honoured", "civil": "honoured"},
    "/db/SKEW": {"gen": "honoured", "civil": "honoured"},
    "/db/SLAN": {"gen": "assigned", "civil": "assigned"},
    "/db/SLANch": {"civil": "assigned"},
    "/db/SLANop": {"civil": "assigned"},
    "/db/SMCT": {"gen": "assigned", "civil": "assigned"},
    "/db/SMLC": {"gen": "assigned", "civil": "assigned"},
    "/db/SMPT": {"gen": "assigned", "civil": "assigned"},
    "/db/SPAN": {"civil": "assigned"},
    "/db/SPFC": {"gen": "assigned", "civil": "assigned"},
    "/db/SPLC": {"gen": "assigned", "civil": "honoured"},
    "/db/STAG": {"gen": "honoured", "civil": "honoured"},
    "/db/STBK": {"gen": "honoured", "civil": "honoured"},
    "/db/STLD": {"gen": "assigned", "civil": "assigned"},
    "/db/STMP": {"gen": "honoured", "civil": "honoured"},
    "/db/TDGR": {"gen": "honoured", "civil": "honoured"},
    "/db/TDME": {"gen": "assigned", "civil": "assigned"},
    "/db/TDMF": {"gen": "assigned", "civil": "honoured"},
    "/db/TDMT": {"gen": "assigned", "civil": "assigned"},
    "/db/TDNT": {"gen": "honoured", "civil": "honoured"},
    "/db/THFC": {"gen": "assigned", "civil": "honoured"},
    "/db/THGC": {"gen": "assigned", "civil": "assigned"},
    "/db/THIK": {"gen": "honoured", "civil": "honoured"},
    "/db/THIS": {"gen": "assigned", "civil": "assigned"},
    "/db/THMS": {"gen": "honoured", "civil": "honoured"},
    "/db/THNL": {"gen": "honoured", "civil": "honoured"},
    "/db/THSL": {"gen": "honoured", "civil": "honoured"},
    "/db/TSGR": {"gen": "assigned", "civil": "assigned"},
    "/db/ULFC": {"gen": "honoured", "civil": "honoured"},
    "/db/VBEM": {"gen": "honoured", "civil": "honoured"},
    "/db/VSEC": {"gen": "honoured", "civil": "honoured"},
    "/db/WMAK": {"gen": "honoured", "civil": "honoured"},
}


@dataclass(frozen=True)
class Operation:
    """One request to one table. ``records`` for POST/PUT, ``ids`` for DELETE."""

    endpoint: str  # "/db/NODE"
    method: str  # "POST", "PUT" or "DELETE"
    records: Optional[Mapping[str, Any]] = None
    ids: Optional[Sequence[Any]] = None
    label: Optional[str] = None  # the caller's name for it


@dataclass(frozen=True)
class Finding:
    """What :func:`validate` expects the product to do with one value.

    ``kind`` is ``"missing"`` (the value names a record that will not exist when
    the operation is sent) or ``"deleted"`` (a DELETE later in the list removes
    a record this one names). ``outcome`` is the measured answer:
    ``reference.on_missing`` for a missing value, ``reference.on_target_delete``
    for a deleted one, ``"unverified"`` where nothing was measured.
    """

    index: int  # position of the operation in the list given
    operation: Operation
    record_key: str
    reference: Reference
    value: Any
    kind: str
    outcome: str
    message: str


def dependencies() -> Dict[str, FrozenSet[str]]:
    """A copy of :data:`DEPENDENCIES`."""
    return dict(DEPENDENCIES)


def references(table: Optional[str] = None) -> List[Reference]:
    """:data:`REFERENCES`, or the ones whose records live in ``table``."""
    return [ref for ref in REFERENCES if table is None or ref.table == table]


def key_policy(endpoint: str, product: str) -> Optional[str]:
    """``"honoured"``, ``"assigned"``, or ``None`` where not measured.

    ``product`` is ``"gen"`` or ``"civil"`` (a :class:`midas_nx.Product`'s value).
    """
    return KEY_POLICY.get(endpoint, {}).get(getattr(product, "value", product))


def rank(endpoint: str) -> int:
    """0 for a table that names nothing, else one more than its deepest target."""
    seen: Dict[str, int] = {}

    def depth(table: str) -> int:
        if table not in seen:
            seen[table] = 1 + max((depth(t) for t in DEPENDENCIES.get(table, ())), default=-1)
        return seen[table]

    return depth(endpoint)


def _check_methods(operations: Sequence[Operation]) -> None:
    for op in operations:
        if op.method.upper() not in WRITE_METHODS + ("DELETE",):
            raise ValueError(f"{op.endpoint}: cannot order a {op.method} (POST, PUT or DELETE only)")


def order(operations: Sequence[Operation]) -> List[Operation]:
    """Deletes first, dependents before what they name; then writes, the reverse.

    Stable: operations of equal rank keep the caller's order, so a ``/db/UNIT``
    change placed first stays first. Raises ``ValueError`` on a method other
    than POST, PUT or DELETE.
    """
    _check_methods(operations)

    def key(item: "tuple[int, Operation]") -> "tuple[int, int, int]":
        index, op = item
        r = rank(op.endpoint)
        if op.method.upper() == "DELETE":
            return (0, -r, index)
        return (1, r, index)

    return [op for _, op in sorted(enumerate(operations), key=key)]


def _values(record: Any, path: str, each: bool) -> Iterator[Any]:
    """The values at ``path`` in one record; empty slots (None, 0, "") skipped."""
    nodes: List[Any] = [record]
    for part in path.split("."):
        is_list = part.endswith("[]")
        name = part[:-2] if is_list else part
        found: List[Any] = []
        for node in nodes:
            if not isinstance(node, Mapping) or name not in node:
                continue
            value = node[name]
            if is_list:
                found.extend(value if isinstance(value, list) else [])
            else:
                found.append(value)
        nodes = found
    for value in nodes:
        for item in value if each and isinstance(value, list) else [value]:
            if item is None or item == 0 or item == "" or isinstance(item, (Mapping, list)):
                continue
            yield item


def _names_written(endpoint: str, records: Mapping[str, Any]) -> Set[str]:
    """Every key and name a write to ``endpoint`` makes available as a target."""
    name_fields = {ref.name_field for ref in REFERENCES if endpoint in ref.targets and ref.name_field}
    out: Set[str] = set()
    for key, record in records.items():
        out.add(str(key))
        if isinstance(record, Mapping):
            out.update(str(record[f]) for f in name_fields if record.get(f) not in (None, ""))
    return out


def validate(
    operations: Sequence[Operation],
    existing: Optional[Mapping[str, Iterable[Any]]] = None,
) -> List[Finding]:
    """Report each reference the product will answer by refusing, orphaning or dropping.

    Offline and pure; it never raises for a finding, and returns them in
    operation order. The operations are read **in the order given** - run
    :func:`order` first to check what will actually be sent.

    ``existing`` maps a table to the ids or names already in the model (ids for
    a table named by id, ``NAME`` values for one named by name). A target table
    absent from it is unknown, and a value naming it is never reported missing:
    a write earlier in the list does not prove a record is the only one. Pass
    ``{"/db/NODE": []}`` to say a table is empty. A value of ``0``, ``""`` or
    ``None`` is an empty slot (``/db/ELEM`` pads ``NODE`` with zeros) and is
    skipped.

    A DELETE reports the records written earlier in the list that name what it
    removes, with the measured ``on_target_delete``. Records already in the
    model cannot be seen from here. A name-keyed target removed by a DELETE is
    tracked only when the list wrote it.
    """
    _check_methods(operations)
    known: Dict[str, Set[str]] = {table: {str(v) for v in values} for table, values in (existing or {}).items()}
    by_id: Dict[str, Dict[str, Set[str]]] = {}  # table -> key -> names written under it
    later: Dict[str, List[Tuple[int, Set[str]]]] = {}
    for index, op in enumerate(operations):
        if op.method.upper() in WRITE_METHODS and op.records:
            later.setdefault(op.endpoint, []).append((index, _names_written(op.endpoint, op.records)))

    findings: List[Finding] = []
    written: List[Tuple[int, Operation]] = []
    for index, op in enumerate(operations):
        method = op.method.upper()
        if method == "DELETE":
            removed = {str(i) for i in op.ids or ()}
            gone = set(removed)
            for key in removed:
                gone |= by_id.get(op.endpoint, {}).pop(key, set())
            if op.endpoint in known:
                known[op.endpoint] -= gone
            for earlier_index, earlier in written:
                for ref in references(earlier.endpoint):
                    if op.endpoint not in ref.targets:
                        continue
                    for record_key, record in (earlier.records or {}).items():
                        for value in _values(record, ref.field, ref.each):
                            if str(value) in gone:
                                outcome = ref.on_target_delete or "unverified"
                                findings.append(Finding(
                                    index, op, str(record_key), ref, value, "deleted", outcome,
                                    f"{op.endpoint} DELETE removes {value!r}, which {earlier.endpoint} "
                                    f"record {record_key} (operation {earlier_index}) names in "
                                    f"{ref.field}: {outcome}",
                                ))
            continue
        for record_key, record in (op.records or {}).items():
            for ref in references(op.endpoint):
                if not all(t in known for t in ref.targets):
                    continue
                for value in _values(record, ref.field, ref.each):
                    if any(str(value) in known[t] for t in ref.targets):
                        continue
                    created_later = [
                        i for t in ref.targets for i, names in later.get(t, []) if i > index and str(value) in names
                    ]
                    hint = f"; operation {created_later[0]} writes it later, see order()" if created_later else ""
                    findings.append(Finding(
                        index, op, str(record_key), ref, value, "missing", ref.on_missing,
                        f"{op.endpoint} record {record_key} names {value!r} in {ref.field}, "
                        f"which {'/'.join(ref.targets)} will not hold: {ref.on_missing}{hint}",
                    ))
        if op.records:
            names = _names_written(op.endpoint, op.records)
            if op.endpoint in known:
                known[op.endpoint] |= names
            for key, record in op.records.items():
                entry = by_id.setdefault(op.endpoint, {}).setdefault(str(key), set())
                entry |= _names_written(op.endpoint, {key: record}) - {str(key)}
            written.append((index, op))
    return findings
