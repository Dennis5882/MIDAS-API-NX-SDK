# Manual defects register

A running record of places where `E:\AI Study\MIDAS-API` (or the MIDASIT
official article it transcribes) disagrees with what the product actually does.

**This file collects; it does not act.** Nothing here has been applied to the
manual repository, sent to MIDASIT, or filed in Jira. Those are the author's
calls. Do not edit the manual repo from this repository, and do not open a Jira
issue about any of these without an explicit go-ahead.

**How to add an entry.** When live evidence contradicts the manual, append a row
here in the same commit that records the evidence in
`docs/live_verification_notes.md`. Give it the next `MD-nn` id, and say which
side owns the correction — the manual repo can rewrite its own transcription,
but only MIDASIT can fix its own article. If the disagreement also affects a
contract, the manual's claim goes under `manualDefects` and the product's
behaviour under `contracts/verification/`, separately, as
`contracts/README.md` requires.

Session baseline for every 2026-08-31 entry: MIDAS Gen NX 2026 v2.1 and MIDAS
Civil NX 2026 v2.2, both build 08/26/2026.

The 2026-09-03 entries (MD-14 through MD-17) were found on the build that
preceded the 09/02/2026 patch, which was installed part-way through that same
day. The build they ran on is not recorded, because the API does not report one
and nobody read the About dialog before the patch went on - see
docs/live_verification_notes.md. A GET-only sweep from each SDK immediately
after the patch (282 of 282 on Civil NX v2.2, 267 of 267 on Gen NX v2.1, both
build 09/02/2026) found no route changed, so nothing in these entries is
known to be patch-specific.

## Register

