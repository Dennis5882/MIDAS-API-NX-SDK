# Codex task prompt — mechanical work only

Updated 2026-09-02 at HEAD `faf9643`. **2.7.5 is published** on both registries;
the next number is the author's call, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

Tasks 1 and 3 need a live product session; ask the author before either.
**Task 2 is the one you can start on right now, offline.**

## What moved since your last batch

2.7.5 shipped to PyPI and npm on 2026-09-02. Nothing in your half changed, but
four things in the tree did:

- **Contracts went 337 → 342** — `/db/MATL`, `/db/RPSC`, and three
  `/DESIGN/RC/KDS-41-20-2022/*`. Drafts 47 → 42.
- **A contract now owns the npm names it publishes.** A new `surface` block
  records `className`, `exportName`, `modulePath` and `payloadTypeName`, and the
  generator raises if a Python class disagrees. 273 of the 304 npm resources
  have one. This is why `npm run generate` now reports "273 identified by a
  contract, 31 still by a Python class".
- **The section's JSON Schema is read twice** — once per table while parsing,
  once against the assembled request, where a row's path is finally correct.
  That second reading is what reached chapter 26's member-object tables.
- **A settled finding is now marked `# RESOLVED:` rather than `# NOTE:`,** and
  the promotion gate is one rule with no substring exceptions. If you see a
  refusal citing a note, the note is genuinely open.

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
  outside evidence to spot — each entry contradicted itself — so a test now
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
python -m pytest -q                       # 941 passed
ruff check src tests scripts && mypy      # clean; 41 source files
python scripts/validate_contracts.py      # OK, 342 endpoints, 1296 operations, 3322 fields
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # 304 resources (273 by contract, 31 by a
                                          # Python class), 750 payload types (258 from
                                          # contracts); no drift; 55 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 172 write / 227
read.** `schema/live-cases.json` holds **167 cases, 143 confirmed**, covering
158 distinct endpoints.

Contract drafts — clear and re-emit before judging anything about them.
`contracts/drafts/` is git-ignored build output, and a stale copy has misled a
run before:

```bash
rm -rf contracts/drafts
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all     # 42 drafts
python scripts/promote_contract.py --all --dry-run          # 0 promoted, 42 refused
```

**Zero of the 42 are promotable, and that is expected.** Grouped by the reason
each states:

| refusal | drafts |
| --- | --- |
| unresolved review notes (39 notes across these) | 17 |
| documented payload already measured wrong live | 8 |
| no payload fields could be parsed | 7 |
| key cell names more than one wire property | 4 |
| schema/table gap, parity, or no live record | 4 |
| unmerged variant tables with no `resolution` | 2 |

**None of that is yours.** Every one needs a manual section read or a live
finding interpreted.

> Two earlier numbers in this file were wrong and are worth naming so they are
> not restored. "124 blocking review notes across 31 drafts" was never measured
> the way the tool measures it. "49 notes across 21 drafts" was measured
> correctly at 2.7.4 and has since moved to 39 across 17. If a number here
> disagrees with a command's output, **the command wins** — say so in your
> report.

---

## Task 1 — capture the Hyper-S `/info` schemas as a committed artifact

**Live, read-only, Civil NX only. Needs the author's go-ahead, but not an empty
document** — this task issues GET and `/info` only and never calls `/doc/NEW`.

### Why this task exists

31 npm resources still have no contract. Seven of them are Hyper-S stubs whose
manual section is a URL, a methods line, a Zendesk link and a one-line GET
snippet — **no Specifications table and no JSON Schema at all**. Read
`## 2. /db/MATL-M1` in `04_DB_Properties.md` to see the shape. The extractor
refuses all seven with "no payload fields could be parsed", and it is right to.

Their only permitted source is live `/info` introspection. That probe has been
run twice already — 2026-07-29 and 2026-07-30, both recorded in
`docs/live_verification_notes.md` — but **only the top-level field names were
written into prose**, and no artifact was committed. `/db/EPMT-M1`'s eight
top-level fields include `TRESCA`, `VMISES`, `MOHRCL`, `DRUCKER`, `MASONRY` and
`CONCDMG`; what is inside any of them is recorded nowhere. **Zero contracts
carry `provenance: info_schema`**, because there has never been anything to
cite.

