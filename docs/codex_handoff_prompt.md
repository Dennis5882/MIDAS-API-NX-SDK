# Codex task prompt — mechanical work only

Updated 2026-09-01 at HEAD `31829dd`. Version stays **2.7.3** on both
registries.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against; a task that turns out
to need a judgment call is one to **stop and report**, not to decide.

## What changed since your last batch

Your seismic-damper batch landed clean and moved write coverage 166 -> 169.
Two results in it were better than the numbers suggest:

- **You root-caused `/db/SDVI` and `/db/SDVE`.** Their `Wrong Field` results
  pre-dated the manual's 2026-08-25 Request-Example corrections - the old SDVI
  fixture omitted `INPUT_TYPE_EXFN` and six exponential fields per `ITEM`, the
  old SDVE fixture had three fields of fourteen. Complete examples pass on both
  products. That is a lead, not just two endpoints: other fixtures may predate
  the same correction.
- **You settled `/db/LCOM-SEISMIC` honestly.** Building the real `/db/SPFC` +
  `/db/SPLC` prerequisite removed the missing-fixture explanation, Civil still
  refused `ANAL="RS"` with its own words, and you moved the entry to Gen-only
  write instead of inventing a Civil payload. It and `/db/SPLC` are now
  consistent - single-product writes pointing opposite ways.

One decision landed on top of that, and it opens the work below.

**An incomplete contract may now exist.** `promote_contract.py` used to refuse
any draft whose manual section had a variant table nobody could merge, so 22
drafts had no contract at all and their gap was not even countable. The manual
is not perfect and neither is the product, so a contract will not always be
either. Record the gap instead: every `extraction.unmergedTables` entry needs a
`resolution`, and `--resolution` supplies it at promotion because drafts are
regenerated build output. The old gate's real reason is kept - a contract
carrying `unmergedTables` is **not** used as an npm payload source, so promoting
one cannot narrow a published type. `/db/THIK` is the worked example: contract
present, gap recorded, npm generation byte-identical.

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

## Task 1 — promote the 22 drafts the old gate blocked

320 contracts, 64 drafts, 0 promotable. **22 of those 64 are refused only for
unmerged variant tables**, which is now a solvable refusal rather than a wall.

The refusal message names how many tables lack a `resolution`. Supply one:

```bash
python scripts/promote_contract.py db-cscs \
  --resolution "the manual names no wire discriminator for this table; left unmerged"
```

**Split the 22 before you write a single resolution.** Of the 116 unmerged
tables across them, **44 have a heading that names a selector value** - things
like `12-A. SECT — DB/User ("SECTTYPE": "DBUSER")`, `INPUT_METHOD = 0
(Simplified)`, `SHAPE = "ELEMENT" 일 때 추가 파라미터:`. Those are **parser
gaps, not manual gaps**. D3 shipped `variant.when` for exactly that shape in
2.7.3; the heading forms above are variations its parser does not recognise yet.

Writing "the manual names no wire discriminator" onto a heading that names one
puts a false claim into the source of truth. Do not do it. That is the one way
this task can go badly wrong.

**12 drafts have no value-naming heading at all — promote these first:**

```text
db-cscs(1)  db-epmt(5)  db-impf(2)  db-nlct-m1(3)  db-nspr(4)  db-sdis(3)
db-sdst(1)  db-spfc(11) db-splc(4)  db-stct(6)     ope-lcom-src(1)
view-resultgraphic(10)
```

(the number is how many tables each needs a resolution for). Read each heading
before writing its resolution — one sentence saying what that table is and why
it stays out is the point, and they will not all be the same sentence.

**10 drafts have at least one value-naming heading — teach the extractor first:**

| draft | value-naming tables | of |
| --- | ---: | ---: |
| `db-tdna` | 7 | 7 |
| `db-this-m1` | 7 | 8 |
| `db-this` | 6 | 16 |
| `db-elem` | 5 | 9 |
| `db-sect` | 4 | 4 |
| `db-swind` | 4 | 4 |
| `db-mvldpl` | 4 | 6 |
| `db-mvld` | 3 | 7 |
| `db-sseis` | 3 | 3 |
| `db-fimp` | 1 | 1 |

Extend `_explicit_variants` in `scripts/extract_contracts.py` to read those
heading forms, re-emit, and see what merges. A table that merges into a real
`variants` entry is strictly better than one carrying a resolution — the
contract then describes the endpoint completely and can own the npm payload
type again. Whatever still will not merge afterwards gets a resolution like the
first group.

**Stop and report** any heading you cannot read confidently. `db-mvldpl`'s
`Vehicle K/Military(LOAD_MODEL=2/3)` should become an `in: [2, 3]` condition —
if it does not, say so rather than forcing it.

Expected outcome you can check your run against: 12 drafts promotable straight
away, and some subset of the other 10 merging into proper variants. Contracts
320 -> at least 332.

**The generation check is `types.ts`, not the whole tree.** The guard protects
published payload types, because those are what break a caller. A contract may
legitimately change resource *metadata* — a display name, most often dash
typography, since the manual writes `—` where a hand-written fallback typed
`-`. `_contract_resource_mismatches` already normalizes that difference when it
compares, which is the project saying it is cosmetic. So: if
`packages/typescript/src/generated/types.ts` changes after promoting a contract
carrying `unmergedTables`, the guard is broken and that is a bug to report. A
label change in `resources.ts` is expected and fine.

## Task 2 — Python live write coverage

Measured today: **169 of 399 rows are write-verified, 230 are read-only.**
A read shows the route exists and parses. Every field-name, enum and default
defect found in this project so far was invisible to one.

