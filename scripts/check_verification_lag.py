"""Report contracts whose `verification` records lag the live ledger.

`docs/coverage.json` and `contracts/verification/` are two ledgers for one
fact. The ledger entry moves the day a write round trip passes; the contract's
`verification.records` keep citing whatever sweep was current when the contract
was promoted. Nothing compared them until this script, and on 2026-09-20 that
was 47 contracts -- every one of them claiming a read sweep for an endpoint the
ledger records at write level.

**This is a ceiling, not a to-do list.** Folding `docs/coverage.json` into
`contracts/verification/` is the planned fix (`contracts/README.md`); hand-
editing a `verification` block to cite a record it was not promoted from would
forge provenance, which is the one thing these blocks exist to carry. So the
count may shrink -- a contract re-promoted from a write sweep drops out -- and
must not grow: a new write-level endpoint whose contract still cites a read is
the drift this catches.

    python scripts/check_verification_lag.py            # list them
    python scripts/check_verification_lag.py --check    # fail if the count grew
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts" / "endpoints"
COVERAGE = ROOT / "docs" / "coverage.json"

#: Measured 2026-09-20 over 384 promoted contracts: 47 under `/db` and
#: `/ope/MEMB`, which a `db-*` glob had missed. A ceiling: see the module
#: docstring for why it is allowed to fall and not to rise.
LAGGING_AT_MOST = 48


def _ledger_levels() -> dict[str, str]:
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    levels: dict[str, str] = {}
    for entry in coverage["endpoints"]:
        live = entry.get("live_verified") or {}
        if live.get("level"):
            levels[entry["endpoint"]] = live["level"]
    return levels


def lagging_contracts() -> list[tuple[str, pathlib.Path]]:
    """Endpoints the ledger records at write level whose contract cites no write.

    The comparison is deliberately coarse -- does the `verification` block
    mention a write anywhere -- because a record id is a free-form string
    (`db-write-sweep-2026-07-29`) and this check is a drift alarm, not an
    audit of which sweep proved what.
    """
    levels = _ledger_levels()
    lagging = []
    for path in sorted(CONTRACTS.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        endpoint = document.get("endpoint")
        if not isinstance(endpoint, str) or levels.get(endpoint) != "write":
            continue
        verification = json.dumps(document.get("verification") or {})
        if "write" not in verification:
            lagging.append((endpoint, path))
    return lagging


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="exit 1 if more contracts lag than the recorded ceiling",
    )
    args = parser.parse_args()

    lagging = lagging_contracts()
    if args.check:
        if len(lagging) > LAGGING_AT_MOST:
            print(
                f"contracts citing a read sweep for a write-level endpoint grew "
                f"from {LAGGING_AT_MOST} to {len(lagging)}:",
                file=sys.stderr,
            )
            for endpoint, path in lagging:
                print(f"  {endpoint}  ({path.name})", file=sys.stderr)
            print(
                "(Hint: a newly write-level endpoint does not get its contract's "
                "verification block hand-edited - raise the ceiling only with the "
                "measurement that justifies it.)",
                file=sys.stderr,
            )
            return 1
        print(
            f"OK - {len(lagging)} contract(s) lag the ledger, ceiling {LAGGING_AT_MOST}."
        )
        return 0

    print(f"{len(lagging)} contract(s) cite no write record for a write-level endpoint:")
    for endpoint, path in lagging:
        print(f"  {endpoint}  ({path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
