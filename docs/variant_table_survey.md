# Variant-table promotion survey

## Scope and method

This is an investigation only.  It does not change the contract schema, promote
a draft, or select an implementation direction.

Baseline: `python scripts/promote_contract.py --all --dry-run` on 2026-08-29
refused **45** draft IDs with `the section has conditional variant tables nobody
has merged`.  The count is the gate population, not the 68-section
`multi-table` headline from the extractor report: sections already recognised as
the current one-level `variants` shape are not in this refusal set.

For every one of the 45, the source used below was the named section in
`E:\AI Study\MIDAS-API\docs\manual\*.md`.  No Python or TypeScript SDK source
was used to decide field membership, a discriminator, or a value.  “Unstated”
means the manual does not provide the missing literal; it is not a request to
infer it from an SDK.

## Result

| Classification | Endpoints | Meaning for a future contract |
| --- | ---: | --- |
| A. Payload is selected by one or more documented field values | 27 | It needs conditional/variant representation.  Some are an exclusive union; many have independent or nested gates and are not a single `oneOf`. |
| B. Tables are a structural split, not a payload discriminator | 18 | Merge the tables into the named object/array properties, or into one ordinary field list after manual review. |
| C. Tables for different HTTP operations are adjacent | 0 | No member of this 45-item gate population has this shape. |

The current gate treats all additional tables alike.  It therefore blocks both
the 27 conditional payloads and the 18 structural splits.  The latter are not a
schema-design question in the same sense as the former.

### A. Documented conditional payloads (27)

`Depth` counts selector levels, not ordinary JSON-object nesting.  “Independent”
means more than one selector may apply to the same payload, so generating one
flat discriminated union would be incorrect.  Counts marked “partial” or
“unstated” are deliberately not made exhaustive.

