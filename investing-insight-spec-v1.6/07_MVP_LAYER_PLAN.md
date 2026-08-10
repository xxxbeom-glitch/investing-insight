# 07. MVP Layer Plan

## Execution Rule

L00→L10 순서. 이전 Layer P0/P1=0 + Blocking QA PASS 전에는 다음 Layer 금지.

---

## L00 — Foundation, Supabase, Config & Audit Framework

### Goal
프로젝트 실행·DB·secret/config·test/audit 기반 구축.

### Build
- repo skeleton
- web/api health
- Supabase PostgreSQL connection
- migration framework
- `.env.example` / secret boundary
- `config/llm_profiles.v0.1.yaml`
- config version registry
- structured logging
- test framework
- audit directory generator
- JSON schema contract skeleton

### Blocking Acceptance
- clean install 실행 가능
- web→api health PASS
- api→Supabase connection PASS
- migrations reproducible
- secret Git leakage 0
- Supabase secret browser exposure 0
- LLM profile config load/validate PASS
- audit template 생성 PASS

---

## L01 — Universe & Identity

### Goal
NYSE/NASDAQ 투자 대상 registry 정확히 구축.

### Build
- Massive adapter
- companies/securities
- security classification/exclusion
- ADR
- company_id/security_id
- raw hash

### Blocking Acceptance
- NYSE/NASDAQ 포함
- 제외 security leakage 0 in fixtures
- ADR 포함 fixture PASS
- duplicate identity 0
- exclusion reason 추적
- raw source/hash

---

## L02 — Market Data

### Goal
일별 OHLCV 적재.

### Build
- Massive daily ingest
- retry/backoff
- missing reason
- raw payload storage
- market QA

### Blocking Acceptance
- fixture OHLCV 정확
- duplicate bar 0
- date/type QA PASS
- API failure silent success 0
- rerun idempotent

---

## L03 — SEC Data

### Goal
CIK mapping + company facts/filing metadata.

### Build
- SEC client
- `SEC_USER_AGENT`
- <=10 req/s limiter
- CIK mapping
- facts normalization
- filing metadata
- source hash
- published/accepted time

### Blocking Acceptance
- US issuer + ADR/foreign issuer fixtures
- period vs published_at 분리
- restatement overwrite 0
- stored facts source traceability 100%
- User-Agent test PASS
- limiter test PASS
- 403/429 silent success 0

---

## L04 — Normalization & Data QA

### Goal
공통 schema와 validated/quarantine 경계 확립.

### Build
- canonical metrics
- unit/currency
- quarantine
- data quality
- QA commands

### Blocking Acceptance
- unit fixture PASS
- missing != zero
- invalid/future dates rejected
- quarantine traceable
- validated layer에 QA FAIL 0

---

## L05 — Snapshot Engine

### Goal
cutoff 당시 이용 가능 정보만 immutable state로 고정.

### Build
- research_runs/snapshot/items
- eligible_at logic
- content hash
- Snapshot QA
- snapshot manifest schema

### Blocking Acceptance
- cutoff 이후 records 0
- same input/cutoff → same hash
- later restatement old snapshot 변경 0
- source/version 역추적
- manifest schema PASS

---

## L06 — Quant Engine

### Goal
LLM 없이 deterministic shortlist.

### Build
- metrics
- quant config/version
- component/total scores
- ranks
- missing handling

### Blocking Acceptance
- formula unit tests PASS
- same snapshot+rule=same score
- aggregation PASS
- LLM dependency 0
- input_hash/rule_version 기록

---

## L07 — Research Packet & Company Research

### Goal
상위 후보를 동적 JSON packet으로 만들어 AI Research 수행.

### Build
- packet builder
- `company_analysis_input.schema.json`
- `company_analysis_output.schema.json`
- token/context budget
- OpenAI Responses API adapter
- Company Research role profile
- structured output/evidence refs

### Baseline
- `gpt-5.6-terra`
- `reasoning.effort=medium`

### Blocking Acceptance
- packet snapshot evidence only
- numeric facts evidence IDs
- input/output schema PASS
- requested/executed model+effort 기록
- llm_profile_version/prompt/input/output hash 기록
- unavailable model silent fallback 0
- unsupported/missing explicit

---

## L08 — Research QA & Final Judgment

### Goal
Research를 엄격 검수하고 최종 상태/Thesis 저장.

### Build
- Research QA role
- Final Judgment role
- claim/evidence checker
- retry/revise loop
- immutable judgment
- QA/Judgment schemas

### Baseline
Research QA:
- `gpt-5.6-terra`, `high`

Final Judgment:
- `gpt-5.6-terra`, `high`

### Blocking Acceptance
- unsupported numeric claim fixture rejected/flagged
- QA FAIL → SELECTED 불가
- final model이 evidence 없는 새 fact 추가 시 FAIL
- role profile mismatch 0
- silent fallback 0
- selection minimum 강제 없음
- judgment overwrite 0
- SELECTED risk+bear+invalidation required

---

## L09 — PC Web Vertical Slice

### Goal
Run→Candidate→Company→Evidence→Audit 전체 탐색.

### Build
- Dashboard
- Research Runs
- Candidates
- Company Detail
- Audit & QA
- Settings summary

### Blocking Acceptance
- evidence navigation works
- latest vs historical clear
- QA FAIL visible
- 1280px+ usable
- LLM profile/model/effort visible
- secret raw value exposure 0

---

## L10 — MVP All-Pass, Freeze & Handoff

### Run
- unit/integration/e2e
- full registry ingest
- representative research run
- audit completeness
- config/schema/version verification
- regression

### Blocking Acceptance
- P0=0 / P1=0
- L00~L09 blocking PASS
- audit complete
- sample run reproducible
- secret scan PASS
- role별 LLM execution trace PASS
- Git tag `mvp-v0.1-pass`
- `MVP_HANDOFF.md`

### Stop
PASS 후 Post-MVP 구현 금지. 외부 검토로 넘긴다.
