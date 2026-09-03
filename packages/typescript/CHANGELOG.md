# Changelog

This file records changes to the JavaScript/TypeScript package published on
npm as `midas-nx`. Python package history is tracked separately in the
repository's `docs/release_notes_v*.md` files and `py-v*` GitHub Releases.

## Unreleased

### Changed — six payload types are now generated from contracts

- `SectionPayload`, `PressureLoadPayload`, `WallRebarPayload`,
  `ColumnRebarPayload`, `BeamRebarPayload` and
  `InelasticMaterialPropertyPayload` now come from `contracts/endpoints/`
  rather than from the Python TypedDict. For the first two that means a **discriminated union**
  over the field the manual actually branches on, with the fields the manual
  marks Required no longer optional.

  `SectionPayload` branches on `SECTTYPE` (`DBUSER`, `VALUE`, `SRC`, `PSC`),
  and each branch carries its own `SECT_BEFORE`. `CALC_OPT` has not been
  removed — it moved into the `VALUE` branch, which is the only one the manual
  documents it for. `PressureLoadPayload` branches on `FACE_EDGE_TYPE` inside
  each `ITEMS` entry: `FORCES` for `"FACE"`/`"PRES"`, `EDGE_LOADS` for
  `"EDGE"`. It also gains `PSLT_KEY`, a `/db/PSLT` reference both products'
  `/info` schema declares and the manual chapter never mentions.

  Code that built one of these as a partial object will now need the required
  members and the discriminant. The compiler points at each one, and the
  branches match what the endpoints already accepted — this narrows the type to
  what the server takes, it does not change any request the SDK sends.

  The three rebar payloads are plainer: `ITEMS` becomes required and its entry
  type is inlined rather than referring to the exported `WallRebarItem` /
  `ColumnRebarItem` / `BeamRebarItem` interface, all of which stay exported and
  unchanged. No field is renamed. These are the endpoints whose manual sections
  document schemas the product does not implement — including in MIDASIT's own
  articles, not just the vendored copy — and this package already shipped the
  server-confirmed names, corrected in 2026-07 and 2026-08.
  `ColumnRebarPayload` also gains `HOOK_TYPE`, the one field of `/db/REBC`
  where the manual survived the comparison intact.

  `InelasticMaterialPropertyPayload` grows the most: 171 members it did not
  declare before. `/db/FIMP` carries seventeen hysteresis-model objects under
  `CONC` and `STEEL`, and the manual documents one of them — its own callout
  says so, pointing at a 5900-line source article it does not transcribe. The
  rest come from the server's own `/info` schema, which both products serve
  identically. Nothing that was there is removed.

  `VehiclePayload` and `TimeDependentMaterialStrengthPayload` were listed here
  in an earlier draft of this entry and are **not** affected. Their contracts
  carry `extraction.unmergedTables` — the manual names no wire discriminator
  for one of their tables — and a contract that admits its field list is
  partial is deliberately not allowed to narrow a published type. Both remain
  the Python-derived interfaces they were.

### Added — `/db/MVHL` refuses an empty `VEH_DEFAULT`

- `vehicles.create()` and `.update()` now throw `MidasRequestError` when
  `VEH_DEFAULT` is sent as `{}`. The server accepts that body, answers
  `{"message": ""}` with no error object, and stores nothing, so the only
  previous signal was a later `get()` showing no vehicle. Omitting
  `VEH_DEFAULT` entirely is unaffected — nine of the documented
  `STANDARD_CODE` values carry their own object instead.

### Added — `/db/PRES` requires an explicit `DIRECTION`

- `pressureLoad.create()` and `.update()` now throw `MidasRequestError` when an
  entry of `ITEMS` omits `DIRECTION`. The manual marks that field Optional with
  the default `"NORMAL"`, and on a `PLATE` with `FACE_EDGE_TYPE: "FACE"` — the
  commonest pressure load there is — the server applies that default and then
  refuses the record, with the same error it gives for `"NORMAL"` sent
  explicitly. There is no default the SDK could substitute: which way a
  pressure acts is an engineering decision, so you are asked rather than
  guessed for.

  Sending `"NORMAL"` yourself is unaffected. The section's own availability
  matrix marks it valid for the other three `ELEM_TYPE`/`FACE_EDGE_TYPE`
  pairs, and refusing a value you typed would overrule that.

  A record with no `ITEMS` at all is left alone — that is a different request,
  not a missing field.

### Fixed — branch fields that were published at the top level

