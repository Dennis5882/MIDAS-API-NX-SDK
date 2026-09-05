# Codex task prompt — mechanical work only

Updated 2026-09-05 at `bbbcdc9`. **2.7.8 is published** on both registries. A
release is now warranted and unreleased — `src/midas_nx` docstrings changed —
but **the number is the author's call**, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

The previous five tasks are all closed. What they settled is near the bottom,
and two of them left open decisions that are not yours.

**If a product session is available, start at Task A. If not, start at Task C.**

---

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 1017 passed
ruff check src tests scripts && mypy      # clean; 41 source files
python scripts/validate_contracts.py      # OK; 381 endpoints, 4956 fields,
                                          # 119 proven safe, 8 unsafe,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check
python scripts/info_baseline.py --divergence --check
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # blank 71, short row 20,
                                          # second key column 3
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 54 fixture leads over 8
                                          # endpoints, 27 contract gaps over 8
python scripts/report_unmerged_tables.py --check       # report is current
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # 304 resources (301 by contract),
                                          # 764 payload types; no drift; 70 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 173 write / 226
read.** `schema/live-cases.json` is **version 5**: 167 cases, 144 confirmed, 9
base-model steps, 46 named seeds, and 3 unsupported seeds that block 4 npm cases
by design. npm live evidence: **47 `/db` endpoints**. Drafts: 3, the IEHG trio,
refused for a reason that will not go away — that is the finished state, not a
backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## Task A — the 55 `/db` endpoints with no live case at all

**Live. Destructive: `/doc/NEW`.** The largest single block of remaining work,
and the only one that moves `ROADMAP.md`'s write count.

72 `/db` endpoints are still read-level. 17 have a case that has never passed
(Task B). The other **55 have no case at all**, and they cluster by chapter:

| chapter | count | endpoints |
| --- | ---: | --- |
| 08 Moving Loads | 18 | `IMPF`, `LLANch`, `LLANid`, `LLANop`, `LLANtr`, `MLSP`, `MLSR`, `MVHLtr`, `MVLDbs`, `MVLDch`, `MVLDeu`, `MVLDid`, `MVLDpl`, `MVLDtr`, `SINF`, `SLAN`, `SLANch`, `SLANop` |
| 04 Properties | 13 | `EPMT`, `EPMT-M1`, `FIBR`, `FIMP`, `IEHC`, `IEHG`, `IEHG-BEAM-M1`, `IEHG-{GL,PSS,TRUSS}-M1`, `IMFM`, `IMFM-M1`, `MATD` |
| 07 Temperature/Prestress | 7 | `EXLD`, `PRST`, `PTNS`, `TDCS`, `TDNA`, `TDNT`, `TDPL` |
| 14 Pushover | 6 | `IEPI`, `PHGE`, `POGD`, `POGD-M1`, `POLC`, `POLC-M1` |
| 24 Design | 4 | |
| 12 Analysis Control | 3 | |
| 09 Dynamic Loads | 2 | |
| 05 Boundary / 10 Construction Stage | 1 each | |

**Start with chapter 08's lane family** — the largest coherent group, and three
of them moved in 2.7.7: `/db/LLANch` and `/db/LLANid` take `{COMMON,
LANE_ITEMS}`, **not** a flat record (the server never accepted the flat one),
and all four `/db/LLAN*` now carry `SPECIAL_LANE_ITEMS`. Build from the
contract, not from memory and not from an older sibling.

Per endpoint:

1. Read the manual chapter and any entry for it in
   `docs/live_verification_notes.md` **first**.
2. Build the fixture **from the contract** — all 55 have one except the IEHG
   trio — or from the manual's own Request Example. **Never hand-write a
   payload.**
3. Add the case to the right tier in `scripts/live_crud_check.py` with
   `confirmed=False`, then `--emit-cases`.
4. **Before running live**, `python scripts/check_fixture_contract.py`. If your
   new case appears there, the payload disagrees with the contract and the live
   run will tell you nothing you could not have learned offline.
