# MIDAS NX Open API — 이슈 리포트 (2026-07-26)

MIDAS NX Open API를 실제 세션에 대해 검증하는 과정에서 확인된 사항을 정리한 것입니다.
`/db/*` 43개 엔드포인트에 대해 **생성 → 조회 → 수정 → 조회 → 삭제 → 조회** 왕복을
수행했고, 그 중 42개는 정상 동작을 확인했습니다. 아래는 정상 동작하지 않은 항목들입니다.

**제품 결함(A)과 문서 오류(B)를 분리했습니다.** 담당 부서가 다를 것으로 생각되어
그렇게 나눴습니다.

## 검증 환경

| 항목 | 내용 |
| --- | --- |
| 제품 | MIDAS CIVIL NX 2026 |
| 버전 | **v2.1 (build 06/05/2026)** 및 **v2.2 (build 06/18/2026)** |
| 릴레이 | `https://moa-engineers.midasit.com:443/civil` |
| 클라이언트 | Python 3.13, `requests` |
| 검증일 | 2026-07-26 |

아래 재현 코드는 **SDK나 라이브러리 의존성이 없습니다.** `requests`만으로 동작하며,
`MAPI_KEY`에 발급받은 키를 넣고 그대로 실행하실 수 있습니다.

A-1(크래시)은 바로 실행 가능한 단일 파일로도 첨부했습니다 — `vendor_repro_nmas.py`.
`pip install requests` 후 `python vendor_repro_nmas.py <MAPI-Key>`로 실행하시면
대조군 호출의 소요시간까지 함께 출력됩니다.

```python
import requests

MAPI_KEY = "<발급받은 MAPI Key>"
BASE = "https://moa-engineers.midasit.com:443/civil"
H = {"Content-Type": "application/json", "MAPI-Key": MAPI_KEY}

def call(method, endpoint, body=None, timeout=15):
    r = requests.request(method, BASE + endpoint, headers=H, json=body, timeout=timeout)
    return r.status_code, r.json()
```

## 요약

| # | 구분 | 대상 | 내용 | 심각도 |
| --- | --- | --- | --- | --- |
| A-1 | 제품 | `/db/NMAS` | **POST 1회로 Civil NX가 종료됨.** 5회 재현, 2개 버전 | 치명적 |
| A-2 | 제품 | `DELETE /db/*` | 문서화된 형식이 지정 ID를 무시하고 **테이블 전체를 삭제** | 치명적 |
| A-3 | 제품 | 다수 | 쓰기가 무시/변조됐는데 **HTTP는 성공을 반환** (4건, 동일 유형) | 높음 |
| A-4 | 제품 | 전역 | 오류 본문이 **HTTP 200 / 201**로 반환됨 | 중간 |
| A-5 | 제품 | `/mapikey/verify` | 프로그램 종료 직후 일정 시간 `"connected"`를 반환 | 중간 |
| A-6 | 제품 | 오류 메시지 | `"Wrong Field"`가 실제로는 **값** 오류를 의미 | 중간 |
| A-7 | 설치 | 복구 파일 | `Program Files` 하위에 기록 시도 → 권한 거부로 조용히 실패 | 낮음 |
| B-1~7 | 문서 | 매뉴얼 | 문서화된 값/키가 제품 동작과 불일치 (7건) | — |

---

# A. 제품 결함

## A-1. 🛑 `POST /db/NMAS` 호출 1회로 Civil NX가 종료됩니다

가장 우선적으로 확인 부탁드리는 항목입니다.

### 재현 코드

```python
# 노드 1개만 만든 뒤 절점질량을 1회 기록합니다.
print(call("POST", "/db/NODE", {"Assign": {"9001": {"X": 50, "Y": 50, "Z": 0}}}))
# -> (200, {...})  정상

print(call("POST", "/db/NMAS", {"Assign": {"9001": {"mX": 1.0, "mY": 1.0, "mZ": 1.0}}}))
# -> requests.exceptions.ReadTimeout
#    이 시점에 Civil NX가 종료됩니다.
```

### 관측 결과

