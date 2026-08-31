# Codex task prompt — mechanical work only

Rewritten 2026-08-31 at 2.7.3, after the four contract-schema decisions closed.

**The division, set by the author.** Judgment-heavy work — schema design, deciding
what a contradictory manual means, deciding what stays unmerged — is Claude's.
Bounded, verifiable, repeatable work is yours. Every task below has an expected
outcome you can check your run against; a task that turns out to need a judgment
call is one to **stop and report**, not to decide.

Nothing in `contracts/` is promotable right now — the dry run offers zero — so
this batch is live verification, which is where the headroom is: 234 of 399
endpoints are `read`-level only, and both harnesses already exist.

---

You are working in `E:\AI Study\MIDAS-API-NX-SDK` on branch `main` — the
`midas-nx` SDKs, published on PyPI and npm at **2.7.3**. Read `CLAUDE.md`,
`contracts/README.md`, and `docs/contract_migration_brief.md` first. Where this
prompt and those disagree, they win.

## Hard rules

1. **Neither SDK is a source for the other, and neither is a source for a
   contract.** Permitted contract sources are exactly three: the manual repo
   (`E:\AI Study\MIDAS-API`, `docs/manual/*.md`),
   `docs/live_verification_notes.md`, and live `/info/{endpoint}` introspection.
2. **Do not guess.** `unverified` is a correct answer; an invented one is not.
3. **`documentedOptional` (docs) and `safeToOmit` (product) are separate.**
4. **Manual and product disagree → record both separately**: the manual's claim
   under `manualDefects`, the product's under `contracts/verification/`, and a
   line in `docs/manual_defects_register.md` naming the side that owns the fix.
5. **A parity failure is an SDK defect, never a reason to edit a contract.**
6. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   Drafts are git-ignored build output. **Run
   `python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all`
   before judging what is promotable** — a stale draft directory silently
   understated it by nine contracts once already.
7. **`ROADMAP.md` is generated from `docs/coverage.json`** — rerun
   `gen_roadmap.py` in the same commit. CI fails if you forget.
8. **Do not bump a version and do not release.** Not `src/midas_nx/__init__.py`,
   not `package.json`. The author cuts releases. This was overstepped once.

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session** and confirm both
  documents are empty: `GET /db/NODE` and `GET /db/ELEM` answer
  `{"message": ""}`.
- **`--save-dir` is required and never inferred.** `verify_connection()["user"]`
  is the MAPI account's email, not the NX host's Windows profile. `C:/temp`
  exists on both machines; the author created it.
- **Model extensions**: pre-NX Gen `.mgb` / Civil `.mcb`; **NX Gen NX `.mgbx` /
  Civil NX `.mcbz`**. `/doc/STAGAS` is the exception that wants legacy `.mcb`.
  This repo got Civil's wrong twice — do not re-derive it.
- **`/doc/NEW` discards unsaved work and has crashed Gen NX.** Never call it
  without the author confirming the open document does not matter.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- Leave both models empty, and say so in the note.

## Task 1 — extend live write coverage (the main body of work)

165 of 399 endpoints are write-verified; 234 are read-only. A read shows the
route exists and parses. Every field-name, enum and default defect found in this
project so far was invisible to one.

`schema/live-cases.json` holds **165 cases, 121 confirmed**. Work in small
batches:

1. Take the payload from a confirmed case or from the endpoint's contract.
2. Run `POST → GET → PUT → GET → DELETE {endpoint}/{id} → GET` on an empty
   scratch model.
3. Record it in `docs/live_verification_notes.md`, set `docs/coverage.json`'s
   `level` to `"write"` with the build baseline, and rerun `gen_roadmap.py` in
   the same commit.
4. A confirmed case that fails is a **regression** (exit 1). An unconfirmed one
   that fails means triage the fixture first (exit 3). Never flip `confirmed` to
   silence a failure.

**A failure is a finding, not a blocked task.** `"Wrong Field"` from a `/db/*`
write usually means a bad **value**, not a bad field name — vary the enum value
before varying the fields, and record what you tried.

