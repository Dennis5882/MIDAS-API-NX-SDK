# Project Plan

High-level architecture, phased roadmap, and milestone plan for `midas-nx`.
For the itemized per-endpoint checklist see the auto-generated
[ROADMAP.md](./ROADMAP.md); this document is the hand-maintained "big picture"
that ROADMAP.md doesn't capture.

> Last updated: 2026-07-15, at v0.6.0 (294/304 documented endpoints, Phase 5a
> complete — design setup + steel design code).

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
    ├── design.py         ch 24  pre-design-calc input: RC/steel code select,
    │                    rebar-check input, unbraced length, design member
    │                    assignment, frame def, slenderness limits, rebar overrides
    └── (planned)        ch 26-27  see §3
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
│   ├── base.py           (planned, if ch26/27 reuse warrants it — not yet needed)
│   └── steel_kds.py       ch 25  Steel design code KDS 41 30:2022 setup,
│                        per-member design parameters, material overrides,
│                        design-execution/result-table/report/image (27/27)
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

## 2. Current status (v0.6.0)

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
| **Everything else** | 26, 27 | **0/2 rows** | ⏳ not started |
| **Total** | | **294/304 (97%)** | v0.6.0 on PyPI |

> ⚠️ **The 304 still undercounts real work.** Design-code chapters 26/27 are
> one aggregate row each but hold **69 + 27 = 96 real endpoints** (ch25's own
> aggregate row was broken out into 27 real rows this phase, mirroring the
> ch18–21 precedent from Phase 2). True remaining surface is closer to
> **~104 endpoints**, entirely in ch26 (RC KDS 41 20:2022) and ch27 (SRC
> AIK-SRC2K).

Velocity reference: the 02–06 build added 76 endpoints in one pass; Phase 1
(07/09/10/11) added another 47 in a second pass; Phase 2 (12–14, 18–21, 23)
added 48 rows (~118 real functions/classes) in a third pass; Phase 3 (15, 16)
added 26 endpoints (131 real functions/classes across ope.py + view.py) in a
fourth pass; Phase 4 (08, 17) added 32 endpoints (90 real classes across
moving_loads.py + bridge.py) in a fifth pass; Phase 5a (24, 25) added 40
endpoints (122 real classes/functions across db/design.py + design/steel_kds.py)
in a sixth pass — all six
followed the same fixed transcribe→type→test→mark-coverage loop (see §5),
with Phase 2's ch19-20/ch21, Phase 3's ch15/ch16, Phase 4's ch08, and Phase
5a's ch24+ch25 (in parallel) each delegated to background agents following
that same established pattern.

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
- **Phase 5b — RC design code  ·  69 real endpoints ✦  ·  → v0.7.0**
  - ch 26 RC KDS 41 20:2022 (69) — largest single chapter in the project
    (13,363 manual lines); will itself need splitting across multiple
    background-agent passes (settings block ~items 1-38, then the
    BD/CD/BRD/WD/HCD/BC/CC/BRC × ANAL/TABLE/REPORT triplets ~items 39-69,
    which compress well via shared TypedDicts + thin wrappers).
- **Phase 5c — SRC design code  ·  27 real endpoints ✦  ·  → v0.8.0**
  - ch 27 SRC AIK-SRC2K (27) — same DCO/DCTL/LLRF/... setup + check-triplet
    structure as ch25/26; expect significant cross-chapter TypedDict/shape
    reuse once ch26 lands.
- v1.0.0 tags immediately once 5c lands (full documented surface covered) —
  no separate v1.0.0-only work planned beyond the version bump itself.

### Cross-cutting / backlog (any time)
- Resolve undocumented Hyper-S stubs (STYP-M1, MATL-M1, IMFM-M1, EPMT-M1,
  IEHG-*-M1) once the vendored manual documents them.
- Package `py.typed` marker so downstream type-checkers see the TypedDicts.
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
| v0.6.0 | Design setup + Steel code (Phase 5a) | ready to release |
| v0.7.0 | RC design code (Phase 5b) | ch 26 usable |
| v0.8.0 | SRC design code (Phase 5c) | ch 27 usable |
| v1.0.0 | Design code checks complete | full documented surface covered |

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
