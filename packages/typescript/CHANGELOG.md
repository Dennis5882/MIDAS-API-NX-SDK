# Changelog

This file records changes to the JavaScript/TypeScript package published on
npm as `midas-nx`. Python package history is tracked separately in the
repository's `docs/release_notes_v*.md` files and `py-v*` GitHub Releases.

## Unreleased

## 2.7.2 - 2026-08-31

### Changed

- Generated payload declarations now use 22 additional reviewed endpoint
  contracts, including their documented nested shapes, requirements and enum
  values.
- Resource metadata retains the manual's labels and punctuation for the
  reviewed analysis-control and seismic-device resources.
- Adds maintainer-only live CRUD and analysis harnesses that make a verified
  checkpoint before dependent scratch-model cases.

### Compatibility

- The newly contracted payload declarations are more specific. Existing
  TypeScript calls that supplied incomplete or incorrectly shaped payloads may
  now fail typechecking; no general runtime payload validation was added.

## 2.7.1 - 2026-08-30

### Added

- Result-table wrappers for the analysis, story and design-force tables,
  generated from reviewed table contracts.

### Changed

- Payload types for the newly contracted endpoints are generated from
  `contracts/` rather than from the reviewed Python model.
- Resource metadata follows three same-day manual revisions: corrected English
  labels for the design chapters, and `/db/POLC-M1` regaining `POST` after a
  live Civil NX call disproved the chapter that denies it.

### Compatibility

- `EigenvalueAnalysisControlPayload`,
  `EigenvalueAnalysisControlHyperSPayload`,
  `NonlinearAnalysisControlDataPayload` and `SkewPayload` are now declared as
  type aliases rather than interfaces. Names, namespaces and members are
  unchanged, so assigning and reading them is unaffected; code that `extends`
  one of them, or relies on declaration merging, needs updating.
- `resources.db.pushover.pushoverLoadCaseHyperS` accepts `create()` again.

## 2.7.0 - 2026-08-28

### Added

- `/db/BODF` (Self-Weight) now has a reviewed language-neutral contract. Its
  generated npm payload requires `LCNAME` and documents the self-weight factor
  vector.

### Changed

- Contracted fixed-length arrays now generate TypeScript tuples. This preserves
  documented array lengths at compile time rather than widening every vector to
  `Array<number>`.

### Compatibility

- `resources.db.staticLoads.selfWeight` now requires `LCNAME`, and its `FV`
  value must contain exactly three numbers. This corrects the published type to
  the documented request shape; existing TypeScript calls that omitted the load
  case name or supplied a non-three-value vector need updating.

## 2.6.1 - 2026-08-28

### Fixed

- Generated operation wrappers now carry the reviewed Gen NX/Civil NX product
  support from `docs/coverage.json`. Calling a Gen-only operation such as
  `operations.ope.getStoryCheckParameter()` with a Civil client now rejects
  with `ProductMismatchError` before sending a request that would return 404.
- Product-mismatch failures from operation wrappers are Promise rejections,
  consistent with their declared async API.

## 2.6.0 - 2026-08-28

### Breaking

> Released as a **minor** bump, at the author's decision, to keep the npm and
> PyPI version numbers aligned. If your code reads `metadata.pythonModule` or an
> operation's `pythonModule`/`pythonFunction`, it will stop compiling on this
> upgrade even though the number does not say so.

- `DbResourceMetadata.pythonModule` and `OperationMetadata.pythonModule` /
  `pythonFunction` are gone. The npm package was shipping the PyPI package's
  module paths (`"midas_nx.db.static_loads"`) to JavaScript users - nothing a
  caller could act on, and a standing advertisement that one language surface
  was generated from the other. `DbResourceMetadata` gains an optional
  `manualChapter` instead, naming the official manual chapter that documents the
  endpoint.

### Added

- `tableTypes` - every `TABLE_TYPE` value from `contracts/tables/*.yaml` as a
  named constant. Previously the npm package named only whichever value a table
  wrapper defaulted to, so variants like `REACTIONL` and
  `REACTIONSURFACESPRING` were reachable only by a caller who already knew they
  existed. The Python package has always named them.

### Changed

- Payload types for contracted endpoints are generated from `contracts/`
  rather than from the Python `TypedDict`s. This makes them more accurate, not
  merely differently sourced: the `TypedDict`s are all `total=False`, so every
  field they produced was optional regardless of what the manual said. Six
  endpoints so far - `/db/RIGD`'s `DOF` and `S_NODE` are now correctly required,
  and its `ITEMS` array carries its real element shape.

## 2.4.0 - 2026-08-27

### Fixed

- **`db.staticLoads.nodalMass` could crash a live MIDAS NX session.** Creating or
  updating a nodal mass without `rmX`/`rmY`/`rmZ` sent the payload to the product
  unchanged. Omitting those three fields has been observed to hang the call and
  end the NX session across both Gen NX and Civil NX; the Python package has
  filled them with their documented default of `0` since 2026-07-29, and this
  package shipped without that protection. `create()` and `update()` now apply the
  same defaults, without overriding any value the caller supplied.

### Added

- `DbResourceMetadata.payloadDefaults`, generated from the new language-neutral
  endpoint contracts in `contracts/`, so an endpoint's safety rules reach both the
  npm and PyPI packages instead of only whichever one they were written in. CI
  fails when either package stops honouring a contract.

## 2.3.4 - 2026-08-27

### Added

- Package-local changelog and an npm release checklist for the independent
  `js-v*` release stream.

### Changed

- Added separate npm trusted-publishing automation for `js-v*` GitHub
  Releases, independent from the Python `py-v*` release stream.

## 2.3.3 - 2026-08-26

### Changed

- Hardened destructive-operation safeguards and kept per-ID deletion
  deliberately sequential.
- Expanded result-table option types and generated operation/table typings.
- Propagated live-verification safety warnings into the published TypeScript
  declarations and added CI checks for those warnings.
- Added packed-artifact smoke tests for both CommonJS and ESM consumers on
  Node.js 18 and 22.

## 2.3.2 - 2026-08-26

### Added

- Initial typed JavaScript/TypeScript SDK for MIDAS Civil NX and MIDAS Gen NX.
- Generated DB resources, operations, result-table wrappers, and payload types
  from the reviewed Python endpoint inventory.
- ESM, CommonJS, and TypeScript declaration outputs.
- Client, document, operation, table, error, and safety APIs with Vitest and
  TypeScript validation.
