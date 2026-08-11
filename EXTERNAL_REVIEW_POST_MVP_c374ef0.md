# investing-insight Post-MVP External Review — c374ef0

- Review date: 2026-08-11
- Candidate: `c374ef0b8ce419cd9c342e6375eadc76ef7bc026`
- Branch: `post-mvp/phase-1`
- Claimed scope: G00 + M01–M06 ALL PASS
- Reviewer verdict: **NO-GO — remediation only**

## Positive controls confirmed

- MVP tags in bundle metadata remain `mvp-v0.1-pass -> e98ff33` and `mvp-v0.1-review-pass -> c1a6692`.
- Production cron examples are commented and API/CLI paths keep `scheduler_enable_allowed=false`.
- Long-Term Optional (entry/sell/sizing/broker) is not implemented.
- Bundle parses cleanly: 108 Python files AST-parse, 61 JSON files parse.
- Independent secret scan on the supplied source snapshot passed after creating a temporary local git index.
- Supplied verification logs record unit `53 passed` and Next build PASS. Fresh full integration was not re-run by the packager.

## Blocking findings

### ER-P0-01 — M03 mutates `snapshot_items` after `content_hash` is sealed

**Evidence**
- `apps/api/app/snapshot/engine.py` computes `content_hash`, inserts `snapshots`, then inserts the hashed base items.
- `apps/api/app/agents/binding.py` subsequently inserts `multiagent_union`, `multiagent_regime`, `multiagent_assessments`, and `multiagent_bottom_up` into the same `snapshot_items` table with the comment `post-hash` / `does not mutate content_hash`.
- Migration `0006_snapshots.sql` has no DB immutability trigger preventing post-freeze `snapshot_items` mutation.

**Why blocking**
The database contents represented as a Snapshot can diverge from the recorded content hash. Spec QA classifies corrupted snapshot as P0.

**Required remediation**
Choose one invariant and enforce it:
1. Include the frozen top-down/bottom-up context before computing the Snapshot hash, or
2. Keep multi-agent context outside `snapshot_items`, add an independent `context_hash`, and make the frozen context immutable.

Add a test proving post-freeze mutation is impossible/detected and same input/cutoff produces stable hashes.

### ER-P1-01 — M02 uses CPI index level as if it were an inflation percentage

**Evidence**
- `config/fred_series.v0.1.yaml`: `CPIAUCSL` assigned role `inflation`.
- `FredClient.get_observations()` requests the series without a FRED units transformation.
- `topdown/engine.py`: `delta = clamp((val - 2.0) * 3, ...)` treats `val` as a percentage around a 2% target.
- Unit test itself uses `CPIAUCSL value=300.0`, but only checks score bounds.

**Impact**
The pricing dimension receives a saturated positive tilt from a CPI index level, so industry attractiveness and candidate promotion can be biased.

**Required remediation**
Normalize CPI to a defined inflation rate (e.g. YoY percent) before scoring, persist/validate the unit/transformation, add semantic unit tests, then re-run live M02 and all downstream frozen contexts.

### ER-P1-02 — M03 Research QA is not actually evidence-grounded

**Evidence**
- `research_qa_agent` receives the research output and `allowed_evidence_refs` copied from the research output itself.
- It does not receive the underlying evidence objects/content needed to determine whether evidence supports each claim.
- No deterministic validator checks that a claim's `evidence_id` exists in the frozen Snapshot/source set.
- `company_agent` receives ticker/union member + industry output but no financial/price/quant research packet.
- `event_agent` receives company output but no actual filings/event records.
- Dedicated agent prompt files are absent; `_system_prompt()` falls back to generic role text.
- M03 PASS evidence is mock-only; live 8-role execution remains listed P2.

**Why blocking**
The spec requires evidence grounding, numeric claim match, unsupported claim rejection, and role-minimal inputs that still contain the facts necessary for the role. A schema-valid mock proves orchestration shape, not research correctness.

**Required remediation**
- Build role packets from actual Snapshot evidence / company Research Packet.
- Give Event actual filing/event evidence.
- Give QA claim + real evidence contents and deterministic allowed-evidence validation.
- Reject unknown evidence IDs before LLM QA.
- Add role-specific prompts/contracts.
- Run one real OpenAI 8-role candidate path and persist requested/resolved model, hashes, gates and final output.

