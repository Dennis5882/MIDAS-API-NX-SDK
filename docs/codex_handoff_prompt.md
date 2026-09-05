# Codex task prompt — mechanical work only

Updated 2026-09-05 at `012d5b4`. **2.7.8 is published** on both registries; the
next number is the author's call, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Task 1 is the one that matters most and it needs a live session.** Task 2 is
offline and you can start it right now.

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
  written down. **You were right, and it has been fixed** — see Task 1.

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
python -m pytest -q                       # 1001 passed
ruff check src tests scripts && mypy      # clean; 41 source files
python scripts/validate_contracts.py      # OK; 381 endpoints, 4916 fields,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check
                                          # OK - differences did not grow
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # blank 71, short row 20,
                                          # second key column 3
python scripts/live_crud_check.py --check-cases        # silent; exit 0
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # 304 resources (301 by contract),
                                          # 764 payload types; no drift; 60 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 173 write / 226
read.** `schema/live-cases.json` is **version 4** and holds **167 cases, 144
confirmed**, plus **9 base-model steps**. npm live evidence stands at **32 `/db`
endpoints**. Drafts: 3, all the IEHG trio, all refused for a reason that will
not go away — that is the finished state, not a backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## Task 1 — prove the base model actually unblocks your thirteen

**Live. Destructive: this calls `/doc/NEW`.** Needs the author's go-ahead and a
document they have confirmed is disposable.

### Why this task exists

You reported thirteen `REGRESS` prints and refused to call them a package
regression, and the reason you wrote down was correct. The fix is in — but
**nobody has run it against a product**, and a fix to a live harness that has
never been run live is a claim, not a result. It was written by someone with no
live session; this is the half of the seam only a live run closes.

### What to run

Exactly the thirteen, plus the two that failed for the neighbouring reason:

```
/db/CNLD, /db/BMLD, /db/CONS, /db/ESSF, /db/SECF, /db/TSGR, /db/TDMT,
/db/GSTP, /db/TDME, /db/IFGS, /db/THGC, /db/THFC, /db/SPLC
```

plus `/db/LCOM-GEN` and `/db/LCOM-CONC`, whose fixtures referenced load case
`DL` — the base model's `/db/STLD` step creates it, so those two should now
resolve for the same reason.

In batches of at most 8, on **both** products:

```bash
npm run live:crud -- -- --product gen --endpoints /db/CNLD,/db/BMLD,... \
  --save-dir <a writable directory on the NX machine>
```

The harness prints `BUILT base model (9 steps)` after `CREATED empty scratch
document`. If that line is missing the fixture is stale — re-emit with
`python scripts/live_crud_check.py --emit-cases` and say so in your report.

### What the outcomes mean

- **`PASS`** — the hole is closed. Record it and extend
  `docs/npm_live_evidence_scratch.md`, which is Task 3 anyway.
- **`REGRESS` still, on a *different* error** — the interesting case, and a
  genuine finding: the base model built, so a missing precondition is no longer
  the explanation. Report the error verbatim; do **not** relabel it a package
  regression on your own, because the third possibility below is real.
- **The base model itself fails to build** — a step's records did not store.
  Stop the batch and report which step and which id. That is a defect in
  `7d2698e` and not yours to fix.

Also confirm the negative: **Python's own runs must be unchanged.** Put the same
selection through `python scripts/live_crud_check.py --endpoints ...` on both
products. `_seed_model` now executes the emitted list instead of inline
literals, and the two are supposed to be identical; a Python-side difference
would mean the refactor changed the model.

**Stop and report if** the two harnesses now disagree about any case both can
run. That is exactly what the change was supposed to make impossible.

---

## Task 2 — guard the product-divergence tagging the way you guarded the sweep

**Offline. Start here if no live session is available.** Same shape as the check
you built in `d82869f`, so this should be short.

### Why this task exists

`scripts/info_baseline.py --divergence` answers a question the other sweep
cannot: **`products: [civil, gen]` says the route answers on both, never that
the record is the same.** Ten of the 177 both-product endpoints declare
different schemas, so a field listed without its own `products` tag is a claim
about both products that is sometimes false. That is MD-46, and 72 npm field
comments came out of it.

The tagging is currently **complete** — `untagged` is 0 across all ten — and
nothing holds it there. A contract gaining a field on a divergent endpoint
without a `products` tag would silently re-introduce exactly the false claim
MD-46 records, and only someone remembering to run `--divergence` would notice.

### What to build

Add `--check` support to `--divergence`, backed by a committed expectation, and
wire it into `.github/workflows/ci.yml` beside your existing
`--against-contracts --check` step.

The current state, which is what your expectation should record:

```text
endpoints answering /info on both products: 177
of those, declaring different schemas: 10
untagged (a contract claims both products; /info contradicts it): 0
absent  (no contract records the field at all): 15
```

All 15 `absent` are on **`/db/SPLC`**, whose field list is already declared
incomplete through `unmergedTables` — 2 Civil-only (`CQCRATIO`, `iANGLETYPE`)
and 13 Gen-only. A known, recorded state, not a gap to close here.

Shape it like the other check, and let the two differ where the questions
differ:

- **`untagged` must be 0 and stay 0.** This is not a ceiling that may drift
  down; it is already at the floor, and any value above it is a false claim
  being published. Fail on 1.
- **`absent` is a per-endpoint ceiling**, like the other check: it may fall for
  free, and growth must be reviewed.

### Done when

`python scripts/info_baseline.py --divergence --check` exits 0 on this tree,
exits non-zero with a readable diff when you fabricate an untagged field to test
it, and CI runs it. Add a test beside `tests/test_info_baseline.py`'s existing
three.

**Not yours:** closing any of the 15 `absent` fields on `/db/SPLC`. That
contract is deliberately incomplete and merging its tables is contract work.

---

## Task 3 — npm live evidence beyond 32, now that it can get there

Do this after Task 1: its fifteen endpoints are the first fifteen of this, and
the base model is what makes the rest reachable at all.

`packages/typescript/scripts/live-crud.mjs` reads the same
`schema/live-cases.json` Python does. The gap is the *record* — npm-side live
verification exists only as prose, inventoried in
`docs/npm_live_evidence_scratch.md` at **32 `/db` endpoints** plus four
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

## Task 5 — measure the 602 waived names against `/info`

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
