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
import copy
import json
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
TABLE_DIR = ROOT / "contracts" / "tables"

DEFAULT_MANUAL_REPO = Path(r"E:\AI Study\MIDAS-API")

# Chapters 18-23 document the shared /post/TABLE family: one endpoint selected by
# a TABLE_TYPE string, with response HEAD columns rather than a request payload.
# Those use a two-layer contract (endpoint plus table).  This extractor only
# emits endpoint drafts, so it reports their measured table-contract coverage
# rather than mangling them into endpoint contracts.
TABLE_FAMILY_CHAPTERS = {
    "18_POST_PreProcess.md",
    "19_POST_AnalysisResult_1.md",
    "20_POST_AnalysisResult_2.md",
    "21_POST_StoryTables.md",
    "22_POST_TH_HY_Pushover.md",
    "23_POST_Design.md",
}

_SECTION = re.compile(r"^##\s+(\d+)\.\s*`?(/?[A-Za-z][A-Za-z0-9/_.\-]*/[A-Za-z0-9/_.\-]+)`?\s*(?:[—\-–]\s*(.*))?$")
_BLOCKQUOTE_TITLE = re.compile(r"^>\s+\*\*([^*]+)\*\*(?:\s*[—\-–]\s*.*)?$")
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
# Some chapters number and localize this heading (for example,
# ``### 1-1. HTTP 메서드 및 URL``).  ``HTTP`` still establishes that the
# following table is an HTTP-method table; the parser below accepts only actual
# HTTP verbs from its first column, so a broader heading match cannot invent a
# method from the surrounding prose.
_METHODS_HEADING = re.compile(
    r"^#{2,4}\s+(?:.*\b(?:Active|Supported)\s+Methods?\b.*|.*\bHTTP\b.*)$",
    re.I,
)

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
_ENUM_VALUE_COLUMNS = {"value", "값"}

_EMPTY_CELLS = {"", "-", "—", "–", "n/a", "N/A"}
_ENUM_VALUES_ELSEWHERE = "the manual types this as an enum but the values are listed elsewhere in the chapter"

# The chapters draw nesting with a box-drawing marker in the Description column.
_DESC_TREE = re.compile(r"^[└├│─\s]+")

# ...and, far more often, in the No. column: a parent is numbered `4`, its
# children `(1)`/`(2)` or `4-1`/`4-2`, and a grandchild `4-1-1`. 1,257 of the
# manual's 4,731 numbered rows are children this way. Missing it flattened
# /db/RIGD's ITEMS array into four sibling keys no payload actually has - a
# wrong contract that reached contracts/endpoints/ before type generation
# from the same contract exposed it.
_NUMBER_CHILD = re.compile(r"^\((?:\d+|[ivxlcdm]+)\)$", re.IGNORECASE)
_NUMBER_PATH = re.compile(r"^\d+(?:[-.]\d+)+$")
# A small group of manual tables marks an immediate array-item member with a
# leading dash in the Description cell (for example ITEM followed by
# `- Time` and `- Value`).  This is deliberately narrower than treating an
# em dash in the No. column as structure: that form also appears for ordinary
# root rows in the load-combination manuals.
_DESC_ARRAY_CHILD = re.compile(r"^-\s+")


def _slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def _clean(cell: str) -> str:
    """Strip the markdown the manual decorates cells with, not their content."""
    text = cell.strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("`", "").strip()
    # Some tables escape brackets solely to keep Markdown from interpreting an
    # array type as a link.  The backslashes are presentation syntax, not part
    # of the documented wire type (for example ``Array \[Number, 3\]``).
    text = text.replace("\\[", "[").replace("\\]", "]")
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


_DESCRIPTION_CONDITION_MARKERS = (
    "if ",
    "when ",
    "\uc77c \ub54c",
    "\uacbd\uc6b0",
    "\uc0ac\uc6a9 \uc2dc",
    "\uc804\uc6a9",
)


def _condition_from_description(cell: str) -> Optional[str]:
    """Keep one condition phrase the parameter description states verbatim.

    ``Conditional Required`` is often terse in the Required column, while the
    Description says exactly when it applies in a parenthesis or after a dash.
    This deliberately retains the manual phrase rather than inferring a
    selector from a sibling field or an example.
    """

    text = _clean(cell)

    def says_when(value: str) -> bool:
        return any(marker in value.lower() for marker in _DESCRIPTION_CONDITION_MARKERS)

    candidates = [part.strip() for part in re.findall(r"\(([^()]*)\)", text) if says_when(part)]
    dash_parts = re.split(r"\s+[\u2014\u2013]\s+", text)
    if len(dash_parts) > 1:
        candidates.extend(part.strip() for part in dash_parts[1:] if says_when(part))
    distinct = list(dict.fromkeys(candidate for candidate in candidates if candidate))
    return distinct[0] if len(distinct) == 1 else None


def _normalize_type(cell: str) -> tuple[Optional[str], Optional[dict], Optional[str]]:
    """Return (type, items, note)."""
    text = _clean(cell)
    if text in _EMPTY_CELLS:
        return None, None, "the manual leaves the Value Type column blank"
    compact_array = re.match(r"^(String|Integer|Number|Boolean|Object|Real)\s*,\s*(\d+)$", text, re.IGNORECASE)
    if compact_array:
        inner, _, note = _normalize_type(compact_array.group(1))
        return "array", ({"type": inner} if inner else None), note
    fixed_array = re.match(
        r"^Array\s*\[\s*(String|Integer|Number|Boolean|Object|Real)\s*,\s*(\d+)\s*\]$",
        text,
        re.IGNORECASE,
    )
    if fixed_array:
        # ``Array[Number,21]`` is one 21-value number array, not an array
        # whose elements are themselves 21-value arrays.  The comma-length
        # form also appears without the outer ``Array[...]`` in older tables.
        inner, _, note = _normalize_type(fixed_array.group(1))
        return "array", ({"type": inner} if inner else None), note
    array = re.match(r"^Array\s*\[\s*(.+?)\s*\]$", text, re.IGNORECASE)
    if array:
        # ``Array[{PY, PZ}]`` is the manual's compact spelling for an array of
        # objects. Its named members still have to appear in adjacent rows;
        # this only reads the container type the cell itself states.
        if re.fullmatch(r"\{[^{}]+\}", array.group(1).strip()):
            return "array", {"type": "object"}, None
        inner, _, note = _normalize_type(array.group(1))
        return "array", ({"type": inner} if inner else None), note
    base = text.lower()
    note = None
    boolean_default = re.match(r"^boolean\s*\(\s*(?:기본|default)\s+(true|false)\s*\)$", base)
    if boolean_default:
        base = "boolean"
    enum_wrapper = re.match(r"^enum\s*\(\s*(string|integer|number)\s*\)$", base)
    if enum_wrapper:
        base = enum_wrapper.group(1)
        note = _ENUM_VALUES_ELSEWHERE
    if re.match(r"^boolean\s*\(\s*(?:oneof|one of)\s*\)$", base):
        base = "boolean"
    object_shape = re.match(r"^object\s*\(\s*(?:oneof|[^)]*/[^)]*)\s*\)$", base)
    if object_shape:
        return (
            "object",
            None,
            "the manual qualifies this object shape, but does not state a representable property schema",
        )
    if re.fullmatch(r'"[^"\\]+"', text):
        return "string", None, None
    const_type = re.match(r"^(string|integer|number|real)\s*\(\s*const(?:\s+[^)]*)?\s*\)$", base)
    if const_type:
        base = const_type.group(1)
    constraint_base = re.match(
        r"^(string|integer|number|real)\s*\((?:≥\s*-?\d+(?:\.\d+)?|>\s*-?\d+(?:\.\d+)?|"
        r"-?\d+(?:\.\d+)?\s*~\s*-?\d+(?:\.\d+)?|0\s*(?:금지|초과\s*1\s*이하)|\d+)\)$",
        base,
    )
    if constraint_base:
        base = constraint_base.group(1)
    enum_hint = re.match(
        r"^(string|integer|number)\s*(?:\(\s*(enum|oneof|one of)(?:\s*:\s*[^)]*)?\s*\)|\s+(enum|oneof|one of))$",
        base,
    )
    if enum_hint:
        base = enum_hint.group(1)
        note = _ENUM_VALUES_ELSEWHERE
    if base in {"number", "double", "float", "real"}:
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


def _number(text: str) -> int | float:
    number = float(text)
    return int(number) if number.is_integer() else number


def _type_constraints(cell: str) -> dict[str, Any]:
    """Return only range/length constraints spelled out by the manual type cell."""

    text = _clean(cell)
    string_const = re.fullmatch(r'"([^"\\]+)"', text)
    if string_const:
        return {"const": string_const.group(1)}
    const = re.fullmatch(r"(?:Number|Integer|Real)\s*\(\s*const\s+(-?\d+(?:\.\d+)?)\s*\)", text, re.IGNORECASE)
    if const:
        return {"const": _number(const.group(1))}
    compact_array = re.fullmatch(
        r"(?:Array\s*\[\s*)?(?:String|Integer|Number|Boolean|Object|Real)\s*,\s*(\d+)(?:\s*\])?",
        text,
        re.IGNORECASE,
    )
    if compact_array:
        length = int(compact_array.group(1))
        return {"minItems": length, "maxItems": length}
    string_length = re.fullmatch(r"String\s*\(\s*(\d+)\s*\)", text, re.IGNORECASE)
    if string_length:
        length = int(string_length.group(1))
        return {"minLength": length, "maxLength": length}

    match = re.fullmatch(r"(?:Number|Integer|Real)\s*\((.+)\)", text, re.IGNORECASE)
    if not match:
        return {}
    constraint = re.sub(r"\s+", "", match.group(1))
    if constraint.lower() in {"0금지", "0notallowed"}:
        return {"notEqual": 0}
    if constraint == "0초과1이하":
        return {"exclusiveMinimum": 0, "maximum": 1}
    if match := re.fullmatch(r"≥(-?\d+(?:\.\d+)?)", constraint):
        return {"minimum": _number(match.group(1))}
    if match := re.fullmatch(r">(-?\d+(?:\.\d+)?)", constraint):
        return {"exclusiveMinimum": _number(match.group(1))}
    if match := re.fullmatch(r"(-?\d+(?:\.\d+)?)~(-?\d+(?:\.\d+)?)", constraint):
        return {"minimum": _number(match.group(1)), "maximum": _number(match.group(2))}
    return {}


