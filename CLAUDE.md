# CLAUDE.md — midas-nx

Python SDK wrapping the **MIDAS NX Open API**, one package for both **Civil NX** and **Gen NX**.
Published to PyPI as `midas-nx`. Repo `Dennis5882/MIDAS-API-NX-SDK`, branch `main`.

## Commands

```bash
pip install -e ".[dev]"      # dev setup
pytest                       # full suite, ~600 tests, no live server needed
ruff check src tests         # lint (config in pyproject.toml: select = ["F", "I"])
python scripts/gen_roadmap.py   # regenerate ROADMAP.md from docs/coverage.json
```

Both `pytest` and `ruff check src tests` must pass before any commit — CI (`.github/workflows/ci.yml`)
runs exactly these on Python 3.9 and 3.13.

## Sibling repos on this machine

| Path | What it is |
| --- | --- |
| `E:\AI Study\MIDAS-API` | **The API manual — source of truth for every endpoint schema.** `docs/manual/*.md` |
| `E:\AI Study\Rebar-repair` | QuickRebar NX, a production web tool on the same API. Live-evidence source; its `CLAUDE.md` has a hard-won domain-rules section |

## Where things go

- `src/midas_nx/` — the only thing that ships in the wheel (`packages = ["src/midas_nx"]`).
  - `client.py` — `MidasClient`, `Product` enum, exception hierarchy rooted at `MidasAPIError`.
  - `db/` — `/db/*` endpoints as `DbResource` subclasses.
  - `doc.py` / `ope.py` / `view.py` — `/doc/*`-style endpoints as **plain functions** (wrapped in
    `"Argument"`, not ID-keyed `"Assign"`).
  - `post/` — everything POSTing to the shared `/post/TABLE` (a `TABLE_TYPE` string selects the
    table, so these are functions over one generic `get_table()`, not a resource per table).
  - `design/` — design-code chapters (`rc_kds/`, `steel_kds.py`, `src_aiksrc2k.py`).
- `docs/coverage.json` — the endpoint ledger. `ROADMAP.md` is **generated from it** — never hand-edit
  `ROADMAP.md`.
- `docs/live_verification_notes.md` — findings from real Gen/Civil NX sessions that are *not* in the
  manual. Deliberately kept out of the typed contracts; read it before trusting any `PRODUCTS` change.
- `PLAN.md` — the hand-maintained big-picture roadmap (`ROADMAP.md` is the generated per-endpoint
  counterpart). It is **editable, and goes stale fast**: it spent v0.11.0–v0.11.2 listing shipped
  work as pending, because releases updated the code but not the plan. When a release changes what
  §2's status table or §4's milestone table claims, update them in the same commit, along with the
  "Last updated" line. Verify against the tree before restating status — most of the 2026-07-26
  corrections were things the plan asserted were missing while the file sat in the repo.

## Adding an endpoint

1. Scaffold from the manual chapter:

   ```bash
   python scripts/gen_endpoint.py \
     "E:\AI Study\MIDAS-API\docs\manual\05_DB_Boundary.md" /db/CONS --class-name Constraint
   ```

   (In Git Bash, prefix with `MSYS_NO_PATHCONV=1` or the `/db/CONS` argument gets mangled into a
   Windows path.)
2. Follow `src/midas_nx/db/node_element.py` as the reference pattern. Each resource declares
   `ENDPOINT` / `NAME` / `PRODUCTS` / `METHODS`, with a `{ClassName}Payload` TypedDict directly above
   it in the same module.
3. TypedDicts are **documentation, not runtime validation** — schemas are too conditional for a
   one-size-fits-all model. Put the manual's requiredness/defaults in a trailing comment per field.
4. Add a test mirroring `tests/db/test_node_element.py` (mock HTTP via `responses`, assert the
   request shape — URL, headers, JSON body).
5. Mark it `"implemented"` in `docs/coverage.json`, then rerun `scripts/gen_roadmap.py`.

## Staying in sync with the manual repo

`docs/coverage.json`'s `vendored_at_commit` records which upstream commit this SDK reflects.

```bash
python scripts/check_manual_drift.py --manual-api-repo "E:\AI Study\MIDAS-API"
```

It maps changed chapters to affected `midas_nx` modules. **Bump `vendored_at_commit` only after
actually reflecting the changes**, then confirm it reports `has_diff: false`.

Two things that have already caused rework:

- **The official MIDASIT docs contain typos and self-contradictions, and the manual repo
  deliberately normalizes them** — marked with `⚠️` callouts that often say outright
  "다음 동기화 때 되돌리지 마십시오". Follow the normalized form. Do **not** transcribe an official
  typo verbatim into `src/` with a `[sic]` note; that shipped `"Drfit"` and
  `"Drift on the Center of Mass"` in v0.11.1 and had to be corrected a day later. Cross-check
  against the same enum in other chapters and against each article's own request example.
  Where a contradiction is genuinely unresolved (e.g. `"X_DIR"` in a table vs `"X-DIR"` in the
  working example), declare both and document which to try first.
