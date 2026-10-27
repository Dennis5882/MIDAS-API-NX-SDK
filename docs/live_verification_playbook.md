# Live verification playbook

How a live write-verification session is run on this repo, what is left to
verify, and why each remaining endpoint sits where it does.

This replaces `docs/codex_handoff_prompt.md`, deleted 2026-09-20 when the
author stopped handing mechanical batches to Codex. Everything here was
written for that file and is kept because it is about the work, not about who
does it; its task assignments and division-of-labour framing are gone. Earlier
versions are in git history (`a9da9a0` and before).

`docs/live_verification_notes.md` remains the evidence record — what ran, on
which build, with verbatim errors. This file is the procedure and the
scoreboard.

## Where things stand (measured 2026-10-26)

- **Both products are installed at v2.2, Build 10/17/2026** - Gen NX 2026
  (v2.2) and Civil NX 2026 (v2.2), each read from its own About dialog by the
  author 2026-10-22, on the author's home PC, which is also the machine
  holding this checkout. **Writes are re-verified on it**: `/info` was diffed
  (no change; the 10/10/2026 baseline stands), the GET breadth sweep ran clean
  (Gen 268 resources, Civil 284), and every confirmed case replayed through
  both SDKs the same day - all 421 endpoint-product pairs passed. Gen RC `MRFT`
  now stores `FACTOR` as sent, and Civil now accepts `/db/NLCT` and `/db/EPMT`;
  the fixture follows both (live notes, 2026-10-22).
- **Gen write verification continued on 2026-10-24**, same build: every
  unconfirmed Gen case was re-run, and **Gen now stores `/db/MADO`**, so MADO
  and `/db/DOEL` pass through both SDKs; the other 25 answered as before.
  Civil, measured 2026-10-25, stores it too: MADO, DOEL and Civil's
  `/db/SBDO` pass there through both SDKs, and Civil's other unconfirmed
  cases answered as before apart from `/db/DSTL`, whose Civil case is now
  confirmed. On 2026-10-26 `/ope/LCOM-CONC`, `-STEEL` and `-SRC` generated
  combinations on Gen that were read back from `/db/LCOM-*`, so they are
  write-level; `/ope/LCOM-GEN` and the design tables refused on 09/24 still
  refuse. Civil, the same day, on its own PSC tutorial model: `/db/TDNA`,
  `TDPL`, `TDCS` and `CSCS` round-trip, and `/ope/GSBG` wrote girder diagrams
  for the first time (recipe in the live notes); `/view/PRECAPTURE` wrote its
  fiber-section preview. Then the refused `/db` endpoints were looked for in
  195 bundled Civil models: the general-link family and `/db/RPSC` now pass
  the CRUD fixture on the base model (records taken from tutorial models),
  and `MVLDeu`, `MVLDbs` and `PHGE` round-trip on those models. The design-function harness ran end to end for the first time, and the TABLE
  `EXPORT_PATH` and REPORT files were inspected on the host, so those eight
  design endpoints are write-level now (live notes, 2026-10-24).
- **2.10.4 is published on PyPI and npm** (2026-10-28): `/db/CNLD` and
  `/db/BMLD` fill documented defaults into every `ITEMS` entry, because a Gen
  PUT copies omitted entry fields from the record's first entry. No type or
  export changed. The npm changelog's `Unreleased` is empty.
- **Coverage: 400/400 implemented, 312 write / 88 read.** Of the 225 `/db`
  endpoints, 210 are write-level and 15 are not.
- **Fixture (`schema/live-cases.json`, version 6):** 338 cases over 259
  endpoints; 310 confirmed over 247 endpoints; 9 base-model steps; 83 named
  seeds; 0 unsupported.
- **npm has replayed all 310 confirmed cases** on every product each declares.
  Keep that gap at 0: every new confirmed case goes through both harnesses.
- **Contracts: 384 endpoints + 87 result tables.** The three drafts left, the
  IEHG trio, have no permitted source; that is final.

## Gates

