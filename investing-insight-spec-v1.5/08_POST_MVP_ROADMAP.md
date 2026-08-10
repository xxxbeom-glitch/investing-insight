# 08. Post-MVP Roadmap

이 문서는 방향만 정의한다. MVP ALL PASS 전에는 아래 기능을 구현하지 않는다.

## Milestone 1 — Top-down Industry Engine

- FRED 등 macro adapter
- market regime summary
- industry attractiveness schema
- demand / CAPEX / supply / pricing / margin / bottleneck
- industry QA
- value-chain map
- Top-down candidate generation
- 기존 Bottom-up shortlist와 union

Exit Gate:
- 동일 snapshot 기준 Top-down 결과 재현
- 산업 claim evidence grounding
- 산업 후보 → 기업 실적 연결성 검증

## Milestone 2 — Multi-Agent Research

Roles:
- Market Agent
- Industry Agent
- Company Agent
- Event Agent
- Research Agent
- Adversarial Reviewer
- Final Selector

Rules:
- 동일 Snapshot 공유
- role별 input 최소화
- JSON contract
- 자유 대화식 agent swarm 금지

독립 LLM 검증을 최종 후보에 추가.

## Milestone 3 — Performance Tracking

- selection price
- 1M / 3M / 6M
- SPY
- QQQ
- sector benchmark
- WATCH / near-reject control group
- absolute vs relative return
- thesis correctness vs price outcome 분리

## Milestone 4 — Error Database

오류 taxonomy 예:
- growth persistence overestimate
- valuation underweight
- cycle misread
- moat overestimate
- competitor underestimate
- momentum miss
- macro miss
- event miss
- data error
- unforeseeable external shock

반복 오류가 충분히 축적될 때만 rule 변경 후보를 만든다.

## Milestone 5 — V1 → V2 Governance

- score/prompt/model 변경 proposal
- old vs new replay test
- holdout period
- change approval log
- version freeze

한두 번의 실패로 weight를 변경하지 않는다.

## Milestone 6 — Automation & Deployment

MVP 로컬 실행이 안정된 뒤 고려:
- scheduled daily ingest
- scheduled biweekly run
- notification
- hosted DB/object store
- deployment
- backup/restore

## Long-Term Optional

- event-triggered reanalysis
- portfolio simulation
- entry timing model
- sell logic
- position sizing

이들은 stock-selection skill 검증 이후에만 검토한다.
