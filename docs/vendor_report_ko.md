# MIDAS NX Open API — 이슈 리포트 (2026-07-27, v1.1)

`/db/*` 43개 엔드포인트에 대해 생성 → 조회 → 수정 → 삭제 왕복을 수행했고, 42개는 정상
동작을 확인했습니다. 아래는 정상 동작하지 않은 항목입니다.

담당 부서가 다를 것으로 보아 **제품 결함(A)과 문서 관련(B)을 분리**했습니다. B는 발송 전
공식 온라인 매뉴얼 원문(2026-07-27 기준)과 다시 대조했습니다.

| 항목 | 내용 |
| --- | --- |
| 제품 | MIDAS CIVIL NX 2026 (A-1은 **MIDAS GEN NX 2026에서도 동일하게 재현** — 아래 참고) |
| 버전 | Civil: **v2.2 (build 06/18/2026)** — 전 항목 확인. A-1·A-2는 v2.1 (build 06/05/2026)에서도 확인. Gen: **v2.1 (build 07/28/2026)** — A-1만 |
| 릴레이 | `https://moa-engineers.midasit.com:443/civil`, `.../gen` |
| 클라이언트 | Python 3.13 + `requests` (SDK 미사용) |

| # | 대상 | 내용 | 심각도 |
| --- | --- | --- | --- |
| A-1 | `/db/NMAS` | **POST 1회로 프로그램이 종료됨. CIVIL·GEN 양쪽 모두 재현** — 7회 | 치명적 |
| A-2 | `DELETE /db/*` | 문서화된 형식이 지정 ID를 무시하고 **테이블 전체를 삭제** | 치명적 |
| A-3 | 3개 엔드포인트 | 쓰기가 무시·변조됐는데 **응답은 성공** | 높음 |
| A-4 | 전역 | 오류 본문이 HTTP **200 / 201**로 반환 | 중간 |
| A-5 | `/mapikey/verify` | 프로그램 종료 후 일정 시간 `"connected"` 반환 | 중간 |
| A-6 | 오류 메시지 | `"Wrong Field"`가 실제로는 **값** 오류를 의미 | 중간 |
| A-7 | 복구 파일 | `Program Files` 하위 기록 시도 → 권한 거부로 조용히 실패 | 낮음 |
| B-1~3 | 매뉴얼 | 기본값·예시·키 처리에 대한 보완 요청 | — |

재현 코드는 `requests`만 사용합니다. 공통 헬퍼:

```python
import requests
BASE = "https://moa-engineers.midasit.com:443/civil"
H = {"Content-Type": "application/json", "MAPI-Key": "<MAPI Key>"}

def call(method, endpoint, body=None, timeout=15):
    r = requests.request(method, BASE + endpoint, headers=H, json=body, timeout=timeout)
    return r.status_code, r.json()
```

A-1은 바로 실행 가능한 단일 파일로도 첨부했습니다 — `vendor_repro_nmas.py`.

---

# A. 제품 결함

## A-1. 🛑 `POST /db/NMAS` 호출 1회로 프로그램이 종료됩니다

```python
call("POST", "/db/NODE", {"Assign": {"9001": {"X": 50, "Y": 50, "Z": 0}}})
# -> 200 정상

call("POST", "/db/NMAS", {"Assign": {"9001": {"mX": 1.0, "mY": 1.0, "mZ": 1.0}}})
# -> ReadTimeout. 이 시점에 프로그램이 종료됩니다.
```

호출이 응답하지 않고, 이후 **모든** `/db/*` 호출이 타임아웃되며 아래 대화상자와 함께
종료됩니다.

> `[Error] Failed to disconnect the work session due to an unidentified error.`
> `Since you have not logged out, other PCs may have limited access to the license.`
> 이어서 `Program will be closed due to an unexpected problem.`

**라이선스가 반환되지 않습니다.** 프로그램을 재실행해 New Project를 누르고 정상 종료해야
회수되므로, 스크립트에서 이 호출이 한 번 발생하면 사람이 개입해야 합니다.