def _type_default(cell: str) -> Any | None:
    """Read an explicit default only where the type cell itself spells it out."""

    match = re.fullmatch(
        r"Boolean\s*\(\s*(?:기본|default)\s+(true|false)\s*\)", _clean(cell), re.IGNORECASE
    )
    return match.group(1).lower() == "true" if match else None


def _enum_values_from_inline_type(cell: str) -> list[Any]:
    """Read only explicit enum literals from a Value Type cell."""

    text = _clean(cell)
    match = re.search(r"\b(?:enum|oneof|one of)\s*:\s*(.+?)\s*\)?$", text, re.IGNORECASE)
    if not match:
        return []
    return _quoted_enum_values(match.group(1))


def _quoted_enum_values(text: str) -> list[Any]:
    """Return explicit double-quoted enum literals, preserving their order."""

    values: list[Any] = []
    for value in re.findall(r'"([^"\\]+)"', text):
        if value not in values:
            values.append(value)
    return values


def _enum_values_from_description(text: str) -> list[Any]:
    """Read an explicitly enumerated description without treating ranges as enums.

    The manual commonly writes integer alternatives as ``0=Simplified /
    1=General``.  Two or more distinct ``number=label`` pairs are a complete
    finite list; a lone condition such as ``MODE=0`` or a range like ``0~20``
    is not, so neither becomes an enum here.  Later chapters put each numeric
    value in a Markdown code span (``Stress: `0` / Force: `1```); those spans
    are likewise an explicit finite list, unless the text uses a range or an
    ellipsis to leave values unstated.
    """

    # An ellipsis is a shorthand for values the manual did not actually list
    # (for example ``1=Method-1 … 4=Method-4``).  It is not evidence for the
    # intervening values, so preserve the enum review note instead of making a
    # partial claim.
    if "..." in text or "…" in text:
        return []

    quoted = _quoted_enum_values(text)
    if quoted:
        return quoted

    # Numeric wire values in the manuals are often written as individual code
    # spans.  Treat only two or more non-range spans as an enum.  A code span
    # adjacent to ``~`` is a documented bound, not an alternative.
    code_numeric: list[int | float] = []
    for match in re.finditer(r"`\s*(-?\d+(?:\.\d+)?)\s*`", text):
        before = text[: match.start()].rstrip()
        after = text[match.end() :].lstrip()
        if (before and before[-1] == "~") or (after and after[0] == "~"):
            continue
        value = _number(match.group(1))
        if value not in code_numeric:
            code_numeric.append(value)
    if len(code_numeric) >= 2:
        return code_numeric

    values: list[int | float] = []
    for literal in re.findall(r"(?<![A-Za-z0-9_.-])(-?\d+(?:\.\d+)?)\s*=", text):
        number = float(literal)
        value = int(number) if number.is_integer() else number
        if value not in values:
            values.append(value)
    if len(values) >= 2:
        return values

    # Some chapters reverse the pair as `Simplified: 0 / General: 1`.
    # A single colon-number can be a prose condition, so accept it only when
    # the field's own enum description names at least two distinct values.
    reverse_numeric: list[int | float] = []
    for literal in re.findall(r":\s*(-?\d+(?:\.\d+)?)(?=\s*(?:[),/·;]|$))", text):
        number = float(literal)
        value = int(number) if number.is_integer() else number
        if value not in reverse_numeric:
            reverse_numeric.append(value)
    if len(reverse_numeric) >= 2:
        return reverse_numeric

    # Design-code chapters also spell a choice as ``Static: STATIC / Stage:
    # STAGE``. The right-hand tokens are the wire values; require two uppercase
    # tokens so a single prose label or ``CODE: Standard`` cannot become an
    # enum by accident.
    reverse_symbolic: list[str] = []
    for value in re.findall(r":\s*([A-Z][A-Z0-9_-]*)(?=\s*(?:[),/·;]|$))", text):
        if value not in reverse_symbolic:
            reverse_symbolic.append(value)
    if len(reverse_symbolic) >= 2:
        return reverse_symbolic

    # A slash-separated number list such as ``(0/1/2)`` is likewise a finite
    # set when the field itself is already typed enum. Do not accept a tilde or
    # dash range here: those are bounds, not alternatives.
    numeric_list = re.search(
        r"(?<![A-Za-z0-9_.-])(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+(?:\.\d+)?)+)(?![A-Za-z0-9_.-])",
        text,
    )
    if numeric_list:
        listed: list[int | float] = []
        for literal in re.split(r"\s*/\s*", numeric_list.group(1)):
            value = _number(literal)
            if value not in listed:
                listed.append(value)
        if len(listed) >= 2:
            return listed

    # The same cell form is used for symbolic values, for example
    # ``Equivalent=... / Each=...``.  Requiring two distinct left-hand codes
    # keeps a condition on another field (``CODE=Standard``) out of this
    # field's enum.
    symbolic: list[str] = []
    for value in re.findall(r"(?<![A-Za-z0-9_.-])([A-Za-z][A-Za-z0-9_/-]*)\s*=", text):
        if value not in symbolic:
            symbolic.append(value)
    return symbolic if len(symbolic) >= 2 else []


def _enum_scalar(cell: str) -> Any | None:
    """Parse a complete value-table cell, or leave non-literal prose alone."""

    text = _clean(cell)
    if re.fullmatch(r'"[^"\\]+"', text):
        return text[1:-1]
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        number = float(text)
        return int(number) if number.is_integer() else number
    return None


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
    # A quoted string is a complete literal default, just like a JSON array or
    # object below. The manual uses this form for values such as ``"FIRST"``
    # and ``"ACTIVE"``; retaining its quotes as part of the value would turn a
    # documented fact into an unnecessary review note.
    if text.startswith('"') and text.endswith('"'):
        try:
            literal = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(literal, str):
                return literal, None
    # ``[]``, ``{}``, and JSON lists such as ``[\"AXIAL\"]`` are complete,
    # typed defaults stated by the manual. Keeping them as strings makes a
    # documented default look unverified, while interpreting prose such as
    # ``Auto`` or ``System`` would be a guess. Accept only a whole JSON array
    # or object so the distinction stays explicit.
    if text.startswith(("[", "{")):
        try:
            structured = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(structured, (list, dict)):
                return structured, None
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
    enum: list[Any] = dataclass_field(default_factory=list)
    constraints: dict[str, Any] = dataclass_field(default_factory=dict)
    condition: Optional[str] = None
    applies_when: list[tuple[str, str | int | float | bool]] = dataclass_field(default_factory=list)
    number: str = ""
    notes: list[str] = dataclass_field(default_factory=list)
    properties: list["ParsedField"] = dataclass_field(default_factory=list)
    products: tuple[str, ...] = ()
    shared_number_group: bool = False


# JSON member names may begin with a digit.  ``7TH_DOF_TYPE`` is an exact,
# quoted wire key in the bridge-operation chapter; rejecting it would turn a
# documented property into an invented ambiguity.  Keep the rest deliberately
# narrow so separators and prose still fail closed.
_PATH_SEGMENT = re.compile(r"^([A-Za-z0-9_]+)(\[\])?$")


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
    column, where a parent is `4` and its children are `(1)`/`(2)`, `4-1`/`4-2`,
    or `4.1`/`4.2`.
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
        if (
            _DESC_ARRAY_CHILD.match(entry.description)
            and "." not in key
            and last_root is not None
            and last_root.type == "array"
        ):
            entry.notes.append(
                f"the manual nests this under {last_root.key!r} by a dash description row"
            )
            _as_container(last_root, is_array=True)
            last_root.properties.append(entry)
            continue
        depth = 0
        if _NUMBER_CHILD.match(entry.number):
            depth = 1
        elif _NUMBER_PATH.match(entry.number):
            depth = len(re.findall(r"[-.]\d+", entry.number))
        if depth and entry.shared_number_group and "." not in key and not key.startswith("└"):
            grouped_parent = by_depth.get(depth - 1)
            if grouped_parent is not None:
                entry.notes.append(
                    f"the manual nests this under {grouped_parent.key!r} by numbering it "
                    f"{entry.number!r}, not by naming a path"
                )
                _as_container(grouped_parent, is_array=grouped_parent.type == "array")
                grouped_parent.properties.append(entry)
                by_depth[depth] = entry
                continue
            # A compact row can give multiple siblings the same child number.
            # Without an already-known numbered parent, the first key cannot
            # become an invented parent for the following literal keys.
            roots.append(entry)
            continue
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


@dataclass(frozen=True)
class StructuralTableMerge:
    """A manually transcribed destination for one supplementary table.

    A multi-table section is *not* safe to merge merely because its headings
    look related.  These entries exist only where the official manual names a
    containing object or array path.  They are deliberately keyed by table
    index as well as endpoint: a heading such as ``Parameters`` is repeated
    throughout several chapters and is not a reliable selector on its own.
    """

    table: int
    targets: tuple[tuple[str, ...], ...]
    products: tuple[str, ...] = ()


