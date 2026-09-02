# Finishing the contract migration

A working brief for whoever picks up the next stage — human or agent. It states
where the migration actually stands (measured, not estimated), what the rules
are, and what order the remaining work goes in.

`CLAUDE.md` and `contracts/README.md` are authoritative. Where this file and
either of those disagree, they win and this file is stale.

**Current measurement: "Measurement — 2026-09-02" below.** The two earlier
tables (2026-08-28 at `c2a4599`, 2026-08-29) are kept as history and are
stale. Regenerate rather than trust any of them:

```bash
python scripts/validate_contracts.py
python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --emit-all
python scripts/promote_contract.py --all --dry-run | tail -1
```

## Where it stands

The intended end state is that both SDKs are **equal implementations of the
contracts**:

```text
              contracts/          <- the manual + real Gen NX/Civil NX records
             /          \
   src/midas_nx      packages/typescript
```

| | from contracts | total | |
| --- | ---: | ---: | ---: |
| endpoint contracts | 124 | 304 | 41% |
| npm resource facts (name/products/methods/chapter) | 124 | 304 | 41% |
| drafts currently promotable | 70 | 259 | |

Stage 3 has begun, and begun correctly: `_contract_resource_surfaces()` in
`scripts/generate_typescript_sdk.py` replaces only the facts a contract owns,
leaves `className`/`pythonModule` as compatibility anchors, falls back to the
Python class where no contract exists, and **raises** on any disagreement rather
than warning. `_load_resources()` still does `import midas_nx` for the
uncontracted 59%.

The Python package reads nothing from `contracts/` at runtime and should not
start: contracts are consumed at generation and validation time, so an installed
`midas-nx` still needs only `requests`.

### Continuation measurement — 2026-08-29

The table above records the earlier baseline. Do not use it as current coverage.
The following values were measured after Stage 2 and the result-table work:

| surface | contracted | total | note |
| --- | ---: | ---: | --- |
| endpoint contracts | 279 | — | `post-table.yaml` is the shared-table family contract |
| npm DB resources | 236 | 304 | 68 resources still have no committed endpoint contract |
| `/post/TABLE` result tables | 87 | 87 | Chapter 23's other two routes are `/post/PM` and `/post/STEELCODECHECK`, not `TABLE_TYPE` tables |
| active promotion candidates | 0 | 104 drafts | re-run the dry-run gate after every extractor change; its output, not this table, is authoritative |

The remaining 68 npm resources are not a uniform parser backlog. They include
unmerged conditional tables, missing Default/Required facts, incomplete enum or
array-item facts, and documented live defects. `/db/STYP-M1` is a distinct
manual gap: it appears in `INDEX.md`, but no endpoint section exists under
`docs/manual/`, so the extractor has no manual source from which to draft a
contract.

The manual also uses dotted No.-column paths such as `14.4.1` to show nested
payloads. The extractor now recognises that notation and the nine affected
promoted design contracts were reviewed against their manual tables and request
examples before their children moved under the documented object or array
parents. Manual drift is zero after that shape migration; do not flatten future
dotted rows back to record-root fields.

Current validation exercises 311 declared executable rules: 154
`per_id_request`, 154 `require_confirmation`, and one each of
`normalize_defaults`, `reject_request`, and `unwrap_table_by_shape`. It runs
one Python and one npm probe for every rule kind. The npm suite currently has
11 files and 55 tests.

## Measurement — 2026-09-02, at `3d36a91`

Supersedes the two tables above. The wire facts are nearly migrated; the npm
package's **public surface is not migrated at all**, and that gap is not a
backlog.

| npm artefact | count | contract-sourced | still Python |
| --- | ---: | ---: | ---: |
| DB resource **inventory** (which resources exist) | 304 | 0 | **304** |
| DB resource facts (name / products / methods / chapter) | 304 | **268** | 36 |
| Payload types | 750 | **253** | 497 |
| Operation wrappers (`/doc`, `/ope`, `/view`, design) | 70 | 0 | **70** |
| Result-table wrappers | 87 | 0 | **87** |

