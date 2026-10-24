# [MIDAS API] Civil NX - POST /DESIGN/RC/KDS-41-20-2022/CD-ANAL 호출 시 CIVIL NX 세션 종료 (재현 2회, 서로 다른 빌드, `wg_rcs.dll` 접근 위반)

> **등록됨: MAPI-2968** (2026-10-24, Bug, 상위 MAPI-2427, 우선순위 높음, Fix version v975,
> PMS Category MQC). 등록본은 요청 2번 끝에 "API 문서에도 Gen NX 전용으로 명시"가 추가됨.
> 상위 에픽: MAPI-2427 (API 동작 중 프로그램 종료 이슈).
> 중복 검색 2026-10-23: `project = MAPI AND (text ~ "CD-ANAL" OR text ~ "wg_rcs")` 13건,
> `parent = MAPI-2427` 7건 — 이 증상을 다룬 이슈 없음. 관련 가능: MAPI-2603
> ([CIVIL NX] RC Design API - AASHTO LRFD24, 20, 진행 중).

## 증상

RC 설계 코드가 설정되지 않은 상태에서, 해석이 끝난 모델에
`POST /DESIGN/RC/KDS-41-20-2022/CD-ANAL`을 호출하면 Civil NX가 종료됩니다.

- 호출 24초 뒤 `404 Client Disconnected` 응답, 이후 모든 호출이 `404 client does not exist`
- `/mapikey/verify`는 `"status": "disconnected"`
- `CVLw.exe` 프로세스가 사라지며, 프로그램을 다시 실행해야 합니다

Windows 응용 프로그램 로그(오류 1000 / WER 1001, APPCRASH):

```
CVLw.exe 26.3.24.1001, 타임스탬프 0x6ad3b719
오류 모듈 wg_rcs.dll 1.0.0.1, 타임스탬프 0x6ad3b602
예외 코드 0xc0000005
오류 오프셋 0x000000000003eeae
오류 모듈 경로 E:\MIDAS PROGRAM\MIDAS CIVIL NX\MIDAS CIVIL NX\wg_rcs.dll
보고서 ID ebc3038f-09ef-45d3-8859-f2c210646e31
```

## 재현 환경

- MIDAS CIVIL NX 2026 (v2.2), Build 10/17/2026
- 빈 문서에서 `/doc/NEW` 후 아래 절차 실행

## 재현 절차

1. 모델 작성 (모든 호출 정상 응답)

   | 요청 | 본문 |
   | --- | --- |
   | `PUT /db/UNIT` | `{"Assign": {"1": {"DIST": "M", "FORCE": "KN"}}}` |
   | `POST /db/MATL` | `{"Assign": {"1": {"TYPE": "CONC", "NAME": "C24", "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}}}` |
   | `POST /db/SECT` | `{"Assign": {"1": {"SECTTYPE": "DBUSER", "SECT_NAME": "Column", "SECT_BEFORE": {"USE_SHEAR_DEFORM": true, "SHAPE": "SB", "DATATYPE": 2, "SECT_I": {"vSIZE": [0.6, 0.6]}}}}}` |
   | `POST /db/NODE` | `{"Assign": {"1": {"X": 0, "Y": 0, "Z": 0}, "2": {"X": 0, "Y": 0, "Z": 3.2}}}` |
   | `POST /db/ELEM` | `{"Assign": {"1": {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]}}}` |
   | `POST /db/CONS` | `{"Assign": {"1": {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111"}]}}}` |
   | `POST /db/STLD` | `{"Assign": {"1": {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"}}}` |
   | `POST /db/BODF` | `{"Assign": {"1": {"LCNAME": "DL", "FV": [0, 0, -1]}}}` |
   | `POST /db/LCOM-CONC` | `{"Assign": {"1": {"NAME": "LCOM_CRUD", "ACTIVE": "STRENGTH", "iTYPE": 0, "DESC": "", "vCOMB": [{"ANAL": "ST", "LCNAME": "DL", "FACTOR": 1.0}]}}}` |
   | `PUT /DESIGN/RC/KDS-41-20-2022/MBTP` | `{"Assign": {"1": {"TYPE": "COLUMN"}}}` |

