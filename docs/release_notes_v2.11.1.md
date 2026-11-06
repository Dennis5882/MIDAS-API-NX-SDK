# midas-nx 2.11.1

A shared PyPI/npm release about the load tables whose record holds every load
case: `plan.validate()` gets one fix and reports one new kind of finding, and a
helper is added. No resource, payload type or request changed.

| surface | what actually changed |
| --- | --- |
| Python | **Fixed** `plan.validate()` merging a PUT into `ITEMS`. **Added** `midas_nx.plan.ITEM_ROWS`, `item_rows()` and `remove_items()`, and findings of kind `"items"`. |
| npm | The same: **added** `plan.itemRows()`, `plan.removeItems()`, the generated `itemRows` / `ItemRow`, and `"items"` in `PlanFinding.kind`. There are still 753 exported payload types. |

## One record holds every load case

`/db/BMLD` (beam loads), `/db/CNLD` (nodal loads) and `/db/PRES` (pressure
loads) keep one record per element or node, with an `ITEMS` entry for each
load case.

Measured on 2026-11-06 on Gen NX and Civil NX. Both products behaved the same:

- A per-id DELETE of the record removes every entry in it.
- A PUT merges `ITEMS` by `ID`: an entry it names is changed, and the rest are
  kept. So a PUT cannot remove an entry, and `ITEMS: []` changes nothing.
- A per-id DELETE followed by a POST of the entries to keep leaves just those
  entries, each under its own `ID`.

## What changed in `plan`

- **Fixed:** `validate()` now merges a PUT into `ITEMS` by `ID`. It used to
  replace the whole list, so after a PUT of one entry it lost the other
  entries' `LCNAME`. A later load-case DELETE then missed those entries.
- `validate()` reports each entry that a DELETE of a known load record takes,
  one finding per entry. These findings have kind `"items"`, the load case as
  `value`, and outcome `"deleted"`.
- `remove_items()` (npm `removeItems()`) returns the DELETE and the POST that
  drop one load case, or the entries with the given ids. Between the two calls
  the record does not exist, so keep the record you read until the POST
  succeeds.

```python
from midas_nx import plan
from midas_nx.plan import Operation

row = {"ITEMS": [{"ID": 1, "LCNAME": "LL", "P": [-5, -5, 0, 0]},
                 {"ID": 2, "LCNAME": "DL", "P": [-10, -10, 0, 0]}]}
for f in plan.validate([Operation("/db/BMLD", "DELETE", ids=[2])], {"/db/BMLD": {"2": row}}):
    print(f.message)
# /db/BMLD DELETE removes record 2 with every ITEMS entry, including ID 1 for 'LL': deleted
# /db/BMLD DELETE removes record 2 with every ITEMS entry, including ID 2 for 'DL': deleted
for op in plan.remove_items("/db/BMLD", 2, row, case="LL"):
    print(op.method, op.ids or op.records)
# DELETE [2]
# POST {'2': {'ITEMS': [{'ID': 2, 'LCNAME': 'DL', 'P': [-10, -10, 0, 0]}]}}
```

Details: https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md
