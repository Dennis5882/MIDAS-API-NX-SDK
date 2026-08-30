# Codex task prompt — contract migration, decision-free batch

Written 2026-08-30 at `3c97abf`, immediately after the 2.7.1 release. Paste the
section below into Codex. Everything in it is work that needs **no decision from
the author**; the items that do need one are named at the end so they are not
started by accident.

---

You are working in `E:\AI Study\MIDAS-API-NX-SDK` on branch `main` — the
`midas-nx` SDKs, published on PyPI and npm at 2.7.1. Read `CLAUDE.md`,
`contracts/README.md`, and `docs/contract_migration_brief.md` first. Where this
prompt and those disagree, they win.

## Hard rules

1. **Neither SDK is a source for the other, and neither is a source for a
   contract.** The only permitted contract sources are the manual repo
   (`E:\AI Study\MIDAS-API`, `docs/manual/*.md`),
   `docs/live_verification_notes.md`, and live `/info/{endpoint}` introspection.
2. **Do not guess.** `unverified` is a correct answer; an invented one is not.
   A field the manual does not describe does not go into a contract.
3. **`documentedOptional` (a claim about the docs) and `safeToOmit` (a claim
   about the product) are separate booleans.** "The manual says Optional" is
   never evidence for `safeToOmit: true`. `/db/NMAS` is the endpoint where
   believing the manual ends a live NX session.
4. **A parity failure is an SDK defect, never a reason to edit a contract.**
5. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   A draft is extractor output. If a draft is wrong, fix the extractor.
6. **Measure, do not assume.** Every number in the working docs carries a date
   because several of them went stale and were repeated back as current. Re-run
   the command before quoting a figure, and say what you measured.
7. **Do not release.** Versions are lockstep across both registries and the
   author picks the number. Expect to commit without releasing; `scripts/` and
   `docs/` ship in neither package.
8. **No live product calls in this batch.** Gen NX and Civil NX are not part of
   this work. Every task below is decidable from the manual.

## Task 1 — `/db/STYP-M1`: fix the child numbering and promote it

The last npm resource with no contract *and* no draft. Blocked by one extractor
gap.

The manual numbers `MASS_CONTROL`'s members `2-(1)` … `2-(4)`
(`02_DB_Project_Structure.md`). `_NUMBER_CHILD` matches a bare `(1)` and
`_NUMBER_PATH` matches `4-1`; neither matches the `N-(M)` hybrid, so the four
members render as root fields beside their own parent — the `/db/RIGD`
flattening defect. `GET /info/db/STYP-M1` confirms the server nests them.

**Two edits are needed, not one.** Widening the regex alone measures as a no-op:

1. `_NUMBER_PATH` must match `2-(1)`.
2. `depth = len(re.findall(r"[-.]\d+", entry.number))` must count a
   parenthesised segment. `re.findall(r"[-.]\d+", "2-(1)")` returns `[]`
   because `(` follows the dash, so a matching number still yields depth 0 and
   the row stays at the root.

Then fix three defects visible in the resulting draft:

- `MASS_POS`'s `enum` is `[LUMPED]`, taken from its own condition instead of
  its value list `[CENTROID, OFFSET]`.
- `MASS_AXIS`'s `enum` is `[CONSISTENT]` instead of `[XYZ, XY, Z]`.
- `SELFWEIGHT`'s `appliesWhen` renders `equals: "true"` as a string on a
  boolean field.

**Expected blast radius, already measured:** re-rendering all 387 manual
sections with both numbering edits changes **exactly one** — this one — and no
promoted contract at all. If your run changes more, stop and report it rather
than accepting it; that is new information, not a green light.

Add a test in `tests/test_extract_contracts.py` covering the `N-(M)` form and
the depth count, following the section-heading test's shape.

The endpoint's methods are settled and are **GET and PUT only**. The official
article tags `DELETE`; the server refuses all three DELETE forms on both
products, measured live 2026-08-30 with a real model open from a non-default
state. Record the article's claim under `manualDefects` with
`describes: method`; do not widen `METHODS`.

Afterwards, `docs/coverage.json`'s `vendored_at_commit` may be raised past
`5c92efe`. Do that only once this contract is promoted, then confirm
`python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"`
reports `has_diff: false`.

## Task 2 — widen the TypeScript generator's shadow gate past `/db/*`

`scripts/generate_typescript_sdk.py:395` and `:530` both filter contracts to
`endpoint.startswith("/db/")`. That filter existed because the `/DESIGN/*`
contracts carried Korean labels while both SDKs used English ones. **That
question is settled — the labels are English**, applied in `5b92881`, and zero
promoted contracts carry a Korean label today. The filter is now just 63
unchecked contracts.

