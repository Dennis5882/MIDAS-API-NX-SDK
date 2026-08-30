# Codex task prompt — closing the npm evidence gap

Rewritten 2026-08-31 at `98eb98d`. The previous edition's four tasks are all
done (`9b8111f`, `2405496`, `b690b16`, `9ea3b21`). Paste the section below.

**Why this batch looks different.** The two packages are at exact parity in
code — 304 endpoint resources each, zero difference in either direction, both
published at 2.7.1. The only real difference between them is **evidence**: 165
endpoints are live-write-verified through the Python package and **zero**
through npm. Until 2026-08-31 the npm package had never spoken to a MIDAS NX
server at all. That gap, not the contract backlog, is what stands between the
npm package and being recommended to other people, so it comes first.

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
3. **`documentedOptional` (docs) and `safeToOmit` (product) are separate
   booleans.** `/db/NMAS` is where believing the manual ends a live NX session.
4. **Manual and product disagree → record both separately**, the manual's claim
   under `manualDefects`, the product's under `contracts/verification/`.
5. **A parity failure is an SDK defect, never a reason to edit a contract.**
6. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   Drafts are git-ignored build output; if a draft is wrong, fix the extractor.
7. **`ROADMAP.md` is generated from `docs/coverage.json`.** Rerun
   `python scripts/gen_roadmap.py` in the same commit that touches coverage.
   This was missed twice in two days; Task 2 makes CI catch it.
8. **Do not release.** The author picks the version; both registries move
   together.

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session** and confirm both
  documents are empty. Verify with `GET /db/NODE` and `GET /db/ELEM` — an empty
  model answers `{"message": ""}`.
- **`/doc/NEW` discards unsaved work and has crashed Gen NX.** Never call it
  without the author confirming the document does not matter.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success.
- **Never hand-write a live payload.** Use the confirmed cases.
- Leave both models empty when you finish, and say so in the note.

## Task 1 — a JS/TS live harness, so npm has its own evidence

Today `scripts/live_crud_check.py`, `live_readonly_sweep.py` and
`live_smoke.py` are all Python, and every npm test mocks `fetch`. The npm
package's hand-written HTTP layer, error mapping and `/post/TABLE` adapter had
never met a real server until a read-only probe on 2026-08-31 (recorded in
`docs/live_verification_notes.md`). Ten checks passed and matched Python
exactly, including `MidasResultError` firing on a 200-with-error-body. **No npm
write has ever reached a live product.**

**1a. Extract the confirmed cases into a shared fixture.** `live_crud_check.py`
holds 127 `confirmed=True` cases out of 160. Do **not** re-type them in
TypeScript, and do not have the JS harness import from Python — that would make
one SDK a source for the other's verification. Instead emit the case list to a
language-neutral JSON fixture (a `--emit-cases` flag on the Python script, or a
small generator writing e.g. `schema/live-cases.json`), and have **both**
harnesses read it. Commit the fixture; CI should fail if it drifts, the same way
the TypeScript generated files are gated.

**1b. Write the harness.** A Node script under `packages/typescript/scripts/`
(or `scripts/`, your call — say why) that takes a MAPI key and product, reads
the fixture, and runs `POST → GET → PUT → GET → DELETE {endpoint}/{id} → GET`
through the **published package's own public API** (`resources.db.<group>.<name>`),
not through raw `client.request`. The point is to exercise what a user touches.

Mirror the Python script's contract exactly: a confirmed case that fails is a
**regression** and exits 1; an unconfirmed case that fails exits 3 and means
"triage the fixture first". Do not flip a case to confirmed to silence a
failure.

**1c. Run it, small batches first.** Start with a handful of low-risk endpoints
(`/db/NODE`, `/db/MATL`, `/db/GRUP`) and grow. Two things specifically want
proving from JavaScript, because both are hand-written and neither is observed:

- **`/db/NMAS`'s `payloadDefaults`.** The generated resource carries
  `{"rmX":0.0,"rmY":0.0,"rmZ":0.0}` and `db-resource.ts` applies it. Omitting
  those three fields is what killed live NX sessions 15+ times. Verify the npm
  package sends them on a real POST — this is the single most important live
  check on the npm side.
