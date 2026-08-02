# midas-nx

A unified Python SDK for the **MIDAS NX Open API** — one package covering both
**MIDAS Civil NX** and **MIDAS Gen NX**, typed directly against the endpoint schema documented
at [Dennis5882/MIDAS-API](https://github.com/Dennis5882/MIDAS-API). See
[ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md) for what's implemented so far vs. planned.

Built by a MIDAS IT employee, from hands-on verification against real Gen NX and
Civil NX sessions. It is an employee-led open-source project — **not an officially
released or supported MIDAS IT product**. Issues with this SDK belong on
[GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues); questions
about the products, licensing, or the Open API service itself go to MIDAS IT's
official support channels.

> **New to programming?** If you're a structural engineer who's never written Python before,
> [docs/en/quickstart.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/en/quickstart.md) walks through everything from installing
> Python to running your first script.
>
> **한국어 사용자를 위한 안내**: `midas-nx`는 MIDAS Civil NX와 MIDAS Gen NX의 Open API를
> 하나의 Python 패키지로 통합해 감싼 SDK입니다. 두 제품을 함께 다루며, [MIDAS-API 매뉴얼
> 저장소](https://github.com/Dennis5882/MIDAS-API)에 문서화된 스펙을 기준으로 구현되어
> 있습니다. 설치는 `pip install midas-nx`, 사용 예시는 아래 "Quick start" 절을
> 참고하세요. 실제 Gen NX/Civil NX 세션으로 검증한 내용(주의할 점, 알려진 이슈)은
> [docs/live_verification_notes.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md)에 정리되어
> 있습니다. **Python이나 프로그래밍이 처음이신 구조 엔지니어**는
> [docs/ko/quickstart.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/ko/quickstart.md)에서 Python 설치부터 첫
> 스크립트 실행까지 순서대로 안내받으실 수 있습니다.
>
> `midas-nx`는 마이다스아이티 재직자가 실제 제품·API 검증 경험을 바탕으로
> 개발·관리하는 **직원 주도형 오픈소스 프로젝트**입니다. 마이다스아이티가 공식적으로
> 출시하거나 기술지원하는 제품은 아닙니다. SDK 자체의 문제는
> [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)로,
> 제품·라이선스·Open API 서비스 자체에 대한 문의는 마이다스아이티 공식 지원 채널로
> 문의해 주세요.
>
> **繁體中文使用者指南**：`midas-nx` 是將 MIDAS Civil NX 與 MIDAS Gen NX 的 Open API
> 整合為單一 Python 套件的 SDK，同時涵蓋兩種產品，並根據
> [MIDAS-API 手冊儲存庫](https://github.com/Dennis5882/MIDAS-API) 中記載的規格實作。
> 安裝方式為 `pip install midas-nx`，使用範例請參考下方「Quick start」章節。實際在
> Gen NX / Civil NX 連線環境中驗證過的內容（注意事項、已知問題）整理於
> [docs/live_verification_notes.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md)。**從未寫過
> Python 的結構工程師**，可參考
> [docs/zh-tw/quickstart.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/zh-tw/quickstart.md)，內含從安裝 Python 到
> 執行第一支腳本的完整步驟。
>
> 本專案由 MIDAS IT 員工依據實際產品與 API 驗證經驗開發維護，屬於**員工自主的開源
> 專案**，並非 MIDAS IT 官方發布或提供技術支援的產品。SDK 本身的問題請至
> [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)；產品、
> 授權或 Open API 服務本身的問題，請洽 MIDAS IT 官方支援管道。
>
> **简体中文使用指南**：`midas-nx` 是将 MIDAS Civil NX 与 MIDAS Gen NX 的 Open API
> 整合为单一 Python 包的 SDK，同时支持两种产品，并根据
> [MIDAS-API 手册仓库](https://github.com/Dennis5882/MIDAS-API) 中记载的规格实现。
> 安装方式为 `pip install midas-nx`，使用示例请参考下方"Quick start"章节。在实际
> Gen NX / Civil NX 连接环境中验证过的内容（注意事项、已知问题）整理于
> [docs/live_verification_notes.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md)。
>
> 本项目由 MIDAS IT 员工基于实际产品与 API 验证经验开发维护，属于**员工自主的开源
> 项目**，并非 MIDAS IT 官方发布或提供技术支持的产品。SDK 本身的问题请提交至
> [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)；产品、
> 授权或 Open API 服务本身的问题，请联系 MIDAS IT 官方支持渠道。

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

More worked examples in [`examples/python/`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/tree/main/examples/python/): a wind-load plate
(`kds_wind_load.py`) and a 20-element simply-supported beam with a load combination
(`simple_beam_load_combination.py`).

## Design

- **Instance-based `MidasClient`** — no global mutable state; errors raise typed exceptions
  (`MidasAuthError`, `MidasNotFoundError`, ...) instead of killing the process. The most common
  ones (auth, connection, not-found) append a plain-language `(Hint: ...)` suggestion to the
  message — no need to guess what a 401 or a dead connection means.
- **A 200 is not assumed to be success** — several endpoints report a refusal with an
  `{"error": ...}` body under a 2xx status (a story table asked for before the story calculation
  has run, a design check whose preconditions aren't met). Those raise `MidasResultError` rather
  than returning an error dict that looks like a result; pass
  `MidasClient(raise_on_result_error=False)` if you'd rather inspect the body yourself.
- **Unified Gen/Civil** — `MidasClient(product=Product.GEN | Product.CIVIL)`; each resource class
  declares which product(s) it supports (`PRODUCTS`), and calling a Civil-only resource against a
  Gen client raises `ProductMismatchError` by default (`strict_product=False` to only warn).
- **`/db/*` resources** are `DbResource` subclasses with `.create()/.get()/.update()/.delete()`
  classmethods; `TypedDict` payload types document each endpoint's schema (from
  `docs/manual/*.md` in the sibling repo) for editor/type-checker support, without runtime
  payload validation — schemas are too conditional (see e.g. the Eurocode moving-load endpoint,
  5 mutually-exclusive variants) for a one-size-fits-all validated model. `.items()` is a
  convenience alternative to `.get()`: `Node.items()` returns `{1: {"X": 0, ...}, 2: {...}}`
  (int-keyed, unwrapped) instead of `.get()`'s raw `{"NODE": {"1": {...}, ...}}` response shape.
- **`/doc/*` lifecycle** endpoints are plain functions (`doc.new_project()`, `doc.save()`, ...) —
  not ID-keyed, wrapped in `"Argument"` rather than `"Assign"`.
- **Connection sanity check + schema fallback** — `client.verify_connection()` wraps the
  server's `/mapikey/verify` health check (is the product alive, is this key valid, which
  product is it) for use right after constructing a client or before a batch of calls. Every
  `DbResource` also has `.info(client=None)`, which asks the server directly for a resource's
  current field/type schema (`GET /info/db/...`) — a fallback for endpoints this SDK hasn't
  wrapped yet, or fields that changed since the vendored manual was last synced.

See `docs/coverage.json` / [ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md) for the full endpoint list, what's
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
exercised against real Gen NX / Civil NX sessions. Notable findings (a Gen NX
application hang that the RC design-check "perform" calls reproducibly
triggered — and that later ran clean on the very same build, so the trigger
is still unidentified and the defensive pattern still matters —
product-availability quirks not documented in the manual, and a couple of
"documented optional but actually required under X" server validation
quirks) are written up in
[docs/live_verification_notes.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md) — most
of the safe, actionable ones are also inlined as docstring warnings on the
specific functions/fields involved, so `help()`/your editor will surface them
directly.

## Known issues — read before writing anything

These are live-observed behaviours of the MIDAS NX API and products, not bugs
in this package. Full detail and reproductions in
[docs/live_verification_notes.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md).

- **A 200 response does not mean success.** Several endpoints report a refusal
  with an `{"error": {...}}` body under a 2xx status. This package raises
  `MidasResultError` for those. Others don't even do that: `/doc/ANAL` reports
  a failed solve as `{"message": "... Analysis failed."}`, and `/doc/SAVEAS`
  answers `"... command complete"` for a save that never happened. **Verify a
  write by reading it back.**
- **`delete_all()` empties the whole table** — for `/db/NODE` that takes every
  attached element with it, with no undo. It requires `confirm=True`. Use
  `delete([ids])` for specific records.
- **Paths belong to the machine running NX, not the one running your script.**
  Calls go through a relay, so the product is often on another PC.
  `EXPORT_PATH`, `/doc/SAVEAS`, `/doc/OPEN` and report/image paths all resolve
  *there*. A path that doesn't exist on that machine raises a modal dialog on
  that machine and blocks the session, while your HTTP call still returns
  something that looks like success. Build paths from
  `verify_connection()["user"]`, and never trust `os.path.exists()` locally.
- **Any modal dialog blocks the entire API session**, not just the call that
  caused it, until a human dismisses it — and `verify_connection()` still
  answers `"connected"` the whole time. Treat a healthy connection check as
  "the key is valid", not as clearance to proceed.
- **Some calls have crashed the product outright.** The `*-ANAL` design-check
  family and a few design/table endpoints have killed a live session; several
  are reported to MIDAS IT. Use a short per-call `timeout=` and read the
  result back separately rather than blocking on a response that may never
  arrive.
- **Don't run destructive scripts against a model that matters.**
  `scripts/live_smoke.py` calls `/doc/NEW` and discards unsaved work;
  `scripts/live_crud_check.py` writes and deletes real records. Only
  `scripts/live_readonly_sweep.py` is safe against an open model.

## Troubleshooting

`MidasConnectionError` almost always means MIDAS Gen/Civil NX isn't running, isn't connected
via Open API, or the connection died mid-session. `client.verify_connection()` (see Design,
above) is the fastest way to tell those apart — it reports whether the product process is
alive and whether the current MAPI-Key is valid for it, before you burn a request timeout
finding out the hard way.

If the app is running and still won't connect, it's usually a corporate firewall blocking
outbound traffic to the MIDAS relay. Share this with your network/security team:

| Item | Value |
| --- | --- |
| Protocol | `https`, `wss` |
| Port | `443` |
| IP | `121.157.60.1/32` (MIDAS public NAT IP) |
| URI | `https://moa-engineers.midasit.com` |

If your network does SSL inspection/interception on all outbound traffic, `moa-engineers.midasit.com`
needs to be excluded from it — several users have hit silent connection failures caused by SSL
inspection specifically, separate from a plain firewall block. When an appliance answers in the
product's place, you'll get a `MidasServerError` reading `response body is not JSON: '<html>...'` —
that message is the giveaway that something between you and MIDAS is intercepting the request.

## Contributing

See [CONTRIBUTING.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/CONTRIBUTING.md)
for setup, the endpoint-adding loop, live-verification safety rules, and the
versioning/deprecation policy. To report a security issue privately, see
[SECURITY.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/SECURITY.md).

The short version: pick an unimplemented endpoint from [ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md), follow the pattern in
`src/midas_nx/db/node_element.py` (or `doc.py` for `/doc/*`/`/ope/*`/`/view/*`-style plain-function
endpoints), and add a test mirroring `tests/db/test_node_element.py`. Mark it `"implemented"` in
`docs/coverage.json` (see `scripts/gen_roadmap.py`) and regenerate `ROADMAP.md`.

## License

MIT — see [LICENSE](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/LICENSE).
