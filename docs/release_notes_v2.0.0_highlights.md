# v2.0.0 — Safety, static typing, and honest verification numbers

## English

**Highlights**

- **⚠️ Breaking:** `delete_all()` now requires `confirm=True` and raises
  `DestructiveOperationError` without it — before sending anything. It empties
  a whole table with no undo, and was the one destructive call with no guard.
  Migration is one keyword; `delete(ids)` is unchanged.
- **Added:** per-request `timeout=`, so calls that can hang can be bounded and
  their results read back separately.
- **Changed:** live-verification counts are now split into **63 write / 329
  read**, instead of one conflated number. A GET proves the route answers; only
  a write round trip proves the request shape is accepted.
- **Fixed:** the README's 12 links were broken on PyPI, and `get_table()`'s
  `additional` parameter had a type no caller could satisfy.
- **New:** a documentation site with a generated API reference, plus
  `SECURITY.md` and `CONTRIBUTING.md`.
- **CI:** mypy (clean), all five supported Python versions, and a built-wheel
  install test that verifies `py.typed` and the safety guard survive packaging.
- This is an employee-led open-source project — **not an officially released or
  supported MIDAS IT product**. Now stated in the README and on PyPI.

## 한국어

**주요 변경사항**

- **⚠️ 주요 변경:** `delete_all()`에 `confirm=True`가 필요합니다. 없으면 요청을
  보내기 **전에** `DestructiveOperationError`가 발생합니다. 테이블 전체를
  되돌릴 수 없이 비우는데도 유일하게 안전장치가 없던 호출이었습니다. 수정은
  키워드 하나이며, `delete(ids)`는 그대로입니다.
- **추가:** 요청별 `timeout=` — 멈출 수 있는 호출에 제한을 두고 결과는 따로
  다시 읽어올 수 있습니다.
- **변경:** 라이브 검증 수치를 **쓰기 63 / 읽기 329**로 분리했습니다. GET이
  응답한다는 건 경로가 살아있다는 뜻일 뿐, SDK가 보내는 요청 형태가 맞다는
  증거는 쓰기 왕복뿐입니다.
- **수정:** README 링크 12개가 PyPI에서 깨져 있었고, `get_table()`의
  `additional` 파라미터는 어떤 호출자도 만족시킬 수 없는 타입이었습니다.
- **신규:** API 레퍼런스가 포함된 문서 사이트, `SECURITY.md`,
  `CONTRIBUTING.md`.
- **CI:** mypy 통과, 지원하는 Python 5개 버전 전체 테스트, 빌드된 wheel을
  설치해 `py.typed`와 안전장치가 실제로 배포되는지 검증.
- 이 프로젝트는 **직원 주도형 오픈소스**이며, 마이다스아이티가 공식적으로
  출시하거나 기술지원하는 제품이 아닙니다. README와 PyPI에 명시했습니다.

## 繁體中文

**重點更新**

- **⚠️ 重大變更：** `delete_all()` 現在必須傳入 `confirm=True`，否則會在送出
  任何請求**之前**拋出 `DestructiveOperationError`。此呼叫會清空整張表且無法
  復原，卻是唯一沒有防護的破壞性操作。修改只需一個關鍵字；`delete(ids)`
  維持不變。
- **新增：** 可針對單次請求指定 `timeout=`，讓可能卡住的呼叫有時間上限，
  結果另外讀回即可。
- **變更：** 實機驗證數量拆分為**寫入 63 / 讀取 329**。GET 有回應只代表路由
  存在；唯有寫入往返才能證明本 SDK 送出的請求格式為伺服器所接受。
- **修復：** README 的 12 個連結在 PyPI 上全部失效；`get_table()` 的
  `additional` 參數型別是任何呼叫端都無法滿足的。
- **新增：** 含自動產生 API 參考的文件網站，以及 `SECURITY.md`、
  `CONTRIBUTING.md`。
- **CI：** mypy 通過、支援的 5 個 Python 版本全部測試，並實際安裝建置出的
  wheel 以驗證 `py.typed` 與安全防護確實隨套件發布。
- 本專案屬於**員工自主的開源專案**，並非 MIDAS IT 官方發布或提供技術支援的
  產品。已於 README 與 PyPI 標示。

---

Full detailed notes: [`release_notes_v2.0.0.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.0.0.md).
