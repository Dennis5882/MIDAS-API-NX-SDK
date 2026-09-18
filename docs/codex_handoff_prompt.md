# Codex task prompt — mechanical work only

Updated 2026-09-18, after the **2.8.3** release. Rewritten from scratch: the
previous version had grown to describe more closed tasks than open ones. What
the closed tasks found is summarised under "Closed — do not reopen"; their full
text is in git history (`0fff09d` and earlier).

## Where things stand

- **Both products are on Build 09/15/2026** (Gen NX 2026 v2.1, Civil NX 2026
  v2.2), read from their About dialogs on 2026-09-16.
- **2.8.3 is published on PyPI and npm.** Nothing in either packaged surface has
  changed since. **No release is warranted**, and a contract edit does not make
  one: the author picks the number and asks for the release explicitly.
- **Coverage: 400/400 implemented, 201 write / 199 read.** Of the 225 `/db`
  endpoints, 46 are short of write level.
- **The npm package has replayed all 177 confirmed live cases** on every product
  each case declares. The npm/Python evidence gap is closed; keep it closed.
- **Contracts: 384 endpoints + 87 result tables**, 5,078 fields. Every npm
  resource and operation that can be named by a contract is. The three drafts
  left, the IEHG trio, have no permitted source; that is final.

## The division, set by the author

Judgment-heavy work is Claude's: schema design, what a contradictory manual
means, what stays unmerged, how a seed or case is represented. Bounded,
verifiable, repeatable work is yours. Every task below has a starting number
you can check your run against. **A task that turns out to need a judgment call
is one to stop and report, not to decide.**

## Order of work

**With a product session** (a session is the scarce thing — use it for these
first):

1. **Task B** — the 22 endpoints whose case has never passed.

**Without one:**

2. **Task A** — run batch 17 — `/db/PHGE`, `/db/POGD`, `/db/POGD-M1` are built
   and unconfirmed — then build fixtures for the rest.

**Task K is closed**: every confirmed case ran on Build 09/15/2026 on
2026-09-18. Its section stays because the next build reopens it.

Task E is offline and **not** yours to start; its section says why.

---

## Measured starting state

Run these first. **If a number differs, say so before starting** — something
moved under you, and the command wins over this file.

```bash
python -m pytest -q                       # 1083 passed
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK; 384 endpoints, 5078 fields,
                                          # 140 proven safe, 8 unsafe
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # has_diff: false
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check   # OK
python scripts/info_baseline.py --divergence --check          # OK
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # exit 0 (always prints
                                          # the MD-50 /db/MVCTch baseline)
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 1 fixture lead over 1
                                          # endpoint, 3 contract gaps over 2
python scripts/report_npm_replay_coverage.py --check   # gap 0; by confirmed
                                          # case 177 complete, 0 partial, 0 none
python scripts/report_unmerged_tables.py --check       # report is current
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 83 tests
```

**A manual sync is not yours to reflect.** Two of these went red on 2026-09-18
when the manual repo moved to `e64a682`, and both are green again now:
`vendored_at_commit` is current and 17 contracts had their manual line
references re-pointed. If they go red again, **stop and say so** — deciding
what a chapter's new text means is a judgement call, and a line number that no
longer resolves can mean a table moved or that it changed.

`schema/live-cases.json` is **version 6**: 215 cases over 192 endpoints, 177
confirmed, 9 base-model steps, 67 named seeds, none unsupported. It dropped one
seed on 2026-09-18: `skew_node` re-created a node the shared base model already
builds, which npm refused as a setup collision.

---

## Task K — re-verify confirmed cases on the current build (closed)

**Live. Destructive: `/doc/NEW`. Closed on 2026-09-18; reopens on the next
build.**

Every confirmed case has passed through both SDKs, but many last ran on an older
build. A confirmed case failing on Build 09/15/2026 is a **regression**, and
that is exactly what this task exists to catch before a user does.

Measure the scope before each session; do not hand-count:

```bash
PYTHONIOENCODING=utf-8 python - <<'PY'
import json
cases = json.load(open("schema/live-cases.json", encoding="utf-8"))["cases"]
ledger = {}
def walk(node):
    if isinstance(node, dict):
        if isinstance(node.get("endpoint"), str) and "live_verified" in node:
            ledger[node["endpoint"]] = json.dumps(node["live_verified"])
        for value in node.values(): walk(value)
    elif isinstance(node, list):
        for value in node: walk(value)
walk(json.load(open("docs/coverage.json", encoding="utf-8")))
todo = sorted({c["endpoint"] for c in cases
               if c["confirmed"] and "09/15/2026" not in ledger.get(c["endpoint"], "")})
print(len(todo)); print(" ".join(todo))
PY
```

