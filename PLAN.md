# Project Plan

High-level architecture, phased roadmap, and milestone plan for `midas-nx`.
For the itemized per-endpoint checklist see the auto-generated
[ROADMAP.md](./ROADMAP.md); this document is the hand-maintained "big picture"
that ROADMAP.md doesn't capture.

> Last updated: 2026-07-13, at v0.1.0 (101/278 documented endpoints, first
> PyPI release published).

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
    └── (planned)        ch 07-27  see §3
```

**Design invariants** (keep these as new chapters land):
- One `DbResource` subclass per endpoint; `TypedDict` payloads document schema
  (no runtime validation — schemas are too conditional).
- Deeply-conditional sub-objects fall back to `Any` (see `SectBefore.SECT_I`);
  only the common envelope is fully typed.
- Every endpoint gets a `responses`-mocked test asserting request shape.
- Coverage tracked in `docs/coverage.json`; `ROADMAP.md` regenerated from it.

---

## 2. Current status (v0.1.0)

| Area | Chapters | Endpoints | State |
|---|---|---|---|
| Lifecycle | 01 | 11/11 | ✅ done |
| Core modeling | 02, 03 | 20/21 | ✅ done (1 undoc Hyper-S stub) |
| Properties | 04 | 25/32 | ✅ done (7 undoc Hyper-S/stub) |
| Boundary | 05 | 24/24 | ✅ done |
| Static loads | 06 | 21/21 | ✅ done |
| **Everything else** | 07–27 | **0/177 rows** | ⏳ not started |
| **Total** | | **101/278 (36%)** | v0.1.0 on PyPI |

> ⚠️ **The 278 undercounts real work.** Design-code chapters 25/26/27 are one
> aggregate row each but hold **27 + 69 + 27 = 123 real endpoints**; POST
> result-table chapters (18–21) are also single aggregate rows. True remaining
> surface is closer to **~400 endpoints**, concentrated in design code-checks.

Velocity reference: the 02–06 build added **76 endpoints in one focused pass**,
following a fixed transcribe→type→test→mark-coverage loop.

---

## 3. Phased roadmap

Phases are ordered by (a) unlocking a complete analyzable model first, then
(b) getting results back out, then (c) specialization. Sizing is by documented
rows; ✦ marks chapters whose real endpoint count far exceeds their row count.

### Phase 1 — Complete the analyzable model  ·  ~47 endpoints  ·  → v0.2.0
Everything needed to define a full model that MIDAS can actually run.
- ch 07 Temperature / Prestress (12)
- ch 09 Dynamic Loads (12)
- ch 10 Construction Stage (14)
- ch 11 Settlement / Misc Loads (9)

### Phase 2 — Analysis control + results out  ·  ~49 rows ✦  ·  → v0.3.0
Configure the run and read results back — the payoff phase.
- ch 12 Analysis Control (21)
- ch 13 Load Combinations (8)
- ch 14 Pushover (6)
- ch 18–21 POST result/story tables (4 aggregate rows ✦ — many table types)
- ch 23 POST Design forces (10)

### Phase 3 — Operations & view  ·  ~26 endpoints  ·  → v0.4.0
- ch 15 OPE operations (19)
- ch 16 VIEW select/capture/display (7)

### Phase 4 — Civil bridge specialization  ·  32 endpoints (civil-only)  ·  → v0.5.0
- ch 08 Moving Loads (28, civil-only)
- ch 17 Bridge diagrams/cable/camber (4, civil-only)

### Phase 5 — Design code checks  ·  ~136 real endpoints ✦  ·  → v1.0.0
The largest chunk; likely warrants its own sub-phasing per code.
- ch 24 DB Design setup (13)
- ch 25 Steel KDS 41 30:2022 (27 ✦)
- ch 26 RC KDS 41 20:2022 (69 ✦)
- ch 27 SRC AIK-SRC2K (27 ✦)

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
| v0.2.0 | Full analyzable model (Phase 1) | can build+run a complete model |
| v0.3.0 | Analysis control + result extraction (Phase 2) | round-trip: define → run → read |
| v0.4.0 | Operations & view (Phase 3) | |
| v0.5.0 | Civil bridge features (Phase 4) | moving loads usable |
| v1.0.0 | Design code checks (Phase 5) | full documented surface covered |

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
