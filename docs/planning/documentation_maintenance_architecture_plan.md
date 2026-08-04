# `midas-nx` 문서 재구성과 업데이트 유지보수 방안

> 대상: `Dennis5882/MIDAS-API` 및 `Dennis5882/MIDAS-API-NX-SDK`  
> SDK 기준 버전: `midas-nx 2.1.2`  
> 최종 검토일: 2026-08-04  
> 참고 문서: <https://midas-rnd.github.io/midasapi-python/>  
> 검토 기준: PyPI 2.1.2, GitHub `main`, 공개 MkDocs 사이트  
> 상태: v2.1.2 구현 현황을 반영한 유지보수 아키텍처 — 추가 공개·배포는 권리·보안 승인 게이트 적용

> **검토 결과 (2026-08-04)**: 리뷰 후 큰 아키텍처(coverage.json schema v2,
> observations[]/discrepancy 12상태 FSM, 버전별 AI inventory 자동생성 등)는
> 1인 유지보수 규모에 과하다고 판단해 보류. 이 문서가 지적한 것 중 실제로
> 검증된 버그 2건만 즉시 반영: (1) 3개 언어 quickstart의 죽은 README
> "Troubleshooting" 링크 → `safety.md#connectivity-troubleshooting`로 수정,
> (2) `docs/coverage.json`의 `live_verified.method` 자유문장 63건에 실제
> 들어있던 "real production cable-stayed bridge model"·`E:/MIDAS PROGRAM/temp`
> 같은 프로덕션 모델 정보·로컬 경로를 비식별화. "MAPI-Key 환경변수를 기본
> 예제로" 항목은 이전에 이미 반대로 결정한 사안(하드코딩 유지 + 보안경고)을
> 근거 없이 뒤집는 것이라 채택하지 않음. 나머지(coverage.json 확장, 생성기,
> engineering-category 등)는 아이디어로 보관.

---

## 0. v2.1.2 현재 상태와 방향 평가

### 0.1 확인된 최신 상태

2026-08-04 기준으로 다음 상태를 확인했다.

| 항목 | v2.1.2 상태 | 평가 |
|---|---|---|
| PyPI | `midas-nx 2.1.2` 게시 | 최신 배포와 GitHub 버전이 일치함 |
| Python | `>=3.12`, CI는 3.12·3.13 | 지원 범위와 CI가 정렬됨 |
| 첫 실행 예제 | `verify_connection()` + `Node.items()` | 실무 모델에도 적용 가능한 읽기 전용 시작점으로 개선됨 |
| 사용자 진입 경로 | Python 학습 / AI 코딩의 두 경로 | 목표 사용자 구분이 문서 구조에 실제 반영됨 |
| AI 코딩 지원 | `safe-start.md` + `context-pack.md` | 초보자가 AI에 전달할 안전 규칙과 요청 형식이 생김 |
| 안전 문서 | 위험 등급 0~4, timeout·dialog·crash·recovery 설명 | 일반적인 SDK 문서를 넘어 실제 제품 운용 위험을 다룸 |
| 검증 문서 | implemented / live read / live write / unverified 구분 | “구현됨”과 “실제품에서 검증됨”을 혼동하지 않음 |
| 연결 원장 | `docs/coverage.json` → `ROADMAP.md` | endpoint 현황을 수동 표로 중복 관리하지 않는 기반이 존재함 |
| 문서 사이트 | MkDocs Material + mkdocstrings + strict build | 수동 가이드와 코드 기반 Reference가 분리됨 |
| 패키지 검증 | wheel 빌드·clean venv smoke test·tag/version 확인 | 소스 트리가 아니라 실제 배포물을 검사함 |
| 배포 보안 | PyPI Trusted Publishing(OIDC) + attestations | 장기 API token 없이 배포되며 공급망 근거가 남음 |

### 0.2 종합 판단

전체 방향은 **올바르며, 이전의 “기능을 많이 감싼 SDK” 단계에서 “초보자가 안전하게 진입하고 검증 근거를 확인할 수 있는 SDK” 단계로 이동했다.** 특히 다음 세 가지는 의미 있는 구조 개선이다.

1. 첫 예제를 고위험 `doc.new_project()`에서 읽기 전용 조회로 바꿨다.
2. Python 초보자와 AI 코딩 초보자를 서로 다른 진입 경로로 분리했다.
3. mock test, 실제품 읽기 검증, 실제품 쓰기 검증을 다른 주장으로 취급한다.

다만 아직 완성된 정보 아키텍처는 아니다. 현재 문서는 “시작하기·안전·개발자 Reference”가 강하고, 구조엔지니어가 **업무 기능으로 찾아가는 Recipe 계층**은 약하다. 또한 `coverage.json`은 구현·검증 원장으로 잘 작동하지만, 공식 사이트 불일치와 개발팀 ticket의 전체 해결 수명주기를 구조화하기에는 아직 단순하다.

### 0.3 최신 문서에서 발견한 보완 항목

#### P0 — 바로 고칠 문서 품질·안전 문제

- 한국어 Quick Start의 회사 방화벽 안내가 더 이상 존재하지 않는 README의 `Troubleshooting` 섹션을 가리킨다. `safety.md#connectivity-troubleshooting`로 바꾼다.
- Python 설치 안내의 `Python 3.x.x` 표현을 `Python 3.12 또는 3.13`으로 명확히 한다. 패키지는 `>=3.12`이지만 현재 CI로 보증하는 버전은 3.12·3.13이다.
- 첫 쓰기 실습이 곧바로 위험 등급 4의 `doc.new_project()`를 호출한다. 읽기 전용 다음에는 사용자가 GUI에서 준비한 폐기 가능한 빈 모델을 대상으로 하는 위험 등급 2의 `create()` 실습을 먼저 둔다.
- 초보자 설치 명령은 전역 `pip`만 안내하기보다 `py -m pip` 또는 선택형 가상환경 절차를 제공해 Python 실행 파일과 pip 불일치를 줄인다.
- MAPI-Key를 코드에 직접 붙이는 예제는 경고만 두지 말고, 환경변수 사용 예제를 기본 경로로 올리고 직접 붙여넣기는 일회성 대안으로 내린다.
- 공개 `coverage.json`의 `method` 자유문장에는 실제 업무 모델 유형·로컬 경로·레코드 수 같은 불필요한 운영 맥락이 들어갈 수 있다. 검증 근거는 유지하되 공개 원장에는 일반화된 fixture 이름과 비식별 요약만 남긴다.