Run these before starting and before committing. If a number differs,
something moved — the command wins over this file. The last one enforces that
for the section above: it re-derives what "Where things stand" claims and fails
if the file and the repository disagree.

```bash
python -m pytest -q                       # 1126 passed
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK - contracts valid
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # has_diff: false
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check   # OK
python scripts/info_baseline.py --divergence --check          # OK
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # exit 0
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 1 fixture lead over 1
                                          # endpoint, 0 contract gaps over 0
python scripts/report_npm_replay_coverage.py --check   # 310 cases over 247
                                          # endpoints; every product: 310
python scripts/check_verification_lag.py --check       # 40, ceiling 40
python scripts/verification_ledger.py                  # 397 endpoints:
                                          # 85 read, 312 write
python scripts/report_unmerged_tables.py --check       # exit 0
python scripts/check_state_numbers.py --check          # OK; it checks this
                                          # block's own numbers too
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 91 tests
```

The manual repo is vendored at `ee5fa8f`. If the drift or extraction check goes
red, a sync landed upstream: deciding what a chapter's new text means is real
work, and a line reference that no longer resolves can mean a table moved or
that it changed.

## The recurring task: re-verify on a new build

**Live. Destructive: `/doc/NEW`.** Every confirmed case was replayed on Build
09/15/2026 on 2026-09-18, on Build 09/24/2026 on 2026-09-27 (302 of 302
endpoint-product pairs), on Build 10/10/2026 on 2026-10-11 (419 of 419), and on
**Build 10/17/2026 on 2026-10-22** - 421 of 421 pairs through both SDKs, after
one expectation followed a product change - so this is dormant until a newer
build ships. A confirmed case failing on a new build is a
**regression**, which is what this exists to catch before a user does.

When a build ships, this command names the scope — set `BUILD` to the **new**
build's string and it lists every confirmed-case endpoint with no ledger
record citing it. Do not hand-count. This sentence said "the **old** build"
until 2026-09-27, which is the opposite of what the code does and of the
comment inside it: the old build's string names everything already covered,
so it prints 0 and no scope at all. Nothing had shipped since the file was
written, so it was never run the wrong way round.

```bash
PYTHONIOENCODING=utf-8 python - <<'PY'
import json, sys
sys.path.insert(0, "scripts")
from verification_ledger import load_records

BUILD = "09/24/2026"   # replace with the NEW build's string
cases = json.load(open("schema/live-cases.json", encoding="utf-8"))["cases"]
seen = set()
for record in load_records():
    nx = json.dumps(record.get("nxVersions") or {})
    if BUILD in nx or BUILD in (record.get("method") or ""):
        seen.update(record.get("endpoints") or [])
todo = sorted({c["endpoint"] for c in cases
               if c["confirmed"] and c["endpoint"] not in seen})
print(len(todo)); print(" ".join(todo))
PY
```

It asks which confirmed-case endpoints have no ledger record citing that
build. A record mentioning the build for another reason drops out of the
list; that errs toward doing less, never toward a false claim. With
`BUILD = "09/24/2026"` it printed the whole confirmed set on the morning of
2026-09-27, before the replay, and prints 0 since the three ledger records that
replay added (`ledger-write-2026-09-27-{1,2,3}`).

Batch by tier (`--tier`), at most 8 endpoints per selection, through **both**
harnesses on **both** products in the same session. **Before calling a batch
done, re-run the scope command**; if it did not drop by the number just run,
the ledger append is what is missing.

## Running a live batch

1. **Ask before the first product call of a session.** Then confirm each
   document is open and empty with **that product's own key**: `GET /db/NODE`
   and `GET /db/ELEM` return no records. If `GET /db/NODE` says
   `The project is not opened`, ask for a document — do not send `/doc/NEW`.
2. In Git Bash, `export MSYS_NO_PATHCONV=1` first, or `/db/PTNS` arrives as
   `C:/Program Files/Git/db/PTNS` and the harness exits 2 before any product
   call.
3. npm: from `packages/typescript`, `npm run live:crud -- -- --product gen
   --endpoints /db/A,/db/B --save-dir C:/temp` (PowerShell takes two `--`, Bash
   one), with `MIDAS_MAPI_KEY` set to that product's key.
