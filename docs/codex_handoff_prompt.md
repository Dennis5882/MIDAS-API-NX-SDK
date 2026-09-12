# Codex task prompt — mechanical work only

Updated 2026-09-06 at `acbbec4`. **2.8.0 is published** on both registries —
that release carried the `UNUMT`/`DIST` optionality. Nothing in either packaged
surface has changed since, so **no release is warranted right now**; when one
is, the number is the author's call.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Read "The one thing that is red, and is not yours" before anything else.**
Then: Task A if a product session is available, Task C if not.

---

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 1044 passed, 1 FAILED - EXPECTED
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK; 381 endpoints, 4963 fields,
                                          # 140 proven safe, 8 unsafe,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # has_diff: TRUE, 10 chapters - EXPECTED
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # 16 disagreements - EXPECTED
python scripts/info_baseline.py --against-contracts --check   # OK
python scripts/info_baseline.py --divergence --check          # OK
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check           # OK
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 41 fixture leads over 5
                                          # endpoints, 2 contract gaps over 1
python scripts/report_unmerged_tables.py --check       # report is current
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 75 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 191 write / 208
read.** `schema/live-cases.json` is **version 5**: 200 cases over 180
endpoints, 165 confirmed, 9 base-model steps, 62 named seeds, and 3 unsupported
seeds named with their reason. npm live evidence: **60 `/db` endpoints**.
Drafts: 3, the IEHG trio, refused for a reason that will not go away — that is
the finished state, not a backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## The one thing that is red, and is not yours

**Do not reflect the 2026-09-06 manual sync. The author has said so directly.**

One pytest case fails —
`test_shipped_contracts_still_match_the_manual_if_it_is_present` — and
`check_manual_drift.py` reports `has_diff: true` over ten chapters. Both are
detecting the same thing: the sibling manual repo at `E:\AI Study\MIDAS-API`
is two local commits ahead of its origin: `205d5f0 docs: 정기 점검 (2026-09-06)`
and follow-up `ff88259 docs(manual): ope/MEMB 요청 키 AELEM 재정정, SSEIS 원문
오염 로케일별 명시`. This repository and the manual repo's `origin/main`
still record `7920759`; the extraction check now reports 16 disagreements
because the follow-up removed the two `/ope/MEMB` differences.
The manual working tree is currently clean, but those unpushed commits are
external drift all the same. Do not consume or edit them from this repository.

**Those commits are not ready to be reflected.** The author is still checking
them, and they have not been pushed to the manual repo's own
`origin/main`. `CLAUDE.md` records the pattern: a bulk `정기 점검` sync is
often followed within a day by self-audit `fix(manual):` commits correcting its
own transcription, and this repository has already been burned by treating one
as final.

So this red check is **a correct detection of a real state**, not a defect to
clear. Concretely, do not:

- edit any contract to match the new manual text,
- touch `vendored_at_commit`,
- re-anchor the twelve `extraction.unmergedTables` entries whose titles and line
  numbers the sync moved (`db-this.yaml` ×10, `db-this-m1.yaml`, `db-splc.yaml`),
