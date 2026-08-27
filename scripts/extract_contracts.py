"""Draft endpoint contracts from the official manual repo, and check them for drift.

The manual repo (`Dennis5882/MIDAS-API`) is one of the three permitted sources
for `contracts/` - see `contracts/README.md`. Its chapters already carry
machine-readable parameter tables (`Key` / `Value Type` / `Default` /
`Required`), roughly 640 of them, so drafting a contract does not have to mean
retyping a table by hand.

What this script will and will not do matters more than what it parses.

**It drafts, it does not promote.** Output goes to `contracts/drafts/`, which is
git-ignored and which `scripts/validate_contracts.py` ignores. Every draft
carries `draft: true`, which the schema forbids, so no draft can be moved into
`contracts/endpoints/` and pass CI without someone reading it first.

**It never answers `safeToOmit` from the manual.** That field is a claim about
the product, and the manual cannot make it: `/db/NMAS` documents
`rmX`/`rmY`/`rmZ` as optional and omitting them kills the session. A draft
answers `true` only where a payload in `scripts/live_crud_check.py` marked
`confirmed=True` actually omitted the field and the round trip still passed,
citing that case. Everything else is emitted `unverified`, which is the honest
state and not a lesser one.

**It reports what it could not parse rather than quietly dropping it.** A
section with conditional sub-tables (`#### LINEAR 전용`, `#### 1-2-B. Korea
Type`) has its extra tables listed under `extraction.unmergedTables` instead of
being merged or silently ignored. A partial field list presented as complete is
its own kind of wrong answer.

Modes
-----
``--report``     (default) how much of each chapter is parseable
``--emit ...``   write drafts for the named endpoints, or ``--emit-all``
``--check``      compare promoted contracts against the manual; exit 1 on drift

``--check`` compares only what the manual actually asserts: the field set,
types, documented defaults, documented optionality and requiredness. It says
nothing about `safeToOmit`, `sdkRules` or verification status, because those are
not the manual's to claim.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
DRAFT_DIR = ROOT / "contracts" / "drafts"
ENDPOINT_DIR = ROOT / "contracts" / "endpoints"

DEFAULT_MANUAL_REPO = Path(r"E:\AI Study\MIDAS-API")

# Chapters 18-23 document the shared /post/TABLE family: one endpoint selected by
# a TABLE_TYPE string, with response HEAD columns rather than a request payload.
# That needs a two-layer contract (endpoint plus table), which this extractor
# does not model yet - so it reports them rather than mangling them into
# endpoint contracts.
TABLE_FAMILY_CHAPTERS = {
    "18_POST_PreProcess.md",
    "19_POST_AnalysisResult_1.md",
    "20_POST_AnalysisResult_2.md",
    "21_POST_StoryTables.md",
    "22_POST_TH_HY_Pushover.md",
    "23_POST_Design.md",
}

_SECTION = re.compile(r"^##\s+(\d+)\.\s*`?(/?[A-Za-z][A-Za-z0-9/_.\-]*/[A-Za-z0-9/_.\-]+)`?\s*(?:[—\-–]\s*(.*))?$")
_DIVIDER = re.compile(r"^\|[\s:|-]+\|$")
_SOURCE_URL = re.compile(r"\*\*Source\*\*:\s*\[[^\]]*\]\((https?://[^)]+)\)")
# The chapters declare methods six ways, and each miss is expensive: without one
# the extractor falls back to the /db/* default of all four verbs, which is how
# /db/GRUP's first draft claimed a DELETE the endpoint does not serve.
#
#   - **Methods**: `POST, GET`          label, then the colon inside the bold
#   **Active Methods:** `POST`, `GET`   label, with the colon outside it
#   **Methods:** `POST` · `GET`         ...and a middle dot for a separator
#   | **Method** | `POST` |             a two-column table row, verb singular
#   ### Active Methods                  a heading, verbs on a following line
#   ### HTTP Methods                    a heading, verbs in a Method column
#
# The first three are one regex; the rest need surrounding lines, so
# _section_methods() drives them. Reading only the narrowest form left 276 of
# 386 sections looking like the manual never stated its verbs at all - it does,
# in five of these six ways, and each is worth a promotable contract.
_METHODS = re.compile(
    r"^\s*(?:[-*]\s*)?\*{0,2}(?:Active\s+|HTTP\s+|Supported\s+)?Methods?\s*\*{0,2}\s*[:：]\s*\*{0,2}\s*"
    r"((?:[`\s]*[A-Z]+[,\s·`/]*)+)",
    re.MULTILINE,
)
_METHODS_TABLE_ROW = re.compile(
    r"^\s*\|\s*\*{0,2}(?:Active\s+|HTTP\s+|Supported\s+)?Methods?\*{0,2}\s*\|\s*([^|]+)\|", re.MULTILINE
)
_METHODS_HEADING = re.compile(r"^#{2,4}\s+\*{0,2}(?:Active|HTTP|Supported)\s+Methods?\*{0,2}\s*$", re.I)

_VERBS = {"GET", "POST", "PUT", "DELETE"}


def _verbs(text: str) -> list[str]:
    return sorted({v for v in re.findall(r"[A-Z]+", text) if v in _VERBS})


def _section_methods(lines: list[str]) -> list[str]:
    """Read an endpoint section's HTTP verbs, in whichever form it declares them."""
    text = "\n".join(lines)
    for pattern in (_METHODS, _METHODS_TABLE_ROW):
        match = pattern.search(text)
        if match:
            verbs = _verbs(match.group(1))
            if verbs:
                return verbs

    # `### Active Methods` puts the verbs on a following line; `### HTTP Methods`
    # puts them in the first column of a table. Both end at the next heading.
    for index, line in enumerate(lines):
        if not _METHODS_HEADING.match(line):
            continue
        verbs: set[str] = set()
        for follow in lines[index + 1 :]:
            if follow.startswith("#"):
                break
            if follow.startswith("|"):
                cells = [cell.strip() for cell in follow.strip("|").split("|")]
                verbs.update(_verbs(cells[0]) if cells else [])
            else:
                verbs.update(_verbs(follow))
        if verbs:
            return sorted(verbs)
    return []

