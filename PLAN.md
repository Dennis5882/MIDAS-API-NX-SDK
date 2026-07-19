# Project Plan

High-level architecture, phased roadmap, and milestone plan for `midas-nx`.
For the itemized per-endpoint checklist see the auto-generated
[ROADMAP.md](./ROADMAP.md); this document is the hand-maintained "big picture"
that ROADMAP.md doesn't capture.

> Last updated: 2026-07-19, at v0.9.1 (390/398 documented endpoints, Phase 5c
> complete — SRC design code AIK-SRC2K; v0.9.0 added extensive live Gen NX /
> Civil NX verification, see docs/live_verification_notes.md; v0.9.1 is a
> live-manual schema-sync fix, see §4). The remaining 8 rows are Hyper-S
> `-M1` endpoints with no JSON Schema in the manual repo (URL/methods + an
> external Zendesk link only) — genuinely not transcribable to this repo's
> typed-TypedDict standard without depending on an external, non-versioned
> source, so they're treated as undocumented stubs per this project's
> existing "100% minus undocumented stubs" gate. v1.0.0 is next; whether it
> requires those 8 (needs a source for their schema) or is already earned
> under the existing stub exclusion is an open call for the next release.

---

## 1. Architecture map

```text
midas_nx/
├── client.py            MidasClient — instance-based HTTP + auth, typed errors,
│                        Product.GEN|CIVIL selection, strict_product guard.
│                        Also: configure()/MidasAPI() low-level free-function API.
├── doc.py               /doc/*, /ope/*, /view/* lifecycle — plain functions,
│                        wrapped in "Argument" (not ID-keyed "Assign").
└── db/
    ├── base.py          DbResource — .create/.get/.update/.delete classmethods,
    │                    METHODS/PRODUCTS guards, shared NO_DELETE_METHODS +
    │                    ItemGroupFields TypedDict.
    ├── project.py       ch 02  Project structure, groups, colors, story
    ├── node_element.py  ch 03  Node/Element/Skew/Domain
    ├── properties/      ch 04  material · section · thickness · hinge · damping
    ├── boundary.py      ch 05  constraints · springs · links · seismic devices
    ├── static_loads.py  ch 06  static/earth-pressure/wind/seismic loads
    ├── temperature_prestress.py  ch 07  temperature loads · tendons · prestress
    ├── dynamic_loads.py ch 09  response spectrum · time history
    ├── construction_stage.py     ch 10  stages · composite sections · hydration
    ├── misc_loads.py    ch 11  settlement · wave loads · initial forces
    ├── analysis_control.py       ch 12  main/P-Delta/buckling/eigenvalue/
    │                    nonlinear/construction-stage/moving-load control
    ├── load_combinations.py      ch 13  LCOM-* combinations · cutting lines
    ├── pushover.py       ch 14  pushover global control · load cases
    ├── moving_loads.py   ch 08  traffic lanes · vehicles · moving load cases
    │                    (country variants) · dynamic factors (civil-only)
    ├── bridge.py         ch 17  girder diagrams · camber control · cable
    │                    unknown-load-factor constraints (civil-only)
    └── design.py         ch 24  pre-design-calc input: RC/steel code select,
                         rebar-check input, unbraced length, design member
                         assignment, frame def, slenderness limits, rebar overrides
├── ope.py                ch 15  GUI/preprocessing operations (element divide,
│                        auto-mesh, LCOM-* auto-generation, gust factor, ...)
│                        — plain functions, one TypedDict argument each.
├── view.py               ch 16  model view control (selection, capture,
│                        viewpoint, active target, display, result graphics)
│                        — plain functions, one TypedDict argument each.
├── design/               DESIGN/<STEEL|RC|SRC>/<code>/<ENDPOINT> — a
│                        different namespace from /db/*; mixes DbResource-style
│                        config/member-CRUD endpoints with plain POST-action
│                        functions (design-execution/table/report/image) that
│                        reuse post/base.py's NodeElemsSelector/TableUnit/
│                        TableStyles.
│   ├── steel_kds.py       ch 25  Steel design code KDS 41 30:2022 setup,
│   │                    per-member design parameters, material overrides,
│   │                    design-execution/result-table/report/image (27/27)
│   ├── rc_kds/            ch 26  RC design code KDS 41 20:2022 (69/69 ✦✦,
│   │   │                largest chapter in the project — split into 4 files,
│   │   │                mirrors db/properties/'s subpackage-per-oversized-
│   │   │                chapter precedent):
│   │   ├── setup.py       design code/frame/load-combination setup, seismic
│   │   │                params, per-member design params (19)
│   │   ├── rebar.py       moment/torsion/rebar-ratio params, wall/rebar-
│   │   │                design-criteria, beam/column/wall/brace rebar
│   │   │                overrides (19)
│   │   ├── design_forces.py  design-execution/table/report per member type:
│   │   │                beam/column/brace/wall/haunched-beam (15)
│   │   └── checks.py      code-check/table/report per member type, plus
│   │                    comprehensive design result and column/brace/beam
│   │                    design-forces tables — the latter 3 share one real
│   │                    HTTP endpoint (TABLE) selected by Argument.TABLE_TYPE,
│   │                    mirroring post/design.py's shared-helper pattern (16)
│   └── src_aiksrc2k.py    ch 27  SRC design code AIK-SRC2K setup, per-member
│                        design parameters, check-execution/result-table/
│                        report, optimal design, material/section overrides
│                        (27/27, single self-contained file — no cross-chapter
│                        TypedDict reuse with steel_kds.py/rc_kds/*, per this
│                        subtree's established convention)
└── post/                 POST /post/* result extraction — plain functions,
    │                    wrapped in "Argument" (same convention as doc.py).
    ├── base.py           get_table() — shared /post/TABLE plumbing (one
    │                    endpoint, TABLE_TYPE selects the table; no
    │                    DbResource-per-type since there's one real endpoint).
    ├── pre_process.py    ch 18  element weight · mass/load summary · material ·
    │                    section · supports · story mass/load/weight (10 types)
    ├── result_1.py       ch 19-20  reaction/displacement/truss/cable/beam/
    │                    plate/plane/solid/link/mode-shape/tendon results (50 types)
    ├── story.py          ch 21  story drift/displacement/shear/eccentricity/
    │                    irregularity-check tables (17 types)
    └── design.py         ch 23  P-M diagram · steel code check · design
                         forces (RC/steel/SRC/cold-formed) (10 endpoints)
```

