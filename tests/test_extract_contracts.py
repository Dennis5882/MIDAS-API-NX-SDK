"""Guards for the manual-to-contract extractor.

These run against synthetic chapter text rather than the sibling manual repo, so
the suite still passes with no live server and no second checkout. The one thing
they will not let slide is the extractor inventing certainty: a draft that fills
in `safeToOmit` from a manual that says "Optional" would turn the documentation
into evidence, and the CI gate built on the difference between those two would
stop meaning anything.
"""

import json
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_contracts as ex  # noqa: E402

CHAPTER = """# 99 DB — Synthetic

## 1. `/db/SYNTH` — Synthetic Endpoint

- **Methods**: `POST`, `GET`, `PUT`, `DELETE`
- **Source**: [Synth ↗](https://support.midasuser.com/hc/en-us/articles/1)

### Specifications

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Ordering Index | `"NO"` | Integer | - | Read Only |
| 2 | Name | `"NAME"` | String | - | Required |
| 3 | Flag | `"bFLAG"` | Boolean | false | Optional |
| 4 | Count | `"COUNT"` | Number | 0 | Optional |
| 5 | Span check | `"SPAN"` | Number | - | Required (bEXACTSPAN=true) |
| 6 | Items | `"ITEMS"` | Array [Object] | - | Required |
| 7 | └ Item name | `"ITEMS[].ITEM_NAME"` | String | - | Required |
| 8 | └ Item value | `"ITEMS[].ITEM_VALUE"` | Number | 1 | Optional |
| 9 | Nested leaf | `"CFG.MODE"` | String | - | Optional |
| 10 | Ambiguous | `"A" / "B"` | String | - | Optional |
| 11 | Non-negative value | `"NON_NEGATIVE"` | Number (≥0) | - | Required |
| 12 | Fixed code | `"CODE"` | String(7) | - | Required |
| 13 | Fixed vector | `"VECTOR"` | Number,3 | - | Required |
| 14 | Inline boolean default | `"INLINE_DEFAULT"` | Boolean (default false) | - | Optional |
| 15 | Fixed numeric value | `"CONST_VALUE"` | Number (const 0.75) | - | Read Only |
| 16 | Reversed numeric choices (Zero: 0 / One: 1) | `"REVERSED"` | Integer (enum) | - | Required |
| 17 | Explicit paired fields | `"ENABLED"` / `"LIMIT"` | Boolean / Number | false / 0 | Optional / Required |
| 18 | Digit-prefixed wire key | `"7TH_DOF_TYPE"` | Integer | 0 | Optional |
| 19 | Escaped fixed vector | `"ESCAPED_VECTOR"` | Array \\[Number, 3\\] | - | Required |
| 20 | Conditional from description (`MODE="SPECIAL"`) | `"SPECIAL_VALUE"` | Number | - | Conditional Required |
| 21 | Empty item defaults | `"DEFAULT_ITEMS"` | Array [Number] | [] | Optional |
| 22 | Empty object default | `"DEFAULT_OPTIONS"` | Object | {} | Optional |
| 23 | Quoted string default | `"DEFAULT_MODE"` | String | `"FIRST"` | Optional |

### Variant table

#### TYPE=SPECIAL 전용

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Special only | `"SPECIAL"` | String | - | Required |
"""


@pytest.fixture
def section(tmp_path: Path) -> ex.Section:
    path = tmp_path / "99_DB_Synthetic.md"
    path.write_text(CHAPTER, encoding="utf-8")
    sections = ex.parse_chapter(path)
    assert len(sections) == 1
    return sections[0]


def test_section_metadata(section: ex.Section):
    assert section.endpoint == "/db/SYNTH"
    assert section.id == "db-synth"
    assert section.title == "Synthetic Endpoint"
    assert section.methods == ["DELETE", "GET", "POST", "PUT"]
    assert section.source_url == "https://support.midasuser.com/hc/en-us/articles/1"


@pytest.mark.parametrize(
    ("heading", "intro", "expected_title"),
    [
        pytest.param(
            "## 1. `/db/TITLE`",
            "> **Title in Blockquote** - endpoint description",
            "Title in Blockquote",
            id="opening-blockquote-title",
        ),
        pytest.param(
            "## 1. `/db/TITLE` - Title in Heading",
            "> **Ignored Blockquote Title** - endpoint description",
            "Title in Heading",
            id="heading-title-wins",
        ),
    ],
)
def test_section_title_reads_the_documented_intro_form(
    tmp_path: Path, heading: str, intro: str, expected_title: str
):
    path = tmp_path / "99_DB_Title.md"
    path.write_text(f"# Synthetic\n\n{heading}\n\n{intro}\n\n### Specifications\n", encoding="utf-8")

    assert ex.parse_chapter(path)[0].title == expected_title


@pytest.mark.parametrize(
    ("label_header", "expected_title"),
    [
        pytest.param("기능", "Korean Function Label", id="korean-function-column"),
        pytest.param("설명", "Korean Description Label", id="korean-description-column"),
        pytest.param("Feature", "English Feature Label", id="english-feature-column"),
    ],
)
def test_section_title_reads_the_documented_contents_table_label(
    tmp_path: Path, label_header: str, expected_title: str
):
    path = tmp_path / "99_DB_Title.md"
    path.write_text(
        "# Synthetic\n\n"
        f"| No. | Endpoint | {label_header} | Methods |\n"
        "|---|---|---|---|\n"
        f"| 1 | [`/db/TITLE`](#1-dbtitle) | {expected_title} | GET |\n\n"
        "## 1. `/db/TITLE`\n",
        encoding="utf-8",
    )

    section = ex.parse_chapter(path)[0]
    assert section.title == expected_title
    assert section.methods == ["GET"]


@pytest.mark.parametrize(
    ("heading", "intro", "expected_title"),
    [
        pytest.param(
            "## 1. `/db/TITLE` - Heading Title",
            "> **Blockquote Title** - endpoint description",
            "Heading Title",
            id="heading-before-blockquote-and-contents-table",
        ),
        pytest.param(
            "## 1. `/db/TITLE`",
            "> **Blockquote Title** - endpoint description",
            "Blockquote Title",
            id="blockquote-before-contents-table",
        ),
    ],
)
def test_section_title_uses_contents_table_only_after_heading_and_blockquote(
    tmp_path: Path, heading: str, intro: str, expected_title: str
):
    path = tmp_path / "99_DB_Title.md"
    path.write_text(
        "# Synthetic\n\n"
        "| No. | Endpoint | 기능 |\n"
        "|---|---|---|\n"
        "| 1 | [`/db/TITLE`](#1-dbtitle) | Contents Table Title |\n\n"
        f"{heading}\n\n"
        f"{intro}\n",
        encoding="utf-8",
    )

    assert ex.parse_chapter(path)[0].title == expected_title


def test_requiredness_and_defaults_come_from_the_table(section: ex.Section):
    fields = {f.key: f for f in section.tables[0].fields}

    assert fields["NO"].requirement == "read_only"
    assert fields["NAME"].requirement == "required"
    assert fields["NAME"].documented_default is None
    assert fields["bFLAG"].requirement == "optional"
    assert fields["bFLAG"].documented_default is False
    assert fields["COUNT"].documented_default == 0


def test_render_draft_keeps_manual_condition_and_structured_applies_when(section: ex.Section):
    field = next(field for field in section.tables[0].fields if field.key == "SPECIAL_VALUE")
    field.condition = "MODE=\"SPECIAL\""
    field.applies_when = [("MODE", "SPECIAL"), ("OPTIONS.ENABLED", True)]

    rendered = yaml.safe_load(ex.render_draft(section))["fields"]
    rendered_field = next(entry for entry in rendered if entry["key"] == "SPECIAL_VALUE")
    assert rendered_field["condition"] == 'MODE="SPECIAL"'
    assert rendered_field["appliesWhen"] == [
        {"path": "MODE", "equals": "SPECIAL"},
        {"path": "OPTIONS.ENABLED", "equals": True},
    ]


def test_inline_conditions_are_kept_verbatim(section: ex.Section):
    span = {f.key: f for f in section.tables[0].fields}["SPAN"]

    assert span.requirement == "conditional"
    assert span.condition == "bEXACTSPAN=true"


def test_exact_description_condition_completes_a_conditional_required_marker(section: ex.Section):
    special = {field.key: field for field in section.tables[0].fields}["SPECIAL_VALUE"]

    assert special.requirement == "conditional"
    assert special.condition == 'MODE="SPECIAL"'
    assert not special.notes


@pytest.mark.parametrize(
    ("description_form", "expected_condition"),
    [
        pytest.param(
            'Detail (MODE\uac00 USER\uc77c \ub54c \ud544\uc218)',
            'MODE\uac00 USER\uc77c \ub54c \ud544\uc218',
            id="parenthesized_korean_selector",
        ),
        pytest.param(
            "Detail \u2014 OPT_USE\uac00 true\uc77c \ub54c \ud544\uc218",
            "OPT_USE\uac00 true\uc77c \ub54c \ud544\uc218",
            id="em_dash_korean_selector",
        ),
        pytest.param(
            "Detail (when INPUT_MODE is MANUAL)",
            "when INPUT_MODE is MANUAL",
            id="parenthesized_english_selector",
        ),
    ],
)
def test_explicit_description_condition_forms_are_retained_verbatim(
    description_form: str, expected_condition: str, tmp_path: Path
):
    path = tmp_path / "99_DB_DescriptionCondition.md"
    path.write_text(
        "## 1. `/db/DESCRIPTION-CONDITION` -- Description condition\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        f"| 1 | {description_form} | `DETAIL` | Number | - | Conditional Required |\n",
        encoding="utf-8",
    )

    detail = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert detail.requirement == "conditional"
    assert detail.condition == expected_condition
    assert not detail.notes


