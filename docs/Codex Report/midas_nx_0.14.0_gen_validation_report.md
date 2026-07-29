# MIDAS-NX 0.14.0 Gen NX 엔드포인트 검증 보고서

생성 시각: 2026-07-29T19:02:45+09:00

## 결론

- 공개 PyPI 최신 버전과 설치 버전은 모두 `midas-nx 0.14.0`이다.
- SDK의 295개 DB/Design 리소스 중 Gen 지원 리소스는 242개이며, GET 가능한 240개를 모두 실제 호출했다.
- OPE/VIEW의 안전한 GET 5개를 추가로 호출하여 총 **245개 읽기 전용 경로**를 검증했다.
- 최종 결과는 **238개 성공, 7개 404**, 성공률은 **97.1%**다.
- POST/PUT/DELETE, 해석, 문서 생성·닫기·저장, 화면 변경은 실행하지 않았다.

## 범위

| 구분 | 수량 | 결과 |
|---|---:|---|
| SDK 전체 DB/Design 리소스 | 295 | Gen 지원 242 |
| Gen DB/Design GET 실호출 | 240 | 성공 233, 404 7 |
| 비-DB 안전 GET 실호출 | 5 | 전부 성공 |
| GET 미지원 Gen 리소스 | 2 | 실제 쓰기 미실행, `/info`만 확인 |
| POST 또는 상태 변경 명령 경로 | 35 | 안전상 미실행 |
| 전체 읽기 전용 실호출 | 245 | 성공 238, 404 7 |

## 성능

- DB/Design GET 240개 전체: 22.713초
- 중앙값: 0.0910초
- p95: 0.1064초
- p99: 0.1860초
- 타임아웃이나 재시도는 없었다.

## 404 분석

아래 7개 경로는 실제 GET과 서버 스키마 조회(`/info`)가 모두 404였다. 빈 테이블은 정상 응답으로 돌아왔으므로, 단순 데이터 부재보다는 **SDK 0.14.0과 현재 Gen NX 서버 빌드 사이의 라우트 차이 또는 기능 게이팅** 가능성이 높다.

- `/db/CMCS`
- `/db/EWSF`
- `/db/PLCB`
- `/db/RCHK`
- `/db/SPAN`
- `/db/STRPSSM`
- `/db/WVLD`

GET 미지원 리소스 중:

- `/DESIGN/SRC/AIK-SRC2K/DSRC`: `/info`도 404
- `/db/REBC`: `/info`는 정상 응답하여 서버 스키마 존재 확인

## Civil NX 결과와 비교

| 항목 | Gen NX | Civil NX |
|---|---:|---:|
| DB/Design GET 대상 | 240 | 293 |
| 최종 DB/Design 성공 | 233 | 273 |
| DB/Design 404 | 7 | 20 |
| 비-DB 안전 GET 성공 | 5/5 | 3/5 |
| 전체 읽기 전용 성공률 | 97.1% | 92.6% |
| DB sweep 소요시간 | 22.7초 | 40.6초 |

## SDK 피드백

1. 현재 Gen NX 서버와의 읽기 전용 호환성은 매우 높으며 Civil보다 404 비율이 낮다.
2. 404 경로는 `/info`도 404이므로 서버 빌드별 capability matrix가 필요하다.
3. 라우트 미지원과 레코드 부재를 동일한 `MidasNotFoundError`로 표현하는 현재 힌트는 개선할 여지가 있다.
4. `/db/REBC`처럼 GET은 지원하지 않지만 `/info`가 존재하는 경로는 스키마 기반 fixture를 만든 뒤 별도 폐기 세션에서 POST를 검증할 수 있다.
5. 완전한 CRUD 검증은 폐기 가능한 Gen NX 문서와 엔드포인트별 최소 모델을 사용해야 한다.

## 산출물

- `midas_nx_0.14.0_gen_endpoint_results.csv`: DB/Design GET 240개 상세 결과
- `midas_nx_0.14.0_gen_validation_summary.json`: 기계 판독용 요약