| Endpoint | Manual evidence | Discriminator values and nesting |
| --- | --- | --- |
| `/db/CCFC` | `10_DB_Construction_Stage.md:871-886`, `TYPE="CONST"` / `TYPE="USER"` tables | `TYPE`: 2 (`CONST`, `USER`); depth 1, exclusive. |
| `/db/ELEM` | `03_DB_Node_Element.md:201-290` | `TYPE`: 10 (`BEAM`, `TRUSS`, `TENSTR`, `COMPTR`, `PLATE`, `WALL`, `PLSTRS`, `PLSTRN`, `AXISYM`, `SOLID`).  `STYPE` then selects 3 `TENSTR`, 2 `COMPTR`, 2 `WALL`, 4 `PLATE`, or 2 `PLSTRS` subtypes; depth 2. |
| `/db/EPMT` | `04_DB_Properties.md:898-965` | `MODEL_TYPE`: 6 (`TR`, `VM`, `MC`, `DP`, `MA`, `DM`) selects one named model object.  Within the two hardening-object families, `OPT_HARDENING` has 2 values and `HARDENING_TYPE` has 3; depth 2. |
| `/db/ETFC` | `10_DB_Construction_Stage.md:759-782` | `TYPE`: 3 (`CONST`, `SINE`, `USER`); depth 1, exclusive. |
| `/db/FBLA` | `06_DB_Static_Loads.md:1241-1255` | `FLOOR_DIST_TYPE`: 4 documented values.  Extra fields are stated for `1`, `2`, and the shared `1 or 2` case; depth 1.  The manual does not state extra fields for `3`/`4`. |
| `/db/FIMP` | `04_DB_Properties.md:2093-2113` | `MATL_TYPE` has 2 values (`CONC`, `STEEL`), and `HYS_MODEL="KPM"` selects the detailed Kent & Park object.  The manual explicitly says other models exist but does not enumerate their complete field sets; depth 2, incomplete. |
| `/db/HSFC` | `10_DB_Construction_Stage.md:1136-1169` | `TYPE`: 3 (`CONST`, `FUNC`, `USER`).  In the `FUNC` branch, `OPT_USE_CONC_DATA`: 2 (`false`, `true`); depth 2. |
| `/db/IMPF` | `08_DB_Moving_Loads.md:2753-2784` | Item-level `FACT_TYPE`: 3 documented literals (`IMPACT_FACT`, `EFF_SPAN_LEN_USER`, `EFF_SPAN_LEN_AUTO`); the auto branch requires `LANE_TYPE="LINE"` and then `ELEMTYPE` has 3 (`BEAM`, `TRUSS`, `PLATE`) affecting `PARTS`.  Depth 3. |
| `/db/MVLD` | `08_DB_Moving_Loads.md:1420-1508` | `TYPE`: 3 (`0` General, `1` Permit, `2` Optimization).  General-load tables additionally vary by national code, but the manual headings do not name a wire field that selects Korea/Australia/Russia; that second discriminator is **unstated**. |
| `/db/MVLDbs` | `08_DB_Moving_Loads.md:1845-1883` | `LOADMODEL`: 4 (`STANDER`, `SPECAIL`, `ALL_MODE_1`, `ALL_MODE_2`) and `bAUTOOPTIMIZE`: boolean.  They select different `LCDATA_*` objects; independent/cross-product, depth 2. |
| `/db/MVLDid` | `08_DB_Moving_Loads.md:1728-1747` | Independent booleans `OPT_AUTO_LL=true` and `OPT_LC_FOR_PERMIT_LOAD=true` add different fields; depth 1.  These are additive conditions, not mutually exclusive variants. |
| `/db/MVLDpl` | `08_DB_Moving_Loads.md:2171-2210` | `LOAD_MODEL`: 3 (`1`, `2`, `3`) combines with `bAUTO_OPTIMIZE` and `bPERMIT_LOAD`.  General, optimization, and permit objects use different fields; multiple selectors, depth 2. |
| `/db/NLCT-M1` | `12_DB_Analysis_Control.md:1848-1875` | Top-level `LC_SCOPE`: 2 and `ITER_METHOD`: 3 (`FORCE`, `ARC`, `DISP`).  Inside `LOAD_STEPS`, `STEP_MODE`: 2 and the parent iteration method changes its fields; depth 2. |
| `/db/NLNK` | `05_DB_Boundary.md:791-802` | `REF_SYSTEM`: 2 (`0`, `1`); when `1`, `INPUT_METHOD`: 3 (`0`, `1`, `2`); depth 2. |
| `/db/NSPR` | `05_DB_Boundary.md:162-196` | `ITEMS[].TYPE`: 4 (`LINEAR`, `COMP`, `TENS`, `MULTI`); independent `FormType`: 2, and `DIR=6` adds `DV` within two type branches; depth 2. |
| `/db/PNLA` | `06_DB_Static_Loads.md:1080-1100` | Independent `ELEM_TYPE`: 2 (`PLATE`, `SOLID`) and `SELECT_TYPE`: 2 (`ON_PLANE`, `IN_GROUP`); depth 1. |
| `/db/SECT` | `04_DB_Properties.md:1030-1041`, `1107-1260` | `SECTTYPE`: 8 documented values (`DBUSER`, `VALUE`, `SRC`, `COMBINED`, `PSC`, `TAPERED`, `COMPOSITE`, `SOD`).  `DBUSER.DATATYPE` has 2 values and further shapes live in named nested objects; depth at least 2. |
| `/db/SPFC` | `09_DB_Dynamic_Loads.md:101-508` | `STR.SPEC_CODE` has 47 listed literals across Korea (7), US (6), Eurocode (3), China (9), Japan (4), Taiwan (7), India (3), and Other Countries (8).  User type is selected by the absence of that object/value, not a literal discriminator.  Further code-specific selectors exist (for example India `iSEISZONE=4`); depth at least 2. |
| `/db/SPLC` | `09_DB_Dynamic_Loads.md:643-696` | `bDAMP` gates damping; `iMDTYPE`: 3 then `iCOEF`: 2 in the Mass & Stiffness branch.  `bACCECC` and `bNDP` independently add GEN-only groups; depth 3. |
| `/db/STCT` | `12_DB_Analysis_Control.md:2036-2133` | Independent `iINC_NLA`: 3 (`0`, `1`, `2`) and `iNLA_TYPE`: 2 (`0`, `1`), plus boolean gates such as `bCONV`, `ITD="GROUP"`, and `bLFFC=true`; depth 1 for the main split, deeper for field conditions. |
| `/db/SWIND` | `06_DB_Static_Loads.md:1732-1800`, `1858-...` | `WIND_CODE` distinguishes documented KDS and `USER TYPE`; within KDS `PARAMETERS.INPUT_METHOD`: 3 (`0`, `1`, `2`), and nested `OPT_USE=true` gates fields.  Depth 3. |
| `/db/TDNA` | `07_DB_Temperature_Prestress.md:823-929` | `SHAPE`: 3 (`ELEMENT`, `STRAIGHT`, `CURVE`) selects extra parameter tables.  The manual's repeated `파라미터` headings do not identify every intermediate object path; depth/value path needs transcription, not inference. |
| `/db/THFC` | `09_DB_Dynamic_Loads.md:1968-1994` | `FUNCTYPE`: 2 (`1` Time Function, `2` Sinusoidal); in Time Function `iMETHOD`: 2 (`0`, `1`); depth 2. |
| `/db/THIK` | `04_DB_Properties.md:1388-1409` | `TYPE`: 2 (`VALUE`, `STIFFENED`); `STIFFENED.STYPE`: 3 (`VALUE`, `USER`, `DB`); `bINOUT=true` also affects `T_OUT`; depth 2. |
| `/db/THIS-M1` | `09_DB_Dynamic_Loads.md:1765-1810` | Nested `COEF_INPUT`: 2 (`0`, `1`) in the M&S damping branch and `INC_METHOD`: 2 (`0`, `1`) in the static branch.  Their parents (`DAMPING_METHOD` and `ANAL_CASE.ANAL_METHOD`) are stated in prose/tables; depth at least 2. |
| `/db/THIS` | `09_DB_Dynamic_Loads.md:1288-1479` | `COMMON.iATYPE` (2) × `COMMON.iAMETHOD` (3) yields 5 documented supported combinations (Linear+Modal, Linear+Direct, Nonlinear+Modal, Nonlinear+Direct, Nonlinear+Static).  Nested `iINCCTRL`: 2; `iMDTYPE`: 3 then `iCOEF`: 2.  Depth at least 3. |
| `/ope/GSBG` | `17_DB_Bridge.md:607-630` | Independent `BATCH`: 2 and `DGRM_TYPE`: 2; within the stress branch, `STRESS_LINE.OPT_USE`: 2.  Depth 2. |