337 endpoint contracts and 87 table contracts exist. 12 contracts reach
nothing in npm; 13 contracted resources carry `unmergedTables`, so their
payload stays on the Python type.

### The blocker is that a contract cannot name anything

A generated resource entry carries ten fields. Five are contract facts. The
other five have **no property in `endpoint-contract.schema.json`** and no
way to acquire one without a decision:

| field | example | expressible in a contract today |
| --- | --- | --- |
| `endpoint` | `/db/BCGA-M1` | yes |
| `name` | `Assign Boundary Combination (Hyper-S)` | yes |
| `products` | `["civil"]` | yes |
| `methods` | `[DELETE, GET, POST, PUT]` | yes |
| `manual[].chapterFile` | `12_DB_Analysis_Control.md` | yes |
| `className` | `AssignBoundaryCombinationHyperS` | **no** |
| `exportName` | `assignBoundaryCombinationHyperS` | **no** |
| `pythonModule` | `midas_nx.db.analysis_control` | **no** |
| `modulePath` | `["db", "analysisControl"]` | **no** |
| `payloadTypeName` | `AssignBoundaryCombinationHyperSPayload` | **no** |

The same holds for the other two artefact kinds. An operation entry's *data*
is `{endpoint, method, products}` — all three contract facts — but its
function name (`exportBeamCheckReport`), its nesting (`design.rcKds.checks`),
its argument type name and its JSDoc all come from the Python function, its
module path and its docstring. All 87 result-table wrappers are generated
from the Python AST even though all 87 tables are contracted.

So the arithmetic that matters is not 268/304. It is this: **delete
`src/midas_nx/` and `npm run generate` produces nothing at all**, because
`_load_resources()` opens with `import midas_nx` and `_source_modules()`
parses the package's AST. Contracts can only *correct* facts about something
Python already declares; a contract for an endpoint with no `DbResource`
subclass is skipped outright (`endpoint not in resource_endpoints`).

### Why "compatibility anchors" cannot expire on their own

`CLAUDE.md` and `generate_typescript_sdk.py` both say class and module names
"remain compatibility anchors **until every resource is contracted**". That
sentence describes a finish line the current design cannot cross: contracting
all 304 resources would still leave every name and every module path with
nowhere to live. Writing the 36 missing contracts is worth doing and does not
move this at all.

### The decision this needs (not to be made unilaterally)

D1–D4 were schema decisions about what the *manual* says. This is the first
one about what the *packages* are called, so it is larger, and both public
APIs are already published under those names. Sketch, for the author:

1. ~~**Add a naming block to the contract schema**~~ **Done 2026-09-02.**
   `surface: {className, exportName, modulePath, payloadTypeName}` is in the
   schema and seeded into **268 of 304** contracts from the generator's own
   committed output, so the published APIs did not change by a byte. The
   generator raises on a disagreement — `className`/`exportName`/`modulePath`
   as resources load, `payloadTypeName` after generation picks it, since a
   legacy TypedDict shared by endpoints with different contracts is renamed on
   the way through. Two tests fail first and name the endpoint. The 36
   resources with no contract keep their Python names, which is the same
   arrangement `name` and `products` already had; they are a shrinking
   remainder rather than a precondition.
2. **Invert the generator**: iterate contracts, not `DbResource` subclasses;
   fall back to Python only where a contract has no `surface` block. The
   parity check flips with it — Python becomes a subject like npm already is.
3. **Extend it to operations and tables**, which need the same block plus a
   place for the wrapper's summary text that JSDoc currently takes from a
   Python docstring.

Step 1 gave the names a home; **steps 2–3 are what make `import midas_nx`
deletable**. Measured 2026-09-02 by deleting `src/midas_nx/` in a worktree:
`npm run build`, `typecheck` and `test` all pass from the committed
generated files, but `npm run generate` dies on `ModuleNotFoundError: No
module named 'midas_nx'`, and `prepack` runs `generate` first — so the
package would be frozen at its last published state, usable but not
releasable. Users of the published tarball are unaffected either way; it
declares no dependencies.