호출이 응답하지 않고, 이후 **모든** `/db/*` 호출이 타임아웃되며, 프로그램이 아래 대화상자를
띄우고 종료됩니다.

> `[Error] Failed to disconnect the work session due to an unidentified error.`
> `Since you have not logged out, other PCs may have limited access to the license.`
> `In order to properly terminate the program, try to re-execute the program, press 'New Project' and then close the program.`

이어서 `Program will be closed due to an unexpected problem.` 대화상자가 표시됩니다.

**라이선스가 반환되지 않습니다.** 위 안내대로 프로그램을 재실행하여 New Project를 누르고
정상 종료해야 회수되므로, 자동화된 스크립트에서 이 호출이 한 번 발생하면 사람이 개입해야
합니다.

### 재현 이력 — 5회 / 2개 버전

| # | 직전 수행 내용 | `/doc/NEW` 호출 | 직전 유휴 | 결과 |
| --- | --- | --- | --- | --- |
| 1 | `/db/*` 쓰기 100건 이상 성공, 직전에 `/db/SDSP` 왕복 완료 | 있음 | 없음 | 종료 |
| 2 | `/db/*` GET 3건 성공 (노드 10개 정상 반환) | 없음 | 약 32분 | 종료 |
| 3 | `/doc/NEW` 후 모델 생성, 직전에 `POST /db/CNLD` 0.1초 성공 | 있음 | 없음 (세션 20초) | 종료 |
| 4 | `POST /db/SKEW`, `POST /db/CONS`, GET 2건 — 5건 모두 직전 1.3초 내 0.08~0.17초에 성공 | **없음** | 없음 | 종료 |
| 5 | #4와 동일 프로토콜, **v2.2에서 재실행** | 없음 | 없음 | 종료 |

### 확인한 사항

- **`GET /db/NMAS`와 `GET /info/db/NMAS`는 정상 동작합니다.** 쓰기 경로에 한정된 문제로
  보입니다.
- **페이로드는 특별하지 않습니다.** 평범한 절점 하나에 단위질량 3개이며,
  `/info/db/NMAS`가 반환하는 스키마와 일치합니다.
- **v2.2 업그레이드로 해결되지 않았습니다.** v2.1(06/05)과 v2.2(06/18) 모두 동일합니다.

### 배제한 원인 2가지

내부적으로 제기된 두 가설을 각각 전용 실험으로 배제했으므로, 조사 범위를 좁히는 데
참고가 되실 것 같습니다.

**세션 유휴 타임아웃** — 재현 #2 직전에 약 32분 공백이 있었습니다. 그러나 그 공백 이후
`/db/*` GET 3건이 정상 응답했고(노드 10개 반환), 이는 릴레이가 아닌 제품이 응답하는
호출입니다. 또한 재현 #1은 공백이 전혀 없었고 직전에 쓰기가 수십 건 성공했습니다.

**모달 대화상자에 의한 세션 차단** — `/doc/NEW`는 미저장 문서에서 저장 확인 대화상자를
띄우고, 대화상자가 열려 있으면 해당 호출뿐 아니라 세션 전체가 멈춥니다. 그래서 재현 #4·#5는
**`/doc/NEW`를 아예 호출하지 않도록** 구성했고, 직전 1.3초 안에 쓰기 3건과 읽기 2건을
각각 0.2초 이내에 성공시켰습니다. 대화상자가 열려 있었다면 이 5건도 함께 멈췄어야 합니다.

---

## A-2. 🛑 `DELETE {endpoint}` + ID 지정 `"Assign"` 본문이 테이블 전체를 삭제합니다

매뉴얼에 기재된 형식 그대로 호출했을 때 발생합니다. 삭제 대상으로 지정한 ID가 무시되고
해당 테이블의 **모든 레코드**가 삭제됩니다.

```python
# 노드 1, 2, 3, 101 이 존재하는 상태에서
call("DELETE", "/db/NODE", {"Assign": {"101": None}})
# 기대: 노드 101만 삭제
# 실제: 노드 테이블이 비워지고, 해당 노드에 연결된 요소까지 함께 삭제됨
```

