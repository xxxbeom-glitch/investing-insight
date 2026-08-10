# 04. Quant & Research Specification

## 1. Separation of Responsibility

### Code
- financial ratios
- growth rates
- momentum
- ranks
- percentile
- missing-data penalties
- filter/ranking

### LLM
- business model
- competitive advantage
- industry linkage
- earnings quality interpretation
- bull / bear reasoning
- risk
- invalidation conditions
- evidence synthesis

LLM에게 숫자 계산을 위임하지 않는다.

## 2. MVP Quant Engine

MVP의 목적은 "완벽한 알파 모델"이 아니라 **재현 가능한 후보 압축 엔진**을 만드는 것이다.

### Components
- Growth
- Quality
- Cash Flow
- Financial Health
- Valuation
- Momentum

가중치는 config file에서 versioning한다.

예시 구조:

```yaml
version: quant-v0.1
growth: 20
quality: 20
cashflow: 15
health: 15
valuation: 15
momentum: 15
```

이 값은 초기 구현값일 뿐 영구 정답으로 취급하지 않는다.

## 3. Hard Exclusion Policy

MVP에서 hard exclusion은 최소화한다.

허용되는 대표 hard exclusion:
- Universe 자체에서 제외되는 security type
- 핵심 identity 불명
- 핵심 가격 데이터 장기 부재
- 분석에 필요한 최소 데이터가 전혀 없음
- QA FAIL

단순히 아래 이유만으로 자동 탈락시키지 않는다.
- high P/E
- current loss
- high growth volatility

이는 score/risk에 반영한다.

## 4. Relative Ranking

가능하면 두 관점을 모두 저장한다.
- market-wide percentile
- peer/industry percentile

MVP에서 industry taxonomy가 완전하지 않으면 sector/industry provider taxonomy를 사용하되, `taxonomy_version`을 기록한다.

## 5. Candidate Construction

```text
Full eligible universe
↓
Quant score
↓
data quality threshold
↓
market rank + peer rank
↓
shortlist
```

MVP 기본 shortlist 목표는 10~20개다.

최종 LLM 대상 수는 config로 조절한다.

## 6. Research Packet

LLM에게 DB 전체를 넘기지 않는다.

각 기업 packet은 최소한 아래 구조를 가진다.

```text
identity
snapshot metadata
price trend
financial trend
computed ratios
valuation
recent filings metadata / selected excerpts
known events if present
quant breakdown
peer context
source/evidence IDs
```

모든 numeric fact에는 evidence/source key가 연결되어야 한다.

## 7. Company Research Output Contract

LLM output은 자유 서술만 허용하지 않는다.

필수 필드:
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
- evidence_refs[]
- unsupported_or_missing[]

각 중요 claim은 `evidence_refs`를 가져야 한다.

## 8. Research QA

Research QA는 원 분석을 옹호하지 않는다.

검사:
- 숫자가 packet과 일치하는가
- claim에 evidence가 있는가
- evidence가 claim을 실제로 지지하는가
- FACT와 inference가 섞이지 않았는가
- 반대자료를 무시했는가
- evidence duplication 때문에 확신이 부풀려졌는가
- cutoff 이후 정보가 사용됐는가

결과:
- PASS
- PASS_WITH_WARNING
- FAIL

FAIL이면 동일 packet으로 수정 재분석 후 다시 QA한다.

## 9. Final Judgment

MVP 최종 status:
- SELECTED
- WATCH
- REJECT

선정 개수를 강제하지 않는다.

### Selected Thesis Contract
- one-line thesis
- why_now
- observable drivers
- key evidence
- biggest risk
- bear case
- invalidation conditions
- expected validation horizon
- evidence quality
- data completeness
- uncertainty

## 10. No Trading Language in MVP Core

MVP report에서 기본적으로 `buy/sell/position size`를 생성하지 않는다.

출력은:
- selected for tracking
- watch
- reject

관점으로 유지한다.
