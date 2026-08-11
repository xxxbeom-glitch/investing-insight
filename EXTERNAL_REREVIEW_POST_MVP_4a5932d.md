# investing-insight — External Re-review Post-MVP `4a5932d`

## Review scope

| Field | Reviewed value |
|---|---|
| Candidate | `4a5932dc269e31b8dc4378385c616b46209851d1` |
| Remediation content | `ff853f530a7808f7cff0b11cfe137503928f6f34` |
| Prior NO-GO | `b65566b` |
| Branch | `post-mvp/phase-1` |
| Scope | ER3-P1-01, ER3-P1-02, ER3-P1-03 |
| Production cron | DISABLED |
| Long-Term Optional | NOT STARTED |
| Post-MVP tag | not created |

The submitted ZIP was inspected as a clean source archive plus evidence/verification metadata. Independent reviewer checks included ZIP integrity, Python `compileall`, direct execution of the current Final Selector gate against adversarial non-numeric cases, direct execution of the current governance evaluator against a syntactically valid but nonexistent model profile, source-level governance proposal/evaluation binding review, and consistency checks on the M03→M06 evidence.

## Verdict

**NO-GO — remediation only.**

ER3-P1-02 is closed. ER3-P1-01 and ER3-P1-03 remain open. P0 remains 0.

Do not create a Post-MVP PASS tag and do not enable production cron.

## ER3 finding disposition

| Finding | Result | Reviewer conclusion |
|---|---|---|
| ER3-P1-01 Final Selector factual grounding | **FAIL — P1 remains** | `claim_refs` are present, but free-text factual output is still accepted by a token allowlist that is not bound to the cited claim IDs and is not semantic fail-closed |
| ER3-P1-02 exact union → assessment → regime lineage | **PASS** | exact `topdown_assessment_ids` are loaded; duplicate/missing/inconsistent regime/as-of lineage fails closed; live evidence shows the same three assessment IDs and one regime |
| ER3-P1-03 artifact-aware replay/holdout | **FAIL — P1 remains** | candidate file is loaded/hashed, but an `llm_profile` is not executed in replay/holdout; governance also does not bind attached PASS evaluations to the proposal's artifact/version |

# Blocking finding 1 — ER3-P1-01 remains open

`apps/api/app/agents/final_gate.py` validates that `claim_refs` exist in the catalog, but lines 175–186 create an allowed token set from **all** approved catalog text plus cited evidence. The actual Final Selector text is then checked only for “significant” leftover tokens.

This does not make the free-text output equivalent to the cited immutable claims. The gate does not require each rationale/risk/bear/invalidation sentence to map to its cited `claim_ref`, and short words/meta vocabulary can change meaning without introducing a blocked token.

Independent direct execution of the submitted gate returned:

```text
negated_approved_claim ('PASS', [])
uncited_catalog_claim ('PASS', [])
short_new_fact ('PASS', [])
```

The tested cases included a QA-approved claim `regime is expansion` while the Final Selector emitted `regime is not expansion`, cited only `claim:0`, and still passed. A Final Selector output using `policy risk` while citing another claim also passed because the token corpus is built from the entire catalog. `regime may crash` likewise passed because the new short tokens are not considered significant.

The submitted negative test `test_fabricated_nonnumeric_claim_cannot_reach_pass` catches long deny-list words such as `insolvent` and `resigned`, but it does not cover semantic negation, uncited catalog claims, or short fabricated predicates.

### Required remediation

Use the preferred fail-closed design literally: factual content in the Final Selector should be represented by immutable IDs, not re-authored free text. The safest implementation is to make rationale/bear/risks/invalidation reference approved claim/finding IDs and derive the displayed text server-side from the frozen catalog. If free text must remain for presentation, it should be non-authoritative and deterministically reconstructed or exact-normalized against the referenced IDs; a vocabulary/token allowlist is insufficient.

Add negative tests proving that all of the following fail before judgment persistence: negating an approved claim, using an approved-but-uncited claim, introducing a new short predicate/event, and citing `claim:0` while the factual sentence corresponds to another claim.

Severity: **P1**.

# Blocking finding 2 — ER3-P1-03 remains open

## A. The LLM profile is loaded and hashed, but it does not affect replay/holdout execution

`apps/api/app/governance/evaluator.py` now resolves the actual file and records `artifact_content_hash`, which is an improvement. However, for `llm_profile` / `model`, the candidate only goes through `_validate_llm_profile(loaded["parsed"])`. Acceptance then calls `_replay_gates(packets)` on hard-coded, already-produced Research/QA/Adversarial/Final outputs. The candidate profile is not passed to `_replay_gates`, no role is executed with its models/reasoning settings, and no baseline candidate comparison is performed.

Independent direct execution of the submitted evaluator with a schema-valid profile in which every role had:

```text
model: THIS_MODEL_DOES_NOT_EXIST
```

returned:

```text
replay  True  gate_pass_rate=1.0
holdout True  gate_pass_rate=1.0
```

