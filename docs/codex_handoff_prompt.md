# Codex task prompt — mechanical work only

Updated 2026-09-04. **2.7.7 is published** on both registries; the next number
is the author's call, so do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

**Task 1 is offline and you can start it right now.** Tasks 2–4 need a live
product session; ask the author before any of them.

## Your last two tasks are both finished

Neither is in this file any more. Both landed while you were away, so read them
as *done* rather than as work waiting for you:

- **The Hyper-S `/info` capture** is `schema/hyper-s-info.json`, and four
  contracts were written from it — the first to carry `provenance:
  info_schema`. The 404 split held exactly as predicted: `/db/IEHG-GL-M1`,
  `/db/IEHG-PSS-M1` and `/db/IEHG-TRUSS-M1` still answer a plain GET and still
  404 on `/info`, which leaves them **no permitted source at all**. They are the
  only three endpoints in the repo that cannot be contracted as things stand.
- **The dropped-row report** is `scripts/report_dropped_manual_rows.py`, wired
  into CI as `--check` against a module-level `EXPECTED_COUNTS`. That file is
  the pattern Task 1 asks you to copy.

## What moved since 2.7.5

Four releases and roughly forty commits. The parts that change how you work:

- **The contract validator gained a fifth check that compares field names.**
  The four before it compare routes, verbs, `products` and executable rules and
  never a field name, which is how `/db/ELNK` published four fields beside a
  twelve-key TypedDict with every gate green. `check_field_parity` fails on any
  wire name an SDK ships that no contract records. If a change of yours makes
  it fail, the contract is behind — **and fixing that is Claude's**, because it
  takes a permitted source.
- **`schema/info-baseline.json` is committed** — every `GET /info{endpoint}`
  both products answer, captured read-only 2026-09-03.
  `scripts/info_baseline.py` diffs a fresh capture against it and sweeps it
  against every contract offline. Task 1 is about that sweep.
- **Contracts 342 → 381, drafts 42 → 3**, and the three are the IEHG trio
  above, refused for a reason that will not go away. **There is no draft
  backlog left.** The line that used to say "the 31 remaining uncontracted npm
  resources are not yours" now covers three. Sixteen ledger rows have no
  endpoint contract: those three, three `/post/TABLE` rows that fold into
  `contracts/tables/` instead, and ten `/post/*` routes that are genuinely
  uncontracted.
- **`extraction.unmergedTables` entries carry `fieldNames`.** A contract that
  declares part of its field list missing now says *which* names that table
  holds, so the field-parity waiver is per-name. If you add or regenerate a
  draft, these come out of the extractor; do not hand-edit them.
- **A Key cell can name several properties at once** (`"bSD" / "iSDOPT" /
  "SDCONST"`, `SFI(STR)`, `"_3_LANE_FACTOR_1" ~ "_3_LANE_FACTOR_4"`). The table
  parser returns the whole cell as one key. `_unpack_key_cell` transcribes the
  three forms that occur and applies **only to `fieldNames`** — merged rows
  still go through `_REVIEWED_SHARED_COMPACT_KEYS`, which demands a named
  review per row. Registered as MD-48. Do not widen it.
- **`/db/NMAS`'s crash does not reproduce** on build 09/02/2026 on either
  product. The workaround stays. Nothing on the record says it was fixed
  deliberately, so keep sending `rmX`/`rmY`/`rmZ`.

## Measured starting state

Run these first and confirm you see the same numbers. **If any differ, say so
before starting** — it means something moved under you.

```bash
python -m pytest -q                       # 996 passed
ruff check src tests scripts && mypy      # clean; 41 source files
python scripts/validate_contracts.py      # OK; 381 endpoints, 1442 operations,
                                          # 4916 fields, 87 result tables,
                                          # 2 unresolved manual contradictions
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # OK - no drift, 365 checked
python scripts/report_dropped_manual_rows.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --check    # blank key 71, short row 20
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # 304 resources (301 by contract, 3 by a
                                          # Python class), 764 payload types (282
                                          # from contracts); no drift; 60 tests
```

