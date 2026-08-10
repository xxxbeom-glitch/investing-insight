# TEST_RESULTS

- layer_id: L09
- executed_at: 2026-08-10T21:18:49+09:00
- commit_hash: eb2002c
- spec_version: investing-insight-spec-v1.6

## Commands

```text
pytest tests -q
cd apps/web; npm run build
```

## Results Summary (historical)

| Suite | Pass | Fail | Skip | Source |
|-------|------|------|------|--------|
| pytest full suite after L09 | 46 | 0 | 0 | original TEST_RESULTS |
| next build | success | — | — | original TEST_RESULTS |

## Browser E2E

- Automated browser suite: not present at PASS (P2)
- Remediation smoke logs (when servers run): `audit/mvp/L10_mvp_freeze/evidence/web_server.log`, `api_server.log`, `api_server.err.log`
- Full interactive browser path proof: unknown — revalidated during L10 remediation (see above logs + any ER-P1-03 evidence if present)

Revalidation pytest: `audit/mvp/L10_mvp_freeze/evidence/pytest_revalidation_erp104.txt`
