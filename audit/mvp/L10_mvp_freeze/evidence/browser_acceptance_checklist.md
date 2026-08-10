# Browser acceptance checklist (ER-P1-03)

Path: Dashboard → Run → Candidate → Company → Evidence/Audit → Settings

- [x] api_health: {"status":"ok","service":"investing-insight-api"}
- [x] web_dashboard: status=200 brand=True
- [x] api/v1/dashboard: status=200
- [x] api/v1/runs: status=200
- [x] api/v1/audit/summary: status=200
- [x] settings_no_raw_secrets: providers flags only
- [x] api/v1/settings/summary: status=200
- [x] run_detail_llm_fields: {"run":{"run_id":"89064263-8b6c-4a58-aeb4-0704ab539d9a","status":"quant_ready","cutoff_at":"2026-08-10 14:19:26.975647+00","quant_rule_version":"quant-rules-v0.1","prompt_bundle_version":null,"llm_pro
- [x] candidates: n=1
- [x] company_evidence: keys=['identity', 'run_id', 'quant', 'judgment', 'research', 'packet']
- [x] qa_fail_field_present: candidate_qa_or_dash_count visible=True
- [x] web/runs: status=200
- [x] web/candidates: status=200
- [x] web/audit: status=200
- [x] web/settings: status=200

Overall: PASS
Generated: 2026-08-10T14:21:01.256793+00:00