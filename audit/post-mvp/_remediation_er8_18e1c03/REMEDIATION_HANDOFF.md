# REMEDIATION HANDOFF — External Re-review NO-GO 18e1c03 (P1-01 Unicode tokens)

- status: ER8 remediation complete (await re-review)
- baseline_nogo: `4c87f7b` (`4c87f7b005665609d9f9859c61cead329847765a`)
- prior_candidate: `18e1c03` (ER7 leftover-ASCII; P1-01 reopened)
- prior_content: `ab189aa`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`
- remediation_commit: `b17a888` (`b17a8883866305df5c12025cdb72dc16869ea3c4`)
- review_candidate: HANDOFF hash-fill tip (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Claim support tokenizes Unicode letters + numbers (not `[a-z0-9]`). Length-1 tokens are checked. Cited **factual payload** only; wrapper `evidence_id`/`kind`/`ref` are not support. Missing-`payload` items use kind-declared fields only (`daily_price`, `financial_fact`). QA SUPPORTED cannot bypass deterministic FAIL. | `claim_support.py`; `test_er8_remediation.py`; `test_er7_remediation.py`; live judgment `82b71c56-…` |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — regime `889d1f45-…` |
| ER3-P1-03 | unchanged this round | registry + 8-role prompt inject kept | M06 freeze `d5029754-…` |

## Required fixtures

| claim | result |
|-------|--------|
| `regime is expansion and 매출 급증` | FAIL |
| `regime is expansion and 收入暴增` | FAIL |
| `regime is expansion and X` | FAIL |
| `regime is expansion and revenue surged` | FAIL |
| `regime is expansion` | PASS |

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag. Do not declare GO.