2. RC 설계 코드 설정 시도 — **Civil NX에서 거부됨**

   `PUT /DESIGN/RC/KDS-41-20-2022/DCO`

   ```json
   {"Assign": {"1": {"DESIGN_CD": "KDS 41 20 : 2022", "MOM_CALC_MTHD": "Equivalent", "EXP_COND": "etc", "PM_CRV_CALC": "KeepMPConstant", "CONC_STRS_STRN": "Equivalent", "FS_MAIN_BAR": "2/3fy", "SEISMIC_PROV": true, "TORS_DES": true, "TORS_RDCT_FACT": 1, "MOM_REDIST_FACT": 1, "USE_SUBDIV_FORCE": true, "UG_LC": true, "SEISMIC": {"FRAME_TYPE": "Special", "STRONG_COL_WEAK_LAST": true, "BEAM_COL_JNT_DES": true, "JOINT": {"CHK_POS": "Top", "EXCL_MEM_TYPES": ["SUBBEAM", "CANTIL", "UGBEAMCOL"]}, "SHEAR_WALL": {"SPEC_RC_WALL": true, "BDRY_ELEM_MTHD": "Displacement", "DEFL_AMP_FACT": 4, "IMP_FACT": 1.2}, "SHEAR_DES": {"R": 0.5, "MTHD": "Ve1", "A1": 1.1, "A2": 1.2}}}}}
   ```

   응답: `{"error": {"message": "[Error] Errors detected in Concrete Design Control Data.(Item:)"}}`
   이후 `GET`은 `{"message": ""}` — 설계 코드가 설정되지 않은 상태입니다.
   같은 본문은 Gen NX에서는 정상 저장됩니다.

3. `/doc/SAVEAS`로 저장 후 `POST /doc/ANAL` — `"MIDAS CIVIL NX command complete"`

4. `POST /DESIGN/RC/KDS-41-20-2022/CD-ANAL`

   ```json
   {"Argument": {"PERFORM_TYPE": "ELEMS", "ELEMS": {"KEYS": [1]}}}
   ```

   → 프로그램 종료

## 재현 이력

| 일자 | 빌드 | 결과 | 오류 모듈 / 예외 / 오프셋 |
| --- | --- | --- | --- |
| 2026-09-29 | Build 09/24/2026 (`CVLw.exe` 0x6ab55331) | 종료 | `wg_rcs.dll` / `0xc0000005` / `0x3eeae` |
| 2026-10-23 | Build 10/17/2026 (`CVLw.exe` 0x6ad3b719) | 종료 | `wg_rcs.dll` / `0xc0000005` / `0x3eeae` |

- 두 빌드에서 같은 모듈, 같은 오프셋의 접근 위반입니다.
- 같은 절차를 Gen NX(RC `DCO` 정상 저장)에서 실행하면 `CD-ANAL`이
  `{"message": "success"}`로 끝나고 `CD-TABLE`, `CD-REPORT`도 정상입니다 (2026-09-29).
- 빈 문서에서 `CD-ANAL`을 호출하면 `"Please perform analysis"`로 정상 응답합니다.
- 설계 코드 미설정이 원인인지는 확인되지 않았습니다. Civil NX에서 RC `DCO`가
  거부되어 설계 코드를 설정한 상태와 비교할 수 없습니다.
- 다른 RC 설계 수행 API(`BD-ANAL`, `BRD-ANAL` 등)도 같은지는 확인하지 않았습니다.

## 요청드립니다

1. `wg_rcs.dll` 오프셋 `0x3eeae`의 접근 위반 원인 확인을 부탁드립니다.
   설계 코드가 없는 경우라면 프로그램 종료 대신 오류 응답을 반환하도록 수정을 부탁드립니다.
2. Civil NX에서 KDS 41 20 RC 설계 API(`/DESIGN/RC/KDS-41-20-2022/*`)가 지원 대상인지
   확인 부탁드립니다. `PUT .../DCO`는 위 본문을 `Errors detected in Concrete Design Control
   Data.(Item:)`로 거부하며 `Item`이 비어 있습니다. 지원 대상이 아니라면, `CD-ANAL`을
   포함한 해당 API들이 프로그램 종료 대신 미지원 오류를 반환하도록 부탁드립니다.
