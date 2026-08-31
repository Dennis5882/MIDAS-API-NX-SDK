# Codex task prompt — mechanical work only

Updated 2026-09-01 at HEAD `bc771c0`, after your live batch. Version stays
**2.7.3** on both registries.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against; a task that turns out
to need a judgment call is one to **stop and report**, not to decide.

## What changed since your last batch

Your two live commits landed and everything is green. Task 3 (the verbatim
Civil WALL response) is **done** — MD-06 now quotes the server and reasons
about the numbering without deciding Civil's support scope. That was the right
shape of answer.

Two things from that batch are worth naming because they change how the next
one runs:

- **You found a real harness defect.** `live-crud.mjs` had been saving a
  checkpoint and then mutating *the caller's open document*. Its earlier
  "empty scratch model" evidence was not what it claimed. Calling `/doc/NEW`
  and verifying `/db/NODE` and `/db/ELEM` are empty is the right fix.
- **One follow-up commit, `bc771c0`, made that destructiveness visible.**
  CLAUDE.md named only the two Python harnesses as discarding unsaved work; the
  npm one now appears in both places, and the script's own header and usage line
  say what `--no-save-before` costs. Behaviour unchanged — only the warning.

The number that moved least is the one Task 1 is about: **write coverage went
165 → 166.** The 13 fixtures you raised to `confirmed` are worth more than that
suggests — a confirmed case fails as a regression — but the ledger itself barely
moved. This batch should move it.

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
   **Quote the server verbatim.** A paraphrase is not evidence — see Task 3.
5. **A parity failure is an SDK defect, never a reason to edit a contract.**
6. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**
   Drafts are git-ignored build output. The directory held **377 stale files**
   before it was cleared; it now holds exactly the 65 live drafts. Before
   judging what is promotable, clear it and re-emit:

   ```bash
   rm -f contracts/drafts/*.yaml
   python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all
   ```

   A stale draft directory understated promotability by nine contracts once
   already.
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
  without the author confirming the open document does not matter. Three
  harnesses now call it: `live_smoke.py`, `live_crud_check.py`, and
  `packages/typescript/scripts/live-crud.mjs`. `--no-save-before` removes the
  npm harness's checkpoint, not its `/doc/NEW`.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- Leave both models empty, and say so in the note.

## Task 1 — Python live write coverage (the main body of work)

Measured today: **166 of 399 rows are write-verified, 233 are read-only.**
A read shows the route exists and parses. Every field-name, enum and default
defect found in this project so far was invisible to one.

The 233 read-only rows break down as `/DESIGN` 122, `/db` 79, `/post` 13,
`/ope` 12, `/view` 7.

`schema/live-cases.json` holds 166 cases across 158 endpoints, **134 confirmed**
after your batch. **24 endpoints still recorded as `read`-level already carry a
fixture** — the payload is written, nobody has watched it pass:

```text
/db/ACTL  /db/CGLP  /db/DOEL  /db/EPSE  /db/EPST  /db/FBLA  /db/HAHS
/db/HECB  /db/HPCE  /db/LCOM-SEISMIC  /db/MADO  /db/MVCT  /db/NLLP
/db/NLNK  /db/NLNK-M1  /db/RPSC  /db/SBDO  /db/SDVE  /db/SDVI
/db/STCT  /db/STRPSSM  /db/TDMF  /db/THMS  /db/WVLD
```

You attempted most of these last batch and they reproduced product rejections —
`SDVE`/`SDVI` answered `Wrong Field` on both products, `MVCT`/`NLLP`/`WVLD`
still fail. **Two were never attempted at all: `/db/HECB` and `/db/STCT`.**
Start there, then `/db/LCOM-SEISMIC` (Task 3), then re-attack a rejection with a
different documented enum value rather than a different field set.

Work in small batches:

1. Take the payload from its existing case, or from the endpoint's contract.
2. Run `POST → GET → PUT → GET → DELETE {endpoint}/{id} → GET` on an empty
   scratch model. Declare `setup=` seeds for element- or node-keyed records
   rather than writing to an empty document — you established that pattern last
   batch for `LTSR`/`MBTP`/`LENG`/`MEMB`/`WMAK`; reuse it.
3. Record it in `docs/live_verification_notes.md`, set `docs/coverage.json`'s
   `level` to `"write"` with the build baseline, and rerun `gen_roadmap.py` in
   the same commit.
4. A confirmed case that fails is a **regression** (exit 1). An unconfirmed one
   that fails means triage the fixture first (exit 3). Never flip `confirmed` to
   silence a failure.

**A failure is a finding, not a blocked task.** `"Wrong Field"` from a `/db/*`
write usually means a bad **value**, not a bad field name — vary the enum value
before varying the fields, and record what you tried.

**Report, do not decide**, if a run suggests the manual is wrong about a field
name, an enum or a method. Write the evidence down and stop there.

## Task 2 — extend the npm live harness

Measured today: **17 endpoints have completed the full public-API CRUD cycle on
both products** — the previous 14 plus `PNLD`, `EIGV` and `DCON`. Four populated
result tables have been read (`MASS_SUMMARY_X`, `REACTIONG`, `DISPLACEMENTG`,
`BEAMFORCE`), and five more endpoints have been created and deleted as analysis
prerequisites. That is 17 against Python's 166 — still the widest gap in the
project.

Now that every npm run starts from `/doc/NEW`, its evidence means what it says.
Re-running a fixture the Python harness has already confirmed is cheap and
worth doing in the same batch as Task 1.

`packages/typescript/scripts/live-crud.mjs` and `live-analysis.mjs` read the
same `schema/live-cases.json` and exercise only the package's public API. Grow
that set the same way, in batches.

Two constraints specific to this side:

