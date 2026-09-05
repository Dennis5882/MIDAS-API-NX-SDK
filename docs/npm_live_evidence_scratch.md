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
| `/db/MVCD` | 2026-09-05 | Gen, Civil |
| `/db/TDGR` | 2026-09-05 | Gen, Civil |
| `/db/NPLN` | 2026-09-05 | Gen, Civil |
| `/db/ETFC` | 2026-09-05 | Gen, Civil |
| `/db/CCFC` | 2026-09-05 | Gen, Civil |
| `/db/HSFC` | 2026-09-05 | Gen, Civil |
| `/db/MLFC` | 2026-09-05 | Gen, Civil |
| `/db/CUTL` | 2026-09-05 | Gen, Civil |
| `/db/CLWP` | 2026-09-05 | Gen, Civil |

| `/db/CNLD` | 2026-09-05 | Gen, Civil |
| `/db/BMLD` | 2026-09-05 | Gen, Civil |
| `/db/CONS` | 2026-09-05 | Gen, Civil |
| `/db/ESSF` | 2026-09-05 | Gen, Civil |
| `/db/SECF` | 2026-09-05 | Gen, Civil |
| `/db/TSGR` | 2026-09-05 | Gen, Civil |
| `/db/TDMT` | 2026-09-05 | Gen, Civil |
| `/db/TDME` | 2026-09-05 | Gen, Civil |
| `/db/GSTP` | 2026-09-05 | Gen, Civil |
| `/db/IFGS` | 2026-09-05 | Gen, Civil |
| `/db/THGC` | 2026-09-05 | Gen, Civil |
| `/db/THFC` | 2026-09-05 | Gen, Civil |
| `/db/SPLC` | 2026-09-05 | Gen, Civil |
| `/db/LCOM-GEN` | 2026-09-05 | Gen, Civil |
| `/db/LCOM-CONC` | 2026-09-05 | Gen, Civil |

| `/db/LLANch` | 2026-09-06 | Civil |
| `/db/SLANch` | 2026-09-06 | Civil |
| `/db/LLANid` | 2026-09-06 | Civil |
| `/db/LLANtr` | 2026-09-06 | Civil |
| `/db/MVHLtr` | 2026-09-06 | Civil |
| `/db/MLSP` | 2026-09-06 | Civil |
| `/db/MLSR` | 2026-09-06 | Civil |
| `/db/MVLDtr` | 2026-09-06 | Civil |

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
- The 2026-09-05 empty-document sweep selected cases whose Python fixture
  relied on that harness's common base model, which the shared JSON did not
  carry, so those npm attempts were not counted. **Resolved.** Fixture version
  5 emits the base model and every tier seed the npm harness can replay, and
  the fifteen affected endpoints were re-run on both products on 2026-09-05.
  They are counted above; see the live notes for the run.

**Count:** 55 distinct `/db` endpoints and 4 distinct result-table operations;
59 distinct npm public-API operations overall.
