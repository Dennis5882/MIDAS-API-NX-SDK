# v2.2.1 — SRC Optimal Design follows MIDASIT's path move (still crashes)

## English

**Highlights**

- **Fixed:** `perform_src_optimal_design()` (`OCHECK`) was calling
  `/DESIGN/SRC/AIK-SRC2K/OCHECK`, a path MIDASIT quietly retired — it now
  404s. MIDASIT confirmed this is an unofficial, paused-development API
  and moved it to
  `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK` to mark it as such. The SDK now
  calls the new path.
- **Not a fix, just following the move:** re-tested live 2026-08-07 —
  the new path still crashes the NX session the same way the old one did.
  The docstring now leads with an unofficial/paused-API warning.
- `docs/coverage.json` gains its first `outcome: "crash_or_hang"` entry,
  a new classification for reproducible crash/hang findings.

## 한국어

**주요 변경사항**

- **수정:** `perform_src_optimal_design()`(`OCHECK`)가 MIDASIT이 조용히
  폐기한 경로인 `/DESIGN/SRC/AIK-SRC2K/OCHECK`를 호출하고 있었습니다 —
  이제 이 경로는 404를 반환합니다. MIDASIT은 이 엔드포인트가 개발이
  중단된 비공식 API라고 확인했고, 이를 표시하기 위해
  `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK`로 옮겼습니다. SDK는 이제 새 경로를
  호출합니다.
- **수정이 아니라 경로만 따라간 것입니다:** 2026-08-07 실환경에서
  재테스트한 결과, 새 경로도 예전과 동일하게 NX 세션을 크래시시킵니다.
  독스트링 맨 앞에 비공식/개발중단 경고를 추가했습니다.
- `docs/coverage.json`에 재현 가능한 크래시/행 상태를 나타내는 새 분류값
  `outcome: "crash_or_hang"`이 처음으로 사용되었습니다.

## 繁體中文

**重點更新**

- **修正：** `perform_src_optimal_design()`（`OCHECK`）呼叫的是 MIDASIT
  已悄悄棄用的路徑 `/DESIGN/SRC/AIK-SRC2K/OCHECK`——現在該路徑會回傳
  404。MIDASIT 已確認此端點是暫停開發的非官方 API，並將其移至 `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK` 以標示此狀態。SDK 現在會
  呼叫新路徑。
- **並非修復，只是跟隨路徑異動：** 2026-08-07 於實際環境重新測試，新路徑
  仍會以與舊路徑相同的方式讓 NX 工作階段當機。文件字串開頭現已加上
  非官方/開發暫停警告。
- `docs/coverage.json` 首次使用新分類值 `outcome: "crash_or_hang"`，用於
  標記可重現的當機/無回應情況。

---

Full detailed notes: [`release_notes_v2.2.1.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.2.1.md).