- **`unwrapTable()` against a populated table.** The 08-31 probe reached it but
  the model was empty, so the unstable-top-level-key behaviour it exists for is
  still unobserved from JavaScript. Seed a few nodes, then read `/post/TABLE`.

Record the results in `docs/live_verification_notes.md` as an npm section, and
say plainly which endpoints are now live-verified **through npm** as distinct
from through Python. Do not raise `docs/coverage.json`'s `level` on the strength
of an npm run alone unless you also say so in the entry — the ledger's `level`
has meant "verified through the Python package" for its whole history, and
silently widening it would make every historical row ambiguous.

## Task 2 — make CI catch the ROADMAP miss

`.github/workflows/ci.yml:66` already fails on TypeScript generation drift:

```yaml
- name: Fail if generated TypeScript files drifted
  run: git diff --exit-code -- schema/typescript-resources.json schema/typescript-coverage.json packages/typescript/src/generated
```

`ROADMAP.md` is generated the same way and has no such gate, which is why two
coverage commits in two days shipped stale counts. Add the symmetric step: run
`python scripts/gen_roadmap.py`, then `git diff --exit-code -- ROADMAP.md`.

## Task 3 — continue live write coverage (background work)

234 of 399 endpoints are `read`-level only. A read shows the route exists and
parses; every field-name, enum and default defect found so far was invisible to
one. This is open-ended by design — do it in batches between the tasks above,
not as a push to finish.

Method: take the payload from a confirmed case or its contract, run the full
round trip on an empty scratch model, record it, set `level` and rerun
`gen_roadmap.py` in the same commit. A failure is a finding, not a blocked task
— `"Wrong Field"` usually means a bad **value**, so vary the enum value before
varying the fields, and record what you tried.

Known-unresolved and worth a fresh attempt: `/db/SDIS`'s LRB branch,
`/db/WVLD` on Civil (suspected module gate), `/db/NLLP`.

## What NOT to start — the author's calls

Four decisions block the contract-shape queue. Each has a written proposal in
`docs/contract_migration_brief.md`. Bring questions, not implementations.

- **D1 — non-literal defaults** (`System`, `Auto`). Blocks `/db/STYP-M1`, whose
  draft is otherwise complete, plus ~14 others. Proposal: a
  `documentedDefaultNote`, mirroring the existing `enumNote`.
- **D2 — requiredness unstated.** Blocks `db-mvctch` (76) and `db-wvld` (54).
- **D3 — conditional variant schema.** 155 unmerged tables, 57 expressible.
- **D4 — scalar `Argument`.** Nine `/doc/*` endpoints.

Also the author's, not yours: **sending `docs/manual_repo_report_2026-08-31.md`**
anywhere. It is a hand-off document. Do not edit the manual repo from here and
do not file anything in MIDASIT's Jira without an explicit go-ahead.

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

Commit messages: imperative subject, body explaining *why*. One task per commit.

---

## Settled — do not re-derive

- **`/db/STYP-M1` numbering, enums, boolean condition** — fixed; only D1 blocks
  promotion.
- **Shadow gate** — widened past `/db/*` to `/DESIGN/*`.
- **Variant measurement** — reproducible: 253 supplementary tables, 155
  unmerged, split 4 / 53 / 98 by selector evidence. This is what D3 decides on.
- **Missing Default columns** — recorded under `extraction.missingColumns`; four
  contracts promoted. The four refused were correctly refused.
- **Live `/info` reconciliation** — `/db/MVCTch` `BRIDGE2`, `/db/MVLD` `ASL`,
  `/db/MVLDch`, `/db/STCT`, `/db/IEHC`. Independently re-verified; all held.
- **Live round trips** — `/db/MATL-M1` (3 `P_TYPE` branches), `/db/SDST` both
  products, `/db/SDIS` SLD + NRB on Gen, `/db/MVCTch` both products.
- **Manual defects** — four consolidated in
  `docs/manual_repo_report_2026-08-31.md`, MIDASIT-article errors separated from
  manual-repo transcription errors.
- **npm read paths, live** — verified 2026-08-31 against both products and
  matching Python exactly. Writes remain unverified; that is Task 1.
