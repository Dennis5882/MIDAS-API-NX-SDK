# midas-nx 2.10.2

A shared PyPI/npm version release. It acts on two downstream apps built on the
npm package. Both call the API only through the raw `request()`, so none of the
resource-level safeguards reached them, and between them they measured three
Gen NX behaviours the SDKs did not know about. Every one was re-measured live
here before anything changed.

> **One change can break a call that works today.** In both SDKs,
> `request()` now refuses a `DELETE` to a bare `/db/<NAME>`, with no id after
> it, unless you confirm it. Code that empties a table that way on purpose
> needs `confirm=True` (Python) or `{ confirm: true }` (npm).

| surface | what actually changed |
| --- | --- |
| Python | `MidasClient.request()` gains `confirm=` and refuses an unconfirmed whole-table `DELETE`. `get_table()` sends a default `COMPONENTS` for `EIGENVALUEMODE`. `get_steel_code_check()` carries a warning, and `get_vibration_mode_shape_table()` documents the default and the response's sub-table keys |
| npm | `request()` and `midasApi()` take `confirm` and refuse the same `DELETE`. `getTable()` sends the same `EIGENVALUEMODE` default. Every table function's options type now accepts `client`, `timeout` and `signal`. `getSteelCodeCheck()` gains a JSDoc warning. No export is added or removed |

## A `DELETE` without an id empties the table, so `request()` now asks first

The manual documents deletion as `DELETE /db/<NAME>` with an ID-keyed
`{"Assign": {...}}` body. The product ignores those ids and clears the whole
table, and for `/db/NODE` it takes the attached elements with it.
`delete_all()`/`deleteAll()` has long demanded a confirmation for that
reason. The raw `request()` sends the same call and had no guard. Steel-Frame,
a multi-storey frame app on the npm package, lost every material to it while
trying to remove one test material. It lost all 324 elements of a frame while
trying to remove its braces.

Both SDKs now raise `DestructiveOperationError` before sending such a call.
Case, a trailing slash and a query string make no difference. A per-record
`DELETE /db/<NAME>/<id>` passes through unchanged, and `delete_all()`/
`deleteAll()` confirm internally, so their callers see no difference:

```python
client.request("DELETE", "/db/MATL/9")                              # one record
client.request("DELETE", "/db/MATL", {"Assign": {}}, confirm=True)  # empties MATL
```

```ts
await client.request("DELETE", "/db/MATL", { Assign: {} }, { confirm: true });
```

## `EIGENVALUEMODE` needs `COMPONENTS`

The vibration mode shape table answered `{"error": {"message": "Unknown
Error"}}` on an analysed model that had eigenvalue results. The app that found
it recorded the failure as intermittent. It is deterministic. On Gen NX
(2026-10-20), every call without `COMPONENTS` failed: five bare calls, and
calls with only `STYLES`, `NODE_ELEMS` or `MODES` added. Every call with
`COMPONENTS` answered: 1500 rows for 125 nodes and 12 modes, plus the five
summary sub-tables.

When no `components` are given, both SDKs now send the list from the manual's
own example: `Node, Mode, UX, UY, UZ, RX, RY, RZ`. A list you pass is sent
unchanged. `PARTICIPATIONVECTORMODE` answers without `COMPONENTS`, so nothing
is added for it. A raw request without `COMPONENTS` still fails.

The summary sub-tables come back keyed with spaces, for example
`"EIGENVALUE ANALYSIS"` and `"MODAL PARTICIPATION MASSES PRINTOUT (1)"`. The
manual writes those keys without spaces, and the documentation now gives the
spaced form (MD-63).

## `getSteelCodeCheck()` can hold the whole session

The tested model was analysed and had a steel design code in `/db/DSTL` but no
`/db/LCOM-STEEL` rows. On it, `/post/STEELCODECHECK` never answered. Gen NX
showed a "No Load Combination exists for Checking." dialog, and every
following call waited behind it, plain GETs included. Closing the dialog
released the session without a restart. Without a steel design code, the same
call answers `{"message": ""}`. That was the only case this repository had
measured before.

The model state that triggers the dialog can't be expressed in the request,
so the SDKs can neither correct nor refuse the call. Both now warn on the
function, and its contract records the risk as session-holding
(`product_crash_risk`, `warn_only`).

## npm: table functions take `client`, `timeout` and `signal`

Each generated table function's options type was a pick of that table's own
fields. That left out the three per-call options `getTable` forwards. So
`tables.result1.getReactionTable({ ..., client })` did not type-check,
although it ran, and so did every other generated table function. The README
example has exactly that shape. The factories now add the per-call options.
This widens the types and narrows nothing.

## Also in this release, shipped in neither package

- Live records for the two apps' Gen rules, all measured on Gen NX:
  - Load-combination names are limited to 20 characters.
  - Two CNLD items for one load case on one node are summed, not dropped.
  - A TRUSS element refuses BMLD.
  - Every `/view/CAPTURE` leaves the window fitted, whatever `ZOOM_LEVEL` it
    was given.
  - PUT creates records that do not exist yet. `/db/STLD` renumbers keys under
    PUT as it does under POST.
  - Any DB write after an analysis discards its results.
  - `STORY_DRIFT` leaves out the top storey's row for every case type.
  - `GB50017-17(S)` database steel is refused.
- The npm README shows per-call `timeout` and `signal`.
- The safety guide no longer tells readers to build paths from
  `verify_connection()["user"]`. That advice was disproved on 2026-08-31.
- The vendored manual moved to `ee5fa8f`, a plug-in-only sync with no change
  to any chapter.
