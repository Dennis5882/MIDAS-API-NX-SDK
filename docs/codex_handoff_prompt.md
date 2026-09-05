# Codex task prompt — mechanical work only

Updated 2026-09-05 at `HEAD_SHA`. **2.7.8 is published** on both registries; the
next number is the author's call, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Tasks 1, 2 and 5 are done** — kept below for what they settled and what
they left open. **Task 4 is what is left and it needs a live session**; Task 3
is now a by-product of it rather than a task of its own.

## Your last batch, and what it settled

All four commits landed, and two of them changed what this repo believes.

- **The `/info` standing check** (`d82869f`) is in CI as a per-endpoint ceiling
  and is already earning its keep — five endpoints were closed against it the
  next day and the ceiling *tightened* rather than lowered, which is only
  possible because you keyed it per endpoint rather than by a total.
- **The two `TABLE_TYPE` probes** (`b8d862b`) overturned a shipped value. The
  majority reading was right about `BEAMFORCESTP` and **wrong** about the
  surface-spring reaction type: both products refuse `REACTIONSURFACESPRING`
  and accept `REACTIONLSURFACESPRING`. Both SDKs had shipped the refused string
  for as long as the constant existed. Fixed and released in 2.7.8. The general
  finding is now a rule: **a wire value is not a majority opinion**, and a
  `describes: table_type` defect can no longer be marked resolved on anything
  but a live check.
- **`/db/STRPSSM` read → write** (`51ff95d`). That fixture had failed
  `Wrong Field` since 2026-08-16 under a recorded guess that it needed a genuine
  PSC/RC section. It needed `Y` and `Z`. Reading the recorded reason and
  distrusting it is the whole job.
- **The npm CRUD batch** (`1686a93`) took npm evidence 23 → 32 endpoints, and
  the part worth repeating is the part you *refused* to claim: thirteen
  `REGRESS` prints you did not report as a package regression, with the reason
  written down. **You were right**, and it took two passes to actually fix:
  sharing the base model closed the common prefix, and your own recheck found
  the rest — the per-tier seeds. Both halves are in. See Task 1.

## What moved since your batch

- **The base model is in the shared fixture** (`7d2698e`). Your thirteen
  `REGRESS` cases were blocked by a real hole: Python built the common model
  inside `_seed_model` with inline literals, so only Python could replay it,
  while `schema/live-cases.json` claimed in its own docstring to be the source
  both harnesses read. It now carries `baseModel`, nine ordered steps, and
  `_seed_model` executes the list it emits so the two cannot drift.
  `live-crud.mjs` replays it after `/doc/NEW`. **Fixture version 3 → 4.**
- **The `/info` sweep's small-count tail is closed** (`c8be182`). Eleven
  endpoints → six, and the six that remain are the large ones where the count
  means nothing. `SPECIAL_LANE_ITEMS` reached the four `/db/LLAN*` siblings, and
  `/db/MVCTch` gained nine fields **its manual documents and this repo could not
  read**: a `FREQ` table with two Key/설명 column pairs where the parser reads
  only the first, plus a `BTYPE` stated in the bold sentence above each
  `BRIDGE` table. MD-50.
- **A third dropped-row cause** (`012d5b4`): `second key column ignored`, at 3.
  Every table in all 27 chapters was scanned and there is exactly **one** with
  two Key columns, so the parser is deliberately not being taught that shape —
  code that runs once is code nobody maintains. The count is the guard instead.
- **2.7.7 and 2.7.8 shipped.** 2.7.7 was the largest breaking npm release so
  far: sixty payload types lost the `Assign` envelope, one interface was
  renamed, eighteen records changed shape. **A fixture built from memory rather
  than from a contract is now wrong.**

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 1016 passed
ruff check src tests scripts && mypy      # clean; 41 source files
python scripts/validate_contracts.py      # OK; 381 endpoints, 4916 fields,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check
                                          # OK - differences did not grow
python scripts/info_baseline.py --divergence --check
                                          # OK - tagging remains complete
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # blank 71, short row 20,
                                          # second key column 3
python scripts/live_crud_check.py --check-cases        # silent; exit 0
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # 304 resources (301 by contract),
                                          # 764 payload types; no drift; 70 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 173 write / 226