4. Python, same selection, same session: `python scripts/live_crud_check.py
   --product gen --endpoints /db/A,/db/B --save-dir C:/temp
   --out <report>.json`. `--save-dir` derives the file name, so the extension
   cannot be got wrong; `--save-as C:/temp/<name>.mgbx` still takes an exact
   path if you want one (`.mcbz` on Civil). The Python harness refuses to run
   (exit 2) when `schema/live-cases.json` has drifted from the script; re-emit,
   never hand-edit the fixture.
5. Repeat both for `civil`.
6. A `BLOCK` (exit 3) means a seed failed and says nothing about the endpoint.
   A confirmed case failing is a regression: report it verbatim, do not change
   the fixture to make it pass, and do not flip `confirmed`.

Selection traps, each of which has cost a session:

- **A case the npm harness can only clean up by resetting the document** may
  only be the **last** endpoint of an npm invocation. That is a case whose own
  endpoint has no DELETE (`/db/GRUP`, `/db/BNGR`, `/db/STYP`, `/db/STYP-M1`,
  `/db/CO_M`, `/db/CO_S`, `/db/CO_T`, `/db/CO_F`, `/db/PZEF`, `/db/CLDR`,
  `/db/MATD`, extras14's `/db/MVCD`) **or** whose setup writes one - every seed
  that creates a group or a boundary group. The rule is `caseCleanupMode` and
  `setupCleanupMode` in `live-harness-support.mjs`; the harness refuses such a
  case anywhere else with `a no-DELETE case must run last and be followed by a
  document reset` and exits 2 before sending it. This bullet named only the
  first two until 2026-09-27, when a selection of extras1 hit `/db/STYP`. Put
  one at the end of each invocation and give the rest their own.
- **RC `LMRR`/`SRDF` and steel `SRDF` need their code's `DCO` written earlier
  in the same document**, and no `needs` says so. An npm selection that puts
  `DCO` in another invocation fails them with `Errors detected in ... Design
  Control Data` - it read as two regressions on 2026-10-11 and passed once
  `DCO` came first. Python runs the whole `design_tables` tier and is not
  affected.
- **An `--endpoints` selection can drop a case another case depends on**, and
  the Python harness does not warn. `extras14`'s `/db/DYFG` and `/db/DYNF` need
  that tier's `/db/MVCD` case; select them together.
- **Selecting `moving` and `extras14` together** makes `mvcd_ksce_seed` answer
  `Key Already Exist`.
- **A seed on a table that renumbers** (STLD, FBLD, …) must be listed in
  `RENUMBERING_SEEDS`, or npm refuses its setup as a collision. `SeedStep` has
  no flag for it; the set is the only place.
- **A seed that replaces a base-model record is cleaned up by restoring it**,
  not by deleting it. extras13's five design cases are the only ones that do
  this: they overwrite material 1, section 1, nodes 1-4, element 2-3 and
  thickness 1. Until 2026-09-20 the npm harness left the fixture's versions in
  place for the rest of the invocation, because it detects what a step created
  by diffing against a snapshot taken before the step's own delete. If a new
  seed needs `replaceExisting`, check that the base model can supply the
  record back — `replacedBaseModelRecord` refuses a PUT step, which the
  document supplies rather than the fixture.
- **A failing read-back probe is a failure of that case, not of the run.** A
  probe subscripts the record it is handed (`p["ITEMS"][0]["END"]`), so a
  record the product returns in another shape used to raise `KeyError` past
  the report, the end-of-run checkpoint and the document restore. Both are
  caught now; a `FAIL` naming a probe means the shape, not the SDK.
- **A tier's seeds are not per-case.** The Python runner executes every seed of
  a selected tier before that tier's cases, so a tier that splices another
  tier's seed list POSTs those records twice whenever both are selected — a
  full re-verification does exactly that. Give a new tier its own seeds, even
  when an existing one looks identical; extras19 was built the other way on
  2026-09-20 and rebuilt the same day (live notes).
- **One Python invocation with no `--tier` is not a re-verification.** It runs
  every tier in one document, and earlier tiers' records break later cases: on
  2026-10-22 it reported six regressions per product, with errors naming the
  model (`element no. 1 is an element type in which ...`), and five of each
  passed in their own tier. Run one invocation per tier.

## Recording a run — three places, every time

A run that reaches only some of these did not happen as far as any count is
concerned. This mistake has been made twice: on 2026-09-17 one endpoint and on
2026-09-18 eleven were recorded in the evidence files and never reached the
ledger, and the second session reported its task complete.

1. **The fixture** — `confirmed=True` per product that passed, then
   `--emit-cases`.
2. **The ledger**, `contracts/verification/ledger.yaml` — see below.
3. **The evidence files** — `docs/live_verification_notes.md` (what ran, on
   which build, verbatim errors) and `docs/npm_live_evidence_scratch.md` (one
   row per npm success: date, products, Count line).
   `report_npm_replay_coverage.py --check` fails if a ledger record's `method`
   says `npm replayed the same emitted fixture` and the scratch file has no
   row.

Then `python scripts/gen_roadmap.py` and commit `ROADMAP.md` with the batch.

**A run adds a record. It never edits one.**

```yaml
  - id: ledger-write-2026-09-21
    endpoints: ["/db/PTNS"]
    date: "2026-09-21"
    level: write            # what the session ACHIEVED, not what it tried
    products: [gen, civil]  # only the products it achieved that on
    nxVersions:
      gen: MIDAS Gen NX 2026 (v2.1), build 09/15/2026
      civil: MIDAS Civil NX 2026 (v2.2), build 09/15/2026
    outcome: success
    method: >-
      What was actually done, including whether npm replayed the same
      emitted fixture.
```

`scripts/verification_ledger.py` resolves the records into one claim per
endpoint: **write if any record achieved a write**, and the earliest record at
that level supplies the date and build, because that is the session that
established the claim. So a re-verification is a new record and the original
claim keeps its date -- which is what the old append-only `method` string kept
getting wrong. A read that follows a write does not demote anything, and a
promotion from read to write is just a write record.

Two things the ledger will not do for you:

- **`level` is what a session achieved.** A write the product refused before
  it changed anything is `read`. Recording a refused write as `write` is how
  the old contract records came to claim `/db/NLLP` and `/db/TDMF` at write
  level while their own `finding` said the write was refused.
- **Nothing is deleted or rewritten.** A record is what one session saw, and a
  later session cannot change that. If a record is wrong about what happened,
  correct it in place with a dated note, the way the live notes do.

Run `python scripts/verification_ledger.py` to see the resolved totals, and
`python scripts/gen_roadmap.py` to publish them.

## What is left, and why

Each `/db` endpoint below write level is here with its reason. **Read its entry
in `docs/live_verification_notes.md` before touching it**: re-running an
unchanged fixture on an unchanged build answers nothing, and on 2026-09-19 all
15 runnable cases in the first table were re-run and every answer matched the
earlier build word for word. **On 2026-09-27 every unconfirmed case in the
fixture - these tables' whole content - was re-run on Build 09/24/2026 through
both SDKs, and nothing was newly resolved**: every answer matched its row below.
**On 2026-10-24 every unconfirmed Gen case was re-run on Build 10/17/2026**:
`/db/MADO` and `/db/DOEL` passed on Gen for the first time and left this table,
and the other 25 matched their rows. On 2026-10-25 Civil's extras9 cases - MADO,
DOEL and SBDO - all passed too, and every other unconfirmed Civil case was re-run:
`/db/DSTL` passed (as it has on Civil since 2026-09-01; it is one case per
product now, Civil confirmed) and the other 23 matched their rows.

### 7 endpoints with a case that has never passed

| endpoint | last answer / reason | blocker |
| --- | --- | --- |
| `/db/EPST`, `/db/EPSE` | `Wrong Field` | every documented value set on EPST varied (`SEL_TYPE`, `EP_TYPE`, `ELEM_TYPE`, `DIR`); EPSE shares its fields |
| `/db/WVLD` | `Wrong Field` | refuses even a bare `NAME`, and still with `/info`'s `NAME_THIS`/`TRAJ`/`USERGRID` added (2026-10-26) |
| `/db/HPCE` | `Wrong Key` | product finding; unchanged on the heat-of-hydration tutorial model and with `START_STAGE`/`END_STAGE` named (2026-10-26) |
| `/db/SINF`, `/db/MVLDpl` | POST accepted, record not stored | product finding; no bundled Civil model carries either |
| `/db/ACTL` | Gen refuses every payload; Civil answers a PUT with the record as sent and keeps neither `ITER` nor `TOL`, on a tutorial model too (2026-10-26) | settled product behaviour |

### 8 endpoints with no case

| endpoint | what stands in the way |
| --- | --- |
| `/db/IEHG` | `PROP_NAME` names an inelastic hinge property that no endpoint creates (`FIBER_NAME`'s FIBR division can be built since 2026-09-28) |
| `/db/IEHG-BEAM-M1` | `INEL_PROP_NAME` names an inelastic hinge property that no endpoint creates |
| `/db/EPMT-M1` | contract is `/info`-only: no value stated anywhere, so any payload would be hand-written |
| `/db/REBB`, `/db/REBR` | ch24 design rebar: the manual's long keys answer `Wrong Field`, `/info`'s short keys `Unknown Error`; each needs a designed RC member |
| `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`, `/db/IEHG-TRUSS-M1` | no manual schema and `/info` 404s — **never** build a fixture |

Write-level without a fixture case, each from a probe the base model cannot
reproduce: `/db/CSCS`, `/db/TDCS` (Civil's PSC tutorial model, 2026-10-26),
`/db/DRLS` and `/db/REBW` (manual probes), `/db/MVLDbs` (the BD37 tutorial model, 2026-10-26; its contract still needs a shape decision on the mutually exclusive `LCDATA_*` objects before a case). `/db/IMFM`, `/db/IMFM-M1`, `/db/FIBR`
and `/db/RCHK` have confirmed cases since 2026-09-28.

### Unconfirmed cases on endpoints already at write level

They move no count. None is actionable unless its cause changes.

| case | product | recorded cause |
| --- | --- | --- |
| `/db/LLANch`, `/db/SLANch`, `/db/LLANid`, `/db/IMPF` | gen | `Unavailable moving load code` for the code these lanes need |
| `/db/LLANop`, `/db/SLANop` | gen | refused under `BS`, the code ch08 gives Gen for this family - `contains errors.(Item:Wheel Spacing)`, the first time the item was recorded (2026-09-27) |
| `/db/LCOM-SEISMIC` | civil | documented `ANAL="RS"` answers `The Load Combination Type is not supported.` |
| `/db/HHCT` | civil | POST accepted, expected value not read back |
| `/db/DSTL` | gen | `Errors detected in Steel Design Control Data.` |
| `/db/SBDO` | gen | `Unknown Error` with the domain it names present (Build 10/17/2026); Civil's own case passes |
| `/db/POGD` | gen | `Wrong Field` for the payload Civil accepts |
| `/db/FBLA` | both | `Unknown Error` on the fixture payload; write-level from a downstream app's floor-load model (Gen, 2026-10-20) |
| `/db/STCT` | both | Gen: drops `iITER` (`wrote 30, read back None`). Civil: never measured - the first `POST /db/STAG` auto-creates `/db/STCT` id 1 with product defaults, so the case's own POST of id 1 is refused by both harnesses before it is sent (pinned 2026-09-27; Gen does not auto-create) |
| `/db/RPSC` | gen | the Civil case passes on a seeded PSC section (2026-10-26); on Gen that section seed is refused - `The section type ... is either not supported by the program or incorrect` (2026-10-27) |
| `/db/PHGE` | both | `Unknown Error`: `HINGE_TYPE` names a pushover hinge property the base model lacks and no endpoint creates; round-trips on Civil's MNL-01 model |
| `/db/TDNA`, `/db/TDPL` | both | `Not Registered String` for `IS_DB_TDNA_NOTENSIONCALC` on the base model (TDPL behind it); both round-trip on Civil's PSC tutorial model (2026-10-26), so the base model lacks a precondition |

`check_fixture_contract.py`'s one lead, `/db/ACTL` sending `CLATS` on Gen, is
covered above.

### The unmerged tables

`docs/unmerged_tables_against_info.md` is down to `/db/TDME`'s two tables,
which review marked `excluded` with evidence rather than merged: they are iGen
code tables this API refuses. Every other table it used to list was merged
between 2026-09-21 and 2026-09-22, several after a live measurement. The
report and its CI check stay as drift detection for the next contract that
declares one - not as a queue to rescan.

## Open decisions

- **Contract `verification` refs lag the ledger.** 40 contracts cite only a
  read session for an endpoint the ledger holds at write level (TDNT, POGD,
  MVLDch, MVLDid and PTNS among them). It read 48 until the checker stopped
  matching the word "write" in the block and started resolving the ref: eight
  contracts cite a write session whose id does not spell it. The fold
  landed on 2026-09-21 and fixed the *source* of the disagreement -- there is
  one ledger now, `contracts/verification/ledger.yaml` -- but a contract's
  `verification.records[].ref` still points at the session it was promoted
  from, and that is not hand-edited: it records provenance, and editing it to
  match a later claim would forge one. `scripts/check_verification_lag.py`
  holds the count as a ceiling so it can fall but not grow. Re-promoting a
  contract is what moves it. **Audited 2026-09-21: not one of the 40 is a
  contract defect, so this is closed as a decision.** A stale citation would
  matter if the later write had revealed something the contract does not
  record; `check_fixture_contract.py` measures that on every `confirmed` case,
  and none of the 40 is among its three confirmed-side findings (39 have a
  confirmed case; `/ope/MEMB` is write-confirmed through the 2026-09-18 manual
  probes instead). `tests/test_check_verification_lag.py` keeps the two sets
  disjoint, so if one ever crosses over it stops being bookkeeping and that
  contract wants re-promoting from a permitted source. Do not churn the 40 to
  drive the number down.
- **`/db/SPLC`'s `NDP` requiredness** — nested under the Optional `bNDP` switch
  with no wire rule, so neither an `appliesWhen` nor a `safeToOmit` is
  grounded.
- **`/db/SPLC`'s cross-tier id collision** — extras4's `lcom_seismic_splc` and
  extras5's Civil case both own id 1, and the family renumbers, so a different
  id does not fix it. It reports `BLOCK`, honestly.
- **`/db/SPLC`'s `aACCECC_ECCEN_LIST[].ALONG`** is created but never updated
  (recorded in the contract's PUT `notes`).
- **`/db/THIS-M1`'s 20 `/info` properties with no manual row** — the ceiling in
  `info_baseline.py` holds the number.
- **`/db/SECT`'s `USE_HAMBLY_EQ`** and **`/db/RPSC`'s `CONTRIBUTION_FACTOR`**
  — both documented nowhere, both contracted from `/info` on 2026-09-27
  (`provenance: info_schema`, `requirement: unstated`), and
  `schema/info-baseline.json` re-captured on Build 09/24/2026 in the same
  change. `USE_HAMBLY_EQ` had been held since 2026-09-16 pending the next
  manual sync; that sync came (MIDAS-API `685be56`) without it, and a second
  build kept it on both products. `CONTRIBUTION_FACTOR` is Civil-only, which
  raised `--divergence`'s ceiling 10 -> 11. Only `SECT_BEFORE`'s copy of
  `USE_HAMBLY_EQ` is recorded: the contract does not model `SECT_AFTER`. At
  the next manual sync, check whether either appears — if it does, the
  manual's text replaces the `/info` description, and a condition it states
  becomes `appliesWhen`.
- **`/db/MVLDbs`'s contract shape**, and the ch24 rebar family above.

## Live-session rules

`CLAUDE.md` carries the full set; these are the ones a live session trips over.

- **`.env` holds `MIDAS_MAPI_KEY_GEN` and `MIDAS_MAPI_KEY_CIVIL`**, no plain
  `MIDAS_MAPI_KEY`. Never print either. A mismatched key still answers
  `connected` and returns 0 records, so check each product with its own key.
- **`verify_connection()` cannot prove a session is alive.** It answers
  `connected` while a modal dialog holds the product; use a real `GET /db/NODE`.
- **Paths belong to the NX machine.** `--save-dir` is required and never
  inferred from `verify_connection()["user"]`, which is an email. Every
  destructive harness asks the same way and refuse to start without an answer
  (`scripts/harness_save_path.py`); the shape is checked while arguments are
  parsed, so a relative path costs nothing, not even a connection.
  `C:/temp` exists; the author manages it — do not clean it.
- **A GET can pop a modal dialog** if the open document lives under
  `Program Files`.
- **Five harnesses call `/doc/NEW` and discard unsaved work**:
  `scripts/live_smoke.py`, `scripts/live_crud_check.py`,
  `packages/typescript/scripts/live-crud.mjs`,
  `scripts/live_manual_feedback.py`, which calls it once per probe rather than
  once per run, and `scripts/live_design_functions.py` (Gen only). Never against a document the author has not confirmed empty.
  Each takes the checkpoint directory from the caller and none guesses one.
  `--no-save-before` waives the checkpoint, not the `/doc/NEW`, and
  `live_manual_feedback.py` and `live_design_functions.py` do not offer it:
  the first's per-probe saves are the run's evidence, the second saves before
  its analysis regardless.
- **Save before analysing.** `/doc/ANAL` on a document that was never saved -
  every document straight after `/doc/NEW` - raised Gen's "Save As" dialog on
  2026-10-22 and the call never answered. Python harnesses analyse only
  through `harness_save_path.analyze_saved`, which saves into `--save-dir`
  first and refuses without one; a test fails on a direct `doc.analyze(`
  under `scripts/`. `live-analysis.mjs` saves before its analysis too.
- **Assert a reset, do not assume it.** `/doc/NEW` without `{"Argument": {}}` is
  HTTP 500 and resets nothing.
- **Never call `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK`**: it crashes Gen, MIDASIT
  has closed it as unsupported, and each call costs a restart and a held
  licence.
- **Never hand-write a live payload.** Use the fixture, a contract or a manual
  example.
- **The processes are `GenNX` and `CVLw`.** Civil NX's executable is
  `CVLw.exe`, so a process filter on "Civil" finds nothing and reads as Civil
  running on another machine (2026-10-23). Match on the window title
  (`MIDAS CIVIL NX ...`) or the name `CVLw`.
- **A crash leaves Windows' own record; read it before writing a report.**
  The Application log's `Application Error` 1000 entries name the faulting
  module, exception and offset (`Get-WinEvent -FilterHashtable
  @{LogName='Application'; ProviderName='Application Error'; Id=1000}`,
  filtered on `CVLw`/`GenNX`), and they go back months: on 2026-10-23/24 they
  showed both reproductions of the Civil `CD-ANAL` crash at the same
  `wg_rcs.dll` offset on two builds, and OCHECK in `wg_main.dll`. The
  `ReportArchive` copies under `C:\ProgramData\...\WER` need admin rights
  for older entries; the event log does not.

## Repository rules this work keeps running into

Beyond what `CLAUDE.md` already states:

- **`appliesWhen`'s `in` needs at least two values**; use `equals` for one.
- **`contracts/` mixes CRLF and LF.** Edit those files as bytes; a deletion
  count on an insert-only change means corrupted line endings. The ledger and
  `docs/coverage.json` are machine-written, so append a record or re-run the
  generator rather than hand-editing either.
- **Never commit a GET response body** — it is the author's model contents.
- **Never put `MAPI-xxxx` or MIDASIT's internal tracker in anything that
  ships**, release notes included. The manual repo names one; it does not come
  across.
- **A wire value is not a majority opinion.** Three documents agreeing can be
  three transcriptions of one typo; only a live check settles one.