#### P1 — 다음 문서 릴리스의 핵심

- `Model setup → Geometry → Properties → Boundary → Loads → Analysis → Results` 구조의 엔지니어링 업무 색인을 만든다.
- 최소 5개의 읽기 중심 Recipe를 추가한다: 연결·모델 요약, 절점/요소 조회, 재료·단면 조회, 하중 케이스 조회, 결과 테이블 추출.
- AI 안전 시작 설명은 한국어 사용자 페이지를 추가하되, AI에 전달하는 context pack 본문은 영어 단일 원본을 유지한다.
- 사용자용 안정 URL인 `docs/ai-coding/context-pack.md`와 버전 고정 생성물인 `docs/generated/ai-context/midas-nx-2.1.2.md`를 분리한다.
- `coverage.json`에 source revision, discrepancy, 개발팀 ticket, 해결 revision을 단계적으로 추가한다.

#### P2 — 운영 성숙도

- 문서별 `tested_with`, 제품, 빌드, 마지막 검증일을 자동 표시한다.
- 새 SDK 공개 symbol이 Reference와 AI context inventory에 누락되면 CI를 실패시킨다.
- 초보자 Quick Start의 성공률, 막힌 단계, 반복 문의를 Issue template으로 수집한다.
- 단일 유지관리자 프로젝트에 맞는 최소 리뷰·릴리스 승인 규칙을 문서화한다.
- PyPI의 `Development Status :: 5 - Production/Stable`을 유지할 객관적 기준(호환성, 지원 범위, 검증 범위, 대응 정책)을 정의하고, 기준을 충족하지 못하면 분류를 재조정한다.

---

## 1. 문제 정의

현재 개발 흐름은 개발팀과 공식 사이트를 출발점으로 하고, MIDAS-API와 SDK의 두 검증 단계를 거쳐 PyPI로 배포되는 구조다.

```text
개발팀
          ↓ 공식 정의·수정
공식 MIDAS NX Open API 사이트
          ↓ 정리·정규화
Dennis5882/MIDAS-API
          │
          ├─ 오타·스키마 모순 발견 → 개발팀 소통
          │                         ↓
          │                  공식 사이트 수정
          │                         ↓
          └──────────────── MIDAS-API 재동기화
          ↓ SDK 구현
Dennis5882/MIDAS-API-NX-SDK
          ↓ 실제 Gen NX/Civil NX 프로그램 검증
    정상 작동하는가?
      ├─ 아니오: 작동 오류·크래시 → 개발팀 소통
      │                              ↓
      │                       제품/공식 사이트 수정
      │                              ↓
      └──────────────── SDK 재동기화·회귀 검증
          ↓ 검증 통과·배포 승인
PyPI에 midas-nx 업로드
```

따라서 검증 지점은 두 곳이다. `MIDAS-API`를 정리하는 과정에서는 공식 사이트의 오타와 스키마 모순을 확인하고, SDK를 구현하는 과정에서는 실제 제품의 작동 오류와 크래시를 확인한다. 두 검증 결과는 모두 개발팀에 전달하지만, 전자는 공식 문서 정정 문제이고 후자는 제품 동작 문제라는 차이가 있다.

다만 SDK에서 관찰한 결과가 곧바로 공식 사실이 되는 것은 아니다. 다음 세 상태를 분리해야 한다.

1. **Official**: 개발팀이 공식 사이트에 게시한 내용
2. **Documented**: 공식 사이트를 기준으로 MIDAS-API에 정리한 내용
3. **Observed**: 특정 제품·빌드·모델에서 SDK로 관찰한 결과
4. **Approved**: 개발팀이 검토하고 공식 사이트 또는 제품에 반영한 내용

여기에 구조엔지니어를 위한 기능별 문서를 별도로 수동 작성하면 다음과 같이 정보가 중복될 수 있다.

```text
MIDAS-API
   ↓ 수동 반영
SDK 코드
   ↓ 다시 수동 정리
구조엔지니어용 기능 문서
   ↓ 다시 요약
AI Context Pack
```

이 구조에서는 endpoint나 필드 하나가 변경돼도 여러 파일과 저장소를 각각 수정해야 한다. 시간이 지나면 다음 문제가 발생한다.

- MIDAS-API와 SDK의 endpoint 정의가 달라짐
- SDK 코드와 API Reference의 함수명이 달라짐
- Gen NX와 Civil NX 지원 범위가 실제와 달라짐
- 기능별 문서에 오래된 payload가 남음
- AI Context Pack이 존재하지 않는 함수를 안내함
- 검증되지 않은 기능이 검증된 것으로 표시됨
- 이전 버전 예제를 최신 버전에서 실행할 수 없음

따라서 이번 방안의 목표는 문서를 다시 복사해 만드는 것이 아니라, **같은 정보를 여러 사용자 관점으로 보여주는 유지보수 구조**를 만드는 것이다.

---

## 2. 핵심 결정

### 2.1 한 가지 사실은 한 곳에서만 관리한다

> One fact, one owner, multiple views.

동일한 endpoint, 함수명, 지원 제품, 위험 등급 또는 검증 상태를 여러 문서에 수동으로 반복하지 않는다.

### 2.2 구조엔지니어 기능별 문서는 새로운 원본 데이터가 아니다

기능별 문서는 다음 역할만 수행한다.

- 구조엔지니어가 익숙한 업무 용어로 기능을 찾게 함
- 관련 Recipe와 API Reference로 연결함
- 업무 순서와 위험도를 짧게 설명함

필드 스키마, 함수 signature 및 endpoint 설명 전체를 다시 복사하지 않는다.

### 2.3 자동 생성과 수동 작성을 분리한다

자동 생성 대상:

- endpoint 목록
- Python 클래스와 함수 목록
- 지원 제품
- 작업 유형
- 위험 등급
- 구현 및 검증 상태
- 구조업무 기능별 색인
- 버전별 변경 목록
- AI Context Pack의 API 목록

수동 작성 대상:

- 온보딩 설명
- Python 초보자 Quick Start
- AI 코딩 안전 가이드
- 구조설계 업무 Recipe
- 오류 해결
- 위험 작업 설명
- 완성형 모델 예제

