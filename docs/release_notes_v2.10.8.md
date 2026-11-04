# midas-nx 2.10.8

A shared PyPI/npm release that adds to both packages. Nothing existing changed
behaviour or type, and nothing was removed.

| surface | what actually changed |
| --- | --- |
| Python | **Added** `LegacyWindLoad` (`/db/WIND`) and `LegacySeismicLoad` (`/db/SEIS`) in `midas_nx.db.static_loads`, and the module `midas_nx.plan` (`order()`, `rank()`, `dependencies()`, `Operation`) |
| npm | **Added** `resources.db.staticLoads.legacyWindLoad` / `legacySeismicLoad` with the payload types `LegacyWindLoadPayload` / `LegacySeismicLoadPayload` (751 -> 753 exported types), and `plan` with `PlanOperation` and the generated `referenceGraph` |

## Legacy wind and seismic loads for the overseas codes

`/db/SWIND` and `/db/SSEIS` take KDS and USER TYPE only. The other codes -
ASCE7, IBC, Eurocode, BS6399, IS875 / IS1893, NSCP, NSR-10, China, Japan,
DPT and more - are only reachable through the legacy `/db/WIND` and
`/db/SEIS`, which MIDASIT keeps without maintenance and the manual does not
document. Both are now resources in both packages, **Gen NX only** (Civil NX
answers neither the route nor `/info`).

```python
from midas_nx.db.static_loads import LegacyWindLoad

# The key is the /db/STLD load case number.
LegacyWindLoad.create({5: {
    "WIND_CODE": "ASCE7(2016)",          # the legacy name, not the dialog's
    "SCALE_FACTOR_X": 1, "SCALE_FACTOR_Y": 0,
    "ASCE7_16": {...},                   # the object of the same code
}})
```

- `WIND_CODE` takes the legacy spellings (`"EURO2005"`, `"CH2001"`,
  `"IS875(87)"`, `"NSCP 2024"`, `"DPT.1311-50:2007"`); `SEIS_LOAD_CODE` takes
  the code object's own name (`"KBC2016"`, `"EURO2004"`).
- **Read the record back after writing it.** A missing required value answers
  `{"message": ""}` and stores nothing, and an out-of-range integer is stored
  with a zero profile - neither raises.
- A whole-table `GET /db/SEIS` fails while a DPT seismic record exists; read it
  by id.

The field lists come from the server's own `/info` schema; methods and the
failure shapes were measured on Gen NX on 2026-11-04.

## `plan.order()`: writes after what they name

```python
from midas_nx import plan
from midas_nx.plan import Operation

ops = plan.order([
    Operation("/db/ELEM", "POST", records={...}),
    Operation("/db/NODE", "POST", records={...}),
])  # NODE first; deletes would come before both, in reverse
```

Offline: nothing is sent. The order comes from a table graph the contracts
now record as `references`, measured on Gen NX and Civil NX on 2026-11-04,
and the two packages hold the same graph. What the products do when the order
is wrong is worth knowing on its own:

- A missing node, load case or group name is refused.
- An element naming a material or section that does not exist is **stored**,
  an orphan.
- `/db/GRUP` and `/db/ELNK` **drop** a missing entry silently.
- A per-id DELETE of a node removes the elements on it, and of a load case the
  loads in it; deleting a material or section in use is not refused.

Details: https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md
