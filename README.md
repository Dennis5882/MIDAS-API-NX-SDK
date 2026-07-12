# midas-nx

An independent, unified Python SDK for the **MIDAS NX Open API** (MIDAS Civil NX + MIDAS Gen NX).

Unlike MIDASIT's official [`midas-civil`](https://pypi.org/project/midas-civil/) /
[`midas-gen`](https://github.com/MIDASIT-Co-Ltd/midas-gen-python) packages — separate,
near-duplicated codebases per product, covering roughly a third of the documented API surface —
`midas_nx` is a single package for both products, built directly against the endpoint schema
documented at [Dennis5882/MIDAS-API](https://github.com/Dennis5882/MIDAS-API). See
[ROADMAP.md](./ROADMAP.md) for what's implemented so far vs. planned.

This is an unofficial, community project — not affiliated with or endorsed by MIDASIT.

## Install

```bash
pip install -e ".[dev]"   # from a checkout, for development
```

## Quick start

```python
from midas_nx import MidasClient, Product
from midas_nx import doc
from midas_nx.db.project import Unit
from midas_nx.db.properties.material import Material
from midas_nx.db.properties.section import Section
from midas_nx.db.node_element import Node, Element

client = MidasClient(mapi_key="your-mapi-key-here", product=Product.GEN)

doc.new_project(client=client)

Unit.update({1: {"DIST": "M", "FORCE": "TONF"}}, client=client)

Material.create({1: {
    "TYPE": "CONC", "NAME": "C32",
    "PARAM": [{"P_TYPE": 1, "STANDARD": "AS17(RC)", "DB": "C32"}],
}}, client=client)

Section.create({1: {
    "SECTTYPE": "DBUSER", "SECT_NAME": "H300x150",
    "SECT_BEFORE": {
        "SHAPE": "H", "OFFSET_PT": "CC", "DATATYPE": 1,
        "SECT_I": {"DB_NAME": "KS21", "SECT_NAME": "H300x150x6.5/9"},
    },
}}, client=client)

Node.create({
    1: {"X": 0, "Y": 0, "Z": 0},
    2: {"X": 0, "Y": 0, "Z": 3.2},
}, client=client)

Element.create({1: {
    "TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2], "ANGLE": 0,
}}, client=client)

doc.save(client=client)
```

Or use the low-level free function directly (same calling convention as the
[MIDAS-API manual repo](https://github.com/Dennis5882/MIDAS-API)'s examples):

```python
from midas_nx import configure, MidasAPI

configure(mapi_key="your-mapi-key-here", product="gen")
MidasAPI("POST", "/doc/NEW", {"Argument": {}})
```

## Design

- **Instance-based `MidasClient`** — no global mutable state; errors raise typed exceptions
  (`MidasAuthError`, `MidasNotFoundError`, ...) instead of killing the process.
- **Unified Gen/Civil** — `MidasClient(product=Product.GEN | Product.CIVIL)`; each resource class
  declares which product(s) it supports (`PRODUCTS`), and calling a Civil-only resource against a
  Gen client raises `ProductMismatchError` by default (`strict_product=False` to only warn).
- **`/db/*` resources** are `DbResource` subclasses with `.create()/.get()/.update()/.delete()`
  classmethods; `TypedDict` payload types document each endpoint's schema (from
  `docs/manual/*.md` in the sibling repo) for editor/type-checker support, without runtime
  payload validation — schemas are too conditional (see e.g. the Eurocode moving-load endpoint,
  5 mutually-exclusive variants) for a one-size-fits-all validated model.
- **`/doc/*` lifecycle** endpoints are plain functions (`doc.new_project()`, `doc.save()`, ...) —
  not ID-keyed, wrapped in `"Argument"` rather than `"Assign"`.

See `docs/coverage.json` / [ROADMAP.md](./ROADMAP.md) for the full endpoint list, what's
implemented, and where new endpoints should go.

## Testing

No live MIDAS Gen/Civil NX server is required — all tests mock HTTP via
[`responses`](https://github.com/getsentry/responses) and assert request shape (URL, headers,
JSON body) against what the manual documents.

```bash
pytest
```

## Contributing

Pick an unimplemented endpoint from [ROADMAP.md](./ROADMAP.md), follow the pattern in
`src/midas_nx/db/node_element.py` (or `doc.py` for `/doc/*`/`/ope/*`/`/view/*`-style plain-function
endpoints), and add a test mirroring `tests/db/test_node_element.py`. Mark it `"implemented"` in
`docs/coverage.json` (see `scripts/gen_roadmap.py`) and regenerate `ROADMAP.md`.

## License

MIT — see [LICENSE](./LICENSE).