`validate_contracts.py`'s field-parity line should read: **294 contracts
compared, 17 waiving part of the comparison through `unmergedTables`, 6 naming
a type Python does not define, 0 ambiguous.**

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 172 write / 227
read** — unchanged since 2026-09-01, because that half is yours and you have
not run since. `schema/live-cases.json` holds **167 cases, 143 confirmed**,
covering 158 distinct endpoints.

Drafts — clear and re-emit before judging anything about them.
`contracts/drafts/` is git-ignored build output and a stale copy has misled a
run before:

```bash
rm -rf contracts/drafts
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all   # 3 drafts
python scripts/promote_contract.py --all --dry-run       # 0 promoted, 3 refused
```

All three refuse with "no payload fields could be parsed" and all three are the
IEHG trio. **That is the finished state, not a backlog.**

> If a number here disagrees with a command's output, **the command wins** —
> say so in your report. One number in `PLAN.md` was wrong for a day this week
> because it was counted by grepping a script's source instead of asking the
> tool that owns it: `live_crud_check.py` has 145 `confirmed=True` occurrences
> in its text and 143 confirmed *cases*. The fixture is the answer, not the
> grep.

---

## Task 1 — make the `/info` sweep a standing check

**Offline. Start here.** This is the closest analogue to the dropped-row report
you already built, and it is deliberately the same shape.

### Why this task exists

`scripts/info_baseline.py --against-contracts` compares the server's own schema
against every contract, in both directions, and it has already found real
defects — MD-34 (a contract written from the manual, promoted, reviewed through
its generated npm diff, and still a shape the server refuses), MD-37 and MD-38.
**Nothing runs it automatically.** It is a thing someone remembers to do, which
means it is a thing that will stop happening.

The dropped-row report had exactly this problem and you fixed it the right way:
a module-level `EXPECTED_COUNTS`, a `--check` flag that fails when the counts
move, and a CI step. Do the same here.

### What to build

Add `--check` to `scripts/info_baseline.py`, backed by a committed expectation
of the current sweep, and wire it into `.github/workflows/ci.yml` beside the
existing "Check promoted contracts against the official manual" step.

Key it **per endpoint**, not by a single total. A total would let one contract
lose a property while another gains one and report nothing, and the whole value
of this sweep is in the small numbers — a count of one or two is what a missing
table row looks like, while `/db/SECT`'s 995 is the section-property tree and
means nothing.

The current sweep, which is what your expectation should record:

```text
contracts compared: 205
skipped, field list admittedly incomplete (unmergedTables): 17
properties waived as infoOnly: 1
endpoints with an unrecorded /info property: 11
unrecorded properties in total: 1392
endpoints publishing a name /info never declares: 4
```

| endpoint | unrecorded `/info` properties |
| --- | --- |
| `/db/SECT` | 995 |
| `/db/MATD` | 172 |
| `/db/NLLP` | 66 |
| `/db/TDMT` | 60 |
| `/db/SWIND` | 40 |
| `/db/SSEIS` | 34 |
| `/db/MVCTch` | 9 |
| `/db/LLANop` | 8 |
| `/db/LLAN` | 3 |
| `/db/LLANch` | 3 |
| `/db/LLANid` | 2 |

| endpoint | publishes a name `/info` declares nowhere |
| --- | --- |
| `/db/POGD-M1` | `SYMMETRIC`, `WALL` |
| `/db/LLANop` | `ECCEN_VERT_LOAD` |
| `/db/SMLC` | `KEY` |
| `/db/STBK` | `LCNAME` |

**A count going *down* must pass, not fail.** Closing one of these is the point;
the check exists to stop a count going *up* in silence. Record that reasoning in
the file the way `EXPECTED_COUNTS` records its own.