# The paths below are transcriptions of the parameter headings and surrounding
# prose in docs/manual, recorded in docs/variant_table_survey.md §B.  This is a
# closed allow-list, not a heuristic: any other extra table remains unmerged.
_STRUCTURAL_TABLE_SPLITS: dict[str, tuple[StructuralTableMerge, ...]] = {
    "/db/ACTL-M1": (
        StructuralTableMerge(1, (("TCELEM",),)),
        StructuralTableMerge(2, (("TCELEM", "CONVERGENCE"),)),
    ),
    "/db/BCCT": (
        StructuralTableMerge(1, ((),)),
        StructuralTableMerge(2, ((),)),
    ),
    "/db/GRDP": (StructuralTableMerge(1, ((),)),),
    "/db/IEHC": (StructuralTableMerge(1, ((),), ("gen",)),),
    "/db/IMFM": (StructuralTableMerge(1, ((),)),),
    "/db/MCON": (
        StructuralTableMerge(1, (("ITEMS", "SLAVES"),)),
        StructuralTableMerge(2, (("ITEMS", "SLAVES"),)),
    ),
    "/db/MVCTch": (
        StructuralTableMerge(1, ((),)),
        StructuralTableMerge(2, (("FREQ",),)),
        StructuralTableMerge(3, (("BRIDGE1",),)),
        StructuralTableMerge(4, (("BRIDGE2",),)),
    ),
    "/db/POGD": (
        StructuralTableMerge(1, (("NONL_OPT",),)),
        StructuralTableMerge(2, (("PHOP_OPT",),)),
    ),
    "/db/RPSC": (
        StructuralTableMerge(1, (("SBAR_ITEMS",),)),
        StructuralTableMerge(2, (("MBAR_ITEMS",),)),
    ),
    "/db/SBDO": (
        StructuralTableMerge(1, ((),), ("civil",)),
        StructuralTableMerge(2, ((),), ("gen",)),
    ),
    "/db/WVLD": (
        StructuralTableMerge(1, (("COEF",),)),
        StructuralTableMerge(2, (("COEF", "COEF_S"), ("COEF", "COEF_R"), ("COEF", "OVER_S"), ("COEF", "OVER_R"))),
        StructuralTableMerge(3, (("CHAR",),)),
        StructuralTableMerge(4, (("PROF",),)),
        StructuralTableMerge(5, (("PROF", "GRID_DATA"),)),
        StructuralTableMerge(6, ((),)),
        StructuralTableMerge(7, (("GROWTH",),)),
        StructuralTableMerge(8, (("USERGRID",), ("TRAJ",))),
    ),
    "/DESIGN/RC/KDS-41-20-2022/DCRM-WALL": (
        StructuralTableMerge(1, (("Assign", "ITEMS"),)),
    ),
    "/DESIGN/RC/KDS-41-20-2022/DCRE": (
        StructuralTableMerge(1, (("Assign", "BEAM"),)),
        StructuralTableMerge(2, (("Assign", "COLUMN"), ("Assign", "BRACE"))),
        StructuralTableMerge(3, (("Assign", "WALL"),)),
        StructuralTableMerge(4, (("Assign", "WALL", "MATERIAL_BY_DIAMETER_INPUT", "VERTICAL_END_REBAR"), ("Assign", "WALL", "MATERIAL_BY_DIAMETER_INPUT", "HORIZONTAL_REBAR"))),
        StructuralTableMerge(5, (("Assign", "WALL", "ADDITIONAL_WALL_DATA"),)),
    ),
    "/DESIGN/RC/KDS-41-20-2022/REBB": (
        StructuralTableMerge(1, (("Assign", "ITEMS", "BAR_SECTOR_I"), ("Assign", "ITEMS", "BAR_SECTOR_M"), ("Assign", "ITEMS", "BAR_SECTOR_J"))),
        StructuralTableMerge(2, (("Assign", "ITEMS", "ELEMS"),)),
    ),
    "/DESIGN/RC/KDS-41-20-2022/REBC": (
        StructuralTableMerge(1, (("Assign", "ITEMS", "MAIN_BAR"),)),
        StructuralTableMerge(2, (("Assign", "ITEMS", "SHEAR_BAR_END"), ("Assign", "ITEMS", "SHEAR_BAR_CEN"))),
        StructuralTableMerge(3, (("Assign", "ITEMS", "ELEMS"),)),
    ),
    "/DESIGN/RC/KDS-41-20-2022/REBR": (
        StructuralTableMerge(1, (("Assign", "ITEMS", "MAIN_BAR"),)),
        StructuralTableMerge(2, (("Assign", "ITEMS", "SHEAR_BAR_END"), ("Assign", "ITEMS", "SHEAR_BAR_CEN"))),
        StructuralTableMerge(3, (("Assign", "ITEMS", "ELEMS"),)),
    ),
    "/view/DISPLAY": tuple(StructuralTableMerge(index, (("Argument",),)) for index in range(1, 7)),
}


_STRUCTURAL_ROOT_MOVES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    # The design endpoints use an ID-keyed Assign map.  The parameter tables
    # describe the value under an Assign key, not sibling root keys.
    "/DESIGN/RC/KDS-41-20-2022/DCRM-WALL": (("ITEMS", ("Assign",)),),
    "/DESIGN/RC/KDS-41-20-2022/DCRE": (
        ("BEAM", ("Assign",)),
        ("COLUMN", ("Assign",)),
        ("BRACE", ("Assign",)),
        ("WALL", ("Assign",)),
    ),
    "/DESIGN/RC/KDS-41-20-2022/REBB": (("ITEMS", ("Assign",)),),
    "/DESIGN/RC/KDS-41-20-2022/REBC": (("ITEMS", ("Assign",)),),
    "/DESIGN/RC/KDS-41-20-2022/REBR": (("ITEMS", ("Assign",)),),
}


_STRUCTURAL_CONTAINERS: dict[str, tuple[str, ...]] = {
    # These names are headings in the manual's supplementary tables; the
    # table does not repeat a separate parent row in the base table.
    "/db/WVLD": ("COEF", "CHAR", "PROF"),
}


def _manual_container(key: str, *, condition: Optional[str] = None) -> ParsedField:
    """Create a container the manual names in a heading rather than a row."""

    return ParsedField(
        key=key,
        description="",
        type="object",
        items=None,
        requirement="conditional" if condition else "optional",
        documented_default=None,
        condition=condition,
    )


def _rchk_structural_fields(section: "Section") -> tuple[list[ParsedField], list[StructuralTableMerge]]:
    """Transcribe the two named BEAM/COLM objects in the RCHK manual section."""

    if len(section.tables) != 5:
        return copy.deepcopy(section.tables[0].fields), []

    def keyed(table: ParsedTable) -> dict[str, ParsedField]:
        return {field.key: copy.deepcopy(field) for field in _walk(table.fields)}

    beam_rows, column_rows, layer_rows, position_rows = (keyed(table) for table in section.tables[1:])
    try:
        beam_main = beam_rows["vMAIN"]
        beam_main.properties = [beam_rows[key] for key in ("SECTOR", "POS_TOP_LAYERS", "POS_BOT_LAYERS")]
        beam_sub = beam_rows["vSUB_BAR"]
        beam_sub.properties = [beam_rows[key] for key in (
            "SECTOR", "dSUB_BARNUM", "SUB_BARNAME", "dSUB_BARDIST", "dSUB_BARANGLE",
            "bTORSIONAL_BAR", "sTRTORBARNA", "dTORBAR_SPACING", "bBUNDLEDBAR",
            "dBUNDLEDBARNUM", "LONGIBARNA", "dLONGIBARNUM",
        )]
        col_layer = column_rows["vLAYER"]
        col_layer.properties = [column_rows[key] for key in ("INDEX", "dDc", "vPOSITION")]
        col_sub = column_rows["SUB_BAR"]
        col_sub.properties = [column_rows[key] for key in (
            "SUBBAR_NAME", "SUBBAR_DIST", "SUBBAR_NUM", "SUBBAR_NAME_Y", "SUBBAR_NAME_Z",
            "SUBBAR_NUM_Y", "SUBBAR_NUM_Z",
        )]
        layer = list(layer_rows.values())
        position = list(position_rows.values())
    except KeyError:
        return copy.deepcopy(section.tables[0].fields), []

    beam = _manual_container("BEAM", condition='MEMBTYPE="BEAM"')
    beam.properties = [beam_main, beam_sub]
    column = _manual_container("COLM", condition='MEMBTYPE="COLUMN"')
    column.properties = [col_layer, col_sub]
    beam_main.properties[1].properties = copy.deepcopy(layer)
    beam_main.properties[2].properties = copy.deepcopy(layer)
    col_layer.properties[2].properties = position
    return copy.deepcopy(section.tables[0].fields) + [beam, column], [
        StructuralTableMerge(index, (("BEAM",) if index in {1, 3} else ("COLM",),))
        for index in range(1, 5)
    ]


def _display_structural_fields(section: "Section") -> tuple[list[ParsedField], list[StructuralTableMerge]]:
    """DISPLAY's seven Argument groups are additive, never a one-of choice."""

    argument = _manual_container("Argument")
    for table in section.tables:
        if not _append_fields(argument.properties, copy.deepcopy(table.fields)):
            return copy.deepcopy(section.tables[0].fields), []
    return [argument], [StructuralTableMerge(index, (("Argument",),)) for index in range(len(section.tables))]


@dataclass(frozen=True)
class ParsedVariant:
    """One manual table selected by an explicitly documented discriminator."""

    field: str
    equals: str | int | float | bool
    table: ParsedTable


_VARIANT_CONDITION = re.compile(
    r'`?([A-Za-z_][A-Za-z0-9_.]*)`?\s*=\s*(?:"([^"]+)"|(-?\d+(?:\.\d+)?)|(true|false))',
    re.IGNORECASE,
)


def _variant_condition(text: str) -> tuple[str, str | int | float | bool] | None:
    """Read one literal discriminator condition without inferring a value.

    Conditions occur both in markdown headings (``TYPE = "FIRST"``) and in
    blank-key divider rows inside a parameter table
    (``OPT_AUTO_OPTIMIZE=false``). Boolean branches are wire values too, not
    prose labels, so preserve them as booleans rather than strings.
    """

    matches = _VARIANT_CONDITION.findall(text)
    if len(matches) != 1:
        return None
    field, string, numeric, boolean = matches[0]
    if string:
        return field, string
    if numeric:
        number = float(numeric)
        return field, int(number) if number.is_integer() else number
    return field, boolean.lower() == "true"


