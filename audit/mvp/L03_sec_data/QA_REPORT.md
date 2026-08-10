# QA_REPORT

- layer_id: L03
- executed_at: 2026-08-10
- commit_hash: be7a006
- previous_layer_commit: fa541d2
- status: PASS
- spec_version: investing-insight-spec-v1.6

## Acceptance Matrix

| ID | Criterion | Evidence | Result |
|----|-----------|----------|--------|
| AC-1 | US issuer + ADR/foreign fixtures | `tests/unit/test_sec.py` | PASS |
| AC-2 | period vs published_at 분리 | unit fixture + QA stub | PASS |
| AC-3 | restatement overwrite 0 | on conflict do nothing (ingest) | PASS |
| AC-4 | source traceability | financial_facts + source fields | PASS |
| AC-5 | User-Agent present | unit UA test | PASS |
| AC-6 | limiter ≤10 rps | unit limiter spacing | PASS |
| AC-7 | 403/429 not silent success | unit fail-closed | PASS |
| Live | AAPL companyfacts insert | integration ingest | PASS |

## Issue Counts

- P0 open: 0
- P1 open: 0
- P2 open: 1 (truncated companyfacts JSON for lab size — see OPEN_ISSUES)
- P3 open: 0

## Final QA Status

- Blocking Status: **PASS**
- Next layer eligible: yes (L04)
