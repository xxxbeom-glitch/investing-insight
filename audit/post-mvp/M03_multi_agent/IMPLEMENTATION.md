# IMPLEMENTATION — M03 Multi-Agent

## Built
1. `config/llm_profiles.v0.2.yaml` (terra only; luna/sol experiments out)
2. Migration `0012_multi_agent.sql` — multi_agent_runs / agent_outputs / agent_gates
3. Schemas: `packages/schemas/agent_*_output.schema.json`
4. `app/agents/` — binding (frozen topdown/bottom-up + shared snapshot), runner, gates, orchestrator, mock client
5. CLI: `scripts/run_multi_agent.py` (`--mock` default, `--live` optional)
6. Unit tests: `tests/unit/test_multi_agent.py`

## Pipeline
Market → Industry → Company → Event → Research → **Research QA gate** → Adversarial → **Adversarial gate** → Final Selector

## Constraints
- Same snapshot_id for all role outputs
- Structured JSON only (no free-chat swarm)
- Production cron DISABLED
