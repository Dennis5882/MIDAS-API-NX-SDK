import json
import sys
from pathlib import Path

import pytest

from midas_nx import plan
from midas_nx.plan import Operation

ROOT = Path(__file__).resolve().parents[1]


def _contract_graph():
    sys.path.insert(0, str(ROOT / "scripts"))
    import yaml
    from reference_graph import reference_graph

    contracts = (
        yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in sorted((ROOT / "contracts" / "endpoints").glob("*.yaml"))
    )
    return {k: frozenset(v) for k, v in reference_graph(contracts).items()}


def test_dependencies_equal_the_contracts():
    assert plan.dependencies() == _contract_graph()


def test_writes_follow_what_they_name_and_keep_the_callers_order_otherwise():
    ops = [
        Operation("/db/BMLD", "POST", label="load"),
        Operation("/db/ELEM", "POST", label="elem"),
        Operation("/db/UNIT", "PUT", label="unit"),
        Operation("/db/STLD", "POST", label="case"),
        Operation("/db/NODE", "POST", label="node"),
        Operation("/db/MATL", "POST", label="matl"),
    ]
    assert [op.label for op in plan.order(ops)] == ["unit", "case", "node", "matl", "elem", "load"]


def test_deletes_come_first_and_dependents_before_what_they_name():
    ops = [
        Operation("/db/NODE", "POST", label="node+"),
        Operation("/db/NODE", "DELETE", ids=[3], label="node-"),
        Operation("/db/ELEM", "DELETE", ids=[1], label="elem-"),
        Operation("/db/BMLD", "DELETE", ids=[1], label="load-"),
    ]
    assert [op.label for op in plan.order(ops)] == ["load-", "elem-", "node-", "node+"]


def test_rank_counts_the_deepest_chain():
    assert plan.rank("/db/NODE") == 0
    assert plan.rank("/db/ELEM") == 1
    assert plan.rank("/db/BMLD") == 2
    assert plan.rank("/db/NOT-A-TABLE") == 0


def test_order_refuses_a_get():
    with pytest.raises(ValueError):
        plan.order([Operation("/db/NODE", "GET")])


def _npm_export(name):
    text = (ROOT / "packages" / "typescript" / "src" / "generated" / "references.ts").read_text(encoding="utf-8")
    start = text.index("= ", text.index(f"export const {name}")) + 2
    return json.loads(text[start : text.index(" as const;", start)])


def test_npm_publishes_the_same_graph():
    assert {k: frozenset(v) for k, v in _npm_export("referenceGraph").items()} == plan.dependencies()


def test_references_are_the_contracts_rows_and_npm_publishes_the_same():
    sys.path.insert(0, str(ROOT / "scripts"))
    import yaml
    from reference_graph import reference_fields

    rows = reference_fields(
        yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in sorted((ROOT / "contracts" / "endpoints").glob("*.yaml"))
    )
    assert [(r.table, r.field, r.on_missing) for r in plan.references()] == [
        (r["table"], r["field"], r["onMissing"]) for r in rows
    ]
    assert _npm_export("referenceFields") == rows
    assert {r.field for r in plan.references("/db/ELEM")} == {"MATL", "NODE", "SECT"}


# One scenario, twinned in packages/typescript/tests/plan.test.ts.
MODEL = {"/db/NODE": [1, 2], "/db/MATL": [1], "/db/SECT": [1], "/db/THIK": [], "/db/STLD": ["DL"], "/db/LDGR": []}