## The rules that are not negotiable

These come from the author and are the reason the layout looks the way it does.
Breaking one of them silently is worse than making no progress.

1. **Neither SDK is a source for the other.** Python source, types and
   docstrings may not feed TypeScript generation, and the reverse likewise. The
   existing SDKs are for compatibility checks, regression tests and live
   verification records only.
2. **Permitted sources for a contract** are exactly three: the official manual
   (`E:\AI Study\MIDAS-API`, `docs/manual/*.md`), `docs/live_verification_notes.md`,
   and live `/info/{endpoint}` introspection.
3. **Do not guess.** A field or behaviour the manual does not describe does not
   go into a contract. `unverified` is a correct answer; an invented one is not.
4. **Where the manual and the product disagree, record both separately** — the
   manual's claim in `manualDefects`, the product's behaviour in
   `contracts/verification/`.
5. **A parity failure is an SDK defect, never a reason to edit the contract.**
6. **`documentedOptional` and `safeToOmit` are separate booleans.** "The manual
   says Optional" is not evidence for `safeToOmit: true` — that is what
   `documentedOptional` already records. `/db/NMAS` is the endpoint where
   believing the manual ends a live NX session.
7. **`risk` and `mitigation` are separate axes.** A mitigated crash risk is
   still a crash risk.
8. **Never hand-edit `contracts/drafts/` or `packages/typescript/src/generated/*`.**

Audited at `c2a4599` and holding: of 706 contracted fields, 83 carry
`safeToOmit: true` — every one of them with `omissionEvidence` — 5 carry
`false`, and 618 carry `unverified`. Zero evidence-free claims survived a
threefold expansion of the contract set. Keep it that way.

## The two open defects

Both are the same shape as the bug this whole system was built to prevent: a
rule that exists in both languages but is verified in only one.

### D1 — completed: executable sdkRules run against both SDK implementations

`scripts/validate_contracts.py` now runs all four executable safety-rule
kinds against recording clients. `normalize_defaults` is exercised against its
actual resource for create and update; `per_id_request` and
`require_confirmation` are each exercised once through the shared `DbResource`
base in Python and npm. `unwrap_table_by_shape` exercises the shared result
table response decoder against the four response shapes declared in the
contract, rather than repeating a uniform check for every endpoint.

| kind | count | executed against either SDK? |
| --- | ---: | --- |
| `per_id_request` | 80 | **yes — Python + npm base probe** |
| `require_confirmation` | 80 | **yes — Python + npm base probe** |
| `normalize_defaults` | 1 | **yes — Python + npm resource probe** |
| `unwrap_table_by_shape` | 1 | **yes — Python + npm response-shape probe** |

`node_id` is a `recordKey.kind`, not an `sdkRule` kind. All 162 currently
declared sdkRules are executable and covered by the validator; no `warn` rule
remains. The validator prints the declared-rule counts and the Python/npm probe
counts, and no longer claims broader parity than it executed.

### D2 — completed: live-hazard adapters have npm tests

```text
packages/typescript/tests/   11 files, 53 tests
post.ts          165 lines  ->  covered
doc.ts            77 lines  ->  covered
errors.ts         42 lines  ->  covered
design-tables.ts  39 lines  ->  covered
types.ts          30 lines  ->  covered
```

`post.ts` contains `unwrapTable()`, the implementation of a documented live
hazard: `/post/TABLE`'s top-level response key is unstable and has been seen as
`"Result Table"` and `"empty"` as well as the `TABLE_NAME` that was sent, so
matching on key name is unsafe and the table must be found by its `HEAD`/`DATA`
shape. `"empty"` is just the default key for a blank `TABLE_NAME` and **can
carry a full table** — reading it as "no data" is a defect.

