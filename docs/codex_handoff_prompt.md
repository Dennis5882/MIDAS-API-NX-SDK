# Codex task prompt — D1 and D2 approved

Rewritten 2026-08-31 at `fbb8d46`. The previous batch is done: the JS/TS live
harness, the ROADMAP CI gate, and the first npm live write evidence all landed.

**The author has decided.** D1 and D2 are approved as proposed. D3 and D4 stay
out of scope and will be discussed after a version bump. Manual-error findings
are collected in one place rather than acted on. Paste the section below.

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
3. **`documentedOptional` (docs) and `safeToOmit` (product) are separate.**
   This matters more than usual in this batch — see D2 below.
4. **Manual and product disagree → record both separately**, the manual's claim
   under `manualDefects`, the product's under `contracts/verification/`.
5. **A parity failure is an SDK defect, never a reason to edit a contract.**
6. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   Drafts are git-ignored build output; if a draft is wrong, fix the extractor.
7. **`ROADMAP.md` is generated from `docs/coverage.json`** — rerun
   `gen_roadmap.py` in the same commit. CI now enforces this.
8. **Do not release.** Task 5 prepares a release; the author cuts it.

## Live-session rules — if you touch the products at all

This batch needs no live calls. If something makes one necessary:

- **Ask the author first** and confirm both documents are empty
  (`GET /db/NODE` and `GET /db/ELEM` answer `{"message": ""}`).
- **`--save-dir` is required and never inferred.** `verify_connection()["user"]`
  is the MAPI account's email, not the NX host's Windows profile; deriving a
  path from it raises the blocking dialog. `C:/temp` exists on both machines
  and the author created it.
- **Model extensions, four in two pairs**: pre-NX Gen `.mgb` / Civil `.mcb`;
  **NX Gen NX `.mgbx` / Civil NX `.mcbz`**. `/doc/STAGAS` is the exception that
  wants legacy `.mcb`. This repo got Civil's wrong twice; do not re-derive it.
- **Delete every test record by its own id.** Leave both models empty.

## Task 1 — D1: `documentedDefaultNote`

**Approved.** The manual's Default cell sometimes holds a description rather
than a wire value — `System`, `Auto`, `ADD, REPLACE`. Today the extractor emits
`# NOTE: non-literal default 'X' kept verbatim`, which is complete information
filed as an open question, and promotion refuses it.

Add a `documentedDefaultNote` string to the field schema, mirroring the
`enumNote` that already exists for the same situation on enums. Then:

- `documentedDefault: null` — the manual gives **no literal** value. This is
  already what the schema says null means.
- `documentedDefaultNote: "System"` — what the manual actually wrote.
- `safeToOmit` stays `unverified`. A described default is not evidence about
  the product. Do not let this batch move a single `safeToOmit`.

Clear the note in the extractor once the value is captured, the same way the
JSON-Schema-supplied default already clears it.

## Task 2 — D2: requiredness may be recorded as unstated

**Approved.** Some manual tables have no Required column at all, and
`requirement` has no value meaning "the manual does not say". Inventing
`optional` for a blank column is exactly the `documentedOptional`/`safeToOmit`
conflation the schema exists to prevent, so:

- Add `"unstated"` to `requirement`'s enum.
- Allow `documentedOptional: null`, **only** when `requirement` is `"unstated"`.
  Enforce that pairing in the schema or the validator — `null` must mean "the
  docs are silent", never "the docs say required".
- Same treatment for a missing Value Type column where the type is genuinely
  unstated; do not invent a type to fill it.

Update `contracts/README.md` for both D1 and D2 in the same commit that adds
them. That file is authoritative and a schema change that is not described
there is half-done.

## Task 3 — promote what D1 and D2 unblock

Measured against the current tree, D1 and D2 together unblock **22 drafts** —
16 by D1 alone, 5 by D2 alone, 1 needing both:

```text
D1: db-bngr db-cscs db-pnld db-sseis db-styp db-styp-m1
    design-rc-kds-41-20-2022-wc-table design-src-aik-src2k-table
    ope-lcom-conc ope-lcom-src ope-lcom-steel ope-linebmld
    ope-storyprop ope-uslc view-display view-resultgraphic
D2: db-matd db-mvctch db-nbof db-wvld doc-stagas
D1+D2: ope-lcom-gen
```

