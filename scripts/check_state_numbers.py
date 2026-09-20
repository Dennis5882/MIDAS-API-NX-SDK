"""Numbers a document states about this repository, re-derived and compared.

`PLAN.md`'s status table and `docs/live_verification_playbook.md` state counts
-- live coverage, fixture size, contract totals -- that nothing ever checked.
Each one is transcribed by hand from some script's output, so each goes stale
the moment the thing it describes moves. On 2026-09-21 §2's write-verification
row still said `177 of 212 cases confirmed` while the fixture held **183 of
220**, and the header four sections above it said 183 of 220 too: one document,
two answers, neither measured. Published release notes have carried wrong
counts for the same reason.

This re-derives every such number from the artefact that owns it -- the ledger,
`schema/live-cases.json`, `docs/coverage.json`, `contracts/` -- and compares it
against every statement of that number in the documents' current-state regions.

**A dated entry is a record, not a claim about now.** PLAN.md's header block is
a changelog and §4 is release history; the milestone row reading `201 write /
199 read` states what was true at 2.8.3, and rewriting it would falsify it. So
the scanned regions are only the two that are present-tense by construction:
PLAN.md's §2 "Current status" and the playbook's "Where things stand". The
playbook's "Gates" section is left out on purpose -- it prints commands beside
their expected output and says outright that the command wins over the file.

Test counts are out of scope: they come from running the suite, and a checker
that shells out to `pytest --collect-only` would be comparing collected tests
against a number that means passed ones.

A pattern matching nothing is a failure too. Deleting the sentence is not a way
to make this pass.

    python scripts/check_state_numbers.py           # show every stated number
    python scripts/check_state_numbers.py --check   # exit 1 on a disagreement
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import validate_contracts  # noqa: E402
from verification_ledger import claims  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
COVERAGE = ROOT / "docs" / "coverage.json"
LIVE_CASES = ROOT / "schema" / "live-cases.json"
PLAN = ROOT / "PLAN.md"
PLAYBOOK = ROOT / "docs" / "live_verification_playbook.md"


@dataclasses.dataclass(frozen=True)
class Region:
    """A stretch of a document whose numbers are claims about the present."""

    path: pathlib.Path
    heading: re.Pattern[str]
    label: str


REGIONS = (
    Region(PLAN, re.compile(r"^## 2\. "), "PLAN.md §2"),
    Region(PLAYBOOK, re.compile(r"^## Where things stand"), "playbook: where things stand"),
)


@dataclasses.dataclass(frozen=True)
class Pattern:
    """A sentence shape, and the measurement each captured group must equal."""

    regex: re.Pattern[str]
    names: tuple[str, ...]


PATTERNS = (
    Pattern(re.compile(r"(\d+) write / (\d+) read"), ("write", "read")),
    Pattern(re.compile(r"(\d+)/(\d+) (?:implemented|recorded)"), ("inventory", "inventory")),
    Pattern(
        re.compile(r"Of the (\d+) `/db` endpoints, (\d+) are write-level and (\d+) are not"),
        ("db", "db_write", "db_read"),
    ),
    Pattern(re.compile(r"(\d+) of (\d+) cases confirmed"), ("confirmed_cases", "cases")),
    Pattern(re.compile(r"(\d+) cases over (\d+) endpoints"), ("cases", "case_endpoints")),
    Pattern(
        re.compile(r"(\d+) confirmed over (\d+) endpoints"),
        ("confirmed_cases", "confirmed_endpoints"),
    ),
    Pattern(re.compile(r"(\d+) base-model steps"), ("base_model_steps",)),
    Pattern(re.compile(r"(\d+) named seeds"), ("seeds",)),
    Pattern(re.compile(r"(\d+) unsupported"), ("unsupported_seeds",)),
    Pattern(re.compile(r"npm has replayed all (\d+)"), ("confirmed_cases",)),
    Pattern(
        re.compile(r"(\d+) endpoints \+ (\d+) result tables"), ("contracts", "tables")
    ),
    Pattern(re.compile(r"([\d,]+) fields"), ("fields",)),
    Pattern(re.compile(r"(\d+) proven safe"), ("omission_safe",)),
    Pattern(re.compile(r"(\d+) proven unsafe"), ("omission_unsafe",)),
    Pattern(re.compile(r"([\d,]+) honestly unverified"), ("omission_unverified",)),
)


def measure() -> dict[str, int]:
    """Every checked number, read from the artefact that owns it."""
    inventory = json.loads(COVERAGE.read_text(encoding="utf-8"))["endpoints"]
    resolved = claims()
    # Over the inventory, not the ledger: three /DESIGN/*/TABLE rows share one
    # endpoint URL, so the ledger holds 397 claims where ROADMAP renders 400.
    levels = Counter(resolved[e["endpoint"]].level for e in inventory)
    db_levels = Counter(
        resolved[e["endpoint"]].level
        for e in inventory
        if e["endpoint"].startswith("/db/")
    )

    fixture = json.loads(LIVE_CASES.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    confirmed = [case for case in cases if case.get("confirmed")]

    contracts = validate_contracts._load_contracts()
    fields = [
        field
        for _, contract in contracts
        for field in validate_contracts._iter_fields(contract.get("fields", []))
    ]
    omission = Counter(field.get("safeToOmit") for field in fields)

    return {
        "inventory": len(inventory),
        "write": levels["write"],
        "read": levels["read"],
        "db": sum(db_levels.values()),
        "db_write": db_levels["write"],
        "db_read": db_levels["read"],
        "cases": len(cases),
        "case_endpoints": len({case["endpoint"] for case in cases}),
        "confirmed_cases": len(confirmed),
        "confirmed_endpoints": len({case["endpoint"] for case in confirmed}),
        "base_model_steps": len(fixture["baseModel"]),
        "seeds": len(fixture["seeds"]),
        "unsupported_seeds": len(fixture["unsupportedSeeds"]),
        "contracts": len(contracts),
        "tables": len(validate_contracts._load_tables()),
        "fields": len(fields),
        "omission_safe": omission[True],
        "omission_unsafe": omission[False],
        "omission_unverified": sum(
            count for value, count in omission.items() if value not in (True, False)
        ),
    }


def region_text(region: Region) -> str:
    """The region's prose, with every run of whitespace collapsed.

    Both documents wrap, and a wrapped sentence is the same claim as an
    unwrapped one -- matching line by line would miss `220 cases over 196\\n
    endpoints` and call the pattern unstated.
    """
    lines = region.path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if region.heading.match(line))
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return re.sub(r"\s+", " ", "\n".join(lines[start:end]))


@dataclasses.dataclass(frozen=True)
class Statement:
    region: str
    name: str
    stated: int
    measured: int
    quote: str

    @property
    def agrees(self) -> bool:
        return self.stated == self.measured


def statements(measured: dict[str, int] | None = None) -> list[Statement]:
    values = measure() if measured is None else measured
    found: list[Statement] = []
    for region in REGIONS:
        text = region_text(region)
        for pattern in PATTERNS:
            for match in pattern.regex.finditer(text):
                for name, group in zip(pattern.names, match.groups()):
                    found.append(Statement(
                        region=region.label,
                        name=name,
                        stated=int(group.replace(",", "")),
                        measured=values[name],
                        quote=match.group(0),
                    ))
    return found


def unstated(found: list[Statement]) -> list[str]:
    """Patterns no region states. A check nothing anchors to is not a check."""
    quoted = {statement.quote for statement in found}
    missing = []
    for pattern in PATTERNS:
        if not any(pattern.regex.fullmatch(quote) for quote in quoted):
            missing.append(pattern.regex.pattern)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="exit 1 on a disagreement"
    )
    args = parser.parse_args()

    found = statements()
    wrong = [statement for statement in found if not statement.agrees]
    missing = unstated(found)

    if not args.check:
        for region in REGIONS:
            print(region.label)
            for statement in found:
                if statement.region != region.label:
                    continue
                mark = "  " if statement.agrees else "!!"
                print(f"  {mark} {statement.name:22} stated {statement.stated:>6}  "
                      f"measured {statement.measured:>6}   \"{statement.quote}\"")
        if missing:
            print("\nstated nowhere:")
            for pattern in missing:
                print(f"  {pattern}")
        return 0

    for statement in wrong:
        print(
            f"{statement.region}: \"{statement.quote}\" states {statement.name} "
            f"= {statement.stated}, measured {statement.measured}",
            file=sys.stderr,
        )
    for pattern in missing:
        print(
            f"no current-state region states /{pattern}/ any more",
            file=sys.stderr,
        )
    if wrong or missing:
        print(
            "(Hint: the artefact wins. Update the prose to the measured value - "
            "and leave PLAN.md's dated header and release history alone, since "
            "those record what was true then.)",
            file=sys.stderr,
        )
        return 1
    print(f"OK - {len(found)} stated number(s) agree with the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