The word “discriminated” here means *the manual says a value changes the field
set*.  It does **not** imply each row can be made a TypeScript `oneOf`: `MVLDid`,
`MVLDpl`, `SPLC`, `STCT`, and `GSBG` have independent gates, while `SPFC` has an
absence-based User branch and `MVLD` lacks a documented wire discriminator for
some national-code tables.

### B. Structural table splits (18)

These are not evidence for a payload union.  Their additional tables describe a
named nested object/array, a product partition, or a presentation-oriented
grouping.  They still need a human to verify the object path from the manual;
“merge” never means flattening child fields into the record root.

| Endpoint(s) | Manual evidence | Why it is a structural split |
| --- | --- | --- |
| `/db/ACTL-M1` | `12_DB_Analysis_Control.md:140-165`, `Parameters — TCELEM 객체` | The second and third tables are the one named `TCELEM` object, not choices of a root discriminator. |
| `/db/BCCT` | `12_DB_Analysis_Control.md:2598-2628`, `vBOUNDARY` / `vLOADANAL` | Both added tables are named list members of the same request. |
| `/db/GRDP` | `04_DB_Properties.md:2270-2304`, Strain Energy / Element Mass & Stiffness | Two independently configurable damping groups; the manual does not say one field value excludes the other. |
| `/db/IEHC` | `04_DB_Properties.md:1910-1947`, `GEN 전용 필드` | Product availability partition, not a wire-value discriminator. |
| `/db/IMFM` | `04_DB_Properties.md:275-290`, Concrete Material / Steel Material | Two named material-reference fields; neither table states a selector value. |
| `/db/MCON` | `05_DB_Boundary.md:1843-1874`, `ITEMS`, `NODE_KEY`/`COEFF`/`DOF`, `WEIGHT` | Array-item structure and alternative row layouts, without an explicit wire selector. |
| `/db/MVCTch` | `12_DB_Analysis_Control.md:1075-1166`, Impact Factor tables | One analysis-control record split into field groups; the headings do not state a selector. |
| `/db/POGD` | `14_DB_Pushover.md:147-230` | Parameter groups accompany a single object-shaped control record; no table heading gives a discriminator. |
| `/db/RCHK` | `24_DB_Design.md:386-455` | `vMAIN`, `vLAYER`, `LAYER`, and `POSITION` are nested collection/detail tables, not branch alternatives. |
| `/db/RPSC` | `04_DB_Properties.md:1635-1690`, `SBAR_ITEMS[]` / `MBAR_ITEMS[]` | The latter two tables are array-item schemas for named fields. |
| `/db/SBDO` | `03_DB_Node_Element.md:844-875`, Civil NX Only / GEN NX Only | Product-specific field partition, not a value selected in the payload. |
| `/db/WVLD` | `11_DB_Settlement_Misc_Loads.md:357-474`, `COEF`, `CHAR`, `PROF` | Named nested objects and array-element tables. |
| `/DESIGN/RC/KDS-41-20-2022/DCRE` | `26_Design_RC_KDS41202022.md:5865-5930` | `BEAM`, `COLUMN`, `BRACE`, and `WALL` object trees are components of the one global settings payload. |
| `/DESIGN/RC/KDS-41-20-2022/DCRM-WALL` | `26_Design_RC_KDS41202022.md:5524-5548` | `Assign.{wallId}.ITEMS[]` plus its item schema. |
| `/DESIGN/RC/KDS-41-20-2022/REBB` | `26_Design_RC_KDS41202022.md:6370-6409` | Top-level `ITEMS[]` item data and the separate move/group fields. |
| `/DESIGN/RC/KDS-41-20-2022/REBC` | `26_Design_RC_KDS41202022.md:6640-6685` | Named bar/tie item substructures, not type-selected records. |
| `/DESIGN/RC/KDS-41-20-2022/REBR` | `26_Design_RC_KDS41202022.md:7112-7154` | Named reinforcement item substructures, not type-selected records. |
| `/view/DISPLAY` | `16_VIEW.md:827-1002`, seven optional `Argument.*` groups | The manual explicitly says callers select which optional display-group objects to send; the groups may coexist. |

