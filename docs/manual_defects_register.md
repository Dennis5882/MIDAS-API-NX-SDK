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
| MD-10 | 2026-09-01 | seven sections' Specifications tables | the table omits a root property the same section's JSON Schema declares | `/db/EPMT` (6 model objects), `/db/ELEM` (`C_RAT`, `LCAXIS`), `/db/FIMP`, `/db/RCHK`, `/ope/LCOM-GEN`, three `DCRM-*` (`SPLICED_BARS`), `/DESIGN/SRC/AIK-SRC2K/DCTL` (`FRAMEX`, `FRAMEY`) | **manual repo** transcription | open |

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

Seven promoted contracts and two drafts are built from a table that omits a
root property the same section's JSON Schema declares. `/db/FIMP` is the one
that caused damage (MD-07); the rest are recorded, not yet reconciled:

| section | root(s) only the schema names |
| --- | --- |
| `/db/EPMT` | `TRESCA`, `VMISES`, `MOHRCL`, `DRUCKER`, `MASONRY`, `CONCDMG` |
| `/db/ELEM` | `C_RAT`, `LCAXIS` |
| `/db/RCHK` | `BEAM`, `COLM` |
| `/ope/LCOM-GEN` | `CODE_SELECTION` |
| `/DESIGN/RC/KDS-41-20-2022/DCRM-BEAM`, `-COLUMN`, `-BRACE` | `SPLICED_BARS` |
| `/DESIGN/SRC/AIK-SRC2K/DCTL` | `FRAMEX`, `FRAMEY` |

Roots are the visible end of a wider pattern. Comparing every path, not just
the top level, **44 of the 337 promoted contracts and 22 of the 47 drafts**
have at least one path their section's JSON Schema declares and their table
never names. The extreme cases are whole subtrees: `/DESIGN/SRC/AIK-SRC2K/MRBD`
gives 14 of 54 paths, `/db/POGD` 9 of 73, `/view/RESULTGRAPHIC` 11 of 66.
That is measurement, not a verdict - a schema path can be a wrapper the
contract models elsewhere - but it is the number to start from. Only the root
case blocks promotion, because a missing top-level branch means the table is
not the request at all; MRBD is listed in `NEEDS_HAND_REVIEW` by name because
the tree-marker fix made it promotable while still a quarter complete.

`extract_contracts.py` now emits a review note for this, so no further contract
can be promoted from a table its own section contradicts. Reconciling the nine
needs someone to read each section and decide how the two renderings relate -
`/db/EPMT`'s six objects are `MODEL_TYPE` branches, `/db/ELEM`'s two are plain
optional fields, and they are not the same kind of gap.

## Suggested follow-up, when the author chooses to act

1. Review each finding against the current online article and manual source.
2. Correct manual-repo-owned text (MD-02, MD-04, MD-05), preserving a visible
   note where the upstream article is contradictory.
3. Escalate MD-01, MD-03, and MD-06 to MIDASIT's documentation owner; those are
   official-source issues that the manual repo can only annotate.
4. After any upstream or manual correction, re-run
   `scripts/check_manual_drift.py` before moving `vendored_at_commit`.