TypeScript now pins the observed `TABLE_NAME`, `"Result Table"`, and `"empty"`
keys, including an `"empty"` response carrying real data and a response with no
table-shaped value. `doc.ts` and `errors.ts` have direct adapter tests as well.
`design-tables.ts` and `types.ts` now have direct tests too.

## Order of work

Re-measured 2026-08-30. The list below carried its original 2026-08-28 counts
long after the work had moved them, and a review repeated one of the stale
figures back as if it were current — so treat any number here as a measurement
with a date, and re-run `--report` before quoting one.

1. ~~**D2 — `post.ts` tests.**~~ Done. `packages/typescript/tests/post.test.ts`
   exists and the npm suite is 11 files, 55 tests.
2. **Conditional variant tables — still the largest single blocker, and still an
   author decision.** `contracts/schema/endpoint-contract.schema.json` has no way
   to express "these fields apply when `TYPE=X`" beyond a single scalar `equals`;
   `/db/FBLA`'s documented `FLOOR_DIST_TYPE = 1 or 2` cannot be transcribed at
   all (see `contract_migration_open_questions.md`). Do not invent a
   representation unilaterally; bring a proposal to the author first.

   Re-measured by `extract_contracts.py --report` on 2026-08-30: 253
   supplementary tables comprise 24 explicit variants, 23 reviewed
   field-level `appliesWhen` merges, 51 structural merges, and 155 unmerged
   tables. The latter split into 4 labels that state several selector values,
   53 that state one literal value, and 98 that state no selector. The report
   prints every unmerged endpoint/table/line with that evidence classification;
   use it rather than a hand-counted section total when judging this item.
3. Remaining extraction fidelity, as field occurrences: conditional-without-
   condition (7), Required column blank (7), enum values unstated (20), array
   item type unstated (5), unrecognised Value Type cell (15).
4. **16 sections have no parseable parameter table, and none of them is a manual
   gap.** They are nine `/doc/*` endpoints in `01_DOC.md` and seven Hyper-S
   `-M1` endpoints in `04_DB_Properties.md` — not, as this list previously said,
   `09_DB_Dynamic_Loads.md` and `10_DB_Construction_Stage.md`. Both groups
   document their payload in a form the extractor does not yet read rather than
   failing to document it: `/doc/OPEN` carries a JSON Schema and no
   Specifications table because its whole argument is one path string, and
   `/db/MATL-M1` delegates with `기본 재료 구조는 /db/MATL과 동일하며` instead of
   repeating the parent's table. Reading either is extractor work, not something
   to ask the manual repo for.

   The companion claim that 26 sections state their methods nowhere is also
   spent: the count is now **0**, closed by teaching `_section_methods()` all six
   forms the chapters use. What that function still gets wrong is reading verbs
   out of text that is not a declaration — see the `/db/POLC-M1` entry in
   `contract_migration_open_questions.md`.

   ~~The one real manual gap is `/db/STYP-M1`.~~ Closed 2026-08-30: the manual
   repo wrote the section (`5c92efe`). `npm resource manual-section coverage`
   is now **0 without a parsed section**. What still blocks that contract is
   the extractor's child numbering, not the manual — see
   `contract_migration_open_questions.md`.
5. **Stage 3 completion — npm stops deriving from Python.** Newly separated
   out on 2026-09-02, because it was being counted as part of "contract more
   resources" and it is not. The wire facts are 268 of 304 contracted; the
   npm package's names and module layout are 0 of 304, and no contract
   property can hold them. See "Measurement — 2026-09-02" for the field-by-
   field gap and the three-step sketch. **Needs the author's decision on
   which names contracts may own before any code moves.**
6. **Stage 4 — Python derives from the contracts.** Deliberately last and
   deliberately unspecified. `src/midas_nx/` is hand-written and its public API
   is on PyPI; changing how it is produced needs the author's call, not an
   agent's. Until then Python stays a *subject* of the parity check, which is
   already true and already valuable.

## Verification before any commit

