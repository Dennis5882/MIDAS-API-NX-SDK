# MIDAS-NX 0.14.0 Civil NX 엔드포인트 검증 보고서

생성 시각: 2026-07-29T18:53:31+09:00

## 결론

- 공개 PyPI 최신 버전과 설치 버전은 모두 `midas-nx 0.14.0`이다.
- SDK에서 확인한 고유 경로는 약 335개이며, 그중 현재 모델을 변경하지 않고 실제 호출 가능한 GET 경로 298개를 검증했다.
- 최종 결과는 **276개 성공, 22개 404**로, 읽기 전용 실호출 성공률은 **92.6%**다.
- DB 리소스 GET 293개는 최초 272개 성공, 20개 404, 1개 타임아웃이었다. 타임아웃(`/db/LLANop`)은 재시도에서 성공하여 최종 DB 성공은 273개다.
- 검증 중 POST/PUT/DELETE, 해석, 문서 생성·닫기·저장, 화면 변경은 실행하지 않았다.

## 범위

| 구분 | 수량 | 결과 |
|---|---:|---|
| SDK DB/Design 리소스 | 295 | GET 가능 293개, GET 미지원 2개 |
| DB/Design GET 실호출 | 293 | 최종 성공 273, 404 20 |
| 비-DB 안전 GET 실호출 | 5 | 성공 3, 404 2 |
| POST 또는 상태 변경 명령 경로 | 35 | 안전상 미실행 |
| 전체 읽기 전용 실호출 | 298 | 성공 276, 404 22 |

## 성능

- DB GET 293개 전체: 40.615초
- 중앙값: 0.0944초
- p95: 0.1185초
- p99: 0.3412초
- `/db/LLANop`은 최초 8초 타임아웃 후 20초 제한 재시도에서 성공했다.

SDK 자체의 일반적인 GET 오버헤드는 작다. 체감 지연은 대개 많은 경로를 순차 호출하거나, 특정 서버 라우트가 지연될 때 발생한다.

## 404 분석

404가 발생한 20개 DB/Design 경로는 실제 GET뿐 아니라 서버 스키마 조회(`/info`)도 모두 404였다. 빈 테이블은 다른 256개 경로처럼 정상 응답으로 처리되므로, 이 20개는 단순히 “현재 데이터가 없음”이라기보다 **SDK 0.14.0과 현재 Civil NX 서버 빌드 사이의 라우트 차이 또는 기능/설계코드 게이팅** 가능성이 높다.

### Design 경로 9개

- `/DESIGN/RC/KDS-41-20-2022/MATD`
- `/DESIGN/RC/KDS-41-20-2022/REBB`
- `/DESIGN/RC/KDS-41-20-2022/REBC`
- `/DESIGN/RC/KDS-41-20-2022/REBR`
- `/DESIGN/RC/KDS-41-20-2022/REBW`
- `/DESIGN/RC/KDS-41-20-2022/TRFT`
- `/DESIGN/RC/KDS-41-20-2022/ULCT`
- `/DESIGN/SRC/AIK-SRC2K/MATD`
- `/DESIGN/STEEL/KDS-41-30-2022/ULCT`

### DB 경로 11개

- `/db/DRLS`
- `/db/EPST`
- `/db/POSP`
- `/db/REBB`
- `/db/REBR`
- `/db/REBW`
- `/db/SDHY`
- `/db/SDIS`
- `/db/SSEIS`
- `/db/STOR`
- `/db/SWIND`

비-DB GET 중 `/ope/STORY_PARAM`, `/ope/STORY_IRR_PARAM`도 404였다.

GET을 지원하지 않는 `/DESIGN/SRC/AIK-SRC2K/DSRC`와 `/db/REBC`는 쓰기 호출 대신 `/info`만 조회했으며 둘 다 404였다.

## SDK 피드백

1. 현재 Civil NX 서버와의 기본 DB GET 호환성은 높다. 최종 293개 중 273개가 응답했다.
2. 라우트 단위 404와 “레코드 ID 없음”이 모두 `MidasNotFoundError`로 합쳐지고 동일한 힌트가 붙는다. `/info`까지 404인 경우에는 “현재 서버 빌드에서 미지원 가능”이라는 별도 진단이 더 정확하다.
3. SDK에 제품 버전/빌드별 capability matrix 또는 시작 시점의 자동 route probing 기능이 있으면 404를 사전에 걸러낼 수 있다.
4. 대량 sweep에는 제한적인 재시도 정책이 유용하다. 이번 `/db/LLANop`처럼 일시적 지연은 재시도로 복구됐다.
5. 완전한 CRUD 검증은 별도의 폐기 가능한 Civil NX 세션과 엔드포인트별 최소 유효 fixture가 필요하다. 현재 세션에서 전부 POST/PUT/DELETE하면 문서, 해석 상태, 설계 데이터와 라이선스 세션을 훼손할 수 있다.

## 산출물

- `midas_nx_0.14.0_civil_endpoint_results.csv`: DB/Design GET 293개 상세 결과
- `midas_nx_0.14.0_civil_validation_summary.json`: 기계 판독용 요약
