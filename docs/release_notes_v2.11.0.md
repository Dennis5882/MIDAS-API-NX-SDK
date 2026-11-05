# midas-nx 2.11.0

A shared PyPI/npm release in which `plan.validate()` reports one more kind of
delete. No resource, payload type or request changed.

| surface | what actually changed |
| --- | --- |
| Python | **Added** `midas_nx.plan.KEY_REFERENCES` and `key_references()`. `validate()` reports records keyed by a node or element. |
| npm | **Added** `plan.keyReferences()` and the generated `keyReferences`. `plan.validate()` changes the same way. There are still 753 exported payload types. |

## Deleting a node or element takes what is keyed by it

Six tables use a node number or an element number as each record's key:

- by node: `/db/CNLD` (nodal loads), `/db/CONS` (supports), `/db/NMAS` (nodal masses);
- by element: `/db/BMLD` (beam loads), `/db/FRLS` (beam end releases), `/db/PRES` (pressure loads).

`plan.order()` already used these keys to order writes, but
`plan.validate()` did not read them.

This was measured on 2026-11-05 on Gen NX (Build 10/17/2026) and Civil NX
(Build 10/31/2026). Both products behaved the same:

- Deleting a node or an element deletes every record keyed by it.
- Deleting a node also deletes the elements on it, and so the records keyed
  by those elements. Deleting a node therefore reaches the beam loads of its
  elements.

`validate()` now reports both of these. The findings appear under
`key_references()` rows, where `field` is `""` because the reference is the
record key itself. A POST keyed by a node or element that will not exist is
reported as refused, as measured on 2026-11-04. `/db/NMAS` was not measured
for this, so it is reported as `unverified`.

```python
from midas_nx import plan
from midas_nx.plan import Operation

model = {
    "/db/ELEM": {"3": {"TYPE": "BEAM", "NODE": [3, 4]}},
    "/db/BMLD": {"3": {"ITEMS": []}},
    "/db/CNLD": {"4": {"ITEMS": []}},
}
for f in plan.validate([Operation("/db/NODE", "DELETE", ids=[4])], model):
    print(f.message)
# /db/NODE DELETE removes 4, which /db/ELEM record 3 (already in the model) names in NODE: deleted
# /db/NODE DELETE removes '4', which /db/CNLD record 4 (already in the model) names in its key: deleted
# /db/NODE DELETE takes /db/ELEM '3' with it, which /db/BMLD record 3 (already in the model) names in its key: deleted
```

Details: https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md
