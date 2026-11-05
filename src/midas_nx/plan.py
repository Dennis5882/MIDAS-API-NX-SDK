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
``/db/ELNK`` drop a missing entry silently. The other way round (2026-11-04 and
-05), a per-id DELETE of a node removes the elements on it; of a load case, each
load entry and combination entry naming it, and a record left with none; of a
group, nothing but the name, which is emptied; of a material, section or
thickness, nothing - the elements stay as orphans. A plate's ``SECT`` is a
``/db/THIK`` number and a beam's a ``/db/SECT`` one (told apart by analysis).
A record keyed by a node or element (:data:`KEY_REFERENCES`: loads, supports,
masses, end releases) goes when that node or element does, and a node takes
the element loads with its elements.
"""
from __future__ import annotations

import copy
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
    Union,
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
    this one, and ``None`` where not measured: ``deleted`` (the record went,
    or for a field inside a list the entry naming it, and the record once no
    entry was left), ``orphaned`` (it stayed, naming nothing) or ``cleared``
    (it stayed with the field emptied).

    ``targets_by`` says which of ``targets`` a value names when another field
    beside it decides: ``("TYPE", (("BEAM", ("/db/SECT",)), ...))``. A value of
    that field not listed names one of ``targets``; :meth:`targets_for` applies it.
    """

    table: str
    field: str
    targets: Tuple[str, ...]
    by: str  # "id" = the target's Assign key; "name" = its name_field
    name_field: Optional[str] = None
    each: bool = False  # the field is an array and each element is a reference
    on_missing: str = "unverified"
    on_target_delete: Optional[str] = None
    targets_by: Optional[Tuple[str, Tuple[Tuple[str, Tuple[str, ...]], ...]]] = None

    def targets_for(self, container: Any) -> Tuple[str, ...]:
        """The table(s) a value names, given the mapping that holds the field."""
        if self.targets_by and isinstance(container, Mapping):
            path, cases = self.targets_by
            for value, tables in cases:
                if container.get(path) == value:
                    return tables
        return self.targets