Known-unresolved and worth a fresh attempt: `/db/SDIS`'s LRB branch,
`/db/WVLD` on Civil (suspected module gate), `/db/NLLP`.

**Report, do not decide**, if a run suggests the manual is wrong about a field
name, an enum or a method. Write the evidence down and stop there.

## Task 2 — extend the npm live harness over the same fixture

`packages/typescript/scripts/live-crud.mjs` and `live-analysis.mjs` read the
same `schema/live-cases.json` and exercise only the package's public API. Seven
endpoints and four result tables have npm evidence so far. Grow that set the
same way, in batches.

Two constraints specific to this side:

- **`docs/coverage.json`'s `level` means verification through the Python
  package** and has for its whole history. Record npm evidence in
  `docs/live_verification_notes.md` as its own entry; do not widen `level` on an
  npm run, which would make every historical row ambiguous.
- Use `resources.db.<group>.<name>`, not raw `client.request`. The point is to
  exercise what a user touches.

## Task 3 — the twelve "enum values listed elsewhere" notes

Twelve fields across the refused drafts carry `the manual types this as an enum
but the values are listed elsewhere in the chapter`. The values exist in the
manual; finding them is reading, not deciding.

For each: locate the value list in the same chapter, confirm it belongs to that
field, and teach the extractor to pick it up — **fix the extractor, never the
draft**. If a value list is ambiguous about which field it belongs to, leave that
one and say which.

Expect this to unblock some of the 18 note-refused drafts. Re-emit drafts and
rerun the dry run to see how many; promote only what the dry run offers, and
review each against its manual section before committing.

## Stop and report — do not decide these

These are judgment calls, and getting one wrong puts a confidently wrong contract
into the source of truth. Write down what you found and hand it back:

- **The 23 drafts refused for unmerged conditional variants.** `in` and the
  array `when` shipped in 2.7.3 and handled every case where the manual states a
  selector. What remains is 98 tables where the manual names **no** wire
  discriminator — `/db/ELEM`'s `#### Wall`, `/db/NLNK`'s Angle/3Points/Vector.
  `TYPE="WALL"` is obvious to a human and is not written down. Leaving these
  unmerged is rule 2 working.
- **The 7 drafts refused for "no payload fields could be parsed."** These are
  Hyper-S `-M1` sections that delegate to a parent. Do not copy the parent's
  fields: `/db/MATL-M1` says it matches `/db/MATL`, and live `/info` shows
  different top-level names, fewer fields, and the `HE_*` fields on the parent
  instead. The delegation claims are not trustworthy.
- **Notes about a type that contradicts its own nested children, a conditional
  with no stated condition, an unstated array item type, or a Korean cross-field
  constraint** (`필수. true이면 BEAM_COLUMN/WALL 중 최소 1개`).
- **Anything that would need a new schema construct.** All four decisions are
  closed; a fifth needs the author.

Also out of scope: Stage 4 (Python generated from contracts), any release, and
any external communication about `docs/manual_defects_register.md` — no manual
repo edit, no MIDASIT contact, no Jira issue.

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

- **All four contract-schema decisions are closed.** D1 `documentedDefaultNote`
  and D2 unstated requiredness shipped in 2.7.2; D3 array `when` with `in` and
  D4 `scalar`/`empty` arguments shipped in 2.7.3. `contracts/README.md` states
  each with its reasoning.
- **319 endpoint contracts, 3,010 fields, 65 drafts awaiting review.** 252 of
  the 304 npm resources take their facts from a contract; 52 use the reviewed
  Python fallback.
- **npm live evidence exists**: seven endpoints round-tripped on both products
  through the public API, four populated result tables read, `/db/NMAS`'s
  `payloadDefaults` confirmed sent on a real POST, and `unwrapTable()` shown
  finding tables by shape under the unstable key `empty`.
- **Five manual defects are registered** in `docs/manual_defects_register.md`,
  labelled by which side owns the fix. Append new ones there; send nothing.
- **`/db/FBLA`'s shared table** — `= 1 or 2` alongside `= 1` and `= 2` — folds
  into both branches at generation time rather than forming a third union
  member. That is decided and implemented.
