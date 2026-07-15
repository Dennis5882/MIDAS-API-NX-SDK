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

## ⚠️ CONFIRMED — `CC-ANAL` (RC column code-check perform) hangs Gen NX and requires a forced process kill

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

**Do not call `design.rc_kds.checks.perform_column_check` (`CC-ANAL`)
against a live session without an escape plan** (expect to force-kill Gen
NX). Given the shared "Design Thread" architecture across every other
`perform_*_check`/`*-ANAL` function in this SDK (`perform_beam_check`,
`perform_brace_check`, `perform_wall_check` in the same file;
`perform_steel_code_check` in `steel_kds.py`;
`perform_src_beam_check`/`perform_src_column_check` in
`src_aiksrc2k.py`; `perform_optimal_design`/`OCHECK` variants), **treat
the entire "perform design check" family as carrying the same
unconfirmed-but-plausible hang risk** until each is independently tested.
This session did not attempt any of the others after this finding.

**Practical takeaway for this SDK**: nothing to fix in `midas-nx` itself —
every request shape sent was correct per the manual (confirmed by the
clean, correctly-shaped `{"error": ...}` responses on the calls that
didn't hang), and the SDK has no way to add a client-side guard against a
server-side thread deadlock. This is a Gen NX application defect worth
reporting to MIDASIT directly, with this file's reproduction steps.
Consider adding a runtime warning to the `perform_*_check` docstrings
pointing future callers at this file before they hit it unprepared.

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