### C. Different-operation tables (0)

There is no `/db/*`, `/DESIGN/*`, `/ope/*`, or `/view/*` member in this 45-item
population whose extracted additional table sits under a GET-, POST-, PUT-, or
DELETE-specific parameter heading.  Each of the 45 places its parsed tables in
one parameter/specification section; method-specific material is request/response
JSON examples, not a second parameter table.  Thus this category must exist in
the future classifier, but it is not a remediation path for any of these 45.

## Contract-schema choices (no choice made)

The current schema has a useful but deliberately narrow `variants` array:
one top-level `field = literal` condition per manual table.  It can express the
existing `/db/EIGV` case, but it cannot faithfully express an object-path
selector, an absence branch, multiple independent gates, or a nested variant.
The following are alternatives for an author decision.

### Option 1 — recursive, typed payload cases

Replace or supersede the current one-level `variants` with a recursively
composable payload-case node.  A node can be a `oneOf` only where its branches
are exclusive, or an `allOf` of independent conditional field groups.

Illustrative YAML for the manual's `/db/CCFC` tables (not valid under the current
schema and **not proposed as an edit in this survey**):

```yaml
payloadCases:
  kind: oneOf
  discriminator: { path: TYPE }
  cases:
    - equals: CONST
      source: { table: "Constant 타입 (TYPE=\"CONST\") 추가 파라미터", line: 873 }
      fields:
        - { key: COEF, type: number, requirement: required, provenance: manual }
    - equals: USER
      source: { table: "User 타입 (TYPE=\"USER\") 추가 파라미터", line: 879 }
      fields:
        - key: ITEM
          type: array
          requirement: required
          properties:
            - { key: TIME, type: number, requirement: required, provenance: manual }
            - { key: VALUE, type: number, requirement: required, provenance: manual }
          provenance: manual
```

The npm generator can emit a real discriminated union for an exclusive node:

```ts
type CcfcPayload = CcfcBase & (
  | { TYPE: "CONST"; COEF: number }
  | { TYPE: "USER"; SCALE_FACTOR: number; ITEM: Array<{ TIME: number; VALUE: number }> }
);
```

Python can expose the same static shape with separate `TypedDict` definitions
and `CcfcPayload: TypeAlias = CcfcConst | CcfcUser`; runtime request validation
would remain a separate product decision.

