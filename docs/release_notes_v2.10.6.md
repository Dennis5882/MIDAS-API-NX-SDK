# midas-nx 2.10.6

A shared PyPI/npm version release: three calls that used to reach the server
now fail in the SDK first, and npm gains two `getTable()` options Python
already had.

> **Behaviour change.** Each of these used to be sent and now raises
> (`MidasRequestError` / `DestructiveOperationError` in Python, a rejected
> promise in npm) before anything is sent:
>
> - `delete()` on a resource given a bare string, or an id that is empty,
>   `.`, `..` or contains `/`;
> - npm only: `request("delete", "/db/<NAME>")` in lower case, which emptied
>   the whole table because fetch sends it as `DELETE`;
> - a `/db/PRES` entry whose `DIRECTION` is `None` / `null`.
>
> The server refused the last one anyway. The first two could delete records
> you did not name.

| surface | what actually changed |
| --- | --- |
| Python | `DbResource.delete()` rejects a `str`/`bytes` argument and ids that are `""`, `"."`, `".."` or contain `/`. `PressureLoad` treats `DIRECTION: None` as missing. `doc` module docstring: name a writable directory on the NX host; never derive one from `verify_connection()["user"]` |
| npm | the same `delete()` checks; `request()`'s whole-table DELETE guard is case-insensitive; a required-explicit field set to `null` counts as missing. `getTable()` gains `averageNodalResult` and `nodeFlag` (two optional members on its options type; nothing removed or made required). The request timeout now covers reading the response body, and a stalled body rejects with `MidasConnectionError`. Error text no longer lets an empty `message` hide `error.message`, and shows an error object as JSON rather than `[object Object]` |

## Why

- **A string given to `delete()` was split into characters.** `delete("12")`
  deleted records 1 and 2. Ids such as `".."` or `"1/.."` build a URL that
  can resolve to the bare table path - the form that empties the table.
- **npm's whole-table DELETE guard compared the method in upper case only.**
  `request("delete", "/db/PRES")` passed it and reached the server on
  2026-11-01.
- **`DIRECTION: null` is refused by both products exactly as an omitted one
  is**: `[Error] Errors detected in Pressure Loads Data.(Item:Load
  Direction)`. Both SDKs already required the field; now `null` counts as not
  given.

## Also recorded (no code change)

Measured 2026-11-01 on Gen NX 2026 v2.2 Build 10/30/2026 and Civil NX 2026
v2.3 Build 10/31/2026. `/info` is unchanged from the 2026-10-11 baseline on
both, and GET-only sweeps through both SDKs answered on every resource.

- **`/db/PHGE`'s Assign key is the element**, not a sequence number as the
  manual says, and `ID` is echoed but always reads back 1. It needs a
  pushover hinge property, which only the dialog can make.
- **`/db/IEHG`** assigns once an inelastic hinge property exists and
  `FIBER_NAME` is sent (`""` for a lumped hinge). An RC hinge whose yield
  strengths are computed is refused where the section has no rebar data - in
  the dialog too.
- **`/db/HPCE`** answers `Wrong Key` until `START_STAGE`/`END_STAGE` name a
  heat-of-hydration stage; the manual documents neither field. It stores
  `DIAMETER` as an integer, so a pipe diameter of 0.025 m set through the API
  becomes 0.
- **`/db/ACTL`** round-trips on Gen with Gen's own fields (`ACWC`, no
  `CLATS`). Civil stores every field but `ITER` and `TOL`.

The full measurements are in
https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md.