def _explicit_variants(tables: list[ParsedTable]) -> list[ParsedVariant]:
    """Model only an all-explicit, single-discriminator set of extra tables.

    A heading such as ``LINEAR only`` does not say which wire value selects the
    table, so it must stay unmerged.  Conversely, every extra table in the set
    must name exactly one backtick-delimited ``FIELD = VALUE`` condition and all
    must use the same field.  That makes the resulting discriminated shape a
    transcription, not an inference from table order or SDK code.
    """

    if len(tables) < 2:
        return []
    variants: list[ParsedVariant] = []
    for table in tables[1:]:
        condition = _variant_condition(table.heading)
        if condition is None:
            return []
        field, value = condition
        variants.append(ParsedVariant(field, value, table))
    if len({variant.field for variant in variants}) != 1:
        return []
    if len({variant.equals for variant in variants}) != len(variants):
        return []
    return variants


def _field_at_path(fields: list[ParsedField], path: tuple[str, ...]) -> Optional[ParsedField]:
    current = fields
    found: Optional[ParsedField] = None
    for part in path:
        found = next((field for field in current if field.key == part), None)
        if found is None:
            return None
        current = found.properties
    return found


def _append_fields(destination: list[ParsedField], additions: list[ParsedField]) -> bool:
    """Append a table's fields without silently replacing a documented key."""

    existing = {field.key: field for field in destination}
    for addition in additions:
        prior = existing.get(addition.key)
        if prior is None:
            destination.append(addition)
            existing[addition.key] = addition
            continue
        # Repeated NODE_KEY in MCON's two SLAVES layouts is the same field,
        # stated in both tables.  Preserve it once only when its documented
        # type and requirement agree; differing declarations remain blocked.
        if (prior.type, prior.requirement, prior.documented_default) != (
            addition.type,
            addition.requirement,
            addition.documented_default,
        ):
            return False
    return True


def _tag_products(fields: list[ParsedField], products: tuple[str, ...]) -> None:
    for field in fields:
        field.products = products
        _tag_products(field.properties, products)


def _structural_fields(section: "Section") -> tuple[list[ParsedField], list[StructuralTableMerge]]:
    """Apply only pre-audited structural table paths for one manual section.

    The return value lists exactly the table resolutions that succeeded.  A
    missing parent, duplicate key, or unlisted table is intentionally left out;
    render_draft will retain it under ``unmergedTables`` and promotion will
    continue to refuse it.
    """

    if not section.tables:
        return [], []
    if section.endpoint == "/db/RCHK":
        return _rchk_structural_fields(section)
    if section.endpoint == "/view/DISPLAY":
        return _display_structural_fields(section)
    fields = copy.deepcopy(section.tables[0].fields)

    for key in _STRUCTURAL_CONTAINERS.get(section.endpoint, ()):
        if _field_at_path(fields, (key,)) is None:
            fields.append(_manual_container(key))

    for key, parent_path in _STRUCTURAL_ROOT_MOVES.get(section.endpoint, ()):
        source = next((field for field in fields if field.key == key), None)
        parent = _field_at_path(fields, parent_path)
        if source is None or parent is None or source is parent:
            continue
        fields.remove(source)
        if not _append_fields(parent.properties, [source]):
            fields.append(source)

    resolved: list[StructuralTableMerge] = []
    by_table = {merge.table: merge for merge in _STRUCTURAL_TABLE_SPLITS.get(section.endpoint, ())}
    for index, table in enumerate(section.tables[1:], start=1):
        merge = by_table.get(index)
        if merge is None:
            continue
        if section.endpoint == "/DESIGN/RC/KDS-41-20-2022/DCRE" and index == 4:
            # The manual says the two arrays share the same item structure.
            # Its one table lists the two array names followed by their shared
            # REBAR_DIAMETER/MATERIAL item rows, so retain that hierarchy for
            # both arrays instead of putting the item rows beside them.
            parent = _field_at_path(fields, ("Assign", "WALL", "MATERIAL_BY_DIAMETER_INPUT"))
            rows = {field.key: copy.deepcopy(field) for field in _walk(table.fields)}
            if parent is not None and {"VERTICAL_END_REBAR", "HORIZONTAL_REBAR", "REBAR_DIAMETER", "MATERIAL"} <= rows.keys():
                children = [rows["REBAR_DIAMETER"], rows["MATERIAL"]]
                vertical = rows["VERTICAL_END_REBAR"]
                horizontal = rows["HORIZONTAL_REBAR"]
                vertical.properties = copy.deepcopy(children)
                horizontal.properties = copy.deepcopy(children)
                if _append_fields(parent.properties, [vertical, horizontal]):
                    resolved.append(merge)
            continue
        destinations: list[list[ParsedField]] = []
        for path in merge.targets:
            parent = _field_at_path(fields, path)
            if path and parent is None:
                destinations = []
                break
            destinations.append(fields if not path else parent.properties)
        if not destinations:
            continue
        # Clone for every target: the manual explicitly states the same item
        # shape for e.g. REBB's I/M/J sectors and REBC's two shear-bar objects.
        # Preflight every destination so a duplicate cannot leave a half-merged
        # draft that looks complete.
        destination_keys = [{field.key: field for field in destination} for destination in destinations]
        compatible = all(
            all(
                field.key not in keys
                or (keys[field.key].type, keys[field.key].requirement, keys[field.key].documented_default)
                == (field.type, field.requirement, field.documented_default)
                for field in table.fields
            )
            for keys in destination_keys
        )
        if not compatible:
            continue
        for destination in destinations:
            additions = copy.deepcopy(table.fields)
            if merge.products:
                _tag_products(additions, merge.products)
            if not _append_fields(destination, additions):
                raise AssertionError("preflighted structural table merge became incompatible")
        resolved.append(merge)
    return fields, resolved


def _conditional_fields(section: "Section", fields: list[ParsedField]) -> tuple[list[ParsedField], set[int]]:
    """Merge audited conditional tables without guessing a payload branch."""
    Condition = tuple[str, str | int | float | bool]
    audited: dict[str, dict[int, tuple[tuple[Condition, ...], str | None]]] = {
        "/db/CCFC": {
            1: ((("TYPE", "CONST"),), 'Constant 타입 (TYPE="CONST") 추가 파라미터'),
            2: ((("TYPE", "USER"),), 'User 타입 (TYPE="USER") 추가 파라미터'),
        },
        "/db/ETFC": {
            1: ((("TYPE", "CONST"),), 'Constant 타입 (TYPE="CONST") 추가 파라미터'),
            2: ((("TYPE", "SINE"),), 'Sine 타입 (TYPE="SINE") 추가 파라미터'),
            3: ((("TYPE", "USER"),), 'User 타입 (TYPE="USER") 추가 파라미터'),
        },
        "/db/PNLA": {
            1: ((("ELEM_TYPE", "PLATE"),), 'ELEM_TYPE = "PLATE"'),
            2: ((("SELECT_TYPE", "IN_GROUP"),), 'SELECT_TYPE = "IN_GROUP"'),
            3: ((("ELEM_TYPE", "SOLID"),), 'ELEM_TYPE = "SOLID"'),
        },
        "/db/THFC": {
            1: ((("FUNCTYPE", 1),), "Time Function (FUNCTYPE=1) 추가 파라미터"),
            2: ((("FUNCTYPE", 2),), "Sinusoidal (FUNCTYPE=2) 추가 파라미터"),
        },
        "/db/HSFC": {
            1: ((("TYPE", "CONST"),), 'Constant 타입 (TYPE="CONST") 추가 파라미터'),
            2: (
                (("TYPE", "FUNC"), ("OPT_USE_CONC_DATA", False)),
                'Code 타입 (TYPE="FUNC") - 콘크리트 데이터 미사용 (OPT_USE_CONC_DATA=false)',
            ),
            3: (
                (("TYPE", "FUNC"), ("OPT_USE_CONC_DATA", True)),
                'Code 타입 (TYPE="FUNC") - 콘크리트 데이터 사용 (OPT_USE_CONC_DATA=true)',
            ),
            4: ((("TYPE", "USER"),), 'User 타입 (TYPE="USER") 추가 파라미터'),
        },
        "/db/MVLDid": {
            1: (
                (("OPT_AUTO_LL", True),),
                "Auto Live Load Combinations (OPT_AUTO_LL=true)",
            ),
            2: (
                (("OPT_LC_FOR_PERMIT_LOAD", True),),
                "Permit Vehicle (OPT_LC_FOR_PERMIT_LOAD=true)",
            ),
        },
        # 05_DB_Boundary.md names both gates in every global-coordinate
        # table.  REF_SYSTEM alone is not enough: INPUT_METHOD selects the
        # Angle, 3Points, or Vector payload field.
        "/db/NLNK": {
            1: ((("REF_SYSTEM", 0),), "REF_SYSTEM=0 (요소계)"),
            2: ((("REF_SYSTEM", 1), ("INPUT_METHOD", 0)), "REF_SYSTEM=1 (전역계) – Angle 방식"),
            3: ((("REF_SYSTEM", 1), ("INPUT_METHOD", 1)), "REF_SYSTEM=1 (전역계) – 3Points 방식"),
            4: ((("REF_SYSTEM", 1), ("INPUT_METHOD", 2)), "REF_SYSTEM=1 (전역계) – Vector 방식"),
        },
        "/ope/GSBG": {
            1: ((("BATCH", True),), None),
            2: ((("BATCH", False),), None),
            3: ((("DGRM_TYPE", 0),), None),
        },
    }
    merged = copy.deepcopy(fields)
    resolved: set[int] = set()

    # HSFC documents OPT_USE_CONC_DATA in both FUNC subtables.  Its own
    # applicability is TYPE=FUNC, while its value selects the sibling field
    # set.  Do not assign either false or true branch to the shared selector.
    shared_selector_conditions: dict[tuple[str, int, str], tuple[tuple[Condition, ...], str]] = {
        ("/db/HSFC", 2, "OPT_USE_CONC_DATA"): ((("TYPE", "FUNC"),), 'Code 타입 (TYPE="FUNC")'),
        ("/db/HSFC", 3, "OPT_USE_CONC_DATA"): ((("TYPE", "FUNC"),), 'Code 타입 (TYPE="FUNC")'),
    }
    # The India moving-load manual repeats SUB_LOAD_ITEMS for the Auto Live
    # Load case and adds item members below it.  The named Array parent already
    # exists in the general-load table, so merge only the documented item
    # members at that path.  Treating them as root fields would recreate the
    # RIGD/OFFS flattening defect.
    conditional_child_paths: dict[tuple[str, int], tuple[str, ...]] = {
        ("/db/MVLDid", 1): ("SUB_LOAD_ITEMS",),
    }

    def annotate(entries: list[ParsedField], conditions: tuple[Condition, ...], raw: str) -> None:
        for entry in entries:
            entry.condition = entry.condition or raw
            entry.applies_when.extend(conditions)

    for index, (conditions, raw) in audited.get(section.endpoint, {}).items():
        if index >= len(section.tables):
            continue
        additions = copy.deepcopy(section.tables[index].fields)
        child_path = conditional_child_paths.get((section.endpoint, index))
        if child_path is not None:
            source = next((field for field in additions if field.key == child_path[-1]), None)
            destination = _field_at_path(merged, child_path)
            if source is None or destination is None:
                continue
            annotate(source.properties, conditions, raw or section.tables[index].heading)
            if not _append_fields(destination.properties, source.properties):
                continue
            additions.remove(source)
            # NUM_LOADED_LANES is a repeated scalar whose base declaration
            # already applies to every payload shape.  Its Auto table does not
            # add a distinct field, whereas SUB_LOAD_ITEMS adds item members.
            additions = [field for field in additions if field.key != "NUM_LOADED_LANES"]
        for addition in additions:
            special = shared_selector_conditions.get((section.endpoint, index, addition.key))
            annotate([addition], *(special or (conditions, raw or section.tables[index].heading)))
        if _append_fields(merged, additions):
            resolved.add(index)
    return merged, resolved


