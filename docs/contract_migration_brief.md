# Finishing the contract migration

A working brief for whoever picks up the next stage — human or agent. It states
where the migration actually stands (measured, not estimated), what the rules
are, and what order the remaining work goes in.

`CLAUDE.md` and `contracts/README.md` are authoritative. Where this file and
either of those disagree, they win and this file is stale.

Numbers below were measured on 2026-08-28 at `c2a4599`. Regenerate rather than
trust them:

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
| endpoint contracts | 278 | — | `post-table.yaml` is the shared-table family contract |
| npm DB resources | 236 | 304 | 68 resources still have no committed endpoint contract |
| `/post/TABLE` result tables | 87 | 87 | Chapter 23's other two routes are `/post/PM` and `/post/STEELCODECHECK`, not `TABLE_TYPE` tables |
| active promotion candidates | 0 | 105 drafts | re-run the dry-run gate after every extractor change; its output, not this table, is authoritative |

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

1. **D2 — `post.ts` tests.** Cheapest, and closes a live-hazard gap.
2. **Conditional variant tables — 45 refusals, now the largest single blocker.**
   This is a *schema design* question, not a parsing one:
   `contracts/schema/endpoint-contract.schema.json` has no way to express "these
   fields apply when `TYPE=X`". Do not invent a representation unilaterally;
   bring a proposal to the author first.
3. Remaining extraction fidelity: conditional-without-condition (23), Required
   column blank (15), enum values elsewhere (14), array element types (9).
4. `no payload fields could be parsed` (16), and methods stated nowhere (26,
   confined to `09_DB_Dynamic_Loads.md` and `10_DB_Construction_Stage.md`), are
   genuine manual gaps rather than extractor bugs. They need the manual repo,
   not code.
5. **Stage 4 — Python derives from the contracts.** Deliberately last and
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
