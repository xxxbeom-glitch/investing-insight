# 00. Project Decisions

이 문서는 대화 과정에서 확정된 결정을 Cursor가 다시 추론하거나 임의 변경하지 않도록 고정한다.

## Product

- Name: `investing-insight`
- Form factor: PC Web only
- Primary user: 개인 투자자 1인 사용 우선
- Core identity: AI stock research + decision audit system
- NOT an execution/trading bot

## Market Universe

### Included
- NYSE 일반 사업회사 보통주
- NASDAQ 일반 사업회사 보통주
- ADR

### Excluded
- ETF / ETN
- REIT
- SPAC
- Preferred Stock
- BDC / CEF
- Warrant / Rights
- Fund / Investment Company type securities
- 기타 일반 사업회사 주식이 아닌 상품

### Tags, not filters
- S&P 500 constituent 여부
- NASDAQ-100 constituent 여부
- ADR 여부
- Exchange
- Sector / Industry
- Market-cap bucket

상장폐지·티커변경·분류변경 종목도 과거 Universe 역사에서 삭제하지 않는다.

## Hosting / Operation Decision

### MVP
- Web/API: 개발 PC에서 로컬 실행
- Main DB: Supabase PostgreSQL
- 데이터 ingest/research: 수동 실행 가능
- Firebase: 사용하지 않음
- Production scheduler/deployment: 사용하지 않음

### MVP 이후
MVP ALL PASS + 외부 검증 + Production Readiness Gate 이후에만:
- 웹 배포
- scheduled daily ingest
- scheduled biweekly research
- 백업/복구 자동화
- 운영 모니터링

## Data Provider Decision

### MVP
- Market: Massive adapter
- Official company facts/filings: SEC EDGAR / data.sec.gov
- LLM: OpenAI Responses API
- Database: Supabase PostgreSQL

### Post-MVP
- Macro: FRED

### Not Needed Now
- ECOS
- KIS
- Firebase
- Trading/broker execution API

외부 provider endpoint/plan은 구현 시 공식 문서를 재확인한다.

## Secret / API Key Policy

- 실제 secret은 `.env.local` 또는 실행환경 secret store에만 저장한다.
- `.env.example`에는 변수명만 둔다.
- secret을 Git, audit log, screenshot, report, error payload에 남기지 않는다.
- Supabase는 publishable/secret key 체계를 사용한다.
- Supabase secret key는 브라우저에서 절대 사용하지 않는다.
- OpenAI/Massive key는 서버 전용이다.
- SEC는 API key 대신 선언된 User-Agent를 사용한다.
- SEC automated requests는 프로젝트 자체 limiter를 두고 10 req/s를 넘지 않도록 한다.

권장 env names:

```text
SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY
SUPABASE_SECRET_KEY
MASSIVE_API_KEY
OPENAI_API_KEY
SEC_USER_AGENT
FRED_API_KEY  # Post-MVP optional
```

`SEC_USER_AGENT` 예:
`investing-insight/0.1 contact@example.com`

## Research Philosophy

- 최종 구조는 Top-down(시장→산업→밸류체인→기업)과 Bottom-up(전체기업→정량이상신호→기업→산업검증)을 병렬 사용한다.
- MVP에서는 Bottom-up vertical slice를 먼저 완성하고 full Top-down engine은 Post-MVP로 둔다.
- 산업 관련성만으로 직접 수혜주로 분류하지 않는다.
- 좋은 기업과 좋은 주가는 다를 수 있으므로 valuation을 별도 평가한다.

## Data Philosophy

- FACT와 AI ASSESSMENT를 분리한다.
- 공식/원천 데이터 우선.
- raw → normalized → QA → historical → snapshot 순서.
- 계산 가능한 파생지표는 코드가 동일 공식으로 계산한다.
- Snapshot에는 cutoff 당시 시장이 알 수 있었던 정보만 포함한다.
- `period`, `published_at`, `collected_at`, `effective_at`을 가능한 한 분리한다.
- restatement는 과거 row를 overwrite하지 않는다.

## JSON / Contract Philosophy

- 기업별 영구 JSON 파일 수천 개를 만들지 않는다.
- PostgreSQL이 system of record다.
- Research Packet JSON은 분석 시 동적 생성한다.
- Input/Output/QA/Snapshot JSON Schema를 버전 관리한다.
- schema validation 실패 payload는 다음 단계로 넘기지 않는다.

## AI Philosophy

- Quant Score는 LLM이 계산하지 않는다.
- LLM은 해석·근거합성·반대논리·불확실성 정리에 사용한다.
- MVP는 같은 모델을 역할별 호출로 분리한다.
- 역할별 model/reasoning profile은 독립 설정 가능해야 한다.
- 모델/profile 변경은 실험 변수이므로 버전 기록과 QA 재실행이 필요하다.
- 모델 unavailable 시 Cursor/프로그램이 임의로 다른 모델로 fallback하지 않는다.
- AI confidence 임의 %보다 Evidence Quality, Data Completeness, Contradicting Evidence, Uncertainty를 저장한다.

## MVP LLM Baseline

- Company Research: `gpt-5.6-terra`, `reasoning.effort=medium`
- Research QA: `gpt-5.6-terra`, `reasoning.effort=high`
- Final Judgment: `gpt-5.6-terra`, `reasoning.effort=high`
- API: OpenAI Responses API
- Profile source of truth: `config/llm_profiles.*`

MVP 이후에만 Luna/Sol 분리를 실험한다.

## Research Cadence

- Data: 미국 장 마감 이후 일별 배치 중심
- Regular Research Run: 기본 격주
- Run 시작 시 cutoff + Snapshot 고정
- event-triggered reanalysis: Post-MVP

## Investment Decision Scope

V1:
- 추적 가치가 높은 기업 선별
- 선정 이유 / Thesis
- 핵심 Risk / Bear Case
- 판단 무효화 조건
- Evidence / Uncertainty

V1 제외:
- 실제 매수/매도
- 분할매수
- 손절/익절
- 포지션 비중
- 자동매매

## Development Philosophy

- MVP 먼저.
- Layer별 Loop Engineering.
- PASS는 evidence로만 인정.
- P0/P1 미해결이면 다음 Layer 금지.
- 각 Layer audit 로그 필수.
- MVP ALL PASS 후 Git tag로 봉인.
- 외부 검토 전 Post-MVP 개발 금지.
