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


def test_npm_publishes_the_same_graph():
    text = (ROOT / "packages" / "typescript" / "src" / "generated" / "references.ts").read_text(encoding="utf-8")
    body = text[text.index("= ") + 2 : text.rindex(" as const")]
    assert {k: frozenset(v) for k, v in json.loads(body).items()} == plan.dependencies()