- **`StaticWindLoadPayload`, `StaticSeismicLoadPayload` and
  `LinearConstraintPayload` declared a whole conditional branch in the wrong
  object.** A manual branch table gates on one field and adds siblings of it,
  so the branch belongs wherever that field lives. The generator attached every
  branch to the payload root instead.

  `/db/SWIND` is the clearest case: `INPUT_METHOD`, `WIND_SPEED`,
  `EXP_CATEGORY`, `ROOF_HEIGHT` and the rest were published as top-level
  members, while the section's own worked examples send all of them inside
  `PARAMETERS` — which is also where the contract declares the `INPUT_METHOD`
  they branch on. `/db/SSEIS` had the same shape with `PERIOD_METHOD` and the
  period fields; `/db/MCON`'s `TYPE` branch belongs inside an `ITEMS` entry.

  `ModifyColumnRebarDataPayload` loses `KEYS`, `TO` and `STRUCTURE_GROUP_NAME`
  from its root for a related reason: the manual states them once, under a
  heading naming both a condition and a parent object, and the contract had
  recorded that one table twice - correctly inside `ELEMS`, and again as a
  root-level branch. The `ELEMS` copy is the one that survives.

  This is the same defect as the field-level nesting fix below, one level up:
  a caller following the published type put the fields where the server does
  not look. The members move rather than disappear, and the compiler will point
  at each one.

- **A branch table naming several values was dropped instead of emitted.** A
  multi-value condition was read as the manual's *shared supplement* table —
  `/db/FBLA` states one for `FLOOR_DIST_TYPE = 1 or 2` beside its `= 1` and
  `= 2` tables — and folded into the branches it covers. When it covers none of
  them it is an ordinary branch that happens to span two values, and folding
  discarded it: `/db/PRES`'s `FACE_EDGE_TYPE = "FACE" or "PRES"` branch took
  `FORCES` with it. Overlap now decides which kind a table is.

### Fixed — nested fields that were published at the top level

- **`BeamSectionTemperaturePayload`, `StaticWindLoadPayload` and
  `HeatOfHydrationAnalysisControlHyperSPayload` had members in the wrong
  place.** The manual marks a third level of nesting with a bare letter or
  roman numeral in its No. column (`a`, `b`, `c` / `i`, `ii`, `iii`), and the
  extractor only knew the parenthesised `(1)` form, so 183 rows across 18
  manual sections were read as top-level fields of the request.

  `/db/BTMP` is the clearest case: `TYPE`, `VAL_B`, `VAL_H1`, `VAL_H2`,
  `VAL_T1`, `VAL_T2`, `ELAST`, `THERMAL`, `OPT_B`, `OPT_H1` and `OPT_H2` were
  declared at the top level of the payload. The section's own Request Example
  sends them inside `ITEMS[].vSECTTMP[]`, three levels down. A caller
  following the published type put them where the server does not look.

  `/db/SWIND` lost a field outright: `TOPOGRAPHIC_EFFECT` and `FORCE_COEF`
  both document their own `OPT_USE`, and flattened to the root the second
  overwrote the first. Both are now declared, each inside its own object,
  along with the thirteen `VIBRATION_PARAMS` members.

  If you were constructing one of these payloads against the old shape, the
  members move rather than disappear — the compiler will point at each one.

### Changed


- **Four Hyper-S payload types come from a contract instead of a Python
  `TypedDict`.** `MaterialHyperSPayload`, `PlasticMaterialHyperSPayload`,
  `InelasticFiberMaterialLinkHyperSPayload` and
  `InelasticHingePropertyHyperSPayload` now inline their members and carry the
  server's own field descriptions as doc comments, which they had none of
  before. The named interfaces they used to reference
  (`MaterialHyperSParam`, `PlasticMaterialHyperSMasonry`,
  `InelasticFiberMaterialLinkHyperSConcrete` and the rest) are still exported
  and unchanged; the payloads no longer point at them.

  Their manual sections state no request at all — a URL, a methods line and a
  link — so these four are the first contracts sourced from live
  `GET /info/db/...` introspection rather than the manual. Every member is
  optional, because `/info` declares no `required` array and `optional` would
  be a claim nobody has made.

- **Fifteen resource labels take the manual's en dash.** `db.*.name` for the
  six `LCOM-*` load combinations, the five `SD*` seismic devices,
  `/db/MVCTch`, `/db/RPSC`, `/db/SECF` and `/db/TDMT` read
  `"Load Combinations – General"` rather than `"Load Combinations - General"`
  and so on. The npm package had been publishing the en dash for thirteen of
  them while the Python package published a hyphen; both now read what their
  manual section reads.

- **Three more endpoints are contract-driven**: `/db/HHCT`, `/db/SECF` and
  `/db/TDMT`. `/db/TDMT` and `/db/SECF` had been held back by a review gate
  quoting findings that were retracted on 2026-07-27, when the vendor report's
  claims were re-checked against MIDASIT's own articles.

- **Two resource labels follow their manual sections.**
  `db.properties.material.inelasticFiberMaterialLinkHyperS.name` is now
  `"Inelastic Material Link for Auto Generation (Hyper-S)"` and
  `db.properties.hinge.inelasticHingePropertyHyperSBeam.name`
  `"Assign Inelastic Hinges - Beam (Hyper-S)"`. Both had been derived from
  their parent endpoint's label; the first named a different feature, since
  `/db/IMFM-M1` is a material link and `/db/IMFM` is fiber-model properties.

## 2.7.5 - 2026-09-02

### Compatibility — breaking

- **`SectionBoundaryDataPayload.AXIS_VECTOR` is `Array<number>`, not
  `number`.** `/db/SBDO`'s Specifications table types it `Number`; the same
  section's JSON Schema types it an array of numbers and its own Request
  Example sends `[0, 0, 0, 0, 0, 0]`. The contract followed the table and npm
  followed the contract, so the field's own documented value did not
  typecheck. Python has always had `List[float]`. Assigning a scalar now
  fails; send the vector.