| id | found | endpoint / topic | manual says | product does | correction owned by | status |
| --- | --- | --- | --- | --- | --- | --- |
| MD-01 | 2026-08-30 | `/db/STYP-M1` `DELETE` | `02_DB_Project_Structure.md` declares GET, PUT, DELETE in three places | all three DELETE forms refused on both products, from a non-default state with a model open | **MIDASIT article** (`activeMethods`); the manual repo repeats it | open |
| MD-02 | 2026-08-30 | `/db/POLC-M1` POST | the `14_DB_Pushover.md` ⚠️ callout says POST is not served and the article's row is an untrimmed template | POST created a record that the next GET returned | **manual repo** (its own callout) | open |
| MD-03 | 2026-08-31 | `/db/MATL-M1` structure | `04_DB_Properties.md:239` — same base material structure as `/db/MATL`, plus Hyperelastic support | different top-level names (`MATL_NAME`/`MATL_TYPE`), four fields against `/db/MATL`'s nine, and the `HE_*` fields are on the parent instead | **MIDASIT article** note | open |
| MD-04 | 2026-08-31 | `/db/IEHC` `WAreaSize` | the Specifications table types it Integer | Gen `/info` types it `string`; the chapter's own Request Example sends `"AUTO"` | **manual repo** transcription | open |
| MD-05 | 2026-08-31 | model file extensions | the manual's examples still show pre-NX spellings | four extensions in two pairs: pre-NX `.mgb`/`.mcb`, NX `.mgbx`/`.mcbz`. Civil NX's own Export menu lists "MCBZ File" | **manual repo** | open |
| MD-06 | 2026-08-31 | `/db/ELEM` `TYPE: "WALL"` on Civil | `03_DB_Node_Element.md` supplies a WALL-element request example for the shared Node/Element chapter | Gen accepted the manual-shaped WALL element; Civil NX v2.2 (08/26/2026) returned the quoted unsupported-type error below | **MIDASIT product/article** (support scope must be clarified) | open |
| MD-07 | 2026-09-01 | `/db/FIMP` Kent & Park table | `04_DB_Properties.md:2103` keys the rows `"KENPAR"."FC"` and omits `CONC`/`STEEL` from Specifications entirely | the same article's Request Body nests them `CONC` > `KENPAR` > `FC`, three levels deep | **manual repo** transcription | open |
| MD-08 | 2026-09-01 | `/db/CO_S`, `/db/CO_T` Specifications | one row keyed `"W_R" ~ "HE_B"` for No. `1-9` | the same section's JSON Schema and Request Example both list nine separate colour components, as `/db/CO_M`'s table does individually | **manual repo** transcription | open |
| MD-09 | 2026-09-01 | `/DESIGN/RC/.../DCRM-*`, `/DESIGN/SRC/AIK-SRC2K/LLRF` | the JSON Schema `enum` lists 5 rebar sizes and 6 reduction factors | the same rows' descriptions say `19종 (D4 ~ D57)` and `가능값 11개`; LLRF's list carries the literal member `...(전체 11개)` | **manual repo** transcription | open |
| MD-10 | 2026-09-01 | four sections' Specifications tables | the table omits a root property the same section's JSON Schema declares | `/db/EPMT` (6 model objects) and `/db/ELEM` (`C_RAT`, `LCAXIS`) reconciled 2026-09-02; `/db/FIMP` and `/db/RCHK` still drafts. Five more turned out to be this SDK's parser, not the manual - see the detail | **manual repo** transcription (4 of the original 9) | 2 reconciled, 2 open |
| MD-11 | 2026-09-02 | nine parameter rows' Value Type | the Specifications table's Value Type cell | the same section's own JSON Schema types the property differently. Seven are integer/number width; two change the shape of the value - `/db/SBDO` `AXIS_VECTOR` (Number vs an array of numbers, and its own Request Example sends six) and `/db/MATL` `PARAM` (Object vs array) | **manual repo** transcription | `/db/SBDO` and `/db/MATL` corrected in their contracts; 7 open |
| MD-12 | 2026-09-02 | seven Hyper-S `-M1` sections, and the `/info` schema that substitutes for them | the section gives a URL, a methods line and a Zendesk link - no Specifications table and no JSON Schema, so live `/info` is the only permitted contract source | `/info` serves a full schema for four of them and 404s for three, and the schemas it serves are malformed twice over: every apostrophe in a `description` is escaped `\'`, which is not a JSON escape, and `maxItems` is stated on an array's `items` subschema instead of the array | **MIDASIT product** (`/info` output) and **MIDASIT article** (the missing section content) | open |
| MD-13 | 2026-09-02 | `/db/TDME` `"SCALE"` | the Specifications table gives the key `"SCALE"` to two different rows - "Scale Factor" (Number) and "Function Data" (Array[Object] of `{TIME, COMP, TENS, ELAST}`) | unknown; the section has no Request Example that sends either, so which row owns the name cannot be read from the chapter. The vendored manual flags this itself in a ⚠️ callout and transcribes both verbatim | **MIDASIT article** (the duplicate is in the source) | **answered 2026-09-02**: `/info` names the array `aDATA`; row 6's key is wrong |
| MD-14 | 2026-09-03 | `/db/TDME` `CODENAME` `Japan(hydration)` / `Japan(elastic)` | `04_DB_Properties.md` lists both in its `CODENAME` code table (entries 16 and 17), each with its own table of required extra fields, and marks neither as belonging to a different product | both answer `Wrong Field` on Gen NX and Civil NX - **correctly**: these two codes are iGen's, and the NX API is not talking to iGen | **manual repo** - the code table needs to say which entries are not available through this API | open |
| MD-15 | 2026-09-03 | `Create Only`, in `/db/SECT` and `/db/SPFC` | the manual's only two `Create Only` cells, both a `CALC_OPT`, say the server honours the field on create and ignores it on modify | true of `/db/SECT` exactly; false of `/db/SPFC`, where `CALC_OPT: true` on a PUT rebuilds the spectrum. Separately, `/db/SPFC`'s KDS(41-17-00:2019) worked example is refused as printed - it omits `CALC_OPT` and supplies no `aFUNC` | **MIDASIT article** (one value used for two contracts, and an example that cannot run) | open |
| MD-16 | 2026-09-03 | `/db/MVHL` common Specifications table | `VEHICLE_TYPE_NAME` and `STANDARD_CODE` Required, `USER_LOAD_TYPE` Optional, with no reference to the branch | `VEHICLE_LOAD_NUM` selects the branch: `1` needs the type name, `2` needs neither it nor `STANDARD_CODE`, which is not required under either. `USER_LOAD_TYPE` is ignored on input. The chapter's own KSCE-LSD15 examples show the branch; the table that claims to cover every code does not mention it | **MIDASIT article** (the table), which the manual repo transcribes faithfully | open |


## Detail

### MD-01 — `/db/STYP-M1` DELETE

The manual names DELETE in its endpoint methods and other chapter locations.
Live checks against both products refused the bare DELETE body forms and the
per-id route while a real model was open. This is a product-capability finding,
not a request-wrapper inference. Keep the endpoint's documented GET/PUT facts
separate from the disproven DELETE claim.

Recorded in the SDK as a `manualDefects` entry with `describes: method`;
`StructureTypeHyperS` keeps `_GET_PUT_ONLY`.

