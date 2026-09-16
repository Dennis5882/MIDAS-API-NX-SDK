"""Report npm live-replay coverage from the authoritative coverage ledger.

``--check`` enforces two things about every ledger entry carrying the replay
marker: that the endpoint has a shared fixture, and that a session record backs
it. The second exists because the first cannot see a claim that was never run.
Three entries were written on 2026-09-16 citing a notes section that does not
mention them, and every derived number was 3 too high until they were found by
hand -- the ledger is authoritative, so nothing else would have caught it.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "schema" / "live-cases.json"
DEFAULT_COVERAGE = ROOT / "docs" / "coverage.json"
DEFAULT_INVENTORY = ROOT / "docs" / "npm_live_evidence_scratch.md"
REPLAY_MARKER = "npm replayed the same emitted fixture"
#: First cell of an inventory row: | `/db/NODE` | 2026-08-31 | Gen, Civil |
INVENTORY_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def confirmed_case_endpoints(cases_path: Path) -> set[str]:
    """Return endpoints whose shared fixture has a confirmed Python case."""
    fixture = json.loads(cases_path.read_text(encoding="utf-8"))
    return {
        case["endpoint"]
        for case in fixture["cases"]
        if case.get("confirmed") is True
    }


def npm_replayed_endpoints(coverage_path: Path) -> set[str]:
    """Return endpoints whose ledger evidence explicitly records npm replay."""
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    replayed: set[str] = set()
    for row in coverage["endpoints"]:
        verified = row.get("live_verified")
        if not isinstance(verified, dict):
            continue
        if REPLAY_MARKER in verified.get("method", ""):
            replayed.add(row["endpoint"])
    return replayed


def inventoried_endpoints(inventory_path: Path) -> set[str]:
    """Return every endpoint the npm evidence inventory records a run for.

    The inventory is the session-by-session record; the ledger is the claim.
    A claim the inventory does not carry is one nobody wrote a session down
    for, whether it was never run or only never recorded.
    """
    rows = inventory_path.read_text(encoding="utf-8").splitlines()
    return {
        match.group(1)
        for match in (INVENTORY_ROW.match(line) for line in rows)
        if match is not None
    }


def report(
    cases_path: Path, coverage_path: Path, inventory_path: Path | None = None
) -> tuple[int, int, int, set[str], set[str]]:
    """Return confirmed, confirmed-replayed, remaining, unknown and unbacked."""
    fixture = json.loads(cases_path.read_text(encoding="utf-8"))
    case_endpoints = {case["endpoint"] for case in fixture["cases"]}
    confirmed = {
        case["endpoint"]
        for case in fixture["cases"]
        if case.get("confirmed") is True
    }
    replayed = npm_replayed_endpoints(coverage_path)
    unknown = replayed - case_endpoints
    unbacked: set[str] = set()
    if inventory_path is not None:
        unbacked = replayed - inventoried_endpoints(inventory_path)
    return (
        len(confirmed),
        len(replayed & confirmed),
        len(confirmed - replayed),
        unknown,
        unbacked,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the ledger marks an endpoint with no shared fixture, or "
             "one the npm evidence inventory records no session for",
    )
    args = parser.parse_args(argv)

    confirmed, replayed, remaining, unknown, unbacked = report(
        args.cases, args.coverage, args.inventory
    )
    total_replayed = len(npm_replayed_endpoints(args.coverage))
    print(f"confirmed Python fixture endpoints: {confirmed}")
    print(f"npm replayed fixture endpoints: {total_replayed} ({replayed} confirmed)")
    print(f"remaining npm replay gap: {remaining}")
    failed = False
    if unknown:
        print("npm replay markers without a shared fixture:")
        for endpoint in sorted(unknown):
            print(f"  {endpoint}")
        failed = True
    if unbacked:
        print(f"npm replay markers the inventory records no session for "
              f"({args.inventory.name}):")
        for endpoint in sorted(unbacked):
            print(f"  {endpoint}")
        print("Record the session that produced each, or drop the claim. Until "
              "then every count above is that many too high.")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