**`ope.py`/`view.py` convention**: like `doc.py`, bodies are wrapped in a plain
`"Argument"` key (not ID-keyed `"Assign"`). But unlike `doc.py`'s few-named-
kwargs style, most ch15/16 endpoints have deeply-nested, highly-optional
bodies (10+ levels in places, e.g. `/view/DISPLAY`'s ~90 boolean toggles), so
each POST function takes one `TypedDict` `argument` parameter instead —
mirroring the `db/*.py` payload-typing style but at the whole-body level.

**Design invariants** (keep these as new chapters land):
- One `DbResource` subclass per endpoint; `TypedDict` payloads document schema
  (no runtime validation — schemas are too conditional).
- Deeply-conditional sub-objects fall back to `Any` (see `SectBefore.SECT_I`);
  only the common envelope is fully typed.
- Every endpoint gets a `responses`-mocked test asserting request shape.
- Coverage tracked in `docs/coverage.json`; `ROADMAP.md` regenerated from it.

---

## 2. Current status (v0.9.1)

| Area | Chapters | Endpoints | State |
|---|---|---|---|
| Lifecycle | 01 | 11/11 | ✅ done |
| Core modeling | 02, 03 | 20/21 | ✅ done (1 undoc Hyper-S stub) |
| Properties | 04 | 25/32 | ✅ done (7 undoc Hyper-S/stub) |
| Boundary | 05 | 24/24 | ✅ done |
| Static loads | 06 | 21/21 | ✅ done |
| **Phase 1 — analyzable model** | 07, 09, 10, 11 | **47/47** | ✅ done |
| **Phase 2 — analysis control + results out** | 12–14, 18–21, 23 | **48/48 rows** | ✅ done |
| **Phase 3 — operations & view** | 15, 16 | **26/26** | ✅ done |
| **Phase 4 — civil bridge specialization** | 08, 17 | **32/32** | ✅ done |
| **Phase 5a — design setup + steel code** | 24, 25 | **40/40** | ✅ done |
| **Phase 5b — RC design code** | 26 | **69/69** | ✅ done |
| **Phase 5c — SRC design code** | 27 | **27/27** | ✅ done |
| **Total** | | **390/398 (98%)** | v0.9.1 on PyPI |

> The remaining 8 rows are undocumented Hyper-S stubs (STYP-M1, MATL-M1,
> IMFM-M1, EPMT-M1, IEHG-*-M1) with no JSON Schema in the manual repo to
> transcribe from (URL/methods + an external Zendesk link only) — see §3's
> cross-cutting backlog. Every endpoint with an actual JSON Schema across
> all 27 chapters is now implemented.

Velocity reference: the 02–06 build added 76 endpoints in one pass; Phase 1
(07/09/10/11) added another 47 in a second pass; Phase 2 (12–14, 18–21, 23)
added 48 rows (~118 real functions/classes) in a third pass; Phase 3 (15, 16)
added 26 endpoints (131 real functions/classes across ope.py + view.py) in a
fourth pass; Phase 4 (08, 17) added 32 endpoints (90 real classes across
moving_loads.py + bridge.py) in a fifth pass; Phase 5a (24, 25) added 40
endpoints (122 real classes/functions across db/design.py + design/steel_kds.py)
in a sixth pass; Phase 5b (26) added 69 endpoints (173 real classes/functions
across design/rc_kds/'s 4 files) in a seventh pass; Phase 5c (27) added 27
endpoints (~68 real classes/functions across design/src_aiksrc2k.py) in an
eighth and final pass — all eight followed the same fixed
transcribe→type→test→mark-coverage loop (see §5), with Phase 2's ch19-20/ch21,
Phase 3's ch15/ch16, Phase 4's ch08, Phase 5a's ch24+ch25 (in parallel), Phase
5b's ch26 (split 4 ways in parallel — the first time a single chapter itself
needed splitting across multiple agents), and Phase 5c's ch27 (small enough,
at 7,148 manual lines, to fit back into a single background-agent pass like
ch25) each delegated to background agents following that same established
pattern.

