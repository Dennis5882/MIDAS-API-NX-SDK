# v2.3.2 — Third Design-Forces crash confirmed; Gen NX coverage jumps to 337/399

## English

**Highlights**

- **Confirmed:** `BRACEDESIGNFORCES` independently reproduces the same
  Gen NX crash as Column/Beam Design Forces (docstring updated, no code
  change).
- A full Gen NX `DbResource` GET sweep (266/266 clean) plus a manual
  38-endpoint design-chapter batch (view/RC/steel/SRC check-and-report
  functions, including the historically hang-prone `WD-ANAL`) found no
  crashes or hangs. `Verified on Gen NX`: 266/399 → 337/399.

## 한국어

**주요 변경사항**

- **확인:** `BRACEDESIGNFORCES`가 Column/Beam Design Forces와 동일한
  Gen NX 크래시를 독립적으로 재현함 (독스트링만 갱신, 코드 변경 없음).
- Gen NX `DbResource` GET 전수 스윕(266/266 정상)과 설계 챕터 38개
  엔드포인트 수동 검증(view/RC/steel/SRC 체크·리포트 함수, 과거 행 이력이
  있던 `WD-ANAL` 포함)에서 크래시·행 없음을 확인했습니다. Gen NX 검증률
  266/399 → 337/399.

## 繁體中文

**重點更新**

- **確認：** `BRACEDESIGNFORCES` 獨立重現與 Column/Beam Design Forces
  相同的 Gen NX 當機（僅更新文件字串，程式碼未變更）。
- 完整的 Gen NX `DbResource` GET 掃描（266/266 正常）加上 38 個設計章節
  端點的人工驗證（view/RC/steel/SRC 檢核與報告函式，包含過去有卡死紀錄的
  `WD-ANAL`），均未發現當機或卡死。Gen NX 驗證覆蓋率：266/399 → 337/399。

---

Full detailed notes: [`release_notes_v2.3.2.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.3.2.md).