**Do not close any of these counts yourself.** Every one needs a manual section
read or a live finding interpreted, and both directions have traps that are
already written down:

- The second table reads **weakly**. `/db/STBK`'s `LCNAME` is in neither
  product's `/info` schema and `scripts/live_crud_check.py` sends it in a
  confirmed round trip that passes on both products. Absence from `/info`
  supports a note, never a deletion.
- `/info` is **neither a superset nor a subset** of what the server accepts. It
  declares `/db/POSL`'s `CODE` on Civil NX, which refuses it live even as an
  empty string. Where `/info` and a live round trip disagree, the round trip
  wins.

### Done when

`python scripts/info_baseline.py --against-contracts --check` exits 0 on this
tree, exits non-zero with a readable diff if you add a property to the baseline
by hand to test it, and CI runs it. Report the shape you chose for the
expectation file; where it lives structurally is worth a sentence, not a
decision you need to ask about.

---

## Task 2 — settle two `TABLE_TYPE` strings the manual contradicts itself on

**Live. POST-shaped read: no `/doc/NEW`, no model mutation, nothing deleted.**
Needs the author's go-ahead, but not an empty document.

`validate_contracts.py` reports "2 unresolved manual contradiction(s)" and has
for weeks. Both are one string each, both are one call each, and both are
currently guesses this repo is shipping:

| contract | the manual says | what we ship | on what basis |
| --- | --- | --- | --- |
| `contracts/tables/post-beam-force-static-prestress.yaml` | JSON Schema enum `BEAMFORCESIP`; request example and Specifications table `BEAMFORCESTP` | `BEAMFORCESTP` | two sources against one, and STP reads as an abbreviation of Static Prestress while SIP reads as nothing |
| `contracts/tables/post-reaction.yaml` | schema and table `REACTIONSURFACESPRING`; request example `REACTIONLSURFACESPRING` | `REACTIONSURFACESPRING` | two sources against one; treated as a typo in the example |

Neither has ever been asked of a running product. Ask both.

**What the answer looks like.** You are not looking for a table of results —
you are looking for the difference between *the server does not know this
string* and *the server knows it and has nothing to show you*. This repo
already relies on that distinction: a shape the server refuses answers
differently from a shape it accepts against a model that cannot satisfy it.
`/post/TABLE` on a model with no analysis results answers "Please perform
analysis" for a **recognised** type. An unrecognised one should not.

So, per pair, send both spellings against the same document and record both
bodies verbatim:

1. `BEAMFORCESTP` and `BEAMFORCESIP`
2. `REACTIONSURFACESPRING` and `REACTIONLSURFACESPRING`

Use `midas_nx.post`'s generic `get_table()` — do not hand-assemble the request.
Run on **both** products; `/post/TABLE`'s behaviour has differed by product
before.

**Record, do not decide.** Append a passage to
`docs/live_verification_notes.md` in the existing style — date, product, build,
the exact strings sent, the exact bodies back. Then say in your report which
way each pair points. **Do not edit the contracts**, do not flip `resolved` to
`true`, and do not touch `docs/manual_defects_register.md` beyond appending a
row with evidence if you find something new. Turning a measurement into a
contract change is Claude's half.

**Stop and report if** both spellings answer identically. That would mean
`/post/TABLE` does not validate `TABLE_TYPE` the way this repo assumes, which
is a bigger finding than either typo and changes how the other 139 values
should be read.

---

## Task 3 — `/db` write coverage (the long-running background task)

Standing work, unchanged and still yours.

**73 `/db` endpoints are still read-level**, exactly as at 2.7.5. They split:

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

**Five of the 18 changed shape since you last looked, and a fixture built
before 2.7.7 now has the wrong shape in it.** Build these from the contract,
not from memory:

| endpoint | what changed |
| --- | --- |
| `/db/RPSC` | longitudinal reinforcement is `MBARS: [{MBAR_ITEMS: [...]}]`, not a root `MBAR_ITEMS`. `SBAR_ITEMS` stays at the root — the pair really is asymmetric (MD-40) |
| `/db/SBDO` | `AXIS_VECTOR` is an array of numbers, not a number |
| `/db/STCT` | its contract's `unmergedTables` now itemises 62 names; the record is wider than the old fixture assumed |
| `/db/STRPSSM` | points are `{Y, Z}`, not `{PY, PZ}` — the manual took `/info`'s *description* for the key |
| `/db/EPSE` | the two products declare four fields between them that the other does not — `LOAD_TYPE`/`WIDTH` on **Civil**, `LOADING_AREA_GROUP`/`SEL_TYPE` on **Gen**. The Civil pair was in no contract at all; the Gen pair was in this one untagged, claimed for both. A fixture that sends all four will fail on both products (MD-46) |

The lane cluster in the 55 also moved: `/db/LLANch` and `/db/LLANid` take
`{COMMON, LANE_ITEMS}`, not a flat record. The server never accepted the flat
one, so any fixture written against the old contract would have failed for a
reason that was ours.

For each endpoint, in batches of at most 8:

1. Read the manual chapter and this endpoint's entry in
   `docs/live_verification_notes.md` **first**. Several already have a recorded
   reason for failing.
2. Build the fixture from the contract where one exists — all 18 have one now —
   or from the manual's own Request Example. **Never hand-write a payload.**
3. Run `python scripts/live_crud_check.py --tier <tier> --product gen` and the
   same for `civil`, from a document the author has confirmed is empty.
4. Classify honestly and record it:
   - **passed** → `confirmed=True`, `level: "write"`, `outcome`, the builds,
     and `live_verified.date` set to **the day the write actually happened**.
     All of them, on the entry that did the write.
   - **failed on a fixture problem** → fix the fixture, rerun.
   - **failed the same way with the documented payload** → leave it read-level
     and write down everything you tried, as you did for `/db/HPCE`.
5. `python scripts/live_crud_check.py --emit-cases` so
   `schema/live-cases.json` moves with the Python cases — CI fails if it
   drifts.
6. `python scripts/gen_roadmap.py`, then update `PLAN.md`'s §2 coverage figures
   and its "Last updated" line in the same commit.

**Do not flip `confirmed` to silence a failure**, and do not report an
unconfirmed failure as an SDK defect. Across every run so far, each one resolved
to a fixture, a wrong documented value, or a product bug.

Expected outcome to check against: each endpoint you finish moves write up by
one and read down by one, and `ROADMAP.md` regenerates with no other change.

---

## Task 4 — record what the npm package has actually proven

Unchanged from the last handoff, and still worth doing after Task 3 rather than
before: every endpoint Task 3 confirms adds to the pool this task draws from.

`packages/typescript/scripts/live-crud.mjs` already reads the same
`schema/live-cases.json` Python does and takes any endpoint through
`--endpoints`, so this needs no new harness. The gap is the *record*:
**npm-side live verification exists only as prose.**

`docs/npm_live_evidence_scratch.md` has the read-out — **23 `/db` endpoints and
4 result-table operations, 27 npm public-API operations**, each traced to the
passage that claims it. Extend it by running, in batches of at most 8:

```bash
npm run live:crud -- -- --product gen --endpoints /db/AAA,/db/BBB \
  --save-dir <a writable directory on the NX machine>
```

`scripts/live_crud_check.py` takes the same `--endpoints`, so a batch can be run
through both packages against one selection. Both refuse an endpoint with no
case in the selected tiers before touching the product.

Start with endpoints whose npm adapter does something beyond generated
metadata. Record each result in `docs/live_verification_notes.md` in the same
style as the existing npm passages.

**Where to record it structurally is Claude's call.** If running it makes it
obvious that a field in `docs/coverage.json` would help, say so in your report
and leave the schema alone.

---