You are collecting the source. Claude writes the contracts from it.

### The seven, and what to expect

| endpoint | `/info` | ledger level |
| --- | --- | --- |
| `/db/MATL-M1` | schema | write (2026-08-31) |
| `/db/EPMT-M1` | schema | read |
| `/db/IMFM-M1` | schema | read |
| `/db/IEHG-BEAM-M1` | schema | read |
| `/db/IEHG-TRUSS-M1` | **404** | read |
| `/db/IEHG-GL-M1` | **404** | read |
| `/db/IEHG-PSS-M1` | **404** | read |

Also capture **`/db/STYP-M1`** even though it is already contracted and
write-verified. Its manual section is a real one, so its contract was written
from the manual — which makes it the one endpoint where a captured `/info`
schema can be checked against a contract that was derived independently. If the
two disagree, that is a finding worth more than the artifact.

**The three 404s are expected and are not a failure of your run.** They have
been confirmed twice. Record them as 404 and move on. Do **not** try other
casings, other prefixes, or a `/info/db/IEHG-M1` guess — that ground has been
covered, in every casing tried. Their `INEL_PROP_NAME` shape is an assumption by
analogy to `IEHG-BEAM-M1` and must stay labelled as one.

### What to produce

A single committed file, `schema/hyper-s-info.json`:

```json
{
  "capturedAt": "2026-09-..",
  "product": "civil",
  "nxVersion": "<the build string the session reports>",
  "method": "GET /info/db/{endpoint}",
  "endpoints": {
    "/db/MATL-M1": { "status": 200, "schema": { ...verbatim response body... } },
    "/db/IEHG-GL-M1": { "status": 404, "schema": null }
  }
}
```

Verbatim response bodies, no reformatting, no reordering, no summarising. The
value of this file is that it is not a paraphrase.

**Commit `/info` responses only. Never commit a GET response body** — that is
the contents of whatever model the author had open, and it is not yours to put
in the repo. If you need to note that an endpoint returned rows, write "returned
N rows" in the report; do not paste them.

Then:

1. Add a passage to `docs/live_verification_notes.md` in the existing style:
   date, product, build, what ran, what each endpoint answered, and explicitly
   whether the 404 split still holds.
2. Update those endpoints' `live_verified.method` in `docs/coverage.json` to
   cite the capture. **Do not change any `level`** — an `/info` probe is not a
   write, and the three 404 endpoints must keep saying that only GET was
   confirmed for them.
3. Run the full check set and `python scripts/gen_roadmap.py`.

**Stop and report if:** an endpoint that answered in 2026-07 now 404s, one of
the three 404s now answers, or a schema's field set differs from the top-level
names in `docs/live_verification_notes.md`. Any of those is a product change,
and what to do about it is Claude's call.

**Not yours in this task:** writing the contracts. Four of the seven will become
contractable once the artifact exists; drafting them from server introspection
is exactly the judgment work the division reserves.

## Task 2 — count the manual rows the extractor still throws away

**Offline. Start here if no live session is available.**

**Measure and report. Do not change the parser.** This task exists because the
same measurement has found two silent row-dropping bugs in a row, and nobody is
running it as a standing check.

Every keyed manual table row that produces no field is a documented thing this
repo cannot see. Two causes are already known:

- `\|` (GFM's escaped pipe) made the row's cell count disagree with its header,
  and each of the four split sites drops such a row. Ten rows, three chapters,
  five of MD-10's nine sections. Fixed 2026-09-02 (`e9dddc8`) — the count below
  confirms the fix is still holding.
- A row that omits the leading No. cell is one cell short and drops the same
  way. 20 rows, still open, still Claude's — aligning a short row to its header
  is a judgment about the table's shape. Chapter 09 loses 11 nested field rows
  (`/db/THIS-M1`); chapters 14, 15 and 17 lose 5, 2 and 2 **variant divider**
  rows.

What to build: a script under `scripts/` that walks the manual repo and, for
every table with a recognised key column, reports each row that yields no field,
grouped by cause. Reuse `extract_contracts.py`'s own helpers (`_split_row`,
`_canonical_wire_property`, `_KEY_COLUMNS`) rather than re-parsing markdown, so
the report cannot drift from what the extractor actually does. Print a
histogram, then the full list for any cause other than a blank key cell.

