# investing-insight — System Design v1.5

> PC Web 기반 미국 주식 AI 리서치·검증 시스템

## 1. 프로젝트 한 줄 정의

`investing-insight`는 NYSE·NASDAQ 전체 일반 상장기업과 ADR을 대상으로 데이터를 수집·검증하고, 정량 스크리닝과 AI 리서치를 통해 추적 가치가 높은 기업을 선별한 뒤, 당시 판단 근거를 변경 불가능한 형태로 저장하여 시간이 지난 후 AI의 종목 선별 능력을 검증하는 개인 리서치 시스템이다.

## 2. V1 최상위 목표

자동매매나 매수·매도 타이밍 최적화가 아니다. V1의 목표는 아래 질문에 답할 수 있는 시스템을 만드는 것이다.

1. 넓은 미국 상장사 Universe에서 좋은 기업을 일관된 규칙으로 찾을 수 있는가?
2. 왜 그 기업을 선택했는지 당시 근거를 재현할 수 있는가?
3. 시간이 지난 뒤 그 판단이 실제로 유효했는지 검증할 수 있는가?
4. 실패했을 때 데이터 오류, 분석 오류, 산업 판단 오류, 외부 충격을 구분할 수 있는가?

## 3. 확정 범위

- 프로젝트명: `investing-insight`
- 화면: PC Web only
- 시장: 미국 only
- 거래소: NYSE + NASDAQ
- 포함: 일반 사업회사 보통주, ADR
- 제외: ETF, ETN, REIT, SPAC, 우선주, BDC, CEF, 워런트, 권리증권, 펀드·투자회사형 증권, 기타 일반 사업회사 주식이 아닌 상품
- S&P 500 / NASDAQ-100 편입 여부: Universe 조건이 아니라 기업 속성/이벤트로 저장
- 자동 주문, 매수·매도 시점, 포지션 사이징: V1 제외
- 기본 연구 주기: 격주
- 데이터 업데이트: 장 마감 이후 일별 배치 중심
- 과거 판단: 수정 금지, 새 버전만 추가

## 4. 개발 철학

### 4.1 Thin Vertical Slice First
처음부터 완성형 Multi-Agent 시스템을 만들지 않는다. 먼저 데이터 수집부터 리포트까지 한 번 실제로 관통하는 MVP를 만든다.

### 4.2 Loop Engineering
모든 Layer는 아래 루프를 반복한다.

`PLAN → IMPLEMENT → TEST → QA → FIX → RETEST → PASS → FREEZE`

### 4.3 QA Gate
다음 Layer는 이전 Layer의 Blocking QA가 모두 PASS인 경우에만 시작한다.

### 4.4 Auditability
Cursor의 설명이 아니라 테스트 결과와 로그가 증거다. 모든 Layer는 감사 가능한 산출물을 남긴다.

### 4.5 Deterministic Before LLM
숫자 계산, 날짜 검증, 중복 제거, 타입 검증, 미래정보 차단은 코드가 담당한다. LLM은 해석이 필요한 작업만 담당한다.

## 5. 문서 읽는 순서

1. `00_PROJECT_DECISIONS.md`
2. `01_ARCHITECTURE.md`
3. `02_MVP_V0_1_SPEC.md`
4. `03_DATA_MODEL_PIPELINE.md`
5. `04_QUANT_RESEARCH_SPEC.md`
6. `05_QA_LOOP_AUDIT.md`
7. `06_PC_WEB_UI.md`
8. `07_MVP_LAYER_PLAN.md`
9. `08_POST_MVP_ROADMAP.md`
10. `09_CURSOR_MASTER_PROMPT.md`

## 6. MVP 완료 정의

MVP는 단순히 화면이 뜨는 상태가 아니다. `L00~L10`의 P0/P1 Blocking QA가 전부 PASS되고, 감사 패키지가 완성되고, Git tag로 봉인된 상태를 MVP 완료로 본다.

MVP가 ALL PASS되면 Cursor는 Post-MVP 기능을 자동으로 시작하지 않는다. `MVP_HANDOFF.md`를 생성하고 외부 검증을 위해 중단한다.