read.** `schema/live-cases.json` is **version 5** and holds **167 cases, 144
confirmed**, plus **9 base-model steps**, **46 named seeds** and **3
unsupported seeds** that block 4 cases on the npm side by design. npm live evidence stands at **47 `/db`
endpoints**. Drafts: 3, all the IEHG trio, all refused for a reason that will
not go away — that is the finished state, not a backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## Task 1 — DONE (2026-09-05), and what it turned up

Closed live on both products. Fixture version 5, npm built from 2.7.8 sources,
both documents confirmed empty with each product's **own** MAPI key first --
an earlier check in that session read one key for both products and proved
nothing, while `verify_connection()` answered `connected` either way.

The fifteen: `/db/TDMT`, `/db/GSTP`, `/db/CNLD`, `/db/BMLD`, `/db/CONS`,
`/db/ESSF`, `/db/SECF`, `/db/TSGR`, `/db/TDME`, `/db/IFGS`, `/db/THGC`,
`/db/THFC`, `/db/SPLC`, `/db/LCOM-GEN`, `/db/LCOM-CONC`.

| harness | Gen | Civil |
| --- | --- | --- |
| npm `live:crud` | 15 PASS | 15 PASS |
| `live_crud_check.py` | 15 PASS | 14 PASS, 1 blocked |

**The two you reported now pass on both harnesses.** `/db/TDMT` and `/db/GSTP`
failed `id 3 missing after POST` because npm replayed no tier seed; version 5
emits them and the symptom is gone.

One thing surfaced that was not yours and not the change's: selecting extras4
and extras5 together on Civil answers `Key Already Exist` on `/db/SPLC`.
extras4's Civil-only `lcom_seismic_splc` seed creates `/db/SPLC` id 1 and
extras5's Civil case owns the same id, and the Python runner executes every
seed step of a selected tier whatever the cases' `needs` say. Alone, the case
passes on the same product in the same session. Asking for a different id is
not the fix -- this load-case family renumbers a requested key to the next free
slot, so a case asking for 2 would land at 1 when extras4 was not selected.

What changed is the classification: `_run_case` now checks whether the id is
already present and reports `BLOCK` (exit 3, fixture problem) rather than
`REGRESS` (exit 1, treat as an SDK defect), verified live in both directions.
**The collision itself is still open and still needs a decision** -- see the
live notes. Nothing about the endpoint is in doubt.

---

## Task 2 — DONE (`3c47a7a`), nothing left here

You built it and it is correct. `--divergence --check` is in CI beside the
sweep, `untagged` fails on 1 rather than tolerating a baseline, and `absent`
is a per-endpoint ceiling holding `/db/SPLC`'s 15.

Two things were added on top rather than sent back:

- **The guard was verified end to end.** The unit tests exercise
  `_check_divergence` with synthetic counts, which proves the comparison and
  not the pipeline feeding it. `/db/ACTL`'s `CLATS` had its `products` tag
  removed, the real command exited 1 naming that endpoint, and the tag was
  put back. Worth doing for any check whose whole job is to fail: a guard
  that has never fired on real input is a guard nobody has seen work.
- **Two ceiling tests.** `untagged` rejection was covered and growth was not,
  so a new absent field and an eleventh divergent endpoint now both have a
  test. The sibling check had them; this one should match.
## Task 3 — npm live evidence, now a by-product rather than a task

**Started; 32 → 47 on 2026-09-05.** Task 1's fifteen were recorded as they
passed, which is how this should keep going: it is the record kept while Task 4
runs, not a separate errand.

`packages/typescript/scripts/live-crud.mjs` reads the same
`schema/live-cases.json` Python does. The gap is the *record* — npm-side live
verification exists only as prose, inventoried in
`docs/npm_live_evidence_scratch.md` at **47 `/db` endpoints** plus four
result-table operations.

The pool is the endpoints Python has confirmed (144 cases) that npm has not run.
Batches of at most 8, both products, each result recorded in
`docs/live_verification_notes.md` in the existing style. Prefer endpoints whose
npm adapter does something beyond generated metadata.

`/db/GRUP` will keep being refused before its write: it has no DELETE and the
harness deliberately refuses a case it cannot clean up. Correct behaviour, not a
gap — do not work around it.

**Where to record it structurally is Claude's call.** If running it makes it
obvious that a field in `docs/coverage.json` would help, say so in your report
and leave the schema alone.

---

## Task 4 — `/db` write coverage (the long-running background task)

**72 `/db` endpoints are still read-level**, down one since your batch — you
moved `/db/STRPSSM`. They split:

- **17 already have a live case** that has not passed:
  `/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
  `/db/HPCE`, `/db/MADO`, `/db/MVCT`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`,
  `/db/RPSC`, `/db/SBDO`, `/db/STCT`, `/db/TDMF`, `/db/WVLD`
- **55 have no case at all**, the biggest coherent cluster being 19
  moving-load/lane endpoints in one chapter.

**Start with the 17, and read `/db/STRPSSM` as the model for how.** Its recorded
reason for failing was a specific, plausible, wrong guess that had stood three
weeks. Treat every recorded reason in `docs/live_verification_notes.md` as a
lead, not a conclusion.

**All 17 were re-run on build 09/02/2026 and all 17 still fail** — the table of
what each answers is in the live notes. Two were probed field by field and both
came back the same, so start from the two things that pass first:

- `python scripts/check_fixture_contract.py` names, per endpoint, every key the
  payload sends that the contract does not license and every `required` key it
  omits. Five of the 17 have one. Held in CI as a baseline, in both directions.
- `/db/ACTL` is **not** one to spend time on. Three payloads derived from the
  contract — including one carrying only its two `required` fields — all answer
  `Wrong Field` on Gen, while Civil accepts every one and then refuses to
  persist `TOL`. Product behaviour on both sides, not coverage.

That script's other list is worth more than the fixture side and is **not**
yours: 64 disagreements across 18 endpoints sit on cases confirmed live, where
the product accepted the payload and the contract is what is behind. Closing
one takes a permitted source. Report, do not merge.

**Five of the 17 changed shape in 2.7.7 or 2.7.8 — build from the contract, not
from memory:**

| endpoint | what moved |
| --- | --- |
| `/db/RPSC` | longitudinal reinforcement is `MBARS[].MBAR_ITEMS[]`, not a root `MBAR_ITEMS`; `SBAR_ITEMS` stays at the root, the pair really is asymmetric (MD-40) |
| `/db/SBDO` | `AXIS_VECTOR` is an array of numbers, not a number |
| `/db/EPSE` | the two products declare four fields between them that the other does not — `LOAD_TYPE`/`WIDTH` on **Civil**, `LOADING_AREA_GROUP`/`SEL_TYPE` on **Gen**. A fixture sending all four fails on both (MD-46) |
| `/db/MVCT` | gained eight Russia-code fields the manual states in a sentence after its table |
| `/db/STCT` | its `unmergedTables` now itemises 62 names; the record is wider than the old fixture assumed |

The lane cluster in the 55 also moved: `/db/LLAN`, `/db/LLANch` and `/db/LLANid`
take `{COMMON, LANE_ITEMS}`, not a flat record — the server never accepted the
flat one — and all four `/db/LLAN*` now carry `SPECIAL_LANE_ITEMS`.

Per endpoint, in batches of at most 8:

1. Read the manual chapter and this endpoint's entry in
   `docs/live_verification_notes.md` **first**.
2. Build the fixture from the contract — all 17 have one — or from the manual's
   own Request Example. **Never hand-write a payload.**
3. Run `python scripts/live_crud_check.py --tier <tier> --product gen` and the
   same for `civil`, from a document the author has confirmed is empty.
4. Classify honestly: **passed** → `confirmed=True`, `level: "write"`,
   `outcome`, the builds, and `live_verified.date` set to the day the write
   actually happened, all on the entry that did the write. **Fixture problem** →
   fix and rerun. **Failed the same way with the documented payload** → leave it
   read-level and write down everything you tried.
5. `python scripts/live_crud_check.py --emit-cases`, then
   `python scripts/gen_roadmap.py`, then update `PLAN.md`'s §2 figures and its
   "Last updated" line in the same commit.

**Do not flip `confirmed` to silence a failure**, and do not report an
unconfirmed failure as an SDK defect. Across every run so far each one resolved
to a fixture, a wrong documented value, or a product bug.

---

## Task 5 — DONE (`8423d9e`), and the answer was not the expected one

Report: `docs/unmerged_tables_against_info.md`, regenerated by
`scripts/report_unmerged_tables.py` (`--check` keeps it honest).

**Of the 534 names on endpoints `/info` answers for, 533 are declared.** The one
that is not is `/db/ELEM`'s `W_CON`. The other 68 sit on `/view/RESULTGRAPHIC`
and `/ope/LCOM-SRC`, where `/info` is not served at all — one source because a
second cannot exist, which is a different finding from one that is absent, and
counted separately for that reason.