def test_dotted_paths_become_nested_fields(section: ex.Section):
    fields = {f.key: f for f in section.tables[0].fields}

    items = fields["ITEMS"]
    assert items.type == "array"
    assert items.items == {"type": "object"}
    assert [child.key for child in items.properties] == ["ITEM_NAME", "ITEM_VALUE"]
    assert items.properties[1].documented_default == 1

    # A parent the manual never gave a row of its own is synthesized, and says so.
    cfg = fields["CFG"]
    assert cfg.type == "object"
    assert [child.key for child in cfg.properties] == ["MODE"]
    assert any("no row of its own" in note for note in cfg.notes)


def test_ambiguous_keys_are_flagged_not_guessed(section: ex.Section):
    ambiguous = {f.key: f for f in section.tables[0].fields}

    assert 'A" / "B' in ambiguous
    assert any("more than one" in note for note in ambiguous['A" / "B'].notes)


def test_exact_digit_prefixed_wire_key_is_not_treated_as_an_ambiguous_label(section: ex.Section):
    fields = {field.key: field for field in section.tables[0].fields}

    assert fields["7TH_DOF_TYPE"].type == "integer"
    assert not fields["7TH_DOF_TYPE"].notes


def test_explicit_type_constraints_are_preserved(section: ex.Section):
    fields = {field.key: field for field in section.tables[0].fields}
    assert fields["NON_NEGATIVE"].type == "number"
    assert fields["NON_NEGATIVE"].constraints == {"minimum": 0}
    assert fields["CODE"].type == "string"
    assert fields["CODE"].constraints == {"minLength": 7, "maxLength": 7}
    assert fields["VECTOR"].type == "array"
    assert fields["VECTOR"].items == {"type": "number"}
    assert fields["VECTOR"].constraints == {"minItems": 3, "maxItems": 3}
    assert fields["ESCAPED_VECTOR"].type == "array"
    assert fields["ESCAPED_VECTOR"].items == {"type": "number"}
    assert fields["ESCAPED_VECTOR"].constraints == {"minItems": 3, "maxItems": 3}
    assert fields["INLINE_DEFAULT"].type == "boolean"
    assert fields["INLINE_DEFAULT"].documented_default is False
    assert fields["CONST_VALUE"].constraints == {"const": 0.75}
    assert fields["DEFAULT_ITEMS"].documented_default == []
    assert fields["DEFAULT_OPTIONS"].documented_default == {}
    assert fields["DEFAULT_MODE"].documented_default == "FIRST"
    assert fields["REVERSED"].enum == [0, 1]
    assert fields["ENABLED"].type == "boolean"
    assert fields["ENABLED"].documented_default is False
    assert fields["ENABLED"].requirement == "optional"
    assert fields["LIMIT"].type == "number"
    assert fields["LIMIT"].documented_default == 0
    assert fields["LIMIT"].requirement == "required"

    draft_fields = {field["key"]: field for field in yaml.safe_load(ex.render_draft(section))["fields"]}
    assert draft_fields["NON_NEGATIVE"]["minimum"] == 0
    assert draft_fields["CODE"]["maxLength"] == 7
    assert draft_fields["VECTOR"]["items"]["type"] == "number"
    assert draft_fields["VECTOR"]["minItems"] == 3
    assert draft_fields["INLINE_DEFAULT"]["documentedDefault"] is False
    assert draft_fields["CONST_VALUE"]["const"] == 0.75
    assert draft_fields["DEFAULT_ITEMS"]["documentedDefault"] == []
    assert draft_fields["DEFAULT_OPTIONS"]["documentedDefault"] == {}
    assert draft_fields["DEFAULT_MODE"]["documentedDefault"] == "FIRST"


def test_only_exact_parallel_columns_are_split_into_independent_fields(tmp_path: Path):
    path = tmp_path / "99_DB_Parallel.md"
    path.write_text(
        """# 99 DB — Parallel

## 1. `/db/PARALLEL` — Parallel fields

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Exact pair | `"FIRST"` / `"SECOND"` | String / Integer | `"A"` / 2 | Optional / Required |
| 2 | Ambiguous pair | `"LEFT"` / `"RIGHT"` | String / Integer | - | Optional |
""",
        encoding="utf-8",
    )
    fields = ex.parse_chapter(path)[0].tables[0].fields
    by_key = {field.key: field for field in fields}

    assert {"FIRST", "SECOND"} <= set(by_key)
    assert by_key["FIRST"].type == "string"
    assert by_key["SECOND"].type == "integer"
    # One Required value beside two keys is not enough to assign it safely.
    assert 'LEFT" / "RIGHT' in by_key
    assert any("more than one" in note for note in by_key['LEFT" / "RIGHT'].notes)


@pytest.mark.parametrize(
    ("number", "key_cell", "expected"),
    [
        ("1", '"R" "G" "B"', ["R", "G", "B"]),
        ("(3)", '"FACTOR" / "CENT_F"', ["FACTOR", "CENT_F"]),
        ("(4)", '"DT" / "DB"', ["DT", "DB"]),
    ],
)
def test_literal_key_groups_with_shared_metadata_are_split(
    tmp_path: Path, number: str, key_cell: str, expected: list[str]
):
    """The manual's one-row homogeneous field shorthand preserves every key."""

    path = tmp_path / "99_DB_LiteralGroup.md"
    path.write_text(
        f"""## 1. `/db/GROUP` -- literal keys

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| {number} | Homogeneous values | {key_cell} | Number | 0 | Optional |
""",
        encoding="utf-8",
    )
    fields = ex.parse_chapter(path)[0].tables[0].fields
    assert [field.key for field in fields] == expected
    assert all(field.type == "number" and field.documented_default == 0 for field in fields)


def test_key_type_only_table_splits_quoted_literal_group_without_a_child_number(tmp_path: Path):
    """A three-column child table gives one homogeneous type for every literal key."""

    path = tmp_path / "99_DB_KeyTypeGroup.md"
    path.write_text(
        """## 1. `/db/GROUP` -- literal keys

| Key | Description | Value Type |
|---|---|---|
| `"RC_C1L1"`/`"RC_C1F1"`/`"RC_C1L2"`/`"RC_C1F2"` | Case values | Number |
""",
        encoding="utf-8",
    )

    fields = ex.parse_chapter(path)[0].tables[0].fields
    assert [field.key for field in fields] == ["RC_C1L1", "RC_C1F1", "RC_C1L2", "RC_C1F2"]
    assert all(field.type == "number" for field in fields)


def test_dotted_numbering_nests_children_under_the_documented_parent(tmp_path: Path):
    """The manual's 14.4.1 notation is a payload hierarchy, not a flat key list."""

    path = tmp_path / "99_DB_DottedNumbering.md"
    path.write_text(
        """## 1. `/db/DOTTED` -- dotted numbering

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 14 | Root | `"ROOT"` | Object | - | Optional |
| 14.4 | Child object | `"CHILD"` | Object | - | Optional |
| 14.4.1 | Leaf | `"LEAF"` | String | - | Required |
""",
        encoding="utf-8",
    )

    root = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert root.key == "ROOT"
    assert [field.key for field in root.properties] == ["CHILD"]
    assert [field.key for field in root.properties[0].properties] == ["LEAF"]


def test_parenthesised_dash_numbering_nests_and_preserves_literal_conditions(tmp_path: Path):
    """``2-(N)`` rows are child payload fields, not independent root keys."""

    path = tmp_path / "99_DB_ParenthesisedNumbering.md"
    path.write_text(
        """## 1. `/db/PARENTHESISED` -- parenthesised numbering

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 2 | Mass control | `"MASS_CONTROL"` | Object | - | Required |
| 2-(1) | Type: `LUMPED` / `CONSISTENT` | `"MASS_TYPE"` | String (enum) | - | Required |
| 2-(2) | Position (`MASS_TYPE="LUMPED"`): `CENTROID` / `OFFSET` | `"MASS_POS"` | String (enum) | - | Conditional Required |
| 2-(3) | Convert self-weight | `"SELFWEIGHT"` | Boolean | - | Required |
| 2-(4) | Axis (`SELFWEIGHT=true`): `XYZ` / `XY` / `Z` | `"MASS_AXIS"` | String (enum) | - | Conditional Required |
""",
        encoding="utf-8",
    )

    root = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert root.key == "MASS_CONTROL"
    assert [field.key for field in root.properties] == [
        "MASS_TYPE",
        "MASS_POS",
        "SELFWEIGHT",
        "MASS_AXIS",
    ]
    mass_type, mass_pos, _, mass_axis = root.properties
    assert mass_type.enum == ["LUMPED", "CONSISTENT"]
    assert mass_pos.enum == ["CENTROID", "OFFSET"]
    assert mass_pos.applies_when == [("MASS_TYPE", "LUMPED")]
    assert mass_axis.enum == ["XYZ", "XY", "Z"]
    assert mass_axis.applies_when == [("SELFWEIGHT", True)]


@pytest.mark.parametrize(
    ("manual_key", "contract_key"),
    [
        ('"POINT"[].ITEM"', "POINT[].ITEM"),
        ('"SPAN_BASE_ITEMS"[].ELEM_KEY"', "SPAN_BASE_ITEMS[].ELEM_KEY"),
    ],
)
def test_quoted_array_member_paths_are_transcribed_without_quote_characters(
    manual_key: str, contract_key: str
):
    assert ex._canonical_wire_property(manual_key) == contract_key


