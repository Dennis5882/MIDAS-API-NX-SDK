# Codex task prompt — post-2026-08-31 batch

Rewritten 2026-08-31 at `54a6050`. The previous edition's four tasks are done or
correctly refused; see "What the last batch settled" at the end. Paste the
section below into Codex.

The contract-shape queue is genuinely blocked on four author decisions, listed
at the bottom. This batch is the work that does not touch them.

---

You are working in `E:\AI Study\MIDAS-API-NX-SDK` on branch `main` — the
`midas-nx` SDKs, published on PyPI and npm at 2.7.1. Read `CLAUDE.md`,
`contracts/README.md`, and `docs/contract_migration_brief.md` first. Where this
prompt and those disagree, they win.

## Hard rules

1. **Neither SDK is a source for the other, and neither is a source for a
   contract.** Permitted contract sources are exactly three: the manual repo
   (`E:\AI Study\MIDAS-API`, `docs/manual/*.md`),
   `docs/live_verification_notes.md`, and live `/info/{endpoint}` introspection.
2. **Do not guess.** `unverified` is a correct answer; an invented one is not.
3. **`documentedOptional` (a claim about the docs) and `safeToOmit` (a claim
   about the product) are separate booleans.** `/db/NMAS` is the endpoint where
   believing the manual ends a live NX session.
4. **Where the manual and the product disagree, record both separately** — the
   manual's claim under `manualDefects`, the product's behaviour under
   `contracts/verification/`. Never collapse them.
5. **A parity failure is an SDK defect, never a reason to edit a contract.**
6. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   Drafts are git-ignored build output; if a draft is wrong, fix the extractor.
7. **`ROADMAP.md` is generated from `docs/coverage.json`.** Any commit that
   touches coverage reruns `python scripts/gen_roadmap.py` in the same commit.
   The 08-31 pass missed this and shipped stale counts.
8. **Do not release.** The author picks the version; both registries move
   together. `scripts/` and `docs/` ship in neither package.

## Live-session rules — read before any product call

The author's Gen NX and Civil NX sessions are reachable and the last pass used
them correctly. Keep it that way.

- **Ask the author before the first product call of a session**, and confirm
  both documents are empty. Verify it yourself with `GET /db/NODE` and
  `GET /db/ELEM` — an empty model answers `{"message": ""}`.
- **`/doc/NEW` discards unsaved work and has crashed Gen NX** when a large real
  model was open. Never call it without the author confirming the document does
  not matter.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` means the method is
  not served; `{"error": {...}}` means it ran and was rejected; an echoed record
  means it worked. `MidasResultError` does not fire on `error status`.
- **Never hand-write a live payload.** Copy from `scripts/live_crud_check.py`'s
  confirmed cases or from `contracts/`. A hand-written fixture produces
  confident wrong findings.
- Leave both models empty when you finish, and say so in the note.

## Task 1 — record the two live-versus-manual defects found on 08-30/08-31

Both are measured and neither is written down yet.

**1a. `/db/MATL-M1` is not "`/db/MATL` plus extras".** The manual says so at
`04_DB_Properties.md:239` — *기본 재료 구조는 `/db/MATL`과 동일하며, Hyper-S 전용
하이퍼엘라스틱 재료 모델을 추가로 지원합니다*. Live `/info` on Civil NX
contradicts every part of it:

```text
/db/MATL     9 props: NAME, TYPE, PARAM, DAMP_RAT, HE_COND, HE_SPEC, PLMT, P_NAME, bMASS_DENS
/db/MATL-M1  4 props: MATL_NAME, MATL_TYPE, PARAM, DAMP_RAT
```

The field names differ (`MATL_NAME`/`MATL_TYPE`, not `NAME`/`TYPE`), MATL-M1 has
**fewer** fields rather than more, and the two `HE_*` fields — the ones that
look like the Hyperelastic support the note claims is exclusive to MATL-M1 —
are on `/db/MATL` and absent from `/db/MATL-M1`. This is the `/db/REBW` class of
defect: a manual section wrong about its own endpoint's field names. Copying the
parent's fields, which the delegating wording invites, would have produced a
contract whose every top-level name is wrong.

Write it into `docs/live_verification_notes.md` with the `/info` output, and add
it to the manual-repo report list in Task 2.

**1b. `/db/IEHC`'s `WAreaSize` type.** `contracts/endpoints/db-iehc.yaml` types
it `integer`, following the manual's Specifications table. Live `/info` on Gen
types it **`string`**, and the manual's own worked example sends `"AUTO"`. Its
sibling `WAreaSizeCover` really is `integer` live, so this is one field, not the
table. Record the manual's claim under `manualDefects` and the live type under
`contracts/verification/`; do not silently retype the contract.

(The rest of `db-iehc.yaml` is already correct — all nine Wall fields carry
`products: [gen]`, matching both the manual's `#### GEN 전용 필드` heading and
live, where Gen exposes 17 properties and Civil 8.)

