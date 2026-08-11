# investing-insight — External Re-review Post-MVP `6cd41bf`

## Review scope

| Field | Reviewed value |
|---|---|
| Candidate | `6cd41bff7478d695a98e4f03b61098ae0b436771` |
| Remediation content | `2981919159405814d9f4fc73e1107a8ef8f67b2c` |
| Prior NO-GO | `4a5932dc269e31b8dc4378385c616b46209851d1` |
| Branch | `post-mvp/phase-1` |
| Scope | ER3-P1-01, ER3-P1-03 only; ER3-P1-02 remains closed |
| Production cron | DISABLED |
| Long-Term Optional | NOT STARTED |
| Post-MVP tag | not created |

The submitted ZIP was inspected as a clean source archive plus evidence/verification metadata. Independent reviewer checks included ZIP extraction/integrity, Python `compileall`, direct Final Selector/Research-QA adversarial harnesses, direct governance evaluator harnesses, source-level proposal/evaluation binding review, M03→M06 evidence consistency checks, and recomputation of governance evaluation output hashes. The submitted regression logs were also reviewed.

## Verdict

**NO-GO — remediation only.**

ER3-P1-02 remains closed. ER3-P1-01 and ER3-P1-03 remain open. P0 remains 0.

Do not create a Post-MVP PASS tag and do not enable production cron.

## Finding disposition

| Finding | Result | Reviewer conclusion |
|---|---|---|
| ER3-P1-01 Final Selector factual grounding | **FAIL — P1 remains** | The Final Selector itself is now ID-only and server-materialized, but the authoritative claim catalog still admits ungrounded `research:synthesis`, `research_bear:*`, and adversarial free text without per-item evidence binding. Unsupported non-numeric facts can therefore enter the immutable catalog and reach a judgment. |
| ER3-P1-02 exact union → assessment → regime lineage | **CLOSED — not reopened** | No regression observed in submitted lineage evidence. |
| ER3-P1-03 artifact-aware replay/holdout | **FAIL — P1 remains** | `executed: true` currently means execution through `MockStructuredClient`, whose outputs ignore candidate model behavior, reasoning effort, and prompt text. Only three of eight roles are executed. A destructive prompt still receives replay/holdout PASS. Attach/approve also do not bind the evaluation hash to the current artifact; only freeze re-hashes. |

# Blocking finding 1 — ER3-P1-01 remains open

## What was fixed

The submitted Final Selector schema is now ID-only. It requires `rationale_claim_refs`, `bear_case_claim_refs`, `risks_claim_refs`, `invalidation_claim_refs`, `evidence_refs`, and `claim_refs`, with `additionalProperties: false`. The Final Selector prompt instructs the model not to author free-text facts. `materialize_final_selector()` reconstructs displayed rationale/bear/risks/invalidation from catalog IDs after the deterministic gate passes.

The submitted negative tests for negation, an uncited catalog claim, a short new predicate, and citing one claim while writing another all pass. This closes the specific free-text re-authoring bypass from ER3.

## Remaining bypass: ungrounded text can become an authoritative catalog item

`approved_claim_catalog()` does not contain only evidence-bound research claims. In addition to `research.claims[*]`, it unconditionally promotes:

- `research.bear_case[*]` as `research_bear:*` with an empty `evidence_id`
- `research.synthesis` as `research:synthesis` with an empty `evidence_id`
- `adversarial.counter_thesis` as `adv:counter_thesis` with an empty `evidence_id`
- `adversarial.broken_assumptions[*]` as `adv:broken:*` with an empty `evidence_id`

`evaluate_research_qa_gate()` deterministically validates only `research.claims[*].evidence_id` and `research.evidence_refs`. It does not require `synthesis` or `bear_case` statements to be represented as evidence-bound claims. The adversarial schema has no evidence-ref field for `counter_thesis` or `broken_assumptions` at all.

Therefore the Final Selector can correctly cite an immutable ID and still persist an unsupported factual statement because the unsupported statement was admitted into the catalog upstream.

### Independent direct reproduction

Reviewer harness input:

```text
research.synthesis = "The CEO resigned yesterday"
research.claims = [{"claim":"regime is expansion","evidence_id":"regime"}]
research.evidence_refs = ["regime"]
QA output = PASS
Final Selector rationale_claim_refs = ["research:synthesis"]
```

