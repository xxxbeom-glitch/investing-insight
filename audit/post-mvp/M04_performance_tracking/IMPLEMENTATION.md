# IMPLEMENTATION — M04 Performance Tracking

## Built
- `config/performance_rules.v0.1.yaml` (1M/3M/6M = 21/63/126)
- `migrations/0013_performance_tracking.sql`
- `app/performance/` metrics + engine
- `scripts/run_performance_eval.py`
- `GET /v1/performance/summary`
- unit tests

## Behavior
- SELECTED = selected cohort; WATCH/REJECT = control
- Absolute + SPY/QQQ relative when benchmark prices exist
- Missing forward bars / benchmarks → INCOMPLETE (no fake returns)
- thesis_correctness deterministic heuristic vs price_outcome