### ER-P1-03 — M04 does not track M03 Final Selector decisions

**Evidence**
- M03 final selector is persisted only in `agent_outputs`.
- M04 `evaluate_run()` / `evaluate_judgment_horizons()` reads only the legacy `judgments` table.
- No code projects a PASSed multi-agent final selector output into an immutable judgment or directly into the performance cohort.

**Impact**
The performance system can evaluate older MVP judgments while ignoring the decisions produced by the new Multi-Agent system. Therefore M03 -> M04 is not an end-to-end connected roadmap.

**Required remediation**
Define the authoritative decision record. Prefer projecting a gate-passed Final Selector result into a versioned immutable judgment record with `multi_agent_run_id` lineage, then make M04 track that record.

### ER-P1-04 — M04 conflates price outcome with thesis correctness and permits historical as-of leakage

**Evidence**
- `performance/metrics.py`: SELECTED + positive return => `supported`; SELECTED + negative return => `challenged`.
- This makes `thesis_correctness` a direct function of price direction despite the roadmap requiring thesis correctness vs price outcome to be separate.
- `evaluate_judgment_horizons(as_of_date=...)` loads all `daily_prices`; `as_of_date` does not cap eligible exit bars. Historical replay can therefore use prices after the requested as-of date.
- Sector benchmark is explicitly deferred even though the roadmap lists SPY/QQQ/sector benchmark.

**Required remediation**
- Keep `price_outcome` purely price-based.
- Evaluate thesis correctness from observable thesis drivers/invalidation conditions; until evidence exists, store `UNASSESSED/INCONCLUSIVE` rather than infer from return sign.
- Restrict all evaluation prices to `<= as_of_date`.
- Add leakage tests and implement/explicitly re-scope sector benchmark requirement.

### ER-P1-05 — M06 does not implement replay/holdout governance; it only requires free-text notes

**Evidence**
- `approve_proposal()` only checks that `replay_notes` and `holdout_notes` strings are non-empty.
- M06's own `OPEN_ISSUES.md` states replay/holdout automation harness is not built.
- There is no machine-verifiable replay result, holdout result, dataset/snapshot IDs, metric comparison, or PASS gate tied to approval.

**Why blocking**
Roadmap M06 explicitly requires replay test + holdout + approval log + version freeze. Notes-only approval can freeze an untested rule/model/profile change.

**Required remediation**
Persist replay/holdout evaluation artifacts and IDs, require both to have an approved PASS state before `approve`/`freeze`, and add negative tests showing notes alone cannot pass governance.

## Non-blocking / audit findings

### ER-P2-01 — M01 "Deployment" is packaging, not hosted deployment
The current policy intentionally keeps production schedulers disabled, which is acceptable. However roadmap M01 says hosted PC Web deployment while the acceptance criterion was weakened to Docker/compose/runbook packaging. Either explicitly amend/re-scope the roadmap or produce hosted-deploy evidence before claiming M01 literally complete.

### ER-P2-02 — Review candidate working tree was not clean
`git/status.txt` records modified tracked evidence files and untracked delivery/review files at packaging time. Before a final Post-MVP tag, create a clean committed review candidate and generate the bundle from that exact commit.

### ER-P2-03 — Fresh full integration suite missing in packaging verification
The bundle records unit 53 PASS and web build PASS, but the packager did not freshly rerun the full DB integration suite because its Supabase connection timed out. After remediation, run the full suite with a working DB and attach raw output.

## Milestone disposition

- G00: structurally acceptable.
- M01: operational scaffolding acceptable under current cron-disabled policy; literal hosted-deploy requirement remains re-scope/evidence item.
- M02: **REOPEN** due CPI semantic/unit bug.
- M03: **REOPEN** due Snapshot integrity + evidence-grounding/live-path gaps.
- M04: **REOPEN** due M03 disconnect + thesis/price conflation + as-of leakage.
- M05: implementation can remain, but final PASS depends on corrected M04 lineage/results.
- M06: **REOPEN** due missing actual replay/holdout gate.

## Final verdict

**NO-GO for "Post-MVP roadmap complete".**

Do not start Long-Term Optional and do not create a Post-MVP PASS tag yet. Freeze feature expansion and perform remediation only. After fixes, rerun M02 -> M03 -> M04 -> M05 linkage -> M06 governance, full regression, secret scan, web build, and request external re-review.
