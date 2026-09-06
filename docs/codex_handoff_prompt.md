# Codex task prompt — mechanical work only

Updated 2026-09-06 at `d05c831`. **2.7.9 is published** on both registries.
Nothing in either packaged surface has changed since, so **no release is
warranted right now** — and when one is, the number is the author's call.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Start at Task 0.** It is new, it is the only thing currently red, and it is
the reason the numbers below moved. After it: Task A if a product session is
available, Task C if not.

---

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 1023 passed, 1 FAILED (see Task 0)
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK; 381 endpoints, 4956 fields,
                                          # 119 proven safe, 8 unsafe,
                                          # 0 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # has_diff: TRUE, 9 chapters (Task 0)
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # 16 disagreements (Task 0)
python scripts/info_baseline.py --against-contracts --check   # OK
python scripts/info_baseline.py --divergence --check          # OK
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check           # OK
python scripts/live_crud_check.py --check-cases        # silent; exit 0
python scripts/check_fixture_contract.py --check       # 54 fixture leads over 8
                                          # endpoints, 27 contract gaps over 8
python scripts/report_unmerged_tables.py --check       # report is current
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift; 70 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 185 write / 214
read.** `schema/live-cases.json` is **version 5**: 188 cases over 171
endpoints, 158 confirmed, 9 base-model steps, 56 named seeds, and 3 unsupported
seeds named with their reason. npm live evidence: **55 `/db` endpoints**.
Drafts: 3, the IEHG trio, refused for a reason that will not go away — that is
the finished state, not a backlog.

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report.

---

## Task 0 — reflect the manual repo's 2026-09-06 sync

**Offline. Currently the only red check in the repository.** One pytest case
fails (`test_shipped_contracts_still_match_the_manual_if_it_is_present`) and it
fails for a good reason: the sibling manual repo gained
`205d5f0 docs: 정기 점검 (2026-09-06)` and this repository still records
`7920759` in `docs/coverage.json`'s `vendored_at_commit`.

Nine chapters changed: `02`, `04`, `06`, `07`, `09`, `11`, `17`, `19`, `25`.

**Read this before touching `vendored_at_commit`.** Two things make that field
the last edit of this task, not the first:

- `205d5f0` is **unpushed** — it exists only in the local manual repo, not on
  its `origin/main`. It is the author's in-flight work.
- `CLAUDE.md` records that a bulk `정기 점검` sync is often followed within a
  day by self-audit `fix(manual):` commits correcting its own transcription.
  That has happened before on this exact pattern.

So: **do the reflection, report it, and ask the author before bumping
`vendored_at_commit`.** Bumping it to an unpushed commit that then gets amended
is how this repository would end up claiming to reflect a manual that no longer
exists.

`extract_contracts.py --check` names 16 disagreements in three groups.

**Twelve are mechanical re-anchoring — these are yours.** The sync renumbered
and retitled headings, so `extraction.unmergedTables` entries no longer resolve
to a table that exists:

| contract | entries | what moved |
| --- | ---: | --- |
| `db-this.yaml` | 10 | section headings `6-3.` through `6-8.` and their sub-tables |
| `db-this-m1.yaml` | 1 | `비선형 경계요소 해석 (BOUNDARY_NL_ANAL)` |
| `db-splc.yaml` | 1 | `Mass & Stiffness Proportional 감쇠 추가 파라미터` |

Re-point each entry at the table's new title and line. **The `fieldNames` list
in each entry does not change** — if it would, that is not re-anchoring and you
should stop: it means the table's contents moved, not its heading.

One of them is worth reporting rather than silently fixing: `db-this.yaml`
names `6-6. Nonlinear + Direct Integration (Transient)` **twice**, at lines
1371 and 1381. Check whether the manual now has two headings with that number.
If it does, that is a manual defect (a duplicate section number), and it goes
in `docs/manual_defects_register.md` — not worked around in the contract.

**Four are new content.** The sync documents fields the contracts do not have:

| contract | fields |
| --- | --- |
| `db-matd.yaml` | `bSERVCHECK`, `dSHORTTERM`, `dLONGTERM` |
| `db-tdna.yaml` | `bPJ`, in variant `SHAPE='CURVE'` only |

