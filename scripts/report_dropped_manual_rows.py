"""Report keyed manual-table rows the contract extractor cannot turn into fields.

This is a measurement tool, not a parser.  It deliberately imports the
extractor's Markdown-cell and wire-key helpers, so the report cannot claim a
row is preserved when the extractor drops it (or vice versa).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import extract_contracts as extractor

EXPECTED_COUNTS = {
    "blank key cell": 71,
    "cell count disagrees with header": 20,
}


@dataclass(frozen=True)
class DroppedRow:
    cause: str
    chapter: str
    endpoint: str
    line: int
    key: str
    cells: tuple[str, ...]


def scan_lines(chapter: str, lines: list[str]) -> list[DroppedRow]:
    """Find rows that the extractor skips in tables with a recognised key.

    A literal empty key is a blank-key row.  ``-`` is an intentional manual
    placeholder rather than an empty cell, so it is not part of the established
    blank-key measurement.  It remains handled by the extractor as before.
    """

    rows: list[DroppedRow] = []
    endpoint = ""
    index = 0
    while index + 1 < len(lines):
        section = extractor._SECTION.match(lines[index])
        if section:
            endpoint = section.group(2)
            if not endpoint.startswith("/"):
                endpoint = "/" + endpoint
            index += 1
            continue
        if not endpoint or not (
            lines[index].startswith("|") and extractor._DIVIDER.match(lines[index + 1])
        ):
            index += 1
            continue

        header = [cell.lower() for cell in extractor._split_row(lines[index])]
        key_column = next(
            (column for column, name in enumerate(header) if name in extractor._KEY_COLUMNS),
            None,
        )
        if key_column is None:
            index += 1
            continue

        row = index + 2
        while row < len(lines) and lines[row].startswith("|"):
            cells = extractor._split_row(lines[row])
            if len(cells) != len(header):
                rows.append(
                    DroppedRow(
                        "cell count disagrees with header",
                        chapter,
                        endpoint,
                        row + 1,
                        "",
                        tuple(cells),
                    )
                )
            else:
                key = extractor._canonical_wire_property(cells[key_column])
                if not key:
                    rows.append(DroppedRow("blank key cell", chapter, endpoint, row + 1, key, tuple(cells)))
            row += 1
        index = row
    return rows


def scan_manual(manual_repo: Path) -> list[DroppedRow]:
    manual_dir = manual_repo / "docs" / "manual"
    return [
        row
        for path in sorted(manual_dir.glob("*.md"))
        for row in scan_lines(path.name, path.read_text(encoding="utf-8").splitlines())
    ]


def report(rows: list[DroppedRow]) -> Counter[str]:
    counts = Counter(row.cause for row in rows)
    print("Dropped keyed manual-table rows:")
    for cause, count in sorted(counts.items()):
        print(f"  {cause}: {count}")
    for cause in sorted(counts):
        if cause == "blank key cell":
            continue
        print(f"\n{cause}:")
        for row in (item for item in rows if item.cause == cause):
            print(f"  {row.chapter}:{row.line} {row.endpoint} | {' | '.join(row.cells)}")
    return counts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual-api-repo", type=Path, default=extractor.DEFAULT_MANUAL_REPO)
    parser.add_argument("--check", action="store_true", help="fail if the established cause counts change")
    args = parser.parse_args(argv)

    counts = report(scan_manual(args.manual_api_repo))
    if args.check and dict(counts) != EXPECTED_COUNTS:
        print(f"\nExpected {EXPECTED_COUNTS}, got {dict(counts)}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