- **`docs/coverage.json`'s `level` means verification through the Python
  package** and has for its whole history. Record npm evidence in
  `docs/live_verification_notes.md` as its own entry; do not widen `level` on an
  npm run, which would make every historical row ambiguous. You got this right
  last batch — keep doing it.
- Use `resources.db.<group>.<name>`, not raw `client.request`. The point is to
  exercise what a user touches.

## Task 3 — `/db/LCOM-SEISMIC`, whose blocker you just removed

Its ledger entry from 2026-08-16 says the `ANAL="ST"` payload that all five
sibling `LCOM-*` endpoints accept passed a full round trip on **Gen**, while
Civil answered `"The Load Combination Type is not supported"`. The note then
records why it was parked:

> The manual's own example uses `ANAL="RS"`/`"CS"` instead of `"ST"`; testing
> that path needs a real `/db/SPLC` Response Spectrum Load Case fixture,
> deferred to a future `db.dynamic_loads` batch.

**You built that fixture last batch.** `/db/SPLC` now round-trips on Civil with
its `spfc_seed` prerequisite, so the deferral's stated condition is met.

Seed a Response Spectrum Load Case, then run `LCOM-SEISMIC` with the manual's
`ANAL="RS"` on Civil. Both outcomes are useful: a pass says the asymmetry was a
payload value rather than a product limit, and a failure is a verbatim response
worth recording.

Two constraints:

- **Do not raise the level from the 2026-08-16 record alone.** That Gen pass is
  real, and the ledger has 9 gen-only writes as precedent, so raising it would
  be defensible on convention — but it ran on build 06/23/2026, and every entry
  raised this week was re-run first. Re-run it.
- `/db/SPLC` is now `write` with `products: [civil]` while `LCOM-SEISMIC` sits
  at `read` with both products, and SPLC's own note names LCOM-SEISMIC as
  "same treatment". After this run the two should agree. Say which way, and why.

## Stop and report — do not decide these

The dry run offers **0 of 65 drafts** right now. The refusals break down as:

| count | reason |
| --- | --- |
| 23 | conditional variant tables nobody has merged |
| 18 | N unresolved review notes |
| 7 | no payload fields could be parsed |
| 8 | a documented value proven wrong live, or a broken write path |
| 7 | a Key cell naming two wire properties at once (`'DT" / "DB'`) |
| 1 | plain-function parity surface not discovered |
| 1 | no live-verification record in `docs/coverage.json` |

None of that is a mechanical batch. Specifically:

- **The 23 refused for unmerged conditional variants.** `in` and the array
  `when` shipped in 2.7.3 and handled every case where the manual states a
  selector. What remains is tables where the manual names **no** wire
  discriminator — `/db/ELEM`'s `#### Wall`, `/db/NLNK`'s Angle/3Points/Vector.
  `TYPE="WALL"` is obvious to a human and is not written down. Leaving these
  unmerged is rule 2 working.
- **The 7 refused for "no payload fields could be parsed."** These are Hyper-S
  `-M1` sections that delegate to a parent. Do not copy the parent's fields:
  `/db/MATL-M1` says it matches `/db/MATL`, and live `/info` shows different
  top-level names, fewer fields, and the `HE_*` fields on the parent instead.
  The delegation claims are not trustworthy.
- **The remaining "values listed elsewhere" enum notes — 26 across 6 drafts**
  (`db-thgc-m1`, and the RC `dcre`, `dcrm-wall`, `rebb`, `rebc`, `rebr`
  drafts). Your rule already took the ones written as a complete list. What is
  left is ranges and abbreviations: `19종 (D4 ~ D57)` names a count and two
  endpoints, not nineteen values. **Do not extend the parser to expand a
  range.** Only `dcrm-wall` is blocked by these alone; the rest carry other
  notes too.
- **A section fold the extractor refused.** `--emit-all` now warns when two
  manual sections share a draft name and could not be folded. Today nothing
  warns. If something starts to, read both sections and hand it back — the
  refusal means they disagree by more than one field, which is two documents
  about one endpoint, not an average waiting to be taken.
- **Anything that would need a new schema construct.** All four contract-schema
  decisions are closed; a fifth needs the author.

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

Baseline to beat: **896 Python tests, 55 npm tests**, all green at `bc771c0`.

Commit messages: imperative subject, body explaining *why*. One task per commit.

---

## Settled — do not re-derive

- **All four contract-schema decisions are closed.** D1 `documentedDefaultNote`
  and D2 unstated requiredness shipped in 2.7.2; D3 array `when` with `in` and
  D4 `scalar`/`empty` arguments shipped in 2.7.3. `contracts/README.md` states
  each with its reasoning, and now also states the one-route section fold.
- **319 endpoint contracts, 65 drafts, 0 promotable.** 252 of the 304 npm
  resources take their facts from a contract; 52 use the reviewed Python
  fallback. npm's surface coverage is 399/399 — the gap is live evidence, not
  reach.
- **`docs/coverage.json` carries one row per result table, not per route.**
  `/DESIGN/RC/KDS-41-20-2022/TABLE` has three rows and
  `/DESIGN/SRC/AIK-SRC2K/TABLE` two, because each `TABLE_TYPE` returns its own
  table and verifying one does not verify the others. The contracts fold those
  same sections into one endpoint each. Both are right; do not "reconcile" them.
- **Six manual defects are registered** in `docs/manual_defects_register.md`,
  labelled by which side owns the fix, and MD-06 now quotes the server verbatim.
  Append new ones there; send nothing.
- **`/db/FBLA`'s shared table** — `= 1 or 2` alongside `= 1` and `= 2` — folds
  into both branches at generation time rather than forming a third union
  member. That is decided and implemented.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Omitting them ends the
  session on both products. Both SDKs fill them in, and the npm side is now
  live-confirmed to do so on a real POST.
