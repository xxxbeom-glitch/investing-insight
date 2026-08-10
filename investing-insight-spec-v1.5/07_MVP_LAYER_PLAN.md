# 07. MVP Layer Plan

## Execution Rule

각 Layer는 순서대로 진행한다. 이전 Layer의 P0/P1이 0이고 Blocking QA가 PASS여야 다음 Layer를 시작한다.

---

## L00 — Foundation & Audit Framework

### Goal
프로젝트가 이후 모든 작업을 검증 가능하게 만드는 기반을 만든다.

### Build
- repo skeleton
- web/api 실행
- PostgreSQL connection
- migration framework
- structured logging
- test framework
- audit directory generator
- config/version registry
- health endpoint

### Blocking Acceptance
- clean install에서 실행 가능
- web → api health 확인 가능
- DB migration up/down 또는 재생성 절차 검증
- unit/integration test command 존재
- audit template 자동 생성 가능
- secret이 git에 포함되지 않음

---

## L01 — Universe & Identity

### Goal
NYSE/NASDAQ 투자 대상 registry를 정확히 만든다.

### Build
- provider adapter
- companies
- securities
- classification
- exclusion rules
- ADR flag
- company_id/security_id

### Blocking Acceptance
- NYSE/NASDAQ 포함
- 명시 제외 security type leakage 0 in classification fixture tests
- ADR fixture가 포함됨
- duplicate security identity 0
- exclusion reason 추적 가능
- raw source/hash 존재

---

## L02 — Market Data

### Goal
일별 가격과 거래량을 역사 DB에 안정적으로 적재.

### Build
- daily price ingest
- retry/backoff
- missing reason
- raw payload storage
- market data QA

### Blocking Acceptance
- fixture symbols OHLCV 정확
- duplicate daily bar 0
- date/type QA PASS
- API failure가 silent success로 처리되지 않음
- rerun idempotent

---

## L03 — SEC Data

### Goal
회사와 SEC identity를 연결하고 핵심 company facts / filings metadata 수집.

### Build
- CIK mapping
- company facts normalization
- filings metadata
- source hash
- filed/published time handling

### Blocking Acceptance
- 대표 US issuer와 ADR/foreign issuer fixture mapping 확인
- period vs published_at 분리
- restated fact overwrite 금지
- source traceability 100% for stored facts

---

## L04 — Normalization & Data QA

### Goal
시장/SEC 데이터를 공통 schema로 정리하고 검증 전/후 경계를 확립.

### Build
- canonical metric keys
- unit/currency rules
- quarantine
- data quality status
- QA commands

### Blocking Acceptance
- unit conversion fixture PASS
- missing != zero
- invalid/future date fixture FAIL 처리
- quarantine record 추적 가능
- validated table에 QA FAIL record 0

---

## L05 — Snapshot Engine

### Goal
특정 cutoff 당시 알 수 있었던 정보만으로 immutable analysis state 생성.

### Build
- research_runs
- snapshot
- eligible record selection
- content hash
- snapshot QA

### Blocking Acceptance
- cutoff 이후 record 0
- same input/cutoff → same content hash
- later restatement가 old snapshot을 변경하지 않음
- source/version 역추적 가능

---

## L06 — Quant Engine

### Goal
LLM 없이 deterministic shortlist 생성.

### Build
- metric calculator
- score config version
- total/component scores
- rank
- missing handling

### Blocking Acceptance
- formula unit tests PASS
- same snapshot + same rule = same score
- score components sum/aggregation rule PASS
- no LLM dependency
- result contains input_hash/rule_version

---

## L07 — Research Packet & LLM Research

### Goal
상위 후보를 근거 중심으로 심층 분석.

### Build
- packet builder
- token/context budget
- LLM provider adapter
- structured output
- evidence references

### Blocking Acceptance
- packet only uses snapshot-eligible evidence
- numeric facts map to evidence IDs
- output schema validation PASS
- model/prompt version stored
- unsupported/missing items explicit

---

## L08 — Research QA & Judgment

### Goal
LLM 결과를 검수하고 최종 SELECTED/WATCH/REJECT Thesis를 저장.

### Build
- QA prompt
- numeric claim checker where possible
- evidence grounding checker
- retry/revise loop
- immutable judgment

### Blocking Acceptance
- unsupported numeric claim fixture rejected/flagged
- QA FAIL judgment cannot become SELECTED
- selection count forced minimum 없음
- judgment cannot be UPDATE-overwritten
- risk + invalidation required for SELECTED

---

## L09 — PC Web Vertical Slice

### Goal
실제 사용자가 전체 연구 결과와 QA 근거를 탐색.

### Build
- Dashboard
- Research Runs
- Candidates
- Company Detail
- Audit & QA

### Blocking Acceptance
- run → candidate → company → evidence navigation works
- latest vs historical judgment clearly separated
- QA FAIL visible
- 1280px+ desktop core flow usable

---

## L10 — MVP All-Pass, Freeze & Handoff

### Goal
MVP 전체를 다시 검증하고 외부 감사 가능한 상태로 봉인.

### Run
- full unit tests
- integration tests
- e2e smoke
- full registry ingest
- representative research run
- audit completeness check
- regression check

### Blocking Acceptance
- P0 = 0
- P1 = 0
- L00~L09 all blocking criteria PASS
- audit docs complete
- sample run reproducible
- git tag `mvp-v0.1-pass`
- `MVP_HANDOFF.md` complete

### Stop
이 Layer PASS 후 Post-MVP 구현을 시작하지 않는다.
