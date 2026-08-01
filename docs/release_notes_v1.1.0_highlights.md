# v1.1.0 — Manual sync, first post-freeze breaking change

## English

**Highlights**

- **⚠️ Breaking:** `get_table()`/`get_wall_force_table()` drop `sect_position`
  (Wall Force also drops `parts`) — the server never supported either field.
- **Fixed:** `STORY_DRIFT_METHOD`'s first value for Story Stability
  Coefficient is `"Drift on the Center of Mass"`, not `"...at..."`.
- **Added:** `VehicleKsceLsd15Params` (`VEH_KSCE_LSD15`) for KSCE-LSD15
  vehicles, with the correct `MVLD_CODE` (`13`, not `1`).
- **Added:** optional `ADDITIONAL.SET_ANGLE` on Ultimate Story Shear Force
  Check.
- Syncs 3 manual chapters that drifted since v1.0.0.

## 한국어

**주요 변경사항**

- **⚠️ 주요 변경:** `get_table()`/`get_wall_force_table()`에서 `sect_position`을
  제거했습니다 (Wall Force는 `parts`도 함께 제거) — 서버가 애초에 두 필드를
  지원하지 않았습니다.
- **수정:** Story Stability Coefficient의 `STORY_DRIFT_METHOD` 첫 값은
  `"Drift on the Center of Mass"`가 맞습니다(`"at"`이 아님).
- **추가:** `VehicleKsceLsd15Params`(`VEH_KSCE_LSD15`) — KSCE-LSD15 차량용,
  올바른 `MVLD_CODE`(1이 아닌 13) 포함.
- **추가:** Ultimate Story Shear Force Check에 선택적
  `ADDITIONAL.SET_ANGLE`을 추가했습니다.
- v1.0.0 이후 갱신된 매뉴얼 3개 챕터를 동기화했습니다.

## 繁體中文

**重點更新**

- **⚠️ 重大變更：** `get_table()`／`get_wall_force_table()` 移除了
  `sect_position`（Wall Force 也一併移除 `parts`）—— 伺服器從未支援過這兩個
  欄位。
- **修復：** Story Stability Coefficient 的 `STORY_DRIFT_METHOD` 第一個值應為
  `"Drift on the Center of Mass"`，而非 `"...at..."`。
- **新增：** `VehicleKsceLsd15Params`（`VEH_KSCE_LSD15`），用於 KSCE-LSD15
  車輛，並修正正確的 `MVLD_CODE`（應為 13，而非 1）。
- **新增：** Ultimate Story Shear Force Check 新增可選欄位
  `ADDITIONAL.SET_ANGLE`。
- 同步自 v1.0.0 以來手冊變動的 3 個章節。

---

Full detailed notes: [`release_notes_v1.1.0.md`](./release_notes_v1.1.0.md).