```bash
pip install -e ".[dev]"      # after any version bump, or test_version fails
pytest && ruff check src tests scripts && mypy
python scripts/validate_contracts.py
python scripts/extract_contracts.py --manual-api-repo "E:\AI Study\MIDAS-API" --check
cd packages/typescript && npm run generate && npm run typecheck && npm test
git status --short           # generation drift must be empty
```

CI runs all of this on 3.12/3.13 and Node 18/22 and fails on generated-file
drift. It has been red on `main` while a release was tagged before — check that
it is green rather than assuming.

## Releasing

Don't, unless the author asks. Versions are **lockstep** across PyPI and npm
since 2026-08-28: one number, both registries, a `py-vX.Y.Z` and a `js-vX.Y.Z`
Release each time, even when one surface has no shipped change. `scripts/`,
`docs/` and `.github/` ship in neither package and warrant no release on their
own — much of the work above is exactly that, so expect to commit without
releasing. The author picks the number.

## Handoff — 2026-08-30, at `49f3eca` (post-2.7.1)

Measured, not estimated. Every number below came from a command in this file;
re-run them before quoting one, because the list above them is a record of
counts that went stale while nobody re-measured.

### State

| | |
| --- | ---: |
| promoted endpoint contracts | 279 |
| result-table contracts | 87 (139 `TABLE_TYPE` values) |
| drafts awaiting review | 104 |
| npm resources with no contract | 68 |
| ...of which `/db/STYP-M1` is the only one with no draft either | 1 |
| contracted fields / proven safe to omit / proven unsafe | 2162 / 123 / 5 |
| Python tests · npm tests | 845 · 55 |

All four gates are green at this commit: `pytest`, `validate_contracts.py`,
`extract_contracts.py --check`, and npm `typecheck`/`test` with no generation
drift. Both registries are published at 2.7.1.

### The 104 refused drafts, partitioned by why

`python scripts/promote_contract.py --all --dry-run` refuses every one of them.
The refusals are not one backlog; they are five, and only one needs the author:

| n | refusal | who unblocks it |
| ---: | --- | --- |
| 48 | unresolved review notes — missing Default/Required columns, non-literal defaults (`"System"`, `"Auto"`, `"ADD, REPLACE"`) | per-draft review against the manual |
| 19 | conditional variant tables nobody has merged | **the author** — schema decision |
| 16 | no payload fields could be parsed | extractor work (see below) |
| ~10 | the manual is provably wrong live | `manualDefects` + `contracts/verification/`; evidence already in the repo |
| 5 | the Key cell names several wire properties, not one | per-draft transcription |

The 16 unparseable sections are **not** manual gaps: nine `/doc/*` sections in
`01_DOC.md` carry a JSON Schema instead of a Specifications table, and seven
Hyper-S `-M1` sections in `04_DB_Properties.md` delegate with
`기본 재료 구조는 /db/MATL과 동일하며` rather than repeating the parent table.
Reading either form is extractor work. Do not ask the manual repo for them.

### Order for the next agent

1. **`/db/STYP-M1` — smallest real win, and it closes the last no-draft
   resource.** Two extractor edits, measured to change exactly one section and
   zero promoted contracts, plus two enum-from-condition defects and one
   boolean-rendered-as-string. Full measurement and the reason a one-line regex
   change measures as a no-op: `contract_migration_open_questions.md`.
2. **Widen the generator's shadow gate past `/db/*`**
   (`scripts/generate_typescript_sdk.py:395`, `:530`). The Korean-label
   question that justified the narrow filter is settled; 63 `/DESIGN/*`
   contracts are currently unchecked against the npm surface. Every gate
   widened on 2026-08-30 found real drift on its first run — 114 stale labels,
   one wrong method set, 103 stale section strings. Expect this one to as well.
3. **The 48 review-note drafts**, in chapter order. Mechanical, reviewable in
   batches, and the largest single movement available without an author call.