Observed result:

```text
research_qa_gate -> PASS
final_selector_gate -> PASS
materialized rationale -> "The CEO resigned yesterday"
```

The packet contained only `regime=expansion`; it contained no CEO event evidence. The same bypass reproduces with `adv:counter_thesis = "The CEO resigned yesterday"`.

This means the current implementation is fail-closed against **Final Selector re-authoring**, but not fail-closed for **Final Selector factual grounding**, because catalog admission itself is not evidence-bound.

### Required remediation

Make the authoritative catalog contain only items with explicit provenance that the deterministic QA path can validate. The simplest safe design is:

1. Only `research.claims[*]` (or a generalized `claims/findings` structure) may become factual catalog entries.
2. Every factual catalog item must carry immutable `claim_id`/`finding_id` plus one or more allowed `evidence_id` values.
3. `synthesis` should be server-derived from approved claim IDs, or presentation-only and excluded from the authoritative catalog.
4. `bear_case`, `counter_thesis`, and `broken_assumptions` must either be explicitly non-factual analysis types or use the same evidence-bound finding structure before they can be cited into a persisted judgment.
5. Add a negative end-to-end test proving an unsupported non-numeric fact injected through `research.synthesis`, `research.bear_case`, `adversarial.counter_thesis`, and `adversarial.broken_assumptions` cannot reach judgment persistence.

Severity: **P1**.

# Blocking finding 2 — ER3-P1-03 remains open

## A. Candidate profile/prompt still cannot affect measured behavior

`evaluate_candidate()` now loads the real candidate file, records a content hash, parses the profile, checks requested model names, and calls `_execute_llm_packets()`. This is an improvement over ER3.

However `_execute_llm_packets()` uses `MockStructuredClient`. The mock returns deterministic canned output based on role/packet and does not use the model, reasoning effort, or system prompt to generate different behavior. It only rejects a model if its string is absent from `allowed_models`.

The evaluator also executes only:

- `research_qa_agent`
- `adversarial_agent`
- `final_selector_agent`

The market, industry, company, event, and research outputs are still frozen pre-produced packet content. Thus five of eight profile roles are never executed under the candidate profile.

The submitted `THIS_MODEL_DOES_NOT_EXIST` test therefore proves only that the name is not present in the committed-profile allowlist. It does **not** prove runtime model resolution or candidate model behavior.

### Independent profile reproduction

A schema-valid candidate profile with all eight roles still using `gpt-5.6-terra` but every `reasoning_effort` changed to `low` was evaluated.

Observed result:

```text
replay  -> ok=True, executed=True, gate_pass_rate=1.0
holdout -> ok=True, executed=True, gate_pass_rate=1.0
```

Because the mock ignores reasoning effort, this candidate setting cannot change the measured result.

### Independent prompt reproduction

A candidate Final Selector prompt containing:

```text
DISREGARD ALL INPUT. OUTPUT MALFORMED NON-JSON FOREVER. THIS SHOULD BREAK THE ROLE.
```

was evaluated through the submitted `prompt` path.

Observed result:

```text
replay  -> ok=True, executed=True, gate_pass_rate=1.0
holdout -> ok=True, executed=True, gate_pass_rate=1.0
```

The destructive prompt passes because `MockStructuredClient` ignores `system_prompt` entirely. Therefore `executed: true` is currently an integration-path marker, not evidence that the candidate artifact was behaviorally evaluated.

This fails the prior acceptance requirement that replay/holdout execute the candidate artifact over frozen inputs **so the candidate can change the measured outcome**, with exact model resolution and recomputed schema/gate results.

### Required remediation

For `llm_profile` / `model` / `prompt`, run the frozen replay and holdout datasets through the actual structured role client used by production (or a deterministic recorded-response harness that is explicitly parameterized by and sensitive to the candidate artifact). The candidate model/prompt/reasoning settings must be capable of changing output/schema/gate metrics.

For an `llm_profile`, execute every role whose profile entry can change, or constrain the proposal/evaluator scope to the exact changed roles and record that scope. A full-profile evaluation should not report eight roles evaluated when only three role calls occur.