---

## 3. 정보 소유권

모든 정보를 하나의 거대한 파일에 넣기보다 정보 종류별 원본을 명확하게 정한다.

| 정보 | 원본 | 비고 |
|---|---|---|
| 공식 API 정의 | 공식 MIDAS NX Open API 사이트 | 개발팀이 게시·수정하는 최상위 공개 원본 |
| endpoint와 HTTP method | `MIDAS-API` | 공식 사이트의 API 사실을 정규화한 정보 |
| request/response 필드 | `MIDAS-API` | 공식 사이트를 기준으로 사실정보 중심 관리 |
| Python import와 signature | SDK 소스코드 | 실제 사용 가능한 공개 Python API |
| docstring과 예외 | SDK 소스코드 | API Reference 자동 생성 원본 |
| endpoint ↔ SDK 연결 | `docs/coverage.json` | 두 저장소 사이의 유일한 매핑 원장 |
| 지원 제품 | `docs/coverage.json` | Gen/Civil 및 실제 확인 상태 포함 |
| 위험 등급 | `docs/coverage.json` | read/write/delete 등 작업 기준 |
| 실제품 검증 | `docs/coverage.json` | mock와 live verification 구분 |
| 문서 불일치 관찰 | `docs/coverage.json` | 제품·빌드·재현조건과 함께 증거 기록 |
| 개발팀 검토 상태 | `docs/coverage.json` | ticket과 결정 상태 연결 |
| 승인된 API 정정 | 공식 사이트 → `MIDAS-API` | 개발팀이 공식 사이트를 수정한 뒤 재동기화 |
| 초보자 설명 | MkDocs 수동 문서 | 기술 명세를 반복하지 않음 |
| 업무 Recipe | MkDocs 수동 문서 | Reference로 연결 |
| AI Context Pack | 안정 URL의 수동 안전 규칙 + 버전 고정 자동 생성 inventory | 사용자 링크와 버전별 근거를 함께 유지 |

전역적으로 하나의 파일만 원본으로 삼는 것이 아니라, **정보 종류마다 정확한 소유자를 한 곳만 지정**한다.

---

## 4. 권장 전체 구조

```text
개발팀
        │ 공식 정의·수정
        ▼
공식 MIDAS NX Open API 사이트
        │
        ▼
MIDAS-API
endpoint·method·schema 사실정보
        │
        ├─ 오타·모순 → 개발팀 → 공식 사이트 수정 → 재동기화
        │
        │ source revision
        ▼
coverage.json  ◀──────── SDK Python 코드·docstring
매핑·제품·위험·검증              │
        │                         │
        ├──────────┬──────────────┤
        ▼          ▼              ▼
기능별 색인    API Reference    AI Context Pack
자동 생성      자동 생성         자동 생성
        │          │              │
        └──────────┴──────────────┘
                   │
                   ▼
          수동 온보딩·Recipe·안전 문서
                   │
                   ▼
            실제 제품 검증 실행
                   │
                   ▼
        관찰 증거·불일치·문제 후보 기록
                   │
                   ▼
             개발팀 검토 요청
                   │
          ┌────────┴────────┐
          ▼                 ▼
  문서 정정 승인       제품 문제/크래시 판단
          │                 │
          ▼                 ▼
 공식 사이트 수정      제품 수정·검증 원장 기록
          │                 │
          ▼                 │
   MIDAS-API 재동기화       │
          └────────┬────────┘
                   ▼
           SDK 재동기화·회귀 검증
                   │
                   ▼
            승인 후 PyPI 업로드
```

이 구조에서는 문서 구조를 바꾸더라도 endpoint와 SDK 정보 자체는 복제되지 않는다.

---

## 5. `coverage.json`을 연결 원장으로 확장

현재 SDK 저장소에는 다음 기반이 이미 존재한다.

- `docs/coverage.json`
- `scripts/vendor_coverage.py`
- `scripts/check_manual_drift.py`
- 자동 생성되는 `ROADMAP.md`

새로운 별도 데이터베이스나 중복 YAML을 만들기보다 `coverage.json`을 확장한다.

### 5.0 v2.1.2 현재 schema와 마이그레이션 원칙

v2.1.2의 원장은 이미 다음 정보를 갖고 있다.

- `vendored_from`
- `vendored_at_commit` — 현재 MIDAS-API source commit 고정
- endpoint, name, chapter file, products, implementation status, SDK module
- `live_verified.date`, `products`, `method`, `nx_versions`, `level`

이 구조는 현재 `ROADMAP.md` 생성과 read/write 검증 집계에 사용 중이므로 한 번에 교체하지 않는다. 다음 순서로 호환 마이그레이션한다.

1. 최상위에 `schema_version`을 추가한다.
2. 기존 필드는 그대로 읽으면서 새 `id`, `sdk.symbol`, `risk`를 선택 필드로 추가한다.
3. 단일 `live_verified`를 새 `observations[]`로 변환하는 migration/validation script를 먼저 만든다.
4. 모든 endpoint가 새 필드로 전환된 뒤 generator가 구·신 schema를 동시에 읽는 기간을 둔다.
5. `ROADMAP.md`, Reference, engineering index가 같은 원장을 사용함을 CI로 확인한 후 구 필드를 제거한다.

`method` 같은 자유문장은 공개 원장의 검색성과 비식별성을 약화하므로 다음처럼 구조화한다.

```json
{
  "fixture": "sanitized-disposable-model",
  "procedure": "live CRUD round trip",
  "result": "passed",
  "evidence_ref": "private-or-sanitized-reference"
}
```

고객명, 실제 업무 모델의 고유 유형, 로컬 사용자 경로, 내부 ticket의 비공개 설명은 공개 `coverage.json`에 넣지 않는다.

### 5.1 권장 항목