The numbers to reproduce before you add anything to them:

| cause | rows |
| --- | --- |
| blank key cell (mostly legitimate section dividers) | 71 |
| cell count disagrees with the header | 20 |

Then wire it into CI the way the drift check is wired, so the count cannot grow
silently on the next manual sync.

**A new cause you find is a report, not a fix**: say which rows, which
endpoints, and whether each endpoint is promoted or a draft. Whether the parser
should learn the shape is Claude's call — the escaped-pipe one was mechanical,
the short-row one is not, and you cannot tell which a new case is without
reading the section.

## Task 3 — `/db` write coverage (the long-running background task)

Standing work, unchanged and still yours. Lower priority than Tasks 1 and 2 only
because those two unblock things nothing else can.

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

Two of the 18 moved in 2.7.5. `/db/RPSC` gained a contract, so its documented
shape is now written down in `contracts/endpoints/` rather than only in a manual
table. `/db/SBDO` already had one, and its `AXIS_VECTOR` was corrected from
`number` to an array of numbers — a fixture built before 2.7.5 has the wrong
type in it. Build both from the contract.

For each endpoint, in batches of at most 8:

1. Read the manual chapter and this endpoint's entry in
   `docs/live_verification_notes.md` **first**. Several already have a recorded
   reason for failing.
2. Build the fixture from the manual's own Request Example, or from the contract
   where one exists. **Never hand-write a payload.**
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

## Task 4 — record what the npm package has actually proven

`packages/typescript/scripts/live-crud.mjs` already reads the same
`schema/live-cases.json` Python does and takes any endpoint through
`--endpoints`, so this needs no new harness. The gap is the *record*:
**npm-side live verification exists only as prose.**

1. ~~**Read out what is already claimed.**~~ **Done** —
   `docs/npm_live_evidence_scratch.md` has it: **23 `/db` endpoints and 4
   result-table operations, 27 npm public-API operations**, each traced to
   the passage that claims it, with the rejections and harness calls
   (`/doc/NEW`, `SAVEAS`) deliberately excluded.
2. **Then extend it by running.** Pick endpoints Python has confirmed but npm
   has not, in batches of at most 8:

   ```bash
   npm run live:crud -- -- --product gen --endpoints /db/AAA,/db/BBB \
     --save-dir <a writable directory on the NX machine>
   ```

   `scripts/live_crud_check.py` takes the same `--endpoints`, so a batch can be
   run through both packages against one selection. Both refuse an endpoint with
   no case in the selected tiers before touching the product.

   The confirmed Python cases npm has never run are the pool. Start with
   endpoints whose npm adapter does something beyond generated metadata.

   Record each result in `docs/live_verification_notes.md` in the same style as
   the existing npm passages.

**Where to record it structurally is Claude's call.** If step 1 makes it obvious
that a field in `docs/coverage.json` would help, say so in your report and leave
the schema alone.

---

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session.** For anything
  that writes, confirm both documents are empty: `GET /db/NODE` and
  `GET /db/ELEM` answer `{"message": ""}`. Task 1 is read-only and does not need
  an empty document, but still needs the go-ahead.
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
- **A GET can still pop a modal dialog** if the open document lives under
  `Program Files` or another path a standard account cannot write to. Keep
  working documents elsewhere before any sweep.
- **Delete every test record by its own id** (`DELETE {endpoint}/{id}`).
  `DELETE {endpoint}` with an ID-keyed `Assign` body empties the whole table.
- **A 200 is not success.** `{"message": "error status"}` = method not served;
  `{"error": {...}}` = ran and rejected; an echoed record = success.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- **Never commit a GET response body.** It is the author's model contents.