### MD-02 — `/db/POLC-M1` POST

The manual-repo warning is more restrictive than the product. A live POST
created a record and a following GET returned it. The proposed correction is
not to invent a payload schema: only to stop claiming that POST is absent.

No evidence establishes that the official article makes the same claim, so this
one is the manual repo's own to fix.

### MD-03 — `/db/MATL-M1` structure

The Hyper-S endpoint cannot safely inherit `/db/MATL`'s fields:

```text
/db/MATL     9 props: NAME, TYPE, PARAM, DAMP_RAT, HE_COND, HE_SPEC, PLMT, P_NAME, bMASS_DENS
/db/MATL-M1  4 props: MATL_NAME, MATL_TYPE, PARAM, DAMP_RAT
```

Beyond the different top-level names and count, `PARAM[].P_TYPE` is 0-based and
user-defined material values are nested under `USER_DEFINED`, whereas
`/db/MATL` uses a different, flatter parameter shape. The `HE_*` fields — the
ones that look like the Hyperelastic support the note claims is exclusive to
MATL-M1 — are on the parent and absent from MATL-M1.

The wording is therefore not a harmless abbreviation. It directs a reader to a
wrong wire contract, and copying the parent's fields would have produced a
contract whose every top-level name is wrong. This is the `/db/REBW` class of
defect: a section wrong about its own endpoint's field names.

### MD-04 — `/db/IEHC` `WAreaSize`

Recorded in the SDK as a `manualDefects` entry plus a Gen verification record.
The contract keeps the manual's `integer` rather than silently substituting the
live `string`, so a reader sees both claims and decides. Its sibling
`WAreaSizeCover` really is `integer` live, so this is one field, not the table.

### MD-05 — model file extensions

Four extensions, two pairs, and this repository got Civil's wrong twice before
landing on it — once as `.mcbx`, once over-corrected to `.mcb`:

| | Gen | Civil |
| --- | --- | --- |
| pre-NX | `.mgb` | `.mcb` |
| **NX** | **`.mgbx`** | **`.mcbz`** |

`/doc/STAGAS` is a real exception that wants the legacy `.mcb` and rejects
other spellings ("Please check the file name or extension"). Civil also
*tolerates* `.mcbx` for `SAVEAS` — a 2026-07 round trip wrote one and reopened
it with all 273 nodes — which is exactly why a wrong spelling survived a live
run without complaint. Being accepted is not being native.

The Export menus also differ by product in a way the manual does not state:
Civil NX offers MCT and an "MCBZ File"; Gen NX offers MGTX/MGT variants and no
MGBX. Both offer a product-named JSON export, which is `/doc/EXPORT`.

### MD-06 — `/db/ELEM` `TYPE: "WALL"` on Civil

The manual's element example uses `TYPE: "WALL"`, material 1, thickness/section
1, node order `[1, 2, 4, 3]`, `STYPE: 1`, `WALL: 1`, `W_CON: 0`, and
`W_TYPE: 0`. On a disposable rectangular model, Gen NX accepted that request.
Under the same shape and ids, Civil NX 2026 v2.2 build 08/26/2026 returned:

> `[Error] Unable to add/modify the element. The element type no. 5 for the element no. 4 is not supported.`

The manual's one-based type table says 5 is `PLATE` and 6 is `WALL`; that is
inconsistent with the server's displayed 5. A zero-based internal sequence
would label `WALL` as 5 and is therefore consistent with the message, while
the manual's displayed numbering is not. This is only a numbering observation,
not evidence deciding Civil's WALL-element support scope.

This is not a claim that a PLATE is semantically interchangeable with a WALL.
The separate `/db/WMAK` check merely established that its existing fixture
round-trips when its `WID_LIST` references an actual PLATE on both products.
No endpoint contract was changed: the evidence is insufficient to replace the
manual's element-type statement or to infer product-specific WMAK semantics.

### MD-07 - `/db/FIMP` Kent & Park parameter table

The Specifications table for the Kent & Park hysteresis model keys its rows
`"KENPAR"."FC"`, `"KENPAR"."PARTIAL_FACT"` and so on - a parent and a child,
with no row for the parent itself - while `CONC` and `STEEL` appear only in the
chapter's JSON Schema block and never in a Specifications table. The request
example in the same article shows the real shape:

```json
{"NAME": "Conc_Kent&Park", "MATL_TYPE": "CONC", "HYS_MODEL": "KPM",
 "CONC": {"KENPAR": {"FC": 30000, "PARTIAL_FACT": 1.0}}}
```

