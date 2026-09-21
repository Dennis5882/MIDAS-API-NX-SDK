"""Where each generated npm payload type's shape comes from, counted.

`npm run generate` no longer imports `midas_nx`, but it still reads the Python
**source tree**: `scripts/generate_typescript_sdk.py` parses it for TypedDicts
and keys the payload-type lookup by `pythonModule`, a fact no contract records.
Deleting `src/midas_nx/` breaks generation. Closing that is a standing goal,
and until now the only measurement of it was a hand count in CLAUDE.md -- the
same kind of number `check_state_numbers.py` exists to stop trusting.

This counts it from the generated file. `_render_types` marks every interface
it builds from a contract with a one-line JSDoc, so the split is readable
without re-running the generator:

    contract        the contract supplied the field list
    python:nested   a named object *inside* a payload or an argument that no
                    contract's `surface.nestedTypes` claims, so its field list
                    is still Python's. What those are is broken down below.
    python:unmerged the contract declares `extraction.unmergedTables`, so
                    `_contract_payload_fields` skips it on purpose: narrowing a
                    published type onto an admittedly partial field list would
                    delete fields the manual documents in the table nobody
                    could merge. Merging those tables is a judgement task --
                    see docs/unmerged_tables_against_info.md.
    python:uncontracted  no contract names the type at all.
    python:contract-ignored  a contract names it, does not waive it, and the
                    generator built it from Python anyway. Always empty; a hit
                    is a generator defect, not a known gap.

One caveat on how the buckets are attributed: a payload name is matched
against the contracts by name alone, while the generator keys its lookup by
`(pythonModule, name)` -- `types.ts` is a stack of namespaces and 765
declarations carry 742 distinct names. That is only a risk for the two
contract-aware buckets, and today it is not one: `python:contract-ignored` is
empty and `python:unmerged` is exactly the 13 waived contracts.

Measured 2026-09-21 and 2026-09-22 across two generator changes: 478
Python-sourced types, then 250 once contracts could own a payload's **nested**
types (`surface.nestedTypes`), then 162 once an operation's **argument** type
and its nested types were built from the operation contract as well. What the
147 left in `python:nested` are, roughly:

    51  operation arguments and their children still on Python: a union
        argument (the /ope load-combination pair), a contract with
        unmergedTables (/view/RESULTGRAPHIC), and the two held in
        `_ARGUMENT_TYPES_LEFT_ON_PYTHON` with their reasons
    46  /db modules - the 13 unmergedTables roots' children, objects a
        contract declares without members, shared bases, and names two
        contracts shape differently
    25  design modules, same classes of reason
    25  /post table result types, which no contract describes

    python scripts/report_npm_type_provenance.py           # the breakdown
    python scripts/report_npm_type_provenance.py --check   # fail if it grows
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter

import yaml

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

ROOT = pathlib.Path(__file__).resolve().parent.parent
TYPES = ROOT / "packages" / "typescript" / "src" / "generated" / "types.ts"
CONTRACTS = ROOT / "contracts" / "endpoints"

#: Measured 2026-09-21 over 765 generated types, after nestedTypes. A ceiling: it falls as
#: contracts take over more of the emitted shape, and a rise means a type that
#: used to come from a contract is being read out of the Python tree again.
PYTHON_SOURCED_AT_MOST = 162

CONTRACT_MARKER = "/** Generated from contracts/endpoints/. */"
_EXPORT = re.compile(r"^export (?:interface|type) (\w+)")


def _contract_payload_names() -> tuple[set[str], set[str]]:
    """Payload type names a contract claims, split by the unmergedTables waiver."""
    named: set[str] = set()
    waived: set[str] = set()
    for path in sorted(CONTRACTS.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        name = (contract.get("surface") or {}).get("payloadTypeName")
        if not isinstance(name, str):
            continue
        named.add(name)
        if (contract.get("extraction") or {}).get("unmergedTables"):
            waived.add(name)
    return named, waived


def classify() -> dict[str, list[str]]:
    """Every exported type in the generated file, by where its shape came from."""
    named, waived = _contract_payload_names()
    found: dict[str, list[str]] = {
        "contract": [],
        "python:nested": [],
        "python:unmerged": [],
        "python:uncontracted": [],
        "python:contract-ignored": [],
    }
    previous_line_marked = False
    for line in TYPES.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = _EXPORT.match(stripped)
        if match:
            name = match.group(1)
            if previous_line_marked:
                bucket = "contract"
            elif not name.endswith("Payload"):
                # A nested object. The generator emits the payload root from
                # the contract and leaves everything under it to Python.
                bucket = "python:nested"
            elif name in waived:
                bucket = "python:unmerged"
            elif name in named:
                bucket = "python:contract-ignored"
            else:
                bucket = "python:uncontracted"
            found[bucket].append(name)
        previous_line_marked = stripped == CONTRACT_MARKER
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="exit 1 if more types come from the Python tree than the ceiling",
    )
    args = parser.parse_args()

    found = classify()
    counts = Counter({bucket: len(names) for bucket, names in found.items()})
    python_sourced = sum(count for bucket, count in counts.items() if bucket != "contract")
    total = sum(counts.values())

    if args.check:
        if python_sourced > PYTHON_SOURCED_AT_MOST:
            print(
                f"npm payload types read out of the Python source tree grew from "
                f"{PYTHON_SOURCED_AT_MOST} to {python_sourced}:",
                file=sys.stderr,
            )
            for bucket in (
                "python:contract-ignored", "python:uncontracted",
                "python:unmerged", "python:nested",
            ):
                print(f"  {bucket}: {counts[bucket]}", file=sys.stderr)
            print(
                "(Hint: a contract taking over a type lowers this. A rise means "
                "generation fell back to Python for something a contract had.)",
                file=sys.stderr,
            )
            return 1
        print(
            f"OK - {python_sourced} of {total} generated types come from the Python "
            f"source tree, ceiling {PYTHON_SOURCED_AT_MOST}."
        )
        return 0

    print(f"{total} generated npm types:")
    for bucket in (
        "contract", "python:nested", "python:unmerged", "python:uncontracted",
        "python:contract-ignored",
    ):
        print(f"  {bucket:22} {counts[bucket]:>4}")
    print(f"\n  {'python total':22} {python_sourced:>4}  (ceiling {PYTHON_SOURCED_AT_MOST})")
    for bucket in ("python:unmerged", "python:uncontracted", "python:contract-ignored"):
        if found[bucket]:
            print(f"\n{bucket}:")
            for name in sorted(found[bucket]):
                print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