| 요청 | 결과 |
| --- | --- |
| `DELETE /db/NODE` + `{"Assign": {"3": null}}` | 테이블 전체 삭제 |
| `DELETE /db/NODE` + `{"Assign": {"3": {}}}` | 테이블 전체 삭제 |
| `DELETE /db/NODE` + `{"Assign": {"2": {}, "3": {}}}` | 테이블 전체 삭제 |
| **`DELETE /db/NODE/3`** | **노드 3만 삭제** (기대 동작) |

`/db/NODE`의 경우 삭제된 절점에 연결된 요소까지 함께 사라지므로, 단일 호출로 모델이
소실될 수 있습니다. `/db/NODE`, `/db/STLD`, `/db/LDGR`, `/db/MATL`에서 동일하게
확인했습니다.

v2.2 (build 06/18/2026)에서 실측한 결과입니다.

```text
before  NODE 10개, ELEM 4개
        DELETE /db/NODE  {"Assign": {"21": null}}      <- 절점 21 하나만 지정
after   NODE 0개, ELEM 0개                              <- 모델 전체 소실

before  STLD ['1', '2']
        DELETE /db/STLD  {"Assign": {"1": {}}}         <- 하중조건 1만 지정
after   STLD []                                        <- 둘 다 삭제

        DELETE /db/NODE/502                            <- per-ID 형식
        -> {"NODE": {"502": {...}}}, 501·503 은 그대로 유지
```

응답 본문이 삭제된 **모든** 레코드를 되돌려주므로, 응답을 확인하면 의도보다 많이 삭제됐음을
알 수는 있습니다. 다만 그때는 이미 삭제된 뒤입니다.

정상 동작하는 `DELETE {endpoint}/{id}` 형식은 매뉴얼에 기재되어 있지 않습니다. 문서를
per-ID 형식으로 고치는 방향이든 본문 형식이 ID를 존중하도록 고치는 방향이든, 현재 상태는
문서를 따라 구현하면 모델이 소실되는 조합입니다.

---

## A-3. ⚠️ 쓰기가 무시되거나 변조됐는데 HTTP는 성공을 반환합니다 (4건)

개별 사안이 아니라 **하나의 유형**으로 보고 있습니다. 공통적으로 요청이 거부되거나 값이
바뀌었는데 응답에는 오류가 없어, 호출 측에서 알아차릴 방법이 레코드를 다시 읽어 비교하는
것밖에 없습니다.

| 대상 | 입력 | 실제 결과 | 응답 |
| --- | --- | --- | --- |
| `/db/SECF` | element ID를 키로 사용 | **아무것도 저장되지 않음** | 200, 오류 없음 |
| `/db/MVHL` | `VEHICLE_LOAD_NUM: 2` | `VEHICLE_TYPE_NAME`·`STANDARD_CODE`가 **폐기**되고 사용자정의 차량으로 저장 | 200, 오류 없음 |
| `/db/CONS` | `CONSTRAINT` 8자 | 앞 7자로 **절단** → 요청하지 않은 구속이 생성됨 | 200. **응답은 보낸 8자를 그대로 반환** |

세 건 모두 v2.2 (build 06/18/2026)에서 확인했습니다.

### `/db/CONS` 상세 — 응답도 절단 사실을 알려주지 않습니다

`CONSTRAINT`는 7자(Dx Dy Dz Rx Ry Rz Rw)여야 합니다. 8자를 보내면 앞 7자로 절단되는데,
**POST 응답은 보낸 8자를 그대로 되돌려줍니다.** 별도로 GET 해서 비교하지 않으면 절단
사실을 알 수 없습니다.

```python
call("POST", "/db/CONS",
     {"Assign": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}})
# 응답: {"CONS": {"3": {"ITEMS": [{"ID": 1, "CONSTRAINT": "11111111"}]}}}   <- 8자

call("GET", "/db/CONS")
# 저장: {"3": {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "CONSTRAINT": "1111111"}]}}  <- 7자
```

