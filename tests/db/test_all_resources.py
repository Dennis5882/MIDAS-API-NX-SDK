import json
from pathlib import Path

from midas_nx.db import all_resources
from midas_nx.db.base import DbResource

ROOT = Path(__file__).resolve().parents[2]


def _published():
    data = json.loads((ROOT / "schema" / "typescript-resources.json").read_text(encoding="utf-8"))
    return {r["endpoint"]: r for r in data["resources"]}


def test_lists_exactly_the_resources_npm_publishes():
    # npm's resources.db / resources.design tree is generated from the same set,
    # so the two languages' lists cannot drift apart.
    assert set(all_resources()) == set(_published())


def test_each_entry_is_the_class_for_its_endpoint():
    published = _published()
    for endpoint, cls in all_resources().items():
        assert issubclass(cls, DbResource)
        assert cls.ENDPOINT == endpoint
        assert cls.__name__ == published[endpoint]["className"]
        assert sorted(cls.PRODUCTS) == sorted(published[endpoint]["products"])
        assert sorted(cls.METHODS) == sorted(published[endpoint]["methods"])


def test_includes_the_modules_a_caller_is_likely_to_miss():
    resources = all_resources()
    # db.properties (MATL, SECT) and the design chapters live off the obvious path.
    assert {"/db/MATL", "/db/SECT", "/db/NODE"} <= resources.keys()
    assert any(e.startswith("/DESIGN/") for e in resources)


def test_returns_a_fresh_dict_sorted_by_endpoint():
    first = all_resources()
    first.clear()
    second = all_resources()
    assert second
    assert list(second) == sorted(second)
