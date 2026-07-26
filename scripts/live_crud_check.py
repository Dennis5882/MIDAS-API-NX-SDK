"""Live create -> read -> update -> read -> delete -> read round trip for a
curated set of /db/* resources, against a real Gen NX / Civil NX session.

The read-only counterpart, scripts/live_readonly_sweep.py, proves an endpoint
exists and answers. This proves the SDK's *write* shapes are the ones the
server actually accepts: that ``create()``'s "Assign" body lands, that a
``get()`` echoes back what was written, that ``update()`` changes it, and that
``delete()`` removes it. A TypedDict transcribed with a wrong field name will
pass every mocked test in tests/ and only fail here.

DESTRUCTIVE. It calls /doc/NEW and builds a throwaway model. Never point it at
a session holding work you care about.

⚠️ /doc/NEW on a document with unsaved changes raises MIDAS's own save-changes
dialog, and that dialog blocks the entire API session until a human clicks it -
the next call fails for reasons unrelated to itself. Have a human present, or
start from a saved document.

⚠️ --save-as exists to clear that dialog by saving first, but /doc/SAVEAS is
not safe to automate blind: given a path NX dislikes it raises a modal
"invalid path" error dialog, blocks the session until someone clicks it, and
then returns {"message": "... command complete"} anyway - the same string a
real save returns, with no file on disk. Verified 2026-07-26 on Civil NX.
Check the file exists yourself afterwards; do not trust the response.

Run with the dev environment active (``pip install -e ".[dev]"``), e.g.:
    python scripts/live_crud_check.py --product civil
    python scripts/live_crud_check.py --product civil --save-as C:/tmp/scratch.mcb
    python scripts/live_crud_check.py --product civil --out crud.json

Exit code 0 -> every step of every case passed.
Exit code 1 -> at least one step failed (see the report).
Exit code 2 -> couldn't connect, or the server rejected the connection.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from midas_nx import doc
from midas_nx.client import MidasAPIError, MidasClient
from midas_nx.db.boundary import Constraint
from midas_nx.db.moving_loads import MovingLoadCode
from midas_nx.db.node_element import Element, Node, Skew
from midas_nx.db.project import BoundaryGroup, LoadGroup, StructureGroup, Unit
from midas_nx.db.properties.material import Material
from midas_nx.db.properties.section import Section
from midas_nx.db.static_loads import BeamLoad, NodalLoad, SelfWeight, StaticLoadCase

sys.stdout.reconfigure(encoding="utf-8")

SIZE, HEIGHT = 0.6, 3.2


class Case:
    """One resource's round trip: what to write, what to change, what to check.

    ``probe`` pulls the single value the assertions compare on, so a case
    stays readable even when the payload is deeply nested.
    """

    def __init__(
        self,
        resource,
        create_payload: dict,
        update_payload: dict,
        probe: Callable[[dict], Any],
        expect_created: Any,
        expect_updated: Any,
        item_id: int = 1,
    ) -> None:
        self.resource = resource
        self.create_payload = create_payload
        self.update_payload = update_payload
        self.probe = probe
        self.expect_created = expect_created
        self.expect_updated = expect_updated
        self.item_id = item_id


def _cases() -> List[Case]:
    """Curated, not exhaustive: one case per write-shape family, biased toward
    the endpoints a real modelling script actually touches."""
    return [
        Case(
            StructureGroup,
            {"NAME": "SG_CRUD"}, {"NAME": "SG_CRUD_2"},
            lambda p: p.get("NAME"), "SG_CRUD", "SG_CRUD_2",
        ),
        Case(
            BoundaryGroup,
            {"NAME": "BG_CRUD"}, {"NAME": "BG_CRUD_2"},
            lambda p: p.get("NAME"), "BG_CRUD", "BG_CRUD_2",
        ),
        Case(
            LoadGroup,
            {"NAME": "LG_CRUD"}, {"NAME": "LG_CRUD_2"},
            lambda p: p.get("NAME"), "LG_CRUD", "LG_CRUD_2",
        ),
        Case(
            Node,
            {"X": 1.0, "Y": 2.0, "Z": 3.0}, {"X": 1.0, "Y": 2.0, "Z": 9.5},
            lambda p: p.get("Z"), 3.0, 9.5,
            item_id=101,
        ),
        # Keyed by node id: node 2 is seeded and no case deletes it.
        Case(
            Skew,
            {"iMETHOD": 1, "ANGLE_X": 0, "ANGLE_Y": 0, "ANGLE_Z": 30},
            {"iMETHOD": 1, "ANGLE_X": 0, "ANGLE_Y": 0, "ANGLE_Z": 45},
            lambda p: p.get("ANGLE_Z"), 30, 45,
            item_id=2,
        ),
        # /db/STLD renumbers: the server assigns NO sequentially rather than
        # honouring the "Assign" key, so this has to be the next free slot
        # after the two the seed creates.
        Case(
            StaticLoadCase,
            {"NAME": "CRUDCASE", "TYPE": "L", "DESC": "crud"},
            {"NAME": "CRUDCASE", "TYPE": "L", "DESC": "crud updated"},
            lambda p: p.get("DESC"), "crud", "crud updated",
            item_id=3,
        ),
        # Loads reference LC_SCRATCH, which the seed creates and nothing deletes.
        Case(
            NodalLoad,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "FZ": -10.0}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "FZ": -25.0}]},
            lambda p: p["ITEMS"][0].get("FZ"), -10.0, -25.0,
            item_id=2,
        ),
        Case(
            BeamLoad,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "CMD": "BEAM", "TYPE": "UNILOAD",
                        "DIRECTION": "GZ", "D": [0, 1, 0, 0], "P": [-5.0, -5.0, 0, 0]}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "CMD": "BEAM", "TYPE": "UNILOAD",
                        "DIRECTION": "GZ", "D": [0, 1, 0, 0], "P": [-8.0, -8.0, 0, 0]}]},
            lambda p: p["ITEMS"][0]["P"][0], -5.0, -8.0,
        ),
        # CONSTRAINT must be exactly 7 characters (Dx Dy Dz Rx Ry Rz W). A
        # 6-character string is rejected with "[Error] Constraint Condition
        # has(have) been incorrectly entered." rather than being padded.
        Case(
            Constraint,
            {"ITEMS": [{"ID": 2, "CONSTRAINT": "1110000"}]},
            {"ITEMS": [{"ID": 2, "CONSTRAINT": "1111111"}]},
            lambda p: p["ITEMS"][0].get("CONSTRAINT"), "1110000", "1111111",
            item_id=2,
        ),
    ]


def _civil_only_cases() -> List[Case]:
    return [
        Case(
            MovingLoadCode,
            {"CODE": "KOREA"}, {"CODE": "AASHTO LRFD"},
            lambda p: p.get("CODE"), "KOREA", "AASHTO LRFD",
        ),
    ]


def _seed_model(client: MidasClient) -> None:
    """Minimum model the load/boundary cases need to attach to."""
    Unit.update({1: {"DIST": "M", "FORCE": "KN"}}, client=client)
    Material.create(
        {1: {"TYPE": "CONC", "NAME": "C24",
             "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}},
        client=client,
    )
    Section.create(
        {1: {"SECTTYPE": "DBUSER", "SECT_NAME": "Column",
             "SECT_BEFORE": {"USE_SHEAR_DEFORM": True, "SHAPE": "SB", "DATATYPE": 2,
                             "SECT_I": {"vSIZE": [SIZE, SIZE]}}}},
        client=client,
    )
    Node.create({1: {"X": 0, "Y": 0, "Z": 0}, 2: {"X": 0, "Y": 0, "Z": HEIGHT}}, client=client)
    Element.create({1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]}}, client=client)
    Constraint.create({1: {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111"}]}}, client=client)
    StaticLoadCase.create({1: {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"}}, client=client)
    # A load case the load cases below can attach to, that no case deletes.
    StaticLoadCase.create({2: {"NAME": "LC_SCRATCH", "TYPE": "L", "DESC": "crud fixture"}},
                          client=client)
    SelfWeight.create({1: {"LCNAME": "DL", "FV": [0, 0, -1]}}, client=client)


def _run_case(case: Case, client: MidasClient) -> Dict[str, Any]:
    res = case.resource
    row: Dict[str, Any] = {
        "endpoint": res.ENDPOINT,
        "name": res.NAME,
        "id": case.item_id,
        "steps": {},
    }

    def record(step: str, fn) -> Any:
        try:
            value = fn()
        except MidasAPIError as exc:
            row["steps"][step] = {"ok": False, "error": str(exc)[:200]}
            raise
        row["steps"][step] = {"ok": True}
        return value

    try:
        record("create", lambda: res.create({case.item_id: case.create_payload}, client=client))

        def check_created():
            got = res.items(client=client).get(case.item_id)
            if got is None:
                raise MidasAPIError(f"{res.ENDPOINT}: id {case.item_id} missing after create")
            actual = case.probe(got)
            if actual != case.expect_created:
                raise MidasAPIError(
                    f"{res.ENDPOINT}: wrote {case.expect_created!r}, read back {actual!r}"
                )
            return actual

        record("read_back", check_created)

        if "PUT" in res.METHODS:
            record("update", lambda: res.update({case.item_id: case.update_payload}, client=client))

            def check_updated():
                got = res.items(client=client).get(case.item_id, {})
                actual = case.probe(got)
                if actual != case.expect_updated:
                    raise MidasAPIError(
                        f"{res.ENDPOINT}: updated to {case.expect_updated!r}, read back {actual!r}"
                    )
                return actual

            record("read_updated", check_updated)
        else:
            row["steps"]["update"] = {"ok": True, "skipped": "endpoint has no PUT"}

        if "DELETE" in res.METHODS:
            record("delete", lambda: res.delete([case.item_id], client=client))

            def check_deleted():
                if case.item_id in res.items(client=client):
                    raise MidasAPIError(f"{res.ENDPOINT}: id {case.item_id} still present after delete")
                return True

            record("read_deleted", check_deleted)
        else:
            row["steps"]["delete"] = {"ok": True, "skipped": "endpoint has no DELETE"}
    except MidasAPIError:
        pass

    row["ok"] = all(step.get("ok") for step in row["steps"].values())
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=["gen", "civil"], required=True)
    parser.add_argument("--mapi-key", help="defaults to MIDAS_MAPI_KEY env var")
    parser.add_argument("--base-url", help="defaults to MIDAS_BASE_URL env var")
    parser.add_argument(
        "--save-as",
        help="save the currently open document here before /doc/NEW, so a "
        "save-changes dialog can't block the session",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--out", help="path to write the report JSON (optional)")
    args = parser.parse_args()

    client = MidasClient(
        mapi_key=args.mapi_key, base_url=args.base_url,
        product=args.product, timeout=args.timeout,
    )
    try:
        health = client.verify_connection()
    except MidasAPIError as exc:
        print(f"Could not reach the MIDAS NX Open API server: {exc}", file=sys.stderr)
        return 2
    if health.get("status") != "connected":
        print(f"Server reachable but not connected: {health}", file=sys.stderr)
        return 2

    if args.save_as:
        print(f"Saving the open document to {args.save_as} first...")
        doc.save_as(args.save_as, client=client)

    print("Creating a throwaway document and seeding a minimal model...")
    doc.new_project(client=client)
    _seed_model(client)

    cases = _cases()
    if client.product.value == "civil":
        cases += _civil_only_cases()

    results = []
    for case in cases:
        row = _run_case(case, client)
        results.append(row)
        marks = " ".join(
            f"{name}={'ok' if step.get('ok') else 'FAIL'}" for name, step in row["steps"].items()
        )
        print(f"{'PASS' if row['ok'] else 'FAIL'}  {row['endpoint']:12} {marks}")

    passed = sum(1 for r in results if r["ok"])
    report = {
        "product": client.product.value,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "connection": {k: health.get(k) for k in ("user", "program", "connectionID")},
        "cases": len(results),
        "passed": passed,
        "results": results,
    }

    print()
    print(f"{passed}/{len(results)} resources completed a full round trip.")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"Report written to {args.out}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
