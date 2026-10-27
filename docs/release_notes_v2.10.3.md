# midas-nx 2.10.3

A shared PyPI/npm version release. Nothing changes at runtime in either SDK:
one payload type gains optional fields, and four docstrings record what live
sessions on Civil NX and Gen NX (Build 10/17/2026) measured. Nothing in it can
break a call that works today.

| surface | what actually changed |
| --- | --- |
| Python | `GeneralLinkPropertyPayload` (`/db/NLLP`) gains `SEIS_TYPE`, `SEIS_PROP`, `LDP_EFF_STIFF_COUPLED_ITEMS`, `LDP_EFF_DAMPING_COUPLED_ITEMS` and `ITEMS`. Docstrings on `generate_load_combination_concrete()`, `generate_load_combination_src()`, `generate_bridge_girder_diagram()` and `GeneralLinkPropertyPayload` gain live findings |
| npm | The same five fields on `GeneralLinkPropertyPayload`, all optional - 66 members counting those nested under `ITEMS`. No export is added or removed, and no member is removed or made required |

## `/db/NLLP` takes a lead-rubber-bearing record

The manual's SPG example for General Link Properties is refused on both
products. The `FORCE`/`LRBI` record that one of Civil NX's own tutorial models
holds is stored, and round-trips on Civil NX and Gen NX. It carries
seismic-device fields the manual does not list and the product's own `/info`
schema does, so both SDKs now type them.

The server stores a POSTed record at the next free id and answers with the key
you sent. Read the table back and match on `PROPERTY_NAME` before updating or
deleting by id.

## What the docstrings now say

- `/ope/LCOM-CONC`, `/ope/LCOM-STEEL` and `/ope/LCOM-SRC` generate and store
  load combinations on Gen NX. `OPTION: "ADD"` appends; `"REPLACE"` removes the
  existing combinations first. `LCOM-SRC` with `DGNCODE: "AIK-SRC2K"` answers
  `Set_DefaultLoadComb failed` even on an empty table. The duplicate-name hint
  in that message is not the cause.
- `/ope/GSBG` (bridge girder diagram) works on Civil NX. It needs:
  - analysis results with no DB write after the analysis;
  - a construction stage selected through `view.capture()` with `SET_MODE: "post"`;
  - `LC_NAME` without `(CS)`;
  - a single girder line as `BRDG_GROUP`;
  - an `EXPORT_PATH` that already exists.

  For a missing folder the call still answers with the file names and writes
  nothing.

## Verification behind it

The repository's live write coverage moved from 281 to 312 of 400 endpoints
over these sessions. Several endpoints that had always refused their documented
payload were stored once given a record the product's own example models hold.
These are `/db/RPSC` (needs `PART`), `/db/TDMF` (needs a non-zero `ELAST` with
`RELAXATION`) and `/db/MVLDeu` (Load Model 1 in its tutorial shape). None of
that ships in either package; the evidence is in
https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md.