```json
{
  "id": "db-node",
  "source": {
    "repository": "Dennis5882/MIDAS-API",
    "revision": "exact-commit-sha",
    "document": "docs/manual/...",
    "section": "Node"
  },
  "endpoint": "/db/NODE",
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "engineering_category": "model.geometry.nodes",
  "products": {
    "gen": "supported",
    "civil": "supported"
  },
  "sdk": {
    "symbol": "midas_nx.db.node_element.Node",
    "import_path": "midas_nx.db.node_element",
    "implemented": true
  },
  "operation": {
    "read": true,
    "create": true,
    "update": true,
    "delete": true
  },
  "risk": {
    "read": 1,
    "create": 2,
    "update": 3,
    "delete": 4
  },
  "verification": {
    "read": "live-verified",
    "create": "live-verified",
    "update": "live-verified",
    "delete": "unverified"
  },
  "observations": [
    {
      "id": "obs-db-node-001",
      "product": "gen",
      "product_build": "exact-build-number",
      "tested_at": "2026-08-04T00:00:00+09:00",
      "operation": "read",
      "result": "matches-documentation",
      "evidence": "sanitized-test-record",
      "discrepancy_id": null
    }
  ],
  "discrepancy": {
    "status": "none",
    "ticket": null,
    "decision": null,
    "resolved_in_source_revision": null
  },
  "recipes": [
    "read-nodes",
    "create-nodes"
  ]
}
```

### 5.2 안정적인 ID 사용

문서 제목이나 Python 클래스명이 변경돼도 연결이 깨지지 않도록 `id`는 안정적인 내부 식별자로 사용한다.

예:

```text
db-node
db-elem
db-matl
ope-project-status
post-result-table
```

페이지 URL과 화면 표시 이름은 이 ID에서 생성하되 ID 자체는 가능한 한 변경하지 않는다.

### 5.3 원본 revision 기록

SDK가 어느 시점의 MIDAS-API를 반영했는지 정확한 commit SHA를 기록한다.

```json
{
  "manual_repository": "Dennis5882/MIDAS-API",
  "manual_source_revision": "exact-commit-sha",
  "synced_at": "2026-08-04T00:00:00+09:00"
}
```

`latest`, `main` 또는 날짜만 기록하지 않는다. 재현 가능한 정확한 revision을 사용한다.

### 5.4 관찰 기록과 canonical 정보 분리

실제품 검증에서 MIDAS-API와 다른 결과가 나와도 endpoint나 schema 정보를 즉시 수정하지 않는다. 먼저 `observations`와 `discrepancy`에 기록하고 개발팀 검토를 요청한다.

권장 상태:

```text
none
observed
reproduced
pending-dev-review
documentation-fix-approved
official-site-updated
midas-api-resynced
product-fix-approved
product-fix-released
expected-product-difference
environment-specific
unable-to-reproduce
resolved
```

개발팀이 문서 정정을 승인하고 공식 사이트가 수정된 후, 그 내용을 MIDAS-API에 재동기화해 canonical 정보를 갱신한다. 제품 버그로 판정된 경우 공식 정의는 유지하고 알려진 문제와 해당 제품 빌드를 기록한 뒤 제품 수정 후 다시 검증한다.

---

## 6. 구조엔지니어 기능별 정보구조

공식 MIDAS Python 문서는 Model, Node, Element, Material, Section, Boundary, Load, Analysis, Results 및 실제 구조물 Examples처럼 구조엔지니어가 익숙한 개념으로 구성되어 있다.

이 장점은 참고하되 문장, 코드, 표를 복사하지 않고 `midas-nx`용 탐색 체계를 독립 작성한다.

### 6.1 권장 3단 정보구조

```text
1단계: 시작 방법
├─ Python을 배우면서 시작
└─ AI와 함께 시작

2단계: 구조설계 업무
├─ 모델 기본 설정
├─ 절점과 요소
├─ 재료와 단면
├─ 그룹과 경계조건
├─ 정적하중
├─ 동적·지진하중
├─ 온도·이동하중
├─ 시공단계
├─ 해석
└─ 결과 조회

3단계: 개발자 Reference
├─ Client
├─ DB Resources
├─ Operation Functions
├─ Post/Result Functions
├─ View Functions
└─ Exceptions
```

### 6.2 기능별 페이지는 색인으로 제한

예:

```markdown
# 절점과 요소

구조모델의 형상과 연결관계를 구성하는 기능입니다.

## 조회

- [절점 조회](../reference/db-node.md) — Level 1
- [요소 조회](../reference/db-elem.md) — Level 1

## 생성

- [절점 생성 Recipe](../recipes/create-nodes.md) — Level 2
- [보 요소 생성 Recipe](../recipes/create-beams.md) — Level 2

## 수정 및 삭제

- [절점 수정](../reference/db-node.md#update) — Level 3
- [절점 삭제](../safety/destructive-operations.md) — Level 4
```

이 페이지에 `/db/NODE`의 전체 필드 정의나 Python signature를 다시 작성하지 않는다.

### 6.3 한 페이지를 여러 경로에서 연결

동일한 Reference 페이지를 다음 위치에서 모두 링크할 수 있다.

- 구조업무 기능별 색인
- Python 초보자 Recipe
- AI Context Pack
- 전체 API Reference
- 검색 결과

콘텐츠는 한 번만 존재하고 탐색 경로만 여러 개 제공한다.

---

## 7. 수동 작성 문서 규칙

### 7.1 온보딩

온보딩은 사용자 경험을 설명하므로 수동 작성한다. 다만 다음 정보는 자동 삽입한다.

- 현재 SDK 버전
- 요구 Python 버전
- 실제 import 경로
- 지원 제품
- 위험 등급
- 검증 상태

### 7.2 Recipe

Recipe에는 전체 API 스키마를 복사하지 않는다.

```markdown
# [업무 이름]

- 기준 SDK: 자동 삽입
- 지원 제품: coverage.json에서 삽입
- 위험 등급: coverage.json에서 삽입
- 검증 상태: coverage.json에서 삽입

## 업무 목적
## 실행 전 조건
## 실행 가능한 전체 코드
## 예상 결과
## 결과 확인
## 오류 및 복구
## 관련 Reference
```

### 7.3 AI Context Pack

다음은 자동 생성한다.

- 설치 버전
- 공개 Python symbol 목록
- 지원 제품
- 작업 유형
- 위험 등급
- 검증 상태
- 금지 또는 주의 함수

다음은 수동 작성한다.

- API 키 보안 규칙
- 읽기 전용 우선 원칙
- timeout 후 재시도 금지
- preview 요구사항
- 테스트 순서

AI Context Pack은 두 층으로 관리한다.