On 2026-09-17 it printed **107** of the 166 confirmed-case endpoints. It is a
text search of the ledger entry, so an entry that mentions the build for another
reason drops out of the list; that errs toward doing less, never toward a false
claim.

**On 2026-09-18 it reached 0, and this task is closed until the next build.**
All 107 were replayed that day through both SDKs on every product each case
declares. Task G accounts for three of them; the other 104 went through the
tier batches, each recorded in the live notes and the npm evidence scratch
under its own heading.

The command stays here because **a new build reopens the task**. When one
ships, change the build string and it names the new scope. Nothing else in this
section changes.

**Record all three places, or the next session re-runs the batch.** This is the
one mistake this task has actually made, twice, and the second time was worse
than the first. On 2026-09-17 a session recorded `/db/SLANch` in the live notes
and the npm evidence scratch and stopped before the ledger append, leaving one
passing endpoint in the to-do list. On 2026-09-18 the session that finished the
task did the same thing to all **eleven** of its last endpoints, left both
evidence files uncommitted, and reported the task complete — while its own copy
of this file still said twelve were left. The measurement reads the ledger and
nothing else, so evidence that never reaches `docs/coverage.json` does not
exist as far as any count is concerned.

**Before saying a batch is done**, re-run the scope command. If it has not
dropped by the number of endpoints you just ran, the ledger is what is missing —
go back and append, then commit the evidence files with it.

**Append, and change nothing else.** That same session moved `/db/PRST`'s
`date` from 2026-09-12 to 2026-09-18 while leaving `nx_versions` on build
09/02/2026. `ROADMAP.md` builds its session table from that pair, so the next
`gen_roadmap.py` run published a 2026-09-18 session on a build nothing ran on
that day. Both were corrected the same day. Diff the ledger against `HEAD`
before committing a batch — every change should be a `method` suffix and
nothing else:

```bash
git show HEAD:docs/coverage.json > /tmp/cov-head.json   # any scratch path
PYTHONIOENCODING=utf-8 python - <<'PY'
import json, os
def index(doc):
    out = {}
    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("endpoint"), str) and "live_verified" in node:
                out[node["endpoint"]] = node["live_verified"]
            for v in node.values(): walk(v)
        elif isinstance(node, list):
            for v in node: walk(v)
    walk(doc); return out
head = index(json.load(open("/tmp/cov-head.json", encoding="utf-8")))
now = index(json.load(open("docs/coverage.json", encoding="utf-8")))
print("non-method changes:", [(e, k) for e in now
      for k in set(head.get(e, {})) | set(now[e])
      if k != "method" and head.get(e, {}).get(k) != now[e].get(k)])
print("non-append method edits:", [e for e in now
      if head.get(e, {}).get("method") not in (None, )
      and not now[e]["method"].startswith(head[e]["method"])])
PY
```

Then run `python scripts/gen_roadmap.py` and commit `ROADMAP.md` with the
batch; it is generated, and leaving it behind is how the ledger and the roadmap
drift apart.

