# REMEDIATION HANDOFF — External Re-review NO-GO 4a5932d

- status: ER4 remediation complete (await re-review)
- baseline_nogo: `4a5932d` (`4a5932dc269e31b8dc4378385c616b46209851d1`)
- report: `EXTERNAL_REREVIEW_POST_MVP_4a5932d.md`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags (unchanged): peeled commits `mvp-v0.1-pass` → `e98ff33`, `mvp-v0.1-review-pass` → `c1a6692`. Annotated tag *objects* are `fffff6a0` / `229bbaec` — bundle `git/` records both so they are not confused.
- checkpoint: `f8bb09d` (report freeze)
- remediation_commit: `2981919` (`2981919159405814d9f4fc73e1107a8ef8f67b2c`)
- review_candidate: HANDOFF hash-fill tip on `post-mvp/phase-1` (bundle `git/HEAD_commit.txt` is SoT)

## Finding disposition

| ID | Result | Fix | Evidence |
|----|--------|-----|----------|
| ER3-P1-01 | remediating | Final Selector factual fields are claim IDs; server reconstructs text; free text must exact-normalize-match. Negation / uncited catalog claim / short new predicate FAIL. | `final_gate.py`; schema v0.2; `test_er4_remediation.py`; live judgment `150b9a2e-…` materialized from IDs |
| ER3-P1-02 | **closed (do not reopen)** | unchanged `bind_union_lineage` | `m03_lineage.json` — 3 assessment IDs, one regime `889d1f45-…` |
| ER3-P1-03 | remediating | `llm_profile`/`model`/`prompt` replay/holdout **execute** role path with candidate model; nonexistent model FAIL; attach/approve/freeze bind type/ref/version/hash; freeze re-hashes | `governance-eval-v0.3`; `m06_replay.json` `executed: true`; freeze `8bbdbfcc-…` |

## Re-verify order

1. M03 — PASS (mock + live 8-role; final_selector PASS; judgment `150b9a2e-…`)
2. M04 — PASS (that judgment; thesis UNASSESSED; 1M/3M/6M INCOMPLETE)
3. M05 — PASS (error `76dddc34-…` linked to the judgment)
4. M06 — PASS (executed replay/holdout → attach → approve → freeze `llm-profile-v0.2`)

## Regression

- secret_scan PASS
- pytest 103 passed; unit 84 passed
- Next.js `npm run build` PASS
- `scheduler_enable_allowed: false`

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag.
