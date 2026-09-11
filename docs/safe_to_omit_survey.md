# `safeToOmit` evidence survey

Measured 2026-09-12 from the confirmed cases in `schema/live-cases.json` and
the promoted endpoint contracts. This is a review of recorded live behaviour,
not a reading of `documentedOptional` as product behaviour.

## Result

The handoff listed 60 unverified fields across 19 endpoints. The current tree
has 57 across 16 endpoints: the other three are `/db/NMAS`'s `rmX`, `rmY`, and
`rmZ`, which are correctly `safeToOmit: false` because omission crashes both
products and both SDKs normalize them before transmission.

Of the current 57 candidates:

- 21 fields have same-level, same-product, applicable-branch omission evidence
  and are promoted to `safeToOmit: true`.
- 36 fields do not. They remain `unverified`.

The accepted-call evidence means only that the server accepted the omission;
it does not claim the resulting engineering model is desirable.

## Promoted from recorded live calls (21)

| Endpoint | Fields | Evidence |
| --- | --- | --- |
| `/db/GSTP` | `OPT_MASS`, `MASS`, `OPT_DAMPING`, `DAMPING` | The confirmed Gen/Civil case omits these root fields in both POST and PUT; no endpoint normalizer fills them. |
| `/db/PNLD` | `SEQ` | The confirmed Gen/Civil case omits it in POST and PUT; the server accepts and assigns the record. |
| `/db/STCT-M1` | `RESTART_CS_ANAL`, `ERECTION_LOAD`, `bSDLE`, `vSDLE`, `TIME_DEP_CONTROL`, `CABLE_CONTROL`, `INITIAL_CONTROL`, `INITIAL_DISP`, `STRESS_DECREASE`, `iBSC`, `FRAME_OUTPUT`, `bSAVE_OCS`, `NONL_CONTROL` | The confirmed Civil PUT-only case omits all thirteen top-level fields and completes PUT/read/per-id DELETE/read. No endpoint normalizer fills them. |
| `/db/TDMT` | `TCODE`, `bSILICA` | The confirmed European-code case omits both in POST and PUT on Gen/Civil; no endpoint normalizer fills them. |
| `/db/THGC` | `bCONV_WALL_STIFF` | The confirmed case omits this Gen-only root field and passes on Gen; no endpoint normalizer fills it. |

## Kept `unverified` (36)

| Endpoint | Fields | Why the recorded case does not prove omission safety |
| --- | --- | --- |
| `/db/ELNK` | `DIR`, `MLFC`, `RLFC`, `DRENDI` | The case does not select the `MULTILINEAR`/`RAILINTERACT` branches named by their `appliesWhen`. |
| `/db/HSFC` | `OPT_USE_CONC_DATA`, `K`, `ALPHA`, `CEMENT_TYPE`, `TEMP_FUNC`, `CEMENT_CONT`, `IS_ADIABATIC_TEMP`, `SCALE_FACTOR`, `ITEM` | The case selects `TYPE="CONST"`; these belong to the `FUNC` or `USER` branches. |
| `/db/LLAN` | `SPECIAL_LANE_ITEMS` | `/info` says only “Used only when importing”; the normal lane case does not exercise that mode. |
| `/db/MVHL` | `LOAD_ITEMS`, `VEH_EUROCODE` | `LOAD_ITEMS` belongs to vehicle branch 2, while the case uses the standard branch; the `/info`-only Eurocode object has no documented selector. |
| `/db/MVLD` | `PERMIT_LOAD`, `AUTO_OPTIMIZE`, `ASL` | The case does not select the Permit, Optimization, or Australia heavy-platform branches. |
| `/db/PJCF` | `FILE_NAME`, `DIR`, `FILE_SIZE`, `CREATED`, `MODIFIED` | These are file metadata observed in responses. Their absence from a Project/User write is not request-field omission evidence. |
| `/db/POSL` | `EPGAeff`, `Kae` | Both fields are Gen-only, while the confirmed omission case is Civil-only. |
| `/db/SDIS` | `LRB`, `NRB` | They are device-type payload objects; the recorded case exercises neither branch. |
| `/db/SDST` | `LY2`, `LY3`, `IK2` | The case selects a different hysteresis model than the three `appliesWhen` branches. |
| `/db/STAG` | `NO` | This is the server-observed construction-stage number, not a field the confirmed create payload was expected to send. |
| `/db/STCT-M1` | `FINAL_STAGE` | The case sends `bLAST_FINAL: true`; it does not exercise the “other final stage” path that needs a stage name. |
| `/DESIGN/STEEL/KDS-41-30-2022/LENG` | `Assign` | This is the request wrapper, not a record member. |
| `/DESIGN/STEEL/KDS-41-30-2022/LTSR` | `Assign` | This is the request wrapper, not a record member. |
| `/DESIGN/STEEL/KDS-41-30-2022/MBTP` | `Assign` | This is the request wrapper, not a record member. |

## Guard added to the extractor

`live_omission_evidence()` now retains the literal payload values and products
of a confirmed case. Draft rendering grants omission evidence only when every
`appliesWhen` predicate was actually satisfied and the case ran on a product
to which the field applies. Parametrized tests cover a matching branch, a
different branch, and a different product.

This guard intentionally does not guess that response metadata or a wrapper is
a request field. Those remain review findings, as shown above.
