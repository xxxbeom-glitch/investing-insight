# PLAN — ER11 P1-01 structural grounding

- layer_id: ER11 (post-mvp remediation, not an MVP layer)
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-11
- status: IMPLEMENTED (await re-review; not GO)
- previous_layer_commit: `2422556` (ER10 candidate)
- prior_nogo: `2c5b107` (ER9 reverse-pair); ER10 copula-connector still English-pattern

## Goal

Stop verifying free-text claims with token-bag + sentence-pattern. At the **verification** stage, parse each claim into `field / operator / value` and admit SUPPORTED only when those triples match cited factual payload leaves.

## Flow (unchanged wiring)

```
research_agent.claims[i] {claim, evidence_id}
  → research_qa_agent.claim_verdicts (LLM; not authoritative)
  → evaluate_research_qa_gate: deterministic_claim_verdicts overrides QA
  → approved_claim_catalog: claim_is_supported AND QA SUPPORTED
  → final_selector sees approved_claims IDs only
  → materialize from catalog
```

Schema stays `{claim, evidence_id}` string. LLM is not trusted to emit triples. Structure is recovered deterministically from text × cited inventory.

## Design (chosen)

1. **Inventory** from `factual_payload` leaves only (wrapper/`*_id` skipped). Each leaf is `(field, equals, value)`.
2. **Span match** (longest, non-overlapping) of known field phrases and known values (exact string / numeric `_norm` / whole dates). Not a copula list.
3. **Bind**: every mentioned field must be bound to **that leaf's** value present in the claim. Unique extra values may infer their owning field (qualifier). Operator is always `equals` (copulas are stopwords, not syntax).
4. **Leftover** Unicode/open-class tokens FAIL. Field-name tokens of the cited item may be scaffolding (`score` in `demand score of 81.32`). Payload token-bag subset is **never** sufficient.
5. QA SUPPORTED cannot bypass deterministic FAIL (existing gate).

Not chosen: adding `was|were|are` to `_CONN_RE`; changing research JSON schema this round.

## In Scope

- `apps/api/app/agents/claim_support.py` rewrite of support check
- regression + generalized attack tests
- prompts: one-line “restate field/value only” (live claim shape)
- M03→M06 evidence + external rereview bundle

## Out of Scope

- `bind_union_lineage` / ER3-P1-02
- production cron, Long-Term Optional, Post-MVP tag, GO

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | `regime is expansion` → triple field=regime operator=equals value=expansion and SUPPORTED | yes |
| AC-2 | Copula variants (`was/were/are/is/:`) of a true pair stay SUPPORTED; of a false pair stay FAIL | yes |
| AC-3 | Reverse false pairs FAIL (`expansion is as_of`, `100.5 is trading_date`, …) | yes |
| AC-4 | Cross-mix, Unicode leftover, `X`, wrapper/meta, novel prose FAIL | yes |
| AC-5 | Existing PASS fixtures (ER6–ER10) still PASS | yes |
| AC-6 | QA lie cannot enter catalog/judgment | yes |
| AC-7 | P1-02 closed; cron DISABLED; no Post-MVP tag | yes |

## Expected Files

- `apps/api/app/agents/claim_support.py`
- `tests/unit/test_er11_remediation.py`
- `audit/post-mvp/_remediation_er11_2422556/*`

## Tests to Write First

- structural parse of true pairs (both orientations, copula variants)
- generalized attacks listed above
- catalog/QA/final_selector block on QA lie

## Risks

- Live research_agent prose may FAIL leftover check (prompt: field/value restatement only)
- Date/datetime prefix matching must not treat `2026` as `2026-08-10`