자유단으로 의도한 자유도가 구속되어도 아무 신호가 없으므로, 잘못된 해석 결과로 이어질 수
있습니다. 참고로 **6자는 오류로 정상 거부됩니다**
(`[Error] Constraint Condition has(have) been incorrectly entered.`).
짧은 쪽은 거부하고 긴 쪽은 조용히 잘라내는 비대칭이 문제로 보입니다.

### `/db/MVHL` 상세

```python
body = {"MVLD_CODE": 6, "VEHICLE_LOAD_NAME": "KR(SRB)_DB-18",
        "VEHICLE_LOAD_NUM": 2,                      # <- 2로 지정
        "VEHICLE_TYPE_NAME": "DB-18", "STANDARD_CODE": "KS-RB",
        "VEH_DEFAULT": {"DYN_LOAD_ALLOWANCE": 0, "CENT_F": False}}
call("POST", "/db/MVHL", {"Assign": {"2": body}})   # 200, 오류 없음

call("GET", "/db/MVHL")
# 저장된 값:
# {"MVLD_CODE": 6, "VEHICLE_LOAD_NAME": "KR(SRB)_DB-18", "VEHICLE_LOAD_NUM": 2,
#  "USER_LOAD_TYPE": "Truck/Lane",                  # <- 사용자정의로 바뀜
#  "VEH_DEFAULT": {"UNIFORM_LOAD": 0, "PL": 0, "PLM": 0, "PLV": 0}}
# VEHICLE_TYPE_NAME 과 STANDARD_CODE 가 사라졌습니다.
```

`VEHICLE_LOAD_NUM: 1`로 보내면 `DB-18`, `DB-24`, `DL-24` 모두 정상 저장됩니다.
표준 차량 지정이 실패했다면 오류로 알려주시는 편이 안전할 것 같습니다.

### `/db/SECF` 상세

`/db/SECF`는 **단면 ID**를 키로 받습니다. element ID를 키로 보내면 아무것도 저장되지
않으면서 200이 반환됩니다. (문서 관련 사항은 B-3 참조)

```python
call("POST", "/db/SECF", {"Assign": {"3": {"ITEMS": [{"ID": 1, "AREA_SF": 1.2}]}}})
# 200, 오류 없음 → GET 해보면 테이블이 비어 있음
```

---

## A-4. 오류 본문이 HTTP 200 / 201로 반환됩니다

오류 응답이 4xx/5xx가 아니라 성공 상태 코드로 전달됩니다.

```text
POST /db/TDMT   -> 201  {"error": {"message": "Wrong Field"}}
POST /db/CONS   -> 201  {"error": {"message": "[Error] Constraint Condition ..."}}
PUT  /db/TMAT   -> 200  {"error": {"message": "Wrong DB Name"}}
```

또한 오류가 `error` 키 없이 `message`로만 오는 경우가 있습니다.

```text
POST /doc/ANAL  -> {"message": "MIDAS CIVIL NX Analysis failed."}
```

성공 시에도 `message`를 사용하므로(`"... command complete"`), 상태 코드와 응답 키만으로는
성공·실패를 판정할 수 없습니다.

---

## A-5. `/mapikey/verify`가 종료된 프로그램에 대해 `"connected"`를 반환합니다

A-1 크래시 직후 측정한 결과입니다.

```text
GET /mapikey/verify   -> 0.5초,  {"status": "connected"}      <- 프로그램은 이미 종료됨
GET /db/NODE          -> 15초 타임아웃
```

릴레이가 응답하는 것으로 이해됩니다. 다만 이 엔드포인트의 용도가 연결 상태 확인이라면
"제품이 응답 가능한 상태인지"를 반영하지 못하는 것은 문제로 보입니다. 자동화 스크립트가
사전 점검으로 사용하기 어렵습니다.

**시간에 따라 달라집니다.** 크래시 직후에 호출하면 두 차례 모두 `"connected"`였고,
약 30초 뒤(타임아웃 2회를 거친 뒤)에 호출한 경우에는 `"disconnected"`가 반환되었습니다.
정상 재시작 후에도 `"disconnected"`를 정확히 반환합니다. 즉 영구적으로 잘못된 값을
주는 것은 아니고, **연결 기록이 갱신되기 전까지 일정 시간 낡은 값을 반환**하는 것으로
보입니다. 그 구간이 자동화에서 문제가 됩니다.

