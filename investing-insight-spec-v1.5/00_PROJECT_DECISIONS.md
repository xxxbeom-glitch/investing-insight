# 00. Project Decisions

이 문서는 대화 과정에서 확정된 결정을 Cursor가 다시 추론하거나 임의 변경하지 않도록 고정한다.

## Product

- Name: `investing-insight`
- Form factor: PC Web only
- Primary user: 개인 투자자 1인 사용을 우선
- Core identity: AI stock research + decision audit system
- NOT an execution/trading bot

## Market Universe

### Included
- NYSE 일반 사업회사 보통주
- NASDAQ 일반 사업회사 보통주
- ADR

### Excluded
- ETF
- ETN
- REIT
- SPAC
- Preferred Stock
- BDC
- CEF
- Warrant
- Rights
- Fund / Investment Company type securities
- 기타 일반 사업회사 주식이 아닌 상품

### Tags, not filters
- S&P 500 constituent 여부
- NASDAQ-100 constituent 여부
- ADR 여부
- Exchange
- Sector / Industry
- Market-cap bucket

과거 Universe는 삭제하지 않는다. 상장폐지 또는 분류 변경이 발생해도 당시 상태를 역사 데이터로 보존한다.

## Research Philosophy

- 시장 → 산업 → 밸류체인 → 기업의 Top-down 분석을 최종 구조에 포함한다.
- 전체 기업 → 정량 이상신호 → 기업 → 산업 검증의 Bottom-up 분석도 병렬로 둔다.
- Top-down과 Bottom-up 후보를 합친 뒤 심층 분석한다.
- 산업 관련성이 있다는 이유만으로 직접 수혜주로 분류하지 않는다.
- 좋은 기업과 좋은 주가는 다를 수 있으므로 밸류에이션을 별도 평가한다.

## Data Philosophy

- FACT와 AI ASSESSMENT를 분리 저장한다.
- 공식/원천 데이터 우선.
- 데이터가 충돌하면 원천 출처와 기준시각을 보존한다.
- 계산 가능한 파생지표는 동일 공식으로 내부 계산한다.
- 분석시점에 알 수 없었던 정보는 Snapshot에 절대 포함하지 않는다.
- 데이터의 `period`, `published_at`, `collected_at`, `effective_at`을 가능한 한 분리한다.

## AI Philosophy

- 정량 점수는 LLM이 계산하지 않는다.
- LLM은 리서치, 비교, 반대논리, 불확실성 정리에 사용한다.
- 같은 LLM을 역할별 Agent로 분리할 수 있다.
- 최종 구조에서는 중요 후보에 독립 LLM 검증을 추가한다.
- MVP는 복잡한 Multi-Agent보다 1개의 주 LLM + 역할 분리 호출로 시작한다.
- 모든 핵심 주장에는 evidence reference가 있어야 한다.
- AI confidence 숫자 자체보다 Evidence Quality, Data Completeness, Contradicting Evidence, Uncertainty를 저장한다.

## Research Cadence

- 데이터: 장 마감 이후 일별 배치 중심
- 정기 Research Run: 기본 격주
- Research Run 시작 시 Snapshot 고정
- 향후 event-triggered reanalysis는 Post-MVP

## Investment Decision Scope

V1에서 다루는 것:
- 추적 가치가 높은 기업 선별
- 선정 이유
- 핵심 리스크
- 반대 논리
- 판단 무효화 조건
- 연구 기간/검증 포인트

V1에서 다루지 않는 것:
- 실제 매수 주문
- 분할매수
- 매도 타이밍
- 손절/익절
- 포지션 비중
- 자동매매

## Development Philosophy

- MVP 먼저.
- MVP Blocking QA ALL PASS 이후 다음 Milestone 계획.
- 각 Layer는 Loop Engineering으로 진행.
- PASS는 Cursor의 선언이 아니라 Acceptance Criteria의 증거로 판단.
- P0/P1 미해결 상태에서는 다음 Layer 금지.
- 모든 Layer에 감사 로그를 남긴다.
- MVP ALL PASS 후 Git tag로 봉인하고 외부 검증을 위해 중단한다.
