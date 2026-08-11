# REMEDIATION HANDOFF — External Re-review baseline 2422556 (P1-01 structural triples)

- status: ER11 remediation complete (await re-review)
- baseline_candidate: `2422556` (`2422556030353fbe9b2f7c68ab74497fabfe229e`)
- prior_nogo: `2c5b107` (`2c5b107d49c68a82adc154f429384c9f030fc38e`)
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`
- remediation_commit: (filled after content commit)
- review_candidate: HANDOFF hash-fill tip (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Claims are structured at verification into field/operator/value and compared to cited factual leaves. Copula lists are not used. Token-bag subset is not sufficient. Wrapper/meta is not support. QA SUPPORTED cannot bypass deterministic FAIL. | `claim_support.py`; `test_er11_remediation.py`; live judgment `9ea3b045-…` |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — regime `889d1f45-…` |
| ER3-P1-03 | unchanged this round | registry + 8-role prompt inject kept | M06 freeze `6c12334b-…` |

## Required fixtures

| claim | result |
|-------|--------|
| `regime is expansion` | PASS → field=`regime` operator=`equals` value=`expansion` |
| `regime was expansion` | PASS |
| `expansion is as_of` | FAIL |
| `expansion was as_of` | FAIL |
| `2026 is close` / `2026 was close` | FAIL |
| `100.5 is trading_date` | FAIL |
| `81.32 is overall_score` | FAIL |
| `close is 100.5` / `100.5 is close` | PASS |
| `trading_date is 2026-08-10` | PASS |
| leftover Unicode / `X` / wrapper | FAIL |

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag. Do not declare GO.
