# investing-insight — System Design v1.6

> PC Web 기반 미국 주식 AI 리서치·검증 시스템

## 1. 프로젝트 한 줄 정의

`investing-insight`는 NYSE·NASDAQ의 일반 사업회사 보통주와 ADR을 대상으로 데이터를 수집·검증하고, 정량 스크리닝과 AI 리서치를 통해 추적 가치가 높은 기업을 선별한 뒤, 당시 판단 근거와 사용 데이터·모델·프롬프트를 변경 불가능한 형태로 저장하여 이후 AI의 종목 선별 능력을 검증하는 개인 리서치 시스템이다.

## 2. V1 최상위 목표

자동매매나 매수·매도 타이밍 최적화가 아니다. V1은 다음을 검증한다.

1. 넓은 미국 상장사 Universe에서 좋은 기업을 일관된 규칙으로 찾을 수 있는가?
2. 왜 그 기업을 선택했는지 당시 정보만으로 재현할 수 있는가?
3. AI의 사실 주장과 해석을 근거까지 추적할 수 있는가?
4. 시스템·데이터·AI 오류를 구분할 수 있는가?
5. MVP 자체가 QA 증거와 감사 로그로 외부 검증 가능한가?

## 3. 확정 범위

- 프로젝트명: `investing-insight`
- 화면: PC Web only
- 시장: 미국 only
- 거래소: NYSE + NASDAQ
- 포함: 일반 사업회사 보통주, ADR
- 제외: ETF, ETN, REIT, SPAC, 우선주, BDC, CEF, 워런트, 권리증권, 펀드·투자회사형 증권, 기타 일반 사업회사 주식이 아닌 상품
- S&P 500 / NASDAQ-100 편입 여부: Universe 조건이 아니라 태그/이벤트 데이터
- 자동 주문, 진입·청산 시점, 포지션 사이징: V1 제외
- 기본 연구 주기: 격주
- 데이터 업데이트: 장 마감 이후 일별 배치 중심
- 과거 Snapshot/Judgment: 수정 금지, 새 버전만 추가

## 4. MVP 운영 경계

MVP 단계는 **실험실**이다.

- PC에서 Web/API를 로컬 실행한다.
- DB는 처음부터 Supabase PostgreSQL을 사용한다.
- Firebase는 사용하지 않는다.
- 데이터 수집과 Research Run은 MVP에서 수동 실행 가능해야 한다.
- 자동 스케줄링, 상시 운영, 웹 배포는 MVP ALL PASS + 외부 검토 + Production Readiness Gate 이후에만 진행한다.

즉 `로컬 개발 + 클라우드 DB` 구조이며, MVP 검증 전에는 실제 상시 운영을 시작하지 않는다.

## 5. 외부 데이터/API 기준

MVP:
- Supabase PostgreSQL: 핵심 DB
- Massive: 미국 종목 registry / 가격 / 거래량 / 시장 metadata
- SEC EDGAR / data.sec.gov: 공식 재무·공시
- OpenAI Responses API: AI Research / QA / Final Judgment

Post-MVP:
- FRED: 미국 거시경제 / Top-down Industry Engine

현재 제외:
- Firebase
- ECOS
- KIS
- 자동매매 API
- 별도 뉴스 API는 MVP 필수가 아님

## 6. LLM Baseline

MVP는 모델을 여러 종류 섞지 않고 GPT-5.6 Terra를 역할별로 분리 사용한다.

| Role | Model | reasoning.effort |
|---|---|---|
| Company Research | `gpt-5.6-terra` | `medium` |
| Research QA | `gpt-5.6-terra` | `high` |
| Final Judgment | `gpt-5.6-terra` | `high` |

- OpenAI 호출은 Responses API를 기본으로 한다.
- 모델/리소닝 값은 secret이 아니므로 `.env`가 아니라 versioned config로 관리한다.
- API key만 환경변수로 관리한다.
- 모델을 바꾸면 `llm_profile_version`을 올리고 QA를 다시 통과해야 한다.
- MVP 이후 Luna는 대량 저비용 분류, Sol은 최종 독립검증 후보로 실험할 수 있다.

## 7. 기업별 JSON 정책

기업마다 `NVDA.json`, `AAPL.json` 같은 영구 파일을 미리 만들지 않는다.

- 실제 데이터는 PostgreSQL에 저장한다.
- 분석 시 DB + Snapshot에서 필요한 정보만 모아 Research Packet JSON을 동적으로 만든다.
- AI 결과 JSON은 schema validation 후 DB에 저장한다.
- JSON **파일 수천 개**가 아니라 JSON **Schema/Contract**를 버전 관리한다.

예시 계약은 `schema_examples/`에 제공한다.

## 8. 개발 철학

### Thin Vertical Slice First
처음부터 완성형 Multi-Agent를 만들지 않는다. 데이터 수집부터 Research/QA/Report까지 한 번 끝까지 관통하는 MVP를 먼저 만든다.

### Loop Engineering
각 Layer는 `PLAN → IMPLEMENT → TEST → QA → FIX → RETEST → PASS → FREEZE`를 따른다.

### QA Gate
이전 Layer의 P0/P1이 0이고 Blocking Acceptance Criteria가 모두 PASS해야 다음 Layer로 진행한다.

### Auditability
Cursor의 설명이 아니라 테스트 결과·명령·hash·commit·audit log가 증거다.

### Deterministic Before LLM
숫자 계산, 날짜, 중복, 타입, future leakage, rule score는 코드가 담당한다.

### Fail Closed
필수 provider/model/config가 없거나 QA가 실패하면 임의 fallback으로 정상처럼 진행하지 않는다.

## 9. 문서 읽는 순서

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

## 10. MVP 완료 정의

`L00~L10`의 모든 Blocking Criteria가 PASS되고 P0/P1 open issue가 0이며, representative end-to-end run이 재현되고 audit package와 `MVP_HANDOFF.md`가 완성되고 Git tag로 봉인된 상태다.

MVP ALL PASS 후 Cursor는 Post-MVP를 자동으로 시작하지 않는다.
