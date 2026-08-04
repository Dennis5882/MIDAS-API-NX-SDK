# Project Plan

High-level architecture, phased roadmap, and milestone plan for `midas-nx`.
For the itemized per-endpoint checklist see the auto-generated
[ROADMAP.md](./ROADMAP.md); this document is the hand-maintained "big picture"
that ROADMAP.md doesn't capture.

> Last updated: 2026-08-04, at v2.1.3. **v2.1.3 shipped 2026-08-04**: the
> first `src/midas_nx/` behaviour change since v2.0.0 — fixes a real bug in
> `MidasClient._send()`'s non-2xx error path: building the exception message
> assumed `data["error"]` was always a dict, so a 4xx/5xx response shaped
> like `{"error": "some string"}` raised a bare `AttributeError` instead of
> the intended `MidasAuthError`/`MidasRequestError`/`MidasServerError`,
> breaking any `except MidasAPIError:` handler. Found by a review pass
> across all of `src/midas_nx/` (41 modules, ~16.4k lines) prompted by a
> week of heavy docs churn; added a regression test
> (`test_non_dict_error_body_on_4xx_does_not_crash`). Same pass also fixed
> two stale docstrings: `db/dynamic_loads.py`'s THGC payload still claimed
> Civil-only despite the class already being correctly left ungated per the
> 2026-07-29 Gen NX correction, and `db/design.py`'s `RebarNameDist` still
> cited REBW's old, confirmed-wrong manual field names instead of the
> server-confirmed `VER_BAR`/`HOR_BAR`/`BE_HOR_BAR` the code actually uses.
> Everything else reviewed — `db/base.py`'s CRUD pattern, all model/load/
> analysis resources, `doc.py`/`ope.py`/`view.py`, `post/*`'s shape-based
> table unwrapping, and all three RC/steel/SRC design-code chapters — came
> back clean.
>
> Previously: **v2.1.2 shipped 2026-08-04** — packaged-metadata-only
> beginner-onboarding rewrite; see `docs/release_notes_v2.1.2.md`.
>
> **Release-by-release history lives in `docs/release_notes_v*.md`** (and,
> for anything predating v1.0.0, in `docs/live_verification_notes.md` and
> git history) — this header is kept to the current release plus one
> "Previously" line so it doesn't re-accumulate the 200+ line chain trimmed
> on 2026-08-04.

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
    ├── base.py          DbResource — .create/.get/.update/.delete/.info()/
    │                    .items() classmethods (.info() = /info/db/... schema
    │                    introspection, independent of METHODS/CRUD;
    │                    .items() = ID-keyed GET-response unwrap, v0.11.0),
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

## 2. Current status (endpoint table as of 2026-07-29; verification/tooling rows updated for v2.0.0)

| Area | Chapters | Endpoints | State |
|---|---|---|---|
| Lifecycle | 01 | 11/11 | ✅ done |
| Core modeling | 02, 03 | 21/21 | ✅ done |
| Properties | 04 | 32/32 | ✅ done |
| Boundary | 05 | 24/24 | ✅ done |
| Static loads | 06 | 21/21 | ✅ done |
| **Phase 1 — analyzable model** | 07, 09, 10, 11 | **47/47** | ✅ done |
| **Phase 2 — analysis control + results out** | 12–14, 18–21, 23 | **48/48 rows** | ✅ done |
| **Phase 3 — operations & view** | 15, 16 | **26/26** | ✅ done |
| **Phase 4 — civil bridge specialization** | 08, 17 | **32/32** | ✅ done |
| **Phase 5a — design setup + steel code** | 24, 25 | **40/40** | ✅ done |
| **Phase 5b — RC design code** | 26 | **69/69** | ✅ done |
| **Phase 5c — SRC design code** | 27 | **27/27** | ✅ done |
| **Total** | | **398/398 (100%)** | 390/398 published through v0.11.2; the last 8 landed 2026-07-29 |

> The last 8 rows (STYP-M1, MATL-M1, IMFM-M1, EPMT-M1, IEHG-{BEAM,TRUSS,GL,
> PSS}-M1) had no JSON Schema in the manual repo to transcribe from — this
> was v1.0.0 gate item (a). Resolved 2026-07-29 by deriving their payload
> TypedDicts from live `GET /info/db/...` server introspection instead
> (confirmed for 5 of 8; the other 3 — IEHG-TRUSS/GL/PSS-M1 — have no
> `/info` route at all, so their shape is assumed by sibling analogy to
> IEHG-BEAM-M1, not independently confirmed). Documented in-module as
> server-derived, not manual-transcribed. Every documented endpoint across
> all 27 chapters is now implemented.

