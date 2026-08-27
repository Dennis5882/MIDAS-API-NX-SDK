"""Guards for the manual-to-contract extractor.

These run against synthetic chapter text rather than the sibling manual repo, so
the suite still passes with no live server and no second checkout. The one thing
they will not let slide is the extractor inventing certainty: a draft that fills
in `safeToOmit` from a manual that says "Optional" would turn the documentation
into evidence, and the CI gate built on the difference between those two would
stop meaning anything.
"""

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


def test_requiredness_and_defaults_come_from_the_table(section: ex.Section):
    fields = {f.key: f for f in section.tables[0].fields}

    assert fields["NO"].requirement == "read_only"
    assert fields["NAME"].requirement == "required"
    assert fields["NAME"].documented_default is None
    assert fields["bFLAG"].requirement == "optional"
    assert fields["bFLAG"].documented_default is False
    assert fields["COUNT"].documented_default == 0


def test_inline_conditions_are_kept_verbatim(section: ex.Section):
    span = {f.key: f for f in section.tables[0].fields}["SPAN"]

    assert span.requirement == "conditional"
    assert span.condition == "bEXACTSPAN=true"


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


def test_conditional_variant_tables_are_reported_not_merged(section: ex.Section):
    assert len(section.tables) == 2
    main_keys = {f.key for f in section.tables[0].fields}

    assert "SPECIAL" not in main_keys
    assert section.tables[1].heading == "TYPE=SPECIAL 전용"


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
    assert {tuple(e.path) for e in errors} == {("draft",)}, [
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


def test_shipped_contracts_still_match_the_manual_if_it_is_present():
    """Runs only where the sibling manual repo is checked out - CI does both."""
    manual_repo = ex.DEFAULT_MANUAL_REPO
    if not (manual_repo / "docs" / "manual").is_dir():
        pytest.skip("manual repo not available")

    assert ex.run_check(ex.load_manual(manual_repo)[0]) == 0
