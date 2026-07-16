# midas-nx

An independent, unified Python SDK for the **MIDAS NX Open API** (MIDAS Civil NX + MIDAS Gen NX).

Unlike MIDASIT's official [`midas-civil`](https://pypi.org/project/midas-civil/) /
[`midas-gen`](https://github.com/MIDASIT-Co-Ltd/midas-gen-python) packages — separate,
near-duplicated codebases per product, covering roughly a third of the documented API surface —
`midas_nx` is a single package for both products, built directly against the endpoint schema
documented at [Dennis5882/MIDAS-API](https://github.com/Dennis5882/MIDAS-API). See
[ROADMAP.md](./ROADMAP.md) for what's implemented so far vs. planned.

This is an unofficial, community project — not affiliated with or endorsed by MIDASIT.

> **한국어 사용자를 위한 안내**: `midas-nx`는 MIDAS Civil NX와 MIDAS Gen NX의 Open API를
> 하나의 Python 패키지로 통합해 감싼 비공식 커뮤니티 SDK입니다. MIDASIT의 공식
> `midas-civil`/`midas-gen` 패키지가 제품별로 나뉘어 있고 문서화된 API 표면의 일부만
> 지원하는 것과 달리, `midas-nx`는 두 제품을 함께 다루며 [MIDAS-API 매뉴얼
> 저장소](https://github.com/Dennis5882/MIDAS-API)에 문서화된 스펙을 기준으로 구현되어
> 있습니다. 설치는 `pip install midas-nx`, 사용 예시는 아래 "Quick start" 절을
> 참고하세요. 실제 Gen NX/Civil NX 세션으로 검증한 내용(주의할 점, 알려진 이슈)은
> [docs/live_verification_notes.md](./docs/live_verification_notes.md)에 정리되어
> 있습니다.
>
> **繁體中文使用者指南**：`midas-nx` 是將 MIDAS Civil NX 與 MIDAS Gen NX 的 Open API
> 整合為單一 Python 套件的非官方社群 SDK。與 MIDASIT 官方的 `midas-civil`/`midas-gen`
> 套件依產品分開、且僅涵蓋部分已文件化 API 不同，`midas-nx` 同時涵蓋兩種產品，並根據
> [MIDAS-API 手冊儲存庫](https://github.com/Dennis5882/MIDAS-API) 中記載的規格實作。
> 安裝方式為 `pip install midas-nx`，使用範例請參考下方「Quick start」章節。實際在
> Gen NX / Civil NX 連線環境中驗證過的內容（注意事項、已知問題）整理於
> [docs/live_verification_notes.md](./docs/live_verification_notes.md)。
>
> **简体中文使用指南**：`midas-nx` 是将 MIDAS Civil NX 与 MIDAS Gen NX 的 Open API
> 整合为单一 Python 包的非官方社区 SDK。与 MIDASIT 官方的 `midas-civil`/`midas-gen`
> 包按产品拆分、且仅覆盖部分已文档化 API 不同，`midas-nx` 同时支持两种产品，并根据
> [MIDAS-API 手册仓库](https://github.com/Dennis5882/MIDAS-API) 中记载的规格实现。
> 安装方式为 `pip install midas-nx`，使用示例请参考下方"Quick start"章节。在实际
> Gen NX / Civil NX 连接环境中验证过的内容（注意事项、已知问题）整理于
> [docs/live_verification_notes.md](./docs/live_verification_notes.md)。

## Use cases

- **Automation** — bulk-create or bulk-edit hundreds of section/material/load entries in one
  script instead of clicking through the GUI one member at a time.
- **Data integration** — pull structural data straight from Excel/pandas or a database into a
  live MIDAS model (or the reverse: pull model/result data out into your existing analysis
  pipeline).
- **Design optimization** — drive an optimization loop with Python's numeric/scientific stack
  (NumPy, SciPy, ...) against real analysis results, iterating section sizes or member layouts
  automatically.

## Install

```bash
pip install midas-nx
```

To contribute or develop against a checkout:

```bash
pip install -e ".[dev]"
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

## Live verification notes

This package's request/response shapes are typed from the vendored manual and
tested with mocked HTTP (see below) — but a subset of endpoints has also been
exercised against real Gen NX / Civil NX sessions. Notable findings (a
confirmed Gen NX application hang triggered by one specific design-check
call, product-availability quirks not documented in the manual, a couple of
"documented optional but actually required under X" server validation
quirks) are written up in
[docs/live_verification_notes.md](./docs/live_verification_notes.md) — most
of the safe, actionable ones are also inlined as docstring warnings on the
specific functions/fields involved, so `help()`/your editor will surface them
directly.

## Contributing

Pick an unimplemented endpoint from [ROADMAP.md](./ROADMAP.md), follow the pattern in
`src/midas_nx/db/node_element.py` (or `doc.py` for `/doc/*`/`/ope/*`/`/view/*`-style plain-function
endpoints), and add a test mirroring `tests/db/test_node_element.py`. Mark it `"implemented"` in
`docs/coverage.json` (see `scripts/gen_roadmap.py`) and regenerate `ROADMAP.md`.

## License

MIT — see [LICENSE](./LICENSE).