Batch by tier (`--tier`), at most 8 endpoints per selection, and run each batch
through **both** harnesses on **both** products in the same session — the
procedure is under "Running a live batch". Record each re-run by **appending**
to the entry's `method`: `Re-verified 2026-09-nn on Build 09/15/2026 through both
SDKs (Gen, Civil).` Do not touch `nx_versions` or `date`; they record the first
write, and an entry that loses that has lost information.

## Task B — the 22 that have a case and no passing run

**Live.** These endpoints are below write level although a case exists:

`/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
`/db/FIMP`, `/db/HPCE`, `/db/MADO`, `/db/MVLDch`, `/db/MVLDeu`, `/db/MVLDid`,
`/db/MVLDpl`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`, `/db/RPSC`, `/db/SBDO`,
`/db/SINF`, `/db/STCT`, `/db/TDMF`, `/db/WVLD`

Each one's last error is recorded verbatim in `docs/live_verification_notes.md`;
**read it before a run**, because re-running an unchanged fixture against an
unchanged build answers nothing.

- **Not yours:** `/db/ACTL` is settled product behaviour (Gen refuses every
  payload, including one with only its required fields; Civil accepts and does
  not persist `TOL`). `/db/FIMP`'s printed `ECU=0.003` violates the product's
  `Epsilon_cu > 0.8 / Z + Epsilon_co`, and no compliant value is documented.
  `/db/STCT` silently drops `iITER`/`TOL` on both products.
- **`/db/NLLP` blocks `/db/NLNK`, `/db/NLNK-M1` and `/db/CGLP`.** `nllp_seed`
  answered `Unknown Error` on both products again on 2026-09-17. Fix the seed
  first or those three stay blocked.
- `python scripts/check_fixture_contract.py` names **1 lead**: `/db/ACTL` sends
  `CLATS` on Gen while the contract tags it Civil-only. It is covered above.
- Fill a missing required field from the **contract's** description, enum or
  default, or from the manual's Request Example. If neither states a value,
  **stop and report it**; inventing one is hand-writing a payload.

**Eleven unconfirmed cases sit on endpoints that already have write level**, so
they move no count. All are recorded, and none is a task unless the cause below
changes:

| case | product | recorded cause |
| --- | --- | --- |
| `/db/LLANch`, `/db/SLANch`, `/db/LLANid`, `/db/IMPF` | gen | Gen answers `Unavailable moving load code` for the code these lanes need |
| `/db/LLANop`, `/db/SLANop` | gen | refused under `BS`, the code chapter 08 gives Gen for this family |
| `/db/LCOM-SEISMIC` | civil | the documented `ANAL="RS"` combination answers `The Load Combination Type is not supported.` with a real `/db/SPLC` |
| `/db/HHCT` | civil | POST accepted, expected value not read back |
| `/db/NLCT` | civil | `LINE_SEARCH_OPTION` required when `OPT_ENABLE_LINE_SEARCH` is true |
| `/db/DSTL` | gen, civil | passes on Civil; Gen answers `Errors detected in Steel Design Control Data.` |
| `/db/EPMT` | civil | `Wrong Field` for the request Gen accepts |

`/db/NLCT`'s Civil message names the missing field. If the contract documents a
value for `LINE_SEARCH_OPTION`, that one is a fixture fix you may make, under the
rules above.

## Task A — the 21 `/db` endpoints with no case

**Offline to build, live to run.** 18 are buildable:

| chapter | endpoints |
| --- | --- |
| 04 Properties | `EPMT-M1`, `FIBR`, `IEHG`, `IEHG-BEAM-M1`, `IMFM`, `IMFM-M1` |
| 07 Temperature/Prestress | `PTNS`, `TDCS`, `TDNA`, `TDNT`, `TDPL` |
| 14 Pushover | `PHGE`, `POGD`, `POGD-M1` — unconfirmed `extras17` fixtures added 2026-09-18; await a live session |
| 24 Design | `RCHK`, `REBB`, `REBR`, `REBW` |
| 08 Moving Loads | `MVLDbs` — **blocked**, see below |
| 05 Boundary | `DRLS` |
| 10 Construction Stage | `CSCS` |

The other three, `IEHG-GL-M1`, `IEHG-PSS-M1` and `IEHG-TRUSS-M1`, have no manual
schema and `/info` 404s for them. **Do not build a fixture for them.**

`extras17` uses only contract/manual values: the PHGE request examples' element
1-to-2 assignment, POGD's common nonlinear-control fields (excluding the
product-specific `PHOP_OPT` members), and POGD-M1's documented no-initial-load
PUT branch. All three cases remain `confirmed: false` until both public SDKs
pass on every declared product.

`/db/MVLDbs` stays blocked: its contract marks mutually exclusive `LCDATA_*`
objects required together, and its two-value `ALL_MODE` condition needs a
contract-shape decision first.

Per endpoint:

1. Read the manual chapter and any entry in `docs/live_verification_notes.md`
   first. Chapters 04 and 24 matter most: `/db/REBW` and `/db/REBC` are the
   confirmed cases where a manual section is wrong about its own field names.
2. Build the fixture **from the contract** or the manual's Request Example.
3. Add the case to the right tier in `scripts/live_crud_check.py` with
   `confirmed=False`, list its `needs` **in build order**, then `--emit-cases`.
4. **A seed that owns a fixed id is shared whether or not it was written as
   one.** Check no other tier's seed POSTs the same id; `/db/SPLC` and
   `/db/MVCD` both collided that way.
5. **A seed must be expressible in the fixture**: Assign POSTs and per-id
   DELETEs. A seed that reads state back and branches cannot be exported; the
   emitter reports it under `unsupportedSeeds`, which is 0 today and should stay
   0. Do not add to `FRESH_DOCUMENT_SEEDS` or use `setup_replaces` without
   asking — both are representation decisions.
6. `python scripts/check_fixture_contract.py` before running live. If your new
   case appears there, fix that first.
7. Run it through both harnesses on both products (below). Passed on a product →
   `confirmed=True` for that product, `level: "write"` in `docs/coverage.json`,
   `python scripts/gen_roadmap.py`. Failed → leave it unconfirmed and record the
   verbatim error in the live notes.

`/db/TDNA`'s `CURVE` variant declares `bPJ`, and every manual CURVE example sends
it, so a fixture built from those examples may too.

## Task E — merge the unmerged tables: not yours to start

`docs/unmerged_tables_against_info.md` splits **72 tables (482 names) across 15
contracts**. Eleven batches already merged every table that could be merged
mechanically, and an audit found none left among the 32 one-object tables:
their manual does not state a complete wire discriminator, or the extractor
cannot reproduce the documented nesting, or both products reject the branch.
The 25 scattered tables need a judgement about which `/info` object is meant.
Do not rescan any of it as a queue.

---

## Running a live batch

1. **Ask the author before the first product call of a session.** Then confirm
   each document is open and empty with **that product's own key**:
   `GET /db/NODE` and `GET /db/ELEM` return no records.
2. npm: from `packages/typescript`, `npm run live:crud -- -- --product gen
   --endpoints /db/A,/db/B` (PowerShell takes two `--`, Bash one), with
   `MIDAS_MAPI_KEY` set to that product's key and `--save-dir C:/temp`.
3. Python, same selection, same session: `python scripts/live_crud_check.py
   --product gen --endpoints /db/A,/db/B --save-as C:/temp/<name>.mgbx`
   (`.mcbz` on Civil).
4. Repeat both for `civil`.
5. Record the npm result in `docs/npm_live_evidence_scratch.md` (one row per
   endpoint: date, products, and the Count line), and **append** to the entry's
   `method` in `docs/coverage.json`. `report_npm_replay_coverage.py --check`
   fails if the ledger claims an npm replay the inventory does not carry.
6. A confirmed case failing is a **regression**: report it verbatim, do not
   change the fixture to make it pass, and do not flip `confirmed`. A `BLOCK`
   (exit 3) means a seed failed and says nothing about the endpoint.

Selection traps, each of which has cost a session:

- **A case whose setup touches a table with no per-id DELETE** — `/db/GRUP`,
  `/db/BNGR` — may only be the **last** endpoint of an npm invocation, because
  the document reset is its cleanup. Give each such case its own invocation.
- **An `--endpoints` selection can drop a case another case depends on**, and
  the Python harness does not warn. In `extras14`, `/db/DYFG` and `/db/DYNF`
  need that tier's `/db/MVCD` case to switch the code to EUROCODE; select
  `/db/MVCD` with them. They read as a regression on 2026-09-16 and were not one.
- **Selecting `moving` and `extras14` together** makes `mvcd_ksce_seed` answer
  `Key Already Exist`, because `moving` already created `/db/MVCD` id 1.

---

## Closed — do not reopen

| what | outcome | where |
| --- | --- | --- |
| re-verification on Build 09/15/2026 (Task K) | all 107 confirmed-case endpoints replayed through both SDKs on every declared product, 2026-09-18; the scope command prints 0. The section stays because the next build reopens it | live notes, 2026-09-18 |
| meaningful update assertions (was Task G) | MATD now proves `MAINREBAR_B_FY: 500000`; IEHC proves `BEAM_LOC: 1 -> 2`; POLC-M1 proves `NLTYPE: PDELTA -> NONE`. Both SDKs passed every declared product on 2026-09-18, Build 09/15/2026 | live notes, 2026-09-18 |
| npm replay of every confirmed case (was Task F) | 177 of 177, 2026-09-17; fixture v6 added per-id DELETE seed steps, `FRESH_DOCUMENT_SEEDS`, `expected.unordered` and `setup_replaces` | live notes, 2026-09-17 (later) |
| `DESIGN/STEEL/DSTL` contract and PUT (was Tasks H, I) | contracted; Gen accepts the documented PUT, Civil refuses it with `Errors detected in Steel Design Control Data.` **Do not re-run it**: the enum has one value, so there is nothing to vary | live notes; contract PUT `notes` |
| `USE_HAMBLY_EQ` read probe (was Task J) | absent from a DB/User solid section's record on both products; composite sections unprobed, and no confirmed fixture builds one | live notes, 2026-09-17 (later) |
| crash re-tests on Build 09/15/2026 | all historical crash paths clean except `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK`. **Never call OCHECK**: it crashes Gen, MIDASIT has closed it as unsupported, and each call costs a restart and a held licence | live notes, 2026-09-16 (later) |
| manual sync to `a6947a7` | reflected; 108 anchors re-mapped across 59 contracts. At the next sync, map every anchor in a changed chapter, not only the ones the drift check names | `docs/release_notes_v2.8.2.md`; this file at `0fff09d` |
| `safeToOmit` re-derivation (was Task C) | 21 claims grounded, 36 left `unverified`. Re-derive at the end of any session that confirms a case, and report the count | git history `fa1332b` |
| the 21 "unrecorded variant names" (was Task D) | the checker's own defect, not 21 defects. A new checker's first count is a hypothesis | — |

## Decisions that are open and are not yours

- **`/db/SPLC`'s `NDP` requiredness** — the manual nests it under the Optional
  `bNDP` switch without stating a wire rule. Do not add an `appliesWhen` or a
  `safeToOmit` for it.
- **`/db/SPLC`'s cross-tier id collision** — extras4's `lcom_seismic_splc` seed
  and extras5's Civil case both own id 1, and the family renumbers, so a
  different id does not fix it. It reports `BLOCK`, honestly.
- **`/db/THIS-M1`'s 20 `/info` properties with no manual row** — the ceiling in
  `info_baseline.py` holds the number. Do not raise it.
- **`/db/SECT`'s `USE_HAMBLY_EQ` and the `/info` baseline** — added by Build
  09/15/2026 on both products, documented nowhere. Do not add it to the contract
  and **do not re-capture `schema/info-baseline.json`**; CI fails when the
  uncontracted set grows. At the next manual sync, check whether
  `04_DB_Properties.md`'s 공통 Specifications table grows a row (13).
- **What Civil NX needs before `DESIGN/STEEL/DSTL` accepts a PUT**, and why Gen
  refuses `/db/DSTL`'s POST with the same message.
- **`/db/MVLDbs`'s contract shape** (Task A).

## Live-session rules

- **If `GET /db/NODE` says `The project is not opened`, stop and ask for a
  document.** A `/doc/NEW` sent to Gen NX with no project open blocked the
  session on 2026-09-17 until the product was brought back up.
- **`.env` holds `MIDAS_MAPI_KEY_GEN` and `MIDAS_MAPI_KEY_CIVIL`**, no plain
  `MIDAS_MAPI_KEY`. A mismatched key still answers `connected` and returns 0
  records, so check each product with its own key.
- **`verify_connection()` cannot prove a session is alive.** It answers
  `connected` while a modal dialog holds the product; use a real `GET /db/NODE`.
- **Paths belong to the NX machine.** `--save-dir` is required and never inferred
  from `verify_connection()["user"]`, which is an email. `C:/temp` exists; the
  author manages it.
- **A GET can pop a modal dialog** if the open document lives under
  `Program Files`.
- **Three harnesses call `/doc/NEW` and discard unsaved work**:
  `scripts/live_smoke.py`, `scripts/live_crud_check.py`,
  `packages/typescript/scripts/live-crud.mjs`.
- **Assert a reset, do not assume it.** `/doc/NEW` without `{"Argument": {}}` is
  HTTP 500 and resets nothing.
- **Never hand-write a live payload.** Use the fixture or a contract.

## Repository rules that keep catching people

- **`contracts/` is the source of truth; neither SDK and no fixture is a source
  for it.** Permitted sources: the manual repo, `docs/live_verification_notes.md`
  and live `/info`.
- **`documentedOptional` is about the docs; `safeToOmit` is about the product.**
- **`/info` is neither a superset nor a subset of what the server accepts.**
  Where `/info` and a live round trip disagree, the round trip wins.
- **A wire value is not a majority opinion.** Three documents agreeing can be
  three transcriptions of one typo; only a live check settles one.
- **Never put `MAPI-xxxx` or MIDASIT's internal tracker in anything that
  ships**, release notes included.
- **An official article has a locale, and locales differ.** Name the locale you
  quote.
- **A 200 does not mean success**, and error bodies also arrive under 201.
- **`DELETE {endpoint}` with an ID-keyed body empties the whole table.**
- **Never commit a GET response body** — it is the author's model contents.
- **`contracts/` mixes CRLF and LF files.** Edit them as bytes; a deletion count
  on an insert-only change means you corrupted line endings.
- Windows consoles are cp949: keep user-facing exception text ASCII.