- **CIVIL NX에서 6회 / 2개 버전(v2.1 build 06/05, v2.2 build 06/18)에서 100% 재현**됩니다.
- **GEN NX v2.1 (build 07/28/2026)에서도 같은 방식으로 재현됩니다** — 같은 릴레이 API를
  통해 재현이 시도된 것은 이번이 처음이었고, **첫 시도에서 바로 재현**됐습니다. 오류 문자열도
  이후 호출이 전부 `"client does not exist"`로 실패하는 동일한 패턴이었습니다. 두 제품이
  공유하는 쓰기 경로의 결함으로 보이며, CIVIL NX 한정 문제가 아닙니다.
- `GET /db/NMAS`와 `GET /info/db/NMAS`는 정상입니다. 쓰기 경로 한정으로 보입니다.
- 페이로드는 평범한 절점 1개에 단위질량 3개이며 `/info/db/NMAS` 스키마와 일치합니다.

조사 범위를 좁히시는 데 참고가 될 만한 사항으로, 아래 두 가지는 배제했습니다.

- **유휴 타임아웃 아님** — 32분 공백 후에도 `/db/*` GET 3건이 정상 응답(절점 10개 반환)한
  뒤 이 호출에서만 종료되었고, 공백이 전혀 없는 실행에서도 동일했습니다.
- **모달 대화상자 차단 아님** — `/doc/NEW`를 호출하지 않는 구성으로도 재현됩니다. 직전
  1.3초 내에 쓰기 3건·읽기 2건이 각각 0.2초 이내에 성공했으므로, 대화상자가 열려 있었다면
  이들도 함께 멈췄어야 합니다.

## A-2. 🛑 `DELETE {endpoint}` + ID 지정 `"Assign"`이 테이블 전체를 삭제합니다

매뉴얼 기재 형식대로 호출했을 때 발생하며, 지정한 ID가 무시됩니다.

| 요청 | 결과 |
| --- | --- |
| `DELETE /db/NODE` + `{"Assign": {"21": null}}` | **NODE 10개 → 0개, ELEM 4개 → 0개** |
| `DELETE /db/NODE` + `{"Assign": {"3": {}}}` | 테이블 전체 삭제 |
| `DELETE /db/STLD` + `{"Assign": {"1": {}}}` | 하중조건 2개 모두 삭제 |
| **`DELETE /db/NODE/502`** | **502만 삭제** (기대 동작, 문서에 없음) |

`/db/NODE`는 삭제된 절점에 연결된 요소까지 사라지므로 **단일 호출로 모델이 소실됩니다.**
`/db/NODE`·`/db/STLD`·`/db/LDGR`·`/db/MATL`에서 동일하게 확인했습니다.

응답 본문이 삭제된 **모든** 레코드를 반환하므로 응답을 보면 과다 삭제를 알 수는 있으나,
이미 삭제된 뒤입니다. 문서를 per-ID 형식으로 고치시든 본문 형식이 ID를 존중하도록
고치시든, 현재는 문서를 따라 구현하면 모델이 소실되는 조합입니다.

## A-3. ⚠️ 쓰기가 무시·변조됐는데 응답은 성공을 반환합니다

개별 사안이 아니라 하나의 유형으로 보고 있습니다. 호출 측에서 알아차릴 방법이 레코드를
다시 읽어 비교하는 것뿐입니다.

| 대상 | 입력 | 실제 결과 | 응답 |
| --- | --- | --- | --- |
| `/db/CONS` | `CONSTRAINT` 8자 | 앞 7자로 **절단** → 요청하지 않은 구속 생성 | 200. **응답은 8자 그대로 반환** |
| `/db/MVHL` | `VEHICLE_LOAD_NUM: 2` | `VEHICLE_TYPE_NAME`·`STANDARD_CODE` **폐기**, 사용자정의 차량으로 저장 | 200, 오류 없음 |
| `/db/SECF` | element ID를 키로 사용 | **아무것도 저장되지 않음** | 200, 오류 없음 |