## Task 2 — consolidate the manual-repo report

Four findings are owed to `E:\AI Study\MIDAS-API` and none has been sent. Write
them up as one document in this repo — do **not** edit the manual repo from
here, and do not file anything in MIDASIT's Jira without the author's explicit
go-ahead.

| finding | what the manual says | what the product does |
| --- | --- | --- |
| `/db/STYP-M1` `DELETE` (3 places in `02_DB_Project_Structure.md`) | GET, PUT, DELETE | all three DELETE forms refused on both products, from a non-default state with a model open |
| `/db/POLC-M1` POST (⚠️ callout in `14_DB_Pushover.md`) | "no POST; the article's row is an untrimmed template" | POST creates a record that reads back on the next GET |
| `/db/MATL-M1` structure (`04_DB_Properties.md:239`) | same structure as `/db/MATL`, plus Hyperelastic | different field names, fewer fields, `HE_*` on the parent instead |
| `/db/IEHC` `WAreaSize` | Integer | `string` live; the chapter's own example sends `"AUTO"` |

Two of these originate in MIDASIT's official articles rather than the manual
repo's transcription (`/db/STYP-M1`'s `activeMethods`, `/db/MATL-M1`'s note).
Say which is which — the manual repo can fix its own text, but only MIDASIT can
fix theirs.

## Task 3 — bring `PLAN.md` back to the measured state

`CLAUDE.md` requires §2's status table and §4's milestone table to match the
tree, and they do not. Measure, do not copy these:

| PLAN.md says | measured 2026-08-31 |
| --- | --- |
| 845 Python tests | 863 |
| 279 endpoint contracts, 2,162 fields, 104 drafts | 283, 2,228, 100 |
| write coverage 162/399 | 165/399 (read 234) |

Update the "Last updated" line in the same commit. `PLAN.md` goes stale fast —
it spent three releases listing shipped work as pending — so verify each row
against the tree rather than adjusting the numbers you find.

## Task 4 — continue the live write-coverage push

This is the largest body of available work and it needs no schema decision. 234
of 399 endpoints are verified at `read` level only, and a read proves far less
than a round trip: it shows the route exists and parses, while every
field-name, enum and default defect found so far was invisible to reads.

Read `docs/live_verification_notes.md`'s existing batches for the established
method, then work in small batches. For each endpoint:

1. Take the payload from `scripts/live_crud_check.py`'s confirmed cases or from
   its contract. Never hand-write one.
2. `POST -> GET -> PUT -> GET -> DELETE {endpoint}/{id} -> GET`, on an empty
   scratch model, following the live-session rules above.
3. Record the result in `docs/live_verification_notes.md` **and** set
   `docs/coverage.json`'s `level` to `"write"` with the build baseline — then
   rerun `gen_roadmap.py` in the same commit.
