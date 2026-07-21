"""Live-server counterpart to scripts/check_manual_drift.py: for every
DbResource subclass in this SDK, compares its TypedDict's field names
against the field names the live NX server actually reports via
``GET /info/db/...`` (DbResource.info(), added v0.10.0).

Unlike check_manual_drift.py this needs a running MIDAS Gen NX or Civil NX
instance with the Open API connected (see src/midas_nx/README.md Quick
Start) — it is a local dev tool, not something CI can run.

Run with the dev environment active (``pip install -e ".[dev]"``), e.g.:
    python scripts/check_drift.py --product gen
    python scripts/check_drift.py --product civil --resource /db/MATL

Exit code 0 -> no field-name drift found among the resources checked.
Exit code 1 -> at least one resource has a field-name mismatch.
Exit code 2 -> couldn't connect, or the server rejected the connection.
"""
from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
from pathlib import Path
from typing import Optional

import midas_nx
from midas_nx.client import MidasAPIError, MidasClient
from midas_nx.db.base import DbResource

ROOT = Path(__file__).resolve().parent.parent


def _import_all_submodules() -> None:
    for _, name, _ in pkgutil.walk_packages(midas_nx.__path__, prefix=midas_nx.__name__ + "."):
        importlib.import_module(name)


def _all_resources() -> list[type]:
    """Every concrete DbResource subclass across the whole package (db/*,
    db/properties/*, design/*, design/rc_kds/*), found by walking every
    submodule and then DbResource's subclass tree — there's no central
    registry, so this is the only reliable enumeration."""
    _import_all_submodules()
    seen: set[type] = set()
    stack = list(DbResource.__subclasses__())
    resources = []
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        stack.extend(cls.__subclasses__())
        if "ENDPOINT" in cls.__dict__:
            resources.append(cls)
    return sorted(resources, key=lambda c: c.ENDPOINT)


def _payload_fields(cls: type) -> Optional[set[str]]:
    """Look up the sibling ``{ClassName}Payload`` TypedDict in the resource's
    own module — the naming convention every chapter module follows, since
    DbResource itself has no attribute linking a resource to its TypedDict."""
    module = sys.modules.get(cls.__module__)
    payload = getattr(module, cls.__name__ + "Payload", None)
    annotations = getattr(payload, "__annotations__", None)
    return set(annotations.keys()) if annotations else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=["gen", "civil"], default="gen")
    parser.add_argument("--mapi-key", help="defaults to MIDAS_MAPI_KEY env var")
    parser.add_argument("--base-url", help="defaults to MIDAS_BASE_URL env var")
    parser.add_argument(
        "--resource", help="only check resources whose ENDPOINT contains this substring"
    )
    parser.add_argument("--out", help="path to write the report JSON (optional)")
    args = parser.parse_args()

    client = MidasClient(mapi_key=args.mapi_key, base_url=args.base_url, product=args.product)
    try:
        health = client.verify_connection()
    except MidasAPIError as exc:
        print(f"Could not reach the MIDAS NX Open API server: {exc}", file=sys.stderr)
        sys.exit(2)
    if health.get("status") != "connected":
        print(f"Server reachable but not connected: {health}", file=sys.stderr)
        sys.exit(2)

    resources = _all_resources()
    if args.resource:
        resources = [r for r in resources if args.resource in r.ENDPOINT]

    drift = []
    errors = []
    skipped_no_payload = []
    checked = 0

    for cls in resources:
        if client.product.value not in cls.PRODUCTS:
            continue
        sdk_fields = _payload_fields(cls)
        if sdk_fields is None:
            skipped_no_payload.append(cls.ENDPOINT)
            continue
        try:
            info = cls.info(client=client)
        except MidasAPIError as exc:
            errors.append({"endpoint": cls.ENDPOINT, "error": str(exc)})
            continue

        checked += 1
        server_schema = next(iter(info.values()), {}) if info else {}
        server_fields = set(server_schema.keys())

        missing_in_sdk = sorted(server_fields - sdk_fields)
        missing_on_server = sorted(sdk_fields - server_fields)
        if missing_in_sdk or missing_on_server:
            drift.append({
                "endpoint": cls.ENDPOINT,
                "module": cls.__module__,
                "missing_in_sdk": missing_in_sdk,
                "missing_on_server": missing_on_server,
            })

    result = {
        "product": client.product.value,
        "checked": checked,
        "drift_count": len(drift),
        "error_count": len(errors),
        "skipped_no_payload_typeddict": skipped_no_payload,
        "drift": drift,
        "errors": errors,
    }
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")

    sys.exit(1 if drift else 0)


if __name__ == "__main__":
    main()