---

## A-6. `"Wrong Field"`가 실제로는 값 오류를 의미합니다

메시지 문구 관련 요청입니다. `/db/TDMT`, `/db/TDME`에서 `CODE`/`CODENAME` 값이
인식되지 않으면 `"Wrong Field"`가 반환됩니다.

```text
CODE 값이 인식되지 않음        -> "Wrong Field"
CODE는 인식되나 부속 필드 부족 -> "[Error] Time Dependent Material(...) input data contain errors."
```

`"Field"`라는 단어 때문에 필드 **이름**을 의심하게 됩니다. 실제로 이 문제를 추적하면서
문서상의 모든 필드를 하나씩 제거해보고 `{"NAME": "C"}` 단일 키까지 시도한 뒤에야
`CODE` 값이 원인임을 발견했습니다. `"Unknown value for field 'CODE'"` 정도로
필드명을 함께 알려주시면 진단 시간이 크게 줄어듭니다.

두 메시지가 실제로는 잘 구분되어 있어 유용하다는 점도 함께 말씀드립니다. 문구만
조정되면 충분합니다.

---

## A-7. 크래시 복구 파일이 `Program Files` 하위에 기록되어 실패합니다

A-1 크래시 시 관측된 사항입니다.

```text
C:\Program Files\MIDAS\MIDAS CIVIL NX\DgnPlugIn\_restore.mcb  -> 액세스 거부 (2회)
C:\Users\<user>\Downloads\제목 없음_restore.mcb                -> 정상 저장 (1회)
```

문서 상태에 따라 경로가 달라지는 것으로 보이며, `Program Files` 하위인 경우 일반 사용자
권한으로는 기록할 수 없어 **복구가 조용히 실패합니다.** 자동 복구를 신뢰할 수 없게 되므로
`%LOCALAPPDATA%` 등 쓰기 가능한 경로를 사용하시는 것이 좋겠습니다.

---

# B. 문서 오류

제품 동작은 정상이며, 매뉴얼 기재 내용과 불일치하는 항목입니다.

| # | 대상 | 문서 기재 | 실제 동작 |
| --- | --- | --- | --- |
| B-1 | `/db/TDMT` | `CODE`: "CEB-FIP(2010/1990/1978), ACI, KDS 등" | `European`·`AASHTO`·`ACI` 허용, `Russian` 인식. **CEB-FIP 표기는 전부 거부** |
| B-2 | `/db/TDME` | `CODENAME` 예시 `"KDS2016"` | 거부됨. `CEB-FIP(2010)`·`CEB-FIP(1990)`·`Ohzagi` 허용, `ACI`는 `A`/`B` 동반 시 허용 |
| B-3 | `/db/SECF` | 예시 키 `9001` (element로 읽힘) | **단면 ID** 키 |
| B-4 | `/db/PRES` | `DIRECTION` 기본값 `"NORMAL"` | PLATE + `FACE_EDGE_TYPE:"FACE"`에서 **거부**. 필드 생략 시에도 동일 실패. `LZ`/`LX`/`GZ`/`VECTOR`는 정상 |
| B-5 | `/db/MVHC` | `VEHICLE_LD_NAMES` 예시가 차량 **종류명**(`"DB-18"`) | 차량의 `VEHICLE_LOAD_NAME`(`"KR(SRB)_DB-24"`). 종류명을 보내면 `Unknown Error`로 거부됨 |
| B-6 | `/db/STLD`, `/db/TDME` | `"Assign"` 키로 ID 지정 | 키를 무시하고 **다음 빈 번호로 재부여** (문서에 언급 없음). 키 `7`로 POST → ID `3` 생성 |
| B-7 | `/db/PRES` | `FORCES` 예시 4개 | 5개로 반환. `/info/db/PRES`의 `maxItems`도 5. 또한 `/info`에는 있는 `PSLT_KEY`가 챕터에 없음 |