5. `python scripts/live_crud_check.py --endpoints ... --product gen` and the
   same for `civil`, in batches of at most 8, from a document the author has
   confirmed is empty.
6. Classify honestly. Passed → `confirmed=True`, `level: "write"` in
   `docs/coverage.json`, rerun `gen_roadmap.py`. Failed → leave it unconfirmed
   and record the verbatim error. **Never flip `confirmed` to silence a
   failure**, and never report an unconfirmed failure as an SDK defect: across
   every run so far they resolved to a fixture, a wrong documented value, or a
   product bug.
7. Record the npm side on the same selection in
   `docs/npm_live_evidence_scratch.md`. That is a by-product of this task, not
   a separate errand.

The three `IEHG-{GL,PSS,TRUSS}-M1` have **no permitted source at all** — no
manual schema and `/info` 404s. Do not invent a fixture for them.

---

## Task B — the 17 that have a case and have never passed

**Live.** All 17 were re-run on build 09/02/2026 on 2026-09-05 and **all 17
still fail**; the table of what each answers is in the live notes. Start where
the offline evidence already points.

`python scripts/check_fixture_contract.py` names **54 concrete leads across 8
endpoints**, and they are the cheapest thing in this document:

| endpoint | what the checker says |
| --- | --- |
| `/db/GRDP` | omits 14 `required` fields, on both products |
| `/db/NLNK`, `/db/NLNK-M1` | omit 4 and 6 `required` fields |
| `/db/TDMF` | omits `CTYPE`, `RELAXATION` |
| `/db/MVCT` | omits `DIST` |
| `/db/FBLA` | sends `LOAD_ANGLE`, recorded nowhere |
| `/db/ACTL` | sends `CLATS` on Gen, tagged Civil-only |

Fill a missing `required` field from the **contract's own** description, enum or
documented default, or from the manual's Request Example. If neither states a
value, **stop and report that** — inventing one is hand-writing a payload.

**Two of the 17 are already settled and are not yours:**

- **`/db/ACTL` is product behaviour on both sides.** Three payloads derived from
  committed sources, including one carrying only its two `required` fields, all
  answer `Wrong Field` on Gen; Civil accepts every one and then refuses to
  persist a changed `TOL`. Do not spend a session on it.
- **`/db/FBLA`'s `LOAD_ANGLE` is a real fixture defect and not the cause.**
  Sending the contract's seven keys without it answers the same `Unknown Error`
  on both products.

`/db/STCT` cannot run from the npm harness at all: it needs `stage11_seed`,
which reads state back and cannot be replayed from an emitted POST. Python runs
it fine. By design, not a gap.

---

## Task C — re-derive `safeToOmit` from evidence already collected

**Offline. Start here when no product session is available.**

`extract_contracts.py`'s `live_omission_evidence()` reads
`scripts/live_crud_check.py`'s confirmed cases statically and answers
`safeToOmit: true` where a confirmed payload actually omitted a documented
field. It runs at **draft** time and nothing revisits it — its own docstring
still says "116 cases marked `confirmed=True`", and there are now **144**.
`extract_contracts.py --check` compares field *sets* against the manual and
never looks at `safeToOmit`, so CI has been green over the whole gap.

Across the 125 endpoints that have live omission evidence, 113 fields already
carry `safeToOmit: true` and **57 more, across 18 endpoints, are still
`unverified` while a confirmed payload omitted them**:

| endpoint | fields | endpoint | fields |
| --- | ---: | --- | ---: |
| `/db/STCT-M1` | 14 | `/db/SDST` | 3 |
| `/db/HSFC` | 9 | `/db/MVHL` | 2 |
| `/db/PJCF` | 5 | `/db/POSL` | 2 |
| `/db/ELNK` | 4 | `/db/SDIS` | 2 |
| `/db/GSTP` | 4 | `/db/TDMT` | 2 |
| `/db/MVLD` | 3 | `/db/LLAN` | 1 |

The repository has **119 proven-safe fields out of 4,956**. This is a 48% move
in its only proven-safety number, from observations already paid for.

**It is not a bulk edit. Two traps make it a task you must stop on.**