- **A bulk "정기 점검" sync commit is often followed within a day by self-audit `fix(manual):`
  commits** correcting its own transcription. Re-run the drift checker instead of assuming one
  sync is final.

## Live-server behaviour worth knowing

- **A 200 does not mean success.** Several endpoints return HTTP 200 with an `{"error": {...}}`
  body. Since v0.12.0 `MidasClient._send()` detects this and raises `MidasResultError`
  (opt out with `raise_on_result_error=False`) — don't add a second check per call site, and
  don't regress it: before v0.12.0 the client returned the error dict as a successful result.
- **`/post/TABLE`'s top-level response key is unstable** (seen as `"Result Table"` and `"empty"`
  as well as the `TABLE_NAME` you passed). Match on shape — find the dict carrying `HEAD`/`DATA` —
  not on a key name. `post.base.unwrap_table()` does this; use it instead of indexing by
  `TABLE_NAME`. Confirmed 2026-07-26: **`"empty"` is just the default key for a blank
  `TABLE_NAME`**, and it can carry a full table — never read it as "no data".
- **Every path belongs to the machine running NX, not the one running the script.** Calls go
  through MIDASIT's relay, so the product is often on another PC. `EXPORT_PATH`, `/doc/SAVEAS`,
  `/doc/OPEN`, report and image paths all resolve there. A path that doesn't exist on that machine
  raises a modal dialog *there* and blocks the session, while the HTTP call still answers
  `{"message": "... command complete"}` — identical to success. Build paths from
  `verify_connection()["user"]`, and verify a write with `/doc/OPEN`, never `os.path.exists()`.
  This cost an afternoon of chasing a "broken" `/doc/SAVEAS` that was working fine.
- **`DELETE {endpoint}` with an ID-keyed `"Assign"` body empties the whole table**, ignoring the
  ids — for `/db/NODE` that takes the attached elements with it. This is what the manual documents,
  and it cost a model before it was caught. The undocumented `DELETE {endpoint}/{id}` is the one
  that deletes a single record. `DbResource.delete()` uses it as of v0.14.0; the destructive form is
  `delete_all()`. Don't "simplify" `delete()` back to one request.
- **Not every failure carries an `error` key.** `/doc/ANAL` reports a failed solve as
  `{"message": "... Analysis failed."}` and `/doc/SAVEAS` returns `"... command complete"` for a
  save that never happened. Error bodies also arrive under **201**, not just 200. When adding a
  write endpoint, verify the failure shape live rather than assuming `MidasResultError` covers it.
- **`verify_connection()` can't see a blocked session.** While a modal dialog is up, `/mapikey/verify`
  still answers `"connected"` (the relay serves it) while every `/db/*` call times out.
- **Hyper-S (`-M1`) endpoints are Civil NX only** — it's the solver MIDASIT shipped with Civil NX.
  They 404 under Gen. Use `HYPER_S_ONLY` from `db/base.py`, not `CIVIL_ONLY`: Hyper-S is expected
  to reach Gen NX eventually, and that constant is the one place to widen when it does.
- **Verifying against a live session: `scripts/live_readonly_sweep.py` is the safe one.** It
  issues GET only, so it can run against a model the user has open. `scripts/live_smoke.py` calls
  `/doc/NEW` and **discards unsaved work** — never run it against someone's open document without
  asking first.
- **`scripts/live_crud_check.py` write coverage is tracked in the script itself.** Cases carry
  `confirmed=True` only once someone has watched them pass live (all 43 as of 2026-07-29,
  Civil NX, after `/db/NMAS`'s crash was root-caused and worked around — see above); a failure of
  a confirmed case is a **regression** and exits 1, while a failure of an
  unconfirmed one exits 3 and means "triage the fixture first". Don't flip `confirmed` to silence
  a failure, and don't report an unconfirmed failure as an SDK defect — across three runs every
  failure resolved to a fixture, a wrong documented value, or a product bug, and the one real SDK
  defect was a wrong docstring. Five documented values turned out to be wrong live — `/db/SECF`'s
  key, `/db/PRES`'s default `DIRECTION`, `/db/MVHL`'s `VEHICLE_LOAD_NUM`, the `"KDS2016"`
  time-dependent-material code name, and `/db/TDMT`'s whole code-name enum (it wants `"European"`,
  not any CEB-FIP spelling) — so treat the manual's worked examples as a starting guess.