So "does a second source exist" was the wrong question; almost always it does.
The axis that separates these tables is **whether the second source agrees on
shape**: 53 of the 93 tables have one `/info` object holding every name in them,
25 have all their names declared under no common parent. Counting distinct
parents would have measured how common the leaf names are rather than the
table's shape — `NAME` repeats across every branch of `/db/MVHL` — so each
scattered table also names the object covering the most of it, which separates
one stray name (`VEH_PL` covers 13 of 14) from a table `/info` spreads evenly.

Merging any of them is still a judgement call and still Claude's.

<details>
<summary>Original brief</summary>

**Offline. Measure and report; change nothing.**

Nineteen contracts declare part of their field list missing through
`extraction.unmergedTables`, and since 2.7.7 each entry records the `fieldNames`
that table holds, so the field-parity waiver is per-name. That is **602 names**
the SDKs may ship without any contract accounting for them individually:

| endpoint | tables | names | | endpoint | tables | names |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| `/db/MVHL` | 8 | 115 | | `/db/MVLD` | 4 | 21 |
| `/db/SPFC` | 11 | 74 | | `/db/SDIS` | 3 | 21 |
| `/view/RESULTGRAPHIC` | 10 | 63 | | `/db/TDME` | 7 | 19 |
| `/db/STCT` | 6 | 62 | | `/db/IMPF` | 2 | 12 |
| `/db/THIS` | 10 | 41 | | `/db/NSPR` | 4 | 12 |
| `/db/ELEM` | 9 | 31 | | `/db/THIK` | 1 | 11 |
| `/db/EPMT` | 5 | 29 | | `/db/CSCS` | 1 | 9 |
| `/db/MVLDpl` | 4 | 27 | | `/ope/LCOM-SRC` | 1 | 5 |
| `/db/SPLC` | 4 | 25 | | `/db/THIS-M1` | 1 | 2 |
| `/db/NLCT-M1` | 2 | 23 | | | | |

Merging any of these takes reading the manual section and deciding what the
table means, which is not yours. **The measurement that would make that work
tractable is**, and nobody has done it.

For every one of the 602 names, report whether `schema/info-baseline.json`
declares it on that endpoint, and at what path. Group the output **per unmerged
table**, not per name, because the table is the unit a decision gets made about.
Per table give: how many of its names `/info` declares, how many it does not,
and whether the declared ones agree on nesting.

Reuse `info_baseline.py`'s own loader and `validate_contracts.py`'s contract
loader rather than re-parsing, so the report cannot claim a name the tools
disagree about.

**Why it is worth running.** A table whose every name `/info` also declares has
two independent sources and is a candidate to merge. A table with names `/info`
declares nowhere rests on the manual alone and needs its section read. Right now
those two look identical from outside, so the 602 are one undifferentiated pile
and the largest of them — `/db/MVHL` at 115 — is untouchable for that reason
alone.

Put the report in `docs/`; it is a working document someone will reopen, not
terminal output. **Do not merge a table, do not edit any contract, and do not
draw a conclusion about what a table means.** Say which tables have a second
source and which do not.

</details>

---

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session.** For anything
  that writes, confirm both documents are empty: `GET /db/NODE` and
  `GET /db/ELEM` answer `{"message": ""}`.
- **`--save-dir` is required and never inferred.** `verify_connection()["user"]`
  is the MAPI account's email, not the NX host's Windows profile. `C:/temp`
  exists on both machines; the author created it and handles it himself.
- **`verify_connection()` cannot prove a session is alive.** It answers
  `"connected"` through the relay while a modal dialog holds the product. Use a
  real `GET /db/NODE`, as your crash sweep did.
- **Model extensions**: pre-NX Gen `.mgb` / Civil `.mcb`; **NX Gen NX `.mgbx` /
  Civil NX `.mcbz`**. `/doc/STAGAS` is the exception that wants legacy `.mcb`.
  This repo got Civil's wrong twice — do not re-derive it.
- **`/doc/NEW` discards unsaved work and has crashed Gen NX.** Three harnesses
  call it: `live_smoke.py`, `live_crud_check.py`, and `live-crud.mjs`.
  `--no-save-before` removes the npm harness's checkpoint, not its `/doc/NEW`.