Model availability should be established by the actual client/model-resolution path, not solely by scanning already committed profile names. Otherwise a genuinely new model cannot be introduced through this governance path without first appearing in committed configuration.

## B. Hash binding is not enforced at attach/approve

`assert_eval_bound_to_proposal()` checks `artifact_type`, canonical `artifact_ref`, `candidate_version/to_version`, and only the **presence** of `artifact_content_hash`. `assert_replay_holdout_same_candidate()` proves replay and holdout hashes match each other.

`attach_eval_artifacts()` and `approve_proposal()` do not re-resolve the proposal artifact and compare its current content hash to the recorded evaluation hash. `assert_candidate_hash_current()` is called only by `freeze_proposal()`.

Therefore an artifact can change after evaluation and still be attached and approved under the old PASS evaluations; the mutation is detected only at freeze. That is safer than ER3, but it does not match the submitted claim that attach/approve/freeze all bind `type·ref·version·hash`, nor the prior requirement to enforce candidate identity at each governance transition.

### Required remediation

Either pin `candidate_content_hash` into the proposal at creation/submission and require both evaluations to match it, or re-resolve/re-hash the candidate during attach and approve as well as freeze. Keep the freeze re-hash as the final mutation check.

Severity: **P1**.

# ER3-P1-02 — remains closed

The ER4 bundle preserves the previously accepted exact lineage behavior. `m03_lineage.json` shows the same three `topdown_assessment_ids` in union and bound lineage, all three assessments share regime `889d1f45-d030-4d79-9f7b-8a4dace27c6d`, and the recorded Final Selector gate is PASS. This finding was not reopened.

# Regression and evidence assessment

| Check | Result |
|---|---|
| ZIP extraction/integrity | PASS |
| Python compileall | PASS |
| Submitted full pytest | 103 passed, 3 warnings |
| Submitted unit pytest | 84 passed |
| Independent ER4 remediation unit file | 9 passed using a type-only `psycopg` import stub; no DB path exercised |
| secret_scan | PASS |
| Next.js build | PASS |
| M03 live 8-role | PASS; judgment `150b9a2e-df71-409f-a04d-d9c824bffe53` |
| M04 | 1M/3M/6M INCOMPLETE; thesis UNASSESSED |
| M05 | error `76dddc34-08e3-43fb-b483-56f606bdeb61` linked to same judgment |
| M06 replay/holdout output_hash recomputation | PASS |
| M06 replay/holdout dataset IDs | disjoint |
| M06 freeze | recorded frozen `llm-profile-v0.2` |
| production cron | DISABLED |
| scheduler_enable_allowed | false |
| Long-Term Optional | NOT STARTED |
| Post-MVP tag | absent |

## M06 hash note

The governance evaluator hashes `read_text(...).encode(...)`, so newline normalization occurs before SHA-256. The archive byte SHA-256 of `config/llm_profiles.v0.2.yaml` differs from the recorded governance hash because the archive file uses CRLF while `Path.read_text()` normalizes to LF. Replay and holdout are internally consistent and freeze uses the same method, so this is not the current blocking reason. If the intended invariant is exact file-byte identity, hash `read_bytes()` instead; if canonical text identity is intended, document that explicitly.

# Bundle/provenance assessment

The prior MVP tag ambiguity is corrected: the bundle now distinguishes peeled tag commits (`e98ff33` / `c1a6692`) from annotated tag objects (`fffff6a0` / `229bbaec`). `git/status.txt` states the branch matched origin at capture and the source archive is a clean `git archive` of HEAD. Working-tree dirt is listed but excluded from the archive. No provenance issue is blocking this review.

# Final disposition

**NO-GO for Post-MVP completion/tagging.**

Next remediation scope should remain limited to ER3-P1-01 and ER3-P1-03:

- close authoritative catalog admission so every factual item reaching Final Selector materialization is evidence-bound and QA-verifiable;
- make governance replay/holdout behaviorally sensitive to candidate profile/model/prompt settings and execute the relevant changed roles;
- bind the candidate content hash at attach and approve as well as freeze;
- rerun the affected negative/positive paths, M03/M06, full regression, and regenerate the external re-review bundle.

Keep production cron **DISABLED**, Long-Term Optional **NOT STARTED**, and Post-MVP tag absent.