#: Every field reference the contracts record, sorted by table and field.
#: Held equal to them, and to npm's ``referenceFields``, by ``validate_contracts.py``.
REFERENCES: Tuple[Reference, ...] = (
    Reference(
        "/db/BMLD", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="cleared",
    ),
    Reference(
        "/db/BMLD", "ITEMS[].LCNAME", ("/db/STLD",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="deleted",
    ),
    Reference(
        "/db/CNLD", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="cleared",
    ),
    Reference(
        "/db/CNLD", "ITEMS[].LCNAME", ("/db/STLD",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="deleted",
    ),
    Reference(
        "/db/CONS", "ITEMS[].GROUP_NAME", ("/db/BNGR",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="cleared",
    ),
    Reference("/db/ELEM", "MATL", ("/db/MATL",), "id", on_missing="stored", on_target_delete="orphaned"),
    Reference("/db/ELEM", "NODE", ("/db/NODE",), "id", each=True, on_missing="refused", on_target_delete="deleted"),
    Reference(
        "/db/ELEM", "SECT", ("/db/SECT", "/db/THIK"), "id", on_missing="stored", on_target_delete="orphaned",
        targets_by=("TYPE", (("BEAM", ("/db/SECT",)), ("PLATE", ("/db/THIK",)))),
    ),
    Reference(
        "/db/ELNK", "BNGR_NAME", ("/db/BNGR",), "name",
        name_field="NAME", on_missing="dropped", on_target_delete="cleared",
    ),
    Reference("/db/ELNK", "NODE", ("/db/NODE",), "id", each=True, on_missing="refused"),
    Reference(
        "/db/FRLS", "ITEMS[].GROUP_NAME", ("/db/BNGR",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="cleared",
    ),
    Reference("/db/GRUP", "E_LIST", ("/db/ELEM",), "id", each=True, on_missing="dropped"),
    Reference("/db/GRUP", "N_LIST", ("/db/NODE",), "id", each=True, on_missing="dropped"),
    Reference(
        "/db/LCOM-GEN", "vCOMB[].LCNAME", ("/db/STLD",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="deleted",
    ),
    Reference(
        "/db/PRES", "ITEMS[].GROUP_NAME", ("/db/LDGR",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="cleared",
    ),
    Reference(
        "/db/PRES", "ITEMS[].LCNAME", ("/db/STLD",), "name",
        name_field="NAME", on_missing="refused", on_target_delete="deleted",
    ),
)


#: The tables whose Assign key is a node or element id, as :class:`Reference`
#: rows with ``field`` ``""`` (the record key), from the contracts' ``recordKey``.
#: Held equal to them, and to npm's ``keyReferences``, by ``validate_contracts.py``.
#: Measured on Gen NX and Civil NX: a key naming no node or element is refused
#: (2026-11-04; /db/NMAS not tried), and deleting the node or element deletes the
#: record keyed by it (2026-11-05).
KEY_REFERENCES: Tuple[Reference, ...] = (
    Reference("/db/BMLD", "", ("/db/ELEM",), "id", on_missing="refused", on_target_delete="deleted"),
    Reference("/db/CNLD", "", ("/db/NODE",), "id", on_missing="refused", on_target_delete="deleted"),
    Reference("/db/CONS", "", ("/db/NODE",), "id", on_missing="refused", on_target_delete="deleted"),
    Reference("/db/FRLS", "", ("/db/ELEM",), "id", on_missing="refused", on_target_delete="deleted"),
    Reference("/db/NMAS", "", ("/db/NODE",), "id", on_target_delete="deleted"),
    Reference("/db/PRES", "", ("/db/ELEM",), "id", on_missing="refused", on_target_delete="deleted"),
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


def key_references(table: Optional[str] = None) -> List[Reference]:
    """:data:`KEY_REFERENCES`, or the one for ``table``: a record keyed by a node
    or element id, whose ``field`` is ``""``."""
    return [ref for ref in KEY_REFERENCES if table is None or ref.table == table]


def _all_references(table: str) -> List[Reference]:
    return references(table) + key_references(table)


def _ref_values(ref: Reference, record_key: str, record: Any) -> Iterator[Tuple[Any, Mapping[str, Any]]]:
    """What ``ref`` reads from one record: its key for a key reference, else the field."""
    if not ref.field:
        yield record_key, (record if isinstance(record, Mapping) else {})
    else:
        yield from _values(record, ref.field, ref.each)


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


def _values(record: Any, path: str, each: bool) -> Iterator[Tuple[Any, Mapping[str, Any]]]:
    """``(value, the mapping holding it)`` at ``path`` in one record; empty
    slots (None, 0, "") skipped."""
    *parents, leaf = path.split(".")
    nodes: List[Any] = [record]
    for part in parents:
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
    for node in nodes:
        if not isinstance(node, Mapping) or leaf not in node:
            continue
        value = node[leaf]
        for item in value if each and isinstance(value, list) else [value]:
            if item is None or item == 0 or item == "" or isinstance(item, (Mapping, list)):
                continue
            yield item, node


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
    existing: Optional[Mapping[str, Union[Iterable[Any], Mapping[Any, Any]]]] = None,
) -> List[Finding]:
    """Report each reference the product will answer by refusing, orphaning or dropping.

    Offline and pure; it never raises for a finding, and returns them in
    operation order. The operations are read **in the order given** - run
    :func:`order` first to check what will actually be sent.

    ``existing`` describes what is already in the model, per table, as either
    the ids or names in it (ids for a table named by id, ``NAME`` values for one
    named by name) or its records, keyed by id, as a GET of the table returns
    them. A target table absent from it is unknown, and a value naming it is
    never reported missing: a write earlier in the list does not prove a record
    is the only one. Pass ``{"/db/NODE": []}`` to say a table is empty. A value
    of ``0``, ``""`` or ``None`` is an empty slot (``/db/ELEM`` pads ``NODE``
    with zeros) and is skipped.

    A DELETE reports every record that names what it removes and is still there
    when it is sent: one written earlier in the list, or one passed as a record
    in ``existing``. A table given only as ids has no records to look in. Where
    the measured ``on_target_delete`` is ``"deleted"``, the records it takes with
    it are gone from then on.
    """
    _check_methods(operations)
    known: Dict[str, Set[str]] = {}
    state: Dict[str, Dict[str, Tuple[Optional[int], Any]]] = {}  # table -> key -> (operation index or None, record)
    for table, given in (existing or {}).items():
        if isinstance(given, Mapping):
            records = {str(key): record for key, record in given.items()}
            known[table] = _names_written(table, records)
            state[table] = {key: (None, record) for key, record in records.items()}
        else:
            known[table] = {str(v) for v in given}
    later: Dict[str, List[Tuple[int, Set[str]]]] = {}
    for index, op in enumerate(operations):
        if op.method.upper() in WRITE_METHODS and op.records:
            later.setdefault(op.endpoint, []).append((index, _names_written(op.endpoint, op.records)))

    findings: List[Finding] = []
    for index, op in enumerate(operations):
        method = op.method.upper()
        if method == "DELETE":
            table_state = state.get(op.endpoint, {})
            gone: Set[str] = set()
            for key in (str(i) for i in op.ids or ()):
                gone.add(key)
                if key in table_state:
                    gone |= _names_written(op.endpoint, {key: table_state.pop(key)[1]})
            if op.endpoint in known:
                known[op.endpoint] -= gone
            findings.extend(_deleted_findings(index, op, gone, state, known))
            continue
        for record_key, record in (op.records or {}).items():
            if method == "PUT":  # a PUT merges, so a field it leaves out still decides targets_by
                previous = state.get(op.endpoint, {}).get(str(record_key))
                if previous and isinstance(previous[1], Mapping) and isinstance(record, Mapping):
                    record = {**previous[1], **record}
            for ref in _all_references(op.endpoint):
                for value, holder in _ref_values(ref, str(record_key), record):
                    targets = ref.targets_for(holder)
                    if not all(t in known for t in targets) or any(str(value) in known[t] for t in targets):
                        continue
                    created_later = [
                        i for t in targets for i, names in later.get(t, []) if i > index and str(value) in names
                    ]
                    hint = f"; operation {created_later[0]} writes it later, see order()" if created_later else ""
                    findings.append(Finding(
                        index, op, str(record_key), ref, value, "missing", ref.on_missing,
                        f"{op.endpoint} record {record_key} names {value!r} in {ref.field or 'its key'}, "
                        f"which {'/'.join(targets)} will not hold: {ref.on_missing}{hint}",
                    ))
        if op.records:
            if op.endpoint in known:
                known[op.endpoint] |= _names_written(op.endpoint, op.records)
            table_state = state.setdefault(op.endpoint, {})
            for key, record in op.records.items():
                previous = table_state.get(str(key))
                if method == "PUT" and previous and isinstance(previous[1], Mapping) and isinstance(record, Mapping):
                    record = {**previous[1], **record}
                table_state[str(key)] = (index, record)
    return findings


def _deleted_findings(
    index: int,
    op: Operation,
    gone: Set[str],
    state: Dict[str, Dict[str, Tuple[Optional[int], Any]]],
    known: Dict[str, Set[str]],
) -> List[Finding]:
    """The records still present that name something ``op`` removes, and what
    the measured ``on_target_delete`` then does to them in ``state``. A record
    that goes with it is followed in turn: a node takes its elements, and an
    element the loads keyed by it."""
    findings: List[Finding] = []
    queue: List[Tuple[str, Set[str]]] = [(op.endpoint, gone)]
    while queue:
        target, removed = queue.pop(0)
        effects: Dict[Tuple[str, str], List[Tuple[Reference, Mapping[str, Any]]]] = {}
        for table, records in state.items():
            refs = [ref for ref in _all_references(table) if target in ref.targets]
            for record_key, (origin, record) in records.items():
                where = "already in the model" if origin is None else f"operation {origin}"
                for ref in refs:
                    for value, holder in _ref_values(ref, record_key, record):
                        if str(value) not in removed or target not in ref.targets_for(holder):
                            continue
                        outcome = ref.on_target_delete or "unverified"
                        what = f"removes {value!r}" if target == op.endpoint else f"takes {target} {value!r} with it"
                        findings.append(Finding(
                            index, op, record_key, ref, value, "deleted", outcome,
                            f"{op.endpoint} DELETE {what}, which {table} record {record_key} "
                            f"({where}) names in {ref.field or 'its key'}: {outcome}",
                        ))
                        effects.setdefault((table, record_key), []).append((ref, holder))
        for (table, record_key), hits in effects.items():
            dropped = _apply_delete_effects(state, known, table, record_key, hits)
            if dropped:
                queue.append((table, dropped))
    return findings


def _apply_delete_effects(
    state: Dict[str, Dict[str, Tuple[Optional[int], Any]]],
    known: Dict[str, Set[str]],
    table: str,
    record_key: str,
    hits: List[Tuple[Reference, Mapping[str, Any]]],
) -> Optional[Set[str]]:
    """Change one record in ``state`` as the product does: drop it or the list
    entries (``deleted``), or empty the fields (``cleared``). The record is
    replaced by a changed copy, never changed in place, since it may be the
    caller's. A path deeper than one list is left as it was. Returns the key
    and names of the record when it is dropped, else ``None``."""
    origin, record = state[table][record_key]
    drop_record = False
    cleared: List[Tuple[Optional[str], int, str]] = []  # (list name, position, field)
    dropped: Dict[str, Set[int]] = {}
    for ref, holder in hits:
        leaf = ref.field.rsplit(".", 1)[-1]
        if ref.on_target_delete not in ("deleted", "cleared"):
            continue
        if "[]" not in ref.field:
            if ref.on_target_delete == "deleted":
                drop_record = True
            else:
                cleared.append((None, -1, leaf))
            continue
        list_name, rest = ref.field.split("[].", 1)
        entries = record.get(list_name) if isinstance(record, Mapping) else None
        if "." in rest or not isinstance(entries, list):
            continue
        position = next((i for i, entry in enumerate(entries) if entry is holder), None)
        if position is None:
            continue
        if ref.on_target_delete == "deleted":
            dropped.setdefault(list_name, set()).add(position)
        else:
            cleared.append((list_name, position, leaf))
    if not (drop_record or cleared or dropped):
        return None
    if not drop_record:
        changed = copy.deepcopy(dict(record))
        for holder_list, position, leaf in cleared:
            (changed if holder_list is None else changed[holder_list][position])[leaf] = ""
        for list_name, positions in dropped.items():
            changed[list_name] = [e for i, e in enumerate(changed[list_name]) if i not in positions]
            drop_record = drop_record or not changed[list_name]
        if not drop_record:
            state[table][record_key] = (origin, changed)
            return None
    names = _names_written(table, {record_key: record})
    known.get(table, set()).difference_update(names)
    del state[table][record_key]
    return names