- Leave both models empty, and say so in the note.

## Not yours, and why

- **The 31 remaining uncontracted npm resources.** All of them. Every one is
  refused for a reason that needs a manual section read or a live finding
  interpreted — 9 carry open review notes, 8 have a documented payload already
  measured wrong live, 7 have no source at all (Task 1 is about collecting one),
  3 have a key cell naming two wire properties, 2 need a variant `resolution`,
  2 have a table their own schema outsizes. Contract promotion produced three
  defects in one commit; that is why this line is here.
- **Promoting drafts and writing `resolution` text.** If a draft looks
  promotable, report it instead.
- **Editing `contracts/endpoints/*.yaml` by hand** — any contract's `fields`,
  `variants`, `enum` or `surface`.
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
- **A contract's `surface` block owns the published npm names.** 273 of the 304
  resources have one and the generator raises on a disagreement. It raised once
  in 2.7.5 and the disagreement was Python's — two `NAME` attributes were
  changed to match their contracts. Do not resolve such a raise by editing the
  contract.
- **A `requirement: required` carrying an `appliesWhen` is a branch's
  requirement, not the payload's.** 49 fields across nine contracts were
  generated unconditionally required, producing types no caller could satisfy.
  The condition now renders in the doc comment. Fixed in 2.7.5; do not
  "restore" the requiredness.
- **A contract carrying `extraction.unmergedTables` is never an npm payload
  source.** That guard is what makes an incomplete contract safe, and a test
  checks it. If `npm run generate` produces a `types.ts` diff after a promotion,
  the guard is broken — report it, do not work around it. A label change in
  `resources.ts` is expected and fine.
- **A variant union is closed only where the contract proves it** — a declared
  `enum` the branches cover exactly, or both values of a boolean. Otherwise
  generation emits a trailing member carrying the remaining values. Do not
  "tidy" them away.
- **`docs/coverage.json` carries one row per result table, not per route.**
  `/DESIGN/RC/KDS-41-20-2022/TABLE` has three rows and
  `/DESIGN/SRC/AIK-SRC2K/TABLE` two, because each `TABLE_TYPE` returns its own
  table. The contracts fold those same sections into one endpoint each. Both are
  right; do not "reconcile" them.
- **Eleven manual defects are registered** in `docs/manual_defects_register.md`,
  each labelled by which side owns the fix. MD-11 is the newest: nine parameter
  rows carry a Value Type their own section contradicts. Seven are integer/number
  width and change nothing a caller sends; two change the shape of the value and
  are corrected with a `manualDefects` entry. Append new ones there; send
  nothing.
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
  distinct `(date, Gen build, Civil build)` the ledger cites. An entry's `date`
  is when it reached its current level and its builds come from the most recent
  check, so an older date beside a newer build is normal — 122 entries look like
  that and are correct. Only move `date` when the *level* moves.
- **A list the manual's own description outsizes is not an enum.** A count or
  range stated about the list (`19종 (D4 ~ D57)`, `2 ~ 20`) disqualifies it, and
  the field keeps its declared scalar type. Checked by a test over every
  contract. As of 2.7.5 a list proven a sample once in a section is treated as a
  sample everywhere that section writes it.
- **A manual section states its request twice** — a Specifications table and
  often a JSON Schema — and where they disagree the table is *usually* the lossy
  one. A missing *root* blocks promotion outright. MD-10 has the measurement.
  Do not try to close these by editing a contract; each needs its section read.

  **Check the tooling before the source.** Five of MD-10's original nine
  sections were not the manual at all — `extract_contracts.py` was deleting the
  rows. Over half of what looked like a documentation defect was this repo
  failing to count cells. Task 2 exists to keep measuring that.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Omitting them ends the
  session on both products. Both SDKs fill them in, and the npm side is
  live-confirmed to do so on a real POST.

## Before every commit

Run the full set for each surface you touched — the block under "Measured
starting state" is the whole list. `git diff --check` too; a trailing space in a
YAML folded block has blocked a commit here before.