Read as a table of wire keys, the section therefore states a three-level object
as ten flat top-level fields. A contract drafted from it said exactly that, so
`/db/FIMP` is listed in `promote_contract.py`'s `NEEDS_HAND_REVIEW` and stays
on its reviewed Python fallback, whose `CONC`/`STEEL` objects are correct.

The chapter's own callout says this repository documents Kent & Park alone as
a representative of a 5,900-line article covering many concrete and steel
models. That is a deliberate, reasonable scope choice, and it is also why a
generated union over `HYS_MODEL` must never treat `"KPM"` as the only legal
value.

### MD-08 - `/db/CO_S` and `/db/CO_T` colour components

The Specifications table compresses nine keys into one row:

```text
| 1-9 | Wire Frame / Hidden Fill / Hidden Edge RGB (0-255) | `"W_R"` ~ `"HE_B"` | Integer |
```

Read as a list of literal keys that is two fields, and both SDKs published
exactly two: a caller could set the red component of the wire frame and the
blue of the hidden edge, and nothing else. The section's own JSON Schema names
all nine in order, its Request Example sends all nine, and the sibling
`/db/CO_M` lists them individually - three independent statements against the
one compressed row.

The extractor now expands an interval row only when the No. column's span and
the schema's property order agree on the count, which is transcription rather
than inference. Both contracts were re-promoted and the npm
`SectionColorPayload` carries eleven fields.

### MD-09 - sampled `enum` lists presented as complete

`26_Design_RC_KDS41202022.md:5076` declares

```json
"MAIN_REBAR": { "type": "string", "description": "주철근 규격 (전체 19종: D4 ~ D57)",
                "enum": ["D4", "D5", "D6", "D7", "D8"] }
```

The description and the enum contradict each other in the same object. Taken
as an enum it published `MAIN_REBAR: "D4" | "D5" | "D6" | "D7" | "D8"`, so an
npm caller could not name D10 or anything above it - the sizes real rebar
design uses. `/DESIGN/SRC/AIK-SRC2K/LLRF` is blunter still: its list carries
the literal member `...(전체 11개)`, which would have been a legal value.

Nine fields across four contracts were affected. A count or range the manual
states about its own list now disqualifies the list, and the field keeps its
declared scalar type, which is wide enough for every documented value.

### MD-10 - a Specifications table that is not the whole request

**Five of the original nine were this repository's parser, not the manual.**
The rows were there all along. `extract_contracts.py` split each table row on
every `|`, including GFM's escaped `\|`, which the manual uses to write
alternatives - ``None \| 50% \| 100%``. That gave the row more cells than its
header has, and a row whose cell count disagrees was discarded with no
diagnostic. Ten rows across three chapters were being deleted that way,
among them `/ope/LCOM-GEN`'s `CODE_SELECTION`, which the same section's JSON
Schema marks **required** and uses to select the whole request body.
`_split_row` now honours the escape, and the five contracts built from those
tables carry the recovered fields: `CODE_SELECTION`, `SPLICED_BARS` on the
three `DCRM-*` endpoints, and `FRAMEX`/`FRAMEY` on `DCTL`. Three further rows
(`HOOP_TYPE`, `HOOK_TYPE`, and a fourth `SPLICED_BARS`) belong to `REBC`,
`REBR` and `DCRE`, which are still drafts, so nothing promoted was missing
them.

That leaves **two promoted contracts and two drafts** genuinely built from a
table that omits a root its own JSON Schema declares. Both promoted ones are
now reconciled; both drafts are not.

| section | root(s) only the schema names | state |
| --- | --- | --- |
| `/db/EPMT` | `TRESCA`, `VMISES`, `MOHRCL`, `DRUCKER`, `MASONRY`, `CONCDMG` | **reconciled** 2026-09-02 |
| `/db/ELEM` | `C_RAT`, `LCAXIS` | **reconciled** 2026-09-02 |
| `/db/RCHK` (draft) | `BEAM`, `COLM` | open |
| `/db/FIMP` (draft) | `CONC`, `STEEL` | open - see MD-07 |

**`/db/EPMT` was the one the earlier note got wrong.** Its contract said the
six objects stayed unmerged because "the manual does not state a scalar wire
discriminator". It does: Specifications row 2 enumerates `MODEL_TYPE` as
`"TR"`/`"VM"`/`"MC"`/`"DP"`/`"MA"`/`"DM"` against the model each one selects,
and each sub-table heading names the object that model fills. All six are now
conditional `object` fields on `MODEL_TYPE`. Their *members* are still not
transcribed, and that is the honest reason: none of those sub-tables has a
Value Type column, so the manual gives no type for a single member, and the
`MASONRY` object's `BM`/`BED_JOINT`/`HEAD_JOINT`/`GEOM` structure is stated in
prose rather than as a table.

