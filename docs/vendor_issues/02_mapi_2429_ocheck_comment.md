# MAPI-2429 댓글 초안 — OCHECK 재측정 (Build 10/17/2026) 및 공식 문서 게재 상태

> **등록됨: MAPI-2429 댓글 366728** (2026-10-24, 작성자 승인). 대상 이슈 상태는 CANCELED 그대로.
> 근거: `docs/live_verification_notes.md` 2026-10-24 항목, `ledger-read-2026-10-24-1`,
> 공식 Help Center API로 받은 문서 본문 (2026-10-24).

---

**2026-10-24 추가: Civil NX Build 10/17/2026에서 재현, 공식 문서 게재 상태 공유**

비공식 API로 분류된 점은 확인했습니다. 다만 현재 빌드에서도 프로그램이 종료되고, 공식 문서에는
여전히 정식 API로 안내되고 있어 함께 공유드립니다.

**1. 재현 (MIDAS CIVIL NX 2026 v2.2, Build 10/17/2026)**

- 모델: 콘크리트 재질 C24, 일반 콘크리트 단면 1개(DBUSER, SB 0.6×0.6, SRC 대상 아님), 절점 2개, 보 요소 1개. 해석 없음.
- 호출: `POST /TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK`

  ```json
  {"Argument": {"SECT_LIST": [{"SECT_NO": 1, "SECT_DB": "USER"}], "ANALYSIS_OPT": {"ANAL_TIME": 0}, "OUTPUT": {"MODEL_UPDATE": false}}}
  ```

- 결과: 26초 뒤 `404 Client Disconnected`, 이후 모든 호출 `404 client does not exist`, `/mapikey/verify`는 `disconnected`. 프로그램 종료.
- Windows 응용 프로그램 로그 (오류 1000):

  | 일시 | CVLw.exe 타임스탬프 | 오류 모듈 | 예외 / 오프셋 |
  | --- | --- | --- | --- |
  | 2026-07-31 10:18 | 0x6a6a3180 | wg_main.dll | 0xc0000005 / 0xb094e1 |
  | 2026-07-31 10:40 | 0x6a6a3180 | wg_main.dll | 0xc0000005 / 0xb094e1 |
  | 2026-10-24 00:11 | 0x6ad3b719 | wg_main.dll | 0xc0000005 / 0xb09a51 |

  2026-10-24 보고서 ID: `642db7c3-38d8-40d8-a96d-385839227c63`

**2. 공식 문서 게재 상태 (support.midasuser.com, 2026-10-24 확인)**

| 문서 | 최종 수정 | 게재된 경로 | 비공식 안내 |
| --- | --- | --- | --- |
| [DESIGN/SRC/AIK-SRC2K/OCHECK : SRC Optimal Design](https://support.midasuser.com/hc/ko/articles/57472245522201-DESIGN-SRC-AIK-SRC2K-OCHECK-SRC-Optimal-Design) | 2026-05-08 | `DESIGN/SRC/AIK-SRC2K/OCHECK` | 없음 |
| [Steel Optimal Design](https://support.midasuser.com/hc/ko/articles/57389695353241-Steel-Optimal-Design) | 2026-06-22 | `DESIGN/STEEL/KDS-41-30-2022/OCHECK` | 없음 |
| [AIK-SRC2K](https://support.midasuser.com/hc/ko/articles/57711471216537-AIK-SRC2K) (목차) | 2026-07-03 | OCHECK를 3번 항목 "SRC Optimal Design"으로 표기 | 없음 |
| [KDS 41 30 : 2022](https://support.midasuser.com/hc/ko/articles/57678093825049-KDS-41-30-2022) (목차) | 2026-07-03 | `DESIGN/STEEL/KDS-41-30-2022/OCHECK` 표기 | 없음 |

`/TEMP/` 경로 변경(2026-08-06 댓글) 이후 위 문서는 수정되지 않았고, 비공식·개발 중단 안내 없이
변경 전 경로가 정식 API처럼 안내되고 있습니다. `DCHECK`는 공식 문서에서 검색되지 않습니다.

**요청드립니다**

1. 공식 문서에서 SRC/Steel OCHECK 문서를 내리거나, 비공식·개발 중단 API이며 호출 시 프로그램이 종료될 수 있다는 안내를 추가해 주시기 바랍니다.
2. 개발 재개 전까지, 호출 시 프로그램 종료 대신 미지원 오류를 반환하도록 검토 부탁드립니다.
