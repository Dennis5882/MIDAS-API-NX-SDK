# Codex task prompt — mechanical work only

Updated 2026-09-02 at HEAD `a93069b`. **2.7.4 is published** on both
registries; the next number is the author's call, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

## What moved since your last batch

Nothing in your half changed, but three things in the tree did:

- **2.7.4 shipped** to PyPI and npm on 2026-09-02, including the three
  discriminated-union conversions and the fixes for types that had been
  outlawing documented values.
- **`extract_contracts.py` was deleting table rows** that contain GFM's
  escaped pipe (`\|`). Ten rows across three chapters, one of them
  `/ope/LCOM-GEN`'s **required** `CODE_SELECTION`. Five contracts gained the
  recovered fields, five optional fields reach the npm declarations, and
  MD-10 dropped from nine sections to four. Task 3 below is the standing
  check that should have caught it.
- **`/db/EPMT` and `/db/ELEM` were reconciled** against their own JSON
  Schemas. EPMT's contract had claimed the manual states no wire
  discriminator for its six model objects; it does, and all six are now
  conditional fields on `MODEL_TYPE`.

Task 1 and Task 2 are unchanged and are still the main work.

## What your last three batches showed

`801abe0` and `d6d5ca1` are the model to repeat. The best results in both are
the ones you *refused* to claim, and the ones you re-classified downward:

- `/db/HAHS` and `/db/HECB` went read → write once the fixture built a real
  eight-node SOLID. `/db/HECB` kept `ITEMS[].ID=1` because the manual calls it
  a serial number, and the earlier "element no. 1" error turned out to be the
  fixture, not evidence to reinterpret the field.
- `/db/HPCE` stayed read. You tried the SOLID's 8 nodes, the manual example's
  6, then 4 and 2, got the identical `Wrong Key` every time, and **did not
  invent a wire shape** to make it pass.
- `/db/CSCS` stayed read. The manual's only COMPOSITE sample omits the
  dimensions needed to build the prerequisite section, and you did not supply
  them from either SDK.
- `/db/SPLC` and `/db/THMS` were the opposite finding, and just as useful: a
  Gen-only `Unknown Error` and a cross-product `Wrong Field` both turned out to
  be **abbreviated fixtures**, not product behaviour. SPLC was missing eight
  fields of the manual's no-damping example, THMS its Y/Z functions and every
  arrival-time field. A standing product finding is worth re-testing against
  the complete documented payload before anyone reports it.

Two things to carry forward, both from writing results down rather than
getting them:

- **`d6d5ca1` credited the wrong endpoint with a write.** THMS did the round
  trip; HPCE got `level: write` while its own method still ended "Left at
  level: read" and its case was still `confirmed=False`. Neither needed
  outside evidence to spot - each entry contradicted itself - so a test now
  reads exactly that out of `docs/coverage.json`. A ledger entry is five
  fields plus prose, and a batch edits several entries at once.
- **`92149a4` produced three defects, all from writing down what the manual
  *means***: `/db/ELEM` promoted with `STYPE: 1` twice, `/db/FIMP` declaring a
  three-level object as ten flat fields, and a union saying `HYS_MODEL` could
  only be `"KPM"`. The extractor and validator now refuse those shapes.

The conclusion this prompt is built on: **live-harness work is yours; contract
promotion is not.**

## Measured starting state

Run these first and confirm you see the same numbers. If any differ, say so
before starting — it means something moved under you.