_KEY_COLUMNS = {"key", "키"}
_DESC_COLUMNS = {"description", "설명"}
_TYPE_COLUMNS = {"value type", "타입", "value 타입", "type"}
_DEFAULT_COLUMNS = {"default", "기본값", "기본값/enum"}
_REQUIRED_COLUMNS = {"required", "필수"}

_EMPTY_CELLS = {"", "-", "—", "–", "n/a", "N/A"}

# The chapters draw nesting with a box-drawing marker in the Description column.
_DESC_TREE = re.compile(r"^[└├│─\s]+")

# ...and, far more often, in the No. column: a parent is numbered `4`, its
# children `(1)`/`(2)` or `4-1`/`4-2`, and a grandchild `4-1-1`. 1,257 of the
# manual's 4,731 numbered rows are children this way. Missing it flattened
# /db/RIGD's ITEMS array into four sibling keys no payload actually has - a
# wrong contract that reached contracts/endpoints/ before type generation
# from the same contract exposed it.
_NUMBER_CHILD = re.compile(r"^\((\d+)\)$")
_NUMBER_PATH = re.compile(r"^\d+(?:-\d+)+$")


def _slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def _clean(cell: str) -> str:
    """Strip the markdown the manual decorates cells with, not their content."""
    text = cell.strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("`", "").strip()
    # Footnote markers: superscript digits and the "¹⁾" form the chapters use.
    text = re.sub(r"[\u00b9\u00b2\u00b3\u2070-\u209f]+\)?", "", text)
    return text.strip()


_REQUIRED_WORDS = {"required", "필수"}
_OPTIONAL_WORDS = {"optional", "선택"}