1. `docs/ai-coding/context-pack.md`: 초보자와 외부 링크가 사용하는 안정 URL. 사람에게 필요한 안전 원칙과 사용 절차를 수동 관리한다.
2. `docs/generated/ai-context/midas-nx-{version}.md`: 설치 버전, 공개 import, 제품 지원, 위험도, 검증 상태를 코드와 `coverage.json`에서 생성한 버전 고정 inventory다.

안정 URL의 문서가 SDK symbol 전체를 수동으로 복사해서는 안 된다. 버전에 따라 달라지는 목록은 생성물로 연결하고, 안전 규칙처럼 버전과 무관한 설명만 수동 원본에 둔다.

```text
docs/generated/ai-context/midas-nx-2.1.2.md
ai-context/midas-nx-2.2.0.md
```

---

## 8. 업데이트 절차

### 8.1 표준 흐름

```text
1. 개발팀이 관리하는 공식 사이트 기준 상태 확인
2. 공식 사이트 내용을 MIDAS-API에 정리·정규화
3. MIDAS-API 작성 중 오타·스키마 모순 검증
4. 문제가 있으면 개발팀 ticket으로 확인 요청
5. 개발팀이 공식 사이트를 수정하거나 올바른 해석을 회신
6. 수정된 공식 사이트 기준으로 MIDAS-API 재동기화
7. 확정한 MIDAS-API revision을 기준으로 SDK 구현
8. 단위·통합 테스트
9. 실제 Gen NX/Civil NX 프로그램 검증
10. 작동 오류·크래시를 재현하고 SDK 문제와 제품 문제를 구분
11. 제품 또는 API 문제 후보를 개발팀 ticket으로 전달
12. 개발팀이 제품·공식 사이트를 수정하거나 기대 동작을 회신
13. MIDAS-API와 SDK 재동기화
14. 회귀 테스트와 실제품 재검증
15. coverage.json의 검증·ticket·해결 revision 갱신
16. Reference·색인·AI Context 자동 재생성
17. 영향받은 Recipe만 수동 검토
18. 문서·링크·보안 CI 검사
19. 배포 승인 후 PyPI에 midas-nx 업로드
```

### 8.2 변경 유형별 처리

| 변경 | 자동 처리 | 사람 검토 |
|---|---|---|
| 신규 endpoint | 미매핑 항목 생성 | SDK 구현과 카테고리 지정 |
| endpoint 제거 | 삭제 후보 표시 | 하위호환·deprecation 결정 |
| 필드 추가 | schema diff | required 여부와 타입 확인 |
| 필드 제거 | 영향 symbol 및 Recipe 표시 | breaking change 결정 |
| enum 변경 | 타입·문서 영향 표시 | 실제품 확인 |
| 지원 제품 변경 | coverage 불일치 표시 | Gen/Civil 실제품 검증 |
| 함수명 변경 | 링크 영향 표시 | migration 문서 작성 |
| 검증 결과 변경 | badge 자동 갱신 | 안전 문구 검토 |

### 8.3 자동 변경 금지

공식 문서가 변경됐다고 SDK 코드를 무조건 자동 수정하거나 배포하지 않는다.

자동화는 다음까지만 수행한다.

- 변경 탐지
- 영향 범위 계산
- 초안 생성
- 테스트 실행
- 검토용 PR 준비

실제 제품 동작과 공식 문서가 다를 수 있으므로 사람의 검토와 검증 없이 merge하지 않는다.

### 8.4 두 검증 게이트

```text
검증 게이트 A — MIDAS-API 작성 단계
공식 사이트 → MIDAS-API 정리
                    ↓
             오타·모순이 있는가?
        ├─ 아니오 → SDK 구현 진행
        └─ 예 → 개발팀 확인
                  ↓
             공식 사이트 수정
                  ↓
             MIDAS-API 재동기화

검증 게이트 B — SDK 실제품 검증 단계
MIDAS-API → SDK 구현 → 실제 제품 실행
                         ↓
                정상 작동하는가?
        ├─ 예 → live verification 기록 → 배포 후보
        └─ 아니오 → 안전하게 재현·원인 분리
                         ↓
                   개발팀 ticket
                         ↓
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     제품 버그       공식 문서 오류     제품·빌드 차이
        │                │                │
     제품 수정       공식 사이트 수정   조건부 지원 기록
        │                │                │
        └────────────────┴────────────────┘
                         ↓
              MIDAS-API/SDK 재동기화
                         ↓
                    회귀 검증
                         ↓
                 승인 후 PyPI 업로드
```

### 8.5 개발팀 전달 정보

ticket에는 다음을 포함한다.

- endpoint와 HTTP method
- SDK symbol과 SDK 버전
- 제품: Gen NX 또는 Civil NX
- 정확한 제품 빌드
- MIDAS-API source revision
- 안전하게 축소한 재현 절차
- 기대 결과와 실제 결과
- 성공/실패 응답의 민감정보 제거본
- 같은 조건에서의 재현 횟수
- 모델 변경 여부와 복구 여부
- 문서 오류, 제품 버그 또는 제품별 차이 중 예상 분류

API 키, 고객명, 원본 모델 파일, 개인 경로 및 내부 서버 정보는 ticket에 포함하지 않는다.

---

## 9. 두 저장소 동기화

### 9.1 권장 방식

두 저장소를 유지한다면 SDK가 특정 MIDAS-API revision을 명시적으로 고정한다.

권장 파일:

```text
docs/source-revision.json
```

```json
{
  "repository": "https://github.com/Dennis5882/MIDAS-API",
  "revision": "exact-commit-sha",
  "synced_at": "2026-08-04T00:00:00+09:00"
}
```

### 9.2 Git submodule 비권장

소규모 또는 1인 유지보수 프로젝트에서는 Git submodule이 다음 문제를 만들 수 있다.

- clone 이후 추가 초기화 필요
- 사용자와 기여자가 현재 revision을 이해하기 어려움
- CI와 로컬 환경이 서로 다른 revision을 사용할 수 있음

대신 commit SHA와 생성된 정규화 자료를 명시적으로 고정하는 방식을 우선 검토한다.

### 9.3 장기적으로 저장소 단순화 검토

유지보수자가 적다면 장기적으로 다음 중 하나를 선택한다.

#### 선택 A — 두 저장소 유지

- MIDAS-API: API 사실정보
- SDK: Python 코드, mapping, 문서
- revision 고정과 drift CI 필수

