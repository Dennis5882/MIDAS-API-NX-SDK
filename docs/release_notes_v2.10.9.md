# midas-nx 2.10.9

A shared PyPI/npm release that only adds to both packages. No existing
behaviour or type changed, and nothing was removed.

| surface | what actually changed |
| --- | --- |
| Python | **Added** to `midas_nx.plan`: `references()`, `validate()`, `key_policy()`, the data behind them (`REFERENCES`, `KEY_POLICY`) and the `Reference` / `Finding` dataclasses |
| npm | **Added** `plan.references()`, `plan.validate()`, `plan.keyPolicy()`, the generated `referenceFields` / `keyPolicies`, and the types `ReferenceField` / `PlanFinding`. 753 exported payload types, unchanged |

## What a list of writes will do, before it is sent

2.10.8's `plan.order()` puts writes in an order the product accepts. This
release reports on a list before it is sent, using what was measured live.

```python
from midas_nx import plan
from midas_nx.plan import Operation

ops = [Operation("/db/ELEM", "POST", records={"1": {"MATL": 9, "SECT": 1, "NODE": [1, 2]}})]
for f in plan.validate(ops, existing={"/db/MATL": [1], "/db/SECT": [1], "/db/THIK": [], "/db/NODE": [1, 2]}):
    print(f.message)  # ... names 9 in MATL, which /db/MATL will not hold: stored
```

- `plan.references()` lists the 16 fields that name another table's record.
  For each one it says what the product does when the target is missing: the
  write is refused, the record is stored as an orphan, or the value is dropped
  silently. Where it was measured, it also says what deleting the target does
  (`onTargetDelete`):
  - deleting a node removes the elements on it;
  - deleting a load case removes its nodal loads;
  - deleting a material or section in use leaves the elements as orphans.
- `plan.validate()` reports, without raising:
  - each reference the list leaves missing, with the measured outcome;
  - each record that a DELETE in the list removes or orphans.

  It only judges tables you describe in `existing`. A table you leave out is
  never reported as missing.

## Where a POST key lands

`plan.key_policy(endpoint, product)` (npm `plan.keyPolicy`) tells you what
happens to the key you send:

- `"honoured"`: the record is stored under the key you sent.
- `"assigned"`: the product picks the key itself, one past the highest key
  already in the table, so read the table back to learn it.
- No answer: the table was not measured.

This was measured on 2026-11-05 on 120 tables, on both Gen NX (Build
10/17/2026) and Civil NX (Build 10/31/2026). Each table was posted to under a
key that was not the next free one.

- 42 tables assign the key on every product measured, `/db/STLD`, `/db/TDME`
  and `/db/SPFC` among them.
- 73 tables keep the key you sent.
- `/db/FIMP`, `/db/GSTP`, `/db/SPLC`, `/db/TDMF` and `/db/THFC` assign the
  key on Gen NX and keep it on Civil NX.

Details: https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md