- **The `/db/LLAN` failure mode.** In 2.7.7 that contract published a flat
  record while the payload was nested, so comparing top-level keys against a
  flat field list manufactured **ten** `safeToOmit: true` claims nobody had
  earned, and the proven-safe count went *down* when they were removed. A field
  counts as omitted only if contract and payload are keyed at the same level.
  `/db/STCT-M1`'s 14 are exactly the shape to be suspicious of.
- **A `read_only` or `create_only` field was never going to be sent.** Its
  absence from a create payload is evidence about nothing. `/db/PJCF`'s
  `CREATED`/`MODIFIED`/`FILE_SIZE` look like that.

So: **report all 57 with your judgement of which is which, per endpoint, and
apply only those where the levels genuinely match.** Where unsure, list it and
leave it `unverified` — that value is an honest gap and costs nothing, while a
wrong `true` is the `/db/NMAS` shape: the field the manual called Optional and
the server dies on.

`validate_contracts.py` and `check_fixture_contract.py` must both stay green,
and the second one's baseline will move as you go — update it in the same
commit, never at the end.

---

## Task D — the 21 wire names an accepted round trip sent that no contract records

**Offline to find; closing one needs a permitted source. Report, do not merge.**

`check_fixture_contract.py`'s second list holds 27 disagreements on `confirmed`
cases. 21 are this kind: the product accepted a payload carrying a name the
contract has nowhere.

| endpoint | names | products |
| --- | --- | --- |
| `/db/EIGV` | `FRMIN`, `FRMAX`, `iFREQ`, `bMINMAX`, `bSTRUM` | both |
| `/db/NLCT` | `MAX_ITERATIONS`, `NEWTON_ITEMS`, `NUMBER_STEPS` | gen |
| `/db/EIGV-M1` | `FREQ_NO`, `FREQ_RANGE` | civil |
| `/db/PNLD` | `AREALOAD` | both |
| `/db/THIS` | `DALL` | both |
| `/db/NBOF` | `KEY_NODE_ITEMS` | both |

For each, report what the manual's section and `schema/info-baseline.json` state
about that name. Both are permitted sources, and a name `/info` declares plus a
round trip that sent it is about as settled as this repository gets. **Do not
add the field to a contract** — write down what the two sources say and hand it
back. `/db/THIS`'s `DALL` is already described in `CLAUDE.md` as a live fact,
which is a hint about how the rest will read.

The other 6 of the 27 are `required` fields a confirmed call omitted
(`/db/HSFC`, `/db/SDIS`) and belong to Task C.

---

## Task E — merge the unmerged extraction tables, easiest first

**Offline. The measurement is done; the merging is not, and most of it is
Claude's.**

`docs/unmerged_tables_against_info.md` splits the 93 tables (602 field names)
that 19 contracts declare missing:

| what the measurement found | tables |
| --- | ---: |
| whole table declared, **one `/info` object holds it** | 53 |
| whole table declared, several objects | 3 |
| whole table declared, no common parent | 25 |
| partly declared | 1 |
| outside `/info`'s reach (`/view`, `/ope`) | 11 |

**Your part is the 53.** For each, `/info` has a single object holding every
name in the table, so the shape is not in question — the work is transcribing
the manual's rows into the contract at that path, then rerunning
`validate_contracts.py`, `info_baseline.py --against-contracts --check` and
`npm run generate`. Batches of at most 3 tables, one commit each, and stop at
the first table whose manual row says something the `/info` object does not.

The 25 scattered ones are **not** yours. `/info` declares every name but under
no common parent, so what the table means is a judgement. Each report row names
the object covering the most of it — `VEH_PL` covers 13 of 14, `VEH_CN` 28 of
30 — and that near-miss is where a decision has to be made rather than a
transcription.

---

## What the last five tasks settled

- **The `/info` standing check** and the **product-divergence guard** are both
  in CI as per-endpoint ceilings, and both were verified to fail on real input
  rather than only in unit tests.