Expected outcome: promoted contracts **283 → 305**, npm resources whose facts a
contract owns **240/304 → 250/304**, leaving 54 on the Python fallback.
Re-measure rather than trusting these; if your run promotes a materially
different set, stop and report it.

`/db/STYP-M1` is in that list and is the one to do first — its draft has been
complete and correct since the numbering fix and D1 was its only blocker. Once
it is promoted, raise `docs/coverage.json`'s `vendored_at_commit` past `5c92efe`
and confirm `check_manual_drift.py` reports `has_diff: false`.

**Review each promoted contract against its manual section before committing.**
A bulk promotion nobody read is how a wrong contract reaches
`contracts/endpoints/`. Commit in small, reviewable groups, not one commit of 22.

## Task 4 — make the manual-defect register a living document

The author's decision: **collect these, do not act on them.** Do not edit the
manual repo, do not contact MIDASIT, do not file anything in Jira.

`docs/manual_repo_report_2026-08-31.md` is a dated snapshot of four findings.
Convert it into a running register — rename it to something undated such as
`docs/manual_defects_register.md`, give each entry a stable id, the date found,
the evidence, and which side owns the correction (MIDASIT's official article
versus the manual repo's own transcription). Fold in anything already recorded
elsewhere that belongs, including the extension confusion:

- `/db/STYP-M1` `DELETE` — MIDASIT article `activeMethods`
- `/db/POLC-M1` POST — manual-repo callout
- `/db/MATL-M1` structure — MIDASIT article note
- `/db/IEHC` `WAreaSize` type — manual-repo transcription
- Civil NX's save extension — the manual's examples still show pre-NX
  spellings; NX is `.mgbx` / `.mcbz`

From now on a new manual-versus-product finding is appended there in the same
commit that records the live evidence.

## Task 5 — prepare the release, do not cut it

When Tasks 1–4 are done the author will cut a version. Prepare only:

- Draft release notes at `docs/release_notes_vNEXT.md` and an `Unreleased`
  section in `packages/typescript/CHANGELOG.md`. Leave the number out; the
  author picks it, and both registries move together.
- Lead with what actually changes for users. Note honestly that the Python and
  npm **package surfaces** may be unchanged by this batch — it is contract and
  schema work — and say which surface, if either, is the reason for the release.
- Do not bump `src/midas_nx/__init__.py` or `package.json`.

## What NOT to start

- **D3 — conditional variant schema** (155 unmerged tables, 57 expressible) and
  **D4 — scalar `Argument`** (nine `/doc/*` endpoints). The author will decide
  these **after** the version bump. The measurement they will be decided on is
  already in `docs/contract_migration_brief.md`; do not extend it, and do not
  implement either.
- **Stage 4** — Python generated from contracts.
- **Any release.**
- **Any external communication** about the manual defects.

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

Commit messages: imperative subject, body explaining *why*. One task per commit.

---

## Settled — do not re-derive

- **`/db/STYP-M1`** — numbering, enums and boolean condition all fixed; D1 was
  the last blocker.
- **Shadow gate** — widened past `/db/*` to `/DESIGN/*`.
- **Variant measurement** — 253 supplementary tables, 155 unmerged, split
  4 / 53 / 98 by selector evidence. This is what D3 will be decided on.
- **npm live evidence (2026-08-31)** — seven endpoints round-tripped on both
  products through the public API, four populated result tables read, and
  `/db/NMAS`'s `payloadDefaults` confirmed to be sent on a real POST. All four
  tables arrived under the unstable key `empty` and `unwrapTable()` found them
  by shape. Harness: `packages/typescript/scripts/live-crud.mjs` and
  `live-analysis.mjs`, reading `schema/live-cases.json`.
- **npm independence** — the published package has zero runtime dependencies.
  What still reads Python is the *generator*, for the 64 resources with no
  contract, plus the `className`/`pythonModule` compatibility anchors. Task 3
  moves that to 54.
- **Model extensions** — pre-NX `.mgb`/`.mcb`, NX `.mgbx`/`.mcbz`; `/doc/STAGAS`
  wants legacy `.mcb`. Wrong twice already.
