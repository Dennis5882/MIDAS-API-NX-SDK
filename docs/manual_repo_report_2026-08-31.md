# MIDAS-API manual follow-up — measured findings

Prepared 2026-08-31 from the current `midas-nx` live-verification records.
This is a hand-off document only: it has **not** been applied to
`E:\AI Study\MIDAS-API`, sent to MIDASIT, or filed in Jira. The author must
choose those external actions.

The evidence comes from connected Civil NX / Gen NX sessions and is recorded
in `docs/live_verification_notes.md`; the current session baseline is Gen NX
2026 v2.1 and Civil NX 2026 v2.2, both Build 08/26/2026.

| Endpoint | Manual claim | Measured product behaviour | Where the correction belongs |
| --- | --- | --- | --- |
| `/db/STYP-M1` | `02_DB_Project_Structure.md` declares GET, PUT and DELETE in three places. | All three DELETE forms were refused on both products from a non-default open-model state. | **MIDASIT official article** (`activeMethods`) is the upstream error; the manual repo repeats it and should be corrected after the source is fixed. |
| `/db/POLC-M1` | The `14_DB_Pushover.md` warning says POST is not served and the row is an untrimmed template. | POST created a record that the next GET returned. | **Manual-repo transcription/callout.** Reverse or qualify the warning; no evidence establishes that the official article itself makes the same claim. |
| `/db/MATL-M1` | `04_DB_Properties.md:239` says the base material structure matches `/db/MATL` and adds Hyperelastic support. | Civil `/info` reports only `MATL_NAME`, `MATL_TYPE`, `PARAM`, `DAMP_RAT`; `/db/MATL` instead has `NAME`, `TYPE`, `PARAM`, `DAMP_RAT`, `HE_COND`, `HE_SPEC`, `PLMT`, `P_NAME`, `bMASS_DENS`. The purported Hyperelastic `HE_*` fields are on the parent, not MATL-M1. | **MIDASIT official article** note is the upstream error; the manual repo should preserve a correction/callout rather than delegate MATL-M1 to the parent. |
| `/db/IEHC` `WAreaSize` | The Specifications table types `WAreaSize` as Integer. | Gen `/info` types `WAreaSize` as string; the same chapter's Request Example sends `"AUTO"`. Sibling `WAreaSizeCover` is integer live. | **Manual-repo transcription/normalization.** The chapter should call out the one-field type conflict rather than present Integer as unqualified fact. |

## Evidence detail

### `/db/STYP-M1` DELETE

The manual names DELETE in its endpoint methods and other chapter locations.
Live checks against both products refused the bare DELETE body forms and the
per-id route while a real model was open. This is a product-capability finding,
not a request-wrapper inference. Keep the endpoint's documented GET/PUT facts
separate from the disproven DELETE claim.

### `/db/POLC-M1` POST

The manual-repo warning is more restrictive than the product. A live POST
created a record and a following GET returned it. The proposed correction is
not to invent a payload schema: only to stop claiming that POST is absent.

### `/db/MATL-M1` structure

The Hyper-S endpoint cannot safely inherit `/db/MATL` fields. In addition to
the different top-level names and members, its `PARAM[].P_TYPE` values are
0-based and user-defined material values are nested, whereas `/db/MATL` uses
a different, flat parameter shape. The statement is therefore not a harmless
abbreviation; it directs consumers to a wrong wire contract.

### `/db/IEHC` `WAreaSize`

This is deliberately recorded in the SDK contract as a `manualDefects` entry
and a Gen verification record. The contract keeps the manual's `integer` type
instead of silently substituting the live `string`, so downstream review can
see both claims and decide how to handle the documented contradiction.

## Requested follow-up

1. Review the four findings against the current online articles and manual
   sources.
2. Correct manual-repo-owned text for POLC-M1 and IEHC, preserving a visible
   note where the upstream article is contradictory.
3. Escalate STYP-M1's `activeMethods` and MATL-M1's parent-delegation wording
   to MIDASIT's documentation owner; these are official-source issues.
4. After any upstream/manual correction, re-run the SDK's manual drift check
   before updating its vendored revision.
