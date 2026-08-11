# REMEDIATION HANDOFF — External Re-review NO-GO 2c5b107 (P1-01 direction-free relations)

- status: ER10 remediation complete (await re-review)
- baseline_nogo: `2c5b107` (`2c5b107d49c68a82adc154f429384c9f030fc38e`)
- prior_content: `2f41149`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`
- remediation_commit: (fill after commit)
- review_candidate: HANDOFF hash-fill tip (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Field/value support is **direction-free**. Copula sides must be the same payload leaf (field↔value either way). Mentioned-field + foreign number is FAIL. Token-bag subset is necessary, not sufficient. No directed field→value regex ladder. | `claim_support.py`; `test_er10_remediation.py`; live judgment `66fdf368-…` |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — regime `889d1f45-…` |
| ER3-P1-03 | unchanged this round | registry + 8-role prompt inject kept | M06 freeze `011d948c-…` |

## Required fixtures

| claim | result |
|-------|--------|
| `expansion is as_of` | FAIL |
| `2026 is close` | FAIL |
| `100.5 is trading_date` | FAIL |
| `81.32 is overall_score` | FAIL |
| `close is 100.5` | PASS |
| `trading_date is 2026-08-10` | PASS |
| `regime is expansion` | PASS |
| `100.5 is close` | PASS |

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag. Do not declare GO.