**`/db/ELEM`'s two are plain fields with nothing stated about them.** The
schema types and describes `C_RAT` (cable length ratio, number) and `LCAXIS`
(local axis, integer); no table in the section names either - not the common
keys and not any of the nine per-subtype tables, including the Cable table
`C_RAT` clearly belongs with. Both are declared with `requirement: unstated`,
which is the whole claim the manual supports.

**A second row-dropping class, found by the same measurement — open.** Once
escaped pipes stopped hiding it, counting every row in a keyed manual table
that produces no field leaves **20 rows whose cell count is one short of
their header**, because the row omits the leading No. cell. They are not one
kind of loss:

| section | rows | what is lost | state |
| --- | --- | --- | --- |
| `/db/POLC-M1` | 5 | **variant divider rows** (`INCRE_METHOD = "LOAD"인 경우`, ...) | promoted, 0 variants |
| `/db/ULFC` | 2 | **variant divider rows** (`등호(Equality) 조건 (EQ=true)`, ...) | promoted, 0 variants |
| `/ope/GUSTFACTOR` | 2 | **variant divider rows** (`STRUCTURE_TYPE = "RIGID"인 경우`) | draft |
| `/db/THIS-M1` | 11 | nested field rows prefixed `- ` (`MODE_NO`, `MAX_ITER`, ...) | draft |

No field is missing from the two promoted contracts - the rows under each
divider parsed normally. What is missing is the split: `/db/POLC-M1` and
`/db/ULFC` both carry 0 variants and 0 unmerged tables, so the npm generator
takes their flat field list as the payload and offers every branch's fields
at once - the same shape 2.7.3 and 2.7.4 corrected on six other endpoints.
`/db/THIS-M1` is the different case: eleven documented nested fields are
simply absent, and it is still a draft.

Fixing this needs a decision the escaped-pipe fix did not: a short row has to
be aligned to the header, and which column it omits is a judgment about the
table's shape rather than a mechanical un-escape. Left open deliberately.

`/db/RCHK` stays open for a structural reason rather than a judgment one: its
`BEAM` and `COLM` object headings are **bold prose**, not markdown headings,
so the parser reads their contents as free-floating tables and attaches them
to no root. Nothing is promoted from it, so nothing wrong has shipped. Its
`MEMBTYPE == "COLUMN"` / `"COLM"` object pairing is *not* a defect - the wire
value and the object key genuinely differ, and the manual states both.

Roots are the visible end of a wider pattern. Comparing every path, not just
the top level, **39 of the 337 promoted contracts and 22 of the 47 drafts**
have at least one path their section's JSON Schema declares and their table
never names. The extreme cases are whole subtrees: `/DESIGN/SRC/AIK-SRC2K/MRBD`
gives 14 of 54 paths, `/db/POGD` 9 of 73, `/view/RESULTGRAPHIC` 11 of 66.
That is measurement, not a verdict - a schema path can be a wrapper the
contract models elsewhere - but it is the number to start from. Only the root
case blocks promotion, because a missing top-level branch means the table is
not the request at all; MRBD is listed in `NEEDS_HAND_REVIEW` by name because
the tree-marker fix made it promotable while still a quarter complete.

`extract_contracts.py` now emits a review note for this, so no further contract
can be promoted from a table its own section contradicts. Reconciling the four
that remain needs someone to read each section and decide how the two
renderings relate - `/db/EPMT`'s six objects are `MODEL_TYPE` branches,
`/db/ELEM`'s two are plain optional fields, and they are not the same kind of
gap. The parser finding is the reason to check the tooling before the source:
over half of what looked like a documentation defect was this repo silently
dropping rows it could not count.

### MD-11 - a Value Type its own section's JSON Schema contradicts

A section states its request twice, and MD-08 through MD-10 are all cases
where one rendering is *less* than the other. These nine are different: the
two renderings state incompatible things about the same property, so neither
can be read as an abbreviation of the other.

