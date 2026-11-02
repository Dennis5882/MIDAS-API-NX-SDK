# midas-nx 2.10.7

A shared PyPI/npm version release that adds one Python function. Nothing
existing changed behaviour, and the npm package is republished unchanged.

| surface | what actually changed |
| --- | --- |
| Python | **Added** `midas_nx.db.all_resources()`: every resource class the package defines (the 225 `/db/*` tables and the 80 `/DESIGN/*` records), keyed by endpoint and sorted. `DbResource`'s docstring now says what `METHODS` promises and what it does not |
| npm | No change. The same tarball content under the aligned number; npm already publishes the full list as `resources.db` and `resources.design` |

## Why

The resource classes are spread over a dozen modules (`db.properties`,
`db.moving_loads`, `db.boundary`, ..., and `midas_nx.design`), and Python had
no public way to list them: a caller had to import every submodule, and an
MCP server built on the package missed `/db/MATL` and `/db/SECT` that way.

```python
from midas_nx.db import all_resources

tables = {e: c for e, c in all_resources().items() if e.startswith("/db/")}
for endpoint, cls in tables.items():
    print(endpoint, cls.NAME, sorted(cls.PRODUCTS), sorted(cls.METHODS))
```

A test holds the list equal to the one the npm package publishes, so the two
cannot drift apart.

## What `METHODS` means

`METHODS` is the set of verbs the endpoint's contract records - the manual,
corrected where a live call disproved it. It says a verb is documented. It
does not say that a write through it has been verified live on either
product. Before building a write tool on a resource, check its live evidence in
https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/contracts/verification/ledger.yaml.
