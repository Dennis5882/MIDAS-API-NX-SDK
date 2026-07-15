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