The cost is schema and generator complexity.  It still needs a second construct
for `GSBG`/`SPLC`-style independent gates, and it must reject incomplete or
absence-selected cases rather than manufacturing a union.  It is best for a
small, fully enumerated set such as CCFC or ETFC, not automatically for all 27.

### Option 2 — ordinary fields plus structured applicability

Keep one payload shape.  Add a structured `appliesWhen` to fields (including
nested fields) and retain `requirement: conditional` for the manual's
requiredness claim.  Multiple conditions mean logical AND; separate field groups
can coexist.

Illustrative YAML for `/ope/GSBG` (also only a design sketch):

```yaml
fields:
  - { key: BATCH, type: boolean, requirement: optional, provenance: manual }
  - key: BATCH_LIST
    type: array
    items: { type: string }
    requirement: conditional
    appliesWhen: [{ path: BATCH, equals: true }]
    provenance: manual
  - key: BRDG_GROUP
    type: string
    requirement: conditional
    appliesWhen: [{ path: BATCH, equals: false }]
    provenance: manual
  - key: STRESS_LINE
    type: object
    requirement: optional
    appliesWhen: [{ path: DGRM_TYPE, equals: 0 }]
    provenance: manual
```

The npm result is one interface with conditional members optional at the type
level, for example `BATCH_LIST?: string[]; BRDG_GROUP?: string`.  Python is one
`TypedDict(total=False)` (or `NotRequired[...]` fields) with the structured
condition preserved in generated documentation.  Both languages can show the
condition in JSDoc/docstrings.

This handles every independent and nested gate without a combinatorial union,
and it cleanly represents manual facts that are incomplete.  Its drawback is
weaker caller guidance: TypeScript and Python cannot prevent `BATCH_LIST` and
`BRDG_GROUP` being supplied together without extra runtime validation, and a
branch-required field appears optional to a static checker.

### Option 3 — retain a lossless conditional-schema subset

Add an explicit `payloadSchema` whose nodes are a restricted, source-attributed
subset of JSON Schema (`properties`, `required`, `allOf`, `oneOf`, literal
`const`/`enum`, and `if`/`then`).  It preserves complex manual conditions instead
of translating them prematurely.

Illustrative YAML for the documented `/db/NLNK` nesting:

```yaml
payloadSchema:
  allOf:
    - if: { path: REF_SYSTEM, const: 1 }
      then:
        required: [INPUT_METHOD]
        allOf:
          - if: { path: INPUT_METHOD, const: 0 }
            then: { required: [ANGLE_VALUES] }
          - if: { path: INPUT_METHOD, const: 1 }
            then: { required: [POINT_VALUES] }
          - if: { path: INPUT_METHOD, const: 2 }
            then: { required: [VECTOR_VALUES] }
  source:
    chapterFile: 05_DB_Boundary.md
    lines: [791, 802]
```

The npm generator can lower a fully literal, exclusive subtree to a
discriminated union and lower all other subtrees to optional properties with
JSDoc.  Python can use `TypedDict`/`TypeAlias` for the former and a normal
`TypedDict` for the latter; neither requires runtime validation merely because a
schema exists.

This is the most faithful option for `/db/THIS`, `/db/SPFC`, and nested object
conditions.  Its costs are duplication risk between the existing field list and
the new schema, substantially more validator/generator work, and a need to
specify exactly which JSON-Schema features are permitted.  A verbatim arbitrary
JSON Schema would be too broad to generate safely.

## Decision points before implementation

1. Decide whether the contract should optimise for exact static unions (Option
   1), complete documentation of applicability (Option 2), or lossless
   conditional source representation (Option 3).
2. Decide whether incomplete manual variants (`FIMP`, the national-code portion
   of `MVLD`, and the absence branch in `SPFC`) are contractable at all before
   live `/info` or manual evidence fills the gap.  They should remain
   `unverified`/unpromoted rather than receive invented branches.
3. Independently of that decision, the 18 structural rows can be reviewed as
   object/array-path transcriptions.  They do not require a variant feature,
   but they must not be bulk-flattened.
4. Make the promotion gate classify these categories before allowing any bulk
   promotion; do not simply waive `unmergedTables`.

No schema representation is selected by this document.