| endpoint | path | table says | schema says |
| --- | --- | --- | --- |
| `/db/SBDO` | `AXIS_VECTOR` | Number | `array` of `number` |
| `/db/MATL` | `PARAM` | Object | `array` |
| `/ope/AUTOMESH` | `MESH_SIZE.LENGTH` | Number | `integer` |
| `/ope/AUTOMESH` | `MESH_SIZE.DIV` | Number | `integer` |
| `/db/RCHK` | `BEAM.vSUB_BAR.dSUB_BARNUM` | Integer | `number` |
| `/db/RCHK` | `COLM.vLAYER.vPOSITION.BAR_NUM` | Number | `integer` |
| `/db/RCHK` | `COLM.SUB_BAR.SUBBAR_NUM` | Integer | `number` |
| `/db/RCHK` | `COLM.SUB_BAR.SUBBAR_NUM_Y` | Integer | `number` |
| `/db/RCHK` | `COLM.SUB_BAR.SUBBAR_NUM_Z` | Integer | `number` |

Seven are numeric width, where either reading accepts the values the other
does and nothing a caller sends is refused by the difference. The two at the
top are not: a caller who believes the table sends a scalar where the server
wants a vector.

`/db/SBDO`'s reached users. The contract followed the table, the npm payload
followed the contract, and `SectionBoundaryDataPayload.AXIS_VECTOR` shipped
as `number` - a field whose own documented value, `[0, 0, 0, 0, 0, 0]`, does
not typecheck. Python was never wrong about it (`List[float]` since the
endpoint was added), which is the same asymmetry `/db/CO_S` had: one surface
read the schema, the other read the table, and only the contract could make
them answer the same question. Corrected 2026-09-02 with a `manualDefects`
entry; the npm type is now `Array<number>`, a breaking change for anyone
assigning a scalar.

`/db/MATL`'s reached users differently. `PARAM` was typed `Object`, which the
extractor's nesting then read as a container: read as one branch of the
request rather than of a `PARAM` entry, the three `#### PARAM - P_TYPE = n`
tables would have put `STANDARD`, `ELAST` and `ELAST_M` beside `TYPE` and
`NAME`, where no payload has ever carried them. Corrected 2026-09-02 with the
same kind of `manualDefects` entry, and the endpoint is contracted now.

`extract_contracts.py` attaches a review note wherever the two disagree, so no
further contract can be promoted from a Value Type its own section
contradicts. It deliberately transcribes neither side: choosing between them
took the Request Example and the Python SDK, and neither is a source the
extractor reads for types. The two resolutions above are transcribed in
`_MANUAL_TYPE_CORRECTIONS`, a closed list that also writes each one's
`manualDefects` entry into the contract - so a manual re-sync that reinstates
the table's claim has to argue with the record rather than silently win.

## Suggested follow-up, when the author chooses to act

1. Review each finding against the current online article and manual source.
2. Correct manual-repo-owned text (MD-02, MD-04, MD-05), preserving a visible
   note where the upstream article is contradictory.
3. Escalate MD-01, MD-03, and MD-06 to MIDASIT's documentation owner; those are
   official-source issues that the manual repo can only annotate.
4. After any upstream or manual correction, re-run
   `scripts/check_manual_drift.py` before moving `vendored_at_commit`.

### MD-12 - the only source these endpoints have is itself malformed

Seven `-M1` sections in `04_DB_Properties.md` are stubs: a URL, a methods
line, a Zendesk link, and a one-line GET snippet. There is no Specifications
table and no JSON Schema, so `contracts/README.md`'s three permitted sources
reduce to one - live `/info` introspection. Three of the seven
(`/db/IEHG-TRUSS-M1`, `/db/IEHG-GL-M1`, `/db/IEHG-PSS-M1`) 404 on `/info`,
which leaves them with **no permitted source at all**; that split has now been
observed three times, most recently in `schema/hyper-s-info.json`.

The four that do answer carry two defects in the schema they return. Both are
in the captured artifact verbatim, and a contract written from it must not
transcribe either.

**Apostrophes are escaped with a backslash inside a JSON string.** Eight
`description` values across `/db/MATL-M1` and `/db/EPMT-M1`:

| endpoint | path | `description` as served |
| --- | --- | --- |
| `/db/MATL-M1` | `PARAM[].USER_DEFINED.POISN` | `" Poisson\'s ratio"` |
| `/db/MATL-M1` | `PARAM[].USER_DEFINED.POISN_M` | `" Poisson\'s ratio [xy,xz,yz]"` |
| `/db/EPMT-M1` | `MASONRY.{BM,BED_JOINT,HEAD_JOINT}.YOUNG_S_MODULUS` | `" Young\'s Modulus"` |
| `/db/EPMT-M1` | `MASONRY.{BM,BED_JOINT,HEAD_JOINT}.POSSIONS_S_RATIO` | `" Poisson\'s Ratio"` |

