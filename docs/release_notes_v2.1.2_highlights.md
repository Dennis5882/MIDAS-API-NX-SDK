# v2.1.2 — Beginner onboarding: read-only first, AI-assisted path, risk levels

## English

**Highlights**

- No SDK behaviour changed — packaged-metadata-only release.
- The first example in README, the docs site, and all three quickstart
  guides is now read-only (`verify_connection()` + `Node.items()`) instead
  of a script that discards unsaved work in whatever model is currently
  open. The old model-building example moved to an explicit, clearly
  risk-labeled optional step.
- New `docs/ai-coding/` section: a context pack to hand an AI coding
  assistant before asking it to write `midas-nx` code, plus a review
  checklist for what it hands back.
- The docs site's homepage now leads with a two-path choice — learn Python,
  or build with an AI assistant — instead of an unordered link table.
- New risk-level labels (0-4) in `docs/safety.md`, applied across the
  updated examples.

## 한국어

**주요 변경사항**

- SDK 동작 변경 없음 — 패키지 메타데이터(문서)만 변경된 릴리즈입니다.
- README, 문서 사이트, 3개 언어 퀵스타트 가이드의 첫 예제가 모두 읽기
  전용(`verify_connection()` + `Node.items()`)으로 바뀌었습니다. 기존
  예제는 열려 있는 모델의 저장하지 않은 작업을 버릴 수 있었는데, 이제는
  위험 등급이 명시된 선택 단계로 옮겼습니다.
- 새 `docs/ai-coding/` 섹션: AI 코딩 도구에게 `midas-nx` 코드를 요청하기
  전에 건네줄 context pack과, 받은 코드를 검토할 체크리스트를 제공합니다.
- 문서 사이트 홈이 순서 없는 링크 표 대신 "Python을 배울지, AI와 함께
  만들지" 두 경로 선택으로 시작합니다.
- `docs/safety.md`에 위험 등급(0~4) 표기를 추가하고 업데이트된 예제 전체에
  적용했습니다.

## 繁體中文

**重點更新**

- SDK 行為未變更 —— 僅為套件中繼資料（文件）異動的版本。
- README、文件網站與三個語言的快速入門指南，第一個範例都改為唯讀
  （`verify_connection()` + `Node.items()`），不再是會捨棄目前開啟模型中
  未儲存工作的建模腳本。原本的建模範例移至明確標示風險等級的選用步驟。
- 新增 `docs/ai-coding/` 章節：在請 AI 程式設計工具撰寫 `midas-nx`
  程式碼前可提供的 context pack，以及檢查其產出的檢查清單。
- 文件網站首頁改為「學 Python」或「用 AI 輔助開發」兩條路徑選擇，取代原本
  無排序的連結表格。
- `docs/safety.md` 新增風險等級（0-4）標示，並套用到更新後的所有範例。

---

Full detailed notes: [`release_notes_v2.1.2.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.1.2.md).