@pytest.mark.parametrize(
    ("property_schema", "expected"),
    [
        ({"enum": [0, 1]}, [0, 1]),
        ({"oneOf": [{"const": "LEFT"}, {"const": "RIGHT"}]}, ["LEFT", "RIGHT"]),
        ({"oneOf": [{"const": "D4"}, {"title": "remaining values"}]}, None),
    ],
)
def test_schema_enum_forms_only_accept_complete_literal_lists(property_schema: dict, expected: list | None):
    assert ex._schema_enum_values(property_schema) == expected


def test_endpoint_named_schema_wrapper_is_not_a_payload_property(tmp_path: Path):
    path = tmp_path / "99_DB_WrappedSchema.md"
    path.write_text(
        """## 1. `/db/WRAPPED` -- wrapped schema

### JSON Schema
```json
{"WRAPPED": {"type": "object", "properties": {"POINT": {"type": "array", "items": {"type": "object", "properties": {"ITEM": {"type": "number"}}}}}}}
```

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Point item | `"POINT"[].ITEM"` | Number | - | Optional |
""",
        encoding="utf-8",
    )
    field = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert field.key == "POINT"
    assert field.type == "array"
    assert field.items == {"type": "object"}
    assert field.properties[0].key == "ITEM"
    assert not field.notes


@pytest.mark.parametrize(
    ("manual_type", "item_type", "length"),
    [
        ("Array[Number,21]", "number", 21),
        ("Array[Number, 6]", "number", 6),
        ("Array[Integer,2]", "integer", 2),
        ("Array[Boolean,6]", "boolean", 6),
        ("Array[Object,3]", "object", 3),
    ],
)
def test_fixed_length_array_forms_are_transcribed_without_nesting(
    manual_type: str, item_type: str, length: int
):
    assert ex._normalize_type(manual_type) == ("array", {"type": item_type}, None)
    assert ex._type_constraints(manual_type) == {"minItems": length, "maxItems": length}


def test_compact_object_arrays_and_literal_type_cells_are_transcribed_without_guessing():
    assert ex._normalize_type("Array[{PY, PZ}]") == ("array", {"type": "object"}, None)
    assert ex._normalize_type('"KDS(41-17-00:2019)"') == ("string", None, None)
    assert ex._type_constraints('"KDS(41-17-00:2019)"') == {"const": "KDS(41-17-00:2019)"}
    field_type, _, note = ex._normalize_type("Object (oneOf)")
    assert field_type == "object"
    assert "does not state" in note


def test_report_prints_measured_stage_two_blockers(section: ex.Section, capsys: pytest.CaptureFixture[str]):
    assert ex.run_report([section], {}) == 0
    output = capsys.readouterr().out
    assert "Stage 2 fidelity blockers:" in output
    assert "promotion-note forms (field occurrences):" in output
    assert "conditional requirement has no stated condition" in output
    assert "non-literal System default kept verbatim" in output
    assert "supplementary tables:" in output
    assert "unmerged supplementary tables by manual selector evidence:" in output


def test_report_measures_table_contract_coverage(section: ex.Section, capsys: pytest.CaptureFixture[str]):
    assert ex.run_report([section], {"18_POST_PreProcess.md": 10}) == 0
    output = capsys.readouterr().out
    assert "table-contract coverage:" in output
    assert "/post/PM and /post/STEELCODECHECK" in output


