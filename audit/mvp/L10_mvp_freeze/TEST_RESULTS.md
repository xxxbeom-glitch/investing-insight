# TEST_RESULTS

- layer_id: L10
- executed_at: 2026-08-10T21:22:57+09:00 (freeze) / remediation revalidation later
- freeze_content_commit: 67c9c2d
- baseline_tag_target: e98ff33
- spec_version: investing-insight-spec-v1.6

## Commands (historical)

```text
scripts/secret_scan.py          # PASS
pytest tests -q                 # 46 passed
npm run build (apps/web)        # success (L09; reused for freeze)
```

## Results Summary (historical)

| Suite | Pass | Fail | Source |
|-------|------|------|--------|
| secret_scan | PASS | 0 | original TEST_RESULTS |
| pytest | 46 | 0 | original TEST_RESULTS |
| next build | success | — | L09 / freeze |

## Representative Run (from MVP_HANDOFF)

- run_id: `afe422f2-2b2d-4aa6-8606-bd5d24356cc5`
- snapshot_id: `73c39991-01a4-5e6d-9b0b-f2e6ab19c6f9`
- content_hash: `5fb7a83bf533fafc35056024c6d40a71b22b775cc76ada68f01d370e2203d9fb`
- quant scored: 3
- judgment_ids: sample path exercised in tests; live judgment optional per model availability

## Remediation revalidation (ER-P1-04)

| Artifact | Path / Result |
|----------|---------------|
| pytest revalidation | `evidence/pytest_revalidation_erp104.txt` — **unit** 28 passed; full `tests/` suite hung (>6min, killed) — unknown for full-suite at remediation |
| LLM config versions snapshot | `evidence/llm_config_versions_erp104.md` |
| registry QA (ER-P1-01) | `evidence/registry_qa_report.json` |
| API/Web server smoke logs | `evidence/api_server.log`, `web_server.log` |
