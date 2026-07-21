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

**Hyper-S (`-M1`) endpoints — 13, fail under Gen, absent from the Civil
target set entirely** (their `PRODUCTS` is already `{"gen"}`-only in the
SDK). Expected: the connected Gen session isn't running in Hyper-S solver
mode, so these routes simply don't exist for it right now. Not evidence of
an SDK bug.

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