#### 선택 B — SDK 저장소로 정규화 정보 통합

- SDK 저장소 안에 `spec/` 또는 `catalog/` 배치
- MIDAS-API는 참고·보관 저장소로 전환
- 하나의 PR에서 코드와 문서 동시 변경 가능

현재 상태에서는 먼저 선택 A를 자동화하고, 실제 유지보수 비용을 측정한 뒤 선택 B를 검토한다.

---

## 10. CI와 자동 검증

### 10.0 v2.1.2에서 이미 동작하는 게이트

v2.1.2에는 다음 자동화가 이미 구현되어 있다. 새 자동화는 이를 대체하지 않고 확장한다.

- Python 3.12·3.13에서 pytest와 ruff 실행
- mypy 실행
- wheel/sdist 빌드와 `twine check`
- clean virtual environment에 wheel을 설치한 smoke test
- MkDocs `--strict` 빌드와 GitHub Pages 배포
- GitHub Release tag와 `midas_nx.__version__` 일치 확인
- PyPI Trusted Publishing과 artifact attestations

남은 핵심은 일반 Python 패키지 CI가 아니라 **두 저장소 drift, 생성 문서 최신성, 예제 위험도 및 공개 검증정보 비식별화**를 검사하는 것이다.

### 10.1 Drift 검사

기존 `scripts/check_manual_drift.py`를 확장해 다음을 검사한다.

- MIDAS-API에 새 endpoint가 존재하는가?
- 기존 endpoint의 method가 변경됐는가?
- SDK에 매핑되지 않은 항목이 있는가?
- MIDAS-API에서 사라진 endpoint가 SDK에 남아 있는가?
- source revision이 현재 동기화 상태와 일치하는가?
- 해결된 discrepancy가 새 MIDAS-API revision에 실제 반영됐는가?
- pending ticket을 승인된 사실처럼 문서에 표시하지 않았는가?

### 10.2 코드와 문서 검사

- 공개 Python symbol이 실제 import되는지 확인
- Reference에 존재하지 않는 symbol이 없는지 확인
- Recipe의 import와 함수명이 현재 버전에서 유효한지 확인
- 기능별 색인에 연결되지 않은 endpoint 탐지
- 깨진 내부 링크와 anchor 검사
- 오래된 SDK 버전 문자열 탐지
- `mkdocs build --strict`

### 10.3 안전 검사

- MAPI-Key 패턴 탐지
- 이메일, 고객명, 내부 경로 및 모델 경로 탐지
- `delete_all`, 전체 DELETE, `/doc/NEW`, `/doc/OPEN` 탐지
- 파일 덮어쓰기와 자동 재시도 예제 탐지
- 위험 작업에 Level 3 또는 Level 4 표시가 있는지 확인

### 10.4 생성 결과 변경 검사

생성 스크립트를 실행한 뒤 Git diff가 남으면 CI를 실패시킨다.

```text
source data 변경
    ↓
generator 실행
    ↓
생성 파일 변경 여부 확인
    ↓
미반영 변경이 있으면 CI 실패
```

이를 통해 원본 정보는 바뀌었지만 문서를 재생성하지 않은 상태를 방지한다.

---

## 11. 버전 관리와 릴리스

### 11.1 버전별 생성물

각 SDK 릴리스에서 다음 산출물을 고정한다.

- source revision
- coverage ledger
- API Reference
- 기능별 색인
- AI Context Pack
- verification summary
- observation 및 discrepancy summary
- 개발팀 ticket과 해결 source revision 연결
- release notes

### 11.2 문서의 버전 표시

모든 실행 예제 상단에 기준 버전을 표시한다.

```text
Tested with: midas-nx 2.1.2
Python: 3.12+
Product: Gen NX / Civil NX
Verification: live-read / live-write / unverified
```

### 11.3 변경 영향 보고서

릴리스 시 다음 보고서를 자동 생성한다.

```markdown
# Documentation Impact

- Added endpoints:
- Removed endpoints:
- Changed schemas:
- Changed Python symbols:
- Changed product support:
- Recipes requiring review:
- AI Context Pack regenerated: yes/no
- Live verification required:
```

### 11.4 문서 변경과 버전 증가 기준

v2.1.2는 `src/midas_nx/` 동작 변경 없이 README와 온보딩을 갱신한 packaged-metadata release다. `pyproject.toml`의 `readme = "README.md"` 때문에 README는 PyPI에 배포되는 패키지 메타데이터이므로 patch release가 타당하다.

앞으로는 다음 기준을 적용한다.

| 변경 | SDK 버전 증가 | 배포 경로 |
|---|---:|---|
| `docs/`만 변경, PyPI 설명·wheel 내용 불변 | 원칙적으로 불필요 | GitHub Pages만 배포 |
| README/PyPI 설명, package metadata 변경 | patch | PyPI 재배포 |
| 호환되는 기능·endpoint 추가 | minor | PyPI 재배포 |
| 버그 수정, payload 교정 | patch가 기본 | 영향과 호환성 검토 후 PyPI |
| 공개 API 제거·호환성 파괴 | major | migration guide 포함 |
| 즉시 막아야 하는 파괴적 안전 결함 | 예외적으로 즉시 수정 | release notes 최상단에 명시 |

문서 사이트와 패키지 릴리스를 불필요하게 결합하지 않되, 사용자가 `pip install` 후 PyPI에서 보는 설명과 실제 문서가 다른 상태는 허용하지 않는다.

---

## 12. 권리와 출처 관리

현재 저장소의 권리 관계가 검토 중이므로 다음 원칙을 적용한다.

- 공식 문서의 문장, 표, 코드 및 이미지를 그대로 복사하지 않는다.
- endpoint와 필드 같은 사실정보를 정규화하되 출처 revision을 기록한다.
- 구조엔지니어 설명과 예제는 독립적으로 작성한다.
- 회사 소스코드, 비공개 문서 및 내부 도구를 generator 입력으로 사용하지 않는다.
- 고객 모델 데이터와 식별 가능한 검증 정보를 공개 문서에 포함하지 않는다.
- 자동 생성은 권리 문제를 해결하지 않으므로 공개 전 사람의 승인을 받는다.
- 문제가 발견돼도 기록을 임의로 삭제하거나 출처 흔적을 숨기지 않고 담당자에게 보고한다.

