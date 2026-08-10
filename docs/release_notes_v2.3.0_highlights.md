# v2.3.0 — Manual sync: one new result table, two additive load-schema extensions

## English

**Highlights**

- New endpoint: `get_concurrent_joint_force_table()` — extracts joint
  forces concurrent with a reaction node's extreme (max/min) value,
  typically used with moving-load `(MV:max)`/`(MV:min)` cases.
- `StaticWindLoadPayload`/`StaticSeismicLoadPayload` gain fields for a
  `"USER TYPE"` variant that inputs story-level wind pressure/seismic
  force directly instead of the KDS calculation — additive, no breaking
  change.
- `/ope/GSBG`'s new second listing in the manual's Bridge chapter turned
  out to be the same endpoint this SDK already implements, not a new one
  — no code change needed there.

## 한국어

**주요 변경사항**

- 신규 엔드포인트: `get_concurrent_joint_force_table()` — 반력 절점의
  극값(최대/최소) 시점에 동시(concurrent)로 발생하는 절점력을
  추출합니다. 주로 이동하중 `(MV:max)`/`(MV:min)` 하중케이스와 함께
  사용됩니다.
- `StaticWindLoadPayload`/`StaticSeismicLoadPayload`에 KDS 계산식 대신
  층별 풍압/지진력을 직접 입력하는 `"USER TYPE"` 변형용 필드가
  추가됐습니다 — 기존 방식은 그대로 유지되는 추가적 변경입니다.
- 매뉴얼 Bridge 챕터에 새로 등장한 `/ope/GSBG` 항목은 알고 보니 이 SDK가
  이미 구현하고 있던 것과 동일한 엔드포인트였습니다 — 코드 변경 불필요.

## 繁體中文

**重點更新**

- 新端點：`get_concurrent_joint_force_table()`——擷取反力節點達到極值
  （最大/最小）當下，其他指定荷載工況的同時（concurrent）節點力，通常
  搭配移動荷載 `(MV:max)`/`(MV:min)` 工況使用。
- `StaticWindLoadPayload`/`StaticSeismicLoadPayload` 新增欄位，支援
  `"USER TYPE"` 變體，可直接輸入各樓層風壓/地震力，取代 KDS 計算式——
  屬於新增功能，不影響既有呼叫方式。
- 手冊 Bridge 章節新出現的 `/ope/GSBG` 項目，經確認與本 SDK 已實作的端點
  相同，並非新端點——無需修改程式碼。

---

Full detailed notes: [`release_notes_v2.3.0.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.3.0.md).