```python
# /db/CONS — 응답도 절단 사실을 알려주지 않습니다
call("POST", "/db/CONS", {"Assign": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}})
# 응답: {"CONS": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}}   8자
call("GET", "/db/CONS")
# 저장: {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111"}]}}              7자
```

6자는 오류로 정상 거부됩니다(`[Error] Constraint Condition has(have) been incorrectly
entered.`). **짧으면 거부하고 길면 조용히 잘라내는 비대칭**이 문제로 보입니다.

```python
# /db/MVHL — VEHICLE_LOAD_NUM 을 2로 보낸 경우
# 전송: {..., "VEHICLE_LOAD_NUM": 2, "VEHICLE_TYPE_NAME": "DB-18",
#             "STANDARD_CODE": "KS-RB", ...}
# 저장: {..., "VEHICLE_LOAD_NUM": 2, "USER_LOAD_TYPE": "Truck/Lane", ...}
#       VEHICLE_TYPE_NAME 과 STANDARD_CODE 가 사라졌습니다.
```

`VEHICLE_LOAD_NUM: 1`이면 `DB-18`·`DB-24`·`DL-24` 모두 정상 저장됩니다. 표준 차량 지정이
실패했다면 오류로 알려주시는 편이 안전합니다.

`/db/SECF`는 **단면 ID**를 키로 받습니다. element ID로 보내면 200이 반환되면서 아무것도
저장되지 않습니다. 잘못된 키를 쓴 저희 쪽 실수였지만, 조회되지 않는 키에 대해 성공을
반환하는 점은 확인을 부탁드립니다.

## A-4. 오류 본문이 HTTP 200 / 201로 반환됩니다

```text
POST /db/TDMT   -> 201  {"error": {"message": "Wrong Field"}}
PUT  /db/TMAT   -> 200  {"error": {"message": "Wrong DB Name"}}
POST /doc/ANAL  -> 200  {"message": "MIDAS CIVIL NX Analysis failed."}
```

마지막 사례는 `error` 키 없이 `message`로만 오는데, 성공 시에도 같은 키를
사용하므로(`"... command complete"`) 상태 코드와 응답 키만으로는 성공·실패를 판정할 수
없습니다.

## A-5. `/mapikey/verify`가 종료된 프로그램에 `"connected"`를 반환합니다

```text
GET /mapikey/verify   -> 0.5초, {"status": "connected"}   <- 프로그램은 이미 종료됨
GET /db/NODE          -> 15초 타임아웃
```

영구적으로 잘못된 값은 아닙니다. 크래시 직후 호출 시 두 차례 `"connected"`였고, 약 30초
뒤에는 `"disconnected"`가 반환되었습니다. **연결 기록이 갱신되기 전까지 낡은 값을 주는
구간**이 있고, 그 구간 때문에 자동화 스크립트의 사전 점검으로 사용할 수 없습니다.

## A-6. `"Wrong Field"`가 실제로는 값 오류를 의미합니다

`/db/TDMT`·`/db/TDME`에서 `CODE`/`CODENAME` 값이 인식되지 않을 때 반환됩니다.

```text
값이 인식되지 않음        -> "Wrong Field"
값은 인식되나 필드 부족   -> "[Error] Time Dependent Material(...) input data contain errors."
```

두 메시지가 구분되어 있는 것은 유용합니다. 다만 `"Field"`라는 단어 때문에 필드 **이름**을
의심하게 됩니다. 실제로 이 문제를 추적할 때 문서상 모든 필드를 하나씩 제거하고 단일 키
페이로드까지 시도한 뒤에야 `CODE` 값이 원인임을 발견했습니다.
`"Unknown value for field 'CODE'"` 정도로 필드명을 함께 주시면 진단이 훨씬 빨라집니다.

## A-7. 크래시 복구 파일이 `Program Files` 하위에 기록되어 실패합니다

