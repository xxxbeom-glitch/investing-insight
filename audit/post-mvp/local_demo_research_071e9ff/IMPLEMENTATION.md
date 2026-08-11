# IMPLEMENTATION

- status: DONE (local demo; not GO)
- completed_at: 2026-08-11T14:26:00+00:00
- scheduler_enable_allowed: false
- go_declared: false

## Commands

```powershell
$env:PYTHONPATH = "apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\run_biweekly_research.py --limit 5
```

수동 1회. cron 미사용.

## Result

- job_id: `e5f98040-49e5-442e-aa9d-8a936cb01678`
- run_id: `31835b24-8823-4306-be7a-c48b43a4b66d`
- researched: 1 (AAPL / XNAS)
- quant shortlist: 1
- judgment: REJECT
- research_qa: FAIL

limit=5였으나 priced security 조회가 1건만 반환됨 (`security_ids` 길이 1).

## Files

- `biweekly.json` — job stdout (secret 없음)
- `dashboard_after.json` — `/v1/dashboard`
- `candidates.json` — `/v1/runs/{run_id}/candidates`