4. A failure is a finding, not a blocked task. `"Wrong Field"` from a `/db/*`
   write usually means a bad **value**, not a bad field name — vary the enum
   value before varying the fields. Record what you tried.

Three known-unresolved write paths are worth a fresh attempt with this method,
and all three are already documented as unresolved rather than assumed broken:
`/db/SDIS`'s LRB and NRB branches, `/db/WVLD` on Civil (suspected module gate,
not payload spelling), and `/db/NLLP`.

## What NOT to start — these are the author's calls

All four block contract-shape work and none may be decided by an agent. Each
has a proposal in `docs/contract_migration_brief.md`; bring questions, not
implementations.

- **D1 — non-literal defaults** (`System`, `Auto`, `ADD, REPLACE`). Blocks
  `/db/STYP-M1`, whose draft is otherwise complete and correct, plus ~14 others.
  Proposal: a `documentedDefaultNote`, mirroring the existing `enumNote`.
- **D2 — requiredness unstated.** Blocks `db-mvctch` (76 notes) and `db-wvld`
  (54). `requirement` has no value for "the manual does not say", and inventing
  `optional` for a blank column is the `documentedOptional`/`safeToOmit`
  conflation the schema exists to prevent.
- **D3 — conditional variant schema.** 155 unmerged tables; 57 become
  expressible. Proposal: give `variant.when` the shape field-level
  `appliesWhen` already has, and add `in` to both.
- **D4 — scalar `Argument`.** Nine `/doc/*` endpoints whose whole argument is a
  string, not an object with fields.

Also out of scope: Stage 4 (Python generated from contracts), and any release.

## Before every commit

```bash
pip install -e ".[dev]"
pytest && ruff check src tests scripts && mypy
python scripts/validate_contracts.py
python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --check
python scripts/gen_roadmap.py          # if coverage.json changed
cd packages/typescript && npm run generate && npm run typecheck && npm test
git status --short                     # generation drift must be empty
```

Commit messages: imperative subject, body explaining *why*; match `git log`.
One task per commit.

---

## What the last batch settled — verified 2026-08-31

Kept so the same ground is not re-covered.

- **`/db/STYP-M1` numbering** — fixed. The draft now nests all four
  `MASS_CONTROL` members, with the correct enums (`[CENTROID, OFFSET]`,
  `[XYZ, XY, Z]`) and a boolean `appliesWhen`. Only D1 blocks promotion.
- **Shadow gate** — widened past `/db/*` to `/DESIGN/*`.
- **Variant measurement** — the counter is reproducible now: 253 supplementary
  tables, of which 155 unmerged, split 4 / 53 / 98 by selector evidence, with
  per-table detail from `--report`. This is what D3 will be decided on.
- **Missing Default columns** — recorded once under `extraction.missingColumns`;
  four contracts promoted (SDHY, SDVE, SDVI, NLLP). The four not promoted were
  correctly refused: SDIS and SDST are variant-blocked, MVCTch and WVLD are
  Required-blocked.
- **Live `/info` reconciliation** — `/db/MVCTch` `BRIDGE2`, `/db/MVLD` `ASL`,
  `/db/MVLDch`'s auto-optimize branch, `/db/STCT`'s `bSDLE`/`vSDLE`, and
  `/db/IEHC`'s beam-field renames. Independently re-verified against both
  products; every claim held, including the nested member names.
- **Live round trips (08-31)** — `/db/MATL-M1` all three `P_TYPE` branches,
  `/db/SDST` on both products, `/db/SDIS`'s SLD branch on Gen, `/db/MVCTch`'s
  `iCODETYPE=0` branch on both. Cleanup verified: both models answer
  `{"message": ""}` for every endpoint touched.
- **`/doc/*` and Hyper-S `-M1`** — correctly identified as blocked, not skipped.
  `/doc/OPEN`'s `Argument` really is a bare string (D4), and `/db/MATL-M1`'s
  "same structure as the parent" wording is provably wrong, so copying the
  parent's fields would have been a guess. See Task 1a.
