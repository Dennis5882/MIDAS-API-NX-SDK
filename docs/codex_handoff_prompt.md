# Codex task prompt — mechanical work only

Updated 2026-09-01 at HEAD `368f9d2`. Version stays **2.7.3** on both
registries; do not bump it.

**The division, set by the author.** Judgment-heavy work — schema design,
deciding what a contradictory manual means, deciding what stays unmerged — is
Claude's. Bounded, verifiable, repeatable work is yours. Every task below has a
measured starting number you can check your run against. A task that turns out
to need a judgment call is one to **stop and report**, not to decide.

## What your last two batches showed

`801abe0` is the model to repeat. Six live results, and the best ones are the
ones you *refused* to claim:

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
- `/db/STCT` stayed unconfirmed, but you disproved the standing hypothesis: the
  documented Linear + Independent branch loses `iITER`/`TOL` too, so it was
  never a branch-selection mistake.

`92149a4` is the one to learn from. Three defects came out of it, all in the
same place — writing down what the manual *means*:

- `/db/ELEM` was promoted with `STYPE: 1` twice and `STYPE: 2` twice. The gate
  is the pair with `TYPE`, whose values live in the chapter's footnoted code
  table. The `resolution` said "the manual gives no wire selector value"; the
  code table gives every one of them.
- `/db/FIMP`'s table keys rows `"KENPAR"."FC"` and never lists the
  `CONC`/`STEEL` parents, so the contract declared a three-level object as ten
  flat top-level fields — replacing a correct payload with a wrong one.
- The generated union then said `HYS_MODEL` could only be `"KPM"`, in a chapter
  whose own callout says Kent & Park is one representative of many models.

Both the extractor and the validator now refuse those shapes, so they cannot
recur silently. The conclusion for this prompt: **live-harness work is yours;
contract promotion is not.** The tasks below follow that split.

## Measured starting state

Run these first and confirm you see the same numbers. If any differ, say so
before starting — it means something moved under you.

```bash
python -m pytest -q                       # 916 passed
ruff check src tests scripts && mypy      # clean
python scripts/validate_contracts.py      # OK, 337 contracts
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
                                          # {"has_diff": false}
cd packages/typescript && npm run generate && npm run typecheck && npm test
                                          # no drift, 55 tests
```

Coverage as `ROADMAP.md` reports it: **399/399 implemented, 171 write / 228
read.** `schema/live-cases.json` holds **167 cases, 141 confirmed**.

Contract drafts — clear and re-emit before judging anything about them.
`contracts/drafts/` is git-ignored build output, and a stale copy has misled a
run before:

```bash
rm -rf contracts/drafts
MSYS_NO_PATHCONV=1 python scripts/extract_contracts.py \
  --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all     # 47 drafts
python scripts/promote_contract.py --all --dry-run          # 0 promoted, 47 refused
```

**Zero of the 47 are promotable, and that is expected.** There are 124 blocking
review notes across 31 drafts, and the large groups are all judgment: 26 "types
this as an enum but the values are listed elsewhere", 18 "types this X but it
has nested children", 7 "marks this conditional but does not state the
condition". Nine more drafts sit in `NEEDS_HAND_REVIEW` because their documented
payload is already measured wrong live. None of that is yours. Task 3 is the one
bounded parser gap left in the pile.

---

## Task 1 — `/db` write coverage (the main task)

74 `/db` endpoints are still read-level. They split cleanly:

- **19 already have a live case** that has not passed:
  `/db/ACTL`, `/db/CGLP`, `/db/DOEL`, `/db/EPSE`, `/db/EPST`, `/db/FBLA`,
  `/db/HPCE`, `/db/MADO`, `/db/MVCT`, `/db/NLLP`, `/db/NLNK`, `/db/NLNK-M1`,
  `/db/RPSC`, `/db/SBDO`, `/db/STCT`, `/db/STRPSSM`, `/db/TDMF`, `/db/THMS`,
  `/db/WVLD`
- **55 have no case at all.** The biggest coherent cluster is moving-load and
  lane — one manual chapter, 19 endpoints: `/db/LLANch`, `/db/LLANid`,
  `/db/LLANop`, `/db/LLANtr`, `/db/MLSP`, `/db/MLSR`, `/db/MVCTbs`,
  `/db/MVCTid`, `/db/MVCTtr`, `/db/MVHLtr`, `/db/MVLDbs`, `/db/MVLDch`,
  `/db/MVLDeu`, `/db/MVLDid`, `/db/MVLDpl`, `/db/MVLDtr`, `/db/SINF`,
  `/db/SLAN`, `/db/SLANch`, `/db/SLANop`

**Start with the 19.** A fixture that exists is cheaper to triage than one you
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
   - **passed** → `confirmed=True`, `level: "write"`, and set
     `live_verified.date` to **the day the write actually happened**. Two
     entries in `801abe0` kept an old date beside a new build and put a session
     that never existed into `ROADMAP.md`'s version matrix.
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

1. **Read out what is already claimed.** Go through
   `docs/live_verification_notes.md` and list every endpoint a passage says the
   built npm package completed, with its date and product. Put the list in a
   scratch file, report the count, and stop there. This step is a measurement,
   not a schema change.
2. **Then extend it by running.** Pick endpoints Python has confirmed but npm
   has not, in batches of at most 8:

   ```bash
   npm run live:crud -- -- --product gen --endpoints /db/AAA,/db/BBB \
     --save-dir <a writable directory on the NX machine>
   ```

   Record each result in `docs/live_verification_notes.md` in the same style as
   the existing npm passages.

**Where to record it structurally is Claude's call.** If step 1 makes it obvious
that a field in `docs/coverage.json` would help, say so in your report and leave
the schema alone.

## Task 3 — nothing here for now

The tree-marker parser gap this section used to describe is fixed, along with
two shipped payload defects it turned up on the way. Contract work is now
blocked on reading manual sections, which is Claude's half of the split.

If Tasks 1 and 2 finish before new work is scoped, report and stop rather than
looking for something in `contracts/drafts/`. All 47 are refused on purpose.

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
  generation emits a trailing member carrying the remaining values. 11 of the 14
  union payloads have one. Do not "tidy" them away.
- **`docs/coverage.json` carries one row per result table, not per route.**
  `/DESIGN/RC/KDS-41-20-2022/TABLE` has three rows and
  `/DESIGN/SRC/AIK-SRC2K/TABLE` two, because each `TABLE_TYPE` returns its own
  table. The contracts fold those same sections into one endpoint each. Both are
  right; do not "reconcile" them.
- **Seven manual defects are registered** in `docs/manual_defects_register.md`,
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
- **A manual section states its request twice** - a Specifications table and
  often a JSON Schema - and where they disagree the table is the lossy one.
  44 of the 337 promoted contracts and 22 of the 47 drafts are missing at
  least one path their own section's schema declares; MD-10 in
  `docs/manual_defects_register.md` has the measurement. A missing *root*
  now blocks promotion outright. Do not try to close these by editing a
  contract - each needs its section read.
- **`/db/NMAS` must be sent with `rmX`/`rmY`/`rmZ`.** Omitting them ends the
  session on both products. Both SDKs fill them in, and the npm side is
  live-confirmed to do so on a real POST.

## Before every commit

Run the full set for each surface you touched — the block under "Measured
starting state" is the whole list. `git diff --check` too; a trailing space in a
YAML folded block has blocked a commit here before.
