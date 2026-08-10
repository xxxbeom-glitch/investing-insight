# 02. MVP v0.1 Specification

## 1. MVP Definition

MVP는 "미국 상장사 전체 레지스트리에서 시작하여, 데이터 수집·검증·Snapshot·정량 스크리닝·소수 기업 AI 분석·최종 Thesis 저장·PC Web 표시까지 한 번 끝까지 통과하는 최소 완성품"이다.

MVP의 목적은 투자 성과를 증명하는 것이 아니라 **시스템의 데이터 무결성과 판단 추적 가능성**을 증명하는 것이다.

## 2. MVP In Scope

### Universe Registry
- NYSE + NASDAQ registry 구성
- 일반 사업회사 보통주 + ADR 포함
- 지정 제외상품 제거
- company_id / security_id 생성
- S&P500 / NASDAQ100 / ADR 등 태그 확장 가능 구조

### Data
- 일별 가격/거래량
- 기본 security metadata
- SEC company facts 중심 핵심 재무
- SEC filings metadata
- raw payload hash / source metadata

### Data QA
- schema
- required field
- duplicate
- unit
- date
- impossible value
- future leak
- source traceability

### Snapshot
- cutoff timestamp
- universe membership
- price availability
- financial published_at eligibility
- source hashes
- snapshot content hash

### Quant
MVP score는 지나치게 복잡하게 하지 않는다.

공통 요소:
- Growth
- Profitability / Quality
- Cash Flow
- Financial Health
- Valuation
- Momentum

Industry-specific 25% 체계는 Post-MVP에서 확장한다. MVP는 industry-neutral 공통 엔진을 검증한다.

### Candidate Shortlist
- hard exclusion은 최소화
- 정량 rank 기반
- deep research 대상 10~20개 수준으로 제한 가능
- 최종 선정은 최대 5개로 MVP 축소 가능
- 좋은 후보가 없으면 0개 허용

### AI Research
MVP는 단일 주 LLM을 역할 분리해 사용한다.

1. Company Research call
2. Research QA call

출력은 schema-constrained JSON으로 저장한다.

### Judgment
각 최종 후보에 아래를 저장한다.
- selection status
- selection price
- quant score
- thesis
- key evidence
- bear case
- risk
- invalidation conditions
- uncertainty
- evidence quality
- data completeness
- snapshot_id
- model / prompt version

### PC Web
MVP에서 최소 5개 화면을 제공한다.
1. Dashboard
2. Research Runs
3. Candidates
4. Company Detail
5. Audit / QA

## 3. MVP Explicitly Out of Scope

- Macro Agent
- full Top-down industry attractiveness engine
- detailed value-chain engine
- industry-specific score templates
- independent second-LLM QA
- event-triggered research
- 1M/3M/6M performance grading automation
- rejected-stock long-term control group
- error taxonomy self-learning
- V1→V2 automatic rule optimization
- trading execution

이 기능들은 MVP ALL PASS 이후에만 시작한다.

## 4. MVP Run Modes

### Smoke Mode
- 고정 fixture / 대표 종목 20~30개
- 빠른 개발 루프
- 외부 API 장애와 무관한 deterministic tests 포함

### Integration Mode
- 실제 provider와 연결
- 여러 sector/ADR/대형·중형 종목을 포함한 대표 sample

### Full Registry Mode
- NYSE + NASDAQ 전체 security registry 구축
- 분류/제외 규칙 전체 적용

### Research Mode
- quant shortlist 중 제한된 수만 LLM 심층 분석
- 비용 상한 적용

## 5. MVP Success Criteria

MVP 성공은 다음을 모두 만족해야 한다.

- L00~L10 Blocking QA PASS
- P0 open issue = 0
- P1 open issue = 0
- P2/P3는 명시적 backlog 존재
- Snapshot 재현성 검증 PASS
- Quant deterministic test PASS
- unsupported factual claim 차단 또는 flagging PASS
- 최종 judgment가 snapshot과 source evidence로 역추적 가능
- PC Web에서 run → candidate → company → audit 경로 탐색 가능
- audit package 완성
- Git tag 생성

## 6. MVP Stop Rule

`MVP ALL PASS`가 되면 Cursor는 다음 Milestone을 구현하지 않는다.

반드시:
1. `MVP_HANDOFF.md` 생성
2. 전체 QA matrix 요약
3. open P2/P3 목록
4. Git tag / commit hash
5. DB schema version
6. prompt version
7. test command 목록
8. 재현 절차

을 남기고 중단한다.