---

## 13. 도입 단계

### v2.1.2 체크포인트

| Phase | 상태 | v2.1.2 기준 남은 일 |
|---|---|---|
| 0 승인 게이트 | 미완료 | 회사 차원의 권리·상표·공개 검증 범위 승인 |
| 1 정보 지도 | 부분 완료 | source SHA와 module mapping은 존재, 정보 소유권·ticket 위치 확정 필요 |
| 2 Coverage 확장 | 부분 완료 | product·live level은 존재, stable ID·risk·observations·discrepancy 필요 |
| 3 생성기 | 부분 완료 | ROADMAP과 API Reference는 존재, 업무 색인·AI inventory·impact report 필요 |
| 4 수동 문서 | 부분 완료 | 두 진입 경로·안전 문서는 완료, Recipe 계층과 지역화 보강 필요 |
| 5 CI·사용자 검증 | 부분 완료 | 패키지·문서 CI는 강함, cross-repo drift·secret/context lint·사용자 테스트 필요 |

### Phase 0 — 승인 게이트

- 두 저장소의 코드·문서 출처 조사
- MIDAS-API 사용 및 재배포 권한 확인
- 업무상저작물과 개인 저작권 확인
- MIDAS 상표 및 제품명 사용 확인
- 공개 가능한 실제품 검증 범위 확인

승인 전 금지:

- GitHub push
- 신규 Release
- PyPI 업로드
- 외부 문서 공개
- LinkedIn 홍보

### Phase 1 — 원본 정보 지도 작성

- 각 정보의 현재 위치 파악
- 중복된 endpoint·schema·함수 설명 식별
- `coverage.json`과 SDK symbol 연결 확인
- MIDAS-API source revision 기록
- 기존 실제품 검증 결과와 개발팀 feedback 흐름 조사
- observation, discrepancy 및 ticket의 현재 저장 위치 파악
- 수동 문서와 자동 생성 후보 구분

산출물:

- 정보 소유권 표
- 중복 콘텐츠 목록
- 현재 dependency graph
- migration 대상 목록

### Phase 2 — Coverage schema 확장

- 안정적인 endpoint ID 도입
- engineering category 추가
- SDK symbol 연결
- 제품별 지원 상태 추가
- 작업별 위험 등급 추가
- method별 검증 상태 추가
- source revision 추가
- 제품 build와 검증 날짜를 포함하는 observation 추가
- 개발팀 ticket과 결정 상태를 포함하는 discrepancy 추가

### Phase 3 — 생성기 구현

- API Reference 색인 생성
- 구조업무 기능별 색인 생성
- 지원 제품 표 생성
- 위험 및 검증 badge 생성
- AI Context Pack API 목록 생성
- Documentation Impact 보고서 생성

### Phase 4 — 수동 문서 정리

- 중복 스키마 제거
- 수동 문서에서 자동 Reference로 연결
- Python 초보자와 AI 코딩 초보자 경로 유지
- 업무 Recipe를 표준 형식으로 변경
- Excel/VBA는 핵심 온보딩에서 제외

### Phase 5 — CI와 사용자 검증

- drift 검사
- 생성 결과 검사
- import 및 smoke test
- MkDocs strict build
- 보안정보 검사
- 구조엔지니어 사용자 테스트

---

## 14. 우선순위

### P0

- 법무·IP 승인 게이트
- 한국어 Quick Start의 깨진 Troubleshooting 링크 수정
- Python 3.12·3.13 설치·실행 안내 명확화
- MAPI-Key 환경변수 사용을 기본 예제로 승격
- 읽기 전용 다음의 첫 쓰기 실습을 위험 등급 2로 재설계
- 공개 `coverage.json` 자유문장의 비식별화 audit
- `schema_version`과 호환 migration 방안 확정
- 실제품 관찰과 개발팀 승인 정보를 분리하는 상태 모델 확정

### P1

- engineering category 추가
- SDK symbol 자동 추출
- 기능별 색인 자동 생성
- Reference 자동 생성
- 위험·검증 badge 자동 생성
- 문서 변경 영향 보고서
- 한국어 AI 안전 시작 페이지
- 읽기 중심 구조업무 Recipe 최소 5개
- MIDAS-API drift 검사 유지·확장

### P2

- 버전 고정 AI API inventory 자동 생성
- Recipe 영향 분석
- scheduled upstream drift 검사
- 버전별 문서 보관
- 저장소 통합 여부 재평가
- PyPI maturity classifier와 지원정책 정기 재검토

---

## 15. 완료 기준

다음 조건을 모두 만족하면 유지보수 구조가 완성된 것으로 본다.

- endpoint 정보는 MIDAS-API에서 한 번만 관리된다.
- Python signature는 SDK 코드에서 한 번만 관리된다.
- endpoint와 SDK 연결은 `coverage.json` 한 곳에서 관리된다.
- 기능별 문서는 동일 스키마를 복사하지 않고 Reference로 연결한다.
- MIDAS-API source revision을 정확한 commit SHA로 재현할 수 있다.
- upstream 변경 시 영향받는 SDK symbol과 Recipe를 자동으로 확인할 수 있다.
- SDK 검증에서 발견된 불일치가 observation으로 기록되고 개발팀 ticket과 연결된다.
- 개발팀 승인 및 공식 사이트 반영 전 관찰 결과가 canonical 사실로 자동 승격되지 않는다.
- 승인된 정정은 MIDAS-API revision, SDK 수정 및 회귀 검증까지 추적된다.
- 기능별 색인, Reference 및 AI API 목록이 자동 생성된다.
- 자동 생성 결과를 갱신하지 않으면 CI가 실패한다.
- Recipe에는 버전, 제품, 위험 및 검증 상태가 표시된다.
- 문서와 예제에 API 키나 고객정보가 없다.
- 공개 전에 법무·지식재산권 승인을 받는다.

---

## 16. AI 구현 요청문

