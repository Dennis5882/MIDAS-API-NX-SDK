# v2.1.3 — Fixes a crash in non-2xx error handling

## English

**Highlights**

- Fixes a real bug: a 4xx/5xx response whose body was `{"error": "some
  string"}` (non-dict `error`) crashed with a bare `AttributeError` instead
  of raising `MidasAuthError`/`MidasRequestError`/`MidasServerError` as
  documented — breaking any `except MidasAPIError:` handler. Added a
  regression test.
- Two stale docstrings corrected (no behavior change): `db/dynamic_loads.py`
  THGC and `db/design.py`'s `RebarNameDist`.
- Found via a full review of `src/midas_nx/`; everything else came back
  clean.

## 한국어

**주요 변경사항**

- 실제 버그 수정: 4xx/5xx 응답 본문이 `{"error": "문자열"}`처럼 `error`가
  dict가 아닐 때, 문서화된 `MidasAuthError`/`MidasRequestError`/
  `MidasServerError` 대신 처리되지 않은 `AttributeError`가 발생하던 문제를
  고쳤습니다 — `except MidasAPIError:`로 잡던 코드가 깨지는 원인이었습니다.
  회귀 테스트 추가.
- 낡은 docstring 2건 수정 (동작 변경 없음): `db/dynamic_loads.py`의 THGC,
  `db/design.py`의 `RebarNameDist`.
- `src/midas_nx/` 전체 리뷰 중 발견했으며, 나머지는 전부 정상이었습니다.

## 繁體中文

**重點更新**

- 修正實際錯誤：當 4xx/5xx 回應內容為 `{"error": "字串"}`（`error` 非
  dict）時，會拋出未處理的 `AttributeError`，而非文件記載的
  `MidasAuthError`/`MidasRequestError`/`MidasServerError`——導致
  `except MidasAPIError:` 的錯誤處理失效。已新增回歸測試。
- 修正兩處過時的 docstring（不影響行為）：`db/dynamic_loads.py` 的 THGC、
  `db/design.py` 的 `RebarNameDist`。
- 透過完整檢視 `src/midas_nx/` 發現，其餘部分皆正常。

---

Full detailed notes: [`release_notes_v2.1.3.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.1.3.md).