```text
C:\Program Files\MIDAS\MIDAS CIVIL NX\DgnPlugIn\_restore.mcb  -> 액세스 거부 (2회)
C:\Users\<user>\Downloads\제목 없음_restore.mcb                -> 정상 저장 (1회)
```

문서 상태에 따라 경로가 달라지며, `Program Files` 하위인 경우 일반 사용자 권한으로
기록할 수 없어 **복구가 조용히 실패합니다.** `%LOCALAPPDATA%` 등 쓰기 가능한 경로를
사용하시는 것이 좋겠습니다.

---

# B. 문서 관련

제품 동작은 정상이며, 공식 온라인 매뉴얼(JSON Manual 섹션) 기재 내용과 관련된 항목입니다.
아래 3건은 **2026-07-27자 공식 아티클 원문을 다시 확인**한 결과만 남긴 것입니다.

| # | 대상 | 아티클 | 내용 |
| --- | --- | --- | --- |
| B-1 | `/db/PRES` | Assign Pressure Loads | `DIRECTION`이 `Optional / 기본값 "NORMAL"`인데, 각주 ¹⁾ 표에서는 해당 조합에 `NORMAL`이 불가로 표기 |
| B-2 | `/db/MVHC` | Vehicle Classes | 예시의 `VEHICLE_LD_NAMES: ["DB-18"]`이 그대로는 동작하지 않음 |
| B-3 | `/db/STLD` | Static Load Cases | `"Assign"` 키의 의미가 명시되어 있지 않음 (이 엔드포인트는 키를 무시하고 재부여) |

## B-1. `/db/PRES` — `DIRECTION`의 기본값과 각주가 서로 맞지 않습니다

각주 ¹⁾의 표는 실제 동작을 **정확히** 기술하고 있습니다.

| Element Types | Normal | Local x/y/z | Global X/Y/Z | Vectors |
| --- | --- | --- | --- | --- |
| `"PLATE"` `"FACE"` | **-** | O | O | O |
| `"PLATE"` `"EDGE"` | O | O | O | O |
| `"SOLID"` `"PRES"` | O | O | O | O |

다만 Specifications 표의 `DIRECTION` 행은 `Default: "NORMAL"`, `Required: Optional`로
되어 있습니다. `PLATE` + `FACE` 조합에서는 두 기술이 양립할 수 없고, 실제로 **필드를
생략하면 요청이 실패합니다.**

```python
# PLATE + FACE, DIRECTION 생략 -> 실패
# PLATE + FACE, DIRECTION: "LZ" -> 정상
```

해당 조합에서는 `DIRECTION`을 Required로 표기하거나, 기본값에 예외를 병기해 주시면
좋겠습니다.

## B-2. `/db/MVHC` — 예시를 그대로 실행하면 `Unknown Error`가 발생합니다

공식 예시는 아래와 같습니다.

```json
{ "Assign": { "1": { "VEHICLE_CLS_NAME": "VCN1",
                     "VEHICLE_LD_NAMES": ["DB-18"] } } }
```

`VEHICLE_LD_NAMES`는 "Selected Vehicle List"로, `/db/MVHL`에 정의된 차량의
`VEHICLE_LOAD_NAME`을 넣어야 합니다. `"DB-18"`은 표준 차량의 **종류명**이어서, 같은 이름의
차량을 먼저 정의해 두지 않으면 `Unknown Error`로 거부됩니다.

선행 조건(`/db/MVHL` 정의가 먼저 필요하다는 점)을 한 줄 덧붙여 주시거나, 예시를
사용자가 지정한 이름으로 바꿔 주시면 좋겠습니다. 참고로 실패 시 메시지가
`Unknown Error`뿐이라 원인 파악이 어렵습니다(A-6과 같은 사안입니다).

## B-3. `/db/STLD` — `"Assign"` 키가 ID로 쓰이지 않는다는 설명이 없습니다

대부분의 `/db/*` 엔드포인트는 `"Assign"`의 키가 곧 레코드 ID입니다(`/db/NODE`에 키
`9001`로 쓰면 절점 9001이 생성됩니다). 그런데 `/db/STLD`와 `/db/TDME`는 키를 무시하고
**다음 빈 번호로 재부여**합니다.

