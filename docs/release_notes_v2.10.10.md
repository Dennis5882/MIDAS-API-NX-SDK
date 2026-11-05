# midas-nx 2.10.10

A shared PyPI/npm release that changes what `plan.validate()` reports. This
follows feedback on 2.10.9 from a project that uses it. No resource, payload
type or request changed.

| surface | what actually changed |
| --- | --- |
| Python | `midas_nx.plan.validate()` reports more, as described below. `Reference` gains `targets_by` and `targets_for()`, and `on_target_delete` can be `"cleared"`. |
| npm | `plan.validate()` changes the same way. `ReferenceField` gains `targetsBy`, and `onTargetDelete` (so also `PlanFinding.outcome`) can be `"cleared"`: a `switch` that lists every value needs the new case. There are still 753 exported payload types. |

## What 2.10.9 missed

- **A plate element naming a section number.** `/db/ELEM`'s `SECT` points to
  a `/db/SECT` or a `/db/THIK` record, depending on the element type. 2.10.9
  accepted any number that either table held.

  Now a `PLATE` is checked against `/db/THIK` and a `BEAM` against
  `/db/SECT`. This was measured on 2026-11-05 by running an analysis on Gen NX
  (Build 10/17/2026) and Civil NX (Build 10/31/2026):

  - a plate fails analysis when its thickness is deleted;
  - a plate solves when it points at a number that only `/db/THIK` holds;
  - a beam fails when it points at a number that only `/db/THIK` holds.

  Other element types were not tested, so they still accept either table.
- **Deleting a section that elements already in the model use.** `existing`
  can now hold a table's records, keyed by id as a GET returns them, instead
  of only their ids. A DELETE then reports every record that names what it
  removes, whether the record is already in the model or written earlier in
  the list.
- **Deleting a load case.** Only `/db/CNLD` had been measured. The other load
  tables were measured on 2026-11-05, and Gen NX and Civil NX behaved the same:
  - Deleting a load case removes, from `/db/BMLD`, `/db/CNLD` and `/db/PRES`,
    the entries that name it. It also removes the `/db/LCOM-GEN` `vCOMB`
    entries that name it. A record with no entries left is deleted.
  - Deleting a load group or a boundary group keeps every record but empties
    the group name. This is the new outcome `"cleared"`.
  - Deleting a thickness that is in use leaves the plate as an orphan.

```python
from midas_nx import plan
from midas_nx.plan import Operation

model = {
    "/db/SECT": [1], "/db/THIK": [1],
    "/db/ELEM": {"4": {"TYPE": "PLATE", "MATL": 1, "SECT": 1, "NODE": [5, 6, 7, 8]}},
    "/db/STLD": {"2": {"NAME": "LL"}},
    "/db/BMLD": {"1": {"ITEMS": [{"ID": 1, "LCNAME": "LL"}]}},
}
for f in plan.validate([Operation("/db/STLD", "DELETE", ids=[2])], model):
    print(f.message)  # ... /db/BMLD record 1 (already in the model) names in ITEMS[].LCNAME: deleted
```

`validate()` now also applies the result of each DELETE before checking the
operations after it. For example, after a node is deleted, the elements on it
no longer exist for the operations that follow. As a result, deleting a node
and then the material of an element on that node reports only the node.

Details: https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md
