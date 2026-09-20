# Codex task prompt — mechanical work only

Updated 2026-09-20. Rewritten from scratch after the 2026-09-19 live sessions
emptied most of the old queue. The previous version (`6e8dcab` and earlier)
listed 14 Task A endpoints as buildable; checked against their contracts, 13
of them are blocked or need a judgement, and the remaining `/db/PTNS` case
passed on 2026-09-20. **The Codex queue is now empty.** Do not grow it by
relabelling something below as mechanical.

## Where things stand

- **Both products are on Build 09/15/2026** (Gen NX 2026 v2.1, Civil NX 2026
  v2.2).
- **2.8.3 is published on PyPI and npm.** No release is warranted and none is
  yours to start: the author picks the number and asks for it explicitly.
  One npm-surface change is waiting for the next release notes: `/db/TDNT`'s
  `FT`, `FPK` and `TDMFNAME` became optional, each with its `appliesWhen`
  condition in JSDoc (`c76bff0`).
- **Coverage: 400/400 implemented, 207 write / 193 read.** Of the 225 `/db`
  endpoints, 185 are write-level and 40 are not.
- **Fixture (`schema/live-cases.json`, version 6):** 220 cases over 196
  endpoints; 183 confirmed over 172 endpoints; 9 base-model steps; 77 named
  seeds; 0 unsupported.
- **npm has replayed all 183 confirmed cases** on every product each declares.
  Keep that gap at 0: every new confirmed case goes through both harnesses.
- **Contracts: 384 endpoints + 87 result tables.** The three drafts left, the
  IEHG trio, have no permitted source; that is final.

## The division, set by the author

Judgement-heavy work is Claude's: schema design, what a contradictory manual
means, how a seed or case is represented, what a live failure says about the
product. Bounded, verifiable, repeatable work is yours. **A task that turns
out to need a judgement is one to stop and report, not to decide.** If Task P
is done and no new build has shipped, there is no Codex work — say so rather
than finding some.

## Your queue

| task | kind | state |
| --- | --- | --- |
| **P** — build and run a `/db/PTNS` case | offline build, then live | **complete 2026-09-20** |
| **K** — re-verify confirmed cases on a new build | live, destructive | dormant; reopens when a build newer than 09/15/2026 ships |

Everything else is inventoried under "Not yours", with the reason for each
endpoint, so you can check a claim of "nothing left" against it.

---

## Measured starting state

Run these first. **If a number differs, say so before starting** — something
moved under you, and the command wins over this file.

```bash
python -m pytest -q                       # 1087 passed
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
                                          # endpoint, 3 contract gaps over 2
python scripts/report_npm_replay_coverage.py --check   # 183 cases over 172
                                          # endpoints; every product: 183
python scripts/report_unmerged_tables.py --check       # exit 0
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 83 tests
```

**A manual sync is not yours to reflect.** The manual repo is vendored at
`e64a682`. If the drift or extraction check goes red, **stop and say so** —
deciding what a chapter's new text means is a judgement, and a line reference
that no longer resolves can mean a table moved or that it changed.

---

## Task P — `/db/PTNS` (Pretension Loads, ch07 section 11)

**Complete.** This was the last `/db` endpoint without a case whose every
prerequisite a confirmed fixture or a manual example already supplied.

**2026-09-20 result:** the `extras19` fixture, its three-step prerequisite
chain and its structural regression test passed every offline gate. The built
npm package and Python SDK then completed create/read/update/read/delete/read
on Gen and Civil, Build 09/15/2026; `TENSION` changed from 130 to 260 and read
back correctly. The fixture is confirmed and the ledger is write-level.

What the case needs, in build order, and where each piece comes from:

1. **A truss element.** PTNS applies to truss/cable elements (ch07 §11's first
   line); the base model's elements 1–3 are all `BEAM`. Seed one element with
   ch03's `TRUSS` example (`03_DB_Node_Element.md`, the `#### TRUSS` block:
   `TYPE "TRUSS"`, `MATL 1`, `SECT 1`, `ANGLE 0`). Change only the key and the
   `NODE` pair, to nodes the base model already builds. Before choosing the
   element id, check that no other tier's seed POSTs it; `/db/SPLC` and
   `/db/MVCD` both collided that way.
2. **A load case**: the existing `prestress_load_cases` seed (`PS15_SEED`,
   `PS16_SEED`). It is already in `RENUMBERING_SEEDS`. Do not add another STLD
   seed.
3. **The load case registered as External Type in `/db/EXLD`.** ch07 §11's
   example says so (`하중 케이스 PrS1은 EXLD에서 External Type으로 별도 지정 필요`).
   Seed it with the create payload of extras15's confirmed `/db/EXLD` case:
   id 1, `{"LCNAME_ITEM": ["PS15_SEED"]}`. **That case also owns id 1**, so the
   PTNS case goes in a **new tier** (`extras19`), not in extras15.
4. **The PTNS case**, keyed on the truss element id, built from ch07 §11's
   request body with `LCNAME` set to `PS15_SEED` and `GROUP_NAME` `""` (the
   Python example's value). Make the update change `TENSION` (130 → 260) and
   assert it. An update identical to the create proves nothing; two cases were
   rebuilt on 2026-09-19 for that reason.

Then:

- `confirmed=False`, `needs` in build order, `products` from the contract
  (`[civil, gen]`), `--emit-cases`, and a test in `tests/test_live_cases.py`
  that the tier seeds each step it depends on (the extras18 test is the
  pattern).
- `python scripts/check_fixture_contract.py --check` before running live.
- Run it through both harnesses on both products ("Running a live batch").
  Passed on a product → `confirmed=True` for that product and a ledger
  promotion ("Recording a run"). Failed → leave it unconfirmed and record the
  verbatim error in the live notes.
- **If a step fails for a reason the fixture cannot fix** — the truss seed is
  refused, EXLD refuses the seed, PTNS answers something that needs a value no
  source states — **stop and report it.** Do not permute fields; that is
  hand-writing a payload.

## Task K — re-verify confirmed cases on a new build (dormant)

**Live. Destructive: `/doc/NEW`.** Closed for Build 09/15/2026 on 2026-09-18.
When a newer build ships, this command names the scope — change the build
string to the **old** build and it lists every confirmed-case endpoint not yet
re-run on anything newer. Do not hand-count.

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
BUILD = "09/15/2026"   # replace with the NEW build's string
todo = sorted({c["endpoint"] for c in cases
               if c["confirmed"] and BUILD not in ledger.get(c["endpoint"], "")})
print(len(todo)); print(" ".join(todo))
PY
```

It is a text search of the ledger entry, so an entry that mentions the build
for another reason drops out; that errs toward doing less, never toward a false
claim. With `BUILD = "09/15/2026"` it prints 0 today.

Batch by tier (`--tier`), at most 8 endpoints per selection, through **both**
harnesses on **both** products in the same session. A confirmed case failing is
a **regression**: report it verbatim, do not change the fixture, do not flip
`confirmed`. **Before saying a batch is done, re-run the scope command**; if it
did not drop by the number you ran, the ledger append is what is missing.

---

## Running a live batch

1. **Ask the author before the first product call of a session.** Then confirm
   each document is open and empty with **that product's own key**:
   `GET /db/NODE` and `GET /db/ELEM` return no records. If `GET /db/NODE` says
   `The project is not opened`, stop and ask for a document — do not send
   `/doc/NEW`.
2. In Git Bash, `export MSYS_NO_PATHCONV=1` first, or `/db/PTNS` arrives as
   `C:/Program Files/Git/db/PTNS` and the harness exits 2 before any product
   call.
3. npm: from `packages/typescript`, `npm run live:crud -- -- --product gen
   --endpoints /db/A,/db/B --save-dir C:/temp` (PowerShell takes two `--`, Bash
   one), with `MIDAS_MAPI_KEY` set to that product's key.
4. Python, same selection, same session: `python scripts/live_crud_check.py
   --product gen --endpoints /db/A,/db/B --save-as C:/temp/<name>.mgbx
   --out <report>.json` (`.mcbz` on Civil). The Python harness refuses to run
   (exit 2) when `schema/live-cases.json` has drifted from the script; re-emit,
   never hand-edit the fixture.
5. Repeat both for `civil`.
6. A `BLOCK` (exit 3) means a seed failed and says nothing about the endpoint.

Selection traps, each of which has cost a session:

- **A case whose setup touches a table with no per-id DELETE** — `/db/GRUP`,
  `/db/BNGR` — may only be the **last** endpoint of an npm invocation, because
  the document reset is its cleanup. Give each such case its own invocation.
- **An `--endpoints` selection can drop a case another case depends on**, and
  the Python harness does not warn. `extras14`'s `/db/DYFG` and `/db/DYNF` need
  that tier's `/db/MVCD` case; select them together.
- **Selecting `moving` and `extras14` together** makes `mvcd_ksce_seed` answer
  `Key Already Exist`.
- **A seed on a table that renumbers** (STLD, FBLD, …) must be listed in
  `RENUMBERING_SEEDS`, or npm refuses its setup as a collision. `SeedStep` has
  no flag for it; the set is the only place.
- **A tier's seeds are not per-case.** The Python runner executes every seed of
  a selected tier before that tier's cases, so a tier that splices another
  tier's seed list POSTs those records twice whenever both are selected — a
  full re-verification does exactly that. Give a new tier its own seeds, even
  when an existing one looks identical; extras19 was built the other way on
  2026-09-20 and rebuilt the same day (live notes).

## Recording a run — three places, every time

A run that reaches only some of these did not happen as far as any count is
concerned. This is the one mistake this work has actually made, twice: on
2026-09-17 one endpoint and on 2026-09-18 eleven were recorded in the evidence
files and never reached the ledger, and the second session reported its task
complete.

1. **The fixture** — `confirmed=True` per product that passed, then
   `--emit-cases`.
2. **The ledger**, `docs/coverage.json` — see below.
3. **The evidence files** — `docs/live_verification_notes.md` (what ran, on
   which build, verbatim errors) and `docs/npm_live_evidence_scratch.md` (one
   row per npm success: date, products, Count line).
   `report_npm_replay_coverage.py --check` fails if a ledger `method` says
   `npm replayed the same emitted fixture` and the scratch file has no row.

Then `python scripts/gen_roadmap.py` and commit `ROADMAP.md` with the batch.

**The ledger has two kinds of change, and only two.**

- **A re-verification appends** to `method` and changes nothing else:
  `Re-verified 2026-09-nn on Build mm/dd/yyyy through both SDKs (Gen, Civil).`
  `date` and `nx_versions` record the first write; on 2026-09-18 a session
  moved `/db/PRST`'s `date` without its `nx_versions`, and `ROADMAP.md`
  published a session on a build nothing ran on.
- **A read → write promotion** sets `date`, `nx_versions`, `level: "write"`,
  `outcome` and `products` **from the write**, where `products` lists only the
  products the write passed on. The older read evidence stays at the start of
  `method`. `/db/DSTL` is the precedent. Do not write phrases like "stays
  read-level" into a write entry: `test_no_ledger_entry_contradicts_its_own_level`
  rejects them. Say "Gen's evidence is the read above" instead.

`docs/coverage.json` mixes CRLF and LF lines. Edit it as bytes (find the entry
by its endpoint string and match braces), not with a whole-file rewrite.
Before committing, diff it against `HEAD`; every change should be one of the
two kinds above:

```bash
git show HEAD:docs/coverage.json > /tmp/cov-head.json   # any scratch path
PYTHONIOENCODING=utf-8 python - <<'PY'
import json
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
for e in now:
    changed = sorted(k for k in set(head.get(e, {})) | set(now[e])
                     if head.get(e, {}).get(k) != now[e].get(k))
    if not changed: continue
    promoted = head.get(e, {}).get("level") == "read" and now[e]["level"] == "write"
    appended = now[e]["method"].startswith(head.get(e, {}).get("method", ""))
    kind = "promotion" if promoted else ("append" if changed == ["method"] and appended else "CHECK THIS")
    print(f"{kind:10} {e}: {changed}")
PY
```

---

## Not yours — the whole inventory

Each `/db` endpoint below write level is here, with the reason. **Read its
entry in `docs/live_verification_notes.md` before touching it**: re-running an
unchanged fixture on an unchanged build answers nothing, and on 2026-09-19 all
15 runnable Task B cases were re-run and every answer matched the earlier build
word for word.

### 23 endpoints with a case that has never passed

| endpoint | last answer / reason | blocker |
| --- | --- | --- |
| `/db/EPST`, `/db/EPSE` | `Wrong Field` | every documented value set on EPST varied (`SEL_TYPE`, `EP_TYPE`, `ELEM_TYPE`, `DIR`); EPSE shares its fields |
| `/db/WVLD` | `Wrong Field` | refuses even a bare `NAME` — not a value |
| `/db/TDMF` | `Wrong Field` | sends no field with a value set to vary |
| `/db/RPSC` | `Wrong Field` | `/info` lists `MBARS[].MBAR_ITEMS[].PART`, which the fixture never sends; no source states a value |
| `/db/HPCE` | `Wrong Key` | product finding |
| `/db/FBLA`, `/db/MVLDeu`, `/db/PHGE` | `Unknown Error` | product finding |
| `/db/MADO`, `/db/SBDO`, `/db/DOEL`, `/db/SINF`, `/db/MVLDpl` | POST accepted, record not stored | product finding |
| `/db/ACTL` | Gen refuses every payload; Civil accepts and drops `TOL` | settled product behaviour |
| `/db/STCT` | drops `iITER`/`TOL` on both products | settled product behaviour |
| `/db/FIMP` | printed `ECU=0.003` violates the product's `Epsilon_cu > 0.8 / Z + Epsilon_co` | no compliant value documented |
| `/db/NLLP` | `nllp_seed` answers `Unknown Error` on both | — |
| `/db/NLNK`, `/db/NLNK-M1`, `/db/CGLP` | blocked by `nllp_seed` | NLLP |
| `/db/TDNA` | `Errors detected in Tendon Profile Data.(Item:IS_DB_TDNA_NOTENSIONCALC : Not Registered String)` | a model precondition; do not permute fields |
| `/db/TDPL` | blocked by the TDNA seed | TDNA |

### 17 endpoints with no case

| endpoint | why it is not buildable mechanically |
| --- | --- |
| `/db/IMFM`, `/db/IMFM-M1` | every name field is a **FIMP** property name (`Fiber Model Property Name`); blocked by `/db/FIMP` |
| `/db/FIBR` | a fiber division needs FIMP materials; blocked by `/db/FIMP` |
| `/db/IEHG` | `FIBER_NAME` names a FIBR division (blocked), and `PROP_NAME` an inelastic hinge property that no endpoint creates |
| `/db/IEHG-BEAM-M1` | `INEL_PROP_NAME` names an inelastic hinge property that no endpoint creates |
| `/db/EPMT-M1` | contract is `/info`-only: no value stated anywhere, so any payload would be hand-written |
| `/db/CSCS` | needs a `COMPOSITE` section; the manual's only sample omits its dimensions and Gen refuses it (live notes, 2026-09-01) |
| `/db/TDCS` | needs CSCS and the TDNA seed; both blocked |
| `/db/DRLS` | Gen-only; `/info` carries a `DUMMY` placeholder the contract waives — representation decision |
| `/db/RCHK`, `/db/REBB`, `/db/REBR`, `/db/REBW` | ch24 design rebar; REBW's manual section is known wrong about its own field names, and each needs a designed RC member — judgement |
| `/db/MVLDbs` | contract marks mutually exclusive `LCDATA_*` objects required together, and `ALL_MODE`'s two-value condition needs a shape decision |
| `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`, `/db/IEHG-TRUSS-M1` | no manual schema and `/info` 404s — **never** build a fixture |

### Unconfirmed cases on endpoints already at write level

They move no count. None is a task unless its cause changes.

| case | product | recorded cause |
| --- | --- | --- |
| `/db/LLANch`, `/db/SLANch`, `/db/LLANid`, `/db/IMPF` | gen | `Unavailable moving load code` for the code these lanes need |
| `/db/LLANop`, `/db/SLANop` | gen | refused under `BS`, the code ch08 gives Gen for this family |
| `/db/LCOM-SEISMIC` | civil | documented `ANAL="RS"` answers `The Load Combination Type is not supported.` |
| `/db/HHCT` | civil | POST accepted, expected value not read back |
| `/db/NLCT` | civil | `LINE_SEARCH_OPTION` required when `OPT_ENABLE_LINE_SEARCH` is true; the contract records no value for it |
| `/db/DSTL` | gen | `Errors detected in Steel Design Control Data.` |
| `/db/EPMT` | civil | `Wrong Field` for the request Gen accepts |
| `/db/POGD` | gen | `Wrong Field` for the payload Civil accepts |

`check_fixture_contract.py`'s one lead, `/db/ACTL` sending `CLATS` on Gen, is
covered above.

### Task E — merge the unmerged tables

`docs/unmerged_tables_against_info.md` splits 72 tables (482 names) across 15
contracts. Every mechanically mergeable table is merged; what is left needs a
judgement about which `/info` object is meant. Do not rescan it as a queue.

---

## Closed — do not reopen

| what | outcome | where |
| --- | --- | --- |
| Task P `/db/PTNS` | the manual TRUSS + STLD + EXLD chain passed through npm and Python on Gen and Civil; write-level. 2026-09-20 | live notes, 2026-09-20 |
| Task A reclassified | 13 of the 14 "buildable" endpoints are blocked or need a judgement (inventory above); PTNS was the one mechanical remainder and is now closed. 2026-09-20 | this file |
| the five `Wrong Field` Task B cases | not bad values: EPST's documented values exhausted, WVLD fails on a bare `NAME`, RPSC's `PART` has no source, TDMF has nothing to vary. `/info` rooting RPSC at `Argument` is not a wrapper signal — all 399 do. 2026-09-19 | live notes, 2026-09-19 (later) |
| moving-load country cases | `/db/MVLDch`, `/db/MVLDid` pass on Civil once each case's vehicle is seeded from ch08; MVLDid's `Number of Sub-Load Cases` was the missing vehicle. 2026-09-19 | live notes, 2026-09-19 (later) |
| batches 17 and 18 | `/db/TDNT` (both), `/db/POGD` (Civil), `/db/POGD-M1` reached write. 2026-09-19 | live notes, 2026-09-19 |
| re-verification on Build 09/15/2026 (Task K) | all 107 confirmed-case endpoints replayed through both SDKs, 2026-09-18 | live notes, 2026-09-18 |
| meaningful update assertions | MATD, IEHC, POLC-M1 prove a changed value. 2026-09-18 | live notes, 2026-09-18 |
| npm replay of every confirmed case | complete since 2026-09-17; 183 of 183 now | live notes, 2026-09-17 (later) |
| `DESIGN/STEEL/DSTL` PUT | Gen accepts; Civil refuses. **Do not re-run**: one enum value, nothing to vary | contract PUT `notes` |
| crash re-tests on Build 09/15/2026 | clean except `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK`. **Never call OCHECK**: it crashes Gen and each call costs a restart and a held licence | live notes, 2026-09-16 (later) |
| manual sync to `e64a682` | reflected; 17 contracts' line references re-pointed | git history |

## Decisions that are open and are not yours

- **Contract `verification` records lag the ledger.** 47 contracts cite a read
  sweep for an endpoint `docs/coverage.json` records at write level (TDNT,
  POGD, MVLDch and MVLDid among them). No check compares the two; folding the
  ledger into `contracts/verification/` is planned in `contracts/README.md`.
  Do not hand-edit `verification` blocks to match.
- **`/db/SPLC`'s `NDP` requiredness** — nested under the Optional `bNDP`
  switch with no wire rule. No `appliesWhen`, no `safeToOmit`.
- **`/db/SPLC`'s cross-tier id collision** — extras4's `lcom_seismic_splc` and
  extras5's Civil case both own id 1, and the family renumbers. It reports
  `BLOCK`, honestly.
- **`/db/SPLC`'s `aACCECC_ECCEN_LIST[].ALONG`** is created but never updated
  (recorded in the contract's PUT `notes`).
- **`/db/THIS-M1`'s 20 `/info` properties with no manual row** — do not raise
  the ceiling in `info_baseline.py`.
- **`/db/SECT`'s `USE_HAMBLY_EQ`** — added by Build 09/15/2026, documented
  nowhere. Do not contract it and **do not re-capture
  `schema/info-baseline.json`**.
- **`/db/MVLDbs`'s contract shape**, and everything in the "no case" table
  marked judgement.

## Live-session rules

- **`.env` holds `MIDAS_MAPI_KEY_GEN` and `MIDAS_MAPI_KEY_CIVIL`**, no plain
  `MIDAS_MAPI_KEY`. Never print either. A mismatched key still answers
  `connected` and returns 0 records, so check each product with its own key.
- **`verify_connection()` cannot prove a session is alive.** It answers
  `connected` while a modal dialog holds the product; use a real `GET /db/NODE`.
- **Paths belong to the NX machine.** `--save-dir`/`--save-as` are required and
  never inferred from `verify_connection()["user"]`, which is an email.
  `C:/temp` exists; the author manages it — do not clean it.
- **A GET can pop a modal dialog** if the open document lives under
  `Program Files`.
- **Three harnesses call `/doc/NEW` and discard unsaved work**:
  `scripts/live_smoke.py`, `scripts/live_crud_check.py`,
  `packages/typescript/scripts/live-crud.mjs`. Never against a document the
  author has not confirmed empty.
- **Assert a reset, do not assume it.** `/doc/NEW` without `{"Argument": {}}` is
  HTTP 500 and resets nothing.
- **Never hand-write a live payload.** Use the fixture, a contract or a manual
  example.

## Repository rules that keep catching people

- **`contracts/` is the source of truth; neither SDK and no fixture is a source
  for it.** Permitted sources: the manual repo, `docs/live_verification_notes.md`
  and live `/info`.
- **`documentedOptional` is about the docs; `safeToOmit` is about the product.**
- **`/info` is neither a superset nor a subset of what the server accepts.**
  Where `/info` and a live round trip disagree, the round trip wins.
- **`appliesWhen`'s `in` needs at least two values**; use `equals` for one.
- **Never put `MAPI-xxxx` or MIDASIT's internal tracker in anything that
  ships**, release notes included. The manual repo now names one; do not copy
  it here.
- **A 200 does not mean success**, and error bodies also arrive under 201.
- **`DELETE {endpoint}` with an ID-keyed body empties the whole table.**
- **Never commit a GET response body** — it is the author's model contents.
- **`contracts/` and `docs/coverage.json` mix CRLF and LF.** Edit them as
  bytes; a deletion count on an insert-only change means corrupted line endings.
- Windows consoles are cp949: keep user-facing exception text ASCII.