def _section_schema_hints(lines: list[str], endpoint: str) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    """Read exact property metadata from a section's own ``JSON Schema`` fence.

    The manual's parameter table remains the primary transcription.  Several
    chapters, however, render Markdown escapes in a table while the same
    section's JSON Schema spells out array items or enum values exactly.  This
    function reads only fenced JSON below a ``JSON Schema`` heading in that
    *same endpoint section*; examples and neighbouring endpoint schemas are
    deliberately excluded.
    """

    hints: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    endpoint_wrapper = endpoint.rsplit("/", 1)[-1]
    for index, line in enumerate(lines):
        if not re.fullmatch(r"#{2,}\s+JSON Schema\s*", line.strip(), re.IGNORECASE):
            continue
        start = next(
            (position for position in range(index + 1, len(lines)) if lines[position].strip() == "```json"),
            None,
        )
        if start is None:
            continue
        end = next(
            (position for position in range(start + 1, len(lines)) if lines[position].strip() == "```"),
            None,
        )
        if end is None:
            continue
        try:
            schema = json.loads("\n".join(lines[start + 1 : end]))
        except json.JSONDecodeError:
            continue
        # Several DB chapters wrap their schema in the endpoint token itself
        # (``{"NPLN": {...}}``), while their parameter table starts directly
        # at the record payload. It is an exact transport wrapper only when it
        # is the sole root member and exactly matches this endpoint.
        if isinstance(schema, dict) and set(schema) == {endpoint_wrapper} and isinstance(schema[endpoint_wrapper], dict):
            schema = schema[endpoint_wrapper]

        def condition_text(node: Any) -> Optional[str]:
            """Render one exact JSON-Schema selector without inventing a rule.

            The design-code chapters put conditional requiredness in ``allOf``
            as a one-property ``if`` plus a ``then.required`` list.  A general
            JSON Schema condition is more expressive than a contract field's
            short ``condition`` string, so accept only the two literal forms
            that can be transcribed losslessly: ``const`` and a finite scalar
            ``enum`` on exactly one named property.
            """

            if not isinstance(node, dict):
                return None
            properties = node.get("properties")
            if not isinstance(properties, dict) or len(properties) != 1:
                return None
            key, constraint = next(iter(properties.items()))
            if not isinstance(key, str) or not isinstance(constraint, dict):
                return None
            if "const" in constraint and isinstance(constraint["const"], (str, int, float, bool)):
                value = constraint["const"]
                rendered = json.dumps(value) if isinstance(value, str) else str(value).lower()
                return f"{key}={rendered}"
            values = constraint.get("enum")
            if (
                isinstance(values, list)
                and values
                and all(isinstance(value, (str, int, float, bool)) for value in values)
            ):
                rendered = [json.dumps(value) if isinstance(value, str) else str(value).lower() for value in values]
                return f"{key} ∈ {{{', '.join(rendered)}}}"
            return None

        def visit(node: Any, prefix: tuple[str, ...] = ()) -> None:
            if not isinstance(node, dict):
                return
            for branch_name in ("allOf", "anyOf", "oneOf"):
                for branch in node.get(branch_name, []):
                    visit(branch, prefix)
                    # A field table that says only "Conditional required" is
                    # completed only when this *same manual schema* names both
                    # the selector and the field that becomes required.  Do
                    # not turn a prose example, or a general JSON-Schema
                    # expression, into a condition claim.
                    if not isinstance(branch, dict):
                        continue
                    condition = condition_text(branch.get("if"))
                    then = branch.get("then")
                    required = then.get("required") if isinstance(then, dict) else None
                    if condition is None or not isinstance(required, list):
                        continue
                    for key in required:
                        if isinstance(key, str):
                            hints.setdefault(prefix + (key,), []).append(
                                {"__conditional": condition}
                            )
            properties = node.get("properties")
            if isinstance(properties, dict):
                required = node.get("required", [])
                required_names = set(required) if isinstance(required, list) and all(isinstance(name, str) for name in required) else set()
                for key, child in properties.items():
                    if not isinstance(key, str) or not isinstance(child, dict):
                        continue
                    # Endpoint wrappers are message transport, not payload
                    # members.  Table paths start immediately inside them.
                    if not prefix and key in {"Argument", "Assign", endpoint_wrapper}:
                        visit(child, prefix)
                        continue
                    path = prefix + (key,)
                    hint = dict(child)
                    hint["__required"] = key in required_names
                    hints.setdefault(path, []).append(hint)
                    visit(child, path)
            # ``Assign`` in the design-code chapters is a dictionary keyed by
            # an ID string.  Its single ``patternProperties`` child is the
            # record schema, not a field named by the regular expression.  At
            # the endpoint root it is therefore safe to unwrap that one layer;
            # doing this below a real field would fabricate a path, so do not.
            pattern_properties = node.get("patternProperties")
            if (
                not prefix
                and isinstance(pattern_properties, dict)
                and len(pattern_properties) == 1
            ):
                child = next(iter(pattern_properties.values()))
                if isinstance(child, dict):
                    visit(child, prefix)
            if node.get("type") == "array":
                # The extractor models Array[Object] children as properties of
                # the array field, so retain the same path when walking items.
                visit(node.get("items"), prefix)

        visit(schema)
    return hints


def _agreed_schema_value(entries: list[dict[str, Any]], key: str) -> Any | None:
    """Return a value only when concrete same-path properties agree on it.

    ``allOf.if/then`` contributes a small ``{"__conditional": ...}`` hint
    at the field made conditionally required.  That marker records the
    relation, but is not a competing property schema: it must not make an
    otherwise explicit enum, default, or type look absent.  Real property
    schemas remain deliberately strict -- every one that states *key* must
    agree before we transcribe it.
    """

    values = [entry[key] for entry in entries if key in entry]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        return None
    return values[0]


def _schema_enum_values(entry: dict[str, Any]) -> Optional[list[Any]]:
    """Read a complete scalar enum from one manual JSON-Schema property.

    Some design chapters use ``oneOf`` with one ``const`` per documented
    choice rather than JSON Schema's compact ``enum`` keyword. Both forms
    state the same finite wire-value set. A shortened ``oneOf`` (for example
    an ellipsis entry or a branch without ``const``) stays unverified.
    """

    enum = entry.get("enum")
    if isinstance(enum, list) and enum and all(isinstance(value, (str, int, float, bool)) for value in enum):
        return enum
    choices = entry.get("oneOf")
    if not isinstance(choices, list) or not choices:
        return None
    values: list[Any] = []
    for choice in choices:
        if not isinstance(choice, dict) or "const" not in choice:
            return None
        value = choice["const"]
        if not isinstance(value, (str, int, float, bool)) or value in values:
            return None
        values.append(value)
    return values