```markdown
# Task: Evolve the v2.1.2 midas-nx documentation architecture

Repositories:
- Dennis5882/MIDAS-API
- Dennis5882/MIDAS-API-NX-SDK

Target SDK version: midas-nx 2.1.2

Working directory:
- Run from the MIDAS-API-NX-SDK repository root.
- Treat the sibling ../MIDAS-API repository as read-only unless a separate, explicitly approved task authorizes a change there.

Existing v2.1.2 foundations — preserve and extend them:
- MkDocs Material site and mkdocstrings reference;
- read-only first examples in README, docs/index.md, and three quickstarts;
- two onboarding paths: learning Python and AI-assisted coding;
- docs/ai-coding/safe-start.md and docs/ai-coding/context-pack.md;
- risk levels 0-4 in docs/safety.md;
- implemented/live-read/live-write/unverified verification semantics;
- docs/coverage.json, scripts/vendor_coverage.py, scripts/check_manual_drift.py, and generated ROADMAP.md;
- CI for Python 3.12/3.13, typing, wheel smoke tests, strict docs build, tag/version matching, Trusted Publishing, and attestations.

Do not rebuild these foundations from scratch or replace working automation with a parallel system.

Goal:
Reorganize documentation for structural engineers without duplicating API facts, Python signatures, product support, verification status, or safety metadata across multiple documents.

Core principles:

1. One fact must have one owner.
2. MIDAS-API owns normalized endpoint, method, and schema facts.
3. SDK source code and docstrings own Python imports, symbols, signatures, returns, and exceptions.
4. docs/coverage.json is the only mapping and verification ledger between the API source, SDK code, live product observations, and development-team decisions.
5. Engineering-task pages are navigation indexes, not copied API references.
6. API reference pages must be generated from SDK code and mapping metadata.
7. AI context packs must be versioned and generated from verified public symbols.
8. Tutorials, recipes, troubleshooting, and safety explanations remain human-authored.
9. Do not create a third YAML/JSON source that duplicates coverage.json.
10. Do not automatically merge or publish changes detected from upstream documentation.
11. Treat the workflow as a gated feedback loop: development team -> official API site -> MIDAS-API normalization -> SDK implementation -> live product verification -> development-team ticket -> official site/product correction -> MIDAS-API and SDK resync -> regression verification -> approved PyPI upload.
12. Keep official-site facts, MIDAS-API normalized facts, observed product behavior, and development-team-approved corrections as separate states.
13. Keep docs/ai-coding/context-pack.md as the stable human-facing URL, but generate a version-fixed API inventory under docs/generated/ai-context/.
14. Migrate coverage.json compatibly: add schema_version and optional fields first; do not break ROADMAP generation in one large rewrite.

Required metadata:

- stable endpoint ID;
- exact MIDAS-API source commit SHA;
- endpoint and methods;
- engineering category;
- supported products;
- SDK symbol and import path;
- operation types;
- risk level by operation;
- verification status by operation;
- product build and dated live observations;
- discrepancy status and development-team ticket;
- decision and resolved MIDAS-API source revision;
- related recipes.

Required generated outputs:

- engineering-task indexes;
- Python API reference indexes;
- supported-product tables;
- risk and verification badges;
- versioned AI context pack API inventory;
- documentation impact report for each release.

Required checks:

- extend scripts/check_manual_drift.py rather than duplicating it;
- reuse or extend scripts/vendor_coverage.py;
- validate that all documented Python symbols import successfully;
- detect stale SDK versions and broken links;
- detect unmapped and removed endpoints;
- detect unresolved discrepancies presented as verified facts;
- verify that resolved documentation tickets point to a MIDAS-API commit;
- detect secrets, internal paths, customer information, destructive examples, and automatic retries;
- run mkdocs build --strict;
- fail CI when generated outputs are stale.

Immediate P0 audit:

- fix the Korean quickstart's stale README Troubleshooting link;
- make the tested Python range explicit as 3.12/3.13;
- do not make doc.new_project() the first write exercise after the read-only tutorial;
- propose a level-2 create exercise against a user-prepared disposable blank model;
- make environment-variable MAPI-Key handling the default beginner path;
- audit public coverage.json free text for customer/model/path details and propose a lossless sanitized structure.

Documentation navigation:

1. Start Here: Python beginner / AI-assisted coding beginner.
2. Engineering Tasks: model setup, geometry, properties, boundary, loads, analysis, and results.
3. Practical Recipes.
4. Safety.
5. Developer API Reference.

Scope constraints:

- Do not copy text, code, tables, or images from the official MIDAS Python documentation.
- Use its engineering-oriented navigation only as an information-architecture reference.
- Keep Excel/VBA out of the core onboarding.
- Do not push, publish, release, or upload to PyPI.
- Legal and IP review is pending.
- If source provenance or confidential information is found, report it without deleting or hiding evidence.

For the first response, do not edit files. Report:

- the current sources of truth;
- duplicated information and drift risks;
- proposed coverage.json schema changes;
- the proposed observation, discrepancy, and development-team ticket lifecycle;
- generated versus human-authored content;
- migration phases and exact P0 files;
- CI changes;
- legal/IP questions requiring human approval.
```

---

## 17. 최종 결론

구조엔지니어가 기능을 쉽게 찾을 수 있도록 문서를 재구성하는 것은 필요하다. 하지만 API 내용과 SDK 사용법을 다시 수동 작성하면 장기적으로 유지하기 어렵다. 또한 실제 개발 흐름은 MIDAS-API에서 SDK로 내려오는 단방향이 아니라, SDK의 실제 제품 검증 결과가 개발팀 검토를 거쳐 MIDAS-API를 개선하는 순환 구조다.

최종 구조는 다음과 같아야 한다.

```text
두 가지 시작 경로              ← 수동 작성
구조업무 기능별 목차           ← 자동 생성 + 짧은 수동 설명
실무 Recipe                    ← 수동 작성
Python API Reference           ← SDK 코드에서 자동 생성
endpoint·제품·검증·위험 정보   ← coverage.json에서 자동 생성
관찰·불일치·개발팀 결정        ← coverage.json에서 추적
승인된 API 정정                ← 공식 사이트 반영 후 MIDAS-API 재동기화
검증된 SDK                     ← 승인 후 PyPI 업로드
```

즉, **문서 콘텐츠를 복제하지 않고 탐색 방식만 재구성하며, 실제품 관찰은 개발팀 승인과 공식 사이트 반영 전까지 canonical 사실과 분리한다.** 이 원칙을 지키면 구조엔지니어에게 친숙한 문서를 제공하면서도 공식 사이트, MIDAS-API, SDK 및 PyPI 배포가 같은 검증 흐름 안에서 관리된다.
