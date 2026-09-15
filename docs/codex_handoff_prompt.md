# Codex task prompt — mechanical work only

Updated 2026-09-16, after **2.8.2 was published** to both registries. The tree
is clean and CI is fully green, the contract-to-manual check included.

2.8.2 shipped the manual sync's packaged changes, all additive: the new
`DESIGN/STEEL/DSTL` endpoint, three `/db/MATD` members, `bPJ` on the curved
tendon profile, and a three-state `OPT_CS` description. Full notes in
`docs/release_notes_v2.8.2.md`. npm went out before PyPI, which proved the new
`actions/setup-node` v7 on the Trusted Publishing path; that ordering was a
one-off and the usual order is fine again.

**Nothing in either packaged surface has changed since that release**, so no
release is warranted right now. Do not infer one from a contract edit either:
the author picks the number and must ask for the release explicitly.

**What the previous round actually did**, because the numbers below have all
moved: 21 `safeToOmit` claims grounded in recorded live calls with a guard in
the extractor so the derivation can no longer outrun its evidence (Task C, now
closed); 21 unmerged tables merged, 93 → 72 (Task E); seven case-less endpoints
now live-confirmed through both SDKs (Task A/B-1). The `/db/NMAS` trap in Task C was
spotted and refused, which is the outcome that task was written to test.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Read "The manual sync is reflected" before anything else** — it replaced a
prohibition that had stood since 2026-09-06, and several instructions further
down used to depend on it.

Then, in this order.

**With a product session:**

0. **Task H** — one GET on each product for `DESIGN/STEEL/DSTL`. Read-only, a
   minute, and it unblocks that endpoint's contract.
1. **Task F** — replay the 52 already-confirmed fixtures the npm harness has
   never run. Python has confirmed cases on 166 endpoints; npm evidence covers
   113. Most need only replay; fixture-only blockers must remain distinct from
   product regressions.
2. **Task G** — three confirmed cases that cannot fail, and so prove less than
   their `confirmed=True` claims.
3. **Task B-2** — the 22 that have failed. Only one offline lead is left.

**Without one, and only then:**

4. **Task A** — build fixtures for the 21 buildable endpoints with no case.
   Start with batch 17: `/db/PHGE`, `/db/POGD`, `/db/POGD-M1`.

An earlier version of this file said the offline queue was empty and told you
to report that rather than invent work. That was wrong about Task A: building a
fixture is offline, and 21 endpoints are waiting. What is still true is the
priority — **a session is the scarce thing.** Do not spend one writing fixtures
when 52 endpoints are waiting to be replayed through the other SDK.

Task C is closed and Task E's mechanical set is exhausted; both sections stay
because they say what re-opens them.

---

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 1067 passed, 0 failed
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK; 381 endpoints, 5064 fields,
                                          # 140 proven safe, 8 unsafe,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # has_diff: false
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift
python scripts/info_baseline.py --against-contracts --check   # OK
python scripts/info_baseline.py --divergence --check          # OK
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check           # OK
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 1 fixture lead over 1
                                          # endpoint, 3 contract gaps over 2
