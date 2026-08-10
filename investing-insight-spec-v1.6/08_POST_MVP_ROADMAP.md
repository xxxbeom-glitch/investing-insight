# 08. Post-MVP Roadmap

MVP ALL PASS + 외부 검토 전에는 아래를 구현하지 않는다.

## Gate 0 — Production Readiness Review

MVP를 곧바로 상시운영하지 않는다.

검토:
- Supabase backup/restore
- secret rotation
- provider quotas/cost
- scheduler failure handling
- retry/dead-letter/quarantine
- monitoring/alerting
- deploy access control
- operational runbook

PASS 후에만 자동운영 시작.

## Milestone 1 — Automation & Deployment

- hosted PC Web deployment
- daily market/SEC ingest scheduler
- biweekly research scheduler
- backup/restore automation
- operational health dashboard

## Milestone 2 — Top-down Industry Engine

- FRED adapter
- market regime
- industry attractiveness schema
- demand/CAPEX/supply/pricing/margin/bottleneck
- industry QA
- value-chain map
- Top-down candidates
- Bottom-up shortlist와 union

## Milestone 3 — Multi-Agent / Multi-Profile Research

Roles:
- Market
- Industry
- Company
- Event
- Research
- Adversarial Reviewer
- Final Selector

Rules:
- 같은 Snapshot
- 역할별 최소 input
- JSON contracts
- 자유대화 swarm 금지

### Model Optimization Experiments
- high-volume/simple classification: `gpt-5.6-luna` 후보
- general research: `gpt-5.6-terra`
- independent high-value final verification: `gpt-5.6-sol` 후보

변경은 비용/품질 benchmark 후 승인한다. 모델 차이 때문에 과거 성과가 섞이지 않도록 profile version을 분리한다.

## Milestone 4 — Performance Tracking

- 1M/3M/6M
- SPY/QQQ/sector benchmark
- WATCH/near-reject control group
- absolute vs relative
- thesis correctness vs price outcome

## Milestone 5 — Error Database

- growth persistence overestimate
- valuation underweight
- cycle misread
- moat/competitor miss
- momentum/macro/event miss
- data error
- unforeseen external shock

## Milestone 6 — V1→V2 Governance

- score/prompt/model/profile change proposal
- replay test
- holdout
- approval log
- version freeze

한두 번의 실패로 rule/weight/model을 바꾸지 않는다.

## Long-Term Optional

- event-triggered reanalysis
- portfolio simulation
- entry timing
- sell logic
- position sizing
- broker integration(KIS 등은 실제 실행 필요 시에만 검토)