## Live-session rules — read before any product call

- **Ask the author before the first product call of a session.** For anything
  that writes, confirm both documents are empty: `GET /db/NODE` and
  `GET /db/ELEM` answer `{"message": ""}`. Task 2 does not need an empty
  document, but still needs the go-ahead.
- **`--save-dir` is required and never inferred.** `verify_connection()["user"]`
  is the MAPI account's email, not the NX host's Windows profile. `C:/temp`
  exists on both machines; the author created it and handles it himself.
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
  `{"error": {...}}` = ran and rejected; an echoed record = success. Error
  bodies also arrive under 201.
- **`"Wrong Field"` from a `/db/*` write usually means a bad *value*, not a bad
  field name.** Vary the enum value before you vary the fields.
- **Never hand-write a live payload.** Use `schema/live-cases.json` or a
  contract. A hand-written fixture produces confident wrong findings.
- **Never commit a GET response body.** It is the author's model contents. "Returned
  N rows" in a report is fine; the rows are not.
- Leave both models empty, and say so in the note.

## Not yours, and why

- **The three uncontractable endpoints.** `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`
  and `/db/IEHG-TRUSS-M1` have no manual table and 404 on `/info`. There is
  nothing to collect; the ground has been covered twice, in every casing tried.
  Do not go looking for a fourth source.
- **The ten `/post/*` routes with no endpoint contract** —
  `/post/PM`, `/post/STEELCODECHECK` and the eight `*DESIGNFORCES` routes.
  They are separate routes rather than `TABLE_TYPE` result tables, and
  contracting them is contract work.
- **Closing any of the `/info` counts in Task 1.** Measure them, fence them,
  leave them.
- **The 20 short manual rows** that drop because they omit the leading No. cell
  — 11 nested `/db/THIS-M1` field rows, 9 variant divider rows across chapters
  14, 15 and 17. Aligning a short row to its header is a judgment about the
  table's shape. The escaped-pipe cause was mechanical; this one is not, and
  you cannot tell which a *new* cause is without reading the section, so a new
  cause is a report.
- **Promoting drafts and writing `resolution` text.** If a draft looks
  promotable, report it instead.
- **Editing `contracts/endpoints/*.yaml` by hand** — any contract's `fields`,
  `variants`, `enum`, `surface` or `extraction`.
- **`docs/manual_defects_register.md` beyond appending a row with evidence.** No
  manual-repo edit, no MIDASIT contact, no Jira issue.
- **Version bumps and releases.** The shared number is the author's call.
- Running any destructive harness against a session the author has not confirmed
  is empty.

## Settled — do not re-derive

- **All four contract-schema decisions are closed.** D1 `documentedDefaultNote`
  and D2 unstated requiredness shipped in 2.7.2; D3 array `when` with `in` and
  D4 `scalar`/`empty` arguments in 2.7.3. `contracts/README.md` states each with
  its reasoning.
- **A contract's `surface` block owns the published npm names.** 301 of the 304
  resources have one and the generator raises on a disagreement. It has raised on
  three releases and the disagreement was Python's every time — six `NAME`
  attributes were changed to match their contracts. Do not resolve such a raise
  by editing the contract.
- **`check_field_parity` runs one direction only.** A contract naming more than
  a TypedDict is the intended state; a TypedDict naming more than its contract
  is the defect. A TypedDict is the subject that check measures, **never a
  source** for fixing it.
- **A contract carrying `extraction.unmergedTables` is never an npm payload
  source.** That guard is what makes an incomplete contract safe, and a test
  checks it. If `npm run generate` produces a `types.ts` diff after a
  promotion, the guard is broken — report it, do not work around it. A label
  change in `resources.ts` is expected and fine.
- **A `requirement: required` carrying an `appliesWhen` is a branch's
  requirement, not the payload's.** 49 fields across nine contracts were
  generated unconditionally required, producing types no caller could satisfy.
  Fixed in 2.7.5; do not "restore" the requiredness.