- **Three KDS rebar payloads are contract-driven and require their members.**
  `RebarDesignCriteriaPayload` (`/DESIGN/RC/KDS-41-20-2022/DCRE`),
  `RebarDesignCriteriaByWallMemberPayload` (`DCRM-WALL`) and
  `ModifyColumnRebarDataPayload` (`REBC`) now state the manual's requiredness,
  descriptions and enums - `SPLICED_BARS` (`"None" | "50%" | "100%"`),
  `MATERIAL` (nine grades), `END_REBAR_METHOD` (`1`-`4`), `HOOP_TYPE`,
  `HOOK_TYPE`. Their member shapes are inline, so `DcreBeamCriteria`,
  `DcreColumnBraceCriteria`, `DcreWallCriteria`,
  `RebarDesignCriteriaByWallMemberItem` and `RcColumnRebarItem` are still
  exported but no longer what the payload refers to. Rebar *size* fields stay
  plain `string`: chapter 26 says in each section that it prints only the first
  5 of 19, so there is no enum to publish.
- **Two resource labels follow the manual.**
  `rebarDesignCriteria.name` is `"Design Criteria for Rebar"` and
  `rebarDesignCriteriaByWallMember.name` is
  `"Design Criteria for Rebars by Wall Member"`, matching their manual sections
  and their three `DCRM-*` siblings, which already read that way. The Python
  classes' `NAME` changed with them.
- **`MaterialPayload` requires `TYPE`, `NAME` and `PARAM`.** `/db/MATL` is now
  contracted, and its manual states all three Required. `PARAM` is also
  `Array<...>`, not `Array<MaterialParam>`: the Specifications table types it
  `Object` while the same section's JSON Schema says `array` and every Request
  Example in the section sends `[{...}]`. Each entry now carries the manual's
  own descriptions and, in its doc comment, which `P_TYPE` requires it.
- **`SectionReinforcementPayload` requires its five members.**
  `OPT_MBAR_J`, `OPT_SBAR_J`, `OPT_CRACKED`, `SBAR_ITEMS` and `MBAR_ITEMS`
  are required, as `/db/RPSC`'s table states, and the two item arrays now
  carry their fields inline with the manual's descriptions and its
  requiredness (`IJ`, `NAME`, `REF_Y`, `REF_Z`, `NUM` are required within
  `MBAR_ITEMS`). The exported `SectionReinforcementShearItem` and
  `SectionReinforcementLongitudinalItem` interfaces are unchanged and still
  exported, but the payload no longer refers to them, so a value annotated
  with one of those names no longer widens to the payload's member type.

### Changed

- `sectionReinforcement.name` is `"Section Manager – Reinforcements"`, the
  manual's own section label, where it was `"Section Manager - Reinforcements"`
  before. `/db/RPSC` is now contracted, and a contract's `surface` block owns
  what npm publishes; the hyphen came from the Python class the resource used
  to be described by.

### Fixed

- Five documented fields were missing from the generated declarations:
  `SPLICED_BARS` on `RebarDesignCriteriaBy{Beam,Column,Brace}MemberPayload`
  (`"None" | "50%" | "100%"`, default `"50%"`) and `FRAMEX`/`FRAMEY` on
  `SrcDefinitionOfFramePayload`. The manual documents each of them in a
  Specifications row whose Description cell writes alternatives with GFM's
  escaped pipe (`None \| 50% \| 100%`); the contract extractor split those
  rows on every `|`, got more cells than the header has, and dropped the row.
  All five are optional, so nothing that compiled before stops compiling.
- **49 fields the manual requires only inside one branch are optional again.**
  A `requirement: required` carrying an `appliesWhen` is a branch's
  requirement, not the payload's, and typing it unconditionally required made
  `ConvectionCoefficientFunctionPayload` demand `COEF` (only under
  `TYPE: "CONST"`) together with `SCALE_FACTOR` and `ITEM` (only under
  `TYPE: "USER"`) - no caller could satisfy the type without sending fields
  their own branch does not have, and `InelasticMaterialPropertyPayload` asked
  for all six plasticity models at once. The condition moved into the doc
  comment (`Required when TYPE = "CONST".`). Nothing that constructed a payload
  before stops compiling; code that *reads* one of these fields may now need a
  guard under `strictNullChecks`. Affects `/db/CCFC`, `/db/EPMT`, `/db/ETFC`,
  `/db/HSFC`, `/db/MVLDid`, `/db/NLNK`, `/db/THFC` and `/ope/GSBG`.
- `/db/RPSC`'s two reinforcement item arrays no longer nest each item's
  fields under the first one. The manual numbers those supplementary tables
  `(1)`-`(n)` with no parent row of their own, and the extractor read the
  first row as the parent of its own siblings: `OPT_DR`, a boolean, held the
  twenty fields after it. The section's Request Example writes them side by
  side. `/db/MATL` and `/db/RCHK` had the same shape and are not yet
  contracted.

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