---

## 3. Phased roadmap

Phases are ordered by (a) unlocking a complete analyzable model first, then
(b) getting results back out, then (c) specialization. Sizing is by documented
rows; ✦ marks chapters whose real endpoint count far exceeds their row count.

### Phase 1 ✅ — Complete the analyzable model  ·  47/47 endpoints  ·  v0.2.0
Everything needed to define a full model that MIDAS can actually run.
- ch 07 Temperature / Prestress (12/12)
- ch 09 Dynamic Loads (12/12)
- ch 10 Construction Stage (14/14)
- ch 11 Settlement / Misc Loads (9/9)

### Phase 2 ✅ — Analysis control + results out  ·  48/48 rows ✦  ·  v0.3.0
Configure the run and read results back — the payoff phase.
- ch 12 Analysis Control (21/21)
- ch 13 Load Combinations (8/8)
- ch 14 Pushover (6/6)
- ch 18–21 POST result/story tables (4 aggregate rows ✦ → 87 real functions:
  10 pre-process + 50 analysis-result + 17 story table types)
- ch 23 POST Design forces (10/10)

### Phase 3 ✅ — Operations & view  ·  26/26 endpoints  ·  v0.4.0
- ch 15 OPE operations (19/19)
- ch 16 VIEW select/capture/display (7/7)

### Phase 4 ✅ — Civil bridge specialization  ·  32/32 endpoints (civil-only)  ·  v0.5.0
- ch 08 Moving Loads (28/28, civil-only)
- ch 17 Bridge diagrams/cable/camber (4/4, civil-only)

### Phase 5 — Design code checks  ·  ~136 real endpoints ✦  ·  split by code
The largest chunk — split into per-code sub-phases (confirmed necessary after
measuring source density: ch26 alone is 13,363 manual lines / 69 endpoints,
3x any chapter built so far), each its own release rather than one big bang.

- **Phase 5a ✅ — Design setup + Steel code  ·  40/40 endpoints  ·  v0.6.0**
  - ch 24 DB Design setup (13/13)
  - ch 25 Steel KDS 41 30:2022 (27/27 ✦)
- **Phase 5b ✅ — RC design code  ·  69/69 endpoints ✦  ·  v0.7.0**
  - ch 26 RC KDS 41 20:2022 (69/69) — largest single chapter in the project
    (13,363 manual lines); split into 4 parallel background-agent passes by
    natural endpoint-group boundary (setup items 1-19, rebar/member items
    20-38, design-execution items 39-53, checks+tables items 54-69), each
    writing to its own file under a new `design/rc_kds/` subpackage. No
    cross-chapter TypedDict reuse with ch25 materialized in practice — RC's
    field sets differ enough per-endpoint (even for same-named endpoints
    like DCO/MBTP/MLLR/HCBM) that local-per-chapter shapes stayed the right
    call; `design/base.py` remains unbuilt.