def test_validate_reports_what_the_product_will_do_with_a_missing_reference():
    ops = [
        Operation("/db/ELEM", "POST", records={"1": {"TYPE": "BEAM", "MATL": 9, "SECT": 1, "NODE": [1, 2, 0, 0]}}),
        Operation("/db/ELEM", "POST", records={"2": {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 3]}}),
        Operation("/db/CNLD", "POST", records={"1": {"ITEMS": [{"ID": 1, "LCNAME": "LL", "FZ": -1}]}}),
        Operation("/db/STLD", "POST", records={"2": {"NAME": "LL", "TYPE": "L"}}),
        Operation("/db/GRUP", "POST", records={"1": {"NAME": "G", "N_LIST": [1, 3]}}),
    ]
    found = [(f.index, f.reference.field, f.value, f.outcome) for f in plan.validate(ops, MODEL)]
    assert found == [
        (0, "MATL", 9, "stored"),  # the padding zeros in NODE are not reported
        (1, "NODE", 3, "refused"),
        (2, "ITEMS[].LCNAME", "LL", "refused"),
        (4, "N_LIST", 3, "dropped"),  # E_LIST absent: nothing to check
    ]
    assert "operation 3 writes it later" in plan.validate(ops, MODEL)[2].message
    # Ordered, the load case is written first and only the missing node stays.
    assert [f.reference.field for f in plan.validate(plan.order(ops), MODEL)] == ["MATL", "NODE", "N_LIST"]


def test_validate_reports_nothing_for_a_table_it_was_not_told_about():
    ops = [Operation("/db/ELEM", "POST", records={"1": {"MATL": 9, "SECT": 9, "NODE": [7, 8]}})]
    assert plan.validate(ops) == []
    assert [f.reference.field for f in plan.validate(ops, {"/db/NODE": []})] == ["NODE", "NODE"]


def test_validate_reports_a_dropped_group_entry():
    ops = [Operation("/db/GRUP", "POST", records={"1": {"NAME": "G", "N_LIST": [1, 3], "E_LIST": [5]}})]
    found = plan.validate(ops, {"/db/NODE": [1], "/db/ELEM": [5]})
    assert [(f.reference.field, f.value, f.outcome) for f in found] == [("N_LIST", 3, "dropped")]


def test_validate_reports_what_a_delete_does_to_records_written_before_it():
    ops = [
        Operation("/db/ELEM", "POST", records={"1": {"MATL": 1, "SECT": 1, "NODE": [1, 2]}}),
        Operation("/db/CNLD", "POST", records={"1": {"ITEMS": [{"ID": 1, "LCNAME": "DL"}]}}),
        Operation("/db/NODE", "DELETE", ids=[2]),
        Operation("/db/MATL", "DELETE", ids=[1]),
        Operation("/db/STLD", "DELETE", ids=[1]),
    ]
    found = [(f.index, f.kind, f.reference.field, f.outcome) for f in plan.validate(ops, MODEL)]
    # /db/STLD is named by NAME and the list never wrote record 1, so its name is unknown.
    assert found == [(2, "deleted", "NODE", "deleted"), (3, "deleted", "MATL", "orphaned")]
    ops[4] = Operation("/db/STLD", "DELETE", ids=[1])
    ops.insert(0, Operation("/db/STLD", "POST", records={"1": {"NAME": "DL"}}))
    assert [(f.kind, f.reference.field, f.outcome) for f in plan.validate(ops, MODEL)][-1] == (
        "deleted", "ITEMS[].LCNAME", "deleted",
    )
    # And a write after the delete is missing again.
    ops.append(Operation("/db/ELEM", "POST", records={"2": {"MATL": 1, "SECT": 1, "NODE": [1, 2]}}))
    tail = [(f.index, f.reference.field, f.value) for f in plan.validate(ops, MODEL) if f.kind == "missing"]
    assert tail == [(6, "MATL", 1), (6, "NODE", 2)]


def test_validate_refuses_a_get():
    with pytest.raises(ValueError):
        plan.validate([Operation("/db/NODE", "GET")])


def test_key_policy_is_per_product_and_npm_publishes_the_same():
    from midas_nx import Product

    assert plan.key_policy("/db/STLD", "gen") == "assigned"
    assert plan.key_policy("/db/NODE", Product.CIVIL) == "honoured"
    assert (plan.key_policy("/db/GSTP", "gen"), plan.key_policy("/db/GSTP", "civil")) == ("assigned", "honoured")
    assert plan.key_policy("/db/NOT-A-TABLE", "gen") is None
    assert _npm_export("keyPolicies") == plan.KEY_POLICY
