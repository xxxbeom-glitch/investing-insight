# 04. Quant & Research Specification

## 1. Separation of Responsibility

### Code
- financial ratios / growth rates
- momentum
- rank/percentile
- missing handling
- screening/ranking
- numeric claim cross-check where possible

### LLM
- business model
- competitive advantage
- financial/filing interpretation
- bull/bear synthesis
- risks/invalidation
- evidence synthesis
- final comparative judgment

숫자 계산을 LLM에 위임하지 않는다.

## 2. MVP Quant Engine

목표는 알파 모델 완성이 아니라 **재현 가능한 후보 압축 엔진**이다.

Components:
- Growth
- Quality
- Cash Flow
- Financial Health
- Valuation
- Momentum

예시 config:

```yaml
version: quant-v0.1
growth: 20
quality: 20
cashflow: 15
health: 15
valuation: 15
momentum: 15
```

가중치는 V1의 고정 실험변수이며 결과 몇 번 보고 즉시 바꾸지 않는다.

## 3. Hard Exclusion Policy

대표 hard exclusion:
- Universe 제외 security type
- identity 불명
- 핵심 가격 데이터 장기 부재
- 최소 분석 데이터 없음
- Data/Snapshot QA FAIL

단순 high P/E, 현재 적자, 고변동 성장만으로 자동 탈락 금지.

## 4. Relative Ranking

가능하면 저장:
- market-wide percentile
- peer/industry percentile

taxonomy version 기록.

## 5. Candidate Construction

```text
Eligible Universe
↓
Quant Score
↓
Data Quality Gate
↓
Market + Peer Rank
↓
10~20 Research Shortlist
```

## 6. Research Packet

LLM에 DB 전체를 넘기지 않는다.

포함:
- identity
- snapshot metadata
- price trend
- financial trend
- computed ratios
- valuation
- selected filing metadata/excerpts
- quant breakdown
- peer context
- evidence/source IDs
- missing/limitations

모든 numeric fact에는 evidence/source key가 연결되어야 한다.

## 7. LLM Role Profiles — Source of Truth

### MVP Baseline

#### Company Research
- model: `gpt-5.6-terra`
- reasoning.effort: `medium`
- purpose: 자료 이해·기업 Thesis 후보·리스크 구조화

#### Research QA
- model: `gpt-5.6-terra`
- reasoning.effort: `high`
- purpose: 원 분석의 오류·근거부족·논리비약·반대증거 누락 검증

#### Final Judgment
- model: `gpt-5.6-terra`
- reasoning.effort: `high`
- purpose: QA 통과 결과를 후보 간 비교하여 SELECTED/WATCH/REJECT 결정

OpenAI Responses API를 기본으로 사용한다.

### Profile Governance
- config 파일에서 관리
- code hard-code 금지
- API key와 분리
- 변경 시 `llm_profile_version` 증가
- 변경 전후 representative fixtures/research QA 비교
- silent fallback 금지
- 실제 resolved model과 effort를 DB/audit에 기록

## 8. Company Research Output Contract

필수:
- summary
- business_model
- growth_drivers[]
- moat_assessment
- financial_interpretation
- valuation_interpretation
- bull_case[]
- bear_case[]
- key_risks[]
- invalidation_conditions[]
- uncertainties[]
- claim_evidence_map[]
- unsupported_or_missing[]

중요 claim은 evidence ref 필수.

## 9. Research QA

원 분석을 옹호하지 않는다.

검사:
- 숫자 packet 일치
- claim에 evidence 존재
- evidence가 claim을 실제로 지지
- FACT/inference 구분
- 반대 자료 누락
- duplicate evidence로 확신 부풀림
- cutoff 이후 정보 유입
- unsupported claim

결과:
- PASS
- PASS_WITH_WARNING
- FAIL

FAIL → 동일 snapshot/packet 기준 수정 재분석 → 재QA.

## 10. Final Judgment

Status:
- SELECTED
- WATCH
- REJECT

규칙:
- QA FAIL research는 SELECTED 불가
- 선정 개수 강제 금지
- Final model은 새로운 사실을 발명하지 않고 QA 통과 evidence만 사용

Selected Thesis:
- one-line thesis
- why_now
- observable drivers
- key evidence
- biggest risk
- bear case
- invalidation conditions
- validation horizon
- evidence quality
- data completeness
- uncertainty

## 11. Model/Reasoning Audit Fields

각 LLM 실행마다 저장:
- agent_role
- model requested/resolved
- reasoning_effort
- llm_profile_version
- prompt_version
- input_hash/output_hash
- response_id when available
- token usage/cost when available

## 12. MVP Core Output Language

`buy/sell/position size`를 기본 생성하지 않는다.

- selected for tracking
- watch
- reject

로 유지한다.
