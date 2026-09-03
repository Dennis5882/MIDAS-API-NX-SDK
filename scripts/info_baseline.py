"""Capture ``GET /info{endpoint}`` for every endpoint, and diff it.

``/info`` is the server's own JSON Schema for an endpoint. It is the only
permitted contract source that is the product rather than a document, and
``contracts/README.md`` treats it as such. This script keeps a committed
baseline of what the product declared, so two questions can be answered without
guessing:

  * **Did a product patch change the API surface?** ``--diff`` compares a fresh
    capture against ``schema/info-baseline.json`` and prints every property
    added, removed or retyped. The 2026-09-02 patch was checked this way
    against 26 endpoints and changed none of them; the baseline now covers
    every endpoint that answers, so the next patch gets a real comparison.
  * **Does a contract record what the product declares?** ``--against-contracts``
    is offline and sweeps both directions - properties ``/info`` declares that no
    contract has, and names a contract publishes that ``/info`` declares nowhere.
    The forward pass found MD-34 (`/db/REBR`'s whole item shape), MD-35 (four
    fields on all six `/db/LCOM-*`) and MD-36. The reverse pass is where a wrong
    *name* shows up instead of a missing one, which the forward pass cannot see:
    it found MD-37 (`/db/POGD-M1`'s `UPLIFT` for `UPLIFTING`) and MD-38
    (`/db/STRPSSM`'s `PY` for `Y`). Read the reverse list weakly - the printed
    preamble says why, and `/db/STBK` is the counter-example that sets the bar.

``--capture`` is the only mode that talks to a product, and it issues **GET
only**, so it is safe against an open model - the same guarantee
``scripts/live_readonly_sweep.py`` gives. It records schemas and error strings
and nothing else: a GET response body is the author's model contents and never
belongs in this repository, and ``--capture`` has no code path that would store
one.

``/info`` is served for ``/db/*`` only. Every ``/DESIGN/*`` pair 404s - an API
fact, not a URL bug - and so do the Civil Hyper-S trio ``/db/IEHG-GL-M1``,
``/db/IEHG-PSS-M1`` and ``/db/IEHG-TRUSS-M1``, which is why those three cannot
be contracted at all.

Usage::

    python scripts/info_baseline.py --capture --out fresh.json
    python scripts/info_baseline.py --diff fresh.json
    python scripts/info_baseline.py --against-contracts
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import sys
from typing import Any, Iterable

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASELINE = ROOT / "schema" / "info-baseline.json"
CONTRACTS = ROOT / "contracts" / "endpoints"


# --- reading a capture ------------------------------------------------------


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schemas(capture: dict[str, Any]) -> dict[tuple[str, str], dict]:
    """(endpoint, product) -> schema, for every pair that answered."""
    out: dict[tuple[str, str], dict] = {}
    for endpoint, per_product in capture["endpoints"].items():
        for product, payload in per_product.items():
            if isinstance(payload, dict) and payload.get("schema"):
                out[(endpoint, product)] = payload["schema"]
    return out


def _paths(schema: dict, *, with_types: bool = False) -> dict[str, str]:
    """Every property path a schema declares, dotted, array steps elided.

    An array step is elided on purpose: ``ITEMS[].NAME`` and ``ITEMS.NAME``
    describe the same wire name, and the contracts write the second.
    """
    out: dict[str, str] = {}

    def walk(node: Any, prefix: str) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            for name, sub in properties.items():
                path = f"{prefix}.{name}" if prefix else name
                out[path] = (sub or {}).get("type", "unstated") if with_types else ""
                walk(sub, path)
        items = node.get("items")
        if isinstance(items, dict):
            walk(items, prefix)

    root = schema.get("Argument") if isinstance(schema.get("Argument"), dict) else schema
    walk(root, "")
    return out


# --- reading the contracts --------------------------------------------------


def _contract_documents() -> dict[str, dict]:
    import yaml  # noqa: PLC0415

    found: dict[str, dict] = {}
    for path in sorted(CONTRACTS.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and document.get("endpoint"):
            found[document["endpoint"]] = document
    return found


def _contract_leaves(contract: dict) -> set[str]:
    """Every wire name this contract names anywhere, variants included.

    The reverse sweep compares against this rather than against paths. A
    contract and /info disagree about nesting often enough that a path
    mismatch is not evidence of anything; a wire name /info never mentions
    at any depth is. /db/POGD-M1 is the case that made this worth having -
    the contract said `UPLIFT` where the server says `UPLIFTING`, and a
    one-directional sweep reported the second as missing while saying
    nothing at all about the first.
    """
    out: set[str] = set()

    def walk(fields: Iterable[dict] | None) -> None:
        for field in fields or []:
            out.add(field["key"])
            walk(field.get("properties"))

    walk(contract.get("fields"))
    for variant in contract.get("variants") or []:
        walk(variant.get("fields"))
    # The envelope is documentation of the wrapper, not of the record.
    return out - {"Assign", "Argument"}


def _info_only(contract: dict) -> set[str]:
    """Paths this contract says the server declares but no caller should send."""
    return {entry["path"] for entry in contract.get("infoOnly") or []}


def _contract_paths(contract: dict) -> set[str]:
    out: set[str] = set()

    def walk(fields: Iterable[dict] | None, prefix: str) -> None:
        for field in fields or []:
            path = f"{prefix}.{field['key']}" if prefix else field["key"]
            out.add(path)
            walk(field.get("properties"), path)

    fields = contract.get("fields") or []
    walk(fields, "")
    # A variant's fields are siblings of the field it gates on. Without a
    # declared attach point, offer them at the root and under every root field,
    # so a variant member is not reported as missing.
    for variant in contract.get("variants") or []:
        walk(variant.get("fields"), "")
        for field in fields:
            walk(variant.get("fields"), field["key"])

    # The request envelope is documentation of the wrapper, not of the record.
    for path in list(out):
        for envelope in ("Assign.", "Argument."):
            if path.startswith(envelope):
                out.add(path[len(envelope):])
    return out


# --- the three modes --------------------------------------------------------


def diff(fresh_path: pathlib.Path) -> int:
    baseline = _schemas(_load(BASELINE))
    fresh = _schemas(_load(fresh_path))

    gone = sorted(set(baseline) - set(fresh))
    new = sorted(set(fresh) - set(baseline))
    changed: list[tuple[tuple[str, str], list[str]]] = []

    for key in sorted(set(baseline) & set(fresh)):
        before = _paths(baseline[key], with_types=True)
        after = _paths(fresh[key], with_types=True)
        notes = [f"+ {p} ({after[p]})" for p in sorted(set(after) - set(before))]
        notes += [f"- {p} ({before[p]})" for p in sorted(set(before) - set(after))]
        notes += [
            f"~ {p}: {before[p]} -> {after[p]}"
            for p in sorted(set(before) & set(after))
            if before[p] != after[p]
        ]
        if notes:
            changed.append((key, notes))

    print(f"baseline: {BASELINE.name}, captured {_load(BASELINE)['capturedAt']}")
    print(f"fresh:    {fresh_path.name}, captured {_load(fresh_path)['capturedAt']}")
    print(f"pairs compared: {len(set(baseline) & set(fresh))}")
    print()
    if not (gone or new or changed):
        print("No difference. Every endpoint declares exactly the schema it did before.")
        return 0
    for endpoint, product in new:
        print(f"NEW      {endpoint} ({product}) now answers /info")
    for endpoint, product in gone:
        print(f"GONE     {endpoint} ({product}) no longer answers /info")
    for (endpoint, product), notes in changed:
        print(f"CHANGED  {endpoint} ({product})")
        for note in notes:
            print(f"           {note}")
    return 1


def against_contracts() -> int:
    capture = _load(BASELINE)
    contracts = _contract_documents()

    declared: dict[str, set[str]] = {}
    for (endpoint, _product), schema in _schemas(capture).items():
        declared.setdefault(endpoint, set()).update(_paths(schema))

    rows: list[tuple[int, str, list[str]]] = []
    phantom: list[tuple[str, list[str]]] = []
    skipped: list[str] = []
    waived = 0
    compared = 0
    for endpoint, paths in sorted(declared.items()):
        contract = contracts.get(endpoint)
        if contract is None:
            continue
        if (contract.get("extraction") or {}).get("unmergedTables"):
            skipped.append(endpoint)
            continue
        compared += 1
        known = _contract_paths(contract)
        leaves = {p.rsplit(".", 1)[-1] for p in known}
        declines = _info_only(contract)
        waived += len(declines)
        # Generous on purpose: a property counts as recorded if its full path is
        # known *or* its own name appears anywhere in the contract. /info and
        # the manual disagree about nesting often enough that a path mismatch
        # alone is not evidence of a missing field.
        missing = sorted(
            p for p in paths
            if p not in known and p.rsplit(".", 1)[-1] not in leaves
            and p not in declines
        )
        if missing:
            rows.append((len(missing), endpoint, missing))

        # And the other direction: a wire name the contract publishes that the
        # server declares nowhere. Compared by leaf name, never by path, for
        # the same reason the forward pass is.
        info_leaves = {p.rsplit(".", 1)[-1] for p in paths}
        unknown = sorted(_contract_leaves(contract) - info_leaves)
        if unknown:
            phantom.append((endpoint, unknown))

    rows.sort(key=lambda row: (-row[0], row[1]))
    phantom.sort(key=lambda row: (-len(row[1]), row[0]))
    print(f"contracts compared: {compared}")
    print(f"skipped, field list admittedly incomplete (unmergedTables): {len(skipped)}")
    print(f"properties waived as infoOnly: {waived}")
    print(f"endpoints with an unrecorded /info property: {len(rows)}")
    print(f"unrecorded properties in total: {sum(n for n, _, _ in rows)}")
    print(f"endpoints publishing a name /info never declares: {len(phantom)}")
    print()
    print("A large count is usually not a defect. /info describes the whole")
    print("record including computed read-only members, while a manual section")
    print("often documents only what a request sends - /db/SECT's section-property")
    print("tree is the extreme case. A count of one or two is the interesting")
    print("shape: that is what a missing table row looks like.")
    print()
    for count, endpoint, missing in rows:
        print(f"{count:4}  {endpoint}")
        for index in range(0, len(missing), 6):
            print("        " + ", ".join(missing[index:index + 6]))

    print()
    print("=" * 70)
    print("Names this contract publishes that /info declares nowhere.")
    print()
    print("Read these the other way round from the list above, and read them")
    print("weakly. /info listing a property is not the same as the server")
    print("accepting only those: /db/STBK's LCNAME appears in neither product's")
    print("schema, and scripts/live_crud_check.py runs a confirmed round trip")
    print("that sends it on both. So a name here supports a note, never a")
    print("removal. What it is good for is the case where the manual and the")
    print("server both name a field and name it differently - /db/POGD-M1's")
    print("UPLIFT for UPLIFTING, /db/STRPSSM's PY for Y - because there a")
    print("caller following the manual sends a key the server never mentions")
    print("while the one it does mention goes unsent. Removing a documented")
    print("field takes what settled /db/REBC: a live comparison in which the")
    print("documented shape was refused and the other accepted.")
    print()
    for endpoint, unknown in phantom:
        print(f"{len(unknown):4}  {endpoint}")
        for index in range(0, len(unknown), 6):
            print("        " + ", ".join(unknown[index:index + 6]))
    return 0


def capture(out_path: pathlib.Path, products: list[str]) -> int:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))
    from live_readonly_sweep import (  # noqa: PLC0415
        _all_resources,
        _import_all_submodules,
    )

    from midas_nx import MidasClient, Product  # noqa: PLC0415
    from midas_nx.client import MidasAPIError  # noqa: PLC0415

    _import_all_submodules()
    resources = _all_resources()
    endpoints = sorted({resource.ENDPOINT for resource in resources})
    print(f"sweeping /info for {len(endpoints)} endpoints x {len(products)} product(s)")

    results: dict[str, dict[str, Any]] = {}
    for product in products:
        client = MidasClient(product=Product(product))
        for endpoint in endpoints:
            slot = results.setdefault(endpoint, {})
            try:
                response = client.request("GET", f"/info{endpoint}")
            except MidasAPIError as error:
                slot[product] = {"status": None, "error": f"{type(error).__name__}: {error}"}
            else:
                # Only the schema is kept. A GET response body is model data and
                # never enters this file.
                slot[product] = {"status": 200, "schema": response}
        print(f"  {product}: done")

    answered = sum(1 for v in results.values() for p in v.values() if p.get("schema"))
    payload = {
        "$comment": _load(BASELINE)["$comment"] if BASELINE.exists() else "",
        "capturedAt": __import__("datetime").date.today().isoformat(),
        "method": "GET /info{endpoint}",
        "nxVersions": {product: "TODO: record the build you ran against" for product in products},
        "coverage": {
            "endpointsSwept": len(results),
            "pairsWithSchema": answered,
            "pairsAnswering404": sum(
                1 for v in results.values() for p in v.values() if p.get("error")
            ),
        },
        "endpoints": results,
    }
    io.open(out_path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    )
    print(f"wrote {out_path} ({answered} pairs with a schema)")
    print("Fill in nxVersions before committing this as a baseline.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true", help="live GET-only sweep")
    mode.add_argument("--diff", metavar="CAPTURE", help="compare a capture against the baseline")
    mode.add_argument(
        "--against-contracts",
        action="store_true",
        help="offline: which declared properties no contract records",
    )
    parser.add_argument("--out", default="info-capture.json", help="--capture output path")
    parser.add_argument(
        "--product",
        action="append",
        choices=["civil", "gen"],
        help="repeatable; defaults to both",
    )
    args = parser.parse_args()

    if args.against_contracts:
        return against_contracts()
    if args.diff:
        return diff(pathlib.Path(args.diff))
    return capture(pathlib.Path(args.out), args.product or ["civil", "gen"])


if __name__ == "__main__":
    raise SystemExit(main())