```python
call("POST", "/db/STLD", {"Assign": {"7": {"NAME": "LC7", "TYPE": "D"}}})
call("GET",  "/db/STLD")
# -> 생성된 ID는 3 (7이 아님)
```

Specifications 표는 `"NO"`를 `Read Only`로만 표기하고 있고, `"Assign"` 키가 어떻게
처리되는지는 나와 있지 않습니다. 키를 존중하는 테이블과 재부여하는 테이블이 섞여 있으므로,
재부여하는 엔드포인트에는 그 사실을 명시해 주시면 좋겠습니다.

---

# 부록

- 전 항목을 v2.2 단일 세션에서 심각도 역순으로 일괄 재검증했습니다(문서 → 응답 규약 →
  무언 실패 → 테이블 삭제 → 크래시). A-1·A-2는 v2.1에서도 확인했습니다.
- 모든 항목은 응답 확인에 그치지 않고 **다시 조회해 저장 결과를 비교**했습니다. A-3의
  3건은 이 비교 없이는 발견되지 않습니다.
- 검증 중 제기했다가 **재현되지 않아 제외한 항목 2건**입니다. 확인차 적어 둡니다.
  - `/db/MVHL`에 `VEH_DEFAULT: {}` 전송 — v2.1에서는 저장되지 않고 `{"message": ""}`가
    반환되었으나, v2.2에서는 정상 저장되며 기본값이 채워져 반환됩니다. 조치된 것으로
    보입니다.
  - `/db/PSLT`의 `ELEM_TYPE` 표기 — 본문(`"Plate/Plane Stress (Face)"`)과
    예시(`"Plate/PlaneStress(Face)"`) 표기가 다르지만 **두 표기 모두 허용**되어 제품
    문제가 아닙니다. 매뉴얼 내 표기만 통일해 주시면 됩니다.

- 문서 관련 항목은 발송 전 **2026-07-27자 공식 아티클 원문과 다시 대조**했고, 그 결과
  당초 작성했던 7건 중 **4건을 저희 쪽 오류로 판단해 철회**했습니다. 공식 문서는 정확했고,
  저희가 참조하던 사내 정리본의 전사 오류였습니다. 기록 차원에서 남깁니다.

  | 철회 항목 | 저희가 주장하려던 내용 | 공식 아티클 실제 기재 |
  | --- | --- | --- |
  | `/db/TDMT` `CODE` | "CEB-FIP 표기를 전부 거부한다" | `CEB_FIP_2010`·`CEB`·`KDS_2016`·`EUROPEAN` 등 **28개 값이 정확히 명시**되어 있음. 저희가 시험한 값은 같은 예시의 `NAME`(표시용 이름)이었습니다 |
  | `/db/TDME` `CODENAME` | "`KDS2016`이 거부된다" | 공식 표기는 `KDS-2016`. `KDS2016`은 공식 문서에 없는 표기였습니다 |
  | `/db/SECF` 키 | "예시 키가 element로 읽힌다" | 공식 아티클은 키의 의미를 언급하지 않으며, element라고 쓴 적이 없습니다 |
  | `/db/PRES` `FORCES` | "예시가 4개인데 5개로 반환된다" | 공식 표기가 `Array [Number, 5]`이고 예시도 모두 5개입니다. `PSLT_KEY`도 공식 스키마에 있습니다 |

  참고로 `/db/TDMT`는 `UNDERSCORED_UPPERCASE`(`CEB_FIP_2010`), `/db/TDME`는 표시용
  문자열(`CEB-FIP(2010)`)을 쓰는 것으로 **두 엔드포인트의 표기 규칙이 다릅니다.** 양쪽 다
  문서에는 정확히 적혀 있으나, 같은 코드를 다르게 표기해야 하는 점은 혼동하기 쉬웠습니다.

추가 정보나 재현 로그가 필요하시면 말씀해 주세요.
