# Live API verification notes

Empirical findings from running `midas-nx` v0.8.0 against real MIDAS NX Open
API sessions (one Gen NX session, one Civil NX session, both connected via
the live cloud relay at `moa-engineers.midasit.com`, not mocked). This is
**not** sourced from the vendored manual — everything else in this repo is
typed strictly from `docs/manual/*.md` and treated as the single source of
truth; this file exists precisely because these findings are *not* in the
manual and shouldn't be silently baked into the SDK's typed contracts
(`PRODUCTS`, `METHODS`) without independent reproduction. See the caveat at
the bottom before acting on anything here.

Date: 2026-07-15. One MIDASIT account, one Gen NX process, one Civil NX
process, both freshly reset via `/doc/new` before testing.

## Method

1. **Read-only smoke test**: every `DbResource` subclass across `db/`,
   `design/`, `post/` whose `METHODS` includes `GET` and whose `PRODUCTS`
   includes the product under test got a live `GET` call against a blank
   new document. No fixtures needed — a blank model returns an empty result
   for every valid endpoint (confirmed shape: `{"message": ""}` for
   zero-row tables, `{"<KEY>": {}}` for zero-row `/db/*` tables), so a
   non-2xx response reliably signals a real problem rather than "no data."
2. **Write round-trip** (Gen only): built a minimal model — 1 material
   (`MATL`, concrete C24), 1 section (`SECT`, 600×600), 2 nodes, 1 beam
   element, 1 fixed support — then exercised representative endpoints from
   each design-code chapter (ch24 `db/design.py`, ch25 `steel_kds.py`, ch26
   `rc_kds/setup.py`, ch27 `src_aiksrc2k.py`) against it.

## Read-only results

| Product | GET-capable & product-compatible classes tested | OK | Failed (all 404) |
|---|---|---|---|
| Gen  | 253 | 233 (92%) | 20 |
| Civil | 293 | 273 (93%) | 20 |

### Failure breakdown

**Hyper-S (`-M1`) endpoints — 13, fail under Gen.**

> ⚠️ **Corrected 2026-07-26.** The original text here said these were
> "absent from the Civil target set entirely (their `PRODUCTS` is already
> `{"gen"}`-only in the SDK)" and explained the Gen 404s as the session not
> running in Hyper-S solver mode. **Both halves were wrong.** Their
> `PRODUCTS` was `{"gen", "civil"}`, so they *were* in the Civil target set,
> and re-running the sweep shows all 13 **answering under Civil**. Hyper-S
> is the solver MIDASIT introduced with Civil NX — it is a Civil NX feature,
> not a Gen mode — so the Gen 404s are correct behaviour and the SDK's
> `PRODUCTS` was the thing that was wrong. Fixed via `HYPER_S_ONLY` in
> `db/base.py`. See the 2026-07-26 section below. The claim was never
> checked against a Civil run; it was inferred, and the inference was wrong
> in a way that a one-line `sorted(cls.PRODUCTS)` would have caught.

- `/db/ACTL-M1`, `/db/BCGA-M1`, `/db/BCGD-M1`, `/db/EIGV-M1`,
  `/db/HHCT-M1`, `/db/NLCT-M1`, `/db/NLNK-M1`, `/db/STCT-M1`,
  `/db/THGC-M1`, `/db/THIS-M1`, `/db/THOO-M1`, `/db/POGD-M1`,
  `/db/POLC-M1`

**Failed under Gen, succeeded under Civil (7)** — current SDK `PRODUCTS`
says `{"gen", "civil"}` for all of these (no restriction documented in the
manual), but this session's evidence points to Civil-only in practice:

- `midas_nx.db.construction_stage.CamberConstructionStage` (`/db/CMCS`)
- `midas_nx.db.design.RebarCheckInput` (`/db/RCHK`)
- `midas_nx.db.misc_loads.PreCompositeSection` (`/db/PLCB`)
- `midas_nx.db.misc_loads.WaveLoad` (`/db/WVLD`)
- `midas_nx.db.project.Span` (`/db/SPAN`)
- `midas_nx.db.properties.section.EffectiveWidthScaleFactor` (`/db/EWSF`)
- `midas_nx.db.properties.section.SectionStressPoints` (`/db/STRPSSM`)

**Failed under Civil, succeeded under Gen (20)** — same situation, opposite
direction; evidence points to Gen-only in practice:

- `midas_nx.db.boundary.DiaphragmDisconnect` (`/db/DRLS`)
- `midas_nx.db.boundary.SeismicDeviceHystereticIsolator` (`/db/SDHY`)
- `midas_nx.db.boundary.SeismicDeviceIsolator` (`/db/SDIS`)
- `midas_nx.db.design.BeamRebar` (`/db/REBB`)
- `midas_nx.db.design.BraceRebar` (`/db/REBR`)
- `midas_nx.db.design.WallRebar` (`/db/REBW`)
- `midas_nx.db.project.Story` (`/db/STOR`)
- `midas_nx.db.static_loads.SoilProperty` (`/db/POSP`)
- `midas_nx.db.static_loads.StaticEarthPressure` (`/db/EPST`)
- `midas_nx.db.static_loads.StaticSeismicLoad` (`/db/SSEIS`)
- `midas_nx.db.static_loads.StaticWindLoad` (`/db/SWIND`)
- `midas_nx.design.rc_kds.rebar.ModifyBeamRebarData` (`/DESIGN/RC/KDS-41-20-2022/REBB`)
- `midas_nx.design.rc_kds.rebar.ModifyBraceRebarData` (`/DESIGN/RC/KDS-41-20-2022/REBR`)
- `midas_nx.design.rc_kds.rebar.ModifyColumnRebarData` (`/DESIGN/RC/KDS-41-20-2022/REBC`)
- `midas_nx.design.rc_kds.rebar.ModifyWallRebarData` (`/DESIGN/RC/KDS-41-20-2022/REBW`)
- `midas_nx.design.rc_kds.rebar.TorsionReductionFactor` (`/DESIGN/RC/KDS-41-20-2022/TRFT`)
- `midas_nx.design.rc_kds.setup.ModifyConcreteMaterial` (`/DESIGN/RC/KDS-41-20-2022/MATD`)
- `midas_nx.design.rc_kds.setup.UndergroundLoadCombinationType` (`/DESIGN/RC/KDS-41-20-2022/ULCT`)
- `midas_nx.design.src_aiksrc2k.SrcModifyMaterial` (`/DESIGN/SRC/AIK-SRC2K/MATD`)
- `midas_nx.design.steel_kds.UndergroundLoadCombinationType` (`/DESIGN/STEEL/KDS-41-30-2022/ULCT`)

All URL paths above were double-checked character-for-character against the
manual's own "Input URI" for each endpoint — none of these are SDK
transcription bugs. The URLs are right; the routes just weren't reachable
from the product tested against.

## Write round-trip results (Gen)

- Model build (`MATL`, `SECT`, `NODE`, `ELEM`, `CONS`): all 5 calls returned
  exactly the documented response shape, verified byte-for-byte against
  what was sent.
- ch24–27 config-singleton `PUT` endpoints (`RcDesignCode`, `SteelDesignCode`,
  `SteelDesignCodeOption`, `ConcreteDesignCodeOption`, `SrcDesignCode`,
  `SrcDesignCodeOption`): all succeeded, response echoed the payload under
  the documented top-level key (`DCON`, `DSTL`, `DCO`, `DCORC`, `DSRC`,
  `SRCDCO`).
- ch24 `DesignMemberAssignment.create` (registers element 1 as design
  member 1): succeeded.
- **Operational nuance, not a bug**: once a design member is registered,
  the server auto-seeds a default per-member parameter record (e.g. `LENG`)
  for that member ID in every currently-selected design-code namespace.
  Calling `.create()` (`POST`) on that ID afterward returns
  `{"error": {"message": "Key Already Exist"}}` inside a 200 response
  (not an exception — `MidasClient.request()` only raises on non-2xx
  status, so callers must check for an `"error"` key even on success).
  Calling `.update()` (`PUT`) instead succeeds and a subsequent `GET`
  confirms the value round-trips exactly. Confirmed for
  `steel_kds.UnbracedLength`, `rc_kds.setup.UnbracedLength`, and
  `src_aiksrc2k.SrcUnbracedLength`, all targeting the same RC element —
  this also confirms the server does real semantic validation rather than
  blindly persisting writes (steel/SRC-code member parameters were still
  *accepted* on a plain-concrete element in this test, so no rejection was
  observed there, but the "already exists" behavior itself is a genuine
  cross-code-namespace side effect worth knowing about).

## Extended verification: Civil-only chapters + full analyze→results round-trip

Two more sessions were run after the initial pass above.

### Civil write test — ch08 moving loads / ch17 bridge (previously untested)

Built a minimal Civil model (30 m single-span concrete beam: 1 material, 1
section, 2 nodes, 1 element, 1 fixed support), then:

- `MovingLoadCode.update` (`/db/MVCD`, `CODE="AASHTO LRFD"`): succeeded.
- `TrafficLineLanes.create` (`/db/LLAN`) **first attempt failed** with a real
  server-side semantic validation error, not a schema rejection:
  `"[Error] Line Lane Data (Name:Lane1) contains errors.(Item:Centrifugal
  Force ( 0.0 < Value < 1.0))"`. The manual documents `LANE_ITEMS.CENT_F`
  as merely "optional (AASHTO LRFD only)" — this session's evidence is that
  once `AASHTO LRFD` is the selected moving-load code, `CENT_F` is
  effectively **required** (must be a value in the open interval (0, 1);
  the SDK's implicit default of omitting the field, which the server reads
  as 0.0, is rejected). Retried with `CENT_F: 0.1` — succeeded, and `GET`
  read back every field including server-filled defaults
  (`GROUP_NAME: ""`, `SKEW_START/END: 0`, `WHEEL_SPACE: 0`,
  `OPT_AUTO_LANE: False`, `ALLOW_WIDTH: 0`, `FACT: 0`, `SPAN_START: False`,
  `ECCEN_VERT_LOAD: 0`) — full round-trip confirmed once the semantically
  valid payload was sent. Not an SDK bug (the field genuinely is optional
  per the manual's schema, and the SDK correctly makes it optional in the
  `TypedDict`), but worth knowing if you hit the same error live: pass a
  nonzero `CENT_F` when `MVCD.CODE` is `"AASHTO LRFD"`.
- `BridgeGirderDiagram.create` (`/db/GSBG`) with a placeholder
  `BODY_ELEM_GRUP_K: 1` (no structure group with that ID actually existed):
  succeeded — the server did not validate the group reference exists at
  write time.

### Gen full analyze → results round-trip (post/* chapters, previously only mocked)

Added a static load case (`STLD`, `NAME="DL"`, `TYPE="D"`) and self-weight
(`BODF`, `FV=[0,0,-1]`) to the Gen cantilever-column model from the first
pass, then:

1. `doc.analyze()` (`/doc/ANAL`) — first call (no loads yet) correctly
   failed with `"[Error] Load information has not been entered for
   Analysis."`; after adding the load case, succeeded
   (`"MIDAS GEN NX command complete"`).
2. `post.result_1.get_reaction_table/get_displacement_table/
   get_beam_force_table` — first call used `load_case_names=["DL"]` and
   got back `{"message": ""}` for all three (looked like "no data", but
   was actually a caller mistake). `get_table`'s own docstring in
   `post/base.py` already documents the fix: load case names need a type
   suffix, e.g. `"DL(ST)"`. Retried with `["DL(ST)"]` — all three returned
   full documented `{FORCE, DIST, HEAD, DATA}` tables.
3. **The numbers are physically correct**, not just structurally valid:
   - Reaction at node 1 (base): `FZ = 28.243152` — matches hand-calc
     self-weight of a 0.6×0.6×3.2 m C24 concrete column (`0.36 m² × 3.2 m
     × ~24.5 kN/m³ ≈ 28.2–28.8 kN`).
   - Displacement at node 2 (free top): `DZ = -0.000005` m — negligible
     axial shortening under self-weight, correct sign (downward).
   - Beam force: axial force `-28.24 kN` at the I-end (base), decreasing
     linearly to `0.00` at the J-end (free top) across the 4 reported
     stations — exactly the expected self-weight axial-force diagram for a
     vertical cantilever.

This confirms the full chain end to end: SDK request shape → real Gen NX
solve → SDK response parsing, for both the `/db/*` write side and the
`/post/TABLE` read side.

## Civil full analyze → results round-trip, including moving-load envelope results (previously untested)

A later Civil session closed the remaining gap on the Civil side: static
analysis physically verified end to end, and — Civil's signature feature —
an actual moving-load analysis run and its `(MV:max)`/`(MV:min)` envelope
results read back and sanity-checked.

### Static self-weight round-trip — physically verified

Built a 30 m, 2-span (3-node) simply supported... in practice **fixed
against rotation at both ends** (constraint string `1111100` restrains
`RY` at both supports, not a true pin) concrete girder (`0.6×1.0 m`
rectangular section, `C24`/`KS01(RC)`), added a `DL` self-weight load case,
ran `doc.analyze()`, then read back reactions/displacements/beam forces:

- Total self-weight reaction: `ΣFZ = 423.647281 kN` across both supports
  (`211.823641` each) — consistent with a uniformly distributed self-weight
  load `w = 423.647 / 30 = 14.12 kN/m` on a `0.6 × 1.0 m` section.
- Support moment `MY = ±1059.11825 kN·m` — matches the fixed-end-moment
  formula for a fixed-fixed beam under UDL, `wL²/12 = 14.12 × 30² / 12 =
  1059.12` — an exact hand-calc match.
- Beam-force moment diagram across both elements' I/1/4/2/4/3/4/J stations
  forms a consistent parabola between the two support end-moments and the
  midspan value (`132.39`), matching continuous-beam bending-moment theory.

**Operational note, not a bug**: one `Material.create` attempt with
`STANDARD: "KS(RC)"` failed with `"Failed to get material data for:
C24"` — the correct Civil concrete standard code turned out to be
`"KS01(RC)"`, not `"KS(RC)"`. The manual doesn't enumerate every valid
`STANDARD` string per material type/product, so this is a live-only
finding, not a schema contradiction.

### Moving-load analysis — full chain verified, with real vehicle/lane data

Added `MovingLoadCode` (`CODE="KOREA"`), a Traffic Line Lane spanning both
elements, a `DB-24` Korean standard vehicle, and a moving-load case
referencing both, then re-ran analysis:

