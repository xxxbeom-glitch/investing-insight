# MVP Handoff

## Final Status
**MVP v0.1 external re-review: PASS.**  
Post-MVP는 `post-mvp/phase-1`에서 Gate 0(Production Readiness)부터 진행한다.  
MVP frozen baseline(audit L00–L10 / tag `mvp-v0.1-pass`)은 수정하지 않는다.

## Git
- Baseline tag: `mvp-v0.1-pass` → **`e98ff33`** (unchanged)
- Prior freeze content commit: **`67c9c2d`**
- External re-review PASS tag: `mvp-v0.1-review-pass` → **`c1a6692`**
- Remediation evidence: `audit/mvp/L10_mvp_freeze/REMEDIATION_HANDOFF.md`
- Active branch for Post-MVP: `post-mvp/phase-1`

## Versions
- System Spec: investing-insight-spec-v1.6
- DB Migrations: 0001–0009
- Quant Rule: quant-rules-v0.1
- Prompt: company-research-prompt-v0.1 / research-qa-prompt-v0.1 / final-judgment-prompt-v0.1
- LLM Profile: llm-profile-v0.1 (gpt-5.6-terra; company medium / QA+final high)
- Universe Rule: universe-rules-v0.1

## Representative Run
### Baseline freeze sample
- run_id: afe422f2-2b2d-4aa6-8606-bd5d24356cc5
- snapshot_id: 73c39991-01a4-5e6d-9b0b-f2e6ab19c6f9

### Live Research→QA→Judgment (ER-P1-02)
- run_id: 89064263-8b6c-4a58-aeb4-0704ab539d9a
- judgment_id: c27abda1-e195-48af-b3a5-a9dfb92e4da7

### Playwright UI (ER-P1-03)
- evidence: `audit/mvp/L10_mvp_freeze/evidence/browser_acceptance_playwright.json`

## Layer PASS Commits
- L00 7db06de · L01 37d4fc1 · L02 e184d41 · L03 be7a006 · L04 6fbcff7
- L05 4a9086e · L06 7752b5e · L07 960457c · L08 765c5f0 · L09 eb2002c
- L10 freeze `67c9c2d` / handoff `e98ff33` · remediation UI `c1a6692`

## QA Summary
- P0 Open: 0
- P1 Open: 0
- External review: PASS (`mvp-v0.1-review-pass`)

## Test Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
.\apps\api\.venv\Scripts\python.exe -m pytest tests -q
cd apps\web; npm run build
```

## Known Limitations
- Full browser E2E suite beyond core Playwright path remains P2
- Hosted deploy / schedulers blocked until Gate 0 + Milestone 1

## External Reviewer Notes
> MVP baseline is frozen. Post-MVP starts at Gate 0 Production Readiness on `post-mvp/phase-1`.
