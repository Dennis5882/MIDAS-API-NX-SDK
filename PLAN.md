# Project Plan

High-level architecture, phased roadmap, and milestone plan for `midas-nx`.
For the itemized per-endpoint checklist see the auto-generated
[ROADMAP.md](./ROADMAP.md); this document is the hand-maintained "big picture"
that ROADMAP.md doesn't capture.

> Last updated: 2026-07-21, at v0.10.0 (390/398 documented endpoints, Phase 5c
> complete — SRC design code AIK-SRC2K; v0.9.0 added extensive live Gen NX /
> Civil NX verification, see docs/live_verification_notes.md; v0.9.1 was a
> live-manual schema-sync fix; v0.10.0 adds cross-cutting connection/schema
> helpers not counted in the 390/398, see §4). The remaining 8 rows are
> Hyper-S `-M1` endpoints with no JSON Schema in the manual repo (URL/methods
> and an external Zendesk link only) — genuinely not transcribable to this
> repo's typed-TypedDict standard without depending on an external,
> non-versioned source, so they're treated as undocumented stubs per this
> project's existing "100% minus undocumented stubs" gate. Endpoint coverage
> (Phases 1-5) is essentially done; Phases 6-8 below shift the project's
> center of gravity from "cover the API surface" to "make the SDK trustworthy,
> maintainable, and usable by non-developer structural engineers" — see each
> phase for the reasoning and what's already in place vs. still greenfield.

---

## 1. Architecture map

