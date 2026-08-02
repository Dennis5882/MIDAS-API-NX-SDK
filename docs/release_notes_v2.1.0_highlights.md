# v2.1.0 — Drops Python 3.9–3.11

## English

**Highlights**

- **⚠️ Breaking:** `requires-python` is now `>=3.12`. 3.9, 3.10, and 3.11 are
  no longer supported.
- Why: Python 3.9 reached its own end-of-life on 2025-10-31, which was
  blocking three routine dependency updates (`requests`, `mypy`, `pytest`)
  that had themselves already dropped 3.9. 3.12 was chosen to stay clear of
  any version not yet past its own EOL.
- No public API changes otherwise.

## 한국어

**주요 변경사항**

- **⚠️ 주요 변경:** `requires-python`이 `>=3.12`로 올라갔습니다. 3.9, 3.10,
  3.11은 더 이상 지원하지 않습니다.
- 이유: Python 3.9가 2025-10-31에 이미 EOL(지원 종료)되었고, 이 때문에
  `requests`/`mypy`/`pytest`의 일상적인 의존성 업데이트 3건이 막혀 있었습니다
  (해당 패키지들의 새 버전이 이미 3.9 지원을 끊었기 때문). 아직 EOL되지 않은
  가장 낮은 버전인 3.12를 최소 버전으로 선택했습니다.
- 그 외 공개 API 변경은 없습니다.

## 繁體中文

**重點更新**

- **⚠️ 重大變更：** `requires-python` 提高為 `>=3.12`，不再支援 3.9、3.10、
  3.11。
- 原因：Python 3.9 已於 2025-10-31 終止官方支援（EOL），並因此卡住了
  `requests`／`mypy`／`pytest` 三個例行相依套件更新（這些套件的新版本本身
  已不再支援 3.9）。選擇 3.12 作為新的最低版本，以避開任何尚未 EOL 的版本。
- 除此之外沒有其他公開 API 變更。

---

Full detailed notes: [`release_notes_v2.1.0.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/release_notes_v2.1.0.md).
