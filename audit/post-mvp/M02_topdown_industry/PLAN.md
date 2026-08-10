# PLAN — Post-MVP Milestone 2 Top-down Industry Engine

- milestone_id: M02
- spec: investing-insight-spec-v1.6 / 08_POST_MVP_ROADMAP.md Milestone 2
- branch: post-mvp/phase-1
- previous: M01 @ 61107c3 / bc0a51a
- status: PASS
- constraints: production cron DISABLED; MVP baseline untouched

## Goal
Bottom-up MVP 위에 Top-down 수직 슬라이스를 둔다: FRED → regime → industry attractiveness → QA → value-chain → candidates → bottom-up union.

## In
1. FRED adapter (fail-closed if key missing)
2. Market regime (deterministic)
3. Industry attractiveness schema + demand/CAPEX/supply/pricing/margin/bottleneck scores
4. Industry QA (deterministic)
5. Value-chain map (config-versioned)
6. Top-down candidates
7. Union with bottom-up shortlist

## Out
- Multi-agent swarm (M3)
- Production scheduler enable
- Broker/timing
- Fake PITR / MVP audit mutation

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | FRED client fetches ≥1 configured series; persists observations; no API key in logs/stdout | unit + live smoke |
| AC-2 | Market regime computed from observations; versioned rule id | unit |
| AC-3 | Industry attractiveness rows include 6 dimension scores + overall | unit/integration |
| AC-4 | Industry QA FAIL blocks candidate promotion | unit |
| AC-5 | Value-chain map loads from versioned config | unit |
| AC-6 | Top-down candidates produced for PASS industries | integration |
| AC-7 | Union endpoint/script merges top-down + bottom-up without inventing ranks | integration |
| AC-8 | P0=0 P1=0; cron still disabled | OPEN_ISSUES + cron.examples |
| AC-9 | MVP tags untouched | git rev-list |

## Tests first
- `tests/unit/test_fred_client.py`
- `tests/unit/test_topdown_engine.py`