4. **The ~10 manual-is-wrong-live drafts.** The evidence exists —
   `/db/SECF`'s key, `/db/PRES`'s `DIRECTION`, `/db/MVHL`'s
   `VEHICLE_LOAD_NUM`, `/db/TDMT`'s whole code-name enum, `/db/REBW`'s entire
   Specifications table. Each needs the manual's claim under `manualDefects`
   and the product's behaviour under `contracts/verification/`, separately.
   Never collapse the two into one.
5. **The 16 unparseable sections** — JSON-Schema `/doc/*` bodies and delegating
   `-M1` sections. Two distinct parsers, each worth its own commit.
6. **Conditional variants — the schema decision comes last, and by then it is
   much smaller.** See the staged plan below. Steps 0-2 need no author
   decision; do those first, because they change what the decision is about.

### Two reports owed to the manual repo, not to this one

Both are live-measured and neither has been sent:

- `02_DB_Project_Structure.md` declares `DELETE` for `/db/STYP-M1` in three
  places. The server refuses all three DELETE forms on both products, from a
  non-default state with a real model open. The official article is the
  upstream source of the error, so it needs reporting to MIDAS IT as well.
- `14_DB_Pushover.md`'s ⚠️ callout dismisses `/db/POLC-M1`'s POST as an
  untrimmed template. POST works: it created a record that read back on the
  next GET. The callout is what is wrong, and it should be reversed.

`docs/coverage.json`'s `vendored_at_commit` is still `2cfb2bd`. Raise it past
`5c92efe` once `/db/STYP-M1` is promoted, and confirm `check_manual_drift.py`
reports `has_diff: false` — not before.

### Corrections to earlier revisions of this file

Stated here because each was believed and repeated:

- `/post/PM` and `/post/STEELCODECHECK` are **implemented** in both SDKs
  (`src/midas_nx/post/design.py`, `generated/operations.ts`) and marked
  `implemented` in `docs/coverage.json`. They are uncontracted, which is a
  different and much smaller thing than missing.
- The `N-(M)` numbering fix touches one section, not 71 rows of reshaping.
- `/db/STYP-M1` is no longer a manual gap.
- The Korean-label decision is settled: English.

## Conditional variants: a staged plan, with the schema decision last

Measured 2026-08-30. Read this before treating the 19 refused drafts as one
blocked queue — most of what looks like a schema problem is not one.

### The counter is measuring the wrong thing

176 supplementary tables sit in `extraction.unmergedTables` across 40
endpoints. The extractor labels each with the nearest `#` heading, and the
chapters label a variant table **two** ways:

```text
### 8-2. 파라미터                             <- what the extractor records
| No. | ... |                                   (the common table)

**Time Function (FUNCTYPE=1) 추가 파라미터**    <- the selector lives here
| No. | ... |
**Sinusoidal (FUNCTYPE=2) 추가 파라미터**
| No. | ... |
```

A bold label is not a markdown heading, so every bold-labelled variant table
inherits its section's heading and is filed as "selector not explicit" when the
manual states the selector plainly. `/db/CCFC`'s `TYPE="CONST"` / `TYPE="USER"`
and `/db/THFC`'s `FUNCTYPE=1` / `FUNCTYPE=2` are this case.

The scratch classifiers are retired. The reproducible report now counts **253
supplementary tables**: 24 explicit variants, 23 audited field-level
`appliesWhen` merges, 51 structural merges, and 155 still unmerged. Of those
155, the manual label names a selector with several values in 4 cases, one
literal value in 53 cases, and no selector in 98 cases. `--report` prints the
endpoint, source line, heading, and category for every unmerged table. Bold
labels immediately before a table are now read; prose and inline bold emphasis
are not labels. This is the measurement for the author's schema decision, not
a claim that every one-value table is ready to promote.

### The proposal: unify `when` onto `appliesWhen`, do not invent

The schema already carries two condition constructs, and they have diverged:

| | shape | dotted path | AND | several values |
| --- | --- | :-: | :-: | :-: |
| field `appliesWhen` | `[{path, equals}]` | yes | yes | no |
| `variant.when` | `{field, equals}` | no | no | no |