```text
midas_nx/
├── client.py            MidasClient — instance-based HTTP + auth, typed errors,
│                        Product.GEN|CIVIL selection, strict_product guard.
│                        Also: configure()/MidasAPI() low-level free-function API,
│                        .verify_connection() (/mapikey/verify health check).
├── doc.py               /doc/*, /ope/*, /view/* lifecycle — plain functions,
│                        wrapped in "Argument" (not ID-keyed "Assign").
└── db/
    ├── base.py          DbResource — .create/.get/.update/.delete/.info()
    │                    classmethods (.info() = /info/db/... schema
    │                    introspection, independent of METHODS/CRUD),
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

## 2. Current status (v0.10.0)

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
| **Total** | | **390/398 (98%)** | v0.10.0 ready to release |

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
- **v0.10.0 ✅ — Connection/introspection helpers**
  — `MidasClient.verify_connection()` (`/mapikey/verify` health check) and
  `DbResource.info()` (`/info/db/...` schema introspection, a fallback for
  fields/endpoints this SDK hasn't wrapped yet). Source: the manual repo's
  docs/AUTHENTICATION.md (a cross-cutting auth/ops guide, not a per-chapter
  manual page) — not tracked in docs/coverage.json/ROADMAP.md for that
  reason, so the 390/398 count is unchanged. Also ported the manual repo's
  simple-beam load-combination tutorial to `examples/python/`, and added a
  README Troubleshooting section (connection errors, firewall/SSL-inspection
  allowlist).
### Phase 6 — Trust & maintenance foundation  ·  v0.11-0.13
Endpoint coverage (Phases 1-5) is essentially done; before layering practitioner
features on top, harden the ground it stands on. Reprioritized 2026-07-21 after
a roadmap review found part of this phase already done in earlier releases —
scope below is corrected to what's actually left, not restated from scratch.
- **CI: basic test/lint pipeline** — `.github/workflows/` currently has only
  `publish.yml`, gated on `release` (build+test+publish). There is no
  push/PR CI at all yet. Add `.github/workflows/ci.yml` running
  `pytest` + `ruff` on every push/PR. This is a prerequisite for the manual-diff
  job below, not optional groundwork.
- **A1, narrowed — formalize live verification already done.** v0.9.0 already
  ran a real Gen NX + Civil NX session against 526 endpoints (233/253 Gen,
  273/293 Civil OK) and recorded a reproducible Gen NX defect — see
  `docs/live_verification_notes.md`. That work is *not* reflected in
  `docs/coverage.json` (`"live_verified"` field: 0 occurrences today). Add the
  field per-endpoint from the existing notes, surface a verification-rate line
  in `ROADMAP.md`, and add `scripts/live_smoke.py` so the next live session is
  a rerun, not a one-off.
- **D1, narrowed — wire the vendoring pipeline into CI.** `scripts/vendor_coverage.py`
  and `scripts/gen_roadmap.py` (the chapter↔module mapping D1 wants) already
  exist and work; they're just manual/on-demand. Once basic CI (above) exists,
  add a weekly scheduled job that runs `vendor_coverage.py` against the sibling
  manual repo, diffs the result, flags changed chapters `"stale"` in
  `coverage.json`, and opens an issue.
- **C1, narrowed — beginner tutorial, not install docs.** README already has
  a `pip install midas-nx` section and Korean/Traditional-Chinese/Simplified-Chinese
  onboarding paragraphs (added v0.9.0). Still missing: a screenshot-driven,
  zero-python-experience "first script" walkthrough and a `docs/ko/`/`docs/en/`
  split. One complete path beats a feature-complete doc site.
- **C2 — friendlier error messages.** Exception hierarchy is already solid
  (`MidasAPIError` → `MidasAuthError`/`MidasNotFoundError`/`MidasRequestError`/
  `MidasServerError`/`MidasConnectionError`/`ProductMismatchError`/
  `UnsupportedMethodError`, `src/midas_nx/client.py`). Add "how to fix it" text
  to each: MAPI key location for `MidasAuthError`, NX process/API-server check
  for `MidasConnectionError`.
- **D6 — back the competitive claim already in production.** README already
  ships "covers roughly a third of the documented API surface" (official
  packages) as unbacked prose today — this isn't a future risk, it's a live
  claim with no citation. Build the `coverage.json`-derived comparison table
  (or soften to a neutral "single package, both products, broad coverage"
  framing) this release, not later.

### Phase 7 — Practitioner efficiency  ·  v0.14
- **B2 — Excel round-trip**, `midas-nx[excel]` extra (keep pandas/openpyxl out
  of the core dependency — `requests`-only import stays a hard invariant).
  `from_excel`/`to_excel` for node/element/load tables and result reports;
  `to_dataframe()` folds in as the pandas primitive underneath.
- **B3 — GET response unwrap helper.** `Node.items(client=...) -> dict[int, NodePayload]`
  alongside the existing `.get()`, same pattern across `DbResource` subclasses.
- **C3 — scenario examples** (2 to start): analyze → extract results → Excel
  summary report; construction-stage bulk model edit. Each example doubles as
  live-verification evidence (Phase 6 A1) and onboarding material (C1).

### Phase 8 — High-level workflow layer  ·  v0.15+
Deliberately last: picking the wrong recipe scenarios is the most expensive
mistake in this axis, so it waits on user feedback from Phases 6-7's examples
and README traffic, not just code readiness.
- **B1 — `midas_nx.recipes` (or `.easy`)**: workflow-level functions
  (`create_frame(...)`, `apply_load_combos_kds(...)`, `extract_member_forces(...)`)
  returning practitioner-ready dict/DataFrame shapes, ID/endpoint-key unwrapping
  built in. Low-level layer (current `db.*`/`design.*`) stays untouched
  underneath — this is additive, not a replacement.
- **B4 — opt-in runtime validation**, two-staged: `typing_extensions.Required[]`
  first, opt-in full validation second. Default `strict=True` in the new
  recipes layer; low-level layer keeps today's no-validation behavior.
- **D2 — schema drift checker**, `scripts/check_drift.py`, using the client's
  existing `/info/db/...` introspection (`DbResource.info()`, added v0.10.0) to
  diff live-server schema against this SDK's `TypedDict` definitions — the
  server-side counterpart to Phase 6's manual-diff job.
- **D4 — product-version compatibility matrix** — record verified Gen NX/Civil
  NX product versions per endpoint in `coverage.json`, surface as a table.
- **D3 — scaffolding, not full codegen** — `scripts/gen_endpoint.py` generates
  TypedDict + `DbResource` subclass + mirror-test boilerplate from a manual `.md`
  chapter; human review stays mandatory given the manual's own internal
  inconsistencies (same rationale D1's stale-flagging exists for).

### v1.0.0 — public API freeze
Gate: (a) the 8 undocumented Hyper-S `-M1` stubs resolved once the manual
documents them with an actual JSON Schema, or the existing "100% minus
undocumented stubs" rule is formally invoked instead; (b) Phase 6's live-verification
formalization (A1) complete; (c) Phase 6's manual-diff CI (D1) running. Matches
D5 from the 2026-07-21 roadmap review: 1.0 means "frozen public surface +
live-verified core paths + a running change-detection pipeline," not just
"endpoint count is high."

### Cross-cutting / backlog (any time)
- Resolve undocumented Hyper-S stubs (STYP-M1, MATL-M1, IMFM-M1, EPMT-M1,
  IEHG-*-M1) once the vendored manual documents them with an actual JSON
  Schema (currently only URL/methods + an external Zendesk link).

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
| v0.9.1 ✅ | Live-manual schema sync (`/ope/GSBG` → 2026-07-14 schema) | published |
| v0.10.0 ✅ | Connection/introspection helpers (`verify_connection()`, `DbResource.info()`) + beam example + troubleshooting docs | published |
| v0.11.0 | Phase 6 pt. 1 — CI (`ci.yml`), `coverage.json` `live_verified` field + `scripts/live_smoke.py`, weekly manual-diff job (D1) | CI green, live-verified rate shown in ROADMAP.md |
| v0.12.0 | Phase 6 pt. 2 — friendlier error messages (C2), beginner tutorial + `docs/ko/`/`docs/en/` (C1), coverage-comparison table backing README's competitive claim (D6) | |
| v0.13.0 | Phase 7 — Excel round-trip extra (B2), GET-unwrap helper (B3), 2 scenario examples (C3) | `pip install midas-nx[excel]` works, examples run against a live session |
| v0.14.0+ | Phase 8 — `recipes`/`easy` high-level layer (B1) once scenarios are validated from Phase 7 feedback, opt-in validation (B4), schema-drift checker (D2), version matrix (D4), endpoint scaffolding tool (D3) | |
| v1.0.0 | Public API freeze: Hyper-S `-M1` stub decision + Phase 6 live-verification/manual-diff CI running | full documented surface covered, live-verified, change-detection pipeline live |

Each version ships when its phase's chapters are 100% (minus undocumented
stubs) and green in CI. Release = bump `pyproject.toml` version, tag, publish
GitHub Release → `publish.yml` auto-uploads to PyPI.

> Numbering note (2026-07-21): the original Phase 1-5 numbering above was
> chapter/endpoint-coverage-driven and ended at v0.10.0. Phase 6-8 (this
> section) reflect a 2026-07-21 roadmap review's four-axis reprioritization
> (reliability, practitioner efficiency, non-developer accessibility,
> maintenance architecture) — version numbers from v0.11.0 on are provisional
> until each release's actual scope is locked at cut time.

---

## 5. Working rhythm (per endpoint)

Unchanged from the 02–06 build — the loop that produced the current velocity:
1. Pull the endpoint's spec from the vendored manual.
2. Add `DbResource` subclass + `TypedDict` payload in the chapter module.
3. Add a `responses`-mocked test mirroring `tests/db/test_node_element.py`.
4. Mark `"implemented"` in `docs/coverage.json`, re-run `scripts/gen_roadmap.py`.
5. Run `pytest` + `ruff` before committing the chapter.
