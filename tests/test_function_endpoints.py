"""Regression tests for generic plain-function parity discovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from function_endpoints import (
    ResourceEndpoint,
    ResourceSurface,
    python_function_surfaces,
    typescript_function_surfaces,
)
from promote_contract import (
    _ambiguous_draft_key,
    _non_db_delete_response_unknown,
    _non_db_resource_is_modelled,
)


def test_promotion_rejects_a_manual_row_that_still_names_multiple_fields():
    assert _ambiguous_draft_key(
        "fields:\n  - key: FIRST\n    properties:\n      - key: 'SECOND\" / \"THIRD'\n"
    ) == 'SECOND" / "THIRD'
    assert _ambiguous_draft_key("fields:\n  - key: FIRST\n    properties:\n      - key: SECOND_2\n") is None


def test_plain_function_discovery_resolves_constant_routes_and_npm_metadata(tmp_path):
    python_root = tmp_path / "midas_nx"
    python_root.mkdir()
    (python_root / "operations.py").write_text(
        '''_BASE = "/DESIGN/TEST"

def read():
    return _get(f"{_BASE}/READ")

def write():
    return _post(f"{_BASE}/WRITE", {})

def table():
    return client.request("POST", "/post/TABLE", {})
''',
        encoding="utf-8",
    )

    typescript_root = tmp_path / "typescript"
    generated = typescript_root / "generated"
    generated.mkdir(parents=True)
    (generated / "operations.ts").write_text(
        'defineGetOperation({"endpoint":"/DESIGN/TEST/READ","method":"GET","products":["gen"]})\n'
        'definePostOperation({"endpoint":"/DESIGN/TEST/WRITE","method":"POST","products":["gen"]})\n',
        encoding="utf-8",
    )
    (typescript_root / "doc.ts").write_text('post("/doc/OPEN", "", options);\n', encoding="utf-8")
    (typescript_root / "post.ts").write_text('getTableAt("/post/TABLE", type, options);\n', encoding="utf-8")

    python = python_function_surfaces(python_root)
    typescript = typescript_function_surfaces(typescript_root)

    assert python["/DESIGN/TEST/READ"].methods == {"GET"}
    assert python["/DESIGN/TEST/WRITE"].methods == {"POST"}
    assert python["/post/TABLE"].methods == {"POST"}
    assert typescript["/DESIGN/TEST/READ"].methods == {"GET"}
    assert typescript["/DESIGN/TEST/READ"].products == {"gen"}
    assert typescript["/DESIGN/TEST/WRITE"].methods == {"POST"}
    assert typescript["/doc/OPEN"].methods == {"POST"}
    assert typescript["/post/TABLE"].methods == {"POST"}


def test_non_db_resource_delete_never_inherits_db_delete_evidence():
    surface = ResourceSurface(
        methods=frozenset({"DELETE", "GET", "POST", "PUT"}),
        products=frozenset({"civil", "gen"}),
        entries=("ExampleResource",),
    )
    reason = _non_db_resource_is_modelled(
        "/DESIGN/EXAMPLE",
        {"DELETE", "GET", "POST", "PUT"},
        {"civil", "gen"},
        {"/DESIGN/EXAMPLE": ResourceEndpoint(surface, surface)},
    )

    assert reason is None

    promoted = _non_db_delete_response_unknown(
        """  - method: DELETE
    risk: destructive
    mitigation: none
    request:
      wrapper: none
    response:
      wrapper: table
      keyStability: stable
"""
    )

    assert "wrapper: unknown" in promoted
    assert "deletion scope or response shape" in promoted
    assert "keyStability" not in promoted