Widen it to `/DESIGN/*` and run `npm run generate`. Every gate widened on
2026-08-30 found real drift on its first run — 114 stale labels, one wrong
method set, 103 stale section strings — so expect this one to find something.
A disagreement between a contract and an SDK is an **SDK defect**; fix the SDK,
never the contract. If a disagreement looks like a contract defect instead,
stop and report it with the manual line that decides it.

## Task 3 — make the variant population measurable

Do **not** design variant schema. This task is only about being able to see
what is there.

**3a. Teach the extractor to read bold table labels.** It records the nearest
`#` heading for each supplementary table. The chapters label them two ways:

```text
### 8-2. 파라미터                             <- what is recorded today
| No. | ... |

**Time Function (FUNCTYPE=1) 추가 파라미터**    <- the selector lives here
| No. | ... |
**Sinusoidal (FUNCTYPE=2) 추가 파라미터**
| No. | ... |
```

A bold label is not a markdown heading, so a bold-labelled variant table
inherits its section title and is filed as "selector not explicit" while the
manual states the selector plainly. `/db/CCFC` (`TYPE="CONST"` / `"USER"`) and
`/db/THFC` (`FUNCTYPE=1` / `=2`) are that case. Also stop filing prose as a
label — `없어 확정된 것은 아니다.` and `아래와 동일한 하위 구조를 가짐:` are
currently recorded as variant headings.

**3b. Fix the `9 explicitly modelled / 59 unmerged` counter.** It cannot
measure 3a. `explicit_variants` counts sections whose table *headings* declare a
selector; the hand-curated `_conditional_fields` map (eight endpoints) is
invisible to it, and a section merged by hand still counts among the 59.

**3c. Re-measure and write the result into
`docs/contract_migration_brief.md`**, replacing the two scratch figures it
currently refuses to quote (40 and 63 of 176). Report, per unmerged table,
whether the manual states a selector field, one value, or several. That report
is the deliverable — it is what the author's pending decision will be made on.

## Task 4 — the eight mechanically-promotable drafts

`db-sdhy`, `db-sdis`, `db-sdst`, `db-sdve`, `db-sdvi`, `db-mvctch`, `db-nllp`,
`db-wvld` are refused **only** for `# NOTE: the table has no Default column`.

That note records a structural fact — the manual's table has no Default column
at all — and the schema already has the exact word for it:
`documentedDefault: null` is documented as "the manual gives none". So the note
is complete information filed as an unresolved question.

There is already a precedent for clearing it in `extract_contracts.py`: when a
section's JSON Schema supplies a `default`, the note is removed and the value
recorded. Do the same for the whole-table case — verify the absence from the
table's header row, record it once under `extraction`, and stop emitting a
per-field review note. Fix it in the extractor, never in the drafts.

Then `python scripts/promote_contract.py --all --dry-run` and promote those
eight. Review each promoted contract against its manual section before
committing; a bulk promotion that nobody read is how a wrong contract reaches
`contracts/endpoints/`.

## What NOT to start

These are the author's calls and are explicitly out of scope:

- **Conditional variant schema.** The proposal — give `variant.when` the shape
  field-level `appliesWhen` already has, an ANDed array of `{path, equals}`,
  and add `in` to both — is written up in `docs/contract_migration_brief.md`.
  Task 3 produces the measurement it will be decided on. Do not implement it.
- **Recording requiredness as "unstated".** Four further drafts (`db-actl-m1`,
  `db-mcon`, `view-active`, `view-select`) are blocked by a missing Required or
  Value Type column, and `requirement`/`documentedOptional` have no value for
  "the manual does not say". Inventing `optional` for a blank column is exactly
  the `documentedOptional`/`safeToOmit` conflation the schema exists to
  prevent. Leave them.
- **Stage 4 (Python generated from contracts).** Deliberately last and
  deliberately unspecified. `src/midas_nx/` is hand-written and its public API
  is on PyPI.
- **Any release.**

## Before every commit

```bash
pip install -e ".[dev]"
pytest && ruff check src tests scripts && mypy
python scripts/validate_contracts.py
python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --check
cd packages/typescript && npm run generate && npm run typecheck && npm test
git status --short      # generation drift must be empty
```

CI runs all of it on Python 3.12/3.13 and Node 18/22 and fails on generated-file
drift. Commit messages: imperative subject, body explaining *why*; match
`git log`. One task per commit.
