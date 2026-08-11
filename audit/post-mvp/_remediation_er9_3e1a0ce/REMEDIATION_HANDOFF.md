# REMEDIATION HANDOFF — External Re-review NO-GO 3e1a0ce (P1-01 field-aware grounding)

- status: ER9 remediation complete (await re-review)
- baseline_nogo: `3e1a0ce` (`3e1a0ce3697895c44aa280e78a98065926790d87`)
- prior_content: `b17a888`
- prior ER7 leftover-ASCII: `18e1c03` / `ab189aa`
- prior ER6 NO-GO: `4c87f7b`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`
- remediation_commit: `2f41149` (`2f411497e8938b56c6fd75a6f6088f8d0da02652`)
- review_candidate: HANDOFF hash-fill tip (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Claim support is **field-aware**: copula/number pairings must match the cited field's value, not any token in the payload bag. Unicode leftover facts still FAIL. Wrapper/`*_id` keys are not support. QA SUPPORTED cannot bypass deterministic FAIL. | `claim_support.py`; `test_er9_remediation.py`; live judgment `5c8f2362-…` |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — regime `889d1f45-…` |
| ER3-P1-03 | unchanged this round | registry + 8-role prompt inject kept | M06 freeze `717c3fcb-…` |

## Required fixtures

| claim | cited payload | result |
|-------|---------------|--------|
| `regime is 2026-08-10` | `{regime: expansion, as_of: 2026-08-10}` | FAIL |
| `as_of is expansion` | same | FAIL |
| `overall_score 81.32` | overall=61.76, demand=81.32 | FAIL |
| `overall score of 81.32` | same | FAIL |
| `close 2026-08-10` | `{trading_date, close}` | FAIL |
| `regime is expansion` | `{regime: expansion, as_of: …}` | PASS |
| `regime is expansion as of 2026-08-10` | same | PASS |
| `overall_score 61.76` | overall=61.76 | PASS |

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag. Do not declare GO.