def _apply_schema_hints(tables: list[ParsedTable], hints: dict[tuple[str, ...], list[dict[str, Any]]]) -> None:
    """Fill only table gaps that the same section's JSON Schema states exactly."""

    def visit(fields: list[ParsedField], prefix: tuple[str, ...] = ()) -> None:
        for field in fields:
            path = prefix + (field.key,)
            entries = hints.get(path, [])
            if entries:
                # ``then.required`` contributes only ``__conditional``.  It
                # describes a relationship between fields and must not act as
                # a second, empty property schema when evaluating the
                # concrete property metadata below.
                property_entries = [
                    entry for entry in entries if any(not key.startswith("__") for key in entry)
                ]
                synthesized_note = (
                    "no row of its own in the manual - inferred from the dotted paths of its "
                    "children, so its requiredness and default are unknown"
                )
                # A parent introduced solely to represent an explicit
                # ``PARENT[].CHILD`` path is no longer inferred when this
                # section's own JSON Schema names that parent. The schema is
                # direct manual evidence for the container and its
                # requiredness; retain the note when there is no such source.
                if (
                    synthesized_note in field.notes
                    and isinstance(_agreed_schema_value(property_entries, "type"), str)
                    and isinstance(_agreed_schema_value(property_entries, "__required"), bool)
                ):
                    field.notes.remove(synthesized_note)
                required = _agreed_schema_value(property_entries, "__required")
                if field.requirement is None and isinstance(required, bool):
                    field.requirement = "required" if required else "optional"
                    for note in (
                        "the table has no Required column",
                        "the manual leaves the Required column blank",
                    ):
                        if note in field.notes:
                            field.notes.remove(note)

                conditions = [entry["__conditional"] for entry in entries if "__conditional" in entry]
                distinct_conditions = list(dict.fromkeys(conditions))
                if (
                    field.requirement == "conditional"
                    and field.condition is None
                    and len(distinct_conditions) == 1
                ):
                    field.condition = distinct_conditions[0]
                    conditional_note = "the manual marks this conditional but does not state the condition"
                    if conditional_note in field.notes:
                        field.notes.remove(conditional_note)

                default = _agreed_schema_value(property_entries, "default")
                if "the table has no Default column" in field.notes and default is not None:
                    field.documented_default = default
                    field.notes.remove("the table has no Default column")

                schema_enums = [_schema_enum_values(entry) for entry in property_entries]
                enum = schema_enums[0] if schema_enums and all(value == schema_enums[0] for value in schema_enums) else None
                if not field.enum and _ENUM_VALUES_ELSEWHERE in field.notes and enum:
                    field.enum = enum
                    if _ENUM_VALUES_ELSEWHERE in field.notes:
                        field.notes.remove(_ENUM_VALUES_ELSEWHERE)

                items = _agreed_schema_value(property_entries, "items")
                if field.type == "array" and field.items is None and isinstance(items, dict):
                    item_type = items.get("type")
                    if item_type in {"string", "number", "integer", "boolean", "object", "array"}:
                        field.items = {"type": item_type}
                        if "array element type not stated by the manual" in field.notes:
                            field.notes.remove("array element type not stated by the manual")

                for name in ("minimum", "maximum", "minItems", "maxItems", "minLength", "maxLength", "const"):
                    value = _agreed_schema_value(property_entries, name)
                    # Zero lower bounds are JSON Schema defaults, not a
                    # documented restriction.  Keeping them would manufacture
                    # drift against contracts that correctly omit a no-op.
                    if name in {"minItems", "minLength"} and value == 0:
                        continue
                    if value is not None and name not in field.constraints:
                        field.constraints[name] = value
            visit(field.properties, path)

    for table in tables:
        visit(table.fields)


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
    variants: list[ParsedVariant] = dataclass_field(default_factory=list)

    @property
    def id(self) -> str:
        return _slug(self.endpoint)


_ENUM_TABLE_HEADING = re.compile(r"\b(?:enum|oneof|one of)\b", re.IGNORECASE)