def test_report_separates_resources_with_no_parsed_manual_section(
    section: ex.Section, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    inventory = tmp_path / "schema"
    endpoints = tmp_path / "contracts" / "endpoints"
    drafts = tmp_path / "contracts" / "drafts"
    inventory.mkdir()
    endpoints.mkdir(parents=True)
    drafts.mkdir(parents=True)
    (inventory / "typescript-resources.json").write_text(
        json.dumps({"resources": [{"endpoint": "/db/SYNTH"}, {"endpoint": "/db/NOSECTION"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(ex, "ROOT", tmp_path)
    monkeypatch.setattr(ex, "ENDPOINT_DIR", endpoints)
    monkeypatch.setattr(ex, "DRAFT_DIR", drafts)

    assert ex.run_report([section], {}) == 0
    output = capsys.readouterr().out
    assert "1 without a parsed manual section." in output
    assert "/db/NOSECTION" in output


def test_conditional_variant_tables_are_reported_not_merged(section: ex.Section):
    assert len(section.tables) == 2
    assert section.variants == []
    main_keys = {f.key for f in section.tables[0].fields}

    assert "SPECIAL" not in main_keys
    assert section.tables[1].heading == "TYPE=SPECIAL 전용"


@pytest.mark.parametrize(
    ("endpoint", "extra_headings", "expected"),
    [
        pytest.param(
            "/db/CCFC",
            ['Constant 타입 (TYPE="CONST")', 'User 타입 (TYPE="USER")'],
            [("CONST_FIELD", [("TYPE", "CONST")]), ("USER_FIELD", [("TYPE", "USER")])],
            id="exclusive-string-type-tables",
        ),
        pytest.param(
            "/db/ETFC",
            ['Constant 타입 (TYPE="CONST")', 'Sine 타입 (TYPE="SINE")', 'User 타입 (TYPE="USER")'],
            [
                ("CONST_FIELD", [("TYPE", "CONST")]),
                ("SINE_FIELD", [("TYPE", "SINE")]),
                ("USER_FIELD", [("TYPE", "USER")]),
            ],
            id="three-way-exclusive-string-type-tables",
        ),
        pytest.param(
            "/db/PNLA",
            ['ELEM_TYPE = "PLATE"', 'SELECT_TYPE = "IN_GROUP"', 'ELEM_TYPE = "SOLID"'],
            [
                ("PLATE_FIELD", [("ELEM_TYPE", "PLATE")]),
                ("GROUP_FIELD", [("SELECT_TYPE", "IN_GROUP")]),
                ("SOLID_FIELD", [("ELEM_TYPE", "SOLID")]),
            ],
            id="independent-string-selector-tables",
        ),
        pytest.param(
            "/db/THFC",
            ["Time Function (FUNCTYPE=1)", "Sinusoidal (FUNCTYPE=2)"],
            [("TIME_FIELD", [("FUNCTYPE", 1)]), ("SINE_FIELD", [("FUNCTYPE", 2)])],
            id="exclusive-integer-type-tables",
        ),
        pytest.param(
            "/db/NLNK",
            [
                "REF_SYSTEM=0 (element)",
                "REF_SYSTEM=1 (global) - angle",
                "REF_SYSTEM=1 (global) - 3Points",
                "REF_SYSTEM=1 (global) - vector",
            ],
            [
                ("ELEMENT_FIELD", [("REF_SYSTEM", 0)]),
                ("ANGLE_FIELD", [("REF_SYSTEM", 1), ("INPUT_METHOD", 0)]),
                ("POINTS_FIELD", [("REF_SYSTEM", 1), ("INPUT_METHOD", 1)]),
                ("VECTOR_FIELD", [("REF_SYSTEM", 1), ("INPUT_METHOD", 2)]),
            ],
            id="nested-integer-selectors-use-and-semantics",
        ),
        pytest.param(
            "/db/HSFC",
            [
                'Constant (TYPE="CONST")',
                'Code (TYPE="FUNC", OPT_USE_CONC_DATA=false)',
                'Code (TYPE="FUNC", OPT_USE_CONC_DATA=true)',
                'User (TYPE="USER")',
            ],
            [
                ("CONST_FIELD", [("TYPE", "CONST")]),
                ("FUNC_FALSE_FIELD", [("TYPE", "FUNC"), ("OPT_USE_CONC_DATA", False)]),
                ("FUNC_TRUE_FIELD", [("TYPE", "FUNC"), ("OPT_USE_CONC_DATA", True)]),
                ("USER_FIELD", [("TYPE", "USER")]),
            ],
            id="nested-boolean-selector-tables",
        ),
    ],
)
def test_audited_conditional_table_forms_keep_source_text_and_structured_conditions(
    endpoint: str,
    extra_headings: list[str],
    expected: list[tuple[str, list[tuple[str, str | int]]]],
):
    base = ex.ParsedField("BASE", "Base", "string", None, "required", None)
    tables = [ex.ParsedTable("Base", 1, [base])]
    for index, heading in enumerate(extra_headings, 1):
        key = expected[index - 1][0]
        field = ex.ParsedField(key, key, "number", None, "required", None)
        tables.append(ex.ParsedTable(heading, index + 1, [field]))
    section = ex.Section("manual.md", "1", endpoint, endpoint, endpoint, [], tables=tables)

    fields, resolved = ex._conditional_fields(section, [base])

    assert resolved == set(range(1, len(tables)))
    by_key = {field.key: field for field in fields}
    for key, conditions in expected:
        assert by_key[key].applies_when == conditions
        assert by_key[key].condition


@pytest.mark.parametrize(
    ("parent_type", "expect_child"),
    [
        pytest.param("Array[Object]", True, id="dash-row-after-array-is-an-item-property"),
        pytest.param("Object", False, id="dash-row-after-non-array-is-not-inferred"),
    ],
)
def test_dash_number_row_only_nests_under_an_explicit_array(parent_type: str, expect_child: bool, tmp_path: Path):
    """The manual's dash marker is structural only with its Array parent."""
    path = tmp_path / "99_DB_DashArray.md"
    path.write_text(
        "## 1. `/db/DASH-ARRAY` -- dash array rows\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|---|---|---|---|---|---|\n"
        f'| 1 | Values | `ITEM` | {parent_type} | - | Required |\n'
        "| 2 | - Time | `TIME` | Number | - | Required |\n",
        encoding="utf-8",
    )

    fields = ex.parse_chapter(path)[0].tables[0].fields
    if expect_child:
        assert [field.key for field in fields] == ["ITEM"]
        assert [field.key for field in fields[0].properties] == ["TIME"]
    else:
        assert [field.key for field in fields] == ["ITEM", "TIME"]


def test_conditional_array_table_merges_only_into_its_named_item_path():
    """MVLDid's Auto table extends SUB_LOAD_ITEMS; it never creates root keys."""
    base_item = ex.ParsedField("BASE", "base", "string", None, "required", None)
    sub_load_items = ex.ParsedField("SUB_LOAD_ITEMS", "items", "array", {"type": "object"}, "required", None)
    sub_load_items.properties = [base_item]
    auto_sub_load_items = ex.ParsedField("SUB_LOAD_ITEMS", "items", "array", {"type": "object"}, "required", None)
    auto_extra = ex.ParsedField("VEHICLE_CLASS_2", "auto-only", "string", None, "required", None)
    auto_sub_load_items.properties = [auto_extra]
    tables = [
        ex.ParsedTable("Parameters", 1, [sub_load_items]),
        ex.ParsedTable("Auto Live Load Combinations", 2, [
            ex.ParsedField("NUM_LOADED_LANES", "count", "integer", None, "required", None),
            auto_sub_load_items,
        ]),
        ex.ParsedTable("Permit Vehicle", 3, [
            ex.ParsedField("PERMIT_VEHICLE", "permit", "integer", None, "required", None),
        ]),
    ]
    section = ex.Section("manual.md", "1", "/db/MVLDid", "Moving Load Cases – India", "manual", [], tables=tables)

    fields, resolved = ex._conditional_fields(section, tables[0].fields)

    assert resolved == {1, 2}
    assert [field.key for field in fields] == ["SUB_LOAD_ITEMS", "PERMIT_VEHICLE"]
    child = fields[0].properties[1]
    assert child.key == "VEHICLE_CLASS_2"
    assert child.applies_when == [("OPT_AUTO_LL", True)]
    assert fields[1].applies_when == [("OPT_LC_FOR_PERMIT_LOAD", True)]


def test_structural_table_merge_uses_the_manual_named_object_path(tmp_path: Path):
    """A structural table goes below TCELEM, never beside it at record root."""
    path = tmp_path / "99_DB_Structural.md"
    path.write_text(
        """## 1. `/db/ACTL-M1` -- control

### Base
| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Truss options | `"TCELEM"` | Object | - | Optional |

### TCELEM object
| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Increment count | `"NUMINC"` | Integer | 1 | Optional |
| 2 | Convergence | `"CONVERGENCE"` | Object | - | Optional |

### CONVERGENCE object
| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Use criterion | `"OPT_USE"` | Boolean | false | Optional |
""",
        encoding="utf-8",
    )
    draft = yaml.safe_load(ex.render_draft(ex.parse_chapter(path)[0]))
    tcelem = draft["fields"][0]
    assert [field["key"] for field in tcelem["properties"]] == ["NUMINC", "CONVERGENCE"]
    assert tcelem["properties"][1]["properties"][0]["key"] == "OPT_USE"
    assert "unmergedTables" not in draft["extraction"]
    assert draft["extraction"]["structuralTables"][0]["paths"] == ["TCELEM"]


def test_product_partition_stays_on_fields_not_the_endpoint(tmp_path: Path):
    path = tmp_path / "99_DB_ProductSplit.md"
    path.write_text(
        """## 1. `/db/IEHC` -- hinge control

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Beam | `"BEAM"` | Boolean | false | Optional |

### GEN-only fields
| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 2 | Wall | `"WALL"` | Boolean | false | Optional |
""",
        encoding="utf-8",
    )
    draft = yaml.safe_load(ex.render_draft(ex.parse_chapter(path)[0]))
    fields = {field["key"]: field for field in draft["fields"]}
    assert fields["WALL"]["products"] == ["gen"]
    assert "products" not in fields["BEAM"]


def test_explicit_variant_tables_preserve_their_discriminator_and_do_not_merge(tmp_path: Path):
    path = tmp_path / "99_DB_Variants.md"
    path.write_text(
        """# 99 DB — Variants

## 1. `/db/VARIANT` — Explicit variants

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Select shape | `"TYPE"` | String | - | Required |

### First (`TYPE = "FIRST"`)

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 2 | First-only value | `"FIRST_VALUE"` | Number | - | Required |

### Second (`TYPE = "SECOND"`)

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 3 | Second-only value | `"SECOND_VALUE"` | String | - | Required |
""",
        encoding="utf-8",
    )

    parsed = ex.parse_chapter(path)[0]
    assert [(variant.field, variant.equals) for variant in parsed.variants] == [
        ("TYPE", "FIRST"),
        ("TYPE", "SECOND"),
    ]
    assert {field.key for field in parsed.tables[0].fields} == {"TYPE"}

    draft = yaml.safe_load(ex.render_draft(parsed))
    assert "unmergedTables" not in draft["extraction"]
    assert draft["variants"][0]["when"] == {"field": "TYPE", "equals": "FIRST"}
    assert draft["variants"][1]["fields"][0]["key"] == "SECOND_VALUE"


def test_bold_table_labels_supply_literal_variant_selectors(tmp_path: Path):
    """A bold label immediately preceding a table is equivalent to a heading."""

    path = tmp_path / "99_DB_BoldVariant.md"
    path.write_text(
        """## 1. `/db/BOLD-VARIANT` -- bold variant labels

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Type | `TYPE` | String | - | Required |

**Constant (`TYPE="CONST"`) additional parameters**

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 2 | Constant value | `CONST_VALUE` | Number | - | Required |

**User (`TYPE="USER"`) additional parameters**

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 3 | User value | `USER_VALUE` | Number | - | Required |
""",
        encoding="utf-8",
    )

    parsed = ex.parse_chapter(path)[0]
    assert [(variant.field, variant.equals) for variant in parsed.variants] == [
        ("TYPE", "CONST"),
        ("TYPE", "USER"),
    ]


def test_prose_and_inline_bold_emphasis_do_not_replace_a_table_heading(tmp_path: Path):
    """Only a full bold label directly attached to a table becomes its heading."""

    path = tmp_path / "99_DB_ProseBeforeTable.md"
    path.write_text(
        """## 1. `/db/PROSE-LABEL` -- prose before a table

### Parameters

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 1 | Root | `ROOT` | String | - | Required |

The following has the same child structure (all **Required**):

| No. | Description | Key | Value Type | Default | Required |
|---|---|---|---|---|---|
| 2 | Child | `CHILD` | String | - | Required |
""",
        encoding="utf-8",
    )

    tables = ex.parse_chapter(path)[0].tables
    assert [table.heading for table in tables] == ["Parameters", "Parameters"]


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        pytest.param('Variant (`TYPE="A"` / `TYPE="B"`)', "selector with several values", id="repeated_string_assignments"),
        pytest.param("Variant (`FLOOR_DIST_TYPE=1 or 2`)", "selector with several values", id="numeric_or_list"),
        pytest.param('Variant (`TYPE="A"`)', "selector with one value", id="one_string_value"),
        pytest.param("Variant (STYPE: 1)", "selector with one value", id="colon_numeric_value"),
        pytest.param("Variant (`TYPE`)", "no selector stated", id="field_name_without_equality"),
        pytest.param("Variant table", "no selector stated", id="label_only"),
    ],
)
def test_selector_evidence_reports_only_explicit_manual_literals(heading: str, expected: str):
    assert ex._selector_evidence(heading) == expected


def test_inline_boolean_variant_rows_preserve_branches_and_roman_children(tmp_path: Path):
    """A divider row in one table is a variant only when it names a wire value."""
    path = tmp_path / "99_DB_InlineVariants.md"
    path.write_text(
        """# 99 DB Inline variants

## 1. `/db/INLINE-VARIANT` -- Inline variants

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Choose mode | `"OPT_MODE"` | Boolean | false | Optional |
| | General (`OPT_MODE`=false) | | | | |
| 2 | Items | `"ITEMS"` | Array[Object] | - | Required |
| (i) | General value | `"VALUE"` | Number | - | Required |
| | Optimized (`OPT_MODE`=true) | | | | |
| 2 | Distance | `"DISTANCE"` | Number | - | Required |
""",
        encoding="utf-8",
    )

    parsed = ex.parse_chapter(path)[0]
    assert [(variant.field, variant.equals) for variant in parsed.variants] == [
        ("OPT_MODE", False),
        ("OPT_MODE", True),
    ]
    assert [field.key for field in parsed.tables[0].fields] == ["OPT_MODE"]
    items = parsed.variants[0].table.fields[0]
    assert items.key == "ITEMS"
    assert items.properties[0].key == "VALUE"

    draft = yaml.safe_load(ex.render_draft(parsed))
    assert draft["variants"][0]["when"] == {"field": "OPT_MODE", "equals": False}


def test_manual_check_compares_explicit_variant_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "99_DB_VariantCheck.md"
    path.write_text(
        """# 99 DB — Variant check

## 1. `/db/VARIANT-CHECK` — Explicit variants

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Select shape | `"TYPE"` | String | - | Required |

### First (`TYPE = "FIRST"`)

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 2 | First-only value | `"FIRST_VALUE"` | Number | 1 | Required |
""",
        encoding="utf-8",
    )
    parsed = ex.parse_chapter(path)[0]
    contract = yaml.safe_load(ex.render_draft(parsed))
    contract.pop("draft")
    endpoint_dir = tmp_path / "endpoints"
    endpoint_dir.mkdir()
    (endpoint_dir / "db-variant-check.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
    monkeypatch.setattr(ex, "ENDPOINT_DIR", endpoint_dir)

    assert ex.run_check([parsed]) == 0
    contract["variants"][0]["fields"][0]["documentedDefault"] = 0
    (endpoint_dir / "db-variant-check.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert ex.run_check([parsed]) == 1


def test_draft_never_answers_safe_to_omit_from_the_manual(section: ex.Section):
    """The manual's "Optional" must never become a claim about the product.

    Without live evidence every field stays `unverified`, including the four the
    synthetic chapter marks Optional.
    """
    draft = yaml.safe_load(ex.render_draft(section))

    def walk(fields):
        for field in fields:
            assert field["safeToOmit"] == "unverified", field["key"]
            assert "omissionEvidence" not in field
            walk(field.get("properties", []))

    walk(draft["fields"])
    assert draft["verification"]["status"] == "manual_only"
    assert all(f["provenance"] == "manual" for f in draft["fields"])


def test_draft_answers_safe_to_omit_only_from_a_confirmed_live_payload(section: ex.Section):
    evidence = ex.LiveOmission(
        case="Synthetic",
        endpoint="/db/SYNTH",
        sent=frozenset({"NAME", "ITEMS"}),
        products="gen and civil",
    )
    fields = {f["key"]: f for f in yaml.safe_load(ex.render_draft(section, evidence))["fields"]}

    # Sent in the payload that passed: nothing was learned about omitting them.
    assert fields["NAME"]["safeToOmit"] == "unverified"
    assert fields["ITEMS"]["safeToOmit"] == "unverified"

    # Absent from a payload a product accepted: that is evidence, and it is cited.
    assert fields["bFLAG"]["safeToOmit"] is True
    assert "Synthetic" in fields["bFLAG"]["omissionEvidence"]
    assert "not that the resulting model" in fields["bFLAG"]["omissionEvidence"]


def test_a_case_that_sends_no_create_payload_is_not_omission_evidence():
    """An empty create payload is a skipped request, not an accepted one.

    `live_crud_check.py` writes `{}` for records the product creates itself -
    UNIT, STYP, STYP-M1 and the four CO_* colour defaults, all GET/PUT-only.
    Its POST leg never runs there. Reading that as "the product accepted every
    field's absence" turned a request nobody made into blanket proof: it marked
    31 fields across four promoted contracts safeToOmit on no evidence at all.
    That is the /db/NMAS shape exactly - the field the manual calls Optional
    and the server dies without.
    """
    evidence = ex.live_omission_evidence()

    assert evidence, "the checker should still yield evidence for ordinary cases"
    for endpoint, omission in evidence.items():
        assert omission.sent, f"{endpoint} claims evidence from an empty payload"


def test_an_empty_live_payload_proves_nothing_about_omission(section: ex.Section):
    """Belt and braces: even handed one directly, a draft must not believe it."""
    evidence = ex.LiveOmission(
        case="Singleton", endpoint="/db/SYNTH", sent=frozenset(), products="civil"
    )
    fields = {f["key"]: f for f in yaml.safe_load(ex.render_draft(section, evidence))["fields"]}

    for key, field in fields.items():
        assert field["safeToOmit"] == "unverified", key


def test_nested_fields_are_never_given_live_evidence(section: ex.Section):
    """A top-level payload key says nothing about members inside it."""
    evidence = ex.LiveOmission(
        case="Synthetic", endpoint="/db/SYNTH", sent=frozenset({"NAME"}), products="gen"
    )
    fields = {f["key"]: f for f in yaml.safe_load(ex.render_draft(section, evidence))["fields"]}

    for child in fields["ITEMS"]["properties"]:
        assert child["safeToOmit"] == "unverified", child["key"]


def test_draft_is_valid_yaml_but_cannot_validate_as_a_contract(section: ex.Section):
    """A draft must be unusable until read, and unusable for one obvious reason."""
    jsonschema = pytest.importorskip("jsonschema")
    import json

    schema = json.loads(
        (ROOT / "contracts" / "schema" / "endpoint-contract.schema.json").read_text(encoding="utf-8")
    )
    draft = yaml.safe_load(ex.render_draft(section))
    assert draft["draft"] is True

    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(draft))
    assert errors, "a draft must not validate; review is what promotes it"
    # `draft` is the deliberate gate. This synthetic table also carries an
    # intentionally ambiguous multi-key row, which is now independently
    # rejected by the wire-key schema rather than being allowed into a contract.
    assert ("draft",) in {tuple(e.path) for e in errors}, [
        (list(e.path), e.message) for e in errors
    ]


def test_claiming_safe_to_omit_requires_evidence():
    """`safeToOmit: true` without omissionEvidence is exactly the mistake to block."""
    jsonschema = pytest.importorskip("jsonschema")
    import json

    schema = json.loads(
        (ROOT / "contracts" / "schema" / "endpoint-contract.schema.json").read_text(encoding="utf-8")
    )
    field = {
        "key": "X",
        "type": "number",
        "requirement": "optional",
        "documentedOptional": True,
        "safeToOmit": True,
        "provenance": "manual",
    }
    validator = jsonschema.Draft202012Validator(schema["$defs"]["field"])

    assert [e.message for e in validator.iter_errors(field)] == [
        "'omissionEvidence' is a required property"
    ]

    field["omissionEvidence"] = "live_crud_check.py's Node case omitted it and passed"
    assert not list(validator.iter_errors(field))


def test_field_names_that_yaml_would_mangle_are_quoted(section: ex.Section):
    """`NO` is a real MIDAS field name and a YAML 1.1 boolean."""
    draft = yaml.safe_load(ex.render_draft(section))

    assert draft["fields"][0]["key"] == "NO"


def test_check_reports_drift_between_a_contract_and_the_manual(section: ex.Section):
    manual = ex._flatten_manual(section.tables[0].fields)

    assert manual["ITEMS.ITEM_NAME"].requirement == "required"
    assert set(manual) >= {"NAME", "ITEMS", "ITEMS.ITEM_NAME", "CFG.MODE"}


def test_manual_enum_comparison_uses_array_item_values_when_applicable(tmp_path: Path):
    """A field enum and an array-item enum are intentionally different slots."""
    path = tmp_path / "99_DB_ArrayEnum.md"
    path.write_text(
        """# 99 DB — Array enum

## 1. `/db/ARRAY-ENUM` — Array enum

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Modes | `"MODES"` | Array [String (enum)] | - | Required |

**`MODES` values (enum):**

| Value | Description |
|-------|-------------|
| `"A"` | A |
| `"B"` | B |
""",
        encoding="utf-8",
    )
    field = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert field.type == "array"
    assert field.enum == ["A", "B"]
    assert yaml.safe_load(ex.render_draft(ex.parse_chapter(path)[0]))["fields"][0]["items"]["enum"] == [
        "A",
        "B",
    ]


METHOD_DECLARATION_FORMS = {
    "colon inside the bold": "- **Methods**: `POST`, `GET`",
    "colon outside the bold": "**Active Methods:** `POST, GET`",
    "middle-dot separator": "**Methods:** `POST` · `GET`",
    "two-column table row": "| **Method** | `POST`, `GET` |",
    "heading, verbs below": "### Active Methods\n\n`POST` · `GET`",
    "heading, verbs in a table": (
        "### HTTP Methods\n\n"
        "| Method | URL | 설명 |\n"
        "|--------|-----|------|\n"
        "| POST | `{base_url}/db/SYNTH` | create |\n"
        "| GET | `{base_url}/db/SYNTH` | read |"
    ),
    "numbered local HTTP heading, verbs in a table": (
        "### 1-1. HTTP 메서드 및 URL\n\n"
        "| 메서드 | URL | 설명 |\n"
        "|--------|-----|------|\n"
        "| POST | `{base_url}/db/SYNTH` | create |\n"
        "| GET | `{base_url}/db/SYNTH` | read |"
    ),
}


@pytest.mark.parametrize("form", sorted(METHOD_DECLARATION_FORMS))
def test_every_declaration_form_the_chapters_use_is_read(form: str, tmp_path: Path):
    """The chapters state their verbs six ways, and a missed form is not cosmetic.

    A section whose verbs go unread falls back to the /db/* default of all four -
    which is how /db/GRUP's first draft claimed a DELETE the endpoint does not
    serve - or, once that fallback became a refusal, blocks promotion outright.
    Reading only the narrowest form made 276 of 386 sections look like the manual
    never stated its methods; the real number is 26.
    """
    path = tmp_path / "99_DB_Forms.md"
    path.write_text(
        "# 99 DB — Forms\n\n## 1. `/db/SYNTH` — Synthetic\n\n"
        + METHOD_DECLARATION_FORMS[form]
        + "\n",
        encoding="utf-8",
    )
    assert ex.parse_chapter(path)[0].methods == ["GET", "POST"]


def test_a_section_that_states_no_methods_stays_empty(tmp_path: Path):
    """The fallback belongs to the caller, so silence must stay legible here."""
    path = tmp_path / "99_DB_Silent.md"
    path.write_text("# 99 DB — Silent\n\n## 1. `/db/SYNTH` — Synthetic\n\nNo verbs anywhere.\n", encoding="utf-8")
    assert ex.parse_chapter(path)[0].methods == []


def test_a_comparison_table_is_not_a_method_declaration(tmp_path: Path):
    """A chapter's trailing summary lands inside the last endpoint's section.

    Only a heading that names an endpoint starts a new section, so a closing
    "비교 요약" belongs to whichever endpoint came last. 14_DB_Pushover.md ends
    with exactly this three-column comparison, and reading its first value
    column handed /db/POLC-M1 the *general* endpoint's POST - a verb that same
    chapter twice says Hyper-S does not serve.
    """
    path = tmp_path / "99_DB_Compare.md"
    path.write_text(
        """# 99 DB — Compare

## 1. `/db/SYNTH-M1` — Synthetic Hyper-S

### Active Methods

`GET` · `PUT` · `DELETE`

---

## SYNTH vs SYNTH-M1 비교 요약

| 항목 | 일반(General) | Hyper-S(-M1) |
|------|:---:|:---:|
| Active Methods | POST, GET, PUT, DELETE | GET, PUT, DELETE (POST 미지원) |
""",
        encoding="utf-8",
    )
    assert ex.parse_chapter(path)[0].methods == ["DELETE", "GET", "PUT"]


def test_a_normalisation_callout_does_not_restore_the_verb_it_rejects(tmp_path: Path):
    """The manual repo overrules the official docs in `> ⚠️` callouts.

    Such a callout quotes the form it is rejecting in order to reject it, so a
    scan that sweeps verbs out of one reinstates exactly the value the callout
    exists to overrule.
    """
    path = tmp_path / "99_DB_Callout.md"
    path.write_text(
        """# 99 DB — Callout

## 1. `/db/SYNTH-M1` — Synthetic Hyper-S

### Active Methods

`GET` · `PUT` · `DELETE`

> ⚠️ 원문 아티클의 Active Methods 표는 `POST, GET, PUT, DELETE`로 표기돼 있으나,
> 이 챕터는 POST 미지원을 전제한다. 실기 확인 전까지 `GET`/`PUT`/`DELETE`로 유지한다.

### JSON Schema
""",
        encoding="utf-8",
    )
    assert ex.parse_chapter(path)[0].methods == ["DELETE", "GET", "PUT"]


def test_manual_check_compares_declared_methods(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A contract serving a verb the chapter never states is drift.

    Nothing compared the two before, which is how /db/POLC-M1's misread POST
    survived promotion into the contract and from there into both SDKs.
    """
    path = tmp_path / "99_DB_MethodCheck.md"
    path.write_text(
        """# 99 DB — Method check

## 1. `/db/METHOD-CHECK` — Declared methods

- **Methods**: `GET`, `PUT`

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Name | `"NAME"` | String | - | Required |
""",
        encoding="utf-8",
    )
    parsed = ex.parse_chapter(path)[0]
    contract = yaml.safe_load(ex.render_draft(parsed))
    contract.pop("draft")
    endpoint_dir = tmp_path / "endpoints"
    endpoint_dir.mkdir()
    target = endpoint_dir / "db-method-check.yaml"
    target.write_text(yaml.safe_dump(contract), encoding="utf-8")
    monkeypatch.setattr(ex, "ENDPOINT_DIR", endpoint_dir)

    assert ex.run_check([parsed]) == 0

    contract["operations"].append({"method": "POST", "risk": "write"})
    target.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert ex.run_check([parsed]) == 1

    # A verb the manual denies but a live call proved is a recorded defect, not
    # a silent match - the same escape hatch the field checks already use.
    contract["manualDefects"] = [
        {
            "describes": "method",
            "manualSays": "GET, PUT",
            "actual": "POST is served",
            "evidence": "docs/live_verification_notes.md",
        }
    ]
    target.write_text(yaml.safe_dump(contract), encoding="utf-8")
    assert ex.run_check([parsed]) == 0


def test_a_translated_heading_yields_the_english_label(tmp_path: Path):
    """Chapters 24-27 label sections `English (한글)`; the rest are English.

    Both halves are the manual's, but the label ships as the resource name in
    both packages and `INDEX.md` gives one English name per endpoint, so the
    draft takes the English. A parenthetical with no Hangul is part of the
    label, not a translation of it.
    """
    path = tmp_path / "99_DB_Labels.md"
    path.write_text(
        """# 99 DB — Labels

## 1. `/db/TRANS` — Definition of Frame (프레임 정의)

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Name | `"NAME"` | String | - | Required |

## 2. `/db/PLAIN` — Rebar Input for Checking (Beam/Column)

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Name | `"NAME"` | String | - | Required |
""",
        encoding="utf-8",
    )
    first, second = ex.parse_chapter(path)
    assert yaml.safe_load(ex.render_draft(first))["name"] == "Definition of Frame"
    assert yaml.safe_load(ex.render_draft(second))["name"] == "Rebar Input for Checking (Beam/Column)"


def test_manual_check_compares_the_endpoint_label(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The label is a manual fact, and it ships as the package resource name.

    Nothing compared it: not this check, not validate_contracts.py, and the
    generator's shadow gate reaches only /db/*. So when chapters 24-27 labelled
    their sections in Korean, 113 contracts took a Korean name and /db/DCTL
    carried one into src/midas_nx/ with every gate green - each gate asked
    whether the surfaces agreed, and they did.
    """
    path = tmp_path / "99_DB_LabelCheck.md"
    path.write_text(
        """# 99 DB — Label check

## 1. `/db/LABEL-CHECK` — Definition of Frame (프레임 정의)

- **Methods**: `GET`, `PUT`

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Name | `"NAME"` | String | - | Required |
""",
        encoding="utf-8",
    )
    parsed = ex.parse_chapter(path)[0]
    contract = yaml.safe_load(ex.render_draft(parsed))
    contract.pop("draft")
    endpoint_dir = tmp_path / "endpoints"
    endpoint_dir.mkdir()
    target = endpoint_dir / "db-label-check.yaml"
    target.write_text(yaml.safe_dump(contract), encoding="utf-8")
    monkeypatch.setattr(ex, "ENDPOINT_DIR", endpoint_dir)

    assert ex.run_check([parsed]) == 0

    contract["name"] = "프레임 정의"
    target.write_text(yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8")
    assert ex.run_check([parsed]) == 1


def test_manual_check_compares_the_section_heading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A renumbered chapter leaves every contract below the insert pointing wrong.

    Inserting /db/STYP-M1 at chapter 02's #4 on 2026-08-30 moved eleven
    sections down one, and unifying chapters 24-27's labels rewrote 86 more
    headings. Nothing compared `source.manual.section` against the chapter, so
    103 contracts named a heading that no longer existed - the third blind spot
    of this shape, after the endpoint label and the method set.

    Dash spelling is exempt: 90 contracts write the manual's em dash as `--`,
    and the npm shadow gate already treats that as presentation.
    """
    path = tmp_path / "99_DB_Sections.md"
    path.write_text(
        """# 99 DB — Sections

## 7. `/db/SECTION-CHECK` — Section Check

- **Methods**: `GET`, `PUT`

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Name | `"NAME"` | String | - | Required |
""",
        encoding="utf-8",
    )
    parsed = ex.parse_chapter(path)[0]
    contract = yaml.safe_load(ex.render_draft(parsed))
    contract.pop("draft")
    endpoint_dir = tmp_path / "endpoints"
    endpoint_dir.mkdir()
    target = endpoint_dir / "db-section-check.yaml"
    target.write_text(yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8")
    monkeypatch.setattr(ex, "ENDPOINT_DIR", endpoint_dir)

    assert ex.run_check([parsed]) == 0

    # The same heading spelled with ASCII dashes stays acceptable.
    contract["source"]["manual"]["section"] = "7. `/db/SECTION-CHECK` -- Section Check"
    target.write_text(yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8")
    assert ex.run_check([parsed]) == 0

    # A stale section number does not.
    contract["source"]["manual"]["section"] = "6. `/db/SECTION-CHECK` — Section Check"
    target.write_text(yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8")
    assert ex.run_check([parsed]) == 1


def test_enum_values_are_read_only_when_the_same_manual_section_states_them(tmp_path: Path):
    """Cover the three enum forms used by the manual, including nested paths."""
    path = tmp_path / "99_DB_Enums.md"
    path.write_text(
        """# 99 DB — Enums

## 1. `/db/ENUM` — Enum forms

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Inline choices | `"INLINE"` | String (enum: `"AUTO"`/`"MANUAL"`) | - | Required |
| 2 | Description choices (`"LEFT"` / `"RIGHT"`) | `"DESCRIBED"` | String (enum) | - | Required |
| 5 | Numeric choices (0=Zero / 1=One / 2=Two) | `"NUMBERED"` | Integer (enum) | - | Required |
| 6 | Symbolic choices (FIRST=First / SECOND=Second) | `"SYMBOLIC"` | String (enum) | - | Required |
| 7 | Reverse symbolic choices (Static: STATIC / Stage: STAGE) | `"REVERSE_SYMBOLIC"` | String (enum) | - | Required |
| 8 | Bare numeric choices (0/1/2) | `"BARE_NUMERIC"` | Integer (enum) | - | Required |
| 3 | Settings | `"SETTINGS"` | Object | - | Required |
| (1) | Table choices | `"KIND"` | String (enum) | - | Required |
| 4 | Item choices | `"ITEMS"` | Array [String (enum)] | - | Required |

**`SETTINGS.KIND` values (enum):**

| Value | Description |
|-------|-------------|
| `"FIRST"` | First |
| `"SECOND"` | Second |

**`ITEMS` values (enum):**

| Value | Description | Value | Description |
|-------|-------------|-------|-------------|
| `"ONE"` | One | `"TWO"` | Two |
""",
        encoding="utf-8",
    )

    parsed = ex.parse_chapter(path)[0]
    fields = {field.key: field for field in parsed.tables[0].fields}
    assert fields["INLINE"].enum == ["AUTO", "MANUAL"]
    assert fields["DESCRIBED"].enum == ["LEFT", "RIGHT"]
    assert fields["NUMBERED"].enum == [0, 1, 2]
    assert fields["SYMBOLIC"].enum == ["FIRST", "SECOND"]
    assert fields["REVERSE_SYMBOLIC"].enum == ["STATIC", "STAGE"]
    assert fields["BARE_NUMERIC"].enum == [0, 1, 2]
    assert fields["SETTINGS"].properties[0].enum == ["FIRST", "SECOND"]
    assert fields["ITEMS"].enum == ["ONE", "TWO"]
    assert not any("values are listed elsewhere" in note for field in ex._walk(parsed.tables[0].fields) for note in field.notes)

    draft = yaml.safe_load(ex.render_draft(parsed))
    draft_fields = {field["key"]: field for field in draft["fields"]}
    assert draft_fields["INLINE"]["enum"] == ["AUTO", "MANUAL"]
    assert draft_fields["SETTINGS"]["properties"][0]["enum"] == ["FIRST", "SECOND"]
    assert draft_fields["ITEMS"]["items"]["enum"] == ["ONE", "TWO"]


def test_markdown_numeric_enum_values_do_not_turn_ranges_or_ellipses_into_enums():
    """Code-spanned alternatives are exact values; abbreviated ranges are not."""
    assert ex._enum_values_from_description("Diagram type: Stress `0` / Force `1`") == [0, 1]
    assert ex._enum_values_from_description("Allowed range `0` ~ `20`") == []
    assert ex._enum_values_from_description("1=Method-1 … 4=Method-4") == []


def test_same_section_json_schema_fills_only_exact_table_enum_and_array_gaps(tmp_path: Path):
    path = tmp_path / "99_DB_SchemaHints.md"
    path.write_text(
        """## 1. `/db/HINTS` — Schema hints

### JSON Schema

```json
{"type":"object","properties":{"Assign":{"type":"object","required":["MODE","VECTOR"],"properties":{"MODE":{"type":"string","enum":["FIRST","SECOND"]},"VECTOR":{"type":"array","minItems":3,"maxItems":3,"items":{"type":"number"}},"OPTIONAL_NOTE":{"type":"string"}}}}}
```

| No. | Description | Key | Value Type | Default | Required |
|-----|-------------|-----|------------|---------|----------|
| 1 | Mode | `"MODE"` | String (enum) | - | Required |
| 2 | Vector | `"VECTOR"` | Array | - | Required |
| 3 | Optional note | `"OPTIONAL_NOTE"` | String | - | |
""",
        encoding="utf-8",
    )

    fields = {field.key: field for field in ex.parse_chapter(path)[0].tables[0].fields}
    assert fields["MODE"].enum == ["FIRST", "SECOND"]
    assert not fields["MODE"].notes
    assert fields["VECTOR"].items == {"type": "number"}
    assert fields["VECTOR"].constraints == {"minItems": 3, "maxItems": 3}
    assert not fields["VECTOR"].notes
    assert fields["OPTIONAL_NOTE"].requirement == "optional"
    assert not fields["OPTIONAL_NOTE"].notes


def test_same_section_json_schema_supplies_a_missing_default_column_only(tmp_path: Path):
    path = tmp_path / "99_DB_SchemaDefault.md"
    path.write_text(
        """## 1. `/db/DEFAULT` — Schema default

### JSON Schema

```json
{"type":"object","properties":{"Assign":{"type":"object","properties":{"COUNT":{"type":"integer","default":0}}}}}
```

| No. | Description | Key | Value Type | Required |
|-----|-------------|-----|------------|----------|
| 1 | Count | `"COUNT"` | Integer | Optional |
""",
        encoding="utf-8",
    )

    count = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert count.documented_default == 0
    assert not count.notes


def test_missing_default_column_is_recorded_once_in_extraction_not_per_field(tmp_path: Path):
    path = tmp_path / "99_DB_NoDefaultColumn.md"
    path.write_text(
        """## 1. `/db/NO-DEFAULT` -- no Default column

| No. | Description | Key | Value Type | Required |
|---|---|---|---|---|
| 1 | First | `FIRST` | String | Required |
| 2 | Second | `SECOND` | Number | Optional |
""",
        encoding="utf-8",
    )

    section = ex.parse_chapter(path)[0]
    assert all("the table has no Default column" not in field.notes for field in section.tables[0].fields)
    draft = yaml.safe_load(ex.render_draft(section))
    missing = draft["extraction"]["missingColumns"]
    assert len(missing) == 1
    assert missing[0]["columns"] == ["Default"]


@pytest.mark.parametrize(
    ("schema_form", "record_schema"),
    [
        pytest.param(
            "properties_record_wrapper",
            '{"properties":{"Assign":{"type":"object","properties":{"MODE":{"type":"string","enum":["FIRST","SECOND"]}}}}}',
            id="properties_record_wrapper",
        ),
        pytest.param(
            "numeric_pattern_properties_record_wrapper",
            '{"properties":{"Assign":{"type":"object","patternProperties":{"^[0-9]+$":{"type":"object","properties":{"MODE":{"type":"string","enum":["FIRST","SECOND"]}}}}}}}',
            id="numeric_pattern_properties_record_wrapper",
        ),
    ],
)
def test_same_section_schema_record_wrapper_forms_supply_enum_values(
    schema_form: str, record_schema: str, tmp_path: Path
):
    """Both documented record wrappers lead to the same manual field path."""
    path = tmp_path / f"99_DB_{schema_form}.md"
    path.write_text(
        "## 1. `/db/RECORD-WRAPPER` -- Record wrapper\n\n"
        "### JSON Schema\n\n```json\n"
        + record_schema
        + "\n```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Mode | `MODE` | String (enum) | - | Required |\n",
        encoding="utf-8",
    )

    mode = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert mode.enum == ["FIRST", "SECOND"]
    assert not mode.notes


def test_same_section_schema_additional_properties_record_map_supplies_array_item_type(tmp_path: Path):
    """An ID-keyed map's value schema retains its child field path exactly."""
    path = tmp_path / "99_DB_AdditionalPropertiesMap.md"
    path.write_text(
        "## 1. `/db/RECORD-MAP` -- Record map\n\n"
        "### JSON Schema\n\n```json\n"
        '{"type":"object","properties":{"Assign":{"type":"object","additionalProperties":{"type":"object","properties":{"SELECTED_MEMBERS":{"type":"object","additionalProperties":{"type":"object","properties":{"ELEM_LIST":{"type":"array","items":{"type":"integer"}}}}}}}}}}\n'
        "```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Selected members | `SELECTED_MEMBERS` | Object | - | Required |\n"
        "| 1.1 | Element list | `ELEM_LIST` | Array | - | Required |\n",
        encoding="utf-8",
    )

    selected_members = ex.parse_chapter(path)[0].tables[0].fields[0]
    element_list = selected_members.properties[0]
    assert element_list.items == {"type": "integer"}
    assert not any("array element type not stated" in note for note in element_list.notes)


def test_same_section_schema_expands_compact_one_of_keys_and_rehomes_their_children(tmp_path: Path):
    """A compact selector row is safe only when its exact schema fills every path."""
    path = tmp_path / "99_DB_CompactOneOf.md"
    path.write_text(
        "## 1. `/db/COMPACT-ONE-OF` -- Compact selector\n\n"
        "### JSON Schema\n\n```json\n"
        '{"type":"object","properties":{"Argument":{"type":"object","oneOf":[{"required":["ELEMS"]},{"required":["SECTIONS"]}],"properties":{"ELEMS":{"type":"object","properties":{"KEYS":{"type":"array","items":{"type":"integer"}},"TO":{"type":"string"},"STRUCTURE_GROUP_NAME":{"type":"string"}}},"SECTIONS":{"type":"array","items":{"type":"integer"}}}}}}\n'
        "```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Argument wrapper | `Argument` | Object | - | Required |\n"
        "| 2 | Target | `ELEMS` / `SECTIONS` | Object / Array | - | Conditional |\n"
        "| 2.1 | Individual IDs / ID range / structure group | `KEYS` / `TO` / `STRUCTURE_GROUP_NAME` | Array[Int] / String / String | - | Optional |\n",
        encoding="utf-8",
    )

    fields = {field.key: field for field in ex.parse_chapter(path)[0].tables[0].fields}
    elems = fields["ELEMS"]
    sections = fields["SECTIONS"]
    assert [field.key for field in elems.properties] == ["KEYS", "TO", "STRUCTURE_GROUP_NAME"]
    assert elems.properties[0].items == {"type": "integer"}
    assert sections.items == {"type": "integer"}
    assert elems.condition == 'oneOf: exactly one of "ELEMS", "SECTIONS" is required'
    assert sections.condition == elems.condition
    assert not any(_note for field in ex._walk(list(fields.values())) for _note in field.notes if "single field name" in _note)


@pytest.mark.parametrize(
    ("value", "target"),
    [
        pytest.param("MEMB", "CURRENT_MODE_MEMB", id="first_code_spanned_branch"),
        pytest.param("PROP", "CURRENT_MODE_PROP", id="compact_second_code_spanned_branch"),
    ],
)
def test_manual_prose_compact_condition_pair_supplies_applies_when(
    value: str, target: str, tmp_path: Path
):
    """The explicit paired prose form is a condition source, unlike examples."""
    path = tmp_path / "99_DB_ProseConditions.md"
    path.write_text(
        "## 1. `/db/PROSE-CONDITIONS` -- Prose conditions\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Report type | `REPORT_TYPE` | String | - | Required |\n"
        "| 2 | Member mode | `CURRENT_MODE_MEMB` | String | - | Conditional |\n"
        "| 3 | Property mode | `CURRENT_MODE_PROP` | String | - | Conditional |\n\n"
        '> `REPORT_TYPE="MEMB"`이면 `CURRENT_MODE_MEMB`, `"PROP"`이면 `CURRENT_MODE_PROP`를 사용합니다.\n',
        encoding="utf-8",
    )

    fields = {field.key: field for field in ex.parse_chapter(path)[0].tables[0].fields}
    conditional = fields[target]
    assert conditional.condition == f'REPORT_TYPE="{value}"'
    assert conditional.applies_when == [("REPORT_TYPE", value)]
    assert not conditional.notes


@pytest.mark.parametrize(
    ("value", "target"),
    [
        pytest.param("WID+STORY", "CURRENT_MODE_WID_STORY", id="first_parallel_branch"),
        pytest.param("WID", "CURRENT_MODE_WID", id="second_parallel_branch"),
    ],
)
def test_manual_prose_parallel_code_span_conditions_supply_applies_when(
    value: str, target: str, tmp_path: Path
):
    """The Korean 'respectively' form maps only equal-length code-span pairs."""
    path = tmp_path / "99_DB_ParallelProseConditions.md"
    path.write_text(
        "## 1. `/db/PARALLEL-CONDITIONS` -- Parallel prose conditions\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Report type | `REPORT_TYPE` | String | - | Required |\n"
        "| 2 | Story mode | `CURRENT_MODE_WID_STORY` | String | - | Conditional |\n"
        "| 3 | Wall mode | `CURRENT_MODE_WID` | String | - | Conditional |\n\n"
        '> `REPORT_TYPE`으로 출력 단위(`"WID+STORY"`/`"WID"`)를 정하고 각각 `CURRENT_MODE_WID_STORY`/`CURRENT_MODE_WID`로 모드를 지정합니다.\n',
        encoding="utf-8",
    )

    fields = {field.key: field for field in ex.parse_chapter(path)[0].tables[0].fields}
    conditional = fields[target]
    assert conditional.condition == f'REPORT_TYPE="{value}"'
    assert conditional.applies_when == [("REPORT_TYPE", value)]
    assert not conditional.notes


@pytest.mark.parametrize(
    ("selector_schema", "expected_condition"),
    [
        pytest.param('{"const":true}', "OPT_USE=true", id="const_selector_then_required"),
        pytest.param('{"enum":["AUTO","USER"]}', 'MODE ∈ {"AUTO", "USER"}', id="enum_selector_then_required"),
    ],
)
def test_same_section_schema_conditional_required_forms_supply_exact_condition(
    selector_schema: str, expected_condition: str, tmp_path: Path
):
    """Only literal schema selectors resolve a table's otherwise blank condition."""
    path = tmp_path / "99_DB_ConditionalSchema.md"
    path.write_text(
        "## 1. `/db/CONDITIONAL-SCHEMA` -- Conditional schema\n\n"
        "### JSON Schema\n\n```json\n"
        '{"type":"object","properties":{"Assign":{"type":"object","properties":{"OPT_USE":{"type":"boolean"},"MODE":{"type":"string"},"DETAIL":{"type":"number"}},"allOf":[{"if":{"properties":{"'
        + ("OPT_USE" if "OPT_USE" in expected_condition else "MODE")
        + '":'
        + selector_schema
        + '},"required":["'
        + ("OPT_USE" if "OPT_USE" in expected_condition else "MODE")
        + '"]},"then":{"required":["DETAIL"]}}]}}}\n'
        "```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Selector | `OPT_USE` | Boolean | - | Optional |\n"
        "| 2 | Mode | `MODE` | String | - | Optional |\n"
        "| 3 | Detail | `DETAIL` | Number | - | Conditional Required |\n",
        encoding="utf-8",
    )

    detail = ex.parse_chapter(path)[0].tables[0].fields[2]
    assert detail.requirement == "conditional"
    assert detail.condition == expected_condition
    assert not detail.notes


def test_schema_conditional_marker_does_not_mask_same_field_enum(tmp_path: Path):
    """A ``then.required`` marker is relation metadata, not a second schema."""
    path = tmp_path / "99_DB_ConditionalEnumSchema.md"
    path.write_text(
        "## 1. `/db/CONDITIONAL-ENUM` -- Conditional enum\n\n"
        "### JSON Schema\n\n```json\n"
        '{"type":"object","properties":{"Assign":{"type":"object","properties":{"MODE":{"type":"string","enum":["AUTO","USER"]},"DETAIL":{"type":"string","enum":["FIRST","SECOND"]}},"allOf":[{"if":{"properties":{"MODE":{"const":"USER"}},"required":["MODE"]},"then":{"required":["DETAIL"]}}]}}}\n'
        "```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Mode | `MODE` | String (enum) | - | Optional |\n"
        "| 2 | Detail | `DETAIL` | String (enum) | - | Conditional Required |\n",
        encoding="utf-8",
    )

    detail = ex.parse_chapter(path)[0].tables[0].fields[1]
    assert detail.enum == ["FIRST", "SECOND"]
    assert detail.condition == 'MODE="USER"'
    assert detail.applies_when == [("MODE", "USER")]
    assert not detail.notes


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        pytest.param("Use a range (INPUT_METHOD=KEYS)", ("INPUT_METHOD", "KEYS"), id="bare_uppercase_value"),
        pytest.param("Material strength (CODE=None)", ("CODE", "None"), id="bare_titlecase_value"),
        pytest.param("Two choices (MODE=A, CODE=None)", None, id="multiple_equalities_stay_unverified"),
    ],
)
def test_description_literal_condition_accepts_only_one_explicit_equality(
    description: str, expected: tuple[str, str] | None
):
    assert ex._description_literal_condition(description) == expected


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        pytest.param("Target (same structure as SOURCE)", "SOURCE", id="english_same_structure"),
        pytest.param("Target (구조는 Part A와 동일)", "PART_A", id="korean_same_structure"),
        pytest.param("Target object", None, id="no_explicit_inheritance"),
    ],
)
def test_same_object_shape_reference_requires_an_explicit_manual_statement(
    description: str, expected: str | None
):
    assert ex._same_object_shape_reference(description) == expected


def test_explicit_same_object_structure_clones_only_parsed_sibling_children(tmp_path: Path):
    path = tmp_path / "99_DB_SameStructure.md"
    path.write_text(
        "## 1. `/db/SAME-STRUCTURE` -- Same object structure\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | Source object | `SOURCE` | Object | - | Required |\n"
        "| 1.1 | Input method | `INPUT_METHOD` | String | - | Required |\n"
        "| 1.2 | Source child (INPUT_METHOD=KEYS) | `CHILD` | String | - | Conditional Required |\n"
        "| 2 | Target (same structure as SOURCE) | `TARGET` | Object | - | Required |\n",
        encoding="utf-8",
    )

    fields, _ = ex._structural_fields(ex.parse_chapter(path)[0])
    target = next(field for field in fields if field.key == "TARGET")
    assert [field.key for field in target.properties] == ["INPUT_METHOD", "CHILD"]
    assert not target.properties[1].notes

    draft = yaml.safe_load(ex.render_draft(ex.parse_chapter(path)[0]))
    target_draft = next(field for field in draft["fields"] if field["key"] == "TARGET")
    child = target_draft["properties"][1]
    assert child["appliesWhen"] == [{"path": "TARGET.INPUT_METHOD", "equals": "KEYS"}]


def test_repeated_child_key_is_retained_under_each_numbered_parent(tmp_path: Path):
    path = tmp_path / "99_DB_RepeatedChild.md"
    path.write_text(
        "## 1. `/db/REPEATED-CHILD` -- Repeated child key\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        "| 1 | First object | `FIRST` | Object | - | Required |\n"
        "| 1.1 | First code | `CODE` | String | - | Required |\n"
        "| 2 | Second object | `SECOND` | Object | - | Required |\n"
        "| 2.1 | Second code | `CODE` | String | - | Required |\n",
        encoding="utf-8",
    )

    fields = ex.parse_chapter(path)[0].tables[0].fields
    assert [field.key for field in fields[0].properties] == ["CODE"]
    assert [field.key for field in fields[1].properties] == ["CODE"]


@pytest.mark.parametrize(
    ("table_default", "schema_default", "has_note"),
    [
        pytest.param("AUTO", '"AUTO"', False, id="matching_schema_string_confirms_bare_default"),
        pytest.param("AUTO", '"MANUAL"', True, id="different_schema_default_stays_unverified"),
    ],
)
def test_schema_default_confirms_only_the_same_bare_table_default(
    table_default: str, schema_default: str, has_note: bool, tmp_path: Path
):
    path = tmp_path / "99_DB_BareDefault.md"
    path.write_text(
        "## 1. `/db/BARE-DEFAULT` -- Bare default\n\n"
        "### JSON Schema\n\n```json\n"
        '{"type":"object","properties":{"Assign":{"type":"object","properties":{"MODE":{"type":"string","default":'
        + schema_default
        + "}}}}}\n```\n\n"
        "| No. | Description | Key | Value Type | Default | Required |\n"
        "|-----|-------------|-----|------------|---------|----------|\n"
        f"| 1 | Mode | `MODE` | String | {table_default} | Optional |\n",
        encoding="utf-8",
    )

    mode = ex.parse_chapter(path)[0].tables[0].fields[0]
    assert mode.documented_default == table_default
    assert any(note.startswith("non-literal default ") for note in mode.notes) is has_note


def test_shipped_contracts_still_match_the_manual_if_it_is_present():
    """Runs only where the sibling manual repo is checked out - CI does both."""
    manual_repo = ex.DEFAULT_MANUAL_REPO
    if not (manual_repo / "docs" / "manual").is_dir():
        pytest.skip("manual repo not available")

    assert ex.run_check(ex.load_manual(manual_repo)[0]) == 0
