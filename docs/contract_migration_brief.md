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

### D1 — 164 sdkRules are declared, 1 is enforced

`_check_python_normalization()` in `scripts/validate_contracts.py` actually
calls the SDK and inspects the payload it would send — but only for
`kind: normalize_defaults`, of which there is exactly one (the `/db/NMAS`
rotational-mass rule).

| kind | count | executed against either SDK? |
| --- | ---: | --- |
| `per_id_request` | 80 | no |
| `require_confirmation` | 80 | no |
| `normalize_defaults` | 1 | **yes** |
| `node_id`, `warn` | 3 | no |

The behaviour those 163 rules describe *is* implemented and *is* tested in both
languages — but by tests written independently of the contract, which is exactly
the coupling the contract system exists to create. The safeguards live in the
`DbResource` / `db-resource.ts` base classes, so today they are uniform and the
practical risk is low; the moment one endpoint needs to deviate, nothing
notices.

`validate_contracts.py` also prints `OK - contracts valid and both SDK surfaces
match them`, which claims more than it checked.

**Fix**: drive `per_id_request` and `require_confirmation` from the contract the
way `normalize_defaults` already is — exercise the base class once per kind
against a recording client, in both languages, and make the summary line state
what was actually verified rather than implying all of it was.

### D2 — the npm package's riskiest adapter has no tests

```text
packages/typescript/tests/   5 files, 27 tests
post.ts          165 lines  ->  0 tests
doc.ts            77 lines  ->  0 tests
errors.ts         42 lines  ->  0 tests
design-tables.ts  39 lines  ->  0 tests
```

`post.ts` contains `unwrapTable()`, the implementation of a documented live
hazard: `/post/TABLE`'s top-level response key is unstable and has been seen as
`"Result Table"` and `"empty"` as well as the `TABLE_NAME` that was sent, so
matching on key name is unsafe and the table must be found by its `HEAD`/`DATA`
shape. `"empty"` is just the default key for a blank `TABLE_NAME` and **can
carry a full table** — reading it as "no data" is a defect.

Python pins this in `tests/post/test_post_base.py` against the keys actually
observed live. TypeScript pins nothing.

**Fix**: port those cases, including the `"empty"`-carries-a-real-table case and
a response with no table-shaped value at all. Then cover `doc.ts` and
`errors.ts`.

## Order of work

1. **D2 — `post.ts` tests.** Cheapest, and closes a live-hazard gap.
2. **D1 — contract-driven verification of the other rule kinds.** One base class
   per language unlocks 160 rules at once.
3. **Conditional variant tables — 45 refusals, now the largest single blocker.**
   This is a *schema design* question, not a parsing one:
   `contracts/schema/endpoint-contract.schema.json` has no way to express "these
   fields apply when `TYPE=X`". Do not invent a representation unilaterally;
   bring a proposal to the author first.
4. Remaining extraction fidelity: conditional-without-condition (23), Required
   column blank (15), enum values elsewhere (14), array element types (9).
5. `no payload fields could be parsed` (16), and methods stated nowhere (26,
   confined to `09_DB_Dynamic_Loads.md` and `10_DB_Construction_Stage.md`), are
   genuine manual gaps rather than extractor bugs. They need the manual repo,
   not code.
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
