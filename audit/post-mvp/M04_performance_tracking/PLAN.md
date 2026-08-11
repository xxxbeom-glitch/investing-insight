# PLAN — Post-MVP Milestone 4 Performance Tracking

- milestone_id: M04
- spec: investing-insight-spec-v1.6 / 08_POST_MVP_ROADMAP.md Milestone 4
- previous: M03 @ 309d93b / e7c08ff
- status: PASS
- constraints: production cron DISABLED; no trading advice; MVP baseline untouched

## Goal
Judgment cohort(SELECTED / WATCH / REJECT)의 가격 성과를 1M·3M·6M으로 측정하고,
SPY/QQQ(및 가능 시 sector) 대비 상대성과·절대성과·thesis vs price outcome을 기록한다.

## In
- performance config (horizons, benchmarks)
- tables: performance_evals + control cohort tags
- deterministic engine from daily_prices (no LLM)
- CLI + unit tests
- API read summary (optional minimal)

## Out
- Auto rebalance / sell logic / broker
- Enabling cron
- Inventing prices when missing (INCOMPLETE, fail-closed)

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | Horizons 21/63/126 trading-day windows configurable | unit |
| AC-2 | Absolute return computed when prices exist | unit |
| AC-3 | Relative vs SPY/QQQ when benchmark prices exist | unit |
| AC-4 | WATCH/REJECT control group included in cohort eval | unit/integration |
| AC-5 | Missing prices → status INCOMPLETE (no fake returns) | unit |
| AC-6 | thesis_correctness vs price_outcome fields persisted | unit |
| AC-7 | P0=0 P1=0; cron disabled; tags untouched | audit |

## Tests first
- `tests/unit/test_performance_tracking.py`