- **Two `TABLE_TYPE` probes overturned a shipped value.** Both products refuse
  `REACTIONSURFACESPRING` and accept `REACTIONLSURFACESPRING`; both SDKs had
  shipped the refused string for the life of the constant. The general finding
  is now a rule: **a wire value is not a majority opinion**, and a
  `describes: table_type` defect may be marked resolved only on a live check.
- **The two harnesses now begin each case in the same state.** Sharing the base
  model closed only the common prefix; the rest was per-tier seeds. Fixture
  version 5 exports the 34 of 37 the npm harness can replay and names the other
  three with the reason. All fifteen affected endpoints pass on both harnesses
  on both products.
- **Both harnesses read a result the same way.** A failure before the endpoint
  under test is touched is `BLOCK` and exit 3, not `REGRESS` and exit 1.
- **The 602 waived names were measured.** 533 of the 534 that `/info` can speak
  to are declared, so "does a second source exist" was the wrong question and
  "does it agree on shape" is the right one.

## Two decisions that are open and are not yours

- **`/db/SPLC`'s cross-tier id collision.** extras4's Civil-only
  `lcom_seismic_splc` seed creates `/db/SPLC` id 1 and extras5's Civil case owns
  the same id, so the pair answers `Key Already Exist` for a shape both products
  accept alone. A different id does not fix it — this load-case family renumbers
  to the next free slot. It reports `BLOCK` today, honestly. Whether a case may
  own an id a seed can take is a fixture-design call.
- **`/db/ACTL`.** Gen refuses every payload including a `required`-only one;
  Civil accepts and will not persist `TOL`. A vendor-report item, not an SDK one.

---

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session.** For anything
  that writes, confirm both documents are empty with `GET /db/NODE` and
  `GET /db/ELEM`.
- **`.env` holds two keys, `MIDAS_MAPI_KEY_GEN` and `MIDAS_MAPI_KEY_CIVIL`.**
  There is no plain `MIDAS_MAPI_KEY`, and `grep '^MIDAS_MAPI_KEY'` matches both
  and concatenates them. A mismatched key still answers `connected` and still
  returns 0 records, so an emptiness check run with one key for both products
  proves nothing. Check each product with its own key.
- **`--save-dir` is required and never inferred.** `verify_connection()["user"]`
  is the MAPI account's email, not the NX host's Windows profile. `C:/temp`
  exists on both machines; the author created it and handles it himself.
- **`verify_connection()` cannot prove a session is alive.** It answers
  `connected` through the relay while a modal dialog holds the product. Use a
  real `GET /db/NODE`.
- **A GET can still pop a modal dialog** if the open document lives under
  `Program Files` or another path a standard account cannot write to.
- **Three harnesses call `/doc/NEW` and discard unsaved work**:
  `scripts/live_smoke.py`, `scripts/live_crud_check.py`, and
  `packages/typescript/scripts/live-crud.mjs`.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract; a fixture written from memory produces confident wrong findings.

## Repository rules that keep catching people

- **`contracts/` is the source of truth and neither SDK may be a source for
  it.** Permitted sources: the manual repo, `docs/live_verification_notes.md`,
  and live `/info`. A fixture is not one either.
- **`documentedOptional` is a claim about the docs; `safeToOmit` is a claim
  about the product.** Separate booleans, and they must stay that way.
- **`/info` is neither a superset nor a subset of what the server accepts.** It
  declares `/db/POSL`'s `CODE`, which Civil refuses live, and omits
  `/db/STBK`'s `LCNAME`, which a confirmed round trip sends. Where `/info` and a
  live round trip disagree, the round trip wins.
- **Never put `MAPI-xxxx` or MIDASIT's internal tracker in anything that
  ships.** 35 were removed from `src/midas_nx` docstrings on 2026-09-05; they
  had been reaching every PyPI install and seven places in the npm package.
  `docs/` is where that mapping lives.
- **A 200 does not mean success**, and error bodies also arrive under 201.
- **`DELETE {endpoint}` with an ID-keyed body empties the whole table.**
- Windows consoles are cp949: keep user-facing exception text ASCII.