Transcribe each from the manual's own row: type, `requirement`,
`documentedOptional`, description. **`safeToOmit` stays `unverified`** — the
manual saying "Optional" is `documentedOptional` and nothing else; nobody has
omitted these against a running product. If a row does not state the field's
type or requiredness outright, **stop and report that row** rather than
inferring it.

When the contracts are green again, re-run `npm run generate` and review the
generated diff. Finish with the drift checker reporting `has_diff: false` —
**after** the author has confirmed the manual commit is final.

---

## Task A — the 42 `/db` endpoints with no live case at all

**Live. Destructive: `/doc/NEW`.** The largest single block of remaining work,
and the only one that moves `ROADMAP.md`'s write count.

60 `/db` endpoints are still short of write level. 18 have a case that has
never passed (Task B). The other **42 have no case at all**:

| chapter | count | endpoints |
| --- | ---: | --- |
| 04 Properties | 13 | `EPMT`, `EPMT-M1`, `FIBR`, `FIMP`, `IEHC`, `IEHG`, `IEHG-BEAM-M1`, `IEHG-GL-M1`, `IEHG-PSS-M1`, `IEHG-TRUSS-M1`, `IMFM`, `IMFM-M1`, `MATD` |
| 07 Temperature/Prestress | 7 | `EXLD`, `PRST`, `PTNS`, `TDCS`, `TDNA`, `TDNT`, `TDPL` |
| 14 Pushover | 6 | `IEPI`, `PHGE`, `POGD`, `POGD-M1`, `POLC`, `POLC-M1` |
| 08 Moving Loads | 5 | `MVLDbs`, `MVLDch`, `MVLDeu`, `MVLDid`, `MVLDpl` |
| 24 Design | 4 | `RCHK`, `REBB`, `REBR`, `REBW` |
| 12 Analysis Control | 3 | `MVCTbs`, `MVCTid`, `MVCTtr` |
| 09 Dynamic Loads | 2 | `THGC-M1`, `THOO-M1` |
| 05 Boundary | 1 | `DRLS` |
| 10 Construction Stage | 1 | `CSCS` |

Chapter 08's lane family closed in 2.7.9 — thirteen endpoints, both products —
so **the five `/db/MVLD*` left here are what remains of that chapter**, and the
three `/db/MVCT*` in chapter 12 are their analysis-control siblings. That is
the most coherent group and the one with the freshest evidence next to it:
read `docs/live_verification_notes.md`'s 2026-09-05 entries before starting.
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

## Task B — the 18 that have a case and have never passed

**Live.** All were re-run on build 09/02/2026 on 2026-09-05 and all still fail;
the table of what each answers is in the live notes. `/db/SINF` joined this
list in 2.7.9 — it gained a case during the chapter 08 work that has not
passed.

`/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
`/db/HPCE`, `/db/MADO`, `/db/MVCT`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`,
`/db/RPSC`, `/db/SBDO`, `/db/SINF`, `/db/STCT`, `/db/TDMF`, `/db/WVLD`

Start where the offline evidence already points.
`python scripts/check_fixture_contract.py` names **54 concrete leads across 8
endpoints**, and they are the cheapest thing in this document:

| endpoint | what the checker says |
| --- | --- |
| `/db/GRDP` | omits 14 `required` fields, on both products |
| `/db/NLNK` | omits `ANGLE_VALUES`, `INPUT_METHOD`, `POINT_VALUES`, `VECTOR_VALUES` |
| `/db/NLNK-M1` | the same four plus `BETA_ANGLE`, `REF_SYSTEM` |
| `/db/TDMF` | omits `CTYPE`, `RELAXATION` |
| `/db/MVCT` | omits `DIST` |
| `/db/NLCT` | sends `MAX_ITERATIONS`, `NEWTON_ITEMS`, `NUMBER_STEPS` on civil, recorded nowhere |
| `/db/FBLA` | sends `LOAD_ANGLE`, recorded nowhere |
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

## Task C — re-derive `safeToOmit` from evidence already collected

**Offline. Start here when no product session is available.**

