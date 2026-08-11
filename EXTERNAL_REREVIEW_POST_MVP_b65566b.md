# investing-insight — External Re-review Post-MVP `b65566b`

## Review scope

- Candidate: `b65566b629bf3b8b88d6b816eba747cef5b3ad8c`
- Remediation content commit: `6ed8dc5cb9bc2df628b7e65c0b20c6229b95d086`
- Prior NO-GO: `e0f4672`
- Branch: `post-mvp/phase-1`
- Bundle: clean `git archive` source snapshot plus audit/evidence/verification
- Production cron: DISABLED
- Long-Term Optional: NOT STARTED

Reviewed source, migrations, configs/schemas, evidence, audit/handoff and verification outputs.
Independent checks performed in reviewer environment:
- ZIP integrity: PASS
- Python compileall: PASS
- source-level review of M03/M06 remediation paths
- direct synthetic execution of current `final_selector` gate logic: unsupported non-numeric factual claims passed
- submitted regression evidence inspected: pytest 84 PASS, unit 65 PASS, secret_scan PASS, Next build PASS
- full test suite could not be independently run because reviewer environment lacks project psycopg/Supabase runtime dependencies/credentials

## Verdict

**NO-GO — remediation only.**

ER2-P0-01 and ER2-P1-01 are materially closed. ER2-P1-02 is only partially closed, and M06's new evaluator has provenance but does not actually evaluate the candidate artifact/version being governed. A separate M03 lineage issue was also found in the frozen top-down context construction.

Do not create a Post-MVP PASS tag and do not enable production cron.

---

## ER2 finding disposition

| Finding | Result | Notes |
|---|---|---|
| ER2-P0-01 frozen_context immutability | **PASS** | DB trigger blocks immutable lineage/context mutation and DELETE; read-time `context_hash` verification exists; negative integration test exists |
| ER2-P1-01 Quant frozen-run binding | **PASS** | exact `(run_id, security_id)` lookup; no UUID-desc borrowing; bound quant records are included before `context_hash` |
| ER2-P1-02 Final Selector deterministic gate | **PARTIAL — P1 remains** | unknown refs / SELECTED empty risk arrays / unsupported numbers are blocked, but unsupported **non-numeric factual claims** still pass |
| ER2-P1-03 replay/holdout evaluator provenance | **PARTIAL — P1 remains** | DB-recorded evaluator + output hash exists and hand-authored PASS JSON is rejected, but evaluator ignores the candidate LLM/profile/prompt/rule artifact and scores unrelated M02 macro/industry logic |

---

# Blocking findings

## ER3-P1-01 — Final Selector gate does not enforce semantic evidence grounding

`app/agents/final_gate.py` now checks:
- evidence refs belong to `allowed_evidence_ids`
- SELECTED has non-empty bear/risk/invalidation/evidence arrays
- unsupported **numeric** claims in `rationale`

However it does not prove that free-text factual claims are actually supported by the referenced evidence, and it does not restrict the Final Selector to QA-approved research claims.

Reviewer independently exercised the current gate with a synthetic SELECTED output containing fabricated non-numeric claims such as:
- "Microsoft lost a major cloud contract"
- "Microsoft is insolvent"
- "The CEO resigned unexpectedly"

while citing only `regime` evidence. Current gate returned:

`('PASS', [])`

Therefore the Final Selector can still create a new unsupported factual thesis after Research QA and Adversarial QA have passed.

### Required remediation

Use one of these fail-closed designs:

1. Preferred: make Final Selector output reference immutable IDs of QA-approved research claims / adversarial findings rather than introducing free-form factual statements; or
2. add per-claim evidence mapping for final rationale/bear/risks/invalidation and deterministically validate every referenced claim against the frozen evidence/approved claim set.

At minimum add negative tests proving a new non-numeric factual claim cannot reach judgment persistence.

Severity: **P1**.

---

## ER3-P1-02 — M03 frozen top-down lineage is not tied to the selected union's exact assessment/regime set

`app/agents/binding.py::_load_frozen_context()` selects:
- the latest `shortlist_unions` row,
- then independently the latest `market_regimes` row,
- then independently the latest assessment for each industry using `distinct on (industry_id) ... order by created_at desc`.

But `shortlist_unions` already stores `topdown_assessment_ids`, and each industry assessment carries a `regime_id`. `_load_frozen_context()` does not load the union's exact assessment IDs and does not derive the regime from those exact assessments.

This creates a race/lineage hole: if a new top-down run writes newer regime/assessment rows after a union was created but before M03 binds, the frozen context can combine one union with another run's regime/assessments. The context is then perfectly immutable — but it is the wrong mixed context.

### Required remediation

- load `topdown_assessment_ids` from the selected union
- load exactly those assessment rows, not latest-per-industry rows
- require their `regime_id` lineage to be consistent and load that exact regime
- fail closed if assessment IDs are missing, duplicated, or span inconsistent regime/as-of lineage
- include exact IDs/as-of in the frozen context hash
- add an integration/unit test with two top-down generations proving an older selected union cannot borrow newer assessments/regime

Severity: **P1**.

---

## ER3-P1-03 — M06 evaluator is recorded, but it does not evaluate the candidate artifact/version