```bash
python -m pytest -q                       # 920 passed
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK, 337 contracts, 3,174 fields
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift, 55 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 172 write / 227
read.** `schema/live-cases.json` holds **167 cases, 143 confirmed**.

Contract drafts — clear and re-emit before judging anything about them.
`contracts/drafts/` is git-ignored build output, and a stale copy has misled a
run before:

```bash
rm -rf contracts/drafts
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all     # 47 drafts
python scripts/promote_contract.py --all --dry-run          # 0 promoted, 47 refused
```

**Zero of the 47 are promotable, and that is expected.** Grouping the refusals
by their stated reason: **49 unresolved review notes across 21 drafts** (all
judgment - an enum whose values live elsewhere, a type that has nested
children, a condition the manual gestures at), 7 with no parseable payload
fields, 8 whose key cell names two wire properties at once, and the rest in
`NEEDS_HAND_REVIEW` because their documented payload is already measured wrong
live. None of that is yours.

> An earlier version of this prompt said "124 blocking review notes across 31
> drafts". That number was never measured this way and was wrong; the figure
> above is what `promote_contract.py --all --dry-run` actually prints. If a
> number in this file disagrees with a command's output, the command wins -
> say so in your report.

---

## Task 1 — `/db` write coverage (the main task)

73 `/db` endpoints are still read-level. They split cleanly:

- **18 already have a live case** that has not passed:
  `/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
  `/db/HPCE`, `/db/MADO`, `/db/MVCT`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`,
  `/db/RPSC`, `/db/SBDO`, `/db/STCT`, `/db/STRPSSM`, `/db/TDMF`, `/db/WVLD`
- **55 have no case at all.** The biggest coherent cluster is moving-load and
  lane — one manual chapter, 19 endpoints: `/db/LLANch`, `/db/LLANid`,
  `/db/LLANop`, `/db/LLANtr`, `/db/MLSP`, `/db/MLSR`, `/db/MVCTbs`,
  `/db/MVCTid`, `/db/MVCTtr`, `/db/MVHLtr`, `/db/MVLDbs`, `/db/MVLDch`,
  `/db/MVLDeu`, `/db/MVLDid`, `/db/MVLDpl`, `/db/MVLDtr`, `/db/SINF`,
  `/db/SLAN`, `/db/SLANch`, `/db/SLANop`

**Start with the 18.** A fixture that exists is cheaper to triage than one you
have to write, and three of them (`/db/HPCE`, `/db/STCT`, `/db/FBLA`) already
have recorded findings to build on rather than rediscover.

For each endpoint, in batches of at most 8:

1. Read the manual chapter and this endpoint's entry in
   `docs/live_verification_notes.md` **first**. Several already have a recorded
   reason for failing.
2. Build the fixture from the manual's own Request Example. **Never hand-write a
   payload** — copy the documented one, or an existing confirmed case's.
3. Run `python scripts/live_crud_check.py --tier <tier> --product gen` and the
   same for `civil`, from a document the author has confirmed is empty.
4. Classify honestly and record it:
   - **passed** → `confirmed=True`, `level: "write"`, `outcome`, the builds,
     and `live_verified.date` set to **the day the write actually happened**.
     All of them, on the entry that did the write. In `d6d5ca1` the SPLC/THMS
     batch left `/db/THMS` at `read` under a method describing its own
     completed round trip, and raised `/db/HPCE` to `write` without touching
     its method, which still ends "Left at level: read". A test now fails on
     either shape, so run the suite before committing a batch.
   - **failed on a fixture problem** → fix the fixture, rerun.
   - **failed the same way with the documented payload** → leave it read-level
     and write down everything you tried, as you did for `/db/HPCE`.
5. `python scripts/gen_roadmap.py`, then update `PLAN.md`'s §2 coverage figures
   and its "Last updated" line in the same commit.

**Do not flip `confirmed` to silence a failure**, and do not report an
unconfirmed failure as an SDK defect. Across every run so far, each one resolved
to a fixture, a wrong documented value, or a product bug.

Expected outcome to check against: each endpoint you finish moves write up by
one and read down by one, and `ROADMAP.md` regenerates with no other change.

## Task 2 — record what the npm package has actually proven

`packages/typescript/scripts/live-crud.mjs` already reads the same
`schema/live-cases.json` Python does and takes any endpoint through
`--endpoints`, so this needs no new harness. The gap is the *record*:
**npm-side live verification exists only as prose**, in about a dozen passages
of `docs/live_verification_notes.md`. Nothing in `docs/coverage.json` or
anywhere else says which endpoints the built npm package has been run against,
so "how much of the npm surface is live-proven?" cannot be answered without
reading 8,000 lines.

Two steps, in order:

1. ~~**Read out what is already claimed.**~~ **Done** —
   `docs/npm_live_evidence_scratch.md` has it: **23 `/db` endpoints and 4
   result-table operations, 27 npm public-API operations**, each traced to
   the passage that claims it, with the rejections and harness calls
   (`/doc/NEW`, `SAVEAS`) deliberately excluded. Spot-checked against the
   notes and correct. This prompt guessed "under ten" from a crude grep over
   paragraphs mentioning the npm package; reading them properly more than
   doubled it.
2. **Then extend it by running.** Pick endpoints Python has confirmed but npm
   has not, in batches of at most 8:

   ```bash
   npm run live:crud -- -- --product gen --endpoints /db/AAA,/db/BBB \
     --save-dir <a writable directory on the NX machine>
   ```

   `scripts/live_crud_check.py` now takes the same `--endpoints`, so a batch
   can be run through both packages against one selection. Both refuse an
   endpoint with no case in the selected tiers before touching the product.

   The 116 confirmed Python cases npm has never run are the pool. Start with
   endpoints whose npm adapter does something beyond generated metadata.

   Record each result in `docs/live_verification_notes.md` in the same style as
   the existing npm passages.

**Where to record it structurally is Claude's call.** If step 1 makes it obvious
that a field in `docs/coverage.json` would help, say so in your report and leave
the schema alone.

## Task 3 — count the manual rows the extractor still throws away

**Measure and report. Do not change the parser.** This task exists because the
same measurement has now found two silent row-dropping bugs in a row, and
nobody was running it as a check.

Every keyed manual table row that produces no field is a documented thing this
repo cannot see. Two causes are already known and fixed or recorded:

- `\|` (GFM's escaped pipe) made the row's cell count disagree with its
  header, and each of the four split sites drops such a row. Ten rows, three
  chapters, five of MD-10's nine sections. Fixed 2026-09-02 (`e9dddc8`).
- A row that omits the leading No. cell is one cell short and drops the same
  way. 20 rows: `/db/POLC-M1` (5) and `/db/ULFC` (2) lose **variant divider**
  rows, `/ope/GUSTFACTOR` (2) the same, `/db/THIS-M1` (11) loses nested field
  rows. Recorded under MD-10, open, and Claude's - aligning a short row to its
  header is a judgment about the table's shape.

What to build: a script under `scripts/` that walks the manual repo, and for
every table with a recognised key column reports each row that yields no
field, grouped by cause. Reuse `extract_contracts.py`'s own helpers
(`_split_row`, `_canonical_wire_property`, `_KEY_COLUMNS`) rather than
re-parsing markdown, so the report cannot drift from what the extractor
actually does. Print a histogram, then the full list for any cause other than
a blank key cell.

The numbers to reproduce before you add anything to them:

| cause | rows |
| --- | --- |
| blank key cell (mostly legitimate section dividers) | 71 |
| cell count disagrees with the header | 20 |

Then wire it into CI the way the drift check is wired, so the count cannot
grow silently on the next manual sync. **A new cause you find is a report, not
a fix**: say which rows, which endpoints, and whether each endpoint is
promoted or a draft. Whether the parser should learn the shape is Claude's
call - the escaped-pipe one was mechanical, the short-row one is not, and you
cannot tell which a new case is without reading the section.

---

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
  harnesses call it: `live_smoke.py`, `live_crud_check.py`, and
  `packages/typescript/scripts/live-crud.mjs`. `--no-save-before` removes the
  npm harness's checkpoint, not its `/doc/NEW`.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- Leave both models empty, and say so in the note.

## Not yours, and why

- **Promoting drafts and writing `resolution` text.** Three defects came from it
  in one commit. If a draft looks promotable, report it instead.
- **Editing `contracts/endpoints/*.yaml` by hand** — any contract's `fields`,
  `variants` or `enum`.
- **`docs/manual_defects_register.md` beyond appending a row with evidence.** No
  manual-repo edit, no MIDASIT contact, no Jira issue.
- **Version bumps and releases.** The shared number is the author's call.
- Running any destructive harness against a session the author has not confirmed
  is empty.

## Settled — do not re-derive

- **All four contract-schema decisions are closed.** D1 `documentedDefaultNote`
  and D2 unstated requiredness shipped in 2.7.2; D3 array `when` with `in` and
  D4 `scalar`/`empty` arguments in 2.7.3. `contracts/README.md` states each with
  its reasoning, plus the one-route section fold and the repeated-selector rule.
- **A contract carrying `extraction.unmergedTables` is never an npm payload
  source.** That guard is what makes an incomplete contract safe, and a test
  checks it. If `npm run generate` produces a `types.ts` diff after a promotion,
  the guard is broken — report it, do not work around it. A label change in
  `resources.ts` is expected and fine.
- **A variant union is closed only where the contract proves it** — a declared
  `enum` the branches cover exactly, or both values of a boolean. Otherwise
  generation emits a trailing member carrying the remaining values. 10 of the 13
  union payloads have one; the other three are proven closed. Do not "tidy"
  them away.
- **`docs/coverage.json` carries one row per result table, not per route.**
  `/DESIGN/RC/KDS-41-20-2022/TABLE` has three rows and
  `/DESIGN/SRC/AIK-SRC2K/TABLE` two, because each `TABLE_TYPE` returns its own
  table. The contracts fold those same sections into one endpoint each. Both are
  right; do not "reconcile" them.
- **Ten manual defects are registered** in `docs/manual_defects_register.md`,
  each labelled by which side owns the fix. Append new ones there; send nothing.
- **`/info` is a `/db/*` facility.** All 147 `/DESIGN/*` resource-product pairs
  404 on introspection while the endpoints answer a plain GET, so a design-code
  contract has two permitted sources rather than three and can never carry
  `provenance: info_schema`. Three `/db/*` endpoints are the same way, all Civil
  Hyper-S: `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`, `/db/IEHG-TRUSS-M1`.
- **Both SDKs were swept read-only across all 549 declared resource-product
  pairs on 2026-09-01** and agreed on every one, and all 57 single-product
  resources 404 on the product they do not declare. Product gating is settled in
  both directions.
- **`/db/FBLA`'s shared table** — `= 1 or 2` alongside `= 1` and `= 2` — folds
  into both branches at generation time rather than forming a third union
  member. Decided and implemented.
- **A ledger entry must not contradict its own prose.** `tests/test_live_cases.py`
  fails if a `method` describing a completed write round trip sits beside
  `level: read`, or one ending "left at level: read" sits beside
  `level: write`. Fix the entry, never the test.
- **`ROADMAP.md`'s version table is not a list of sessions.** It is every
  distinct `(date, Gen build, Civil build)` the ledger cites. An entry's
  `date` is when it reached its current level and its builds come from the
  most recent check, so an older date beside a newer build is normal - 122
  entries look like that and are correct. Only move `date` when the *level*
  moves.
- **A list the manual's own description outsizes is not an enum.** A count or
  range stated about the list (`19종 (D4 ~ D57)`, `2 ~ 20`) disqualifies it,
  and the field keeps its declared scalar type. This is checked by a test over
  every contract.
- **A manual section states its request twice** - a Specifications table and
  often a JSON Schema - and where they disagree the table is *usually* the
  lossy one. 39 of the 337 promoted contracts and 22 of the 47 drafts are
  missing at least one path their own section's schema declares; MD-10 in
  `docs/manual_defects_register.md` has the measurement. A missing *root* now
  blocks promotion outright, and four sections still have one - two promoted
  and reconciled, two still drafts. Do not try to close these by editing a
  contract; each needs its section read.

  **Check the tooling before the source.** Five of MD-10's original nine
  sections were not the manual at all - `extract_contracts.py` was deleting
  the rows. Over half of what looked like a documentation defect was this
  repo failing to count cells. Task 3 exists to keep measuring that.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Omitting them ends the
  session on both products. Both SDKs fill them in, and the npm side is
  live-confirmed to do so on a real POST.

## Before every commit

Run the full set for each surface you touched — the block under "Measured
starting state" is the whole list. `git diff --check` too; a trailing space in a
YAML folded block has blocked a commit here before.