- add the four fields the sync documents (`db-matd.yaml`'s `bSERVCHECK`,
  `dSHORTTERM`, `dLONGTERM`; `db-tdna.yaml`'s `bPJ` under `SHAPE='CURVE'`),
- or `git -C "E:\AI Study\MIDAS-API" checkout`/`reset` anything to make the
  check pass. **The manual repo is not yours to change.**

If you find yourself with a green `extract_contracts --check`, you have done
something on this list — say so and revert it.

The work is real and will come back as its own task once the author has
verified the sync. It is written down here so nobody rediscovers it as a
surprise, not so that it gets done now.

**One consequence for the tasks below.** Every manual line number cited in a
contract — `extraction.unmergedTables` anchors especially — is against
`7920759`, not against what is in the manual working tree right now. When a
task tells you to read a manual section, read it at the vendored commit:

```bash
git -C "E:\AI Study\MIDAS-API" show 7920759:docs/manual/12_DB_Analysis_Control.md
```

Reading the working tree instead will show you rows the contracts were never
written against, and you will "find" disagreements that are just this drift.

---

## Task A — the 33 `/db` endpoints with no live case at all

**Live. Destructive: `/doc/NEW`.** The largest single block of remaining work,
and the only one that moves `ROADMAP.md`'s write count.

55 `/db` endpoints are still short of write level. 22 have a case that has
never passed (Task B). The other **33 have no case at all**:

| chapter | count | endpoints |
| --- | ---: | --- |
| 04 Properties | 13 | `EPMT`, `EPMT-M1`, `FIBR`, `FIMP`, `IEHC`, `IEHG`, `IEHG-BEAM-M1`, `IEHG-GL-M1`, `IEHG-PSS-M1`, `IEHG-TRUSS-M1`, `IMFM`, `IMFM-M1`, `MATD` |
| 07 Temperature/Prestress | 7 | `EXLD`, `PRST`, `PTNS`, `TDCS`, `TDNA`, `TDNT`, `TDPL` |
| 14 Pushover | 6 | `IEPI`, `PHGE`, `POGD`, `POGD-M1`, `POLC`, `POLC-M1` |
| 08 Moving Loads | 1 | `MVLDbs` |
| 24 Design | 4 | `RCHK`, `REBB`, `REBR`, `REBW` |
| 05 Boundary | 1 | `DRLS` |
| 10 Construction Stage | 1 | `CSCS` |

The three `/db/MVCT*` analysis-control siblings are now confirmed, and four of
the five `/db/MVLD*` endpoints have honest unconfirmed cases (Task B). The one
remaining endpoint with no case is `/db/MVLDbs`: its contract marks mutually
exclusive `LCDATA_*` objects required together, and representing its two-value
ALL_MODE condition needs a contract-shape decision. Do not waive the fixture
gate or run it until that decision is made.
**Which moving-load code a product offers decides what can be written at all** —
`POST /db/MVCD` answers "Unavailable moving load code" on Gen NX for `CHINA`,
`INDIA` and `KOREA`. Split the cases per product rather than writing one
payload that fails on one of them.

Per endpoint:

1. Read the manual chapter and any entry for it in
   `docs/live_verification_notes.md` **first**.
2. Build the fixture **from the contract**, or from the manual's own Request
   Example. **Never hand-write a payload.**
3. Add the case to the right tier in `scripts/live_crud_check.py` with
   `confirmed=False`, then `--emit-cases`.
4. **A seed that owns a fixed id is a shared resource whether or not it was
   written as one.** Two collisions were found two days apart — `/db/SPLC` and
   `/db/MVCD` — and both looked like endpoint failures. Before adding a seed
   that POSTs a fixed id, check whether another tier already owns it.
5. **A seed must be replayable from an emitted payload.** A seed that reads
   state back and branches cannot be exported, and silently takes every case
   that needs it away from the npm harness. Where a seed must tolerate an
   existing record, POST and fall back to PUT — do not read and branch. The
   emitter will catch you, but after the fact.
6. **Before running live**, `python scripts/check_fixture_contract.py`. If your
   new case appears there, the payload disagrees with the contract and the live
   run will tell you nothing you could not have learned offline.
7. `python scripts/live_crud_check.py --endpoints ... --product gen` and the
   same for `civil`, in batches of at most 8, from a document the author has
   confirmed is empty.
8. Classify honestly. Passed → `confirmed=True`, `level: "write"` in
   `docs/coverage.json`, rerun `gen_roadmap.py`. Failed → leave it unconfirmed
   and record the verbatim error. **Never flip `confirmed` to silence a
   failure**, and never report an unconfirmed failure as an SDK defect: across
   every run so far they resolved to a fixture, a wrong documented value, or a
   product bug.
9. Record the npm side on the same selection in
   `docs/npm_live_evidence_scratch.md`. That is a by-product of this task, not
   a separate errand.

The three `IEHG-{GL,PSS,TRUSS}-M1` have **no permitted source at all** — no
manual schema and `/info` 404s. Do not invent a fixture for them.

Chapter 04 and chapter 24 are both worth checking against
`docs/live_verification_notes.md` before writing anything: `/db/REBW` and
`/db/REBC` are the two confirmed cases where a manual section is wrong about
its own field *names*, and `REBB`/`REBW` are on this list.

---

## Task B — the 22 that have a case and have never passed

**Live.** The original 18 were re-run on build 09/02/2026 on 2026-09-05 and
still fail; the table of what each answers is in the live notes. Four manual
moving-load cases joined on 2026-09-06 and carry their exact current errors in
that file.

`/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
`/db/HPCE`, `/db/MADO`, `/db/MVCT`, `/db/MVLDch`, `/db/MVLDeu`,
`/db/MVLDid`, `/db/MVLDpl`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`, `/db/RPSC`,
`/db/SBDO`, `/db/SINF`, `/db/STCT`, `/db/TDMF`, `/db/WVLD`

Start where the offline evidence already points.
`python scripts/check_fixture_contract.py` names **41 concrete leads across 5
endpoints**. It now understands root `appliesWhen` and counts variant fields as
recorded names; the larger old count was partly checker blindness, not missing
contract fields:

| endpoint | what the checker says |
| --- | --- |
| `/db/GRDP` | omits 14 `required` fields, on both products |
| `/db/NLNK-M1` | the same four plus `BETA_ANGLE`, `REF_SYSTEM` |
| `/db/TDMF` | omits `CTYPE`, `RELAXATION` |
| `/db/MVCT` | omits `DIST` |
| `/db/ACTL` | sends `CLATS` on Gen, tagged Civil-only |

Fill a missing `required` field from the **contract's own** description, enum or
documented default, or from the manual's Request Example. If neither states a
value, **stop and report that** — inventing one is hand-writing a payload.

**Two of the 18 are already settled and are not yours:**

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

## Task C — completed: re-derived `safeToOmit` from recorded evidence

Completed 2026-09-12; the per-endpoint classification and rationale are in
`docs/safe_to_omit_survey.md`.

The measured starting count was no longer 60: `/db/NMAS`'s three crashing
omissions had already been fixed at `safeToOmit: false`, leaving 57 candidates
across 16 endpoints. Of those, 21 same-level, same-product, applicable-branch
omissions are now `true`; 36 remain honestly `unverified` because the case ran
a different conditional branch/product, omitted response metadata, or was
being compared with an `Assign` wrapper rather than a record member.

`live_omission_evidence()` now retains payload values and products, and draft
rendering refuses to infer omission safety unless every `appliesWhen` predicate
and product tag matches the case that actually ran. Parametrized tests cover
the matching branch, different branch, and different product forms. This does
not try to infer which `/info` fields are response-only; those still require
review rather than an automatic `true`.

---

## Task D — closed, and it was never a task

The 21 names were already declared in their own contracts' `variants`. The
checker read only the root `fields` array and called them unrecorded. It now
counts variant keys as recorded names, without guessing that a variant field is
required at the record root. The confirmed side is down to `/db/SDIS`'s `LRB`
and `NRB`, which belong to Task C.

**Do not treat this as a task that got done quickly.** It was a list of 21
defects that did not exist, written up from a checker's first run and handed
over as work. A checker that compares two artefacts is a third claim about the
shape, and its first output is a hypothesis: confirm a sample by hand against
the artefacts before reporting a count as a fact. The same run also mis-read
`/db/NLNK`'s four and `/db/HSFC`'s two, which already carried the `appliesWhen`
that says when they apply. 38 of 81 findings were the checker.

---

## Task E — merge the unmerged extraction tables, easiest first

**Offline. The measurement is done; the merging is not, and most of it is
Claude's.** Read each manual section at the vendored commit `7920759`, not in
the working tree — twelve of these entries anchor at titles and line numbers
the unreflected 2026-09-06 sync has already moved.

`docs/unmerged_tables_against_info.md` splits the 81 tables (531 field names)
that 19 contracts declare missing:

| what the measurement found | tables |
| --- | ---: |
| whole table declared, **one `/info` object holds it** | 41 |
| whole table declared, several objects | 3 |
| whole table declared, no common parent | 25 |
| partly declared | 1 |
| outside `/info`'s reach (`/view`, `/ope`) | 11 |

**Your remaining part is the 41.** The first three-table batch merged
`/db/THIS-M1`'s `BOUNDARY_NL_ANAL`, `/db/STCT`'s Linear & Independent Stage,
and `/db/ELEM`'s Beam/Truss/Plane Strain/Axisymmetric table. A second batch
removed three stale `/db/TDME` unmerged markers whose tables were already
represented by explicit variants; a third batch cleared the two remaining
stale Russian and Gilbert/KDS markers. The two Japan tables remain deliberately
unmerged because both products reject those iGen-only branches. A fourth batch
merged `/db/STCT`'s Cable-Pretension/Initial Force and Initial
Displacement/Camber tables at record root, preserving their four explicit
field-level conditions. A fifth batch merged STCT's Nonlinear Analysis and Time Dependent Effect
tables, retaining the headings' `iINC_NLA in [1, 2]` and `iNLA_TYPE=1`
conditions and splitting five reviewed compact rows. For each remaining
table, `/info` has a single object holding every
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

## What the previous rounds settled

- **The `/info` standing check** and the **product-divergence guard** are both
  in CI as per-endpoint ceilings, and both were verified to fail on real input
  rather than only in unit tests.
- **Two `TABLE_TYPE` probes overturned a shipped value.** Both products refuse
  `REACTIONSURFACESPRING` and accept `REACTIONLSURFACESPRING`. The general
  finding is now a rule: **a wire value is not a majority opinion**, and a
  `describes: table_type` defect may be marked resolved only on a live check.
- **The two harnesses now begin each case in the same state.** Sharing the base
  model closed only the common prefix; the rest was per-tier seeds. Fixture
  version 5 exports the 34 of 37 the npm harness can replay and names the other
  three with the reason.
- **Both harnesses read a result the same way.** A failure before the endpoint
  under test is touched is `BLOCK` and exit 3, not `REGRESS` and exit 1.
- **Fixtures are now checked against contracts.** Contracts had been compared
  against both SDKs, against `/info` and against the manual; nothing compared
  them against the fixtures, which decide what a live run actually sends.
- **The 602 waived names were measured.** 533 of the 534 that `/info` can speak
  to are declared, so "does a second source exist" was the wrong question and
  "does it agree on shape" is the right one.
- **Chapter 08's lane and moving-load family is live-verified on both
  products** — 13 endpoints, write coverage 173 → 185, npm evidence 47 → 55.
- **35 internal tracker ids were removed from `src/midas_nx` docstrings**; they
  had been reaching every PyPI install and seven places in the npm package.

## One small follow-up — completed

Completed after the first Task E batch. `/db/MVCTbs`, `/db/MVCTid` and
`/db/MVCTtr` now name the governing `iIGP` / `INFL_GEN_POINT` value in the
Python TypedDict comments. The annotations did not change; the contracts remain
the source for branch-conditional requiredness.

## Three decisions that are open and are not yours

- **Whether the 2026-09-06 manual sync is correct.** The author is checking it
  and has said outright that it still has errors. Until that finishes, nothing
  in this repository moves toward it — see the red-and-not-yours section.
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
- **`POST /doc/NEW` needs `{"Argument": {}}`.** With no request body it is
  HTTP 500 (`Cannot read properties of null (reading 'Argument')`) and the
  document is **not** reset. Assert the reset - GET `/db/NODE`, `/db/ELEM`
  and whatever table the run touches, expecting `{"message": ""}` - rather
  than assuming it. A probe run on 2026-09-06 had to be thrown away and
  repeated because it ignored that 500 and every later probe ran on an
  accumulated model.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract; a fixture written from memory produces confident wrong findings.
- **npm argument passing differs by shell.** Bash takes one `--`
  (`npm run live:crud -- --product gen`), PowerShell takes two
  (`npm run live:crud -- -- --product gen`).

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
  ships** — and that includes a release note. 35 were removed from
  `src/midas_nx` docstrings on 2026-09-05, and one survived into
  `docs/release_notes_v2.7.9.md` and had to be scrubbed before the release went
  out. `docs/` working files are where that mapping lives.
- **A 200 does not mean success**, and error bodies also arrive under 201.
- **`DELETE {endpoint}` with an ID-keyed body empties the whole table.**
- **Never commit a GET response body** — it is the author's model contents.
- Windows consoles are cp949: keep user-facing exception text ASCII.