This is possible because `RoleProfile.model` only requires a non-empty string. Therefore a candidate profile that cannot possibly run can still receive replay PASS and holdout PASS.

The submitted M06 evidence is internally hash-consistent, and replay/holdout packet IDs are disjoint. However its `baseline` is only the candidate artifact hash itself, not a behavioral comparator. The recorded gate PASS metrics are produced from fixed packet outputs, not from execution under `llm-profile-v0.2`.

## B. PASS evaluations are not bound to the proposal artifact/version

`apps/api/app/governance/proposals.py::attach_eval_artifacts()` loads replay/holdout records and then queries only the proposal `status`. It does not compare the evaluation's `artifact_type`, `artifact_ref`, `candidate_version`, or content hash with the proposal's `artifact_type`, `artifact_ref`, and `to_version`.

`approve_proposal()` likewise loads only status/log/evaluation IDs and never verifies artifact identity. `freeze_proposal()` checks only approved status plus replay/holdout PASS status.

A direct reviewer harness supplied recorded PASS evaluations for a `quant_rule` and attached them to a hypothetical LLM-profile proposal; the submitted function accepted them. This is a governance bypass even when every evaluation row is genuine and DB-recorded.

### Required remediation

For `llm_profile` / `model` / `prompt`, replay and holdout must execute the candidate artifact over frozen inputs so the candidate can change the measured outcome. At minimum, the selected model/profile/prompt must be used by the actual role execution path, exact model resolution must be verified, schema/gate outcomes must be recomputed, and candidate-vs-baseline metrics must be recorded. A nonexistent or unavailable model must fail.

At proposal attachment/approval/freeze, require replay and holdout to match the proposal on `artifact_type`, canonical `artifact_ref`, `candidate_version/to_version`, and candidate content hash. Replay and holdout must also match each other on candidate identity. Re-resolve/hash the candidate at freeze or otherwise pin an immutable artifact hash so post-evaluation mutation cannot be frozen under an old PASS.

Add negative tests proving that a schema-valid nonexistent model fails evaluation, a PASS evaluation for another artifact/version cannot be attached, replay and holdout for different content hashes cannot be paired, and an artifact changed after evaluation cannot be frozen.

Severity: **P1**.

# ER3-P1-02 — PASS

`bind_union_lineage()` now loads the union's exact `topdown_assessment_ids`, rejects missing/duplicate IDs, requires one shared `regime_id`, requires one shared assessment `as_of`, and requires the exact regime `as_of` to match. `_load_frozen_context()` queries only those assessment IDs and then loads the regime referenced by them.

The submitted `m03_lineage.json` shows three union assessment IDs, the same three bound assessment IDs, and one common regime ID `889d1f45-d030-4d79-9f7b-8a4dace27c6d`. The live M03 judgment is `5e1899ff-a984-4a09-a9c4-1ff56f63d140`, and the Final Selector gate is recorded PASS.

Disposition: **closed**.

# Regression and evidence assessment

| Check | Result |
|---|---|
| ZIP integrity | PASS |
| Python compileall | PASS |
| Submitted full pytest | 94 passed, 3 warnings |
| Submitted unit pytest | 75 passed |
| secret_scan | PASS |
| Next.js build | PASS |
| M03 live 8-role | PASS; judgment `5e1899ff-…` |
| M04 | 1M/3M/6M INCOMPLETE; thesis UNASSESSED |
| M05 | error `57293274-…` linked to same judgment |
| M06 record/output hashes | internally consistent |
| production cron | DISABLED |
| scheduler_enable_allowed | false |
| Long-Term Optional | NOT STARTED |

# Non-blocking bundle/provenance cleanup

The bundle contains conflicting MVP tag metadata. `README.md`, active-track, and remediation handoff state `mvp-v0.1-pass @ e98ff33` and `mvp-v0.1-review-pass @ c1a6692`, while `git/tag_mvp-v0.1-pass_commit.txt`, `git/tag_mvp-v0.1-review-pass_commit.txt`, and `git/REVIEW_BASELINE.txt` record `fffff6a0` and `229bbaec`. Reconcile this before a final PASS handoff; the bundle cannot currently prove which tag targets are authoritative.

`git/status.txt` also records `post-mvp/phase-1...origin/post-mvp/phase-1 [ahead 3]`. The source archive itself is clean, but the submitted bundle does not prove the candidate was pushed at capture time. If it was pushed after bundle creation, regenerate the final re-review metadata from the pushed state.

These are **P2 / provenance cleanup** items and are not the reason for the current NO-GO.

# Final disposition

**NO-GO for Post-MVP completion/tagging.**

Required next scope is limited to closing ER3-P1-01 and ER3-P1-03, rerunning the affected M03/M06 negative/positive paths plus full regression, regenerating a consistent review bundle, and returning for external re-review. Keep production cron DISABLED, Long-Term Optional NOT STARTED, and Post-MVP tag absent.
