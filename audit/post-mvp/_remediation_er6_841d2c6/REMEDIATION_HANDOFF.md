# REMEDIATION HANDOFF — External Re-review NO-GO 841d2c6

- status: ER6 remediation complete (await re-review)
- baseline_nogo: `841d2c6` (`841d2c6e45801047703149a3114231f22b5e7e26`)
- report: `EXTERNAL_REREVIEW_POST_MVP_841d2c6.md`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`. Annotated tag objects `fffff6a0` / `229bbaec`.
- checkpoint: `6c5eeb7` (report freeze)
- remediation_commit: `ad0fb2f` (`ad0fb2fd8d969e75730baf17ce06567ceb997802`)
- review_candidate: HANDOFF hash-fill tip on `post-mvp/phase-1` (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Claim admission requires cited-evidence support + matching QA `claim_verdicts` (`SUPPORTED`/`UNSUPPORTED`). Allowed `evidence_id` is not enough. CEO-resigned + `regime` cannot persist. | `claim_support.py`; `final_gate.py`; `test_er6_remediation.py`; live judgment `49ed5bf3-…` cites `claim:*` only |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — 3 assessment IDs, one regime `889d1f45-…` |
| ER3-P1-03 | remediating | Model availability is exact membership in `config/llm_model_capabilities.yaml` (production Responses `resolved_model`). No substring heuristics. Prompt candidates inject into the targeted role for all 8 roles. Eval records per-role `resolved_models`. attach/approve/freeze re-hash kept. | `governance-eval-v0.5`; `m06_replay.json` `executed_role_count: 8`; freeze `8632ca98-…` |

## Re-verify order

1. M03 — PASS (mock + live 8-role; QA+final PASS; judgment `49ed5bf3-…`)
2. M04 — PASS (that judgment; thesis UNASSESSED; 1M/3M/6M INCOMPLETE)
3. M05 — PASS (error `7d22c544-…` linked to the judgment)
4. M06 — PASS (8-role executed replay/holdout → attach → approve → freeze `llm-profile-v0.2`)

## Regression

- secret_scan PASS
- pytest 113 passed; unit 94 passed
- Next.js `npm run build` PASS
- `scheduler_enable_allowed: false`

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag.