`\'` is valid in JavaScript and PHP string literals and is not a JSON
escape. A strict parser rejects it; a lenient one keeps the backslash, so the
text reaches a reader as `Poisson\'s ratio`. The same objects also spell the
key `POSSIONS_S_RATIO`, which is the server's own misspelling of "Poisson's"
and is the wire name regardless.

**`maxItems` is attached to the wrong schema.** Four array properties on
`/db/MATL-M1`:

```json
"ELAST_M": {"description": " Modulii of elasticity [X,Y,Z]", "type": "array",
             "items": {"type": "number", "maxItems": 3}}
```

`maxItems` constrains an array; here it sits on the `number` subschema
describing each element, where JSON Schema ignores it. The intent is
unambiguous - three components, named in the description - but as served the
bound constrains nothing. `ELAST_M`, `THERMAL_M`, `SHEAR_M` and `POISN_M` all
have it.

This is the same shape as the rule `extract_contracts.py` already learned
about the manual in 2.7.5: a bound stated for another kind of value is noted,
not transcribed. It now has to hold for `/info` too.

### MD-13 - two fields, one key, and no example to separate them

`/db/TDME`'s Specifications table:

| No. | Description | Key | Value Type |
| --- | --- | --- | --- |
| 5 | Scale Factor | `"SCALE"` | Number |
| 6 | Function Data (Array of `{TIME, COMP, TENS, ELAST}`) | `"SCALE"` | Array [Object] |

The vendored manual does not hide this - its own ⚠️ callout says the source
table repeats the key, that it looks like a typo, and that there is no example
to confirm the real name, so both rows are transcribed as they stand.

That leaves the extractor with one field named `SCALE` that is a `Number` and
also has four children, which is why `/db/TDME` refuses promotion. The note is
genuinely open: no permitted source answers it. The manual states both, and
neither the section's Request Example nor its Python example sends either row.

**One live call settled it**, the same day this was registered.
`GET /info/db/TDME` lists `SCALE` as a `number` named "Scale Factor" and a
separate `aDATA` array whose items are `{TIME, COMP, TENS, ELAST}` - the
"Function Data" row's real key. Civil and Gen return identical schemas.

So row 5 is correct and row 6's key is wrong; there was never a choice between
two documented names, only one typo standing where a different name belongs.
The contract records `aDATA` with `provenance: live_corrected` and this
defect under `manualDefects`. Captured in `schema/info-schemas.json`.

### MD-14 - a code table that mixes in another product's values

`/db/TDME`'s `CODENAME` table lists 20 values. Eighteen are accepted through
the NX API. `Japan(hydration)` and `Japan(elastic)` answer `Wrong Field` on Gen
NX and Civil NX alike, in all seven spellings tried.

**That refusal is correct.** Those two codes belong to **iGen**, a different
MIDAS product, and this API is not talking to it (author, 2026-09-03). The
product is not failing to honour its own documentation; the chapter is listing
values from a product the reader cannot reach here and saying nothing about it.

So the defect is a labelling one, and it is the manual repo's to fix: the code
table should mark which entries this API serves. As it stands, a caller reading
the table has no way to tell entry 16 from entry 15, and the only feedback is
`Wrong Field` - which this file's own diagnostic reads as "unrecognised value",
sending the reader off to try spellings. Seven were tried here before the
answer turned out not to be a spelling at all.

The extra fields those two branches require (`TENS_STRN_FACTOR`, `bUSE`, `A`,
`B`, `D`, `iCTYPE`, `iECTYPE`) are all present in `/info/db/TDME`, so the
endpoint's schema is shared across products even where the code names are not.
A contract for `/db/TDME` should therefore carry the fields and leave those two
code names out of the branch it declares for this API.

> An earlier version of this entry claimed the product refuses a value its own
> documentation gives it, and held the claim back pending a re-fetch of the
> official article. The re-fetch was the right instinct and the conclusion was
> still wrong: the missing context was not in the article, it was that a second
> product exists. Recorded here because "check the source before accusing"
> would not have caught this one either.

### MD-15 - one Required value, two endpoints, two different meanings

`Create Only` appears in exactly two Required cells in the whole manual, and
both belong to a field called `CALC_OPT`:

| chapter | endpoint | row | Default |
| --- | --- | --- | --- |
| `04_DB_Properties.md:1148` | `/db/SECT` (`SECTTYPE: "VALUE"`) | Calculation Options | `true` |
| `09_DB_Dynamic_Loads.md:131` | `/db/SPFC` (KDS 41-17-00:2019) | 계산 옵션 | `false` |

