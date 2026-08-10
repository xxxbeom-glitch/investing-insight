# L10 Remediation Handoff (ER-P1-01…04)

## Status
Remediation complete on branch `review/l10-remediation-er-p1`.  
Baseline tag **`mvp-v0.1-pass` @ `e98ff33` unchanged** (not moved).  
Post-MVP not started. Ready for **external re-review**. Do **not** create `mvp-v0.1-review-pass` until reviewer confirms.

## Findings

| ID | Result | Evidence |
|----|--------|----------|
| ER-P1-01 | PASS | `audit/mvp/L10_mvp_freeze/evidence/registry_ingest_stats.json`, `registry_qa_report.json` |
| ER-P1-02 | PASS | `audit/mvp/L10_mvp_freeze/evidence/live_research_run.json` |
| ER-P1-03 | PASS (Playwright headless) | `evidence/browser_acceptance_playwright.json`, screenshots under `evidence/playwright_er_p1_03/` |
| ER-P1-04 | PASS (with unknowns noted) | L03–L10 audit metadata backfill + `evidence/llm_config_versions_erp104.md` |

## Registry (ER-P1-01)
- Scope: Massive active stocks with `exchange` in {XNYS, XNAS}, ticker-cursor pagination
- seen 8500 · included 5226 · excluded 3274 · NYSE 2924 · NASDAQ 5576
- included_common 4859 · included_adr 367 · missing_cik (ingest) 549
- excluded_security_leakage **0** · duplicate exchange+ticker **0**

## Live integration (ER-P1-02)
- run_id: `89064263-8b6c-4a58-aeb4-0704ab539d9a`
- research/qa/judgment: requested=resolved=`gpt-5.6-terra`
- QA status FAIL → final judgment **REJECT** (policy intact)
- judgment_id: `c27abda1-e195-48af-b3a5-a9dfb92e4da7`

## Browser (ER-P1-03)
Dashboard → Runs → Candidates → Company/Evidence → Audit → Settings: all checks PASS; settings has no raw secrets.

## Regression
- secret_scan PASS
- pytest: 46 passed (scoped snapshots after full registry)
- next build: PASS (prior run in this remediation)

## Tag policy
- Keep `mvp-v0.1-pass`
- After external re-review PASS → new tag `mvp-v0.1-review-pass` on this branch HEAD