- **A variant union is closed only where the contract proves it** — a declared
  `enum` the branches cover exactly, or both values of a boolean. Otherwise
  generation emits a trailing member carrying the remaining values. Do not
  "tidy" them away.
- **`products: [civil, gen]` says the route answers on both, never that the
  record is the same.** Ten of the 177 both-product endpoints declare different
  schemas — mostly the products' own feature sets, not a transcription slip.
  Tagged per field; MD-46 has the measurement.
- **`/info` is a `/db/*` facility.** All 147 `/DESIGN/*` resource-product pairs
  404 on introspection while the endpoints answer a plain GET, so a design-code
  contract has two permitted sources rather than three and can never carry
  `provenance: info_schema`. `check_field_parity` is now the only automated
  field check that family gets.
- **`docs/coverage.json` carries one row per result table, not per route**,
  while the contracts fold those same sections into one endpoint each. Both are
  right; do not "reconcile" them.
- **A ledger entry must not contradict its own prose.** `tests/test_live_cases.py`
  fails if a `method` describing a completed write round trip sits beside
  `level: read`, or one ending "left at level: read" sits beside
  `level: write`. Fix the entry, never the test.
- **`ROADMAP.md`'s version table is not a list of sessions.** It is every
  distinct `(date, Gen build, Civil build)` the ledger cites. An entry's `date`
  is when it reached its current level; an older date beside a newer build is
  normal. Only move `date` when the *level* moves.
- **A list the manual's own description outsizes is not an enum.** A count or
  range stated about the list (`19종 (D4 ~ D57)`, `2 ~ 20`) disqualifies it,
  and the field keeps its declared scalar type. Checked by a test over every
  contract.
- **A manual section states its request twice** — a Specifications table and
  often a JSON Schema — and where they disagree the table is *usually* the
  lossy one. MD-10 has the measurement. **Check the tooling before the
  source**: five of MD-10's original nine sections were not the manual at all,
  they were `extract_contracts.py` deleting rows. Over half of what looked like
  a documentation defect was this repo failing to count cells.
- **Both SDKs were swept read-only across all 549 declared resource-product
  pairs on 2026-09-01** and agreed on every one. Product gating is settled in
  both directions.
- **`/db/FBLA`'s shared table** — `= 1 or 2` alongside `= 1` and `= 2` — folds
  into both branches at generation time rather than forming a third union
  member. Decided and implemented.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Both SDKs fill them in,
  and the npm side is live-confirmed to do so on a real POST. The crash stopped
  reproducing on build 09/02/2026; that is not the same as being fixed.

## Known gaps that are Claude's, listed so you do not report them as findings

- **Six contracts name a payload type Python does not define**, so field parity
  skips them: `/db/DYNF` (`RailwayDynamicFactorByElementPayload`) and five
  `/db/LCOM-*` (`LoadCombinationGeneralPayload`, `...SeismicPayload`,
  `...SRCPayload`, `...SteelPayload`,
  `LoadCombinationCompositeSteelGirderPayload`). Python shares one TypedDict
  across each family while the contracts give npm a distinct name each. Not a
  defect — a hole in the check's join, and closing it is a design decision.
- **Nineteen contracts still waive part of their field list** through
  `extraction.unmergedTables`, 602 names in total, led by `/db/MVHL` (115),
  `/db/SPFC` (74) and `/view/RESULTGRAPHIC` (63). Each needs its manual section
  read.
- **The `/info` tail's small counts** — `/db/MVCTch` (9), `/db/LLANop` (8) and
  the LLAN family's `SPECIAL_LANE_ITEMS` — are the ones that look like missing
  table rows, and they are next in Claude's queue.

## Before every commit

Run the full set for each surface you touched — the block under "Measured
starting state" is the whole list. `git diff --check` too; a trailing space in a
YAML folded block has blocked a commit here before.
