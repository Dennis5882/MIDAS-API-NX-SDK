# Changelog

This file records changes to the JavaScript/TypeScript package published on
npm as `midas-nx`. Python package history is tracked separately in the
repository's `docs/release_notes_v*.md` files and `py-v*` GitHub Releases.

## Unreleased

## 2.7.4 - 2026-09-02

### Compatibility — breaking

Three payload types were flat `interface`s with every member optional and are
now **discriminated unions**, the same change `FloorLoadPayload` went through
in 2.7.3. The version number is a patch; this section is the reason to read it
anyway.

| Type | Endpoint | Discriminator |
| --- | --- | --- |
| `StaticSeismicLoadPayload` | `/db/SSEIS` | `PERIOD_METHOD`, `SEIS_CODE` |
| `StaticWindLoadPayload` | `/db/SWIND` | `INPUT_METHOD`, `WIND_CODE` |
| `TendonProfilePayload` | `/db/TDNA` | `SHAPE`, `INPUT` + `CURVE` |

Three things this affects:

- **Fifteen members became required.** `SEIS_CODE`, `SCALE_FACTOR_X`,
  `SCALE_FACTOR_Y` and `PARAMETERS` on the seismic payload; `WIND_CODE` and
  the same three on the wind one; `NAME`, `TDN_PROP`, `ELEM`, `INPUT`,
  `CURVE`, `LENG_OPT` and `SHAPE` on the tendon profile. The manual marks all
  fifteen Required; the old declarations were wrong about that.
- **They are `type`s now, not `interface`s.** Code that `extends` one, or
  relies on declaration merging, no longer compiles.
- **Branch fields no longer combine with any discriminator value.**
  `STORY_WIND_PRESSURE` is documented under `WIND_CODE: "USER TYPE"` and
  `SEISMIC_FORCE` under `SEIS_CODE: "USER TYPE"`; the flat interfaces offered
  every branch's fields at once regardless.

No runtime behaviour changed, and no runtime payload validation was added.
This is the declaration moving towards the published manual.

### Fixed

- `SectionColorPayload` (`/db/CO_S`, `/db/CO_T`) offered two of the nine
  documented colour components. The manual compresses them into one row keyed
  `"W_R" ~ "HE_B"`, which was read as two literal keys, so `W_G`, `W_B`,
  `HF_R`, `HF_G`, `HF_B`, `HE_R` and `HE_G` could not be set. All eleven
  fields are now declared.
- Rebar size and bar-count fields no longer reject documented values.
  `RebarDesignCriteriaBy{Beam,Column,Brace}MemberPayload` typed `MAIN_REBAR`,
  `STIRRUPS`, `SIDE_BAR` and `TIES_SPIRALS` as `"D4" | "D5" | "D6" | "D7" |
  "D8"` and the leg counts as `2 | 3 | 4 | 5 | 6`, while the same rows are
  described as `19종 (D4 ~ D57)` and `2 ~ 20` - so every bar size from D10 up
  was untypeable. `SrcLiveLoadReductionFactorPayload` went further and
  accepted the literal string `...(전체 11개)`. Fourteen fields across
  four endpoints - nine distinct names - widen to their declared scalar
  type; a list the manual's own
  description outsizes is no longer read as an enum.
- A discriminated payload no longer rejects the documented values the manual
  gives no table for. `FloorLoadPayload` accepted only `FLOOR_DIST_TYPE` 1 and
  2 while `/db/FBLA` documents 1 to 4, so Polygon-Centroid and Polygon-Length
  were untypeable; `SkewPayload` lost `iMETHOD: 1` (Angle) and
  `MovingLoadCaseBsPayload` lost every load model but `"STANDER"`. Each union
  now carries a trailing member for the remaining values, which still denies
  the other branches' fields, so setting `LOAD_ANGLE` under `FLOOR_DIST_TYPE:
  3` remains an error. A union stays closed only where the contract proves it:
  a declared `enum` the branches cover exactly, or both values of a boolean.
  This widens 10 of the 13 generated union payloads; the remaining three -
  `NodalBodyForcePayload`, `MovingLoadCaseChinaPayload` and
  `EigenvalueAnalysisControlHyperSPayload` - stay closed because the
  contract proves they are. Code that relied on
  exhaustiveness narrowing over one of those discriminators needs a default
  case; nothing that compiled before stops compiling.

### Changed

- Generated payload declarations use 18 more reviewed endpoint contracts
  (319 to 337, counted from what 2.7.3 shipped). `/db/SSEIS`, `/db/SWIND` and
  `/db/TDNA` become discriminated unions on `PERIOD_METHOD`/`SEIS_CODE`,
  `INPUT_METHOD`/`WIND_CODE` and `SHAPE`/`INPUT`+`CURVE`; `/db/ELEM` and
  `/db/MVLD` keep their reviewed fallback payloads, because each has manual
  tables no discriminator could merge. **253 of the 750 generated payload
  types** now come from a contract, and 268 of the 304 resources have one.
  The 2.7.2 and 2.7.3 entries stated that first count against the resource
  count, which is the wrong denominator - resources sharing one payload type
  name collapse into a single type.
- `/db/FIMP` stays on its reviewed fallback. Its manual table keys rows
  `"KENPAR"."FC"` and omits the `CONC`/`STEEL` parents, so a contract drafted
  from it declared a three-level object as ten flat top-level fields.

## 2.7.3 - 2026-08-31

### Compatibility — breaking

- `FloorLoadPayload` (`/db/FBLA`) was a flat `interface` with every member
  optional and is now a **discriminated union** on `FLOOR_DIST_TYPE`, with
  `FLOOR_LOAD_TYPE_NAME`, `FLOOR_DIST_TYPE` and `NODES` required. Omitting one
  of those three, `extends`-ing the payload, or setting fields the manual
  documents under different `FLOOR_DIST_TYPE` values now fails typechecking.
  No runtime behaviour changed and no runtime validation was added.

### Changed

- Generated payload declarations use 10 more reviewed endpoint contracts
  (309 → 319): `/db/FBLA` and the nine `/doc/*` endpoints. 252 of the 304
  generated resources now take their facts from a contract rather than the
  reviewed Python fallback.
- Conditional variants are generated from the contract's `when` conditions,
  which now carry a dotted path and may name several documented values. A table
  the manual shares between branches contributes its fields to each of them
  rather than forming a union member that would match the same discriminator
  twice.

## 2.7.2 - 2026-08-31

### Changed

- Generated payload declarations now use **30 additional reviewed endpoint
  contracts** (279 to 309 since 2.7.1), including their documented nested
  shapes, requirements and enum values. 251 of the 304 generated resources now
  take their facts from a contract rather than the reviewed Python fallback.
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