- `Vehicles.create` (`/db/MVHL`) **initially no-op'd silently**
  (`{"message": ""}`, not an error, and a subsequent `GET` confirmed
  nothing was actually saved) when `VEH_DEFAULT` was sent as `{}`. The
  manual's own worked example for `STANDARD_CODE="KS-RB"` always populates
  `VEH_DEFAULT` with explicit `DYN_LOAD_ALLOWANCE`/`CENT_F` values even
  though the schema marks those fields "optional" — copying the manual's
  exact worked example (`MVLD_CODE: 6`, `VEH_DEFAULT: {"DYN_LOAD_ALLOWANCE":
  0, "CENT_F": false}`) succeeded immediately. Worth knowing live: don't
  send an empty `VEH_DEFAULT: {}` even though every one of its fields is
  individually documented as optional — populate it per the manual's
  worked example for your `STANDARD_CODE`.
- `MovingLoadCase.create` (`/db/MVLD`, `TYPE=0` general load referencing
  the vehicle + lane by name) — succeeded.
- `doc.analyze()` — succeeded in **2.0s** (tiny model, no large-model delay
  here).
- `get_beam_force_table(load_case_names=["MV1(MV:max)"])` and
  `["MV1(MV:min)"]` — both returned full, real, non-degenerate envelope
  data: e.g. max positive midspan moment `615.61`–`732.12 kN·m`, min
  (most-negative) support moment `-1702.53 kN·m` (larger in magnitude than
  the plain self-weight case above, as expected — the DB-24 truck adds to
  the fixed-end moment at whichever support it's nearest). This is a
  believable, non-trivial moving-load envelope, not placeholder/zero data.

This confirms the full Civil-specific chain end to end: `MVCD` → `MVHL` →
`LLAN` → `MVLD` → `doc.analyze()` → `post/TABLE` with `(MV:max)`/`(MV:min)`
suffixes, previously only exercised as isolated writes (see the moving-load
write test above), not run through an actual analysis.

### Operational quirk shared with the Gen findings: a confirmation dialog blocks the whole API session, not just one call

Partway through this session, `MovingLoadCode.update` (changing the active
moving-load code) triggered a **Civil NX confirmation dialog** ("changing
this will delete existing analysis results") that the user hadn't
dismissed yet. While that dialog sat open, **every** subsequent API call —
including totally unrelated ones like a plain `GET /db/NODE` — timed out
with no response, not just the call that triggered the dialog. After the
user dismissed the dialog, the session immediately became responsive
again, and a `GET` on the field that triggered it confirmed the change had
already persisted despite the client-side timeout.

This is the same shape of finding as the Gen `CC-ANAL` stall (an API call
blocks on an unacknowledged UI dialog, and the underlying change completes
and persists regardless of whether the HTTP response ever arrives) — but
milder and expected: a normal user-confirmation dialog is not a bug, and
it explains itself once you know to check for it. Worth knowing for
scripted/batch use of this API: **any call that can trigger a confirmation
dialog (destructive/data-loss-risking changes) can make the entire session
appear hung until a human dismisses it**, not just that one call.

## ⚠️ CONFIRMED — `CC-ANAL` (RC column code-check perform) reproducibly stalls Gen NX at "Converting Design Results 0%" (often requires a forced process kill)

> **STATUS UPDATE (2026-07-25): `CC-ANAL`/`BC-ANAL`/`WC-ANAL` ran clean 4/4 —
> on the *same build* that hung here.** This is not a "fixed in a newer
> build" story: both the reproductions below and the clean re-runs happened
> on **Gen NX 2026 (v2.1), build 06/23/2026**. The trigger is therefore
> something other than the build, and is still unidentified — so nothing in
> this section is retracted. See
> [the re-verification section below](#status-update-2026-07-25--cc-analbc-anal-ran-clean-on-the-same-build-that-hung).

While extending the same Gen session above to verify design-code check
*execution* (as opposed to just config-singleton writes), the following
sequence **crashed/hung the Gen NX desktop application itself** (not just
an API error — the process stopped responding and required a manual
restart):

1. `design.rc_kds.setup.ModifyMemberType.create({1: {"TYPE": "COLUMN"}})` —
   succeeded.
2. `design.rc_kds.rebar.ModifyColumnRebarData.create({1: {"ITEMS": [...]}})`
   keyed by section number 1 (main bar D22×8, end/center hoop bars D10) —
   succeeded.
3. First `perform_column_check({"PERFORM_TYPE": "ALL"})` (`CC-ANAL`) —
   failed cleanly with `{"error": {"message": " Please perform
   analysis."}}` (expected — design parameters changed after the last
   solve, invalidating results).
4. Re-ran `doc.analyze()` — succeeded.
5. Retried `CC-ANAL` — failed cleanly with `{"error": {"message":
   "failed:LoadCombination"}}` (also expected — no load combination
   existed yet, only a raw load case).
6. Added `db.load_combinations.LoadCombinationGeneral.create({1: {"NAME":
   "COMB1", "ACTIVE": "ACTIVE", "iTYPE": 0, "vCOMB": [{"ANAL": "ST",
   "LCNAME": "DL", "FACTOR": 1.2}]}})` — succeeded.
7. Retried `CC-ANAL` a third time — **this call never returned**. Timed
   out client-side at both 30s (default) and 120s (explicit
   `MidasClient(timeout=120)`) with `ReadTimeoutError`/`ConnectionError`
   — no HTTP response at all, not even a slow one. The user confirmed the
   Gen NX desktop application itself had stopped responding and needed a
   full restart.

### Reproduction #2 — confirmed, with visual evidence

To rule out "messy session state" as the cause, the entire sequence was
redone from a **fresh `doc.new_project()`**, touching only RC design (no
`steel_kds`/`src_aiksrc2k` namespaces at all this time):

1. Fresh minimal model (1 material, 1 section, 2 nodes, 1 element, 1
   support, 1 static load case `DL`, self-weight) + `doc.analyze()` — all
   clean.
2. `ModifyMemberType` → `COLUMN`, `ModifyColumnRebarData` (same rebar
   payload as before), `doc.analyze()` again — all clean.
3. `CC-ANAL` before any load combination existed — failed cleanly and
   fast with `{"error": {"message": "failed:LoadCombination"}}`. **Did
   not hang.** This suggested the first hang might have been session-state
   related.
4. Manually written `db.load_combinations.LoadCombinationGeneral` combo
   — `CC-ANAL` retried — failed cleanly and fast again with the same
   `"failed:LoadCombination"` message (the manually-entered `LCOM-GEN`
   entry apparently isn't recognized as a valid design combination by the
   RC check module — a separate, milder finding, see below).
5. Used `ope.generate_load_combination_concrete({"OPTION": "ADD",
   "DGNCODE": "KDS 41 20 : 2022"})` instead — this **is** the right way to
   produce design-code-recognized combinations: it auto-generated
   `cLCB1` (`1.4(D)`, `ACTIVE: "STRENGTH"`) and `cLCB2`
   (`SERV:(D)`, `ACTIVE: "SERVICE"`) in `/db/LCOM-CONC`.
6. `CC-ANAL` retried a third time, now with a real, code-recognized
   design combination in place — **hung again**, this time with a 40s
   explicit client timeout.
7. The user checked the Gen NX window directly and found a **"Stop
   Design Thread" dialog, stuck at "Converting Design Results... 0%"**
   with a "Stop Execution" button. Clicking Stop Execution **did nothing**
   — the dialog stayed frozen. The application had to be force-killed via
   Task Manager; there was no graceful recovery path.

**Conclusion**: this is a real, reproducible Gen NX application defect,
not session-state flakiness and not an SDK issue. `CC-ANAL` (RC column
code-check "perform") appears to spawn an internal "Design Thread" that
can deadlock during its "Converting Design Results" phase, and the
deadlock is unrecoverable from the UI (Stop Execution is on the same
stuck thread/message loop). The Open API call blocks synchronously
waiting for that thread, so from the SDK's perspective it just looks like
a network read timeout with no way to distinguish "still computing" from
"permanently stuck" short of an arbitrarily long timeout.

### Reproduction #3 — confirmed a third time, on an unrelated large real-world model

To rule out "this only happens on a tiny synthetic 1-element model," the
same pattern was tested against a separate, pre-existing production-scale
Gen model (thousands of nodes/elements, real materials/loads/analysis
results already present, different RC design code originally selected).
Project-specific numeric details are intentionally omitted here — only the
reproduction pattern matters:

1. A read-only survey confirmed this model's active RC design code was
   **not** KDS 41 20:2022, so its `rc_kds.setup` (config-singleton) and
   `rc_kds.rebar` (member rebar) tables were empty for every member,
   despite the model already having real design-member registrations
   under a different code.
2. `CC-ANAL` on a real, verified-vertical concrete column element with
   `PERFORM_TYPE: "ELEMS"` (single element, not `"ALL"`) — failed cleanly
   and fast: `{"error": {"message": "failed:Rebar, BeamData"}}`. No hang.
3. Assigned `ModifyMemberType` (`COLUMN`) + `ModifyColumnRebarData` (same
   rebar shape as the earlier reproductions) for that element's section,
   re-ran `doc.analyze()` (succeeded, no issue at this model's larger
   scale) — retried `CC-ANAL` — failed cleanly and fast again:
   `{"error": {"message": "failed:LoadCombination"}}` (the model's 50+
   pre-existing general load combinations were **not** recognized as valid
   design combinations, consistent with reproduction #2). No hang.
4. Ran `ope.generate_load_combination_concrete({"OPTION": "ADD", "DGNCODE":
   "KDS 41 20 : 2022"})` — succeeded, auto-generated proper factored
   combinations from the model's real load cases.
5. Retried `CC-ANAL` a third time on the same single element — **hung
   again**, 40s client timeout, no HTTP response. The user confirmed Gen
   NX was frozen again and required another forced kill.

**This is now the exact, minimal, deterministic trigger pattern across
three independent reproductions** (one synthetic model, one real
production model tested twice): `CC-ANAL` hangs specifically once **both**
(a) the target element/section has member-type + rebar data assigned for
the KDS 41 20:2022 namespace, **and** (b) at least one load combination
exists that the KDS check module itself recognizes as a valid design
combination (i.e., one generated via `ope.generate_load_combination_concrete`
or equivalent, not a plain manually-written `/db/LCOM-GEN` entry). In
other words: it hangs at the exact moment the check has *enough real data
to actually attempt the P-M-interaction calculation* — every precondition
short of that fails fast and cleanly instead.

**Do not call `design.rc_kds.checks.perform_column_check` (`CC-ANAL`)
against a live session with both preconditions satisfied, without an
escape plan** (expect to force-kill Gen NX — "Stop Execution" does not
work). Given the shared "Design Thread" architecture across every other
`perform_*_check`/`*-ANAL` function in this SDK (`perform_beam_check`,
`perform_brace_check`, `perform_wall_check` in the same file;
`perform_steel_code_check` in `steel_kds.py`;
`perform_src_beam_check`/`perform_src_column_check` in
`src_aiksrc2k.py`; `perform_optimal_design`/`OCHECK` variants), **treat
the entire "perform design check" family as carrying the same likely hang
risk once both analogous preconditions are met** until each is
independently tested. This session did not attempt any of the others.

### Reproduction #4 — cleanest case: a natively KDS-configured real model, no forced setup

A fourth session opened a separate, unrelated pre-existing Gen model whose
RC design code was **already** `"KDS 41 20 : 2022"` natively (not forced
onto it like reproductions #2/#3) — `rc_kds.setup.ConcreteDesignCodeOption`
and `rc_kds.rebar.ModifyColumnRebarData` already had real data (4 sections)
before any of this session's calls. This is the most realistic scenario
yet: a normal user, on a normal KDS-native model, checking one column.

1. `CC-ANAL` on a real column element (`PERFORM_TYPE: "ELEMS"`, single
   element) — failed cleanly: `{"error": {"message": " Please perform
   analysis."}}`.
2. `doc.analyze()` via the API returned `"MIDAS GEN NX command complete"`,
   but a subsequent `get_reaction_table()` call still reported
   `"[empty] Cannot generate table data as there is no analysis result."`
   — i.e. the API's "complete" acknowledgment did not reliably mean
   results were actually queryable yet on this larger model (4044 nodes).
   Re-running the analysis **from the Gen NX GUI directly** resolved this
   (reaction table then returned real data) — worth noting as a separate,
   milder finding: don't assume `doc.analyze()`'s response means results
   are immediately queryable for large models; confirm with a cheap
   results call before proceeding, or retry.
3. `CC-ANAL` retried on the same element — the HTTP call hung again (40s
   timeout, no response), and the same "Stop Design Thread — Converting
   Design Results... 0%" dialog appeared. **This time the user also
   checked Gen NX's internal message/log window while it was stuck**, and
   it showed the entire check had already finished:

   ```text
   *** Start Code Checking by KDS 41 20 : 2022.
       End preparing Design Informations.
       End Design/Checking of Member.
       Creating design result file...
       End creating design result file.
       End converting Design Results.
   *** End Code Checking by KDS 41 20 : 2022
   ```

   Every step, including "End converting Design Results" and the final
   "End Code Checking" line, had already logged as complete — while the
   progress dialog was still frozen at 0% on that same step. The user
   clicked Stop Execution; the dialog closed and the app recovered
   cleanly, no forced kill needed this time (unlike reproductions #1–#3,
   where an additional error popup appeared and the app had to be
   force-killed).

**Revised diagnosis: this is very likely a stuck progress-dialog / stale
completion-signal bug, not a genuine backend computation deadlock.** The
underlying KDS code check appears to actually finish — the message log
says so explicitly, end to end — but something (the progress dialog's
own close/refresh logic, and/or whatever signal the Open API layer itself
waits on to consider the request "done" and return an HTTP response)
never fires. That would also explain why the API call kept timing out
even in this 4th case: it's plausibly blocked on the *same* stuck signal
as the dialog, not on the design check itself. Reproductions #1–#3 didn't
have this log checked at the time, so it's unconfirmed whether they were
the same underlying issue or a genuinely different (deadlocked, not just
signal-stuck) failure — worth checking the message log first thing if
this is reproduced again.

**Four for four on the stall itself; consequences vary.** Every attempt
where the check had a real target element with real rebar data, a real
recognized load combination, and real analysis results triggered the same
"Converting Design Results... 0%" stall — including this cleanest case
with no artificial setup at all and, per the log, a design check that had
actually completed. That part is no longer a corner case; it's the
expected outcome of calling `CC-ANAL` for its actual intended purpose in
this Gen NX build. What differs is the outcome: an additional error popup
and a required forced kill 3 of 4 times, vs. a clean recovery via Stop
Execution (with the check apparently having already finished
successfully) the 4th time. **Testing was stopped after this
reproduction** — no further value in repeating it, and most attempts
still cost a forced restart or at least a stuck dialog.

### Confirmed: the check result is actually there — `CC-TABLE` proves it

After reconnecting post-reproduction #4, `get_column_check_table` (`CC-TABLE`)
was called for the same element (371) that the "hung" `CC-ANAL` call had
targeted — **it returned full, real design-check results**:
`CHK_STR: "OK"`, `CHK_RBR: "OK"`, real P-M interaction ratios
(`Rat_P: 0.468`, `Rat_M: 0.151`), real assigned rebar (`"28-6-D25"`), real
shear/hoop-spacing checks — not placeholder or empty data. This
conclusively confirms the diagnosis above: the design check itself
genuinely completes and its results genuinely persist to the model, even
when the triggering `CC-ANAL` call times out with no HTTP response.

**Practical workaround for callers**: if `perform_column_check` (`CC-ANAL`)
times out or the connection errors, **don't assume the check failed** —
retry with `get_column_check_table` (`CC-TABLE`) for the same
element/section shortly after. The check very likely already ran to
completion; only the "done" acknowledgment got lost, not the work.

### Reproduction #5 — retried with Gen NX run as Administrator: same result

To rule out a permissions/UAC-related cause, the user closed Gen NX, relaunched
it with "Run as administrator," reopened the same natively-KDS-configured
model from reproduction #4, and re-ran the full analysis from the GUI before
retrying.

1. `perform_column_check` (`CC-ANAL`) on the same element (371) — the API call
   hung again, timing out client-side after 60s with no HTTP response
   (`MidasConnectionError: ... Read timed out`), and the Gen NX progress
   dialog stalled at "Converting Design Results... 0%" again, same as every
   prior reproduction.
2. The user waited briefly without clicking Stop, then clicked **Stop
   Execution** — the dialog closed and the app recovered cleanly, no forced
   process kill needed (matching reproduction #4's recovery behavior, not the
   forced-kill behavior of #1–#3).
3. `get_column_check_table` (`CC-TABLE`) for the same element immediately
   after — returned the identical full result set as reproduction #4
   (`CHK_STR: "OK"`, `CHK_RBR: "OK"`, `Rat_P: 0.468`, `28-6-D25`, ...),
   confirming the workaround holds here too.

**Conclusion: administrator privileges are not a factor.** The stall, the
Stop-Execution recovery path, and the CC-TABLE workaround are all identical
running elevated vs. running normally — this rules out a UAC/file-permission
explanation for the stuck dialog.

**Build/localization confirmed: this is the English/international build,
not a Korean-localized one.** All five reproductions were run against
**Gen NX 2026 v2.1, English version** — so the stall is not a
Korean-UI-localization artifact; it reproduces on the same build
international users install. What remains genuinely untested is the
**design-code axis**: every reproduction used **KDS 41 20 : 2022**
specifically. It's still an open question — not tested here — whether the
same "Converting Design Results 0%" stall occurs for non-Korean design
codes (AISC, Eurocode, etc., via `steel_kds.py` or other `design/*`
modules) or is somehow specific to the KDS check module's own
implementation. Don't generalize "every `perform_*_check` call hangs" past
KDS 41 20:2022 without independent testing of another code.

### `perform_wall_check` (WC-ANAL) — tested, does NOT reproduce the stall

Using a sixth session (a separate, wall-heavy Korean production model, KDS
41 20:2022 native, with pre-existing real wall-check results already present
from prior GUI use — `WID`/`Story`/`WallMark` rows like `101`/`B1`/`RW1`
with real `CHK_STR: "OK"` data), `perform_wall_check` was tested for the
first time:

1. Single wall/story (`SELECTIONS: [{"WALL_IDS": {"KEYS": [101]}, "STORY":
   ["B1"]}]`) — returned `{"message": "success"}` in **3.5s**. No stall.
2. All walls/stories (`SELECTIONS` omitted) — returned `{"message":
   "success"}` in **5.9s**. No stall.

**`WC-ANAL` does not reproduce the `CC-ANAL` stall**, at least on this
model, in either single-target or full-scope form. This is useful negative
evidence: whatever's stuck in the column-check "Design Thread" progress
dialog is not a blanket property of every `perform_*_check` function in
this file — it may be specific to `CC-ANAL` (or to the member-based
ELEMS/SECTIONS-targeted check family: beam/column/brace, vs. the
WID+STORY-targeted wall check, which may run through different internal
code entirely). Don't assume `perform_wall_check` carries the same risk as
`perform_column_check` going forward.

### `perform_beam_check` (BC-ANAL) — CONFIRMED to hang too, on two separate models, with a new crash variant

Same wall-heavy-model session, real beam rebar data already present
(`ModifyBeamRebarData` had entries for elements `11`, `12`, `13`). Walked
the same precondition sequence as the `CC-ANAL` reproductions:

1. `BC-ANAL` on element 11 before member type was registered in this
   design-code namespace — failed cleanly and fast: `{"error": {"message":
   "failed:Rebar"}}` (`ModifyMemberType.get()` was empty for this
   namespace even though rebar data existed — same "each precondition
   fails independently and cleanly" pattern as the column reproductions).
2. `ModifyMemberType.update({11: {"TYPE": "BEAM"}})` — succeeded.
3. `BC-ANAL` retried — failed cleanly: `{"error": {"message": " Please
   perform analysis."}}` (member-type change invalidated prior results,
   same as CC-ANAL reproduction #1/#4).
4. `doc.analyze()` via the API — **timed out after 90s** with no response.
   This one was just a genuinely long-running solve on this large model
   (4000+ nodes), not the progress-dialog bug — the user confirmed Gen
   NX's own progress UI was actively solving, not stuck. See the
   timeout-guidance note below. After the user re-ran analysis from the
   GUI and confirmed it completed, `BC-ANAL` was retried:
5. `BC-ANAL` retried a third time on element 11 — **hung again**, 60s
   client timeout, no HTTP response. This time the user reported the Gen
   NX app itself looked normal (no visible stuck dialog) — but
   `get_beam_check_table` (`BC-TABLE`) for that *same* element also then
   hung repeatedly (multiple retries, up to 30s each), while `BC-TABLE`
   for a different, nonexistent element (12 — actually absent from this
   model, confirmed by the clean fast `"Element 12 does not exist."`
   response) returned instantly. Basic connectivity (`GET /db/NODE`) also
   remained fully responsive throughout. This points to something
   specifically locked/stuck server-side scoped to *that element's* beam
   check state, even without a visibly stuck dialog — consistent with the
   "stuck signal, not a real deadlock" diagnosis, just manifesting without
   an obvious UI symptom this time.

A **second, independent model** was then opened to rule out anything
specific to the wall-heavy model: a real production Taiwan RC frame
("rahmen") structure, 315 nodes / 564 elements, active design code
`TWN-USD112` (not KDS — so, like reproduction #3, the KDS module's own
`MBTP`/`REBB` tables were empty and had to be populated directly, which
the API allowed with no validation against the model's "actual" active
code, consistent with prior findings):

1. `ModifyMemberType.update({1: {"TYPE": "BEAM"}})` (element 1, a real
   `TYPE: "BEAM"` element, section 11) — succeeded.
2. `ModifyBeamRebarData.update({11: {"ITEMS": [...]}})` (keyed by section
   number 11, matching element 1's `SECT`) — succeeded.
3. `doc.analyze()` — this model is much smaller; completed in **16.4s**,
   and a subsequent `get_reaction_table(load_case_names=["DL(ST)"])` call
   confirmed real, queryable results immediately (no large-model delay
   this time).
4. `ope.generate_load_combination_concrete({"OPTION": "ADD", "DGNCODE":
   "KDS 41 20 : 2022"})` — succeeded, generated a full set of KDS strength
   combinations (`cLCB1`..`cLCB7`+) from this model's real load cases
   (`DL`, `LL`, `EXN`, `EXP`, `EYN`, `EYP`, `EZ`, `WX`, `WY`).
5. `BC-ANAL` on element 1, all preconditions now satisfied on this fresh
   model — **hung again**, 60s client timeout, no HTTP response.
6. This time the user reported the exact text of the crash dialog for the
   first time — *"[Error] Failed to disconnect the work session due to an
   unidentified error. Since you have not logged out, other PCs may have
   limited access to the license. In order to properly terminate the
   program, try to re-execute the program, press 'New Project' and then
   close the program."* — and the application crashed/closed. **The user
   confirmed this is the same popup that appeared during the earlier
   forced-kill `CC-ANAL` reproductions (#1-#3)** — it just hadn't been
   transcribed verbatim before (previously logged generically as "an
   additional error popup"). **The user's stated rule: whenever this
   specific license-work-session-disconnect popup appears, the program
   always dies — there is no recovering from it.** This is a different,
   worse outcome than the clean "Stop Execution" recovery seen in
   reproductions #4/#5 (where this popup did not appear at all).

**This confirms `BC-ANAL` shares `CC-ANAL`'s hang, on two independent
models (one forced-KDS-setup wall-heavy Korean model, one forced-KDS-setup
Taiwan RC frame model), both under the same precondition pattern
(member-type + rebar assigned in the KDS namespace, a KDS-recognized load
combination present, confirmed-queryable analysis results).** Combined
with the earlier `CC-ANAL` reproductions, the observed outcomes now form
two consistent buckets rather than random variation: (a) the "Converting
Design Results" dialog gets stuck but recovers cleanly via Stop Execution,
no popup, no crash (`CC-ANAL` reproductions #4/#5) — the check likely did
finish and its results persist (confirmed via `CC-TABLE`); or (b) the
**"Failed to disconnect the work session"** license-error dialog appears
and the program crashes outright, unrecoverable (`CC-ANAL` reproductions 1
through 3, and this session's Taiwan-model `BC-ANAL` reproduction). This
raises the severity of the underlying MIDASIT bug report beyond "a stuck
progress bar" — outcome (b) is a licensing-visible crash that, per the
dialog's own text, may affect *other PCs'* access to the license until the
process is fully terminated.

### This exact crash signature has a prior precedent — it isn't new to v2.1

A separate, earlier round of live MIDAS Gen NX Open API testing (same
account, a different local project, pre-v2.1 build) independently hit the
**identical** `"Failed to disconnect the work session..."` crash text —
from a completely different trigger: calling `doc/new` rapidly and
repeatedly (back-to-back x10, concurrent x5/x15). That round's writeup
retested the `doc/new` trigger specifically against the v2.1 build and
found it **no longer reproducible**, and closed it out as resolved,
concluding the original crash was "limited to a previous build or a
specific sequence." **This session's `CC-ANAL`/`BC-ANAL` reproductions
show that conclusion was premature** — the same crash signature, verbatim,
resurfaces under a different trigger (a design-check "perform" call) in
the same v2.1 build. This is valuable context for framing a MIDASIT bug
report: not a one-off, but a recurring session-teardown defect that keeps
resurfacing under different trigger conditions across builds and across
independent testing sessions — worth reporting as a *class* of bug rather
than a single reproducible steps list tied to one endpoint.

**Useful diagnostic tool for next time**: that same earlier round
identified `GET https://moa-engineers.midasit.com:443/mapikey/verify`
(note: base URL with the product path — `/gen` or `/civil` — removed) as a
live-verified health-check endpoint, undocumented in the vendored manual,
that reliably distinguishes "AWS relay server alive, Gen NX process alive"
(`status: "connected"`) from "AWS relay alive, Gen NX process died"
(other endpoints then return HTTP 404 with `"Client Disconnected"` /
`"client does not exist"`, while `/mapikey/verify` itself still resolves
against the relay). This wasn't used during today's reproductions — relied
on the user's visual confirmation of the Gen NX window instead — but would
give a definitive, scriptable way to confirm process death vs. a merely
slow/busy session in future reproductions, without waiting on manual
screen-watching.

### `perform_wall_design` (WD-ANAL) — CONFIRMED to hang too, even though the sibling `perform_wall_check` (WC-ANAL) does not

Same wall-heavy model, same wall (`WID 101`, `Story B1`) already confirmed
clean under `WC-ANAL`. `perform_wall_design` (a *different* endpoint,
manual item #48, `WD-ANAL` — RC Wall **Design** Perform, distinct from
`WC-ANAL`'s RC Wall **Check** Perform, item #63) was tested for the first
time:

1. First attempt — failed cleanly and fast: `{"error": {"message": "
   Please perform analysis."}}`. Unrelated `steel_kds`/`src_aiksrc2k`
   member-type writes made earlier in this session (while probing whether
   other design-code modules share the `CC-ANAL` bug — see above)
   apparently invalidated the model's analysis results, consistent with
   the established "any design-parameter write invalidates results"
   pattern.
2. Re-ran `doc.analyze()` — completed in **151.3s** (large model, expected
   per the timeout-guidance note below, not a stall).
3. `WD-ANAL` retried on the same wall/story — **hung**, 60s client
   timeout, no HTTP response. The user checked Gen NX and reported the
   app looked completely normal — no visible stuck dialog this time
   either.
4. `get_wall_design_table` (`WD-TABLE`) for the same wall/story —
   **returned full, real design results** immediately (`Pu: 126.106`,
   `Rat-Py: 0.748`, `phiVn: 1804.81`, `Rat-V: 0.634`, real rebar
   `"D13 @300"`/`"D10 @190"`, `CHK: "OK"`). Same workaround as `CC-ANAL`:
   the design computation completed and persisted; only the HTTP
   acknowledgment never arrived.

**Separate schema finding, unrelated to the hang**: the manual documents
`WD-TABLE`'s response as `{"data": {"COMPONENTS": [...], "ROWS": [{col:
val, ...}, ...]}}` (with a worked example iterating `data["ROWS"]`), but
the live response above came back in the same `{"Result Table": {"FORCE":
..., "DIST": ..., "HEAD": [...], "DATA": [[...], ...]}}` HEAD/DATA shape
every other member-check table in this chapter uses. Confirmed by
re-reading the manual's own JSON Schema and worked example for this
endpoint side by side with the live response — this isn't a caller
mistake. `get_wall_design_table`'s docstring now flags this.

**This means the earlier "WID+STORY-targeted checks are safe" hypothesis
(based on `WC-ANAL` alone) was wrong** — `WD-ANAL` is also WID+STORY-
targeted and still hangs. The safe/unsafe split isn't about the targeting
scheme (`ELEMS`/`SECTIONS` vs `WID`/`STORY`); `perform_wall_check`
(`WC-ANAL`) remains the only tested "perform" function in this file so far
that does **not** reproduce the stall — `perform_column_check`,
`perform_beam_check`, and now `perform_wall_design` all do, across every
model tested. What distinguishes `WC-ANAL` from the other three is still
unclear — possibly that a wall "check" only reads/verifies existing rebar
against demand, while `WD-ANAL`/`CC-ANAL`/`BC-ANAL` all compute and
*write* new required-design data back into the model (rebar layout,
member-check parameter records) — but this is a hypothesis, not confirmed.

### Other design-code modules (steel_kds, SRC) — inconclusive, blocked by license/model limitations, not evidence either way

While looking for a fast way to test whether the `CC-ANAL`-style stall
extends beyond the RC-KDS module, two other design-code "perform check"
families were attempted on the same wall-heavy model and both were blocked
before reaching the actual "perform" call, for reasons unrelated to this
bug:

- **`steel_kds.perform_steel_code_check`**: blocked at the load-combination
  step — `ope.generate_load_combination_steel` returned `{"error":
  {"message": "There is no license to use the specified Steel Design
  Code."}}`. A real license limitation, not a bug; this account/model
  cannot exercise the steel design-check module at all.
- **SRC (`src_aiksrc2k`)**: the design code itself is licensed
  (`ope.generate_load_combination_src` succeeded), but `SrcBeamSectionData`
  (the rebar-equivalent registration for SRC composite beams) returned
  `{"error": {"message": "Unknown Error"}}` on every attempt, and
  `SrcModifyMaterial` writes didn't appear to persist (`GET` came back
  empty afterward). Likely cause: every section in this model is a plain
  rectangular RC shape (`SB`) — SRC (steel-reinforced-concrete composite)
  design plausibly requires an actual composite section geometry that
  doesn't exist anywhere in this model, unlike the RC-KDS rebar overlay
  which worked on any section regardless of the model's "real" design
  code.

**Neither result says anything about whether steel/SRC "perform check"
calls share the `CC-ANAL` stall** — both were blocked upstream of the
precondition chain this file's other reproductions establish as necessary
(member type + rebar/section data + recognized load combination +
queryable analysis results). Testing this properly would need a model with
real steel or SRC composite members, not a forced setup on an RC-only
model. Left as a genuinely open question.

### Timeout guidance for `doc.analyze()` on large models — a separate, milder finding

While waiting on step 4 above, it became clear a plain client-side read
timeout on `doc.analyze()` is not by itself evidence of a hang — on a
4000+ node model, analysis can legitimately take longer than
`MidasClient`'s default 30s timeout (observed: still running past 90s,
with the user confirming Gen NX's own progress UI showed it actively
solving, not stuck). **Don't conflate this with the `CC-ANAL` stuck-dialog
bug** — that one is confirmed via the message log to have a specific
"finished but dialog didn't update" signature; a slow `doc.analyze()` on a
big model is just... slow. Pass a larger `MidasClient(timeout=...)` for
big-model analysis calls rather than treating a timeout as failure.

**Practical takeaway for this SDK**: nothing to fix in `midas-nx` itself —
every request shape sent was correct per the manual (confirmed by the
clean, correctly-shaped `{"error": ...}` responses on every call that
didn't hang, across four separate reproductions on three different
models), and the SDK has no way to add a client-side guard against a
server-side dialog/signal bug it can't see. This is a confirmed,
reproducible Gen NX application defect worth reporting to MIDASIT
directly — most usefully framed as "the KDS column-check progress dialog
gets stuck at 'Converting Design Results 0%' even after the message log
shows the check completed, and the Open API call that triggered it never
receives a response either," together with this file's exact precondition
pattern (member-type + rebar assigned, plus a KDS-recognized design load
combination present, plus confirmed-queryable analysis results) —
reproduced 4 for 4 times that all conditions were met, across a trivial
synthetic model, a production-scale model (twice), and a natively
KDS-configured production model.

## Repeatable smoke test — `scripts/live_smoke.py` (2026-07-22)

Everything above was run by hand, one call at a time. This session turned
the core write → analyze → read round trip (new project, unit, material,
section, node, element, support, load case, self-weight, `doc.analyze()`,
reaction/displacement/beam-force tables, checked against a hand-calc) into
`scripts/live_smoke.py`, then ran it fresh against both a live Gen NX and a
live Civil NX session (same MIDASIT account, both freshly reset via
`/doc/NEW`). Both runs succeeded end to end and reported
`reaction_matches_hand_calc: true`. Confirmed builds (via each app's
About/도움말 dialog): **MIDAS Gen NX 2026 (v2.1), build 06/23/2026** and
**MIDAS Civil NX 2026 (v2.1), build 06/05/2026** — the same v2.1 line as
the English-build Gen NX used in the `CC-ANAL`/`BC-ANAL` reproductions
above, now with an exact build date on record for the first time.
`docs/coverage.json` now tags the ten endpoints this script exercises
(`/doc/NEW`, `/doc/ANAL`, `/db/UNIT`, `/db/MATL`, `/db/SECT`, `/db/NODE`,
`/db/ELEM`, `/db/CONS`, `/db/STLD`, `/db/BODF`) with a `"live_verified"`
field carrying this date and both builds; `ROADMAP.md` surfaces the count
and a Gen/Civil build matrix generated from it (PLAN.md's D4).

New findings from this run, beyond what's already recorded above:

- **The `/post/TABLE` response's top-level key is not stable across
  sessions.** Earlier findings in this file saw it as `"Result Table"`;
  this session got back the literal string `"empty"` for the same
  reaction/displacement/beam-force calls (with `table_name` left at its
  default `""`). Don't hardcode either key — `scripts/live_smoke.py`'s
  `_find_head_data()` scans the response's values for the first dict
  containing both `"HEAD"` and `"DATA"` instead, which is robust across
  whatever this key turns out to be call-to-call.
- **A 200 response can carry an `{"error": ...}` body even from a `DbResource.create()` call, and this is easy to miss if a caller only checks
  the HTTP status.** `live_smoke.py`'s first draft didn't check for this
  and silently treated a failed `Constraint.create()` as successful — the
  fix (checking for an `"error"` key in every 2xx body) is the same
  pattern already noted above for design-code "already exists" responses;
  worth treating as a general rule for every `DbResource`/`doc.*` call, not
  just the design-code family.
- **Gen's concrete `STANDARD` code for C24 is `"KS01(RC)"`, same as Civil**
  — confirmed by first trying the plausible-looking `"KS(RC)"` on Gen,
  which failed with `{"error": {"message": "Unknown Error"}}` (an
  unhelpful message with no hint about the actual problem being the
  standard-code string), then retrying with `"KS01(RC)"`, which succeeded
  immediately. The manual doesn't enumerate valid `STANDARD` strings per
  product, so — as with the original Civil finding above — this is a
  live-only data point, not a schema contradiction.
- **Physically-grounded cross-check, both products**: a 0.6×0.6 m, 3.2 m
  tall C24/KS01(RC) cantilever column's self-weight reaction came back as
  `FZ = 27.113426 kN` on both Gen and Civil (byte-identical, same model) —
  about 4% below a naive hand-calc using a generic 24.5 kN/m³ unit weight
  (`0.36 m² × 3.2 m × 24.5 ≈ 28.22 kN`), implying MIDAS's actual `C24`/
  `KS01(RC)` preset unit weight is closer to `27.113 / (0.36 × 3.2) ≈
  23.53 kN/m³`. Useful reference point for anyone else hand-calc-checking
  a KS01(RC) C24 model; `scripts/live_smoke.py` uses a 5% tolerance for
  exactly this reason rather than an exact-match assertion.

## STATUS UPDATE (2026-07-25) — `CC-ANAL`/`BC-ANAL` ran clean on the same build that hung

The `*-ANAL` design-check stall documented at length above — the single
most severe finding in this file, reproduced across three models and five
attempts, and the reason every `perform_*` docstring in `design/` carried a
"treat as a hang risk" warning — **did not reproduce in a later round of
live use.** Critically, this is **not** a "fixed in a newer build" story.

**Source of this finding.** Unlike the rest of this file, this did not come
from a dedicated SDK test session. It comes from *QuickRebar NX*
(`rebar-repair.vercel.app`), a separate production web tool by the same
author that drives the same Gen NX Open API endpoints over HTTP. Its own
project notes record a live re-test on 2026-07-25 that ran:

- `CC-ANAL` — including the whole-model `PERFORM_TYPE: "ALL"` variant, the
  exact shape that reproducibly killed the app in the reproductions above
- `BC-ANAL` — the beam equivalent, also previously confirmed to hang
- `WC-ANAL` — the wall check, which never reproduced the stall anyway

**4 out of 4 clean, with the app staying connected throughout.**
`PERFORM_TYPE: "ALL"` re-checks an entire model in roughly 2 seconds. The
tool now ships `BC-ANAL` wired to a user-facing "Gen NX 재검토" button,
followed by a `BC-TABLE` read of `CHK_STR` / `Rat-N` / `Rat-P` / `Rat-V` —
i.e. this is not a one-off lab result but an endpoint running in a
deployed tool against real users' models.

### ⚠️ The build did not change — so the trigger is still unidentified

The About dialog was checked on 2026-07-25 and reports **MIDAS Gen NX 2026
(v2.1), build 06/23/2026** — byte-for-byte the same build recorded for the
`CC-ANAL`/`BC-ANAL` reproductions above and for the 2026-07-22 smoke test.
**The same binary both hangs and does not hang.**

That rules out the most comforting explanation (a vendor patch) and leaves
the actual variable unknown. Plausible candidates, none of them tested:

- **Model state.** The reproductions established a precondition chain
  (member type + rebar + a *KDS-recognized* load combination, the last one
  generated via `ope.generate_load_combination_concrete` rather than a
  hand-written `/db/LCOM-GEN`) and hung at the exact point the check had
  enough real data to attempt the P-M calculation. Whether the QuickRebar
  models satisfied that same chain was never checked.
- **Call sequence.** The reproductions ran the check immediately after
  API-side writes of member-type/rebar data; the tool's flow may differ in
  ordering or in how much settles first.
- **Client/transport.** Python `requests` from a local machine vs. Node
  `fetch` from a Vercel serverless function — different timeouts and
  connection handling against the same relay.
- **Genuine intermittency in the trigger.** The defect was already known to
  be intermittent in its *consequences* (forced kill 3 of 5 times, clean
  "Stop Execution" recovery the other 2). Intermittency in the trigger
  itself was assumed absent, but four clean runs do not disprove it.

**Nothing in the reproduction sections above is retracted.** The correct
reading is "this is not universal and not always triggered," not "this is
fixed."

### What this does and does not license

| Endpoint | Earlier status (build 06/23/2026) | 2026-07-25 (same build) |
| --- | --- | --- |
| `CC-ANAL` (column check) | hung 5/5 | ✅ clean 4/4 |
| `BC-ANAL` (beam check) | hung on 2 models | ✅ clean |
| `WC-ANAL` (wall check) | never hung | ✅ still clean |
| `WD-ANAL` (wall **design**) | hung | ❓ **not re-tested** |
| `BRC-ANAL`, steel `CODE-ANAL`, SRC `*-ANAL`, `OCHECK` | never tested | ❓ **not re-tested** |

One further limit on the evidence: **KDS 41 20:2022 only.** Every test on
both sides of this — the original reproductions and the re-verification —
used the KDS RC design code. Nothing here says anything about the steel
(`steel_kds.py`), SRC (`src_aiksrc2k.py`), or non-Korean code paths.

### Keep the defensive pattern — this is now the main takeaway

Because the trigger is unidentified rather than removed, the defensive
pattern is not optional hygiene; it is the actual mitigation. The
production tool wraps these calls this way, and the SDK's docstrings
recommend the same:

- **Short timeout** on the `*-ANAL` call (the tool uses 25s).
- **Read the `*-TABLE` back regardless of whether `*-ANAL` returned.** This
  was the confirmed workaround during the hang era — a timed-out check had
  usually completed and persisted anyway — and it remains the correct shape
  for a call whose HTTP acknowledgment is known to be unreliable.
- **Prefer reading `*-TABLE` alone when possible.** Design results the user
  already computed in Gen NX's own GUI are readable with no perform call at
  all. That path never carried any of this risk and is still the zero-risk
  option.

### Why the docstrings kept the history

The `perform_*` docstrings in `design/` now lead with this re-verification
rather than the old "never call this" rule, but they retain a compressed
version of the reproductions. That is deliberate, and the same-build
finding above is why: this exact crash signature (`"Failed to disconnect
the work session..."`) has now resurfaced twice under *different* triggers
— once via rapid `doc/new` calls on a pre-v2.1 build, once via `*-ANAL` on
v2.1 — and was declared resolved after the first. Treating "did not
reproduce" as "fixed" is the mistake this file has already recorded once,
and the first draft of this very section repeated it by assuming a newer
build was responsible before the About dialog was actually checked.

## 2026-07-26 — read-only sweep reproduced on a real model, same build

Re-ran the whole GET surface with the new `scripts/live_readonly_sweep.py`
(read-only; safe against an open document, unlike `live_smoke.py`) against a
**real production model — 710 nodes, 1272 elements, 60 sections, with
analysis results already present** — on **the same build as the 2026-07-22
session** (Gen NX 2026 v2.1, build 06/23/2026).

| | 2026-07-22 (blank model) | 2026-07-26 (710-node model) |
|---|---|---|
| GET-capable Gen resources swept | 253 | 253 |
| Answered | 233 | 233 |
| Failed (all 404) | 20 | 20 |

Civil NX 2026 (v2.1), build 06/05/2026 was swept the same day and also
reproduced exactly — **293 swept, 273 answered, 20 404s**. The Civil session
had a near-empty document (2 nodes, 1 element), so unlike the Gen run it is a
same-conditions repeat, not a different-model one.

**The failing 20 are the same 20 endpoints**, all `MidasNotFoundError` 404:
the 13 Hyper-S `-M1` routes plus `CMCS`, `EWSF`, `PLCB`, `RCHK`, `SPAN`,
`STRPSSM`, `WVLD`. Run twice in the same session, byte-identical both times.

What this does and does not settle:

- **Model state is eliminated as an explanation.** The two sessions differ in
  everything about the document — empty vs. a real analyzed structure — and
  the failure set did not move by one endpoint.
- **License tier is not.** Same MIDASIT account, same license/edition, same
  build. Per this file's own caveat below, that is not yet the "different
  account" trigger, so **`PRODUCTS` was left unchanged** for the 7
  Gen-fails/Civil-succeeds classes. This section is the second data point;
  a third from a different account or license would be the one to act on.
- Results recorded per endpoint in `docs/coverage.json` (`live_verified`),
  taking the count from 10/390 to 235/390.

### Hyper-S is Civil NX only — the SDK's `PRODUCTS` was wrong

Running both products the same day made this unmissable:

| Hyper-S (`-M1`) endpoint family | Gen NX 2026 v2.1 | Civil NX 2026 v2.1 |
|---|---|---|
| Implemented `-M1` endpoints | 13/13 → **404** | 13/13 → **answered** |
| Undocumented `-M1` stubs | 8/8 → **404** | 8/8 → **answered** |

`/db/ACTL-M1` returned a populated row under Civil, not just an empty table,
so these are live routes rather than registered-but-inert ones.

**Confirmed by the project author**: Hyper-S is the name MIDASIT gave the
solver introduced with the Civil NX release. It is a Civil NX product
feature, so the Gen 404s were correct all along and the SDK's
`PRODUCTS = {"gen", "civil"}` was the defect. All 21 `-M1` rows (13
implemented + 8 stubs) are now Civil-only, via a dedicated `HYPER_S_ONLY`
constant in `db/base.py` and a parametrized guard in
`tests/db/test_hyper_s_products.py`.

**This one is expected to change again.** The author notes Hyper-S may reach
Gen NX in a future release. That is why it is its own constant rather than
`CIVIL_ONLY`: when it happens, widen `HYPER_S_ONLY` and re-run
`scripts/live_readonly_sweep.py --product gen` to confirm, instead of
treating the current state as permanent.

Note this changes the Gen failure accounting for the better. Of the 20 Gen
404s, 13 were never SDK-callable errors at all — they were Civil-only
endpoints the SDK wrongly offered to Gen clients. With `PRODUCTS` corrected,
a Gen sweep covers 240 endpoints with **7** unexplained 404s (`CMCS`,
`EWSF`, `PLCB`, `RCHK`, `SPAN`, `STRPSSM`, `WVLD`), and a Gen client now
raises `ProductMismatchError` before issuing a doomed request.

### The 8 "un-transcribable" Hyper-S stubs are introspectable after all

`docs/coverage.json` carries 8 `-M1` rows as `planned`, not implemented,
because the manual gives a URL, methods and a Zendesk link but no JSON
Schema — and this project's v1.0.0 gate has been waiting on exactly that.
Against a live Civil session, **all 8 answer a plain GET**, and 5 return a
field-level schema from `/info/db/...`:

| Endpoint | `/info/db/...` | Top-level fields |
|---|---|---|
| `/db/STYP-M1` | schema | `STYPE`, `GRAV`, `TEMP`, `ALIGNBEAM`, `ALIGNSLAB`, `MASS_CONTROL` |
| `/db/MATL-M1` | schema | `MATL_NAME`, `MATL_TYPE`, `DAMP_RAT`, `PARAM` |
| `/db/IMFM-M1` | schema | `CONCRETE`, `STEEL` |
| `/db/EPMT-M1` | schema | `NAME`, `MODEL_TYPE`, `TRESCA`, `VMISES`, `MOHRCL`, `DRUCKER`, `MASONRY`, `CONCDMG` |
| `/db/IEHG-BEAM-M1` | schema | `INEL_PROP_NAME` |
| `/db/IEHG-TRUSS-M1` | 404 | GET works, no schema route |
| `/db/IEHG-GL-M1` | 404 | GET works, no schema route |
| `/db/IEHG-PSS-M1` | 404 | GET works, no schema route |

`/db/STYP-M1` and `/db/MATL-M1` also returned real data (`{"STYPE": "3D",
"GRAV": 9.806, ...}`, `{"MATL_NAME": "C24", "MATL_TYPE": "CONC", ...}`).

This does not make them transcribed — server introspection is a different
source from the manual, and `DbResource.info()`'s docstring already frames it
as a fallback rather than a substitute. But the v1.0.0 gate's premise, that
these are "genuinely not transcribable without depending on an external,
non-versioned source", no longer holds: the server itself is the source, and
it is the same server the SDK talks to. Deciding whether that clears the gate
is a call for the author, not something this file should assume.

### The `{"message": ""}` zero-row shape is the common case, not an edge case

Of the 233 endpoints that answered, **176 returned `{"message": ""}` and only
57 returned the keyed `{"<KEY>": {...}}` shape** — on a fully populated model.
A zero-row table is the normal state for most endpoints because a given model
uses a small fraction of the API surface. This matters more than it looks:
`DbResource.items()` assumed the keyed shape and raised `AttributeError` on
the string value, so before v0.12.0 that helper failed on roughly three
quarters of the endpoints it was supposed to serve. Fixed in v0.12.0.

### `/post/TABLE`'s unstable top-level key, explained

Earlier sessions recorded the response key varying between `TABLE_NAME`,
`"Result Table"`, and `"empty"` with no known trigger. It is simply the
default: **omit or blank `TABLE_NAME` and the server keys the response
`"empty"`; pass a name and you get that name back.** Same call, same 78 rows
of real data, both ways:

```text
get_story_drift_table(STORY_DRIFT_X)                     -> keys=['empty'] rows=78
get_story_drift_table(STORY_DRIFT_X, table_name="Drift") -> keys=['Drift'] rows=78
```

`"empty"` is *not* an error marker — it carried a full table here. Matching on
shape (`post.base.unwrap_table()`, v0.12.0) remains the right approach, since
this doesn't explain the `"Result Table"` sighting, but "empty means no data"
is a wrong inference to guard against.

### HTTP 200 with an error body — reproduced deliberately

Sending an unknown `TABLE_TYPE` returns **HTTP 200** with:

```json
{"error": {"message": "MIDAS GEN NX there was an error creating utbl. (ex PostMode ...)"}}
```

This is the failure mode the client silently returned as a result until
v0.12.0; it now raises `MidasResultError`. Confirmed against the live server,
not just reasoned from the docs.

### Two practitioner traps found while probing

- **An invalid load-case name is not an error.** `get_reaction_table(
  load_case_names=["NoSuchCase(ST)"])` returned `{"message": ...}` with zero
  rows — after **23 seconds**. Nothing distinguishes "wrong case name" from
  "genuinely no results" in the response, so validate case names against
  `/db/STLD` before trusting an empty table.
- **Unfiltered result tables can exceed a sane timeout.** The beam-force
  table for all 1272 elements timed out at 30s; the same table filtered to a
  single load case returned 6350 rows in **2.2s**. The displacement table came
  back at 4.1 MB / 39760 rows. Pass `load_case_names` rather than raising the
  timeout.

## 2026-07-26 — write verification on Civil NX, and a table-destroying bug

First session with permission to create, modify and delete freely on Civil NX
2026 (v2.1), build 06/05/2026. `scripts/live_crud_check.py` was written for it:
create → read back → update → read back → delete → confirm gone, per resource.
Read sweeps prove an endpoint answers; only this proves the SDK's *write*
shapes are the ones the server accepts.

### 🛑 `DbResource.delete([id])` was deleting the entire table

The single most serious defect found so far, and it was invisible to every
mocked test in `tests/`.

```text
after create      : [1, 2, 3, 101]
after delete([101]): []              <- expected [1, 2, 3]
```

For `/db/NODE` this also takes out every element attached to those nodes, so
one `delete()` call empties a model. It surfaced by accident: the CRUD run
deleted one throwaway node, and the seeded model was gone afterwards.

**The SDK was following the manual exactly.** `03_DB_Node_Element.md` documents
`DELETE /db/NODE` with `{"Assign": {"4": None}}`, and `db/base.py` had reasoned
carefully about `None` vs `{}` across chapters. Both forms behave the same way
live, and neither one respects the ids:

| Request | Result |
|---|---|
| `DELETE /db/NODE` + `{"Assign": {"3": null}}` | table emptied |
| `DELETE /db/NODE` + `{"Assign": {"3": {}}}` | table emptied |
| `DELETE /db/NODE` + `{"Assign": {"2": {}, "3": {}}}` | table emptied |
| **`DELETE /db/NODE/3`** | **only node 3 removed, and returned** |

The per-id URL is undocumented — `db/base.py` explicitly declined to invent it
("no documented per-ID URL filtering across the manual, so we don't invent
one"). It works, and it is the only form that does what `delete()` claims.
Verified on `/db/NODE`, `/db/STLD`, `/db/LDGR` and `/db/MATL`; deleting an id
that doesn't exist is a harmless no-op returning `{"message": ""}`.

Fixed in v0.14.0: `delete()` issues one `DELETE {endpoint}/{id}` per id, and
the whole-table behaviour is kept under the name `delete_all()`.

### Two more "a 200 is not success" variants

v0.12.0 taught the client to reject a 2xx carrying `{"error": ...}`. Writing
turned up two cases that slip past it:

- **`/doc/ANAL` reports a failed solve as `{"message": "MIDAS CIVIL NX
  Analysis failed."}`** — the same `message` key a successful call uses for
  `"... command complete"`, with no `error` object anywhere. Every result table
  then comes back empty with nothing explaining why. `doc.analyze()` now
  inspects that message; the check is deliberately not in the client, since
  `message` is the normal success carrier elsewhere.
- **`/doc/SAVEAS` returns `{"message": "... command complete"}` for a save
  that did not happen.** Given a path NX rejects it raises a modal *"잘못된
  경로가 있습니다"* dialog, blocks the session until someone clicks it, and then
  answers with the success string. No file on disk. There is no way to tell
  success from failure from the response — check the filesystem.

Note also that error bodies arrive under **201** as well as 200
(`POST /db/CONS` → `201` + `{"error": ...}`), so any check keyed on the status
being exactly 200 misses them.

### `verify_connection()` cannot detect a blocked session

While a dialog was up, `/mapikey/verify` answered `{"status": "connected"}`
in milliseconds while every `/db/*` call timed out. The health check is served
by the relay, not by the blocked application. It tells you the process is alive
and the key is valid — it does not tell you the app can currently answer.

### Field-level findings from the round trips

- **`/db/CONS`'s `CONSTRAINT` must be exactly 7 characters.** Six is rejected
  outright; **eight is accepted and silently truncated to seven**, giving a
  support that was never requested with no error raised.
- **`/db/STLD` ignores the `"Assign"` key and renumbers.** Posting under key
  `7` produced record `2` (`NO: 2`), the next free slot. `/db/NODE` honours the
  key exactly (posting under `77` yields node `77`). So the ID-keyed convention
  is not uniform, and code that writes a record and then reads it back by the
  key it sent will miss for load cases.
- **`create()` is not an upsert.** Re-posting an existing key returns `201`
  with `{"error": ...}` "Key Already Exist".

Round-trip results: **Civil 10/10, Gen 9/9** (`/db/MVCD` is Civil-only and
correctly skipped there) across `/db/GRUP`, `/db/BNGR`, `/db/LDGR`,
`/db/NODE`, `/db/SKEW`, `/db/STLD`, `/db/CNLD`, `/db/BMLD`, `/db/CONS` and
`/db/MVCD` — all create/read/update/delete once the payloads above are right.
The four that failed on the first run were all bad test fixtures (deleted
prerequisites, a 6-character constraint), not SDK defects; that is worth
stating plainly, because a checker that cries wolf gets ignored.

The Gen run doubles as confirmation that the per-id delete fix works there
too, without needing a separate assertion: the `/db/CNLD`, `/db/BMLD` and
`/db/CONS` cases attach to seeded node 1, element 1 and node 2, and they run
*after* the `/db/NODE` case deletes node 101. Under the old whole-table
delete, that one call would have taken the seed with it and all three would
have failed — which is exactly how the bug was found on Civil.

## 2026-07-26 — `/doc/NEW` killed Gen NX once, and nothing explains it

> Read the follow-up sections before acting on this one. The framing here —
> that the old `doc/new` concurrency trigger had returned — did not survive
> testing, and every hypothesis raised below was subsequently eliminated,
> including by reopening the very model involved. The crash is real and the
> mitigation stands; the cause is unidentified.

A single `/doc/NEW` against **Gen NX 2026 (v2.1), build 06/23/2026** with a
real 710-node / 1272-element analyzed model open produced the license
work-session crash dialog and killed the application:

> `[Error] Failed to disconnect the work session due to an unidentified error.`
> `Since you have not logged out, other PCs may have limited access to the`
> `license. In order to properly terminate the program, try to re-execute the`
> `program, press 'New Project' and then close the program.`

The API side reported it correctly and immediately: `POST /doc/NEW -> 404:
Client Disconnected`, surfaced as `MidasNotFoundError`. No hang, no timeout —
the SDK's only involvement was issuing one documented call.

**This reopens a trigger this file had closed.** The section "This exact crash
signature has a prior precedent" records that the `doc/new` trigger was
retested against v2.1, found no longer reproducible, and closed out as
"limited to a previous build or a specific sequence". That conclusion is now
wrong twice over: it was already questioned by the `*-ANAL` reproductions, and
here the original `doc/new` trigger itself reproduces on the current build.

Two things are different from the earlier `doc/new` reproductions, and both
make this worse, not better:

- **It was one call, not a burst.** The earlier round needed back-to-back x10
  or concurrent x5/x15 to trigger it. This was a single request.
- **The document mattered.** `/doc/NEW` had been called perhaps a dozen times
  earlier the same day against small scratch documents on Civil NX with no
  incident. The one that crashed was the first against a large, analyzed,
  loaded-from-disk model.

That points at document teardown of a real model, not at call frequency. It is
one occurrence, so treat the size/state correlation as a hypothesis worth
testing deliberately rather than an established cause — but the "resolved"
label on the `doc/new` trigger should not be restored without a reproduction
attempt on a comparable model.

**Practical consequence, unchanged from the earlier findings:** once this
dialog appears the program always dies, and the license stays checked out
until the process is properly terminated — which per the dialog means
re-running the program, pressing New Project, and closing it cleanly. Do not
point `/doc/NEW` at a session holding a model that matters.

## 2026-07-26 — narrowing the `/doc/NEW` crash, and `/doc/SAVEAS` looks broken

### What the `/doc/NEW` crash is *not*

Four controlled runs against Gen NX 2026 (v2.1, build 06/23/2026), each
building the document through the API so only one variable moves:

| Document under `/doc/NEW` | Result |
|---|---|
| 2-node scratch | ✅ 3.1s |
| 710 nodes / 1339 elements, API-built | ✅ 3.6s |
| 750 nodes / 1300 elements, API-built, **solved, reactions readable** | ✅ 4.1s |
| 710 nodes / 700 elements, **saved then reopened from disk** | ✅ 4.1s |
| 710 nodes / 1272 elements, the user's real model, opened from disk, solved | 🛑 crash |

Four candidate causes tested and **all four eliminated**: the product being
Gen, model size, the presence of analysis results, and the document being
disk-backed. The last of those was the leading hypothesis after the first
three fell, and it did not survive contact with a controlled test — a document
saved via `/doc/SAVEAS` and reopened via `/doc/OPEN` tore down cleanly.

What still separates the one document that crashed:

- **Content, not size.** It carried 60 sections, 3 materials, structure and
  boundary groups, story data, load combinations, rebar data, and 190 design
  members each for RC/steel/SRC. Every test model had one material, one
  section and no design data at all.
- **Session history.** That session had served two full 253-endpoint read
  sweeps plus dozens of ad-hoc probes over several hours before the crash. The
  clean runs were minutes old.

Both are testable; neither is cheap, since each attempt costs a crash and a
license recovery. Recorded as the two surviving hypotheses rather than picked
between.

#### The session hypothesis, and why it is now the leading one

The project author proposed a mechanism for the second one that fits the
evidence better than anything model-side: **the server retains a record of the
existing session, and a later request is read as a second client connecting**,
so the session/licence layer refuses the teardown. Three things support it:

1. **The dialog only ever talks about sessions and licences.** It says nothing
   about the model — which is what you would expect given that four
   model-side variables have now been eliminated by experiment.
2. **The original documented trigger was literally concurrency.** The earlier
   pre-v2.1 round reproduced this crash with `doc/new` called *concurrently*
   x5/x15. That was filed here as an obsolete build-specific quirk; under this
   hypothesis it is the same defect seen from the other end, and the "resolved"
   label was hiding a mechanism rather than a fixed bug.
3. **NX runs on a separate machine**, reached through MIDASIT's relay, so
   there really is distributed session state to get out of sync — this was not
   understood when the earlier notes were written.

What does *not* yet fit: Gen and Civil were both connected on the same account
(`sjj0507@midasit.com`, distinct `connectionID`s) during the four clean
`/doc/NEW` runs as well as the crash, so two products sharing an account is
not sufficient on its own.

The one session-level difference that survives: the crashed session was the
**original long-lived connection** — hours old, two 253-endpoint sweeps and
dozens of probes deep — while every clean run happened on a freshly restarted
NX process minutes old.

#### Tested: the historical concurrency trigger does NOT reproduce

Run against a trivial empty document on the same build, reproducing the
pre-v2.1 pattern exactly, each phase followed by a health check:

| Phase | Result |
|---|---|
| 10 back-to-back `/doc/NEW`, no pause | 10/10 fine |
| **5 concurrent** `/doc/NEW`, separate clients | 5/5 fine (18.6s) |
| **15 concurrent** `/doc/NEW`, separate clients | 15/15 fine (59.5s) |

Session stayed healthy throughout, same `connectionID`, app responsive after
every phase. So **concurrency alone does not do it**, and the earlier round's
`doc/new`-burst trigger really does look fixed on v2.1 — the "resolved" label
was right about *that pattern*, even though the endpoint can still crash.

This corrects the framing in the section above, which read the single-call
crash as evidence that the concurrency trigger had returned. It had not. What
they share is the endpoint and the crash text, not the route to it.

Where that leaves the two hypotheses: the session-age one is weakened (an
idle-but-old session is still untested, but burst load on a fresh one is
clean), and **model content is now the leading candidate by elimination**.
Every clean run — including 30 `/doc/NEW` calls across these phases — was
against a document with one material, one section and no design data.

#### Tested: the model is innocent, and so is session load

The decisive test was run — the user reopened the exact model that crashed,
on the same build, same account, same machine:

```text
nodes 710 · elements 1272 · materials 3 · sections 60 · constraints 44
load cases 5 · load combos 6 · structure groups 3
RC design members 190 · beam rebar 31
    /doc/NEW -> {"message": "MIDAS GEN NX command complete"}  (3.7s)
    session survived
```

**No crash.** Model content is eliminated too.

Session load was then tested on its own: two full read sweeps back to back
(~480 calls) followed by `/doc/NEW` — the shape of what preceded the original
crash. Also clean, 4.5s.

So every variable isolated so far is eliminated:

| Hypothesis | Verdict |
|---|---|
| Product being Gen | ✗ |
| Model size | ✗ |
| Analysis results present | ✗ |
| Document loaded from disk | ✗ |
| Request concurrency (10 serial / 5 / 15 parallel) | ✗ |
| Model content (**the very model that crashed**) | ✗ |
| Accumulated session load (~480 calls) | ✗ |

#### What this most likely is

This now matches the pattern already recorded in this file for `CC-ANAL` /
`BC-ANAL`: reproducible five times out of five, then clean on the same build
with nothing changed. Two different endpoints, the same crash text, the same
inability to pin a trigger. Reading them as one intermittent defect in
**session teardown** explains more than any per-endpoint story does — and it
is consistent with everything eliminated above, all of which is about the
document rather than the session.

Untested combinations remain (rich model *and* heavy session load together —
yesterday's actual state; or wall-clock session age measured in hours rather
than call count). But the useful conclusion for this SDK does not depend on
resolving that:

- **Treat `/doc/NEW` and `*-ANAL` as calls that can kill the application**,
  regardless of what the document holds. There is no precondition to check.
- The mitigation is unchanged and is not going to improve: don't point them at
  a session holding work that isn't saved, and expect to restart the product
  and recover the licence when it happens.
- For a vendor report, the honest framing is a **class** of intermittent
  session-teardown failure across `/doc/NEW` and `*-ANAL`, with this file's
  elimination table attached to show what it is *not*. That is more useful
  than a steps-to-reproduce list nobody can run.

### 🧭 Every path in this API belongs to the machine running NX, not yours

The single most useful thing learned today, and it cost five failed
`/doc/SAVEAS` attempts to notice.

The API is reached through MIDASIT's relay at `moa-engineers.midasit.com`, so
the NX process answering your calls **may be on a different computer entirely**
— it was here. Every path-valued field is therefore resolved on *that* machine:

- `/doc/SAVEAS`, `/doc/OPEN`, `/doc/IMPORT*`, `/doc/EXPORT*`
- `EXPORT_PATH` on every `/post/TABLE` call and every design report/image call
- image capture paths in `/view/*` and `/ope/*`

Writing to `C:/Users/<your-windows-account>/Documents/...` fails when that
account exists only on your machine. The failure is quiet in the worst way:

| Path sent | Response | What actually happened |
|---|---|---|
| `C:/Users/Dennis/Documents/x.mgbx` (local account) | `command complete`, 58.2s | modal "invalid path" dialog on the NX machine, blocking until dismissed |
| `C:/Users/sjj0507/Documents/x.mgbx` (NX machine's account) | `command complete`, 0.4s | saved |

**Both answers are byte-identical.** The only signals are the latency — a
blocked dialog inflates it — and, decisively, whether the file is really
there. Checking `os.path.exists()` from the calling script proves nothing; it
is looking at the wrong filesystem. `/doc/OPEN` on the path you just wrote is
the check that works, since it asks the same machine.

The manual repo's `examples/javascript/auto-save-before-analysis.html` already
warns about this — *"%USERPROFILE% 같은 환경변수는 MAPI 서버(Gen NX 프로세스)가
인식하지 못합니다"* — and derives the folder from the account name in
`/mapikey/verify`'s `user` email (`sjj0507@midasit.com` → `sjj0507`). That is
the right pattern: **ask the server who it is, then build the path.**

Two corrections to earlier drafts of this file, kept because the reasoning
error is instructive:

- `/doc/SAVEAS` is **not** broken. It was writing files correctly the whole
  time, to a machine this script could not see.
- Its response is still not proof of success — but the reason is the dialog,
  not the endpoint.

Same lesson for `.mgbx`: the manual's example still shows the pre-NX `.mcb`,
and Gen NX 2026 writes `.mgbx`. That turned out not to be what was failing
here, but the example extension is stale regardless.

## 2026-07-26 (later) — 🛑 `POST /db/NMAS` kills Civil NX, deterministically

The first crash in this file with a **reproducible one-call trigger**. Read it
alongside the `/doc/NEW` section above, whose "cause unidentified, survives
every hypothesis" conclusion it partly supersedes: the license dialog those
sections treat as an unexplained session-teardown symptom can now be produced
on demand.

```text
POST /db/NMAS  {"Assign": {"3": {"mX": 1.0, "mY": 1.0, "mZ": 1.0}}}
```

Civil NX 2026 (v2.1), build 06/05/2026. Four reproductions, no exceptions.
The call times out, **every** subsequent `/db/*` call times out, and the
application raises

> [Error] Failed to disconnect the work session due to an unidentified error.
> Since you have not logged out, other PCs may have limited access to the
> license.

and exits — holding the license until the product is re-run, `New Project` is
pressed, and it is closed properly. A second dialog names it outright:
*"Program will be closed due to an unexpected problem."*

Where NX puts its crash-recovery file varies with the document, and one of the
two locations it chose is unusable. Twice it tried
`C:\Program Files\MIDAS\MIDAS CIVIL NX\DgnPlugIn\_restore.mcb` and was
refused, since a standard account cannot write there; on the fourth
reproduction it wrote to the user's `Downloads` folder successfully. So
auto-recovery is not universally broken here — but it fails silently in the
Program Files case, which is worth knowing before relying on it. That is an
install-level problem, separate from the crash.

### The three reproductions, and why the third one settles it

| # | Preceding activity | `/doc/NEW`? | Idle | Outcome |
|---|---|---|---|---|
| 1 | full `core` + `boundary` tiers; `/db/SDSP` create→update→delete completed immediately before | yes | none | died on `/db/NMAS` |
| 2 | `verify_connection`, `GET /db/NODE` (10 nodes), `GET /db/NMAS` (`{}`) | no | **~32 min** | died on `/db/NMAS` |
| 3 | `/doc/NEW`, seed model, `GET /db/NODE`, **control `POST /db/CNLD` (0.1s)**, `GET /db/CNLD` | yes | none — 20s-old session | died on `/db/NMAS` |
| 4 | `POST /db/NODE`, **`POST /db/SKEW`, `POST /db/CONS`**, `GET /db/NMAS`, `GET /db/NODE` — five calls at 0.08–0.17s each, all within the 1.3s before | **no** | none | died on `/db/NMAS` |

Two competing explanations were raised. Both are excluded by the table.

**An idle work-session timeout**, since a ~32-minute absence sat in front of
reproduction 2. It does not survive the evidence.

- In run 2 itself, **three `/db/*` calls succeeded after the idle gap** and one
  of them returned all ten nodes. Those are answered by the application, not
  the relay, so the work session was alive.
- The narrower variant — "the first *write* after a long idle is what dies" —
  is excluded by run 1, where `/db/NMAS` was nowhere near the first write:
  100+ calls including dozens of writes had already succeeded, and `/db/SDSP`
  had just completed a full round trip.
- Run 3 then removes the confound entirely: a 20-second-old session, a control
  write to a *sibling* static-load endpoint succeeding in 0.1s, then this one
  call taking the session down.

**A blocking save-changes dialog**, since `/doc/NEW` raises one on a document
with unsaved changes, and this file already records that any modal dialog
freezes the whole API session rather than the one call. Reproduction 4 was run
specifically to test it: **no `/doc/NEW` anywhere in the run**, so nothing
could raise that dialog, and it worked on node ids 9001/9002 so the open
document was left alone. Three writes and two reads returned in 0.08–0.17s
each inside the 1.3 seconds before the call — which also excludes a dialog
raised by anything else, because a modal would have frozen those five too.
`POST /db/NMAS` died exactly as before.

The dialogs that appear *afterwards* are consistent with the crash rather than
an explanation of it: NX raises the license and "unexpected problem" dialogs on
its way out.

`GET /db/NMAS` and `/info/db/NMAS` are unaffected. Nothing about the payload is
unusual — three unit masses on a plain seeded node — and `/info/db/NMAS` lists
exactly the fields being sent. **This is a product defect, not a wrong request
shape in this SDK.**

### `verify_connection()` reports "connected" throughout

Worth restating because it was measured twice in a row here, 0.5s each time,
while `GET /db/NODE` timed out at 15s in between. The health check is served by
the relay. It confirms the key is valid and the connection record exists; it
tells you **nothing** about whether the application can answer.

### What was done about it

- `NodalMassPayload` in `db/static_loads.py` carries the warning, with the
  recommendation to use `LoadsToMass` (`/db/LTOM`) where the mass can be
  derived from loads instead.
- `scripts/live_crud_check.py` **quarantines** the case: `Case.crashes` marks
  it, it is skipped by default and reported as `SKIP`, and running it needs an
  explicit `--include-crashers`. It is also last in its tier, so opting in
  costs only that one case rather than the seven that sat behind it in run 1.
- The checker now aborts the whole run the moment a failure looks like a lost
  session (`client does not exist`, or a read timeout) instead of grinding
  through the remainder. Run 1 spent two 30s timeouts and six 404s reporting
  "failures" against an application that had already exited.

Untested on Gen NX. Do not assume it is Civil-only, and do not assume it is
version-specific on this evidence alone.

## 2026-07-26 (later) — write verification, tiers 2-6: 40 of 43 cases confirmed

`scripts/live_crud_check.py` grew from 11 cases to 43, grouped into six tiers
ordered by what a modelling script actually reaches for. Confirmed live on
Civil NX 2026 v2.1 the same day: **40/43**, across five runs. The three that
are not confirmed each have a recorded reason, and none of them is an SDK
defect: `/db/NMAS` crashes the product, `/db/TDMT` refuses every payload
server-side, and `/db/TMAT` cannot be reached without `/db/TDMT`.

> Superseded later the same day, and the numbers below are the v2.1 state, not
> the current one. `/db/TDMT` was **not** refusing anything server-side — the
> `CODE` value was wrong; it and `/db/TMAT` both round-trip, taking this to
> **42/43** on v2.2. See the two later sections.

Newly proven round trips (create → read → update → read → delete → read):

| Tier | Endpoints |
|---|---|
| `props` | `/db/THIK` `/db/ESSF` `/db/SECF` `/db/TSGR` `/db/TDME` |
| `boundary` | `/db/NSPR` `/db/GSTP` `/db/GSPR` `/db/ELNK` `/db/RIGD` `/db/MCON` `/db/FRLS` `/db/OFFS` `/db/SSPS` — 9/9 first time out |
| `static` | `/db/SDSP` `/db/LTOM` `/db/NBOF` `/db/FBLD` `/db/PSLT` `/db/PRES` `/db/ETMP` `/db/NTMP` — 8/8 once `/db/NMAS` was quarantined out of the way |
| `stage` | `/db/STAG` `/db/TMLD` `/db/CRPC` `/db/CMCS` |
| `moving` | `/db/LLAN` `/db/MVHL` `/db/MVHC` `/db/MVLD` |

Still unconfirmed: `/db/NMAS` (quarantined, above), `/db/TDMT` (below) and
`/db/TMAT` (blocked by `/db/TDMT`).

The quarantine paid for itself immediately: the seven `static` cases that had
never been *reached* — they sat behind `/db/NMAS` in the crashed run, and were
never evidence of anything — all passed once it was skipped and moved last.
Six on the first attempt, `/db/PRES` after the fix below.

### 🛑 `/db/SECF` is keyed by section id, and the SDK said element id

`db/properties/section.py` documented `/db/SECF` ("Section Manager -
Stiffness") as keyed by element id. It is keyed by **section** id.

| Request | Response | Stored |
|---|---|---|
| `POST /db/SECF` `{"Assign": {"3": {...}}}` (element 3) | 200, no error | **nothing** |
| `POST /db/SECF` `{"Assign": {"1": {...}}}` (section 1) | 200 | the record, echoed back in full |

The wrong-key form is silent — no error object, no message, nothing to notice
except reading back and finding an empty table. Since this project's TypedDicts
are explicitly documentation rather than runtime validation, a wrong comment
here *is* the defect; corrected in the docstring, with the evidence.

The fixture found it on purpose: the case was deliberately keyed to element 3
with a note saying a "missing after write" failure would mean the key was a
section id, because the manual's worked example keys it `9001` right next to
`/db/STRPSSM`'s `9003`, and `/db/STRPSSM` *is* section-keyed.

### ⚠️ `/db/MVHL` silently downgrades a standard vehicle to a user-defined one

`VEHICLE_LOAD_NUM` must be `1` for a standard-DB vehicle. Send `2` and NX
**discards `VEHICLE_TYPE_NAME` and `STANDARD_CODE`** and stores a user-defined
"Truck/Lane" vehicle instead, with a 200 and no error:

```text
sent    {"MVLD_CODE": 6, "VEHICLE_LOAD_NAME": "KR(SRB)_DB-18",
         "VEHICLE_LOAD_NUM": 2, "VEHICLE_TYPE_NAME": "DB-18",
         "STANDARD_CODE": "KS-RB", "VEH_DEFAULT": {"DYN_LOAD_ALLOWANCE": 0, ...}}
stored  {"MVLD_CODE": 6, "VEHICLE_LOAD_NAME": "KR(SRB)_DB-18",
         "VEHICLE_LOAD_NUM": 2, "USER_LOAD_TYPE": "Truck/Lane",
         "VEH_DEFAULT": {"UNIFORM_LOAD": 0, "PL": 0, "PLM": 0, "PLV": 0}}
```

With `VEHICLE_LOAD_NUM: 1`, `DB-18`, `DB-24` and `DL-24` all store correctly
under `STANDARD_CODE: "KS-RB"`. This joins `/db/CONS` truncating an 8-character
`CONSTRAINT` and the empty-`VEH_DEFAULT` no-op as a **silent data-corruption**
shape: the only defence is to read the record back and compare.

Also resolved: `/db/MVHC`'s `VEHICLE_LD_NAMES` takes the vehicle's
`VEHICLE_LOAD_NAME` (`"KR(SRB)_DB-24"`), not the type name (`"DB-18"`) the
manual's worked example shows.

### ⚠️ `/db/PRES`'s documented default `DIRECTION` is rejected

`DIRECTION` is documented (manual and SDK alike) as defaulting to `"NORMAL"`.
On a 4-node PLATE with `FACE_EDGE_TYPE: "FACE"` — the commonest pressure load
there is — Civil NX 2026 v2.1 rejects it:

```text
[Error] Errors detected in Pressure Loads Data.(Item:Load Direction)
```

**Omitting `DIRECTION` fails identically**, which confirms the default is
applied and the default is unusable. Working values on that same element:

| `DIRECTION` | Result |
|---|---|
| `LZ` (element local z — normal to the plate), `LX`, `GZ` | accepted |
| `VECTOR` with `VECTORS: [0, 0, -1]` | accepted |
| `NORMAL` | `(Item:Load Direction)` |
| `NORMAL_PLANE`, `NORMAL_ELEM`, `GLOBAL_Z`, `LOCAL_Z` | `Wrong Field` |

The two error strings separate the cases again: `"NORMAL"` earns the specific
"Load Direction" complaint rather than the generic `Wrong Field` that the
invented spellings get, so it *is* a recognised enum value — presumably valid
for some other `ELEM_TYPE`/`FACE_EDGE_TYPE` pair. For plate faces, pass `"LZ"`.

Two smaller notes from the same endpoint: the server echoes `FORCES` back with
five entries where the manual's example sends four, and `/info/db/PRES` gives
its `maxItems` as 5; and `/info/db/PRES` carries a `PSLT_KEY` field (a
`/db/PSLT` reference) that the manual chapter does not document.

Also on `/db/PSLT`: the manual spells `ELEM_TYPE` `"Plate/PlaneStress(Face)"`
in its worked example and `"Plate/Plane Stress (Face)"` in its Specifications
prose. This section originally concluded the unspaced form was "the one the
server accepts" — **that was wrong**, and it was inferred from the CRUD case
passing with the unspaced form without ever sending the spaced one. Both are
accepted (checked on v2.2, see the final-verification section). The manual's
inconsistency is cosmetic.

### ⚠️ The manual's only documented time-dependent-material code name is rejected

`"KDS2016"` — the value in the manual's worked example, its Python example and
its `NAME` field for both `/db/TDMT` and `/db/TDME` — is not accepted by Civil
NX 2026 v2.1. Probed against `/db/TDME`:

| `CODENAME` | Result |
|---|---|
| `CEB-FIP(2010)`, `CEB-FIP(1990)`, `Ohzagi` | accepted |
| `ACI` | accepted **once `A`/`B` are supplied** |
| `KDS2016`, `KDS(2016)`, `KDS`, `KCI-2007`, `Korea Standard` | `Wrong Field` |
| `KDS-2016` | recognised, but still rejected even with `A`/`B` |

The two error strings are diagnostic and worth knowing:

- `"Wrong Field"` — the code name is not one the product knows.
- `"[Error] Time Dependent Material(Comp. Strength) input data contain errors."`
  — the name *was* recognised; the code's own conditional fields are missing.

### ⚠️ `/db/TDMT` looked server-side broken and was not — see the correction below

Recorded as written at the time, because the reasoning error is the useful
part. `/db/TDMT` answered `201` + `{"error": {"message": "Wrong Field"}}` to
the manual's worked example, to every code name `/db/TDME` accepts, to each
documented field removed in turn, and to a bare `{"NAME": "C"}`; `PUT`
behaved the same; `/info/db/TDMT` listed every field being sent; and an
`{"Argument": ...}` body was refused with a *different*, correct error. From
that this file concluded "looks server-side".

That conclusion was wrong. Nothing about it was server-side — the `CODE` value
was simply not one this endpoint accepts, and "Wrong Field" is what it says
when it cannot resolve `CODE`. Resolved further down: **"Wrong Field" from
these endpoints means the code name is unknown, not that a field name is
wrong**, and the message being about "Field" is actively misleading. The
lesson worth keeping: an exhaustive-looking elimination sweep over the fields
proves nothing when the bad value is in a field you never varied.

### Fixture design rules, and why they earned their keep

Two rules, both paid for by the first run:

1. **Seed at the lowest free key, let the case take the next one.** Definition
   tables disagree about honouring the `"Assign"` key — `/db/NODE` honours it,
   `/db/STLD` and `/db/TDME` renumber to the next free slot (posting `/db/TDME`
   under keys 10/15/16/18 produced ids 1/2/3/4). Seeding first and taking the
   next sequential key makes both behaviours land on the same id. Where a
   record is referenceable by name — groups, spring types, lanes, vehicles —
   the fixtures use the name and the question never arises.
2. **Seed steps are per-case dependencies, not per-tier.** The first run
   blocked all 7 `props` cases behind the one `/db/TDMT` seed failure, though
   only `/db/TMAT` needed it. Four of those seven pass. A checker that reports
   6 false blockages out of 7 gets ignored, which is the whole point of
   separating **regression** (a confirmed case broke → SDK defect suspect,
   exit 1) from **unverified** (never passed → triage the fixture, exit 3)
   from **blocked** and **skipped**.

The classification held up: across three runs every single failure resolved to
a fixture defect, a documented-value defect, or a product defect — and none to
an SDK behaviour defect. The one SDK defect found was a wrong docstring
(`/db/SECF`), which no amount of round-tripping would have caught if the case
had been keyed correctly by accident.

## 2026-07-26 (later still) — Civil NX v2.2: nothing changed

The user upgraded to **MIDAS Civil NX 2026 (v2.2), build 06/18/2026** — a
version bump, not a reinstall of the crashing build — and the whole checker
was re-run against it.

### The 40 confirmed round trips are unchanged

`live_crud_check.py --product civil` gave a byte-identical verdict on v2.2:
**40/43**, zero regressions, the same three exceptions. That is worth having
on its own — it is the first evidence in this project that the SDK's write
shapes survive a Civil NX version change, and the endpoints in
`docs/coverage.json` now cite v2.2 as their verified version. (The same 40
passed on v2.1 build 06/05/2026 earlier the same day; the `nx_versions` field
holds one build per product, so it names the newer one.)

### 🛑 `/db/NMAS` reproduction #5 — the upgrade did not fix it

Same protocol as reproduction #4, deliberately: no `/doc/NEW` anywhere in the
run, control writes immediately before, node ids 9001+ so the open document is
untouched.

```text
[  0.6s] OK    POST /db/NODE 9001-9005 (fixture)      (0.11s)
[  0.7s] OK    CONTROL POST /db/SKEW 9001             (0.11s)
[  0.8s] OK    CONTROL POST /db/CONS 9002             (0.11s)
[  0.9s] OK    CONTROL GET  /db/NODE  (t-0)           (0.08s)
[ 15.9s] FAIL  POST /db/NMAS 9001                     (15.01s)  read timeout
[ 31.4s] FAIL  GET  /db/NODE                          (15.47s)  read timeout
```

The probe was written to keep going if the call had survived — five more
`POST`s, a `PUT`, a `DELETE` and a read-back — precisely so that a clean
result would not rest on one lucky call. It never got there.

**This is now five reproductions across two versions.** It matters because of
the precedent this file already records: `CC-ANAL`/`BC-ANAL` were reproducible
five times out of five and then ran clean on the *same* build with nothing
changed, and `/doc/NEW`'s crash never got a trigger at all. `/db/NMAS` is not
that. It is deterministic, it is one call, the payload is three unit masses on
a plain node, and a vendor version bump did not touch it.

Practical consequence: **do not wait for this to be fixed by upgrading**, and
the vendor report is worth actually sending — see the crash section above for
the evidence to attach.

### `/db/TDMT` is not version-specific either

Still `201` + `{"error": {"message": "Wrong Field"}}` on v2.2, for the manual's
own worked example. Whatever is wrong with that endpoint survived the same
upgrade, which removes "stale build" as an explanation and makes it worth
reporting alongside the crash rather than sitting on it.

## 2026-07-26 (later still) — `/db/TDMT` solved: the code-name enums differ

`/db/TDMT` and `/db/TDME` sit next to each other in chapter 04, take a code
name each, and **do not share a code-name enum.** That is the whole answer, and
it cost most of a session to find because a `Wrong Field` error pointed at the
fields rather than at the value.

Probed live on v2.2 with the CEB-FIP field set (`MSIZE`/`CTYPE`) and the ACI
field set (`VOL`/`CMETHOD`), 16 candidate names each:

| `CODE` on `/db/TDMT` | Result |
|---|---|
| `European` | accepted with either field set |
| `AASHTO` | accepted with either field set |
| `ACI` | accepted with `VOL`/`CMETHOD` |
| `Russian` | recognised — "input data contain errors", so it wants other fields |
| `CEB-FIP`, `CEB-FIP(2010)`, `CEB-FIP(1990)`, `CEB-FIP(1978)`, `CEB FIP` | `Wrong Field` |
| `Ohzagi`, `KDS-2016`, `KDS2016`, `Korea`, `KCI-USD12`, `JTG3362-2018` | `Wrong Field` |

So **MIDAS calls the CEB-FIP-based creep/shrinkage model `"European"` on this
endpoint**, and every CEB-FIP spelling is rejected — while `/db/TDME` accepts
`CEB-FIP(2010)`/`CEB-FIP(1990)`/`Ohzagi` and rejects `European`-flavoured
guesses. The manual's chapter blurb for `/db/TDMT` — "CEB-FIP(2010/1990/1978),
ACI, KDS 등" — describes a set of names the endpoint does not take. Stored
records come back with `CODE` upper-cased (`"European"` → `"EUROPEAN"`).

The two error strings are the same diagnostic pair seen on `/db/TDME`, and they
are the fastest way to triage this class of endpoint:

- `"Wrong Field"` → the **code name** is unknown. Vary the value, not the fields.
- `"[Error] ... input data contain errors."` → the name is recognised; the
  code's own conditional fields are missing or wrong.

With `CODE: "European"`, `/db/TDMT` round-trips, and `/db/TMAT` — which links a
`/db/TDMT` and a `/db/TDME` record **by name** — round-trips after it. That
takes the checker to **42/43 confirmed**, leaving only the `/db/NMAS` crash.

One more self-inflicted fixture defect on the way there, worth recording
because it is the exact rule this file lays out two sections up: `/db/TMAT`'s
update pointed `TDMT_NAME` at `TDMT_CRUD`, the record the `/db/TDMT` case
creates *and deletes*, so the update earned a `Wrong DB Name` for a reason that
had nothing to do with `/db/TMAT`. Fixed by seeding two creep/shrinkage records
(`TD_SEED`, `TD_SEED_2`) that outlive the tier and switching between them.

### What this changes about the vendor report

`/db/TDMT` comes **off** the product-defect list and moves to the manual team:
the endpoint works, its documented code names don't. What is worth reporting as
a product-side issue is the error text — `"Wrong Field"` for an unrecognised
*value* sends the reader to inspect field names, which is what happened here.

## 2026-07-26 (later still) — v2.2 re-check of the v2.1-only findings

Three findings had only ever been seen on v2.1 (build 06/05/2026) and were
about to be sent to MIDASIT on that basis. Re-run on v2.2 (build 06/18/2026)
before sending. Two hold, one does not.

| Finding | v2.1 | v2.2 |
| --- | --- | --- |
| `/db/CONS` silently truncates an 8-character `CONSTRAINT` to 7 | reproduces | **reproduces** |
| `DELETE {endpoint}` + ID-keyed `"Assign"` empties the whole table | reproduces | **reproduces** |
| `/db/MVHL` no-ops on an empty `VEH_DEFAULT: {}` | reproduces | **does not reproduce** |

### `/db/CONS` — and the response lies too

The truncation is unchanged, and re-checking it turned up something the
original write-up missed: **the POST response echoes the 8-character string
back**, while the stored record holds 7.

```text
POST /db/CONS {"Assign": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}}
  response -> {"CONS": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}}   8 chars
  GET      -> {"3": {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "CONSTRAINT": "1111111"}]}}   7
```

So the immediate response cannot be used to detect it either — a separate GET
is the only signal. Six characters is still rejected outright, so the asymmetry
is the real complaint: too short errors, too long is silently cut.

### `DELETE` — measured on v2.2, and it is as bad as recorded

```text
before  NODE 10, ELEM 4
        DELETE /db/NODE {"Assign": {"21": null}}     one node named
after   NODE 0,  ELEM 0                              the model is gone

before  STLD ['1', '2']
        DELETE /db/STLD {"Assign": {"1": {}}}        one load case named
after   STLD []

        DELETE /db/NODE/502                          the per-id form
        -> {"NODE": {"502": {...}}}, 501 and 503 untouched
```

One detail worth having: the response body returns **every** record it deleted,
so the response does reveal the over-deletion — after the fact. `delete()`
already uses the per-id URL, so nothing changes in the SDK.

### `/db/MVHL`'s empty `VEH_DEFAULT` — fixed, so it comes out of the report

On v2.2 the record saves and `VEH_DEFAULT` comes back populated with
`{"DYN_LOAD_ALLOWANCE": 0, "CENT_F": false}` — the product now fills the
defaults instead of discarding the write. Removed from the vendor report's
silent-write-failure list, since sending a claim that does not reproduce on the
current build costs credibility for the ones that do; kept in the report's
appendix as a note that it appears resolved, and the `VehicleDefaultParams`
docstring now scopes the warning to v2.1.

This is the argument for re-checking before reporting rather than after: the
same sweep that confirmed two findings retired a third and sharpened one of
the two.

## 2026-07-26 (final) — every vendor-report claim re-checked in one pass

Before sending anything to MIDASIT, all 16 claims were re-run against a single
v2.2 session (build 06/18/2026) **in ascending order of severity** — the
documentation items first, then the response conventions, then the silent
write failures, then the destructive `DELETE`, and the crash last. Ordering it
that way matters: the crash ends the session, so anything after it would go
unverified.

**14 of 16 reproduced.** The two that did not are the useful part.

### ❌ Retracted: `/db/PSLT`'s `ELEM_TYPE` spelling was never a defect

Both `"Plate/PlaneStress(Face)"` and `"Plate/Plane Stress (Face)"` are
accepted. The earlier claim that only the unspaced form works came from the
CRUD case passing with that form — the spaced form was never sent. That is an
inference dressed up as a finding, and it is exactly the failure mode this file
already records for `/db/TDMT`: **do not conclude anything about an enum from
one value working.** Removed from the vendor report.

### ⚠️ `A-4` failed its own check, not the claim

The assertion required two probes to both return an error body, and one of them
(`POST /db/CONS` with a 3-character `CONSTRAINT` on a node that does not exist)
returned `201` with no error at all. The claim itself is confirmed by the other
probe — `POST /db/TDMT` → **`201`** + `{"error": {"message": "Wrong Field"}}` —
and by `PUT /db/TMAT` → **`200`** + `Wrong DB Name` earlier the same day. Bad
test, good finding; the report's example list was corrected rather than the
claim.

That stray `201`-with-no-error on a nonexistent node is itself suspicious as
another silent no-op, but it was not checked with a follow-up GET and is not
claimed anywhere.

### `/mapikey/verify` is stale, not permanently wrong

Worth correcting because the report said it reports `"connected"` for a dead
application. It does — but not forever. Measured immediately after two crashes:
`"connected"`. Measured after this crash, roughly 30 seconds later and after
two 15s timeouts had elapsed: **`"disconnected"`**. So the relay's connection
record catches up; there is a window in which it lies. The report now says
that instead.

### Confirmed unchanged on v2.2

`/db/TDMT`'s code-name enum (B-1), `/db/TDME`'s (B-2), `/db/SECF`'s section
key (B-3), `/db/PRES`'s rejected `"NORMAL"` default and its 5-entry `FORCES`
(B-4, B-7), `/db/MVHC`'s `VEHICLE_LD_NAMES` — which rejects a vehicle *type*
name with `Unknown Error` (B-5) — `/db/STLD`'s renumbering, where a POST under
key `7` produced id `3` (B-6), the `"Wrong Field"` vs "input data contain
errors" split (A-6), all three silent write failures (A-3a/b/c), `DELETE`
emptying `/db/NODE` from 10 nodes and 4 elements to zero from a single named id
(A-2), the per-id form working correctly (A-2b), and **`POST /db/NMAS` killing
the application — reproduction #6** (A-1), with the three control calls
immediately before it all returning normally.

## 2026-07-27 — 🛑 four of the seven "documentation defects" were **ours**, not MIDASIT's

Before sending the vendor report, every B-item was re-checked against the
**official Zendesk articles** (`support.midasuser.com`, JSON Manual section
`30087500371097`) fetched that day — not against `E:\AI Study\MIDAS-API`.
That distinction is the whole finding. The vendored manual is a *curated
transcription*; section B had been written against it, so wherever the
transcription was wrong, we were about to accuse MIDASIT of our own error.

**B-1 `/db/TDMT` `CODE` — retracted.** The official article
([Creep/Shrinkage](https://support.midasuser.com/hc/en-us/articles/35808006330009))
documents a complete, exact 28-value enum: `CEB_FIP_2010`, `CEB`,
`CEB_FIP_1978`, `ACI`, `PCA`, `COMBINED`, `AASHTO`, `JSCE_12`, `JSCE_07`,
`JSCE`, `JAPAN`, `INDIA_IRC_18_2000`, `INDIA_IRC_112_2011`, `EUROPEAN`,
`AS_5100_5_2017`, `AS_5100_5_2016`, `AS_RTA_5100_5_2011`, `AS_3600_2009`,
`NEWZEALAND`, `RUSSIAN`, `CHINESE`, `JTG`, `CHINA_JTG3362_2018`, `KDS_2016`,
`KSI_USD12`, `KSCE_2010`, `KS`, `USER_DEFINED`.

The 16 values swept on 2026-07-26 were **`NAME` values read as `CODE` values**.
In the official example, `"NAME": "CEB-FIP(1990)"` sits directly above
`"CODE": "CEB"` — `NAME` is the free-text label, `CODE` is the enum. Every
"rejected CEB-FIP spelling" recorded above was a string the official article
never proposes for that field. `"European"` was not a discovery; `EUROPEAN`
is documented, and the match is case-insensitive.

**B-2 `/db/TDME` `CODENAME` — retracted.** The official article
([Compressive Strength](https://support.midasuser.com/hc/en-us/articles/35808102389401))
gives `"KDS-2016"`. `"KDS2016"`, the value probed and reported as rejected,
appears in **neither** official article — it is a vendored-copy error.

So the two endpoints do differ, and interestingly: `/db/TDMT` takes
`UNDERSCORED_UPPERCASE` tokens, `/db/TDME` takes the display string
(`CEB-FIP(2010)`, `KDS-2016`, `European`). Both are documented correctly and
in full. That the SDK's own seeds already use `CODENAME: "CEB-FIP(2010)"` and
pass live is confirmation, not coincidence.

**B-3 `/db/SECF` — retracted.** The official article is titled *Section
Manager - Stiffness* and never states what the `"Assign"` key means; it just
uses `9001`/`9002` as example keys. "Keyed by element id" was **our own
docstring**, already corrected in `db/properties/section.py`. The live finding
(section id is the right key) stands; the accusation does not.

**B-7 `/db/PRES` — retracted.** The official Specifications row reads
`"FORCES"  Array [Number, 5]`, and all four official examples carry five
entries. `PSLT_KEY` **is** present in the official JSON Schema. Both halves
described the vendored chapter, not the source.

**B-4 `/db/PRES` `DIRECTION` — narrowed, not retracted.** Footnote ¹⁾ of the
official article carries an availability matrix that documents the live
behaviour exactly: for `"PLATE"` + `"FACE"`, Normal is `-` while Local x/y/z,
Global X/Y/Z and Vectors are `O`. What survives is much smaller: the
Specifications row still marks `DIRECTION` *Optional, default `"NORMAL"`*,
which cannot hold for the one combination where `NORMAL` is unavailable —
hence omitting the field fails.

**B-5 and B-6 stand**, B-6 rephrased as an omission: the official `/db/STLD`
article marks `"NO"` *Read Only* and never says what the `"Assign"` key does,
so renumbering contradicts no published statement — it is undocumented, which
is a weaker and more accurate claim.

### The rule this produces

**Never cite the vendored manual as "the documentation" in anything sent
outside.** It exists to be corrected; `E:\AI Study\MIDAS-API`'s own CLAUDE.md
says it deliberately normalizes official typos and marks them `⚠️`. For an
internal decision it is the right source. For a claim *about MIDASIT's
documentation*, fetch the article and quote it. Four of seven claims died on
contact with the source, and the two that survived got weaker.

Still open: a live re-test with the official values (`CODE: "CEB_FIP_2010"`,
`"KDS_2016"` on `/db/TDMT`; `CODENAME: "KDS-2016"` on `/db/TDME`). It was not
possible on 2026-07-27 — the relay answered `client does not exist`, no
session. The retractions do not depend on it (dropping an unverified
accusation is the safe direction), but if any official value *does* fail,
that is a genuine product defect and a new A-item.

## 2026-07-27 (later) — Gen NX v2.1 (build 07/28/2026): `props`/`boundary`/`static`/`stage` get their first Gen CRUD run, `/db/CMCS` corrected to Civil-only

New Gen NX install, new MAPI key, `scripts/live_crud_check.py --product gen`
(no `--include-crashers`). **Correction to get right before it goes stale:**
this was not the checker's first exposure to Gen NX — the `core` tier's own
comment already says "the baseline proven live on 2026-07-26 (Civil 10/10,
Gen 9/9)", and that 2026-07-26 Gen pass is what let `/db/TDMT` and
`/db/TDME` inherit `confirmed=True` in the first place. What today actually
added: the **`props`, `boundary`, `static` and `stage` tiers ran against Gen
for the first time** (27 endpoints), on top of `core` repeating clean. Of
those, `/db/TDMT`/`/db/TDME` are worth calling out specifically — they use
the seeds already fixed in the 2026-07-27 section above
(`CODE: "European"`, `CODENAME: "CEB-FIP(2010)"`), so this is the first
live confirmation of those *specific* values on a Gen session, not just
Civil. `/db/NMAS` stayed quarantined; not run.

First pass: 36/38 confirmed cases passed. **`/db/CMCS` came back a
REGRESSION** — `confirmed=True` in the checker, but that flag was earned on
Civil NX runs only; the `stage` tier had never touched Gen before today.
Before treating it as an SDK defect: `/db/CMCS` is one of the 7 endpoints
already flagged twice in this file (2026-07-22, 2026-07-26) as "manual says
gen+civil, but 404s under Gen in practice" — and both those were GET-only
read sweeps, deliberately left unactioned pending a third, independent data
point per this file's own caveat.

This run is that third point, on a different session (new build, new day)
and with **stronger evidence than either prior one** — an actual `POST`
attempting to create a record, not just a `GET` against an empty table. Same
account as before (`sjj0507@midasit.com`), so it doesn't clear the
stricter "different account" bar floated in the 2026-07-26 section, but it
does satisfy the caveat's actual rule below ("different session" is listed
as sufficient), and three same-account reproductions across five days and
three separate sessions is not a coincidence worth waiting out further.

**Action taken:** `CamberConstructionStage.PRODUCTS` changed from
`{"gen", "civil"}` to `CIVIL_ONLY` in `db/construction_stage.py`, the
`live_crud_check.py` case given `products=("civil",)` so a future Gen run
skips it instead of false-flagging, and its mocked test switched from
`gen_client` to `civil_client`. The other 6 endpoints in that original list
(`EWSF`, `PLCB`, `RCHK`, `SPAN`, `STRPSSM`, `WVLD`) are **not** touched —
none of them are exercised by `live_crud_check.py`, so this run adds no new
evidence for them. They stay at two data points, per the caveat.

**Re-run after the fix: 36/37, clean — 0 regressions, 0 unverified failures,
0 blocked**, `/db/CMCS` correctly filtered out for a Gen client rather than
skipped-and-counted. `docs/coverage.json` updated in bulk for all 36 passing
endpoints: `live_verified.products` gained `"gen"`,
`live_verified.nx_versions.gen` set to `"MIDAS Gen NX 2026 (v2.1), build
07/28/2026"`, date bumped to 2026-07-27. `/db/CMCS`'s own entry instead
dropped `"gen"` from top-level `products` (now `["civil"]`, matching
`PRODUCTS`) and its `live_verified` note records the three-session Gen 404
history.

## 2026-07-27 (later still) — 🛑 `POST /db/NMAS` also crashes Gen NX: not a Civil-specific defect

With the user's explicit go-ahead, `--include-crashers --tier static` was run
once against the fresh Gen NX v2.1 (build 07/28/2026) session — the first
time this case has ever touched Gen. It crashed on the **first attempt**:

```
POST /db/NMAS -> 404: Client Disconnected (Hint: either the product isn't
connected ... or the id you asked for doesn't exist in the current model)
```

A follow-up `GET /db/NODE` a few seconds later confirmed the session was
actually gone, not just this one call rejected: `404 {"error": {"message":
"client does not exist"}}` — the exact string Civil NX gives after this same
crash. The user restarted Gen NX, pressed New Project, and reconnected;
`GET /db/NODE` on the new session returned `200 {"message": ""}` (empty
document), confirming recovery.

This settles the question left open in the 2026-07-26 Civil section: the
crash is **not** a Civil NX peculiarity. Six reproductions on Civil (two
versions) plus one on Gen (first-ever attempt, different build entirely,
different product) is the same failure on both of MIDASIT's NX flagship
products through what must be a shared write path. Not re-running this
again — one clean reproduction on Gen matching Civil's exact signature is
enough; further attempts just burn licenses for no new information.

**Updated everywhere this was recorded as Civil-only:** `CLAUDE.md`,
`NodalMassPayload`'s docstring in `db/static_loads.py`, the `crashes=` note
on the case in `live_crud_check.py`. The vendor report's A-1 needs the same
correction before it's sent — "Civil NX 한정" understates it.

## Caveat — read before acting on this file

This is evidence from **one MIDASIT account, one product license/edition,
one point in time**, not from the manual. It is plausible some of the
20 + 7 "product-only" endpoints above are actually gated by license tier,
Civil/Gen build version, or model state rather than being permanently
unavailable for that product. **Do not change any `PRODUCTS` frozenset in
the SDK based solely on this file.** If the same restriction is
independently reproduced (different account, different session, or a
future manual revision adds an explicit product note), that's the trigger
to revisit `PRODUCTS` for the specific classes involved — cite this file's
date and findings in that future change, and re-verify before trusting it,
since MIDASIT's platform can change between now and then.