- **A GET can still pop a modal dialog** if the open document lives under
  `Program Files` or another path a standard account cannot write to.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success. Error
  bodies also arrive under 201.
- **`"Wrong Field"` from a `/db/*` write usually means a bad *value*, not a bad
  field name.** Vary the enum value before you vary the fields.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- **Never commit a GET response body.** It is the author's model contents.
  "Returned N rows" in a report is fine; the rows are not.
- Leave both models empty, and say so in the note.

## Not yours, and why

- **Merging any `unmergedTables` table.** Task 5 measures them; deciding what a
  table means takes reading its section.
- **The three uncontractable endpoints.** `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`
  and `/db/IEHG-TRUSS-M1` have no manual table and 404 on `/info`. That ground
  has been covered twice, in every casing tried. Do not look for a fourth
  source.
- **The ten `/post/*` routes with no endpoint contract** — `/post/PM`,
  `/post/STEELCODECHECK` and the eight `*DESIGNFORCES` routes.
- **The 20 short manual rows** that drop for omitting a leading No. cell.
  Aligning a short row to its header is a judgment about table shape.
- **Teaching the extractor a second Key column.** Deliberately not done: there
  is exactly one such table in the whole manual, and
  `report_dropped_manual_rows.py` now counts it so a second one fails CI. If
  that count grows it becomes worth writing — and that is a call to report, not
  a threshold to act on.
- **Promoting drafts and writing `resolution` text.** If a draft looks
  promotable, report it instead.
- **Editing `contracts/endpoints/*.yaml` by hand** — any contract's `fields`,
  `variants`, `enum`, `surface` or `extraction`.
- **`docs/manual_defects_register.md` beyond appending a row with evidence.** No
  manual-repo edit, no MIDASIT contact, no Jira issue.
- **Version bumps and releases.** The shared number is the author's call.

## Settled — do not re-derive

- **A wire value is not a majority opinion.** Your own probe is the proof: the
  same 2-1 reading was right about `BEAMFORCESTP` and wrong about
  `REACTIONLSURFACESPRING`. Three documents agreeing is three transcriptions of
  one source. A `describes: table_type` defect may be marked resolved only on a
  live check, and a test enforces it.
- **`/info` is neither a superset nor a subset of what the server accepts.** It
  declares `/db/POSL`'s `CODE` on Civil, refused live even as an empty string,
  and omits `/db/STBK`'s `LCNAME`, which a confirmed round trip sends
  successfully. Where `/info` and a live round trip disagree, the round trip
  wins.
- **`products: [civil, gen]` says the route answers on both, never that the
  record is the same.** Ten of 177 declare different schemas. MD-46.
- **A contract carrying `extraction.unmergedTables` is never an npm payload
  source.** A test checks it. If `npm run generate` produces a `types.ts` diff
  after a promotion, the guard is broken — report it, do not work around it.
- **`check_field_parity` runs one direction only.** A contract naming more than
  a TypedDict is the intended state; a TypedDict naming more than its contract
  is the defect. A TypedDict is the subject that check measures, never a source.
- **A `requirement: required` carrying an `appliesWhen` is a branch's
  requirement, not the payload's.** Fixed in 2.7.5; do not restore it.
- **A variant union is closed only where the contract proves it.** Otherwise
  generation emits a trailing member carrying the remaining values. Do not tidy
  them away.
- **A list the manual's own description outsizes is not an enum.** A count or
  range stated about the list (`19종 (D4 ~ D57)`) disqualifies it.
- **A ledger entry must not contradict its own prose.**
  `tests/test_live_cases.py` fails if a `method` describing a completed write
  sits beside `level: read`. Fix the entry, never the test.
- **`ROADMAP.md`'s version table is not a list of sessions.** An older date
  beside a newer build is normal; only move `date` when the *level* moves.
- **`/info` is a `/db/*` facility.** All 147 `/DESIGN/*` pairs 404 on
  introspection, so a design contract has two permitted sources rather than
  three, and `check_field_parity` is the only automated field check that family
  gets.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Its crash stopped
  reproducing on build 09/02/2026, which is not the same as being fixed — an
  uninitialized read is exactly the defect that hides when the memory happens to
  be zero.

## Before every commit

Run the full set for each surface you touched — the block under "Measured
starting state" is the whole list. `git diff --check` too, and watch your line
endings: several files here have picked up mixed CRLF/LF from appends, and one
such append split the defects register into two tables with the rows out of
order.
