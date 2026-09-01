# npm live-evidence inventory (scratch)

Read-only extraction from `docs/live_verification_notes.md` on 2026-09-01.
This is an inventory, not a coverage or schema change. An entry appears only
when the notes explicitly say the built npm package completed the operation.
`docs/coverage.json` remains Python-only evidence.

## Completed DB endpoints

| Endpoint | Date | Products |
| --- | --- | --- |
| `/db/NODE` | 2026-08-31 | Gen, Civil |
| `/db/NMAS` | 2026-08-31 | Gen, Civil |
| `/db/LDGR` | 2026-08-31 | Gen, Civil |
| `/db/SMCT` | 2026-08-31 | Gen, Civil |
| `/db/SKEW` | 2026-08-31 | Gen, Civil (also separately re-checked on Gen) |
| `/db/STLD` | 2026-08-31 | Gen, Civil |
| `/db/THIK` | 2026-08-31 | Gen, Civil |
| `/db/DCON` | 2026-08-31 | Gen, Civil |
| `/db/DSTL` | 2026-08-31 | Civil |
| `/db/DCTL` | 2026-08-31 | Gen, Civil |
| `/db/LTSR` | 2026-08-31 | Gen, Civil |
| `/db/MBTP` | 2026-08-31 | Gen, Civil |
| `/db/LENG` | 2026-08-31 | Gen, Civil |
| `/db/MEMB` | 2026-08-31 | Gen, Civil |
| `/db/WMAK` | 2026-08-31 | Gen, Civil |
| `/db/SDST` | 2026-08-31 | Gen, Civil |
| `/db/PNLD` | 2026-08-31 | Gen, Civil |
| `/db/EIGV` | 2026-08-31 | Gen, Civil |
| `/db/LCOM-SEISMIC` | 2026-09-01 | Gen |
| `/db/SDVI` | 2026-09-01 | Gen, Civil |
| `/db/SDVE` | 2026-09-01 | Gen, Civil |
| `/db/SDHY` | 2026-09-01 | Gen |
| `/db/SDIS` | 2026-09-01 | Gen |

## Completed result-table operations

| TABLE_TYPE | Date | Products |
| --- | --- | --- |
| `MASS_SUMMARY_X` | 2026-08-31 | Gen, Civil |
| `REACTIONG` | 2026-08-31 | Gen, Civil |
| `DISPLACEMENTG` | 2026-08-31 | Gen, Civil |
| `BEAMFORCE` | 2026-08-31 | Gen, Civil |

## Deliberate exclusions

- Read-only first-session checks (`/db/STYP`, `/info/db/NODE`) were successful
  transport checks, but were not described as completed npm endpoint cases.
- Explicit rejections or unresolved cases (`/db/MVCT`, `/db/SDIS` LRB,
  `/db/WVLD`, `/db/NLLP`, Gen `/db/DSTL`, and `/db/BCCT`) are not evidence of
  a completed endpoint operation.
- `/doc/NEW`, `SAVEAS`, and the model-building prerequisites are harness
  operations, not selected endpoint cases.

**Count:** 23 distinct `/db` endpoints and 4 distinct result-table operations;
27 distinct npm public-API operations overall.