def _enum_tables(lines: list[str]) -> dict[str, list[Any]]:
    """Read ``**`PATH` values (enum):**`` tables from one endpoint section."""

    found: dict[str, list[Any]] = {}
    for index, line in enumerate(lines):
        if not _ENUM_TABLE_HEADING.search(line):
            continue
        paths = re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*)`", line)
        if len(paths) != 1:
            continue
        table = index + 1
        while table < len(lines) and not lines[table].startswith("#"):
            if lines[table].startswith("|") and table + 1 < len(lines) and _DIVIDER.match(lines[table + 1]):
                break
            table += 1
        if table >= len(lines) or not lines[table].startswith("|"):
            continue
        header = [_clean(cell).lower() for cell in lines[table].strip("|").split("|")]
        value_columns = [i for i, cell in enumerate(header) if cell in _ENUM_VALUE_COLUMNS]
        if not value_columns:
            continue
        values: list[Any] = []
        row = table + 2
        while row < len(lines) and lines[row].startswith("|"):
            cells = [cell.strip() for cell in lines[row].strip("|").split("|")]
            row += 1
            if len(cells) != len(header):
                continue
            for column in value_columns:
                value = _enum_scalar(cells[column])
                if value is not None and value not in values:
                    values.append(value)
        if values:
            found[paths[0]] = values
    return found


def _apply_enum_values(tables: list[ParsedTable], values_by_path: dict[str, list[Any]]) -> None:
    """Attach manual enum values to their exact field, including nested paths."""

    by_path: dict[str, ParsedField] = {}

    def walk(fields: list[ParsedField], prefix: str = "") -> None:
        for field in fields:
            path = f"{prefix}.{field.key}" if prefix else field.key
            by_path[path] = field
            walk(field.properties, path)

    for table in tables:
        walk(table.fields)

    for path, values in values_by_path.items():
        field = by_path.get(path)
        if field is None:
            continue
        if field.enum and field.enum != values:
            field.notes.append(
                f"the manual gives conflicting inline and table enum values for {path!r}; review both"
            )
            continue
        field.enum = values
        if _ENUM_VALUES_ELSEWHERE in field.notes:
            field.notes.remove(_ENUM_VALUES_ELSEWHERE)


def _parallel_cells(cell: str, count: int, *, key: bool = False) -> Optional[list[str]]:
    """Split a manual row only when it explicitly gives one value per field.

    The manual sometimes compresses independent keys into one row, using
    matching slash-separated Value Type, Default and Required cells. It is safe
    to restore those separate fields only when every column that makes a claim
    has the same cardinality. A singleton such as ``Optional`` beside two keys
    could apply to either key or both, so it deliberately returns ``None``.
    """

    text = _clean(cell)
    if key:
        quoted = re.findall(r'"([^"\\]+)"', text)
        if len(quoted) == count:
            return quoted
    parts = [part.strip().strip('"') for part in re.split(r"\s*/\s*", text)]
    if len(parts) != count or any(not part for part in parts):
        return None
    # ``Array [Number,4]/[Number,3]`` omits the repeated ``Array`` word in
    # the second half, but its brackets make the repeated form explicit.
    if parts[0].lower().startswith("array ["):
        parts = [part if index == 0 or not part.startswith("[") else f"Array {part}" for index, part in enumerate(parts)]
    return parts


def _parallel_field_cells(
    key_cell: str,
    type_cell: Optional[str],
    default_cell: Optional[str],
    required_cell: Optional[str],
    number: str,
) -> Optional[list[tuple[str, Optional[str], Optional[str], Optional[str]]]]:
    """Return exact parallel field columns, or ``None`` when a row is ambiguous."""

    raw_key = _clean(key_cell)
    quoted = re.findall(r'"([^"\\]+)"', raw_key)
    keys = quoted if len(quoted) > 1 else _parallel_cells(raw_key, 2, key=True)
    if not keys or len(keys) < 2:
        return None
    columns = [type_cell, default_cell, required_cell]
    parts: list[Optional[list[str]]] = []
    for cell in columns:
        if cell is None:
            parts.append(None)
            continue
        split = _parallel_cells(cell, len(keys))
        if split is None:
            # A row such as ``"R" "G" "B" | Integer | 0 | Optional``
            # names several literal wire keys but gives one *shared* claim in
            # every other column. That is different from ``String / Integer |
            # Optional``: there the singleton Required value cannot safely be
            # assigned to either differently typed key. The former is an exact
            # compact table notation for homogeneous vector components, so
            # repeat its complete shared claim for every literal key. A
            # key/description/type-only child table also makes this unambiguous:
            # it has no Default or Required columns that could vary by key.
            if (
                len(quoted) == len(keys)
                and (
                    "/" not in raw_key
                    or _NUMBER_CHILD.match(_clean(number)) is not None
                    or (default_cell is None and required_cell is None)
                )
                and all(cell is None or "/" not in _clean(cell) for cell in columns)
            ):
                parts = [None if cell is None else [_clean(cell)] * len(keys) for cell in columns]
                break
            return None
        parts.append(split)
    return [
        (
            key,
            parts[0][index] if parts[0] else None,
            parts[1][index] if parts[1] else None,
            parts[2][index] if parts[2] else None,
        )
        for index, key in enumerate(keys)
    ]


_QUOTED_ARRAY_PROPERTY = re.compile(
    r'^"([A-Za-z_][A-Za-z0-9_]*)"\[\]\.(?:"?)([A-Za-z_][A-Za-z0-9_]*)(?:"?)$'
)


def _canonical_wire_property(cell: str) -> str:
    """Transcribe a quoted array-member path into the contract's path syntax.

    The manual writes both ``"POINT"[].ITEM"`` and
    ``"SPAN_BASE_ITEMS"[].ELEM_KEY"``. Quotes decorate literal property
    tokens; they are not wire characters. Preserve every other key spelling so
    an unfamiliar decoration still reaches the review gate.
    """

    text = _clean(cell)
    match = _QUOTED_ARRAY_PROPERTY.fullmatch(text)
    if match:
        return f"{match.group(1)}[].{match.group(2)}"
    return text.strip('"')


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
        inline_variants: list[tuple[str, int, list[ParsedField], set[str]]] = []
        target_fields = fields
        target_seen = seen
        row = index + 2
        while row < len(lines) and lines[row].startswith("|"):
            cells = [cell.strip() for cell in lines[row].strip("|").split("|")]
            row += 1
            if len(cells) != len(header):
                continue
            key = _canonical_wire_property(cells[key_column])
            if not key or key in _EMPTY_CELLS:
                # Some manual tables use a blank-key row as an inline section
                # divider, e.g. ``General Load (OPT_AUTO_OPTIMIZE=false)``.
                # It is a variant only when it names one literal wire
                # discriminator. Keep each branch separate so repeated field
                # names are not flattened or deduplicated together.
                # Chapters put this divider in either the No. or Description
                # column, so inspect every non-key cell rather than assuming
                # one column layout.
                condition_text = next(
                    (
                        cell
                        for cell_index, cell in enumerate(cells)
                        if cell_index != key_column and _variant_condition(_clean(cell)) is not None
                    ),
                    "",
                )
                if _variant_condition(_clean(condition_text)) is not None:
                    target_fields = []
                    target_seen = set()
                    inline_variants.append(
                        (_clean(condition_text), offset + row, target_fields, target_seen)
                    )
                continue
            parallel = _parallel_field_cells(
                cells[key_column],
                cells[type_column] if type_column is not None else None,
                cells[default_column] if default_column is not None else None,
                cells[required_column] if required_column is not None else None,
                cells[0] if cells else "",
            )
            entries = parallel or [
                (
                    key,
                    cells[type_column] if type_column is not None else None,
                    cells[default_column] if default_column is not None else None,
                    cells[required_column] if required_column is not None else None,
                )
            ]
            for entry_key, entry_type, entry_default, entry_required in entries:
                if entry_key in target_seen:
                    continue
                target_seen.add(entry_key)

                notes: list[str] = []
                if entry_required is not None:
                    requirement, condition, note = _normalize_requirement(entry_required)
                else:
                    requirement, condition, note = None, None, "the table has no Required column"
                # Some chapters put only "conditional required" in the
                # Required column but spell the one literal selector in the
                # Description cell.  Preserve that exact condition when there
                # is precisely one; two selectors or prose-only wording stay
                # unresolved rather than being guessed.
                if requirement == "conditional" and condition is None and desc_column is not None:
                    description_condition = _variant_condition(_clean(cells[desc_column]))
                    if description_condition is not None:
                        condition_field, condition_value = description_condition
                        rendered_value = (
                            json.dumps(condition_value)
                            if isinstance(condition_value, str)
                            else str(condition_value).lower()
                        )
                        condition = f"{condition_field}={rendered_value}"
                        note = None
                    else:
                        condition = _condition_from_description(cells[desc_column])
                        if condition is not None:
                            note = None
                if note:
                    notes.append(note)
                field_type, items, note = _normalize_type(entry_type) if entry_type is not None else (None, None, "the table has no Value Type column")
                if note:
                    notes.append(note)
                enum = _enum_values_from_inline_type(entry_type) if entry_type is not None else []
                if not enum and note == _ENUM_VALUES_ELSEWHERE and desc_column is not None:
                    enum = _enum_values_from_description(cells[desc_column])
                if enum and _ENUM_VALUES_ELSEWHERE in notes:
                    notes.remove(_ENUM_VALUES_ELSEWHERE)
                constraints = _type_constraints(entry_type) if entry_type is not None else {}
                default, note = _normalize_default(entry_default) if entry_default is not None else (None, "the table has no Default column")
                if note:
                    notes.append(note)
                type_default = _type_default(entry_type) if entry_type is not None else None
                if default is None and type_default is not None:
                    default = type_default
                elif type_default is not None and default != type_default:
                    notes.append(
                        f"the Default column says {default!r}, but the Value Type cell says {type_default!r}"
                    )
                target_fields.append(
                    ParsedField(
                        key=entry_key,
                        description=_DESC_TREE.sub("", _clean(cells[desc_column])).strip() if desc_column is not None else "",
                        type=field_type,
                        items=items,
                        requirement=requirement,
                        documented_default=default,
                        enum=enum,
                        constraints=constraints,
                        condition=condition,
                        number=_clean(cells[0]) if cells else "",
                        notes=notes,
                        shared_number_group=parallel is not None,
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
        for variant_heading, variant_line, variant_fields, _ in inline_variants:
            if variant_fields:
                tables.append(
                    ParsedTable(
                        heading=variant_heading,
                        line=variant_line,
                        fields=_nest(variant_fields),
                    )
                )
        index = row
    return tables


_TOC_METHOD_COLUMNS = {"methods", "active methods", "메서드"}
_TOC_NAME_COLUMNS = {"function", "feature", "description", "name", "기능", "설명"}


def _toc_metadata(lines: list[str]) -> dict[str, tuple[list[str], str]]:
    """Read labels and, where present, methods from a chapter's contents table.

    15 chapters state each endpoint's verbs once, in the table of contents,
    rather than in the endpoint's own section. Without this the extractor falls
    back to the /db/* default of all four verbs, which is how /db/GRUP's first
    draft claimed a DELETE the endpoint does not serve.

    The same tables carry the manual's human-readable resource labels in
    chapters whose endpoint headings are deliberately terse. A methods column
    is therefore optional here: several chapters have a label but no verbs.
    """
    found: dict[str, tuple[list[str], str]] = {}
    for index, line in enumerate(lines):
        if not (line.startswith("|") and index + 1 < len(lines) and _DIVIDER.match(lines[index + 1])):
            continue
        header = [cell.strip().lower() for cell in line.strip("|").split("|")]
        if "endpoint" not in header:
            continue
        method_column = next((i for i, h in enumerate(header) if h in _TOC_METHOD_COLUMNS), None)
        name_column = next((i for i, h in enumerate(header) if h in _TOC_NAME_COLUMNS), None)
        if method_column is None and name_column is None:
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
            verbs = (
                sorted(
                    {
                        v
                        for v in re.findall(r"[A-Z]+", cells[method_column])
                        if v in {"GET", "POST", "PUT", "DELETE"}
                    }
                )
                if method_column is not None
                else []
            )
            title = _clean(cells[name_column]) if name_column is not None else ""
            path = endpoint.group(0)
            found[path if path.startswith("/") else "/" + path] = (verbs, title)
    return found


def parse_chapter(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    toc_metadata = _toc_metadata(lines)
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
        title = (match.group(3) or "").strip()
        toc_methods, toc_title = toc_metadata.get(endpoint, ([], ""))
        if not title:
            # Name precedence follows the manual's increasingly indirect
            # evidence: section heading, then opening blockquote, then chapter
            # contents table. Each later form only fills a missing label.
            # Only inspect introductory metadata, so a bold note in
            # Specifications cannot become the endpoint name.
            for line in body:
                if line.startswith("###"):
                    break
                blockquote_title = _BLOCKQUOTE_TITLE.match(line)
                if blockquote_title:
                    title = blockquote_title.group(1).strip()
                    break
        if not title:
            title = toc_title

        section = Section(
            chapter_file=path.name,
            number=match.group(1),
            endpoint=endpoint,
            title=title,
            heading=lines[index].lstrip("#").strip(),
            lines=body,
        )
        text = "\n".join(body)
        url = _SOURCE_URL.search(text)
        if url:
            section.source_url = url.group(1)
        section.methods = _section_methods(body)
        if not section.methods:
            section.methods = toc_methods
        section.tables = _parse_tables(body, index)
        _apply_enum_values(section.tables, _enum_tables(body))
        _apply_schema_hints(section.tables, _section_schema_hints(body, section.endpoint))
        section.variants = _explicit_variants(section.tables)
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
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ": "))

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
        if parsed.products:
            lines.append(f"{body}products: [{', '.join(parsed.products)}]")
        if parsed.type:
            lines.append(f"{body}type: {parsed.type}")
            if parsed.items and parsed.items.get("type"):
                lines.append(f"{body}items:")
                lines.append(f"{body}  type: {parsed.items['type']}")
                if parsed.type == "array" and parsed.enum:
                    lines.append(f"{body}  enum: [{', '.join(_scalar(value) for value in parsed.enum)}]")
        else:
            lines.append(f"{body}type: string   # TODO(review): the manual did not state a type")
        for key, value in parsed.constraints.items():
            lines.append(f"{body}{key}: {_scalar(value)}")
        lines.append(
            f"{body}requirement: {parsed.requirement}"
            if parsed.requirement
            else f"{body}requirement: optional   # TODO(review): the manual did not state requiredness"
        )
        if parsed.condition:
            lines.append(f"{body}condition: {_scalar(parsed.condition)}")
        elif parsed.requirement == "conditional":
            lines.append(f"{body}condition: \"TODO(review): the manual does not state the condition\"")
        if parsed.applies_when:
            lines.append(f"{body}appliesWhen:")
            for condition_path, equals in parsed.applies_when:
                lines.append(f"{body}  - path: {_scalar(condition_path)}")
                lines.append(f"{body}    equals: {_scalar(equals)}")
        lines.append(f"{body}documentedDefault: {_scalar(parsed.documented_default)}")
        lines.append(f"{body}documentedOptional: {'true' if parsed.requirement == 'optional' else 'false'}")
        if parsed.enum and parsed.type != "array":
            lines.append(f"{body}enum: [{', '.join(_scalar(value) for value in parsed.enum)}]")

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
    fields, structural_merges = _structural_fields(section)
    fields, conditional_merges = _conditional_fields(section, fields)
    resolved_tables = {merge.table for merge in structural_merges} | conditional_merges
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

    if not section.title:
        lines.append(
            "# NOTE: the manual does not state a human-readable endpoint label; keep this draft unpromoted."
        )

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
        lines += _render_fields(fields, "  ", evidence)
        lines.append("")

    if section.variants:
        lines.append("variants:")
        for variant in section.variants:
            lines += [
                "  - when:",
                f"      field: {_scalar(variant.field)}",
                f"      equals: {_scalar(variant.equals)}",
                "    source:",
                f"      table: {_scalar(variant.table.heading)}",
                f"      line: {variant.table.line}",
                "    fields:",
            ]
            lines += _render_fields(variant.table.fields, "      ")
        lines.append("")

    lines.append("extraction:")
    lines.append(f"  source: {section.chapter_file} line {main.line if main else '?'}")
    lines.append(f"  table: {_scalar(main.heading if main else 'none found')}")
    if structural_merges:
        lines.append("  structuralTables:")
        for merge in structural_merges:
            table = section.tables[merge.table]
            lines.append(f"    - heading: {_scalar(table.heading)}")
            lines.append(f"      line: {table.line}")
            lines.append("      paths:")
            for target in merge.targets:
                lines.append(f"        - {_scalar('.'.join(target) or '<root>')}")
    unresolved = [
        (index, table)
        for index, table in enumerate(section.tables[1:], start=1)
        if index not in resolved_tables
    ]
    if unresolved and not section.variants:
        lines.append("  # Additional parameter tables in this section were NOT merged. They are")
        lines.append("  # usually conditional variants selected by a type/code field. Decide")
        lines.append("  # whether they belong in this contract's fields, as nested `properties`,")
        lines.append("  # or as a separate contract - do not assume the first table is the whole")
        lines.append("  # schema.")
        lines.append("  unmergedTables:")
        for _, table in unresolved:
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
    unnamed = [section for section in sections if not section.title]
    print(
        f"\nname extraction: {len(unnamed)} section(s) have no human-readable label in the "
        "heading, opening blockquote, or chapter contents table."
    )

    # How trustworthy is that field count? Anything carrying a note needs a human
    # before it can be believed, and saying so is the difference between a draft
    # and a claim.
    all_fields = [f for section in sections for table in section.tables for f in _walk(table.fields)]
    structured_conditions = 0
    for section in sections:
        rendered_fields, _ = _structural_fields(section)
        rendered_fields, _ = _conditional_fields(section, rendered_fields)
        structured_conditions += sum(len(field.applies_when) for field in _walk(rendered_fields))
    flagged = [f for f in all_fields if f.notes]
    nested = [f for f in all_fields if f.properties]
    print(
        f"\nacross every parsed table: {len(all_fields)} fields, {len(nested)} of them nested, "
        f"{len(flagged)} carrying a review note ({100 * len(flagged) // max(len(all_fields), 1)}%)."
    )
    print(f"structured appliesWhen conditions extracted: {structured_conditions}")
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

    # Stage 2's blockers are intentionally measured here, rather than copied
    # into a planning document by hand.  These are all review notes: a value
    # not counted as parseable stays unverified rather than being guessed.
    enum_missing = sum(_ENUM_VALUES_ELSEWHERE in field.notes for field in all_fields)
    array_element_missing = sum(
        "array element type not stated by the manual" in field.notes for field in all_fields
    )
    unrecognised_types = sum(
        any(note.startswith("unrecognised Value Type") for note in field.notes) for field in all_fields
    )
    explicit_variants = sum(bool(section.variants) for section in sections)
    unmerged_variant_tables = sum(
        len(section.tables) > 1 and not section.variants for section in sections
    )
    print(
        "\nStage 2 fidelity blockers: "
        f"{enum_missing} enum value list(s) unstated, "
        f"{array_element_missing} array element type(s) unstated, "
        f"{unrecognised_types} unrecognised Value Type cell(s)."
    )
    # Keep the six recurring promotion notes measurable here.  These are field
    # occurrences across every parsed manual table, deliberately not a
    # hand-counted list of draft refusals: one endpoint can carry several notes
    # and a single note can be repeated in nested rows.
    promotion_note_counts = {
        "conditional requirement has no stated condition": sum(
            "the manual marks this conditional but does not state the condition" in field.notes
            for field in all_fields
        ),
        "Required cell is blank": sum(
            "the manual leaves the Required column blank" in field.notes for field in all_fields
        ),
        "enum values are unstated": enum_missing,
        "array item type is unstated": array_element_missing,
        "table has no Default column": sum(
            "the table has no Default column" in field.notes for field in all_fields
        ),
        "non-literal System default kept verbatim": sum(
            "non-literal default 'System' kept verbatim; confirm what the server does" in field.notes
            for field in all_fields
        ),
    }
    print("  promotion-note forms (field occurrences):")
    for label, count in promotion_note_counts.items():
        print(f"    {count:>5}  {label}")
    print(
        f"  conditional tables: {explicit_variants} explicitly modelled variant set(s), "
        f"{unmerged_variant_tables} left unmerged because their selector is not explicit."
    )

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
        table_contracts = list(TABLE_DIR.glob("*.yaml")) if TABLE_DIR.is_dir() else []
        print(
            f"\n{skipped} sections across {len(table_family)} chapters belong to the shared "
            f"/post/TABLE/table-result family and are not endpoint contracts:"
        )
        for chapter, count in sorted(table_family.items()):
            print(f"  {count:>3}  {chapter}")
        print(
            "  table-contract coverage: "
            f"{len(table_contracts)} contracted result tables."
        )
        print(
            "  Chapter 23 also contains /post/PM and /post/STEELCODECHECK; "
            "they are separate routes, not TABLE_TYPE result tables."
        )

    promoted = {path.stem for path in ENDPOINT_DIR.glob("*.yaml")} if ENDPOINT_DIR.is_dir() else set()
    drafted = {path.stem for path in DRAFT_DIR.glob("*.yaml")} if DRAFT_DIR.is_dir() else set()
    print(f"\npromoted contracts: {len(promoted)}   drafts awaiting review: {len(drafted - promoted)}")
    resource_inventory = ROOT / "schema" / "typescript-resources.json"
    if resource_inventory.is_file():
        try:
            resources = json.loads(resource_inventory.read_text(encoding="utf-8")).get("resources", [])
            resource_endpoints = {
                item["endpoint"]
                for item in resources
                if isinstance(item, dict) and isinstance(item.get("endpoint"), str)
            }
            contract_endpoints = {
                next(
                    (line.removeprefix("endpoint: ").strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("endpoint: ")),
                    "",
                )
                for path in ENDPOINT_DIR.glob("*.yaml")
            }
        except (json.JSONDecodeError, OSError):
            resource_endpoints = set()
            contract_endpoints = set()
        if resource_endpoints:
            covered = resource_endpoints & contract_endpoints
            print(
                "npm resource contract coverage (committed inventory): "
                f"{len(covered)} of {len(resource_endpoints)} covered; "
                f"{len(resource_endpoints - covered)} without a contract."
            )
            # A missing contract can still be a parser or review problem, but a
            # resource absent from every parsed manual section has no manual
            # payload source at all. Report that separately so it is not
            # mistaken for an ordinary promotable draft.
            manual_endpoints = {section.endpoint for section in sections}
            no_manual_section = sorted(resource_endpoints - manual_endpoints)
            print(
                "npm resource manual-section coverage: "
                f"{len(no_manual_section)} without a parsed manual section."
            )
            if no_manual_section:
                print("  " + ", ".join(no_manual_section))
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

        # Use the same closed structural merge map as draft emission.  Without
        # this, --check would wrongly call a nested supplementary-table field
        # contract drift simply because it only inspected the first table.
        manual_shape, _ = _structural_fields(section)
        manual_shape, _ = _conditional_fields(section, manual_shape)
        manual_fields = _flatten_manual(manual_shape)
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
            if manual.enum and "enum" not in overridden:
                declared_enum = (
                    declared.get("items", {}).get("enum", [])
                    if manual.type == "array"
                    else declared.get("enum", [])
                )
                if declared_enum != manual.enum:
                    problems.append(
                        f"{path.name}: {key} enum={declared_enum!r}, manual says {manual.enum!r}"
                    )
            if manual.constraints and "field_value" not in overridden:
                constraint_keys = {
                    "minimum",
                    "exclusiveMinimum",
                    "maximum",
                    "exclusiveMaximum",
                    "notEqual",
                    "const",
                    "minItems",
                    "maxItems",
                    "minLength",
                    "maxLength",
                }
                declared_constraints = {
                    name: value for name, value in declared.items() if name in constraint_keys
                }
                if declared_constraints != manual.constraints:
                    problems.append(
                        f"{path.name}: {key} constraints={declared_constraints!r}, "
                        f"manual says {manual.constraints!r}"
                    )

        for key in contract_fields:
            if key not in manual_fields and "field_name" not in overridden:
                problems.append(
                    f"{path.name}: the contract declares {key!r}, which the manual's table does not - "
                    f"record it under manualDefects if the manual is the one that is wrong"
                )

        if section.variants:
            declared_variants = {
                (variant.get("when", {}).get("field"), variant.get("when", {}).get("equals")): variant
                for variant in contract.get("variants", [])
            }
            for variant in section.variants:
                label = f"{variant.field}={variant.equals!r}"
                declared_variant = declared_variants.get((variant.field, variant.equals))
                if declared_variant is None:
                    problems.append(f"{path.name}: manual variant {label} is missing from the contract")
                    continue
                variant_manual = _flatten_manual(variant.table.fields)
                variant_contract = _flatten_contract(declared_variant.get("fields", []))
                for key, manual in variant_manual.items():
                    declared = variant_contract.get(key)
                    if declared is None:
                        problems.append(f"{path.name}: variant {label} omits manual field {key!r}")
                        continue
                    if manual.type and declared["type"] != manual.type:
                        problems.append(
                            f"{path.name}: variant {label} field {key} typed {declared['type']!r}, "
                            f"manual says {manual.type!r}"
                        )
                    if manual.requirement and declared["requirement"] != manual.requirement:
                        problems.append(
                            f"{path.name}: variant {label} field {key} requirement "
                            f"{declared['requirement']!r}, manual says {manual.requirement!r}"
                        )
                    if declared.get("documentedDefault") != manual.documented_default:
                        problems.append(
                            f"{path.name}: variant {label} field {key} documentedDefault="
                            f"{declared.get('documentedDefault')!r}, manual says {manual.documented_default!r}"
                        )
                for key in variant_contract:
                    if key not in variant_manual:
                        problems.append(
                            f"{path.name}: variant {label} declares {key!r}, which its manual table does not"
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
    parser.add_argument("--report", action="store_true", help="print extraction coverage and blocker counts (the default mode)")
    args = parser.parse_args(argv)

    sections, table_family = load_manual(args.manual_api_repo)

    if args.check:
        return run_check(sections)
    if args.emit or args.emit_all:
        return run_emit(sections, args.emit or [], args.emit_all)
    return run_report(sections, table_family)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