- **`"Wrong Field"` from a `/db/*` write usually means a bad *value*, not a bad field name.**
  Confirmed on `/db/TDMT` and `/db/TDME`: an unrecognised `CODE`/`CODENAME` answers `Wrong Field`,
  while a recognised one with the wrong companion fields answers `"[Error] ... input data contain
  errors."`. A whole session went into varying fields on `/db/TDMT` before the value was suspected
  — vary the enum value first. Seed steps are per-case dependencies (`needs=`) for the same
  reason: one bad seed used to report 6 false blockages.
- **`*-ANAL` design-check calls** reproducibly hung Gen NX 2026 v2.1 (build 06/23/2026), then ran
  clean on that *same build*. Not a vendor fix; trigger unidentified. Use a short timeout and read
  the `*-TABLE` back regardless of whether the call returned. Full history in
  `docs/live_verification_notes.md`.
- Any call that can raise a **confirmation dialog** blocks the whole API session, not just that
  call, until a human dismisses it.
- **`POST /db/NMAS` used to kill both Civil NX and Gen NX — root cause found and worked around
  2026-07-29.** 15+ reproductions across both products (multiple Civil versions/builds, a real
  production model, a same-LAN-as-the-host caller, a from-scratch minimal fully-connected model)
  first ruled out every wrong explanation — not an idle timeout, not a blocking save-changes
  dialog, not model topology, not which machine the HTTP request comes from — before landing on
  the real one: **the server crashes when the optional `rmX`/`rmY`/`rmZ` fields are omitted from
  the payload, and does not crash when they're sent explicitly, even as `0.0` (their documented
  default)**. Confirmed symmetrically on both products in the same session: a full-fields call
  survives, an immediately following omitted-fields call on a different node kills that same
  session every time — reads as an uninitialized-value read server-side for those three fields
  specifically. `NodalMass.create()`/`.update()` (`db/static_loads.py`) now fill them in
  automatically before sending, so calling the class through this SDK is safe without knowing any
  of this; `live_crud_check.py`'s `/db/NMAS` case runs unquarantined now (`--include-crashers` is
  still there for any future case that needs it). Full reproduction history in
  `docs/live_verification_notes.md`; the vendor report's A-1 now leads with the root cause and
  the workaround, not just "it crashes."
- **`/doc/NEW` has crashed Gen NX** when the open document was a large real model (2026-07-26,
  v2.1 build 06/23/2026) — the "Failed to disconnect the work session" license dialog, which
  always kills the app and holds the license until the process is restarted properly. Harmless
  a dozen times over against small scratch documents the same day. Never point `scripts/live_smoke.py`
  or `scripts/live_crud_check.py` at a session holding a model that matters; get the user to
  press New Project first and confirm the document is empty.

## Releasing

Version bumps are warranted **only when `src/midas_nx/` behaviour or packaged metadata changed** —
`scripts/`, `docs/`, and `.github/` don't ship in the wheel. Re-derive this from the actual diff
each time rather than assuming.

1. Commit the code changes.
2. Separate commit: `chore: bump version to vX.Y.Z` editing only `src/midas_nx/__init__.py`'s
   `__version__`. That is the **single source** — `pyproject.toml` declares `dynamic = ["version"]`
   and hatchling reads it from there. (Until v0.11.2 the bump edited `pyproject.toml` instead, which
   left `midas_nx.__version__` reporting `0.10.0` on a `0.11.2` install; `tests/test_version.py`
   now fails if the two drift apart.)
3. `git push origin main`.
4. **The author publishes the GitHub Release manually via the web UI** (tag `vX.Y.Z`) — `gh` CLI is
   not installed here and no `GITHUB_TOKEN`/`GH_TOKEN` is set, so don't attempt it. Draft the release
   notes for them to paste.
5. That Release triggers `.github/workflows/publish.yml` (PyPI Trusted Publishing).
6. Verify with unauthenticated public APIs:
   `api.github.com/repos/Dennis5882/MIDAS-API-NX-SDK/releases/latest`, the same repo's
   `actions/workflows/publish.yml/runs`, and `pypi.org/pypi/midas-nx/<version>/json`.
   PyPI's `/json` `latest` field caches — query the exact version path to confirm.

## Conventions

- **README framing**: lead with what the SDK does. The author removed all official/unofficial
  positioning and the comparison against MIDASIT's own packages — don't reintroduce it. The README
  carries parallel Korean / 繁體中文 / 简体中文 blocks plus `docs/{ko,en,zh-tw}/quickstart.md`;
  a user-facing wording change usually means touching all of them.
- **Windows consoles are cp949.** Non-ASCII in `print()` or an uncaught traceback either crashes or
  mangles. Scripts call `sys.stdout.reconfigure(encoding="utf-8")`; user-facing exception text stays
  ASCII (hence `(Hint: ...)`, not an em-dash).
- Commit messages: imperative subject, body explaining *why*. Match `git log`.
