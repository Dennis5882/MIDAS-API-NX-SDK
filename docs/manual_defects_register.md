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

## Suggested follow-up, when the author chooses to act

1. Review each finding against the current online article and manual source.
2. Correct manual-repo-owned text (MD-02, MD-04, MD-05), preserving a visible
   note where the upstream article is contradictory.
3. Escalate MD-01 and MD-03 to MIDASIT's documentation owner; those are
   official-source issues that the manual repo can only annotate.
4. After any upstream or manual correction, re-run
   `scripts/check_manual_drift.py` before moving `vendored_at_commit`.
