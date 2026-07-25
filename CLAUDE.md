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
- `PLAN.md` — the author's own roadmap. **Don't edit it.**

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
  body. Check for the key explicitly — a wrapper that only catches non-2xx will report false success.
- **`/post/TABLE`'s top-level response key is unstable** across sessions (seen as both
  `"Result Table"` and `"empty"`). Match on shape — find the dict carrying `HEAD`/`DATA` — not on
  a key name.
- **`*-ANAL` design-check calls** reproducibly hung Gen NX 2026 v2.1 (build 06/23/2026), then ran
  clean on that *same build*. Not a vendor fix; trigger unidentified. Use a short timeout and read
  the `*-TABLE` back regardless of whether the call returned. Full history in
  `docs/live_verification_notes.md`.
- Any call that can raise a **confirmation dialog** blocks the whole API session, not just that
  call, until a human dismisses it.

## Releasing

Version bumps are warranted **only when `src/midas_nx/` behaviour or packaged metadata changed** —
`scripts/`, `docs/`, and `.github/` don't ship in the wheel. Re-derive this from the actual diff
each time rather than assuming.

1. Commit the code changes.
2. Separate commit: `chore: bump version to vX.Y.Z` editing only `pyproject.toml`.
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