`extract_contracts.py`'s `live_omission_evidence()` reads
`scripts/live_crud_check.py`'s confirmed cases statically and answers
`safeToOmit: true` where a confirmed payload actually omitted a documented
field. It runs at **draft** time and nothing revisits it — its own docstring
still says "116 cases marked `confirmed=True`", and there are now **158**.
`extract_contracts.py --check` compares field *sets* against the manual and
never looks at `safeToOmit`, so CI has been green over the whole gap.

Across the 125 endpoints that have live omission evidence, 113 fields already
carry `safeToOmit: true` and **60 more, across 19 endpoints, are still
`unverified` while a confirmed payload omitted them**:

| endpoint | fields | endpoint | fields |
| --- | ---: | --- | ---: |
| `/db/STCT-M1` | 14 | `/db/SDIS` | 2 |
| `/db/HSFC` | 9 | `/db/TDMT` | 2 |
| `/db/PJCF` | 5 | `/db/LLAN` | 1 |
| `/db/ELNK` | 4 | `/db/PNLD` | 1 |
| `/db/GSTP` | 4 | `/db/STAG` | 1 |
| `/db/MVLD` | 3 | `/db/THGC` | 1 |
| **`/db/NMAS`** | **3** | `/DESIGN/…/LENG` | 1 |
| `/db/SDST` | 3 | `/DESIGN/…/LTSR` | 1 |
| `/db/MVHL` | 2 | `/DESIGN/…/MBTP` | 1 |
| `/db/POSL` | 2 | | |

**It is not a bulk edit. Four traps make it a task you must stop on, and the
first one is a live demonstration that the derivation is unsound on its own.**

- **`/db/NMAS`'s `rmX`, `rmY`, `rmZ` are in that list and omitting them kills
  the product.** That is the crash this repository spent 15+ reproductions
  root-causing. They appear as candidates only because `NodalMass.create()`
  fills them in before sending, so the *case* omits them and the *wire payload*
  does not. Marking these three `safeToOmit: true` would publish the exact
  opposite of the most expensive finding in the repository. **If your reasoning
  would have said `true` for these, your reasoning is wrong** — say so in your
  report and re-check the other 57 with that in mind.
- **The three `/DESIGN/*` `Assign` entries are the request wrapper**, not a
  field. Evidence about nothing.
- **The `/db/LLAN` failure mode.** In 2.7.7 that contract published a flat
  record while the payload was nested, so comparing top-level keys against a
  flat field list manufactured **ten** `safeToOmit: true` claims nobody had
  earned, and the proven-safe count went *down* when they were removed. A field
  counts as omitted only if contract and payload are keyed at the same level.
  `/db/STCT-M1`'s 14 are exactly the shape to be suspicious of.
- **A `read_only` or `create_only` field was never going to be sent.** Its
  absence from a create payload is evidence about nothing. `/db/PJCF`'s
  `CREATED`, `MODIFIED` and `FILE_SIZE` look like that.

So: **report all 60 with your judgement of which is which, per endpoint, and
apply only those where the levels genuinely match and no SDK rule fills the
field in behind the case's back.** Where unsure, list it and leave it
`unverified` — that value is an honest gap and costs nothing, while a wrong
`true` is the `/db/NMAS` shape exactly.

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

`/db/NLCT` appears in **both** halves of the checker's report — the same three
names are a fixture lead on civil (never passed) and a contract gap on gen
(confirmed). That is one finding, not two, and it says the contract is missing
the names rather than the fixture inventing them.

The other 6 of the 27 are `required` fields a confirmed call omitted
(`/db/HSFC`'s `ITEM`/`SCALE_FACTOR`, `/db/SDIS`'s `LRB`/`NRB`) and belong to
Task C.

---

## Task E — merge the unmerged extraction tables, easiest first

**Offline. The measurement is done; the merging is not, and most of it is
Claude's.** Note that Task 0 re-anchors twelve of these entries — **do Task 0
first**, or you will merge against titles that no longer exist.

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

## Three decisions that are open and are not yours

- **Whether the 2026-09-06 manual sync is final.** It is unpushed, and this
  repository has been burned by a `정기 점검` commit that got corrected the next
  day. See Task 0.
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