Give `variant.when` the same shape as `appliesWhen`, and add `in` to both:

```yaml
variants:
  - when: [{ path: FLOOR_DIST_TYPE, in: [1, 2] }]          # the OR case
  - when: [{ path: STR.SPEC_CODE, equals: "KS_BRG" }]      # nested selector
  - when: [{ path: TYPE,  equals: TENSTR },                # two-level
            { path: STYPE, equals: 1 }]
```

One array-of-AND-conditions covers all three shapes that block drafts today.
It is not a new concept: `/db/STYP-M1`'s draft already renders
`appliesWhen: [{path: MASS_CONTROL.MASS_TYPE, equals: LUMPED}]`. Constrain
`equals` and `in` as mutually exclusive and require `in` to carry two or more
values, so the looser form cannot be used where the tighter one applies.

**Deliberately out of scope**, and they should stay in `unmergedTables`:

- **Presence-selected variants.** `/db/EPMT`'s
  `Tresca / Von-Mises 공통 파라미터 (`"TRESCA"` or `"VMISES"` object)` switches
  on *which object the payload carries*, not on a scalar's value. Different
  mechanism; do not fold it into this decision.
- **Label-only tables.** `/db/ELEM`'s `#### Wall`, `#### Plate`. `TYPE="WALL"`
  is obvious to a human and is not written down. Leaving these unmerged is what
  rule 3 requires, not a failure. Ask the manual repo to state the selector.

Resolving a label against the discriminator's own enum row
(`"TR"(Tresca)` in `MODEL_TYPE`'s Description, matching `#### Tresca ...`) was
measured as a possible bridge: it resolves only two tables. Not a lever.

### Order — steps 0-2 need no author decision

0. ~~**Teach the extractor to read bold table labels**, and stop filing prose
   as a variant label.~~ Done; fixtures cover bold labels and prose.
1. ~~**Fix the counter.**~~ Done; it measures supplementary tables and their
   actual resolution rather than sections.
2. ~~**Re-measure.**~~ Done; the 253/155 evidence breakdown above is the real
   decision surface.
3. **Then** take the `when`/`in` proposal above to the author.

## What is mechanical, and what is not

The 48 drafts refused for review notes carry 572 notes in 23 distinct forms.
They are not equally hard, and the split is sharp:

| notes | form | mechanical? |
| ---: | --- | --- |
| 262 | the table has no Default column | **yes** — `documentedDefault: null` already means "the manual gives none" |
| 140 | the table has no Required column | **no** — `requirement` and `documentedOptional` have no "unstated" value |
| 18 | the table has no Value Type column | no — same reason |
| 99 | non-literal default `"System"`/`"Auto"`/`"ADD, REPLACE"` kept verbatim | no — needs a live check |
| 12 | enum values are listed elsewhere in the chapter | partly — the values exist, finding them is reading |
| 41 | cross-field constraints, type/child contradictions, unstated conditions | no |

Partitioned by draft rather than by note:

- **8 drafts are blocked only by "no Default column"** and are fully
  mechanical: `db-sdhy`, `db-sdis`, `db-sdst`, `db-sdve`, `db-sdvi`,
  `db-mvctch`, `db-nllp`, `db-wvld`.
- **4 more** (`db-actl-m1`, `db-mcon`, `view-active`, `view-select`) are blocked
  only by missing-whole-column notes, but include a missing Required or Value
  Type column. They become mechanical **only if** the schema gains an
  "unstated" requiredness — a small, separate author decision, and the honest
  one, because inventing `optional` for a blank column is exactly the
  `documentedOptional`/`safeToOmit` conflation the schema exists to prevent.
- **36 drafts carry at least one judgment note** and are not batch work.

Other mechanical items, for completeness: the `/db/STYP-M1` child numbering
(measured: one section changes, zero promoted contracts), reading bold variant
labels, and fixing the variant counter. Widening the generator's shadow gate is
mechanical to apply but will surface drift that is not.