- **Phase 5c ✅ — SRC design code  ·  27/27 endpoints ✦  ·  v0.8.0**
  - ch 27 SRC AIK-SRC2K (27) — same DCO/DCTL/LLRF/... setup + check-triplet
    structure as ch25/26; at 7,148 manual lines it was close in size to
    ch25 (6,199 lines/27 endpoints), so it fit in a single background-agent
    pass rather than ch26's four-way split. Kept fully self-contained (no
    cross-chapter TypedDict reuse with steel_kds.py/rc_kds/*), matching
    Phase 5b's finding that same-named endpoints (DCTL/MBTP/...) still
    differ enough field-for-field across codes that local shapes are the
    right call.
- **v0.9.0 ✅ — Live Gen/Civil NX verification + PyPI discoverability**
  — no new chapter work; extensive live-session verification against real
  Gen NX / Civil NX (see docs/live_verification_notes.md — confirmed a
  reproducible Gen NX application defect in the RC-KDS "perform design
  check" family, confirmed the full Civil analyze→results chain including
  moving loads) plus PyPI-page improvements (`py.typed` marker, classifiers,
  keywords, project URLs, README install/use-cases/multilingual intro).
- **v0.9.1 ✅ — Live-manual schema sync**
  — no new chapter work; the vendored manual's `/ope/GSBG` article changed
  schema between 2026-07-12 (the "확인 필요"/unconfirmed draft this was
  originally transcribed from) and 2026-07-14 (`LC_TYPE` dropped,
  `BATCH_LIST` changed from an object array to a plain string array).
  Updated `BridgeGirderDiagramArgument` + its tests to match; no other
  endpoint affected by that manual update.
- v1.0.0 next — pending a decision on whether the 8 undocumented Hyper-S
  stubs block it (see cross-cutting backlog below) or the existing "100%
  minus undocumented stubs" gate already counts as met.

### Cross-cutting / backlog (any time)
- Resolve undocumented Hyper-S stubs (STYP-M1, MATL-M1, IMFM-M1, EPMT-M1,
  IEHG-*-M1) once the vendored manual documents them with an actual JSON
  Schema (currently only URL/methods + an external Zendesk link).
- Optional runtime validation layer (opt-in) for the non-conditional payloads.
- Integration smoke test against a live MIDAS NX server (currently all mocked).

---

## 4. Release milestones

| Version | Milestone | Gate |
|---|---|---|
| v0.1.0 ✅ | Core DB modeling (ch 01–06) | published |
| v0.2.0 ✅ | Full analyzable model (Phase 1) | published |
| v0.3.0 ✅ | Analysis control + result extraction (Phase 2) | published |
| v0.4.0 ✅ | Operations & view (Phase 3) | published |
| v0.5.0 ✅ | Civil bridge features (Phase 4) | published |
| v0.6.0 ✅ | Design setup + Steel code (Phase 5a) | published |
| v0.7.0 ✅ | RC design code (Phase 5b) | published |
| v0.8.0 ✅ | SRC design code (Phase 5c) | published |
| v0.9.0 ✅ | Live Gen/Civil NX verification + PyPI discoverability (py.typed, classifiers, README) | published |
| v0.9.1 | Live-manual schema sync (`/ope/GSBG` → 2026-07-14 schema) | ready to release |
| v1.0.0 | Design code checks complete (incl. Hyper-S `-M1`, 8 endpoints remaining) | full documented surface covered |

Each version ships when its phase's chapters are 100% (minus undocumented
stubs) and green in CI. Release = bump `pyproject.toml` version, tag, publish
GitHub Release → `publish.yml` auto-uploads to PyPI.

---

## 5. Working rhythm (per endpoint)

Unchanged from the 02–06 build — the loop that produced the current velocity:
1. Pull the endpoint's spec from the vendored manual.
2. Add `DbResource` subclass + `TypedDict` payload in the chapter module.
3. Add a `responses`-mocked test mirroring `tests/db/test_node_element.py`.
4. Mark `"implemented"` in `docs/coverage.json`, re-run `scripts/gen_roadmap.py`.
5. Run `pytest` + `ruff` before committing the chapter.
