# v2.3.1 — Fixes a parameter gap in v2.3.0's new endpoint

## English

**Highlights**

- **Fixed:** `get_concurrent_joint_force_table()` (new in v2.3.0) was
  missing `node_elems`/`components`/`opt_cs`/`stage_step` — its
  docstring wrongly said the manual doesn't document them for this
  table. It does; all four are now exposed.
- `ROADMAP.md` regenerated to match a v2.3.0 date fix that was applied
  after the last regeneration.

## 한국어

**주요 변경사항**

- **수정:** v2.3.0에서 새로 추가된 `get_concurrent_joint_force_table()`에
  `node_elems`/`components`/`opt_cs`/`stage_step`이 빠져 있었고,
  독스트링에는 매뉴얼이 이 테이블에 대해 이 항목들을 문서화하지 않는다고
  잘못 적혀 있었습니다. 실제로는 문서화되어 있으며, 이제 네 항목 모두
  사용할 수 있습니다.
- 마지막 재생성 이후 반영된 v2.3.0의 날짜 수정에 맞춰 `ROADMAP.md`를
  재생성했습니다.

## 繁體中文

**重點更新**

- **修正：** v2.3.0 新增的 `get_concurrent_joint_force_table()` 缺少
  `node_elems`/`components`/`opt_cs`/`stage_step`，其文件字串還誤稱手冊
  未針對此表格記載這些參數。實際上手冊已有記載，現已全數開放使用。
- 重新產生 `ROADMAP.md`，以對齊上次產生之後才套用的 v2.3.0 日期修正。

---

Full detailed notes: [`release_notes_v2.3.1.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.3.1.md).
