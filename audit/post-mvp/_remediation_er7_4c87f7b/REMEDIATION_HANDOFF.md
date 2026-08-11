# REMEDIATION HANDOFF — External Re-review NO-GO 4c87f7b (P1-01 leftover facts)

- status: ER7 remediation complete (await re-review)
- baseline_nogo: `4c87f7b` (`4c87f7b005665609d9f9859c61cead329847765a`)
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`
- remediation_commit: `ab189aa` (`ab189aa740255136432100ed15a0ac37ca9a00fd`)
- review_candidate: HANDOFF hash-fill tip (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Every open-class token and number in a claim must appear in the **cited payload**. No fact denylist. Wrapper keys are not support. Extra conjuncts like `and revenue surged` FAIL. | `claim_support.py`; `test_er7_remediation.py`; live judgment `0c0f5a2c-…` |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — regime `889d1f45-…` |
| ER3-P1-03 | unchanged this round | registry + 8-role prompt inject kept | M06 freeze `3515ce86-…` |

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag.
