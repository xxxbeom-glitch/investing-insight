# IMPLEMENTATION — ER11 P1-01 structural grounding

- layer_id: ER11
- status: IMPLEMENTED
- commit_hash: (filled after content commit)
- previous_layer_commit: `2422556`

## What Changed

Verification no longer treats claim support as token-bag ⊂ payload plus copula regex. `claim_support.parse_claim` recovers `field / operator=equals / value` triples from the claim text against the cited **factual inventory**, then admits SUPPORTED only when every mentioned field is bound to that leaf's value and leftover open-class tokens are empty.

Copulas (`is/was/were/are/:`) are stopwords, not syntax. Wrapper/`*_id` keys remain non-facts. QA SUPPORTED still cannot bypass deterministic FAIL.

## Files Changed

- `apps/api/app/agents/claim_support.py`
- `tests/unit/test_er11_remediation.py`
- `config/prompts/agents/research_agent.v0.1.txt`
- `config/prompts/agents/research_qa_agent.v0.1.txt`
- `agent/TASK_CONTRACT.md`
- `_docs/active-track.md`
- `audit/post-mvp/_remediation_er11_2422556/`

Unchanged: `apps/api/app/agents/binding.py` (`bind_union_lineage`)

## Commands Run

- `pytest tests/unit` → 183 passed
- `pytest tests` → 202 passed
- `scripts/secret_scan.py` → PASS
- `npm run build` (apps/web) → PASS
- `scripts/run_multi_agent.py --mock` → judgment `d91e0ee5-…`
- `scripts/run_multi_agent.py --live` → judgment `9ea3b045-…`; gates research_qa/adversarial/final_selector PASS
- M04–M06 capture → freeze `6c12334b-…` 8-role

## Deviations from PLAN

None. Schema still `{claim, evidence_id}`; triples are verification-only.

## Notes

Production cron DISABLED. Long-Term Optional NOT STARTED. No Post-MVP tag.
