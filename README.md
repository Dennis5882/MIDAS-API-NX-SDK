# midas-nx

Unified Python SDK for the **MIDAS NX Open API** — one package covering both
**MIDAS Civil NX** and **MIDAS Gen NX**.

```bash
pip install midas-nx
```

```python
from midas_nx import MidasClient, Product
from midas_nx.db.node_element import Node

client = MidasClient(mapi_key="your-mapi-key-here", product=Product.GEN)
print(client.verify_connection())
print(f"{len(Node.items(client=client))} node(s) in the current model.")
```

This is read-only — it can't create, change, or delete anything, so it's
safe to run against a real model.

More examples, including ones that build a model:
[`examples/python/`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/tree/main/examples/python/).
Full guide, safety notes, and API reference: **[Documentation site](https://dennis5882.github.io/MIDAS-API-NX-SDK/)**.

---

## English

Built by a MIDAS IT employee, from hands-on verification against real Gen NX
and Civil NX sessions. It's an **employee-led open-source project — not an
officially released or supported MIDAS IT product**. Issues with this SDK go
to [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues);
questions about the products, licensing, or the Open API service itself go to
MIDAS IT's official support channels.

**New to Python?** [docs/en/quickstart.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/en/quickstart.md)
walks through installing Python and running your first script.

## 한국어

`midas-nx`는 MIDAS Civil NX와 MIDAS Gen NX의 Open API를 하나의 Python
패키지로 통합한 SDK입니다. 마이다스아이티 재직자가 실제 제품 검증 경험을
바탕으로 개발·관리하는 **직원 주도형 오픈소스 프로젝트**이며, 마이다스아이티가
공식적으로 출시·지원하는 제품은 아닙니다. SDK 자체의 문제는
[GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)로,
제품·라이선스·Open API 서비스 자체에 대한 문의는 마이다스아이티 공식
지원 채널로 부탁드립니다.

**Python이나 프로그래밍이 처음이신 구조 엔지니어**는
[한국어 퀵스타트 가이드](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/ko/quickstart.md)에서
설치부터 첫 스크립트 실행까지 순서대로 안내받으실 수 있습니다.

## 繁體中文

`midas-nx` 是將 MIDAS Civil NX 與 MIDAS Gen NX 的 Open API 整合為單一
Python 套件的 SDK。由 MIDAS IT 員工根據實際產品驗證經驗開發維護，屬於
**員工自主的開源專案**，並非 MIDAS IT 官方發布或提供技術支援的產品。SDK
本身的問題請至 [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)；
產品、授權或 Open API 服務本身的問題，請洽 MIDAS IT 官方支援管道。

**從未寫過 Python 的結構工程師**，可參考
[繁體中文快速入門指南](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/zh-tw/quickstart.md)，
內含從安裝 Python 到執行第一支腳本的完整步驟。

## 简体中文

`midas-nx` 是将 MIDAS Civil NX 与 MIDAS Gen NX 的 Open API 整合为单一
Python 包的 SDK。由 MIDAS IT 员工基于实际产品验证经验开发维护，属于
**员工自主的开源项目**，并非 MIDAS IT 官方发布或提供技术支持的产品。SDK
本身的问题请提交至 [GitHub Issues](https://github.com/Dennis5882/MIDAS-API-NX-SDK/issues)；
产品、授权或 Open API 服务本身的问题，请联系 MIDAS IT 官方支持渠道。

**Python 新手**可参考
[快速入门指南](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/zh-tw/quickstart.md)（繁体中文版），
了解从安装 Python 到运行第一个脚本的完整步骤。

---

## Learn more

| | |
| --- | --- |
| Full docs & API reference | [Documentation site](https://dennis5882.github.io/MIDAS-API-NX-SDK/) |
| Building with an AI coding assistant instead of writing Python yourself | [Safe start](https://dennis5882.github.io/MIDAS-API-NX-SDK/ai-coding/safe-start/) |
| Known issues / safety notes — read before writing anything | [docs/safety.md](https://dennis5882.github.io/MIDAS-API-NX-SDK/safety/) |
| Endpoint implementation status | [ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md) |
| Contributing / dev setup | [CONTRIBUTING.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/CONTRIBUTING.md) |
| Reporting a security issue | [SECURITY.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/SECURITY.md) |

## License

MIT — see [LICENSE](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/LICENSE).