Non-endpoint status as of **v2.0.0** (these are the axes Phases 6-8 move, and
they're the ones worth re-checking before planning a release):

| Axis | Artifact | State |
|---|---|---|
| Tests | 693 tests, `responses`-mocked | ✅ green |
| CI | `.github/workflows/ci.yml` — ruff + pytest on py3.9/3.10/3.11/3.12/3.13, push+PR | ✅ running |
| Static typing | mypy over `src/midas_nx`, config in `pyproject.toml`, own CI job | ✅ clean across all 41 modules |
| Packaging verification | `package` CI job + `scripts/wheel_smoke_test.py` — builds the wheel, installs it into a clean venv, asserts `py.typed` shipped, `__version__` matches the distribution, and the `delete_all()` guard is armed | ✅ running |
| Destructive-op safety | `delete()` per-id URL; `delete_all(confirm=True)` required, else `DestructiveOperationError` before sending | ✅ guarded |
| Docs site | MkDocs Material + mkdocstrings (`mkdocs.yml`), built `--strict` on every PR | ✅ live at `dennis5882.github.io/MIDAS-API-NX-SDK/` (confirmed 2026-08-04 — this row had drifted stale, saying "GitHub Pages not yet enabled" after it already was) |
| Manual drift | `manual-drift-check.yml` (`cron: 0 3 * * 3`) + `scripts/check_manual_drift.py` | ✅ running |
| Schema drift (live) | `scripts/check_drift.py` (`/info/db/...` vs TypedDict) | ✅ local dev tool |
| Scaffolding | `scripts/gen_endpoint.py` | ✅ in the documented add-an-endpoint loop |
| Response handling | 200-with-`error` body, non-JSON body, empty-table shapes, failed-analysis message | ✅ hardened in v0.12.0/v0.14.0 |
| Write verification | `scripts/live_crud_check.py` — create/read/update/delete round trips, 43 cases in 6 tiers | ✅ **all 43** confirmed live on Civil NX 2026 v2.2, 40 of them on v2.1 too; 36 of the 43 also confirmed on Gen NX v2.1. `/db/NMAS` (the last holdout) used to crash **both** products, root-caused 2026-07-29 (omitted `rmX`/`rmY`/`rmZ`) and worked around in `NodalMass.create()`/`.update()` |
| Version metadata | `__init__.py` `__version__` (hatchling `dynamic`) + `tests/test_version.py` + a tag↔`__version__` check in `publish.yml` | ✅ single source, enforced at release |
| Live verification | `scripts/live_smoke.py` (write round trip), `scripts/live_readonly_sweep.py` (GET breadth) | ✅ 392/398 recorded, now split by `level`: **63 write / 329 read / 6 unverified**, both products |
| Onboarding docs | `docs/{ko,en,zh-tw}/quickstart.md`, `docs/ai-coding/`, `docs/index.md`, `docs/safety.md` risk levels, `docs/recipes/`, `docs/ko/python-basics.md` | ✅ first example read-only + AI-assistant path (v2.1.2); recipe pilot + ko minimal-Python primer + real-session-verified MAPI key step (2026-08-04); ⚠️ still text-only, no screenshots |
| Practitioner layer | Excel round-trip, `recipes`/`easy`, opt-in validation | ❌ not started |

### Write-verification priority

295 of the 390 implemented endpoints answer a live GET; **42 have had a write
round trip proven** against a real server (10 on both products, 32 on Civil).
Answering a GET says an endpoint exists; only a round trip says the SDK's write
shape is the one the server accepts. `scripts/live_crud_check.py`'s tiers close
that gap, ordered by what a real modelling script reaches for rather than by
manual chapter:

| Tier | Covers | Why here |
|---|---|---|
| `core` | groups, nodes, elements, load cases, nodal/beam loads, constraints | the original 10; the regression baseline, proven on Gen since 2026-07-26 |
| `props` | THIK, ESSF, SECF, TSGR, TDMT/TDME/TMAT | every model picks a thickness and a stiffness factor; creep/shrinkage gates PSC and construction stages |
| `boundary` | NSPR, GSTP/GSPR, ELNK, RIGD, MCON, FRLS, OFFS, SSPS | springs and links are the boundary conditions scripts actually write; CONS alone isn't a model |
| `static` | SDSP, NMAS, LTOM, NBOF, FBLD, PSLT, PRES + ch07 ETMP/NTMP | the ch06 remainder, plus the two temperature loads that behave like static loads |
| `stage` | STAG, TMLD, CRPC, CMCS | needs groups by name and a stage id to attach to, so it comes after both |
| `moving` | LLAN, MVHL, MVHC, MVLD (Civil) | last: Civil-only, and the longest prerequisite chain (code → lane → vehicle → case) |

What the live runs settled (see `docs/live_verification_notes.md` for the
evidence): the `boundary` tier passed 9/9 first time, `stage` 4/4 and `moving`
4/4 after fixture fixes, and three defects surfaced that no mocked test could
have caught — `/db/SECF` is keyed by section id and the SDK's docstring said
element id; `/db/MVHL` silently downgrades a standard vehicle to a
user-defined one when `VEHICLE_LOAD_NUM` isn't 1; and `/db/TDMT` and
`/db/TDME` spell the same code differently
(`CODE: "CEB_FIP_2010"`/`"KDS_2016"` vs. `CODENAME: "CEB-FIP(2010)"`/
`"KDS-2016"`) — both documented correctly by the official articles, but easy
to cross-feed and get a false "Wrong Field". One product defect looked severe
enough to gate permanently: **`POST /db/NMAS` crashed both Civil NX and Gen
NX** across 15+ reproductions (multiple Civil versions/builds, a real
production model, a from-scratch minimal model, both products) — until
2026-07-29's root-cause session found it only happens when the optional
`rmX`/`rmY`/`rmZ` fields are omitted, and doesn't when they're sent
explicitly (even as `0.0`, their documented default). `NodalMass.create()`/
`.update()` now fill them in automatically, so the case runs unquarantined
and confirmed. Two more documented-value defects
turned up: `/db/PRES`'s documented default `DIRECTION` of `"NORMAL"` is
rejected on a plate face and omitting the field fails the same way (though
the official article's own footnote already documents this — see the B-4
narrowing in `docs/live_verification_notes.md`); and `/db/CMCS`'s `PRODUCTS`
was corrected to Civil-only after three independent sessions all 404'd it
under Gen despite the manual listing both.

Two rules make the fixtures trustworthy, because on the first Civil run every
failure was a bad fixture rather than an SDK defect. Seeded records go in at
the lowest free key and their case takes the *next* one, so key-honouring
tables (`/db/NODE`) and renumbering tables (`/db/STLD`) land on the same id
either way; and nothing a case deletes is another case's prerequisite. The
report separates a **regression** (a case confirmed live that broke — an SDK
defect suspect, exit 1) from an **unverified failure** (a case that has never
passed, so triage the payload first, exit 3) from a **blocked** case (its
tier's seed failed). A case is only marked `confirmed=True` after it has been
watched passing.

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
- **v0.11.0 ✅ — Phase 6 tooling** (see Phase 6 below for the itemized list):
  CI, weekly manual-drift job, drift/scaffolding/smoke scripts,
  `DbResource.items()`, error hints, ko/en/zh-tw guides.
- **v0.11.1 ✅ — Manual-sync correctness fix**
  — the vendored manual's `DCRM-WALL` changed schema (breaking); added the
  Wall Force result table and the story tables' `ADDITIONAL` params.
- **v0.11.2 ✅ — Enum/spelling correction + README framing**
  — corrected `STORY_DRIFT_METHOD` enum values and direction-key spelling
  (v0.11.1 had transcribed an official-doc typo verbatim; the manual repo
  normalizes those deliberately — this is the incident behind CLAUDE.md's
  "don't transcribe a `[sic]` typo" rule). Also re-verified the `*-ANAL`
  hang on a current build and rewrote `docs/live_verification_notes.md`
  accordingly (same build, not a vendor fix — trigger still unidentified),
  and dropped the official/unofficial framing and trademark line from the
  README.
- **v0.12.0 ✅ — Client correctness** (out-of-band, from a review of
  `src/midas_nx/` rather than of the phase plan — the first release driven by
  auditing the SDK's own behaviour instead of the manual):
  - HTTP 200 carrying an `{"error": {...}}` body now raises `MidasResultError`
    instead of being returned as a successful result. This is the repo's own
    top documented live-server gotcha; it was described in three docstrings
    and handled in none. Opt out with `raise_on_result_error=False`.
  - A non-JSON response (proxy/SSL-inspection appliance answering in the
    product's place) raised a raw `JSONDecodeError` straight past
    `except MidasAPIError`; it now maps into the hierarchy, keeping the
    status-based class so a 401 login page still carries the MAPI-Key hint.
  - `DbResource.items()` raised `AttributeError` on the `{"message": ""}`
    zero-row shape recorded in `live_verification_notes.md`; it now returns
    `{}` and picks the table by value type rather than by position.
  - `post.base.unwrap_table()` — the `/post/TABLE` counterpart to
    `DbResource.items()`, finding the `HEAD`/`DATA` dict by shape. The
    unstable top-level key was documented as a hazard with no helper to
    handle it, and `get_table()`'s own docstring contradicted the finding.
  - `__version__` is now the single source (`dynamic = ["version"]`), with
    `tests/test_version.py` guarding it. It had reported `0.10.0` since
    v0.11.0 because the release step edited only `pyproject.toml`.
- **v0.14.0 ✅ — Write verification, and a table-destroying `delete()`**
  — first session with write permission on a real Civil NX. The new
  `scripts/live_crud_check.py` (create → read → update → delete per resource)
  found `DbResource.delete([id])` **emptying the entire table**, elements
  included, because the manual's documented ID-keyed DELETE body is ignored by
  the server. The undocumented per-id URL works; `delete()` now uses it and
  the old behaviour is named `delete_all()`. Also: `doc.analyze()` raises on
  `{"message": "... Analysis failed."}`, which carries no `error` key and so
  slipped past v0.12.0's check. Ten resources now pass a full round trip. Full
  findings — including `/doc/SAVEAS` returning success for a save that never
  happened, and `verify_connection()` being unable to see a blocked session —
  in `docs/live_verification_notes.md`.
- **v0.13.0 ✅ — Hyper-S is Civil-only + live verification at 295/390**
  — `scripts/live_readonly_sweep.py` (A1, see Phase 6) swept both products
  against real sessions on 2026-07-26 and found the SDK offering the 13
  Hyper-S (`-M1`) endpoints to Gen clients: they answer under Civil NX and
  404 under Gen NX, 21/21 including the 8 unimplemented stubs. Hyper-S is the
  solver MIDASIT shipped with Civil NX, so `PRODUCTS` was simply wrong.
  Corrected via a `HYPER_S_ONLY` constant — deliberately separate from
  `CIVIL_ONLY`, because Hyper-S is expected to reach Gen NX eventually and
  that day this should be one line, not 13. Guarded by
  `tests/db/test_hyper_s_products.py`. A Gen client now raises
  `ProductMismatchError` instead of issuing a request that can only 404.

### Phase 6 ✅ (mostly) — Trust & maintenance foundation  ·  v0.11.0-v0.11.2
Endpoint coverage (Phases 1-5) is done; before layering practitioner features
on top, harden the ground it stands on. **v0.11.0 shipped this phase's tooling
in one pass** (commits `afdcaaf`, `9e837ec`, `6b7fe8c`, `f55fac1`); what's
listed as ⏳ below is the remainder, re-scoped 2026-07-26 against the tree as
it actually is.

**Shipped:**
- **CI: test/lint pipeline ✅** — `.github/workflows/ci.yml` runs `pytest` +
  `ruff check src tests` on every push to `main` and every PR, across Python
  3.9 and 3.13. Prerequisite for the manual-drift job; both are live.
- **D1 ✅ — vendoring pipeline wired into CI.** `manual-drift-check.yml`
  (`cron: '0 3 * * 3'`, `issues: write`) checks out the sibling manual repo,
  runs `scripts/check_manual_drift.py` against `coverage.json`'s
  `vendored_at_commit`, and opens/updates an issue with the affected
  `midas_nx` modules. Deliberately pure-diff, no AI in the workflow.
- **D2 ✅ (moved up from Phase 8) — live schema drift checker.**
  `scripts/check_drift.py` diffs every `DbResource`'s TypedDict field names
  against what the live server reports via `/info/db/...` (`DbResource.info()`).
  Needs a running NX session, so it's a local dev tool, not a CI job — that
  split is the point, not a shortfall.
- **D3 ✅ (moved up from Phase 8) — endpoint scaffolding.**
  `scripts/gen_endpoint.py` generates the TypedDict + `DbResource` + test
  boilerplate from a manual chapter; it's now step 1 of the documented
  add-an-endpoint loop in `CLAUDE.md`. Human review stays mandatory.
- **A1, partial ✅ — live verification formalized.** `live_verified` is a real
  per-endpoint field in `coverage.json`, `ROADMAP.md` prints the verification
  rate and the Gen/Civil build table, and `scripts/live_smoke.py` makes the
  next session a rerun rather than a one-off. See ⏳ below for the gap.
- **C2 ✅ — friendlier error messages.** `MidasAuthError.HINT` (MAPI key
  location) and `MidasConnectionError.HINT` (NX process / API-server check)
  in `src/midas_nx/client.py`, ASCII-only per the cp949 console constraint.
- **C1, partial ✅ — multilingual getting-started guides.**
  `docs/{ko,en,zh-tw}/quickstart.md`, linked from the README.
- **B3 ✅ (moved up from Phase 7) — GET response unwrap.**
  `DbResource.items()` in `db/base.py`, available on every subclass.

**Remaining (⏳ — this is what v0.13.0 is for; v0.12.0 was cut for the
client-correctness fixes above instead):**
- **A1 ✅ done 2026-07-26 — both products swept and recorded.**
  `scripts/live_readonly_sweep.py` is committed (GET-only, safe against an open
  model) and its results are recorded per endpoint: `live_verified` went from
  **10/390 to 295/390**. Gen reproduced 2026-07-22 exactly (253 swept, 233 OK,
  the same 20 404s) on a real 710-node analyzed model rather than a blank one,
  which removes model state as an explanation; Civil reproduced exactly too
  (293/273/20). D4's version matrix now has both halves. The old "526
  endpoints" figure in this plan was wrong in both directions — 546 tested /
  506 OK across both products are the real numbers. **What's left on this axis
  is write coverage**, not read: POST/PUT/DELETE is still only exercised by
  `live_smoke.py`'s ~10-endpoint round trip.
- **C1 remainder — a screenshot-driven, zero-python-experience walkthrough.**
  The three quickstarts are still text-only (211/202/188 lines as of v2.1.2,
  up from 129/147/89 — the read-only-first rewrite added content but not
  images; 0 images). The missing piece is the NX-side half: where the MAPI
  key lives, what "API connected" looks like in the GUI, what a failed
  connection looks like. One complete path with pictures beats a
  feature-complete doc site.
- **D4, pulled forward from Phase 8 — per-endpoint version matrix.**
  `coverage.json` already carries `nx_versions` *inside* each `live_verified`
  block and `ROADMAP.md` prints one global build table. Promoting that to a
  real compatibility matrix is now a small step, and it's a natural companion
  to the A1 widening above — do them in the same pass.

> **D6 is dead, not deferred.** It existed to back the README's "covers roughly
> a third of the documented API surface" comparison against MIDASIT's own
> packages. That prose was removed in `4f050f7`/`a1b7026`, and `CLAUDE.md` now
> forbids reintroducing official/unofficial positioning or the comparison.
> There is no claim left to substantiate — don't rebuild the table.

### Phase 7 — Practitioner efficiency
- **B2 — Excel round-trip**, `midas-nx[excel]` extra (keep pandas/openpyxl out
  of the core dependency — `requests`-only import stays a hard invariant).
  `from_excel`/`to_excel` for node/element/load tables and result reports;
  `to_dataframe()` folds in as the pandas primitive underneath.
- **C3 — scenario examples** (2 to start): analyze → extract results → Excel
  summary report; construction-stage bulk model edit. Each example doubles as
  live-verification evidence (Phase 6 A1) and onboarding material (C1).
  `examples/python/` currently holds three single-purpose scripts
  (`quickstart.py`, `kds_wind_load.py`, `simple_beam_load_combination.py`);
  what C3 wants is end-to-end *workflows*, a different thing.

> B3 shipped early, in v0.11.0 — see Phase 6.

### Phase 8 — High-level workflow layer
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

> **Recipe/engineering-task layer inputs (reviewed 2026-08-04):**
> `docs/planning/onboarding_plan_active.md` §11 (a per-recipe doc standard —
> risk level, product, verification status, full runnable code) and
> `docs/planning/documentation_maintenance_architecture_plan.md` §6-7 (an
> engineering-task index generated as navigation over `coverage.json`, not
> copied API text) both propose shapes for this layer for whenever B1 starts.
> The architecture plan's larger ask — a `coverage.json` schema v2 with
> `observations[]` and a 12-state discrepancy FSM tracking MIDASIT dev-team
> ticket review — was judged disproportionate to solo-maintainer scale and
> deferred as an idea, not adopted; only its two verified bugs (a dead
> Troubleshooting link in the ko quickstart, unsanitized production-model
> detail/local paths in public `coverage.json` free text) were fixed, both
> in v2.1.2. **B1 itself (a new `midas_nx.recipes` code module) is still
> deliberately not started** — it's new public API surface with no usage
> feedback yet (v2.1.2 shipped days before this note). What *did* start
> 2026-08-04: a small pilot of the doc-only recipe format from §11 above —
> `docs/recipes/{index,inspect-project,read-nodes-and-elements,get-results}.md`,
> three read-only (risk level 1) recipes built entirely on the existing
> `db.*`/`post.*` API, no new SDK code. This is architecturally a different,
> much lower-commitment thing than B1: it's navigation and worked examples
> over what already ships, not a new versioned API surface, so it doesn't
> need to wait on the same feedback gate. `mkdocs build --strict` passing
> with the new `Recipes` nav section; import statements in all three spot-
> checked against the installed package.

> D2 (schema drift checker), D3 (endpoint scaffolding) and D4 (version matrix)
> all moved out of this phase: D2/D3 shipped in v0.11.0, and D4 is now folded
> into Phase 6's A1 remainder since `coverage.json` already records
> `nx_versions` per live-verified endpoint. See Phase 6.

### v1.0.0 — public API freeze
Gate: (a) the 8 undocumented Hyper-S `-M1` stubs resolved; (b) live
verification covering the core paths; (c) the manual-diff pipeline having
caught and survived a real upstream change. Matches D5 from the 2026-07-21
roadmap review: 1.0 means "frozen public surface + live-verified core paths +
a running change-detection pipeline," not just "endpoint count is high."

Status after 2026-07-29:

- **(a) is now resolved.** Went with option 1 (the author's explicit choice,
  "1번으로 해서 진행"): implemented all 8 stubs (`StructureTypeHyperS`,
  `MaterialHyperS`, `InelasticFiberMaterialLinkHyperS`, `PlasticMaterialHyperS`,
  `InelasticHingePropertyHyperS{Beam,Truss,GeneralLink,Pss}`) with payload
  TypedDicts derived from live `GET /info/db/...` introspection rather than a
  manual Specifications table, documented in-module as server-derived. 5 of 8
  have a directly-confirmed `/info` schema (`STYP-M1`, `MATL-M1`, `IMFM-M1`,
  `EPMT-M1`, `IEHG-BEAM-M1`); the other 3 (`IEHG-TRUSS-M1`, `IEHG-GL-M1`,
  `IEHG-PSS-M1`) have no `/info` route at all (404, even though GET works),
  so their single-field shape is assumed by sibling analogy to `IEHG-BEAM-M1`
  and flagged as such, not independently confirmed. Two Hyper-S variants
  (`MATL-M1`, `IMFM-M1`) turned out to have a genuinely different wire shape
  from their non-Hyper-S sibling (0-indexed `P_TYPE` vs 1-indexed; nested
  `CONCRETE`/`STEEL` sub-objects with different field names vs flat fields) —
  not just a product gate on an identical schema. Coverage is now 398/398
  (100%); `docs/coverage.json`/`ROADMAP.md`/`tests/db/test_hyper_s_products.py`
  (13→21) updated; 680 tests passing. This is a genuine `src/` addition
  (new classes, new client behavior), so it adds to the pending version-bump
  case, see the project memory.
- **(b) is now met, not half-met.** `scripts/live_crud_check.py` covers 43
  resources across 6 tiers with a full create→read→update→read→delete→read
  round trip: **43/43 confirmed on Civil NX**, **38/43 confirmed on Gen**
  (the other 5 are genuinely Civil-only — `/db/CMCS` and the 4-case moving
  chain — not untested). `/db/NMAS`, the one case that used to gate this
  permanently (crashed both products), was root-caused and fixed 2026-07-29.
  Read paths: 303/398 recorded across both products (the +8 being today's
  Hyper-S stubs), unchanged elsewhere and re-confirmed live the same day with
  zero regressions.
- **(c) is met, and reinforced again today** — not by the automated
  `manual-drift-check.yml` pipeline this time, but by the same live-check
  discipline catching a real, severe manual/server mismatch by hand
  (`/db/REBW`'s entire field-name schema, see `docs/live_verification_notes.md`
  and vendor report B-4). Worth flagging as a new consideration for 1.0,
  not yet in this gate's original three criteria: REBW was only caught
  because someone happened to read real populated data back against a real
  model. There is no way to know how many other endpoints carry the same
  kind of undiscovered manual/server mismatch without doing that same
  check broadly — a case for a wider live drift audit before declaring the
  public surface frozen, not just an endpoint-count or route-existence
  check. Not resolved; a call for the author.

**All three original gate criteria are now met.** The only open item is the
newly-surfaced (c)-adjacent question above (wider live drift audit before
freezing) — a call for the author, not a blocker by the gate's original text.

**v1.0.0 shipped 2026-07-29** on this basis (GitHub Release + `publish.yml` +
PyPI all confirmed live that day). The wider-live-drift-audit question above
was left open by choice, not resolved — and it caught something the same
day: **v1.1.0 (2026-08-02) broke the freeze**, removing `sect_position` from
`get_table()`/`get_wall_force_table()` (and `parts` from the latter) after
MIDASIT confirmed (Jira MAPI-2012) Wall Force never actually supported
either field — this SDK's fields were an inferred guess, not confirmed
against the product. "Frozen" here has always meant "no *known* reason left
to break it," not "provably will never break" — the open audit question is
exactly why that's the honest framing rather than a stronger guarantee.

### Cross-cutting / backlog (any time)

- ~~Resolve the undocumented Hyper-S stubs~~ — done 2026-07-29, see the
  v1.0.0 gate above.
- Extend write verification further. `scripts/live_crud_check.py` now covers
  43 resources across 6 tiers on both products (43/43 Civil, 38/43 Gen — see
  the v1.0.0 gate above), but the design-chapter (`ch24-27`) and `post/`
  write families still aren't covered by it at all. `/db/REBW`'s 2026-07-29
  discovery (whole field-name schema wrong, only found by reading real
  populated data back) is a concrete argument for extending this checker —
  or some equivalent live-data spot-check — into those chapters before 1.0.
- **Doc-site backlog triage (2026-08-04)**, cross-checking
  `docs/planning/documentation_maintenance_architecture_plan.md` §6.1's
  three-tier nav proposal against what's actually on the MkDocs site:
  - **Done this pass**: tier 3 (developer Reference) had two whole chapter
    families — `post/*` (ch18-23 result extraction) and `design/*` (ch24-27
    RC/steel/SRC code checks) — with no Reference page at all, unlike every
    other module. Not an architecture gap, just missed when `reference/`
    was built; added `docs/reference/post.md` and `docs/reference/design.md`
    (curated examples + a ROADMAP.md pointer, matching `reference/db.md`'s
    existing style — not an exhaustive per-endpoint dump), wired into
    `mkdocs.yml` nav, `mkdocs build --strict` passing.
  - **Also done this pass**: `docs/ko/ai-coding/safe-start.md` — a Korean
    translation of the AI-assisted-coding safe-start page (architecture
    plan §0.3 P1's "한국어 AI 안전 시작 페이지"), wired into `mkdocs.yml`
    nav next to the English original (same "language sub-list" pattern as
    Getting started), and `docs/ko/quickstart.md`'s existing cross-link
    repointed at it. `context-pack.md` deliberately stays English-only,
    single-source, per that same plan's own reasoning (AI-facing content
    that must track the SDK exactly — one canonical version, not N to keep
    in sync). `mkdocs build --strict` passing after both additions.
  - **Tier 2 (engineering-task index / Recipes)**: unchanged from the Phase
    8 note above — still not started, still waiting on Phase 6-7 feedback.
- **Quickstart Step 3 corrected from a real session (2026-08-04).** The
  three quickstarts' "get a MAPI key" step had been describing a menu path
  ("find the Open API menu... choose Issue API Key") never confirmed
  against an actual running Gen NX/Civil NX session. The author walked
  through the real screen: top menu **Apps → API Settings**, which shows
  both **Base URL** and **MAPI-Key** with **Copy** buttons, a **Refresh**
  button to reissue the key, and a **Connected** button whose success
  flips Status to **Connected**. Rewrote Step 3 in all three languages to
  match, and simplified the 🌏 China-server note in the process: since the
  product's own API Settings screen shows the correct Base URL directly,
  there's no need to guess a region from a URL pattern — copy what's
  shown. This is the same category of gap as the Phase 6 C1 remainder
  below (text-only quickstarts describing NX-side UI without having seen
  it) but narrower in scope — one step, not a full screenshot pass.

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
| v0.11.0 ✅ | Phase 6 tooling — CI (`ci.yml`), weekly manual-drift job (D1), drift/scaffolding/smoke scripts (D2/D3/A1), `DbResource.items()` (B3), error hints (C2), ko/en/zh-tw guides (C1 pt. 1) | published |
| v0.11.1 ✅ | Manual-sync fix — `DCRM-WALL` breaking schema change, Wall Force table, story-table `ADDITIONAL` params | published |
| v0.11.2 ✅ | `STORY_DRIFT_METHOD` enum + direction-key spelling correction; `*-ANAL` re-verification writeup; README framing cleanup | published |
| v0.12.0 ✅ | Client correctness — `MidasResultError` for 200-with-`error` bodies, non-JSON responses kept inside the exception hierarchy, `items()` empty-shape fix, `post.base.unwrap_table()`, `__version__` single-sourced | published |
| v0.13.0 ✅ | Hyper-S corrected to Civil-only (`HYPER_S_ONLY`), A1 live sweep complete across both products (295/390), D4 matrix has both halves | published |
| v0.14.0 ✅ | `delete()` no longer empties the table (per-id URL) + `delete_all()`, `analyze()` raises on a failed solve, `scripts/live_crud_check.py` | published |
| ~~v0.15.0~~ | Never shipped as its own release — the planned bundle (53 PRODUCTS corrections, `/db/REBW` schema rewrite, `STORY_IRR_PARAM` enum fix, 8 Hyper-S `-M1` stubs) landed directly in v1.0.0 instead (`5b7fc3c`, `05977a5`), same day the freeze gate closed | superseded by v1.0.0 |
| v1.0.0 ✅ | Public API freeze: all three gate criteria met 2026-07-29 (Hyper-S stub decision resolved, core paths live-verified, manual-diff pipeline survived a real change) — only the wider-live-drift-audit question (surfaced by the REBW find) left open by choice | published — GitHub Release + `publish.yml` + PyPI confirmed live 2026-07-29 |
| v1.1.0 ✅ | First post-freeze breaking change: `get_table()`/`get_wall_force_table()` drop `sect_position`/`parts` per MIDASIT's confirmation (Jira MAPI-2012) Wall Force never supported them; plus the open drift-audit question above catching a real drift on the first sync since the freeze (`STORY_DRIFT_METHOD` "on" vs "at", `VEH_KSCE_LSD15`/`MVLD_CODE=13`) | published 2026-08-02 |
| v2.0.0 ✅ | External-review response. **Breaking:** `delete_all()` requires `confirm=True`. Adds per-request `timeout=`, mypy (clean, 41 modules) + the full 3.9–3.13 CI matrix + a built-wheel smoke test, a read/write split in the live-verification numbers (63 write / 329 read), a MkDocs site with a generated API reference, `SECURITY.md`/`CONTRIBUTING.md` with an explicit SemVer + deprecation policy, absolute README links that survive PyPI, and the employee-led project-status statement | published 2026-08-02 |
| v2.0.1 ✅ | Packaged-metadata-only: README trimmed to a lightweight multilingual (en/ko/zh-tw/zh-cn) landing page, developer-level content consolidated onto the MkDocs site instead of duplicated | published 2026-08-02 |
| v2.1.0 ✅ | Drops Python 3.9/3.10/3.11 support (`requires-python = ">=3.12"`); 3.9 was already 9 months past its own EOL, and three Dependabot floor bumps (requests/mypy/pytest) were stuck behind it | published 2026-08-02 |
| v2.1.1 ✅ | Re-applies the requests/mypy/pytest floor bumps closed for blocking on Python 3.9, now that v2.1.0 dropped it | published 2026-08-02 |
| v2.1.2 ✅ | Packaged-metadata-only: beginner onboarding rewrite — read-only first example everywhere, new `docs/ai-coding/` AI-assistant safety pack, two-path doc-site entry, risk-level (0-4) badges in `docs/safety.md` | published 2026-08-04 |
| v2.1.3 ✅ | Fixes `MidasClient._send()` raising `AttributeError` instead of a `MidasAPIError` subclass when a non-2xx error body's `error` field is a non-dict; two stale-docstring corrections found in the same review pass | published 2026-08-04 |
| v0.16.0/Phase 7 (not started) | Excel round-trip extra (B2), 2 scenario examples (C3) | `pip install midas-nx[excel]` works, examples run against a live session |
| v0.17.0+/Phase 8 (not started) | `recipes`/`easy` high-level layer (B1) once scenarios are validated from Phase 7 feedback, opt-in validation (B4) | |

Each version ships when its phase's chapters are 100% (minus undocumented
stubs) and green in CI. Release = bump `pyproject.toml` version, tag, publish
GitHub Release → `publish.yml` auto-uploads to PyPI.

> Numbering note (2026-07-21): the original Phase 1-5 numbering above was
> chapter/endpoint-coverage-driven and ended at v0.10.0. Phase 6-8 (this
> section) reflect a 2026-07-21 roadmap review's four-axis reprioritization
> (reliability, practitioner efficiency, non-developer accessibility,
> maintenance architecture) — version numbers from v0.14.0 on are provisional
> until each release's actual scope is locked at cut time. v0.12.0 and v0.13.0
> are the mechanism working as intended: both were out-of-band releases driven
> by what live testing turned up, and the phase work shifted down rather than
> the releases being forced into the plan's shape. **Phase headings deliberately
> carry no version number** — only this table does, so a re-cut edits one place.
>
> Version-bump note: a release is warranted only when `src/midas_nx/` behaviour
> or packaged metadata changed. `scripts/`, `docs/`, `.github/` and this file
> don't ship in the wheel — v0.11.0 got a bump because it also touched
> `client.py`/`db/base.py`, not because of the CI and script work. Re-derive
> this from the actual diff each time (`CLAUDE.md` § Releasing).
>
> Staleness note (2026-07-26): this plan spent v0.11.0-v0.11.2 describing
> already-shipped work as pending — most of Phase 6, plus D2/D3 sitting in
> Phase 8 while their scripts were already in the repo and in `CLAUDE.md`'s
> documented workflow. **Re-check §2's non-endpoint status table against the
> tree before planning a release**, and update the "Last updated" line in the
> same commit that changes anything below it.

---

## 5. Working rhythm (per endpoint)

Unchanged from the 02–06 build — the loop that produced the current velocity,
now with step 1 scaffolded (see `CLAUDE.md` § Adding an endpoint for the
canonical version):

1. Scaffold from the manual chapter with `scripts/gen_endpoint.py`, then
   correct it against the vendored manual by hand — the scaffolder gives a
   first draft, not a finished module.
2. Add `DbResource` subclass + `TypedDict` payload in the chapter module.
3. Add a `responses`-mocked test mirroring `tests/db/test_node_element.py`.
4. Mark `"implemented"` in `docs/coverage.json`, re-run `scripts/gen_roadmap.py`.
5. Run `pytest` + `ruff check src tests` before committing the chapter — CI
   runs exactly these on py3.9 and py3.13.