The 230 read-only rows break down as `/DESIGN` 119, `/db` 79, `/post` 13,
`/ope` 12, `/view` 7. **206 of them have no fixture at all** — that seam is
where this work goes next, and writing a payload from the manual for an endpoint
nobody has exercised is a different, slower job than re-running one.

`schema/live-cases.json` holds 167 cases across 158 endpoints, **137 confirmed**
after your batch. **21 endpoints still recorded as `read`-level already carry a
fixture** — the payload is written, nobody has watched it pass:

```text
/db/ACTL  /db/CGLP  /db/DOEL  /db/EPSE  /db/EPST  /db/FBLA  /db/HAHS
/db/HECB  /db/HPCE  /db/MADO  /db/MVCT  /db/NLLP  /db/NLNK  /db/NLNK-M1
/db/RPSC  /db/SBDO  /db/STCT  /db/STRPSSM  /db/TDMF  /db/THMS  /db/WVLD
```

**Your own SDVI/SDVE result is the best thing to try here.** Both failed for
months on an incomplete fixture, not a broken endpoint. Check the rest of this
list the same way: does its fixture carry every field the manual's *current*
Request Example shows? Fixtures older than the manual's 2026-08-25 re-sync may
simply be short.

Two of these have a recorded product answer rather than a shape problem:
`/db/HECB`'s scratch beam cannot take an Element Convection Boundary, and Gen
accepted `/db/STCT` while dropping the submitted `iITER` on readback — that
second one is worth a closer look, it has the smell of a wrong field name.

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

## Task 3 — extend the npm live harness

Measured today: **about 20 endpoints have completed the full public-API CRUD
cycle** — the previous 14 plus `PNLD`, `EIGV` and `DCON`. Four populated
result tables have been read (`MASS_SUMMARY_X`, `REACTIONG`, `DISPLACEMENTG`,
`BEAMFORCE`), and five more endpoints have been created and deleted as analysis
prerequisites. That is roughly 20 against Python's 169 — still the widest gap in the
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

## Stop and report — do not decide these

The dry run offers **0 of 64 drafts** right now. The refusals break down as:

| count | reason | who |
| --- | --- | --- |
| 22 | unmerged variant tables with no `resolution` | **Task 1, yours** |
| 18 | N unresolved review notes | stop and report |
| 7 | no payload fields could be parsed | stop and report |
| 8 | a documented value proven wrong live, or a broken write path | stop and report |
| 7 | a Key cell naming two wire properties at once (`'DT" / "DB'`) | stop and report |
| 1 | plain-function parity surface not discovered | stop and report |
| 1 | no live-verification record in `docs/coverage.json` | stop and report |

The 22 are Task 1. The rest are not a mechanical batch:

- **A variant table whose heading names no value stays unmerged.** That is
  rule 2 working, and Task 1 records it rather than solving it. `/db/ELEM`'s
  `#### Wall` and `/db/NLNK`'s Angle/3Points/Vector are the standing examples:
  `TYPE="WALL"` is obvious to a human and is not written down anywhere. Do not
  infer one to make a draft merge — write the resolution and move on.
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

Baseline to beat: **899 Python tests, 55 npm tests**, all green at `31829dd`.

Commit messages: imperative subject, body explaining *why*. One task per commit.

---

## Settled — do not re-derive

- **All four contract-schema decisions are closed.** D1 `documentedDefaultNote`
  and D2 unstated requiredness shipped in 2.7.2; D3 array `when` with `in` and
  D4 `scalar`/`empty` arguments shipped in 2.7.3. `contracts/README.md` states
  each with its reasoning, and now also states the one-route section fold.
- **320 endpoint contracts, 64 drafts.** npm's surface coverage is 399/399 —
  the gap is live evidence, not reach.
- **A contract carrying `extraction.unmergedTables` is never an npm payload
  source.** That guard is what makes promoting an incomplete contract safe, and
  it is checked by a test. If `npm run generate` produces a diff after you
  promote one, the guard is broken — report it, do not work around it.
- **`docs/coverage.json` carries one row per result table, not per route.**
  `/DESIGN/RC/KDS-41-20-2022/TABLE` has three rows and
  `/DESIGN/SRC/AIK-SRC2K/TABLE` two, because each `TABLE_TYPE` returns its own
  table and verifying one does not verify the others. The contracts fold those
  same sections into one endpoint each. Both are right; do not "reconcile" them.
- **Six manual defects are registered** in `docs/manual_defects_register.md`,
  labelled by which side owns the fix, and MD-06 now quotes the server verbatim.
  Append new ones there; send nothing.
- **`/info` is a `/db/*` facility.** All 147 `/DESIGN/*` resource-product pairs
  404 on introspection while the endpoints answer a plain GET, so a design-code
  contract has two permitted sources rather than three and can never carry
  `provenance: info_schema`. Three `/db/*` endpoints are the same way, all Civil
  Hyper-S: `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`, `/db/IEHG-TRUSS-M1`.
- **Both SDKs were swept read-only across all 549 declared resource-product
  pairs on 2026-09-01** and agreed on every one, and all 57 single-product
  resources 404 on the product they do not declare. Product gating is settled in
  both directions — do not re-derive it.
- **`/db/FBLA`'s shared table** — `= 1 or 2` alongside `= 1` and `= 2` — folds
  into both branches at generation time rather than forming a third union
  member. That is decided and implemented.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Omitting them ends the
  session on both products. Both SDKs fill them in, and the npm side is now
  live-confirmed to do so on a real POST.
