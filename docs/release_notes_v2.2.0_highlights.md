# v2.2.0 — Manual-driven sync: one breaking rename, one new endpoint

## English

**Highlights**

- **Breaking:** Story Load Summary Table's `TABLE_TYPE` values renamed
  `STORY_LOAD_SUMMARY_X/Y/Z` → `STORY_LOAD_X/Y/Z`. Callers using
  `get_story_load_summary_table()` through this SDK need no code changes.
- `get_story_load_summary_table()`/`get_story_weight_table()` gain
  `unit`/`styles`/`components` (plus `load_case_names` for the Story Load
  table); `get_wall_design_forces_table()` gains `story_names`.
- New endpoint: `RcDesignCodeSelection` (`/DESIGN/RC/DRC`) — selects the
  active RC design code.
- All three changes trace to long-standing requests against MIDASIT
  shipping in the manual's 2026-08-06 sync; endpoint count 398 → 399.

## 한국어

**주요 변경사항**

- **호환성 깨짐(Breaking):** Story Load Summary Table의 `TABLE_TYPE` 값이
  `STORY_LOAD_SUMMARY_X/Y/Z`에서 `STORY_LOAD_X/Y/Z`로 변경됐습니다. 이
  SDK의 `get_story_load_summary_table()`를 통해 호출하던 코드는 수정할
  필요가 없습니다.
- `get_story_load_summary_table()`/`get_story_weight_table()`에
  `unit`/`styles`/`components`(Story Load 쪽은 `load_case_names`도) 추가,
  `get_wall_design_forces_table()`에 `story_names` 추가.
- 신규 엔드포인트: `RcDesignCodeSelection` (`/DESIGN/RC/DRC`) — 활성 RC
  설계 코드를 선택합니다.
- 세 변경 모두 MIDASIT에 오래전 요청했던 사항이 매뉴얼의 2026-08-06
  동기화로 실제 반영된 것입니다. 엔드포인트 수 398 → 399.

## 繁體中文

**重點更新**

- **重大變更（Breaking）：** Story Load Summary Table 的 `TABLE_TYPE` 值從
  `STORY_LOAD_SUMMARY_X/Y/Z` 改為 `STORY_LOAD_X/Y/Z`。透過本 SDK 的
  `get_story_load_summary_table()` 呼叫的程式碼不需要修改。
- `get_story_load_summary_table()`/`get_story_weight_table()` 新增
  `unit`/`styles`/`components`（Story Load 另加 `load_case_names`）；
  `get_wall_design_forces_table()` 新增 `story_names`。
- 新端點：`RcDesignCodeSelection`（`/DESIGN/RC/DRC`）——選擇目前啟用的
  RC 設計規範。
- 以上三項變更都對應早先向 MIDASIT 提出的需求，隨手冊 2026-08-06 的同步
  實際上線。端點數量 398 → 399。

---

Full detailed notes: [`release_notes_v2.2.0.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.2.0.md).