python scripts/report_unmerged_tables.py --check       # report is current
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 78 tests
```

Coverage as `ROADMAP.md` reports it: **400/400 implemented, 200 write / 199
read / 1 not live-verified** — `DESIGN/STEEL/DSTL`, see Task H.
`schema/live-cases.json` is **version 5**: 212 cases over 189 endpoints, 177
confirmed, 9 base-model steps, 64 named seeds. npm live evidence: **113 `/db`
endpoints**. `extraction.unmergedTables`: **72 tables, 482 names, 15
contracts**. Drafts: 3, the IEHG trio, refused for a reason that will not go
away — that is the finished state, not a backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## The manual sync is reflected — nothing is red

**Resolved 2026-09-16.** The sibling manual repo's five commits past the old
`vendored_at_commit` `7920759` — the 2026-09-06 bulk sync, its two `/ope/MEMB`
self-corrections, the locale check, and the 2026-09-15 sync at `a6947a7` — were
reviewed chapter by chapter and reflected, at the author's instruction.
`vendored_at_commit` is now `a6947a7`, `check_manual_drift.py` reports
`has_diff: false`, the extraction check reports no drift, and the
contract-to-manual pytest case that failed on purpose for ten days passes.

What reflecting it actually took, so the next sync is not a surprise:

| change in the manual | what it did here |
| --- | --- |
| `/db/MATD` gained `bSERVCHECK`, `dSHORTTERM`, `dLONGTERM` | added as `requirement: unstated`. The manual's JSON Schema and live `/info` on both products both declare them; the manual's table and example do not, so nothing about when they apply is recorded |
| `/db/TDNA`'s `CURVE` block gained `bPJ` | added to that variant; `ELEMENT` and `STRAIGHT` already had it |
| `DESIGN/STEEL/DSTL` documented as a new endpoint | added to both SDKs — see Task H. **Not `/db/DSTL`**, which shares the name |
| `OPT_CS` documented as three states | omitting it keeps the current view, `false` switches to the final stage. Both SDKs already omitted it by default; the contract no longer records `false` as its default |
| 108 manual line anchors across 59 contracts moved | re-anchored mechanically from a line-by-line mapping of the two manual versions, with zero anchors whose original line had itself changed |
| every other hunk | `⚠️` callout text only — typos MIDASIT has since fixed upstream, and locale notes. No contract or SDK change |

**The anchor lesson is the one to keep.** The extraction check flagged 11
moved `unmergedTables` anchors. The real number was **108**: `variants[].source.line`,
`missingColumns`, `structuralTables` and `extraction.source` all cite the
same lines and the check reads none of them. A manual sync that inserts one
paragraph near the top of a chapter moves every anchor below it, and fixing
only the ones a checker names leaves the rest silently pointing at the wrong
row. Map the whole file.

**Two things from the old prohibition still hold as habits:**

- a bulk `정기 점검` sync is often followed within a day by self-audit
  `fix(manual):` commits — re-run the drift checker, do not assume one sync is
  final;
- when a task says to read a manual section, read it at `vendored_at_commit`
  (now `a6947a7`), not whatever the working tree holds.

---

## Task H — one endpoint the manual added and nobody has called

**Live, read-only. Safe against an open model — the only task here that is.**

`DESIGN/STEEL/DSTL` (chapter 25 §0, the steel counterpart of `DESIGN/RC/DRC`)
was added to both SDKs on 2026-09-16 from the manual alone. It has **no
contract**: `promote_contract.py` refuses a draft with no live record in
`docs/coverage.json`, which is correct, and the npm resource is generated from
the Python class until then.

1. `GET /DESIGN/STEEL/DSTL` on Gen and on Civil — `live_readonly_sweep.py` or
   `npm run live:readonly`, whichever SDK you are checking. GET only.
2. Record it in `docs/coverage.json` with `level: "read"` and the build.
3. `python scripts/extract_contracts.py --emit /DESIGN/STEEL/DSTL`, then
   `python scripts/promote_contract.py design-steel-dstl`, then
   `validate_contracts.py` and `npm run generate`. The generated npm resource
   should move from the Python fallback to the contract with no name change.

`/info` is not served for `/DESIGN/*`, so do not try it; a design contract never
carries `provenance: info_schema`. A `PUT` round trip would earn `write`, but
it changes the active steel design code of whatever model is open — that one
needs an empty scratch document like every other write.

## Task F — 52 confirmed fixtures the npm harness has never replayed

**Live. Destructive: `/doc/NEW`. The largest remaining block of work, and the
one with the least judgement in it.**

Measured 2026-09-15:

| | |
| --- | ---: |
| endpoints with a `confirmed` Python case | 166 |
| endpoints recorded as replayed through npm | 113 |
| the gap, runnable as it stands | **52** |
| the gap, blocked by a seed npm cannot replay | 3 |

Nothing here needs building and nothing needs deciding. The fixture exists, it
already passed in Python, and `packages/typescript/scripts/live-crud.mjs`
replays the **same emitted fixture** through the built npm package.

**This is not bookkeeping.** It is the only way anything checks that the two
SDKs send the same request. Two harness defects in the last two rounds were
invisible to Python and surfaced the first time npm ran: `containsExpectedValue`
compared objects by reference, so a nested expected value could never match and
the assertion passed nothing; and `runCase` refused every endpoint without
DELETE. Neither was a typo — both were found by running, not by reading.

**A second thing falls out of it for free.** 171 of the 200 write-level
endpoints were last verified on a build older than the current 09/02/2026 —
46 on 08/14, 34 on 07/28, 27 on 08/26, and 29 on 09/02. Run the Python harness
on the same selection in the same session and the re-verification comes with
the replay. Do not spend a separate session on it.

The gap by tier, which is also how to batch it — the harness selects by
`--tier` or `--endpoints`:

| tier | n | endpoints |
| --- | ---: | --- |
| `extras14` | 3 | `BCGA-M1`, `DYFG`, `DYNF` |
| `static` | 8 | `ETMP`, `FBLD`, `LTOM`, `NBOF`, `NTMP`, `PRES`, `PSLT`, `SDSP` |
| `extras5` | 6 | `SPFC`, `THGA`, `THIS`, `THMS`, `THNL`, `THSL` |
| `extras8` | 5 | `BCCT`, `BUCK`, `HHCT`, `NLCT`, `PDEL` |
| `extras12` | 4 | `CAMB`, `GCMB`, `GSBG`, `ULFC` |
| `extras7` | 4 | `FMLD`, `PNLA`, `POSL`, `POSP` |
| `moving` | 4 | `LLAN`, `MVHC`, `MVHL`, `MVLD` |
| `stage` | 4 | `CMCS`, `CRPC`, `STAG`, `TMLD` |
| `extras10` | 3 | `HAHS`, `HSTG`, `STBK` |
| `extras4` | 3 | `LCOM-SRC`, `LCOM-STEEL`, `LCOM-STLCOMP` |
| `lanes_optimization` | 3 | `LLANop`, `SLAN`, `SLANop` |
| `core` | 2 | `BNGR`, `GRUP` |
| `props` · `moving_impact` · `lanes_bs` | 3 | `TMAT`, `IMPF`, `SLAN` |

**Three are blocked and are not defects.** `/db/PJCF` needs `pjcf_unlock`,
`/db/HECB` needs `stage11_seed` and `solid11_seed`, `/db/HSPT` needs
`stage11_seed` — seeds that read state back and therefore cannot be replayed
from an emitted payload. Python runs them fine. Leave them; do not "fix" a seed
by making it branch on a read.

How to run one batch:

1. Confirm both documents are empty with each product's own key, and ask the
   author before the first product call of the session.
2. `npm run live:crud -- -- --product gen --endpoints /db/A,/db/B,...` and the
   same for `civil`, at most 8 endpoints per selection.
3. Run `python scripts/live_crud_check.py --endpoints ...` on the same
   selection, in the same session. That is what re-verifies the older build.
4. Record the npm result in `docs/npm_live_evidence_scratch.md` — one row per
   endpoint with the date and the products it passed on — and update its Count
   line.
5. In `docs/coverage.json`, **append** to the entry's `method`; do not
   overwrite what is there. `Re-verified 2026-09-nn on build 09/02/2026 through
   both SDKs` is the shape. The existing date and history stay: an entry that
   loses its first measurement to a re-run has lost information.
6. A failure here is a **regression** — a case that passed before and does not
   now. Report it, do not re-classify it, and do not flip `confirmed`.

---

## Task G — three confirmed cases that cannot fail

**Offline to prepare, live to re-confirm. Small, and it is about the honesty
of evidence rather than the amount of it.**

A case proves a write happened by reading a value back and comparing it. These
three compare a value that was already there:

| case | what it asserts | why that proves nothing |
| --- | --- | --- |
| `/db/MATD` | `NAME == "C24"` after the PUT | the base model's material 1 is already named `C24`; the PUT would pass unchanged |
| `/db/IEHC` (gen and civil) | a value the create already set | create and update payloads are **byte-identical** |
| `/db/POLC-M1` | `INCRE_STEP == 20` | create and update payloads are **byte-identical** |

Make the update payload differ from the create in one field the endpoint
actually stores, and assert that field. `/db/MATD` already sends
`MAINREBAR_B_FY = 500000` against a seeded material whose rebar fields are
blank, so that one is a natural probe.

**Then set `confirmed=False` and re-run.** A changed payload is not the payload
that passed; leaving `confirmed=True` on it would be exactly the "flip the flag
to keep the light green" move this repository forbids. They are three
endpoints — fold them into whichever Task F batch you are running.

---


## Task A — the 26 `/db` endpoints with no live case at all

**Live. Destructive: `/doc/NEW`.** The largest single block of remaining work,
and the only one that moves `ROADMAP.md`'s write count.

46 `/db` endpoints are still short of write level. 22 have a case that has
never passed (Task B). The other **24 have no case at all**:

| chapter | count | endpoints |
| --- | ---: | --- |
| 04 Properties | 6 | `EPMT-M1`, `FIBR`, `IEHG`, `IEHG-BEAM-M1`, `IMFM`, `IMFM-M1` |
| 07 Temperature/Prestress | 5 | `PTNS`, `TDCS`, `TDNA`, `TDNT`, `TDPL` |
| 14 Pushover | 3 | `PHGE`, `POGD`, `POGD-M1` |
| 24 Design | 4 | `RCHK`, `REBB`, `REBR`, `REBW` |
| — no permitted source | 3 | `IEHG-GL-M1`, `IEHG-PSS-M1`, `IEHG-TRUSS-M1` |
| 08 Moving Loads | 1 | `MVLDbs` |
| 05 Boundary | 1 | `DRLS` |
| 10 Construction Stage | 1 | `CSCS` |

Seven endpoints came off this list and reached write level on 2026-09-12:
`/db/IEPI`, `/db/EXLD`, `/db/PRST`, `/db/POLC`, `/db/MATD`, `/db/IEHC`, and
Civil-only `/db/POLC-M1`. Python and npm both passed the emitted cases; the
details, including `/db/MATD`'s live-only material constraints, are in the live
notes.

`/db/EPMT` followed on 2026-09-14. The exact manual Von-Mises request completed
through both SDKs on Gen. Civil exposes the same `/info` schema but returns
`Wrong Field` for that request through both SDKs, so its separate case remains
unconfirmed.

`/db/FIMP` now also has a case copied from the manual's complete Kent & Park
example. Both SDKs on both products reject its printed `ECU=0.003`: the
product requires `Epsilon_cu > 0.8 / Z + Epsilon_co`. The chapter supplies no
compliant alternative, so the value was not invented and the case remains
unconfirmed.

`/db/TDNA`'s `CURVE` variant now declares `bPJ`, reflected from the manual on
2026-09-16 — every one of the manual's four CURVE examples sends it, so a
fixture built from them may too.

`/db/MVLDbs` still has no case: its contract marks mutually exclusive
`LCDATA_*` objects required together, and representing its two-value ALL_MODE
condition needs a contract-shape decision. Do not waive the fixture gate or run
it until that decision is made.
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

## Task B — the 22 that have a case and no passing run

**Live. B-1 is complete:** the five pending cases plus newly built `/db/IEHC`
and `/db/POLC-M1` passed Python and npm on 2026-09-12.

**B-2: 22 that have failed.** The original 18 were re-run on build 09/02/2026
on 2026-09-05 and still fail; the table of what each answers is in the live
notes. Four manual moving-load cases joined on 2026-09-06 and carry their exact
current errors in that file.

`/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
`/db/FIMP`, `/db/HPCE`, `/db/MADO`, `/db/MVLDch`, `/db/MVLDeu`,
`/db/MVLDid`, `/db/MVLDpl`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`, `/db/RPSC`,
`/db/SBDO`, `/db/SINF`, `/db/STCT`, `/db/TDMF`, `/db/WVLD`

**Two more unconfirmed cases sit on endpoints that already have write
evidence**, so they are not in the 22 and are easy to lose: `/db/EPMT`'s Civil
case, which answers `Wrong Field` for the request Gen accepts, and `/db/DSTL`'s.
Both are live work; neither changes a coverage count if it passes.

The offline evidence pass is complete. `python scripts/check_fixture_contract.py`
now names **1 concrete lead on 1 endpoint**, down from 41 across 5. It
understands root `appliesWhen` and counts variant fields as recorded names:

| endpoint | what the checker says |
| --- | --- |
| `/db/ACTL` | sends `CLATS` on Gen, tagged Civil-only |

GRDP now carries the complete Request Body and passes both SDKs on Gen and
Civil. MVCT, NLNK-M1 and TDMF now encode the manual's explicit branch gates,
so their unrelated branch members are no longer false required-field findings.
MVCT passes both SDKs on both products once the manual's AASHTO LRFD code is
selected; TDMF still fails live and NLNK-M1 is still blocked by the NLLP seed.

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

**What re-opens it, and this is the part to carry forward.** The derivation
runs at draft time and nothing revisits it — that is exactly how 60 fields
drifted out of date behind a green CI. Every Task B run that flips a case to
`confirmed=True` adds evidence this survey has not seen. So **re-run the survey
at the end of any session that confirms a case**, and say in your report how
many candidates it names; do not let the next round rediscover a stale number.
The 36 still-`unverified` rows in `docs/safe_to_omit_survey.md` each name the
branch or product that would settle them, so a run that exercises one is a
direct answer rather than a new investigation.

Rechecked after the seven-endpoint 2026-09-12 batch: none of those endpoints
appears in the survey's 36 retained candidate rows, so the measured result
remains 21 promoted and 36 unverified; no omission claim changed.

---

## Task D — closed, and it was never a task

The 21 names were already declared in their own contracts' `variants`. The
checker read only the root `fields` array and called them unrecorded. It now
counts variant keys as recorded names, without guessing that a variant field is
required at the record root. The confirmed side contains `/db/SDIS`'s `LRB`
and `NRB`, plus `/db/SPLC`'s newly declared `NDP`. They remain explicit
contract-gap leads rather than being converted into conditional omission
claims without a documented branch condition.

**Do not treat this as a task that got done quickly.** It was a list of 21
defects that did not exist, written up from a checker's first run and handed
over as work. A checker that compares two artefacts is a third claim about the
shape, and its first output is a hypothesis: confirm a sample by hand against
the artefacts before reporting a count as a fact. The same run also mis-read
`/db/NLNK`'s four and `/db/HSFC`'s two, which already carried the `appliesWhen`
that says when they apply. 38 of 81 findings were the checker.

---

## Task E — merge the unmerged extraction tables: your part is done

**Offline. Do not start here.** The mechanical set is exhausted, and the next
section says so with the evidence. Read it before deciding otherwise. Read any
manual section at the vendored commit `a6947a7`, which is also the working
tree now that the sync is reflected.

`docs/unmerged_tables_against_info.md` splits the 72 tables (482 field names)
that 15 contracts declare missing:

| what the measurement found | tables |
| --- | ---: |
| whole table declared, **one `/info` object holds it** | 32 |
| whole table declared, several objects | 3 |
| whole table declared, no common parent | 25 |
| partly declared | 1 |
| outside `/info`'s reach (`/view`, `/ope`) | 11 |

**Eleven batches merged 21 tables and 120 names, 93 → 72, and then an audit
found nothing mechanical left among the 32.** The batch history below is kept
because it names what each merge preserved — conditions, gates, nesting — and
that is the standard the next merge has to meet, whoever does it. The first
three-table batch merged
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
conditions and splitting five reviewed compact rows. A sixth batch merged
NSPR's LINEAR, COMP/TENS and MULTI tables into
`ITEMS`, including the additional `DIR=6` gate on `DV`. A seventh batch merged
NSPR's independent `FormType=1` surface-function
table into the same item shape, completing that contract and moving its npm
payload generation from the Python fallback to the contract. An eighth batch
merged both IMPF item tables using their three documented
`FACT_TYPE` values, with the additional `ELEMTYPE in [BEAM, PLATE]` condition
on `PARTS`; npm now generates IMPF from the contract too. The ninth batch
merged `/db/SPLC`'s GEN-only nondissipative-design
table at record root. Its `GEN NX only` suffix is a product qualifier, not a
payload branch; the three damping/accidental-eccentricity tables remain because
their complete wire conditions or nesting are not yet established. A tenth
batch merged `/db/NLCT-M1`'s `ADVANCED` table. The heading explicitly makes
the members optional and the `OPT_USE_DEFAULT` row explicitly overrides that
one member to Required. An eleventh batch merged its `LOAD_STEPS` table while
preserving the distinction between conditionally Required fields and fields
that merely apply under a selector. It also transcribed the two `REF_NODE`
children stated inline, completing NLCT-M1 and moving npm payload generation
from the Python fallback to the contract. For each
remaining table, `/info` has a single object holding every
name in the table, so the shape is not in question — the work is transcribing
the manual's rows into the contract at that path, then rerunning
`validate_contracts.py`, `info_baseline.py --against-contracts --check` and
`npm run generate`. Batches of at most 3 tables, one commit each, and stop at
the first table whose manual row says something the `/info` object does not.

An audit after the eleventh batch found **no further mechanical merge among
those 32**. Do not rescan them as if they were an unreviewed queue:

- `/db/MVHL` 2: the contract is hand-resolved, but the extractor cannot yet
  reproduce the documented nesting; its markers are intentional.
- `/db/SPFC` 2, `/db/THIS` 10, `/db/MVLD` 3 and `/db/SPLC` 1: the manual does
  not state a complete wire discriminator for the table.
- `/db/ELEM` 7: the headings state `STYPE` but not the complete `TYPE`/`STYPE`
  discriminator pair.
- `/db/EPMT` 2: the supplementary rows omit Value Type.
- `/db/SDIS` 2: two identically titled `NRB 객체` tables map to different
  parents, which needs a judgment rather than a title-based merge.
- `/db/CSCS` 1: the manual itself says the nine members' meanings are inferred
  and unconfirmed.
- `/db/TDME` 2: both products reject the remaining iGen-only Japan branches.

The report also has one partly-declared ELEM table, 25 scattered tables and 11
outside `/info`; those were never in the mechanical one-object set.

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
- **`safeToOmit` can no longer outrun its evidence.** The derivation used to
  compare key sets and nothing else, which is how `/db/LLAN` manufactured ten
  claims from a nesting mismatch. It now requires the confirmed case to have
  satisfied every `appliesWhen` predicate and to have run on a product the
  field applies to, with tests for the matching branch, a different branch and
  a different product.
- **A merged table keeps its conditions.** Across eleven batches the merges
  preserved heading-level gates (`iINC_NLA in [1, 2]`, `iNLA_TYPE=1`), field-
  level ones (`DIR=6` on `DV`, `ELEMTYPE in [BEAM, PLATE]` on `PARTS`), and
  `/info`-settled nesting — and `/db/NSPR`, `/db/IMPF` and `/db/NLCT-M1` moved
  their npm payload generation off the Python fallback as a consequence.

## One small follow-up — completed

Completed after the first Task E batch. `/db/MVCTbs`, `/db/MVCTid` and
`/db/MVCTtr` now name the governing `iIGP` / `INFL_GEN_POINT` value in the
Python TypedDict comments. The annotations did not change; the contracts remain
the source for branch-conditional requiredness.

## Four decisions that are open and are not yours

- **`/db/SPLC`'s `NDP` requiredness.** Merging the 비소산 요소 설계 table gave
  the contract a Gen-only `NDP` marked `required` with no condition, and the
  confirmed Gen case — which passed before the field existed — omits it, so
  `check_fixture_contract.py` now carries it as a live-confirmed contract gap.
  The manual numbers it `(1)` beneath the Optional `bNDP` switch, which reads
  as a branch but is never stated as a wire rule. Leaving it as a baseline
  entry was right. **Do not resolve it either way**: an `appliesWhen` nobody
  documented and a `safeToOmit: true` for a field that did not exist when the
  call ran are both claims the sources do not support. This is MD-16's shape —
  requiredness stated without the branch that governs it — and it is the
  author's call.
- **`/db/THIS-M1`'s 20 unrecorded `/info` properties.** Closing that contract's
  last unmerged table made the standing `/info` comparison visible for the
  first time, and 20 properties have no row in the vendored manual. The ceiling
  in `info_baseline.py` records the number without claiming they are request
  fields, which is the right holding position. Deciding what they are needs the
  weak-reading rule: `/info` declaring a property is not the server accepting
  only those. Do not raise that ceiling to absorb anything new.
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
- **An official article has a locale, and the locales differ.** Help-centre
  article 49514964272665 carries the same id and the same `updated_at` in `ko`
  and `en-us` and a **different request example in each** — that is MD-52, and
  it is how a documentation dispute ran for a round with both sides reading
  real text. When you quote the official source, name the locale you read; a
  citation without one is not checkable. `f868e41` in the manual repo adds a
  locale judgement to its own sync checker for the same reason.
- **A 200 does not mean success**, and error bodies also arrive under 201.
- **`DELETE {endpoint}` with an ID-keyed body empties the whole table.**
- **Never commit a GET response body** — it is the author's model contents.
- Windows consoles are cp949: keep user-facing exception text ASCII.
