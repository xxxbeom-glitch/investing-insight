# MVP Handoff

## Final Status
PASS — MVP v0.1 freeze. Post-MVP 구현 금지. 외부 검토로 이관.

## Git
- Tag: mvp-v0.1-pass
- Commit: 67c9c2d13ef42ac646e8aa6e76fba50e07576416

## Versions
- System Spec: investing-insight-spec-v1.6
- DB Migrations: 0001–0009
- Quant Rule: quant-rules-v0.1
- Prompt: company-research-prompt-v0.1 / research-qa-prompt-v0.1 / final-judgment-prompt-v0.1
- LLM Profile: llm-profile-v0.1 (gpt-5.6-terra; company medium / QA+final high)
- Universe Rule: universe-rules-v0.1

## Representative Run
- run_id: afe422f2-2b2d-4aa6-8606-bd5d24356cc5
- snapshot_id: 73c39991-01a4-5e6d-9b0b-f2e6ab19c6f9
- content_hash: 5fb7a83bf533fafc35056024c6d40a71b22b775cc76ada68f01d370e2203d9fb
- quant scored: 3
- judgment_ids: (sample path exercised in tests; live judgment optional per model availability)

## Layer PASS Commits
- L00 7db06de · L01 37d4fc1 · L02 e184d41 · L03 be7a006 · L04 6fbcff7
- L05 4a9086e · L06 7752b5e · L07 960457c · L08 765c5f0 · L09 eb2002c

## QA Summary
- P0 Open: 0
- P1 Open: 0
- P2 Open: live model gateway naming / full-universe scale / browser e2e
- P3 Open: UI polish

## Test Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
.\apps\api\.venv\Scripts\python.exe -m pytest tests -q
cd apps\web; npm run build
```

## Reproduction Steps
1. Configure `.env.local` (never commit)
2. `python scripts/migrate.py`
3. Sample ingest scripts (universe/daily/sec) as used in L01–L03
4. Snapshot → quant → packet/research/QA/judgment modules
5. API `:8000` + Web `:3000` for PC audit UI

## Audit Completeness
`audit/mvp/L00` … `L10` each has PLAN/IMPLEMENTATION/TEST_RESULTS/QA_REPORT/OPEN_ISSUES/CHANGELOG/HANDOFF

## Known Limitations
- Company Research live call depends on OpenAI Responses accepting configured model id (fail-closed, no silent fallback)
- MVP sample universe is small (lab fixtures), not full US registry
- Mobile/tablet out of scope

## P2/P3 Backlog
See L10 OPEN_ISSUES and Post-MVP roadmap (do not implement now)

## External Reviewer Notes
> Do not start Post-MVP implementation until external review is complete.
