# REMEDIATION HANDOFF — External Re-review NO-GO 6cd41bf

- status: ER5 remediation complete (await re-review)
- baseline_nogo: `6cd41bf` (`6cd41bff7478d695a98e4f03b61098ae0b436771`)
- report: `EXTERNAL_REREVIEW_POST_MVP_6cd41bf.md`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`. Annotated tag objects `fffff6a0` / `229bbaec`.
- checkpoint: `f8e219a` (report freeze)
- remediation_commit: (filled after PASS commit; bundle `git/HEAD_commit.txt` is SoT)
- review_candidate: HANDOFF hash-fill tip on `post-mvp/phase-1` (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Authoritative catalog is evidence-bound `research.claims[*]` only. synthesis / bear_case / adversarial free text cannot be cited into a judgment. | `final_gate.py`; `test_er5_remediation.py`; live judgment `20380d75-…` cites `claim:*` only |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — 3 assessment IDs, one regime `889d1f45-…` |
| ER3-P1-03 | remediating | Eval executes all 8 roles; mock/client is sensitive to model/effort/prompt (`resolve_requested_model`, sabotage → schema FAIL, low high-stakes effort → gate FAIL). attach/approve/freeze re-hash. Hash encoding is canonical UTF-8 text (newline-normalized). | `governance-eval-v0.4`; `m06_replay.json` `executed_role_count: 8`; freeze `900d4dc6-…` |

## Re-verify order

1. M03 — PASS (mock + live 8-role; final_selector PASS; judgment `20380d75-…`)
2. M04 — PASS (that judgment; thesis UNASSESSED; 1M/3M/6M INCOMPLETE)
3. M05 — PASS (error `7db58db6-…` linked to the judgment)
4. M06 — PASS (8-role executed replay/holdout → attach → approve → freeze `llm-profile-v0.2`)

## Regression

- secret_scan PASS
- pytest 108 passed; unit 89 passed
- Next.js `npm run build` PASS
- `scheduler_enable_allowed: false`

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag.