def _normalize_requirement(cell: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (requirement, condition, note). None requirement = the manual did not say.

    Many rows qualify the answer in place - `Required (bEXACTSPAN=true)`,
    `필수 (ADDITIONAL_LOAD 사용 시)`. That is a real condition stated in the
    manual's own words, so it is carried across verbatim rather than flattened
    to "required" (which would overstate it) or dropped (which would lose it).
    """
    raw = _clean(cell)
    text = raw.lower()
    if text in _EMPTY_CELLS:
        return None, None, "the manual leaves the Required column blank"
    if "read only" in text or "readonly" in text:
        return "read_only", None, None

    qualified = re.match(r"^(.*?)\s*[（(]\s*(.+?)\s*[)）]\s*$", raw)
    if qualified:
        base = qualified.group(1).strip().lower()
        condition = qualified.group(2).strip()
        if base in _REQUIRED_WORDS or "조건부" in base:
            return "conditional", condition, None
        if base in _OPTIONAL_WORDS:
            return "optional", None, f"the manual qualifies this Optional with {condition!r}"

    if "조건부" in text or "conditional" in text:
        return "conditional", None, "the manual marks this conditional but does not state the condition"
    if text in _REQUIRED_WORDS | {"o", "yes", "y"}:
        return "required", None, None
    if text in _OPTIONAL_WORDS | {"x", "no", "n"}:
        return "optional", None, None
    if text in {"불명", "unknown", "미상"}:
        return None, None, "the manual states outright that the requiredness is unknown"
    return None, None, f"unrecognised Required value {raw!r}"


def _normalize_type(cell: str) -> tuple[Optional[str], Optional[dict], Optional[str]]:
    """Return (type, items, note)."""
    text = _clean(cell)
    if text in _EMPTY_CELLS:
        return None, None, "the manual leaves the Value Type column blank"
    array = re.match(r"^Array\s*\[\s*([A-Za-z]+)\s*\]$", text, re.IGNORECASE)
    if array:
        inner, _, note = _normalize_type(array.group(1))
        return "array", ({"type": inner} if inner else None), note
    base = text.lower()
    note = None
    enum_hint = re.match(r"^(string|integer|number)\s*\((enum|oneof|one of)\)$", base)
    if enum_hint:
        base = enum_hint.group(1)
        note = "the manual types this as an enum but the values are listed elsewhere in the chapter"
    if base in {"number", "double", "float"}:
        return "number", None, note
    if base in {"integer", "int"}:
        return "integer", None, note
    if base in {"string", "str"}:
        return "string", None, note
    if base in {"boolean", "bool"}:
        return "boolean", None, note
    if base in {"object", "json"}:
        return "object", None, note
    if base.startswith("array"):
        return "array", None, "array element type not stated by the manual"
    return None, None, f"unrecognised Value Type {text!r}"


def _normalize_default(cell: str) -> tuple[Any, Optional[str]]:
    """Return (default, note). None means the manual documents no default."""
    text = _clean(cell)
    if text in _EMPTY_CELLS:
        return None, None
    low = text.lower()
    if low in {"false", "true"}:
        return low == "true", None
    if low in {"blank", "빈 문자열", '""'}:
        return "", None
    try:
        number = float(text)
    except ValueError:
        return text, f"non-literal default {text!r} kept verbatim; confirm what the server does"
    return int(number) if number.is_integer() else number, None


@dataclass
class ParsedField:
    key: str
    description: str
    type: Optional[str]
    items: Optional[dict]
    requirement: Optional[str]
    documented_default: Any
    condition: Optional[str] = None
    number: str = ""
    notes: list[str] = dataclass_field(default_factory=list)
    properties: list["ParsedField"] = dataclass_field(default_factory=list)


_PATH_SEGMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(\[\])?$")


def _split_path(key: str) -> Optional[list[tuple[str, bool]]]:
    """Split `PERMIT_LOAD.AXLE_TYPES` or `POINT_ITEMS[].POINT_LOAD` into segments.

    Returns None for anything that is not a clean path, so callers can flag it
    instead of guessing. 121 rows in the manual name two keys at once
    (`"ELEMS" / "SECTIONS"`) and those are genuinely ambiguous - the right
    response is to say so, not to pick one.
    """
    segments: list[tuple[str, bool]] = []
    for part in key.split("."):
        match = _PATH_SEGMENT.match(part)
        if not match:
            return None
        segments.append((match.group(1), bool(match.group(2))))
    return segments


def _as_container(field: ParsedField, is_array: bool) -> None:
    """Make a field able to hold children, without discarding what it declared."""
    if is_array:
        if field.type not in {"array"}:
            if field.type not in {None, "object"}:
                field.notes.append(
                    f"the manual types this {field.type!r} but its children are addressed as "
                    f"an array; treated as array of objects"
                )
            field.type = "array"
        field.items = {"type": "object"}
    elif field.type not in {"object", "array"}:
        if field.type is not None:
            field.notes.append(
                f"the manual types this {field.type!r} but it has nested children; treated as object"
            )
        field.type = "object"


def _nest(flat: list[ParsedField]) -> list[ParsedField]:
    """Turn the manual's dotted Key paths into real nested fields.

    The chapters address nested payload members four ways: a dotted path in the
    Key column (`DATA1.DESIGN.C_FC`), a bracketed array path
    (`POINT_ITEMS[].POINT_LOAD`), a `└` tree marker that sometimes leaks out of
    the Description column into the Key, and - most often of all - the No.
    column, where a parent is `4` and its children are `(1)`/`(2)` or `4-1`/`4-2`.
    All four describe structure the contract can represent exactly, so they are
    reconstructed rather than flattened into keys no payload actually has.
    """
    roots: list[ParsedField] = []
    by_path: dict[tuple[str, ...], ParsedField] = {}
    last_root: Optional[ParsedField] = None
    by_depth: dict[int, ParsedField] = {}

    for entry in flat:
        key = entry.key

        # The No. column decides nesting unless the key itself spells out a
        # path, which is unambiguous and wins.
        depth = 0
        if _NUMBER_CHILD.match(entry.number):
            depth = 1
        elif _NUMBER_PATH.match(entry.number):
            depth = entry.number.count("-")
        if depth and "." not in key and not key.startswith("└"):
            parent = by_depth.get(depth - 1)
            if parent is not None:
                entry.notes.append(
                    f"the manual nests this under {parent.key!r} by numbering it "
                    f"{entry.number!r}, not by naming a path"
                )
                _as_container(parent, is_array=parent.type == "array")
                parent.properties.append(entry)
                by_depth[depth] = entry
                continue
        tree_marked = key.startswith("└")
        if tree_marked:
            key = key.lstrip("└").strip()

        segments = _split_path(key)
        if segments is None:
            entry.notes.append(
                f"key {entry.key!r} is not a single field name; the manual names more than one "
                f"key in this row, or decorates it - confirm the wire name by hand"
            )
            roots.append(entry)
            continue

        if tree_marked and len(segments) == 1 and last_root is not None:
            entry.key = segments[0][0]
            entry.notes.append(
                f"the manual nests this under {last_root.key!r} with a tree marker rather than a path"
            )
            _as_container(last_root, is_array=False)
            last_root.properties.append(entry)
            continue

        path: tuple[str, ...] = ()
        parent: Optional[ParsedField] = None
        for depth, (name, is_array) in enumerate(segments):
            path = path + (name,)
            leaf = depth == len(segments) - 1
            existing = by_path.get(path)

            if leaf:
                entry.key = name
                if is_array and entry.type is None:
                    entry.type = "array"
                if existing is not None:
                    # The manual listed the container first and is now listing it
                    # again as a leaf; keep the container and its children.
                    existing.notes.append("the manual documents this key twice; kept the first row")
                    break
                by_path[path] = entry
                (parent.properties if parent is not None else roots).append(entry)
                if parent is None:
                    last_root = entry
                    by_depth[0] = entry
                    by_depth.pop(1, None)
                break

            if existing is None:
                existing = ParsedField(
                    key=name,
                    description="",
                    type=None,
                    items=None,
                    requirement=None,
                    documented_default=None,
                    notes=[
                        "no row of its own in the manual - inferred from the dotted paths of its "
                        "children, so its requiredness and default are unknown"
                    ],
                )
                by_path[path] = existing
                (parent.properties if parent is not None else roots).append(existing)
                if parent is None:
                    last_root = existing
            _as_container(existing, is_array)
            parent = existing

    return roots


def _walk(fields: list[ParsedField]) -> list[ParsedField]:
    out: list[ParsedField] = []
    for entry in fields:
        out.append(entry)
        out.extend(_walk(entry.properties))
    return out


@dataclass
class ParsedTable:
    heading: str
    line: int
    fields: list[ParsedField]


@dataclass
class Section:
    chapter_file: str
    number: str
    endpoint: str
    title: str
    heading: str
    lines: list[str]
    source_url: Optional[str] = None
    methods: list[str] = dataclass_field(default_factory=list)
    tables: list[ParsedTable] = dataclass_field(default_factory=list)

    @property
    def id(self) -> str:
        return _slug(self.endpoint)


def _parse_tables(lines: list[str], offset: int) -> list[ParsedTable]:
    tables: list[ParsedTable] = []
    heading = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            index += 1
            continue
        if not (line.startswith("|") and index + 1 < len(lines) and _DIVIDER.match(lines[index + 1])):
            index += 1
            continue

        header = [cell.strip().lower() for cell in line.strip("|").split("|")]
        key_column = next((i for i, h in enumerate(header) if h in _KEY_COLUMNS), None)
        if key_column is None:
            index += 1
            continue

        desc_column = next((i for i, h in enumerate(header) if h in _DESC_COLUMNS), None)
        type_column = next((i for i, h in enumerate(header) if h in _TYPE_COLUMNS), None)
        default_column = next((i for i, h in enumerate(header) if h in _DEFAULT_COLUMNS), None)
        required_column = next((i for i, h in enumerate(header) if h in _REQUIRED_COLUMNS), None)

        fields: list[ParsedField] = []
        seen: set[str] = set()
        row = index + 2
        while row < len(lines) and lines[row].startswith("|"):
            cells = [cell.strip() for cell in lines[row].strip("|").split("|")]
            row += 1
            if len(cells) != len(header):
                continue
            key = _clean(cells[key_column]).strip('"')
            if not key or key in _EMPTY_CELLS:
                continue
            if key in seen:
                continue
            seen.add(key)

            notes: list[str] = []
            if required_column is not None:
                requirement, condition, note = _normalize_requirement(cells[required_column])
            else:
                requirement, condition, note = None, None, "the table has no Required column"
            if note:
                notes.append(note)
            field_type, items, note = _normalize_type(cells[type_column]) if type_column is not None else (None, None, "the table has no Value Type column")
            if note:
                notes.append(note)
            default, note = _normalize_default(cells[default_column]) if default_column is not None else (None, "the table has no Default column")
            if note:
                notes.append(note)
            fields.append(
                ParsedField(
                    key=key,
                    description=_DESC_TREE.sub("", _clean(cells[desc_column])).strip() if desc_column is not None else "",
                    type=field_type,
                    items=items,
                    requirement=requirement,
                    documented_default=default,
                    condition=condition,
                    number=_clean(cells[0]) if cells else "",
                    notes=notes,
                )
            )

        if fields:
            tables.append(
                ParsedTable(
                    heading=heading or "(unlabelled table)",
                    line=offset + index + 1,
                    fields=_nest(fields),
                )
            )
        index = row
    return tables


_TOC_METHOD_COLUMNS = {"methods", "active methods", "메서드"}


def _toc_methods(lines: list[str]) -> dict[str, list[str]]:
    """Read methods out of a chapter's contents table.

    15 chapters state each endpoint's verbs once, in the table of contents,
    rather than in the endpoint's own section. Without this the extractor falls
    back to the /db/* default of all four verbs, which is how /db/GRUP's first
    draft claimed a DELETE the endpoint does not serve.
    """
    found: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        if not (line.startswith("|") and index + 1 < len(lines) and _DIVIDER.match(lines[index + 1])):
            continue
        header = [cell.strip().lower() for cell in line.strip("|").split("|")]
        if "endpoint" not in header:
            continue
        method_column = next((i for i, h in enumerate(header) if h in _TOC_METHOD_COLUMNS), None)
        if method_column is None:
            continue
        endpoint_column = header.index("endpoint")
        row = index + 2
        while row < len(lines) and lines[row].startswith("|"):
            cells = [cell.strip() for cell in lines[row].strip("|").split("|")]
            row += 1
            if len(cells) != len(header):
                continue
            endpoint = re.search(r"/?[A-Za-z][A-Za-z0-9/_.\-]*/[A-Za-z0-9/_.\-]+", _clean(cells[endpoint_column]))
            if not endpoint:
                continue
            verbs = sorted(
                {v for v in re.findall(r"[A-Z]+", cells[method_column]) if v in {"GET", "POST", "PUT", "DELETE"}}
            )
            if verbs:
                path = endpoint.group(0)
                found[path if path.startswith("/") else "/" + path] = verbs
    return found


def parse_chapter(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    toc_methods = _toc_methods(lines)
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = _SECTION.match(line)
        if match:
            starts.append((index, match))

    sections: list[Section] = []
    for position, (index, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        body = lines[index + 1 : end]
        endpoint = match.group(2)
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        section = Section(
            chapter_file=path.name,
            number=match.group(1),
            endpoint=endpoint,
            title=(match.group(3) or "").strip(),
            heading=lines[index].lstrip("#").strip(),
            lines=body,
        )
        text = "\n".join(body)
        url = _SOURCE_URL.search(text)
        if url:
            section.source_url = url.group(1)
        section.methods = _section_methods(body)
        if not section.methods:
            section.methods = toc_methods.get(section.endpoint, [])
        section.tables = _parse_tables(body, index)
        sections.append(section)
    return sections


def load_manual(manual_repo: Path) -> tuple[list[Section], dict[str, int]]:
    manual_dir = manual_repo / "docs" / "manual"
    if not manual_dir.is_dir():
        raise SystemExit(f"ERROR: no manual chapters at {manual_dir}")
    sections: list[Section] = []
    table_family: dict[str, int] = {}
    for path in sorted(manual_dir.glob("*.md")):
        if path.name == "INDEX.md":
            continue
        if path.name in TABLE_FAMILY_CHAPTERS:
            table_family[path.name] = sum(
                1 for line in path.read_text(encoding="utf-8").splitlines() if re.match(r"^##\s+\d+\.", line)
            )
            continue
        sections.extend(parse_chapter(path))
    return sections, table_family


# ---------------------------------------------------------------------------
# YAML emission. Written by hand rather than through yaml.dump so a draft can
# carry the review markers that make it a draft.
# ---------------------------------------------------------------------------


def _scalar(value: Any) -> str:
    """Render a YAML scalar that reads back as exactly what was passed in.

    Quoting by character class is not enough here. YAML 1.1 resolves bare `NO`,
    `Y`, `ON` and `OFF` to booleans, and `NO` is a real MIDAS field name - it
    appears as a Key in 7 of the manual's parameter tables. Emitting it unquoted
    silently turns a field name into `false`. So the test is a round trip: if
    the bare form does not parse back to the identical string, quote it.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)

    text = str(value)
    quoted = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if text == "" or text.strip() != text or re.search(r"[:#{}\[\]&*!|>%@`\"']", text):
        return quoted
    try:
        import yaml  # noqa: PLC0415

        if yaml.safe_load(text) != text:
            return quoted
    except Exception:
        return quoted
    return text


@dataclass
class LiveOmission:
    """A payload that a real product accepted, and what it left out."""

    case: str
    endpoint: str
    sent: frozenset[str]
    products: str


def live_omission_evidence() -> dict[str, LiveOmission]:
    """Which fields a confirmed live write actually omitted, per endpoint.

    `scripts/live_crud_check.py` carries 116 cases marked `confirmed=True`,
    meaning someone watched that exact payload complete a create-read-update-
    delete round trip against a running product. A documented field absent from
    such a payload was omitted and the call still worked - which is evidence
    about the product, and therefore the only kind of thing `safeToOmit: true`
    is allowed to rest on.

    Read statically, through `ast`. Importing the checker would be reading an
    SDK to learn about the API; this reads a record of what a server did.

    It proves the call was accepted, not that the resulting model was what the
    engineer wanted - the emitted evidence string says so.
    """
    import ast  # noqa: PLC0415

    checker = ROOT / "scripts" / "live_crud_check.py"
    if not checker.exists():
        return {}

    endpoints: dict[str, str] = {}
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import importlib  # noqa: PLC0415
        import pkgutil  # noqa: PLC0415

        import midas_nx  # noqa: PLC0415
        from midas_nx.db.base import DbResource  # noqa: PLC0415

        for module in pkgutil.walk_packages(midas_nx.__path__, "midas_nx."):
            importlib.import_module(module.name)

        def walk(base: type) -> None:
            for child in base.__subclasses__():
                if getattr(child, "ENDPOINT", None):
                    endpoints[child.__name__] = child.ENDPOINT
                walk(child)

        walk(DbResource)
    except Exception:
        return {}

    found: dict[str, LiveOmission] = {}
    for node in ast.walk(ast.parse(checker.read_text(encoding="utf-8"))):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Case"):
            continue
        keywords = {k.arg: k.value for k in node.keywords}
        confirmed = keywords.get("confirmed")
        if not (isinstance(confirmed, ast.Constant) and confirmed.value is True):
            continue

        resource = node.args[0] if node.args else keywords.get("resource")
        payload = node.args[1] if len(node.args) > 1 else keywords.get("create_payload")
        if resource is None or payload is None:
            continue
        name = getattr(resource, "id", None) or ast.unparse(resource)
        endpoint = endpoints.get(name)
        if endpoint is None or endpoint in found:
            continue
        try:
            sent = frozenset(ast.literal_eval(payload).keys())
        except Exception:
            continue

        products = keywords.get("products")
        found[endpoint] = LiveOmission(
            case=name,
            endpoint=endpoint,
            sent=sent,
            products=ast.unparse(products) if products is not None else "gen and civil",
        )
    return found


def _block(text: str, indent: str, prefix: str = "") -> list[str]:
    """Wrap `text` at a readable width.

    `prefix` is repeated on every wrapped line, which matters for comments: a
    `# NOTE:` whose continuation lines lose the `#` stops being a comment and
    becomes a YAML parse error.
    """
    words = " ".join(text.split())
    limit = 74 - len(prefix)
    out: list[str] = []
    line = ""
    for word in words.split(" "):
        if line and len(line) + len(word) + 1 > limit:
            out.append(indent + prefix + line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(indent + prefix + line)
    return out


def _render_fields(
    fields: list[ParsedField], indent: str, evidence: Optional[LiveOmission] = None
) -> list[str]:
    lines: list[str] = []
    body = indent + "  "
    for parsed in fields:
        lines.append(f"{indent}- key: {_scalar(parsed.key)}")
        if parsed.description:
            lines.append(f"{body}description: >-")
            lines += _block(parsed.description, body + "  ")
        if parsed.type:
            lines.append(f"{body}type: {parsed.type}")
            if parsed.items and parsed.items.get("type"):
                lines.append(f"{body}items:")
                lines.append(f"{body}  type: {parsed.items['type']}")
        else:
            lines.append(f"{body}type: string   # TODO(review): the manual did not state a type")
        lines.append(
            f"{body}requirement: {parsed.requirement}"
            if parsed.requirement
            else f"{body}requirement: optional   # TODO(review): the manual did not state requiredness"
        )
        if parsed.requirement == "conditional":
            if parsed.condition:
                lines.append(f"{body}condition: {_scalar(parsed.condition)}")
            else:
                lines.append(f"{body}condition: \"TODO(review): the manual does not state the condition\"")
        lines.append(f"{body}documentedDefault: {_scalar(parsed.documented_default)}")
        lines.append(f"{body}documentedOptional: {'true' if parsed.requirement == 'optional' else 'false'}")

        # safeToOmit is a claim about the product, so it is only ever answered
        # `true` here from a payload a product actually accepted without the
        # field. Everything else stays `unverified`, which is the honest state,
        # not a lesser one.
        omitted_live = (
            evidence is not None and indent == "  " and parsed.key not in evidence.sent
        )
        if omitted_live:
            assert evidence is not None
            lines.append(f"{body}safeToOmit: true")
            lines.append(f"{body}omissionEvidence: >-")
            lines += _block(
                f"scripts/live_crud_check.py's {evidence.case} case completed a live "
                f"create-read-update-delete round trip on {evidence.products} without this "
                f"field in its payload. That is evidence the call is accepted, not that the "
                f"resulting model is what an engineer wanted.",
                body + "  ",
            )
        else:
            lines.append(f"{body}safeToOmit: unverified")
            lines.append(f"{body}# TODO(review): nobody has omitted this against a live product.")
            lines.append(f"{body}# Leave it unverified, or find out - do not read the manual's")
            lines.append(f"{body}# 'Optional' as an answer; that is what documentedOptional records.")
        lines.append(f"{body}provenance: manual")
        for note in parsed.notes:
            lines += _block(f"NOTE: {note}", body, prefix="# ")
        if parsed.properties:
            lines.append(f"{body}properties:")
            lines += _render_fields(parsed.properties, body + "  ")
    return lines


def render_draft(section: Section, evidence: Optional[LiveOmission] = None) -> str:
    main = section.tables[0] if section.tables else None
    lines: list[str] = [
        f"# DRAFT contract for {section.endpoint} - extracted, not reviewed.",
        "#",
        "# Generated by scripts/extract_contracts.py from the official manual. It is a",
        "# transcription of what the manual says, nothing more. Before moving this file",
        "# to contracts/endpoints/ you must supply what the manual cannot know:",
        "#",
        "#   1. safeToOmit for every field. Omitted here on purpose - the file will not",
        "#      validate until you answer it. 'Optional' in the manual is a claim about",
        "#      the documentation; safeToOmit is a claim about the product, and /db/NMAS",
        "#      is the case where the two disagree and the session dies.",
        "#   2. verification.status and any records under contracts/verification/.",
        "#   3. sdkRules for anything a caller could reasonably do that breaks the product.",
        "#   4. products - confirm against live evidence, not the manual's framing.",
        "#      32 of 47 endpoints the manual calls Civil-only answer on Gen NX too.",
        "#",
        "# Then run: python scripts/validate_contracts.py",
        "",
        "contractVersion: 1",
        "draft: true   # reviewing this file is what removes this line",
        f"id: {section.id}",
        f"endpoint: {section.endpoint}",
        f"name: {_scalar(section.title or section.endpoint)}",
    ]

    lines += ["", "# TODO(review): confirm against live evidence, not the manual's framing.", "products: [gen, civil]", ""]

    lines += ["source:", "  manual:", "    status: documented", "    repo: Dennis5882/MIDAS-API"]
    lines.append(f"    chapterFile: {section.chapter_file}")
    lines.append(f"    section: {_scalar(section.heading)}")
    if section.source_url:
        lines.append(f"    url: {section.source_url}")
    lines += ["  liveNotes:", "    - docs/live_verification_notes.md", ""]

    lines += [
        "# TODO(review): manual_only is the honest state for a contract nobody has",
        "# called yet. Raise it only with a record in contracts/verification/.",
        "verification:",
        "  status: manual_only",
        "",
    ]

    methods = section.methods or ["GET", "POST", "PUT", "DELETE"]
    if not section.methods:
        lines.append("# TODO(review): the chapter did not state its methods; this is the /db/* default.")
    lines.append("operations:")
    for method in methods:
        risk = "read_only" if method == "GET" else ("destructive" if method == "DELETE" else "write")
        lines.append(f"  - method: {method}")
        lines.append(f"    risk: {risk}   # TODO(review): product_crash_risk if it has ever ended a session")
        if method == "DELETE":
            lines.append("    mitigation: none   # TODO(review): see /db/NODE's contract for the two DELETE forms")
        lines.append("    request:")
        if method in {"GET", "DELETE"}:
            lines.append("      wrapper: none")
        else:
            lines.append("      wrapper: assign")
            lines.append("      itemSchema: fields")
        lines.append("    response:")
        lines.append("      wrapper: table")
        lines.append("      keyStability: stable")
    lines.append("")

    if main is None:
        lines += [
            "# No parameter table could be parsed from this section. Transcribe the",
            "# fields by hand, or check whether the endpoint takes no payload at all.",
            "fields: []",
            "",
        ]
    else:
        lines.append("fields:")
        lines += _render_fields(main.fields, "  ", evidence)
        lines.append("")

    lines.append("extraction:")
    lines.append(f"  source: {section.chapter_file} line {main.line if main else '?'}")
    lines.append(f"  table: {_scalar(main.heading if main else 'none found')}")
    if len(section.tables) > 1:
        lines.append("  # Additional parameter tables in this section were NOT merged. They are")
        lines.append("  # usually conditional variants selected by a type/code field. Decide")
        lines.append("  # whether they belong in this contract's fields, as nested `properties`,")
        lines.append("  # or as a separate contract - do not assume the first table is the whole")
        lines.append("  # schema.")
        lines.append("  unmergedTables:")
        for table in section.tables[1:]:
            lines.append(f"    - heading: {_scalar(table.heading)}")
            lines.append(f"      fields: {len(table.fields)}")
            lines.append(f"      line: {table.line}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def run_report(sections: list[Section], table_family: dict[str, int]) -> int:
    by_chapter: dict[str, list[Section]] = {}
    for section in sections:
        by_chapter.setdefault(section.chapter_file, []).append(section)

    print(f"{'chapter':<40}{'endpoints':>10}{'with fields':>13}{'fields':>9}{'multi-table':>13}")
    total = with_fields = fields = multi = 0
    for chapter, items in sorted(by_chapter.items()):
        parsed = [s for s in items if s.tables]
        count = sum(len(_walk(s.tables[0].fields)) for s in parsed)
        many = sum(1 for s in items if len(s.tables) > 1)
        print(f"{chapter:<40}{len(items):>10}{len(parsed):>13}{count:>9}{many:>13}")
        total += len(items)
        with_fields += len(parsed)
        fields += count
        multi += many
    print(f"{'TOTAL':<40}{total:>10}{with_fields:>13}{fields:>9}{multi:>13}")

    # How trustworthy is that field count? Anything carrying a note needs a human
    # before it can be believed, and saying so is the difference between a draft
    # and a claim.
    all_fields = [f for section in sections for table in section.tables for f in _walk(table.fields)]
    flagged = [f for f in all_fields if f.notes]
    nested = [f for f in all_fields if f.properties]
    print(
        f"\nacross every parsed table: {len(all_fields)} fields, {len(nested)} of them nested, "
        f"{len(flagged)} carrying a review note ({100 * len(flagged) // max(len(all_fields), 1)}%)."
    )
    reasons: dict[str, int] = {}
    for entry in flagged:
        for note in entry.notes:
            head = note.split(";")[0].split(" - ")[0].strip()
            head = re.sub(r"^key '.*?' is", "key is", head)
            head = re.sub(r"^the manual types this '\w+'", "the manual types this", head)
            head = re.sub(r"^unrecognised (\w+) .*", r"unrecognised \1 value", head)
            reasons[head] = reasons.get(head, 0) + 1
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {count:>5}  {reason}")

    # A section with no stated verbs cannot be promoted, so this is a headline
    # number, not a detail - and it was reported as 276 while the extractor could
    # read only the narrowest of the six forms the chapters use. Print it, so the
    # next person quoting it is quoting a measurement.
    silent = [s for s in sections if not s.methods]
    if silent:
        print(f"\n{len(silent)} of {total} sections state their HTTP methods nowhere the extractor can read:")
        for chapter, count in sorted(Counter(s.chapter_file for s in silent).items()):
            print(f"  {count:>3}  {chapter}")

    if table_family:
        skipped = sum(table_family.values())
        print(
            f"\n{skipped} sections across {len(table_family)} chapters belong to the shared "
            f"/post/TABLE family and are not endpoint contracts:"
        )
        for chapter, count in sorted(table_family.items()):
            print(f"  {count:>3}  {chapter}")
        print("  They need a two-layer contract (endpoint + table), which is not modelled yet.")

    promoted = {path.stem for path in ENDPOINT_DIR.glob("*.yaml")} if ENDPOINT_DIR.is_dir() else set()
    drafted = {path.stem for path in DRAFT_DIR.glob("*.yaml")} if DRAFT_DIR.is_dir() else set()
    print(f"\npromoted contracts: {len(promoted)}   drafts awaiting review: {len(drafted - promoted)}")
    return 0


def run_emit(sections: list[Section], targets: list[str], emit_all: bool) -> int:
    wanted = {t.lower().rstrip("/") for t in targets}
    promoted = {path.stem for path in ENDPOINT_DIR.glob("*.yaml")} if ENDPOINT_DIR.is_dir() else set()

    chosen = [
        section
        for section in sections
        if emit_all or section.endpoint.lower() in wanted or section.id in wanted
    ]
    if not chosen:
        print(f"ERROR: nothing matched {sorted(wanted)}", file=sys.stderr)
        return 2

    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    evidence = live_omission_evidence()
    written = skipped = 0
    for section in chosen:
        if section.id in promoted:
            skipped += 1
            continue
        draft = render_draft(section, evidence.get(section.endpoint))
        (DRAFT_DIR / f"{section.id}.yaml").write_text(draft, encoding="utf-8")
        written += 1
        if not emit_all:
            print(f"  {section.endpoint:<45} -> contracts/drafts/{section.id}.yaml")
    print(f"\nwrote {written} draft(s); skipped {skipped} already promoted to contracts/endpoints/")
    print("Every draft needs review before it can validate - see the header of each file.")
    return 0


def _flatten_manual(fields: list[ParsedField], prefix: str = "") -> dict[str, ParsedField]:
    """Address nested fields by dotted path so the comparison is order-free."""
    out: dict[str, ParsedField] = {}
    for entry in fields:
        path = f"{prefix}{entry.key}"
        out[path] = entry
        out.update(_flatten_manual(entry.properties, f"{path}."))
    return out


def _flatten_contract(fields: list[dict], prefix: str = "") -> dict[str, dict]:
    out: dict[str, dict] = {}
    for entry in fields:
        path = f"{prefix}{entry['key']}"
        out[path] = entry
        out.update(_flatten_contract(entry.get("properties", []), f"{path}."))
    return out


def run_check(sections: list[Section]) -> int:
    try:
        import yaml
    except ImportError:
        print('ERROR: PyYAML is not installed. Run: pip install -e ".[dev]"', file=sys.stderr)
        return 2

    by_endpoint = {section.endpoint: section for section in sections}
    problems: list[str] = []
    skipped: list[str] = []
    checked = 0

    for path in sorted(ENDPOINT_DIR.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        if contract["source"]["manual"]["status"] != "documented":
            continue
        chapter = contract["source"]["manual"].get("chapterFile")
        if chapter in TABLE_FAMILY_CHAPTERS:
            # /post/TABLE is documented in those chapters' shared "공통 사항"
            # sections, not in a numbered endpoint section, and this extractor
            # does not model that chapter family. Reporting it as missing would
            # be reporting the extractor's own gap as a contract defect.
            skipped.append(f"{path.name} ({chapter}: /post/TABLE family, not modelled)")
            continue

        section = by_endpoint.get(contract["endpoint"])
        if section is None:
            problems.append(f"{path.name}: claims a documented manual source, but no chapter section describes {contract['endpoint']}")
            continue
        if not section.tables:
            problems.append(f"{path.name}: no parameter table could be parsed from {section.chapter_file}; cannot check")
            continue
        checked += 1

        manual_fields = _flatten_manual(section.tables[0].fields)
        contract_fields = _flatten_contract(contract.get("fields", []))
        overridden = {
            d.get("describes") for d in contract.get("manualDefects", [])
        }

        for key, manual in manual_fields.items():
            if key not in contract_fields:
                problems.append(f"{path.name}: the manual documents {key!r}, the contract does not")
                continue
            declared = contract_fields[key]
            if manual.type and declared["type"] != manual.type and "field_value" not in overridden:
                problems.append(f"{path.name}: {key} typed {declared['type']!r}, manual says {manual.type!r}")
            if manual.requirement and declared["requirement"] != manual.requirement:
                problems.append(f"{path.name}: {key} requirement {declared['requirement']!r}, manual says {manual.requirement!r}")
            documented_optional = manual.requirement == "optional"
            if declared["documentedOptional"] != documented_optional:
                problems.append(
                    f"{path.name}: {key} documentedOptional={declared['documentedOptional']}, "
                    f"manual's Required column says {'Optional' if documented_optional else 'not Optional'}"
                )
            if declared.get("documentedDefault") != manual.documented_default and "default" not in overridden:
                problems.append(
                    f"{path.name}: {key} documentedDefault={declared.get('documentedDefault')!r}, "
                    f"manual says {manual.documented_default!r}"
                )

        for key in contract_fields:
            if key not in manual_fields and "field_name" not in overridden:
                problems.append(
                    f"{path.name}: the contract declares {key!r}, which the manual's table does not - "
                    f"record it under manualDefects if the manual is the one that is wrong"
                )

    print(f"checked {checked} promoted contract(s) against the manual")
    for note in skipped:
        print(f"  skipped {note}")
    if problems:
        print(f"\n{len(problems)} disagreement(s):")
        for problem in problems:
            print(f"  {problem}")
        print("\nA disagreement is not automatically the contract's fault. Where a live check")
        print("has disproved the manual, record it under manualDefects and set the field's")
        print("provenance to live_corrected - do not edit the contract back to match a manual")
        print("that has already been measured wrong.")
        return 1
    print("OK - no drift between the manual and the promoted contracts.")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manual-api-repo", type=Path, default=DEFAULT_MANUAL_REPO)
    parser.add_argument("--emit", nargs="+", metavar="ENDPOINT", help="write drafts for these endpoints or ids")
    parser.add_argument("--emit-all", action="store_true", help="write a draft for every parseable section")
    parser.add_argument("--check", action="store_true", help="check promoted contracts against the manual")
    args = parser.parse_args(argv)

    sections, table_family = load_manual(args.manual_api_repo)

    if args.check:
        return run_check(sections)
    if args.emit or args.emit_all:
        return run_emit(sections, args.emit or [], args.emit_all)
    return run_report(sections, table_family)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