Read plainly the value says: the server honours the field on create and
ignores it on modify. Measured on Gen NX on 2026-09-03, that is true of the
first row and false of the second.

`/db/SECT` matches it exactly. The identical body that POST refuses -
`CALC_OPT: false` with no `SECT_I.STIFF` to fall back on, answered
`[Error] Section input data contain errors.` - is accepted as a PUT, and a PUT
that changes `vSIZE` never recomputes `STIFF`, not even with `CALC_OPT: true`
sent explicitly.

`/db/SPFC` does not. `CALC_OPT: true` on a PUT rebuilt a spectrum that had been
hand-set to a flat two-point curve into the 103-point curve its code
parameters generate; `false` and omission both left the stale curve while
accepting new parameters.

So the defect is not that either endpoint misbehaves - each is internally
consistent - but that one Required value is being used for two different
contracts, with nothing in either cell to tell them apart. A reader who
generalises from the row they happen to meet first will be wrong about the
other one half the time.

**A second defect in the same section, found on the way.** `/db/SPFC`'s
KDS(41-17-00:2019) Request Body example omits `CALC_OPT` and supplies no
`aFUNC`. That exact body is refused:

```text
[Error] Spectrum Function Data (Name:KDS_2019_func) contains errors.(Item:Spectrum Data)
```

A design-spectrum function needs either `CALC_OPT: true`, so the server builds
the curve from `STR`/`OPT`/`VAL`, or an explicit `aFUNC`. The documented
default `false` is correct - it is the worked example that cannot run, which
is the more serious of the two because a worked example is what a reader
copies.

Both are recorded in `contracts/endpoints/db-spfc.yaml` under `manualDefects`,
and in `_MANUAL_REQUIREDNESS_CORRECTIONS` in `scripts/extract_contracts.py`
so a re-extraction carries them forward. The contract schema now accepts
`create_only` as a `requirement`, described as what the manual claims rather
than as what the product does - which is what this entry is about.

### MD-16 - a branch's requiredness stated as if there were no branch

`/db/MVHL`'s common Specifications table marks eight fields Required or
Optional without reference to `VEHICLE_LOAD_NUM`, which is the field that
decides which of them apply. Measured on Civil NX, 2026-09-03:

| No. | field | table says | measured |
| --- | --- | --- | --- |
| 4 | `VEHICLE_TYPE_NAME` | Required | required **only** under `VEHICLE_LOAD_NUM: 1`; omitting it there is refused with `(Item:Length of Vehicular Load Type(0 ~ 40 characters))` |
| 5 | `STANDARD_CODE` | Required | **not required at all** - omitted, accepted, and stored without it |
| 6 | `USER_LOAD_TYPE` | Optional | ignored on input under `MVLD_CODE: 2`; `"Train"`, `"Lane"`, `"Truck"`, `"TruckLane"` and omission all stored `"Truck/Lane"` |

Same shape as `/db/FIMP`'s table stating child keys without their parents: the
rows are not individually false so much as unqualified, and a caller reading
row 4 as an unconditional requirement writes a request the server refuses.

The chapter already contains the information. Its KSCE-LSD15 section, added
2026-07-30, carries a Standard example with `"VEHICLE_LOAD_NUM": 1` and
`VEHICLE_TYPE_NAME`, and a User Defined example with `"VEHICLE_LOAD_NUM": 2`,
`USER_LOAD_TYPE` and no type name. What is missing is any statement that this
is a branch, in the one table that presents itself as covering every code.

Row 5 also has an independent confirmation predating this: `VehiclePayload`'s
docstring records that a real production Eurocode PSC bridge model's
predefined "Load Model 1" vehicle carries no `STANDARD_CODE` key at all.

> This entry replaces a claim this repo carried for five weeks in three files:
> that `VEHICLE_LOAD_NUM` was a *documented value wrong live*, and that sending
> `2` made the product silently corrupt a standard vehicle. The observation was
> accurate and reproduces exactly; the conclusion was not. `2` selects the
> user-defined branch, and discarding branch 1's fields is that branch working.
> The observation was made 2026-07-26, four days before the manual documented
> the branch, and nobody re-read it afterwards. Fourth entry in the family that
> includes the retracted B-1/B-2/B-3 and MD-14's iGen codes - see the
> 2026-09-03 passage in `docs/live_verification_notes.md`.
