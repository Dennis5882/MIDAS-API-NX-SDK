# v1.0.0 — Public API Freeze

## English

**Highlights**

- **100% endpoint coverage (398/398)** — the last 8 undocumented Hyper-S `-M1`
  stubs are now implemented, derived from live `GET /info/db/...` server
  introspection instead of a manual table (none existed for them).
- **⚠️ Breaking:** 21 endpoints reclassified Gen NX only (`GEN_ONLY`) — a
  Civil client now raises `ProductMismatchError` for them instead of getting
  a server 404.
- **⚠️ Breaking:** `/db/REBW`'s field names were entirely wrong
  (`VERTICAL_REBAR`/`STORY: {FROM,TO}`/... never matched the server) and have
  been corrected to the real wire shape (`VER_BAR`, `vSTORY_NAME`, ...) —
  update any existing `WallRebar` payloads.
- **Fixed a crash:** `POST /db/NMAS` used to crash both Civil NX and Gen NX;
  root-caused (a missing-field server bug) and auto-worked-around in
  `NodalMass.create()`/`.update()` — no caller-side change needed.
- 32 endpoints wrongly marked Civil-only (moving-load/bridge chapters, etc.)
  now also work on Gen NX and have been reclassified.
- 680 tests passing; write round-trips confirmed on 43/43 Civil and 38/43
  Gen resources.

## 한국어

**주요 변경사항**

- **엔드포인트 커버리지 100% (398/398)** 달성 — 마지막까지 남아있던 Hyper-S
  `-M1` 스텁 8개를 매뉴얼 표 대신 서버 `GET /info/db/...` 라이브 스키마 조회로
  구현했습니다 (해당 엔드포인트들은 매뉴얼에 스펙 표 자체가 없었음).
- **⚠️ 주요 변경:** 21개 엔드포인트를 Gen NX 전용(`GEN_ONLY`)으로 재분류 —
  이제 Civil 클라이언트는 서버 404 대신 `ProductMismatchError`를 즉시 발생시킵니다.
- **⚠️ 주요 변경:** `/db/REBW`의 필드명이 전부 잘못되어 있었습니다
  (`VERTICAL_REBAR`/`STORY: {FROM,TO}` 등은 실제 서버와 전혀 다름) — 실제
  통신 규격(`VER_BAR`, `vSTORY_NAME` 등)에 맞게 수정했습니다. 기존
  `WallRebar` 페이로드를 사용 중이었다면 업데이트가 필요합니다.
- **크래시 수정:** `POST /db/NMAS`가 Civil NX와 Gen NX를 모두 크래시시키던
  문제의 근본 원인(서버 측 필드 누락 버그)을 규명하고, `NodalMass.create()`/
  `.update()`에서 자동으로 우회 처리하도록 수정 — 호출부 변경 불필요.
- 이동하중/교량 챕터 등에서 Civil 전용으로 잘못 분류되어 있던 32개
  엔드포인트가 Gen NX에서도 동작함을 확인하고 재분류했습니다.
- 테스트 680개 통과, Civil 43/43·Gen 38/43 리소스에서 쓰기 왕복(round-trip)
  검증을 완료했습니다.

## 繁體中文

**重點更新**

- **端點覆蓋率達 100%（398/398）** — 最後 8 個未記載的 Hyper-S `-M1` stub
  端點已完成實作，改以即時 `GET /info/db/...` 伺服器 schema 內省方式取得欄位
  定義（因為手冊中原本就沒有這些端點的規格表）。
- **⚠️ 重大變更：** 21 個端點重新分類為僅限 Gen NX（`GEN_ONLY`）— Civil
  客戶端現在會立即拋出 `ProductMismatchError`，而不是等伺服器回傳 404。
- **⚠️ 重大變更：** `/db/REBW` 的欄位名稱完全錯誤（`VERTICAL_REBAR`／
  `STORY: {FROM,TO}` 等從未與伺服器相符），現已修正為實際通訊格式
  （`VER_BAR`、`vSTORY_NAME` 等）— 若你正在使用既有的 `WallRebar` payload，
  請更新欄位名稱。
- **修復當機問題：** `POST /db/NMAS` 曾同時導致 Civil NX 與 Gen NX 當機，
  已找出根本原因（伺服器端欄位遺漏所致的錯誤）並在 `NodalMass.create()`／
  `.update()` 中自動繞過，呼叫端無需修改。
- 32 個原先誤標為僅限 Civil（動態載重／橋梁章節等）的端點，確認在 Gen NX
  上也能運作，已重新分類。
- 680 項測試通過；Civil 43/43、Gen 38/43 個資源的寫入往返（round-trip）
  驗證已完成。

---

Full detailed notes: [`release_notes_v1.0.0.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v1.0.0.md).