The ER2 remediation successfully created `governance_evaluations`, `evaluation_id`, evaluator version, dataset hash, thresholds, status and output hash. `change_proposals` only trusts DB-recorded PASS evaluations, so hand-authored PASS JSON is correctly rejected.

However `app/governance/evaluator.py` does not use the proposed artifact itself when computing replay/holdout results.

For the submitted evidence:
- `artifact_type = llm_profile`
- `artifact_ref = llm_profiles`
- `candidate_version = v0.2-er2`

but both evaluator paths only call macro regime + `score_industry()` from M02. They never:
- load the candidate LLM profile,
- compare it with the current/baseline profile,
- replay frozen research packets through the candidate profile,
- execute any LLM/model/prompt/quant artifact under change,
- or otherwise make the candidate artifact affect the metrics.

`artifact_type`, `artifact_ref`, and `candidate_version` are effectively labels persisted onto an unrelated industry-score evaluation.

As a result, an arbitrary or broken LLM profile could still receive replay/holdout PASS as long as the unrelated M02 industry scoring remains within thresholds.

The submitted replay evidence is especially telling: current M02 scores are simply recomputed against stored M02 scores, yielding exact `abs_delta: 0.0`; this does not validate an LLM profile change.

### Required remediation

Governance evaluator must be artifact-aware.

Examples:
- `llm_profile` / `model` / `prompt`: replay a fixed set of frozen historical Research Packets/Snapshots under baseline and candidate profiles; evaluate schema pass, evidence-grounding gate rates, decision stability/change rate, QA/adversarial/final-gate outcomes, cost/token metrics as applicable.
- `quant_rule` / `score_rule`: replay the candidate quant/scoring rule on fixed historical snapshots and compare ranking/score/selection deltas against explicit thresholds.

Holdout must use a dataset not used to tune/select the candidate and must compute acceptance metrics from the candidate artifact, not merely check that unrelated scores lie in 0–100.

The evaluator record should bind to a content hash of the actual candidate artifact/config, not just a free-text version label.

Add a negative test proving that a deliberately invalid candidate artifact fails even when M02 macro/industry scores are unchanged.

Severity: **P1**.

---

# Passed items

## ER2-P0-01 — frozen context immutability

PASS.

Migration `0017_er2_remediation.sql`:
- blocks UPDATE of frozen context/lineage fields
- blocks DELETE of `multi_agent_runs`
- still allows operational status/completion fields to change

`verify_frozen_context()` recomputes the hash before role execution and fails closed on mismatch. Integration test attempts mutation and expects failure.

## ER2-P1-01 — Quant binding

PASS.

- frozen run ID comes from the union/bottom-up lineage
- exact `(security_id, run_id)` is queried
- absent record stays absent rather than borrowing another run
- `run_id`, security/ticker, rule version and input hash are carried in the Quant record
- Quant records are attached before the multi-agent context hash is computed

The submitted live run had `quant_n=0`, which is acceptable for a top-down candidate because the system correctly did not borrow an unrelated Quant row.

## M04/M05 regression lineage

PASS for prior findings.

- live M03 judgment `4e012869-...` is the object tracked by M04
- 1M/3M/6M are `INCOMPLETE` rather than fabricated
- thesis correctness remains `UNASSESSED`
- M05 error row links to the same judgment

## Operational controls

- production cron: DISABLED
- scheduler_enable_allowed: false
- Long-Term Optional: NOT STARTED
- post-MVP tag: not created

Submitted verification:
- pytest: **84 passed**
- unit: **65 passed**
- secret_scan: PASS
- web build: PASS

---

# Non-blocking hardening

## ER3-P2-01 — Governance freeze/evaluation rows are not DB-immutable

`change_proposals.status='frozen'` and `governance_evaluations` are protected by application logic but no DB trigger prevents direct UPDATE/DELETE. Given this project already uses DB immutability for judgments and frozen multi-agent context, consider applying the same pattern before production scheduling.

## ER3-P2-02 — Review bundle status capture is not clean, although the source archive is

`git/status.txt` records working-tree modifications/untracked review delivery files, while `REVIEW_BASELINE.txt` states the source bundle itself was generated from `git archive` of HEAD. This does not invalidate source review, but final handoff should clearly distinguish archive cleanliness from local working-tree status.

## ER3-P2-03 — FRED raw revision provenance remains weak

Prior review P2 remains: source hash should ultimately bind actual normalized/raw observations or provider revision/vintage data, not only request/count metadata, before unattended production scheduling.

---

# Final disposition

**NO-GO for Post-MVP phase completion/tagging.**

Allowed work only:
1. ER3-P1-01 final-selector semantic claim grounding
2. ER3-P1-02 exact union → assessment → regime lineage binding
3. ER3-P1-03 artifact-aware replay/holdout governance evaluator
4. regression + live M03 rerun + M04/M05 linkage + M06 rerun
5. clean evidence/handoff bundle and external re-review

Keep:
- Production cron **DISABLED**
- Long-Term Optional **NOT STARTED**
- existing MVP tags unchanged
- no Post-MVP PASS tag until external re-review clears P1