`/db/PSLT`의 `ELEM_TYPE` 표기(본문 `"Plate/Plane Stress (Face)"` vs 예시
`"Plate/PlaneStress(Face)"`)도 초안에 포함했다가 제외했습니다. 검증해 보니 **두 표기가
모두 허용**되어 제품 측 문제가 아니었습니다. 다만 매뉴얼 안에서 표기가 갈리는 것은
그대로이므로, 문서만 통일해 주시면 좋겠습니다.

## B-1 상세 — `/db/TDMT`와 `/db/TDME`의 코드명 목록이 다릅니다

두 엔드포인트가 같은 챕터에 나란히 있고 각각 코드명을 받지만, **허용값 목록이
서로 다릅니다.** CEB-FIP 필드 세트(`MSIZE`/`CTYPE`)와 ACI 필드 세트(`VOL`/`CMETHOD`)로
각각 16개 후보값을 시도한 결과입니다.

| `/db/TDMT`의 `CODE` | 결과 |
| --- | --- |
| `European` | 두 필드 세트 모두 허용 |
| `AASHTO` | 두 필드 세트 모두 허용 |
| `ACI` | `VOL`/`CMETHOD`와 함께 허용 |
| `Russian` | 인식됨 (다른 부속 필드 요구) |
| `CEB-FIP`, `CEB-FIP(2010)`, `CEB-FIP(1990)`, `CEB-FIP(1978)`, `CEB FIP` | 거부 |
| `Ohzagi`, `KDS-2016`, `KDS2016`, `Korea`, `KCI-USD12`, `JTG3362-2018` | 거부 |

CEB-FIP 기반 모델은 이 엔드포인트에서 **`"European"`**이라는 이름을 사용하는 것으로
이해했습니다. 반면 `/db/TDME`는 `CEB-FIP(2010)`을 받고 `European` 계열을 받지 않습니다.
매뉴얼의 `/db/TDMT` 설명이 이 엔드포인트가 받지 않는 코드명들을 나열하고 있어, 두
엔드포인트의 허용값 목록을 각각 명시해 주시면 좋겠습니다.

저장된 레코드는 `CODE`가 대문자로 반환됩니다 (`"European"` → `"EUROPEAN"`).

---

# 부록 — 확인 방법

- 각 항목은 `/doc/NEW` 직후의 최소 모델(재료 1, 단면 1, 두께 1, 절점 10, 요소 4,
  하중조건 2)에 대해 확인했습니다.
- 모든 항목은 응답만 확인하지 않고 **다시 조회해서 저장 결과를 비교**했습니다. A-3의
  4건은 이 비교 없이는 발견되지 않습니다.
- **최종적으로 전 항목을 v2.2 (build 06/18/2026) 단일 세션에서 심각도 역순으로
  일괄 재검증했습니다** (문서 항목 → 응답 규약 → 무언 실패 → 테이블 삭제 → 크래시).
  A-1(크래시)과 A-2(DELETE)는 v2.1 (build 06/05/2026)에서도 동일하게 확인했습니다.
  A-1은 총 6회 재현되었습니다.
- **초안에서 제외한 항목 2건** — 재현되지 않는 내용을 함께 보내면 나머지 항목의
  신뢰도까지 떨어지므로 뺐습니다. 확인차 남겨 둡니다.
  - `/db/MVHL`에 `VEH_DEFAULT: {}`(빈 객체) 전송: v2.1에서는 저장되지 않으면서
    `{"message": ""}`가 반환되었으나, **v2.2에서는 정상 저장**되고 `VEH_DEFAULT`에
    기본값(`DYN_LOAD_ALLOWANCE: 0`, `CENT_F: false`)이 채워져 반환됩니다. 조치된 것으로
    보입니다.
  - `/db/PSLT`의 `ELEM_TYPE` 표기: **두 표기 모두 허용**되어 제품 문제가 아닙니다
    (B 목록 아래 주석 참조).
- 모든 항목은 응답 확인에 그치지 않고 **다시 조회하여 저장 결과를 비교**했습니다.

추가 정보나 재현 로그가 필요하시면 말씀해 주세요.
