# v1.1.0 — Manual sync, first post-freeze breaking change

## English

**Highlights**

- **⚠️ Breaking:** `get_table()`/`get_wall_force_table()` drop `sect_position`
  (and the latter drops `parts` too) — MIDASIT confirmed (Jira `MAPI-2012`)
  Wall Force never supported either field; they were only ever an inferred
  guess from the official article's JSON Schema.
- **Fixed:** `STORY_DRIFT_METHOD`'s first value for Story Stability
  Coefficient is `"Drift on the Center of Mass"`, not `"...at..."` — an
  earlier release's typo-normalization pass wrongly assumed it matched two
  other tables' wording; MIDASIT confirmed the product screen genuinely says
  "on" (Jira `MAPI-2009`).
- **Added:** `VehicleKsceLsd15Params` (`VEH_KSCE_LSD15`) — the schema
  KSCE-LSD15 vehicles actually use instead of `VEH_DEFAULT`, plus the
  correct `MVLD_CODE` (`13`, not `1`).
- **Added:** optional `ADDITIONAL.SET_ANGLE` on Ultimate Story Shear Force
  Check, newly documented by MIDASIT.
- Syncs 3 manual chapters that drifted since v1.0.0 (`docs/coverage.json`'s
  `vendored_at_commit` updated, `check_manual_drift.py` reports clean).

## 한국어

**주요 변경사항**

- **⚠️ 주요 변경:** `get_table()`/`get_wall_force_table()`에서 `sect_position`을
  제거했습니다 (Wall Force는 `parts`도 함께 제거). MIDASIT가 Jira
  `MAPI-2012`로 확인해준 대로, 이 테이블은 애초에 두 필드를 지원한 적이
  없습니다 — 공식 문서의 JSON Schema만 보고 추정했던 필드였습니다.
- **수정:** Story Stability Coefficient의 `STORY_DRIFT_METHOD` 첫 값은
  `"Drift on the Center of Mass"`가 맞습니다(`"at"`이 아님) — 이전 릴리즈의
  오타 정규화 작업이 이 테이블도 다른 두 테이블과 같은 표기를 쓴다고 잘못
  가정했었는데, MIDASIT가 Jira `MAPI-2009`로 제품 화면이 실제로 "on"을
  쓴다고 확인해줬습니다.
- **추가:** `VehicleKsceLsd15Params`(`VEH_KSCE_LSD15`) — KSCE-LSD15 차량이
  `VEH_DEFAULT` 대신 실제로 사용하는 스키마이며, 올바른 `MVLD_CODE`(1이 아닌
  13)도 함께 반영했습니다.
- **추가:** Ultimate Story Shear Force Check에 새로 문서화된 선택적
  `ADDITIONAL.SET_ANGLE`을 추가했습니다.
- v1.0.0 이후 새로 갱신된 매뉴얼 3개 챕터를 동기화했습니다
  (`docs/coverage.json`의 `vendored_at_commit` 갱신, `check_manual_drift.py`
  정상 확인).

## 繁體中文

**重點更新**

- **⚠️ 重大變更：** `get_table()`／`get_wall_force_table()` 移除了
  `sect_position`（Wall Force 也一併移除 `parts`）。MIDASIT 已透過 Jira
  `MAPI-2012` 確認，這個表格從未支援過這兩個欄位 —— 它們原本只是根據官方文件
  JSON Schema 推測出來的欄位。
- **修復：** Story Stability Coefficient 的 `STORY_DRIFT_METHOD` 第一個值應為
  `"Drift on the Center of Mass"`，而非 `"...at..."` —— 先前版本的錯字校正
  誤以為此表格與另外兩個表格用詞相同，MIDASIT 透過 Jira `MAPI-2009` 確認
  產品畫面確實使用 "on"。
- **新增：** `VehicleKsceLsd15Params`（`VEH_KSCE_LSD15`）—— KSCE-LSD15
  車輛實際使用的結構（取代 `VEH_DEFAULT`），並修正正確的 `MVLD_CODE`
  （應為 13，而非 1）。
- **新增：** Ultimate Story Shear Force Check 新增官方新文件化的可選欄位
  `ADDITIONAL.SET_ANGLE`。
- 同步自 v1.0.0 以來手冊變動的 3 個章節（`docs/coverage.json` 的
  `vendored_at_commit` 已更新，`check_manual_drift.py` 確認無差異）。

---

Full detailed notes: [`release_notes_v1.1.0.md`](./release_notes_v1.1.0.md).
