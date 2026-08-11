# investing-insight — External Re-review Post-MVP `e0f4672`

## Review scope

- Candidate commit: `e0f4672f88394aa554a2f6d63a460a702a38c3b9`
- Branch: `post-mvp/phase-1`
- Prior NO-GO: `c374ef0`
- Bundle: `external-rereview-post-mvp-e0f4672.zip`
- Production cron: DISABLED
- Long-Term Optional: NOT STARTED

Reviewed source snapshot, migrations, configs/schemas, remediation evidence, audit files and verification outputs.
Independent static checks performed:
- Python compileall: PASS
- JSON schema/config parse: PASS
- `tests/unit/test_performance_tracking.py`: 5 PASS in reviewer environment
- submitted verification evidence: pytest 77 PASS, unit 59 PASS, secret_scan PASS, Next build PASS

## Verdict

**NO-GO — remediation only.**

M02 and M04 prior blockers are materially fixed. M03 and M06 still contain blocking integrity gaps. Do not create a Post-MVP completion tag and do not enable production cron.

---

## Prior finding disposition

| Prior finding | Re-review | Notes |
|---|---|---|
| ER-P0-01 Snapshot integrity | **PARTIAL / P0 remains** | `snapshot_items` seal fixed, but external `frozen_context` is not immutable |
| ER-P1-01 CPI semantics | **PASS** | CPIAUCSL uses FRED `units=pc1`, `value_unit=yoy_pct`, semantic guards/tests added |
| ER-P1-02 Evidence-grounded M03 | **PARTIAL / P1 remains** | real evidence bundle exists, but Quant lineage is not snapshot/run bound; final selector has no final evidence gate |
| ER-P1-03 M03→M04 lineage | **PASS** | Final Selector projects into immutable `judgments` with `multi_agent_run_id` lineage |
| ER-P1-04 Thesis/as-of leakage | **PASS** | thesis defaults `UNASSESSED`; price query and forward return cap to `<= as_of` |
| ER-P1-05 Replay/Holdout governance | **FAIL / P1 remains** | JSON PASS artifacts can be hand-authored; no evaluator provenance or actual replay/holdout harness is required |

---

# Blocking findings

## ER2-P0-01 — Multi-agent frozen context is hashed but not immutable

### What was fixed

Migration `0016_post_mvp_remediation.sql` correctly:
- adds `snapshots.sealed`
- blocks UPDATE/DELETE of `snapshot_items`
- blocks INSERT after snapshot seal
- moves multi-agent context outside `snapshot_items`
- adds `multi_agent_runs.context_hash`

This fixes the original post-hash `snapshot_items` mutation.

### Remaining issue

`multi_agent_runs.frozen_context` and `context_hash` remain ordinary mutable columns.

- `0012_multi_agent.sql`: `frozen_context jsonb not null`
- `0016_post_mvp_remediation.sql`: only `add column ... context_hash text`
- no trigger/check prevents later UPDATE of `frozen_context`, `context_hash`, `union_id`, `bottom_up_run_id`, `regime_id`, or `snapshot_id`
- no read-time verification recomputes `context_hash(frozen_context)` before agents use it

The prior remediation requirement explicitly required the out-of-Snapshot context to be independently hashed **and immutable**. Only the hash half is implemented.

### Required remediation

Enforce one of:
1. DB trigger preventing changes to immutable context/lineage columns after INSERT while allowing status/completed_at/block_reason updates; preferably also prevent DELETE, or
2. immutable context table referenced by `multi_agent_runs`.

Additionally:
- recompute/verify `context_hash` before role execution, or enforce it in DB
- add negative integration test: changing frozen_context after bind must fail
- add test that same frozen context produces same context_hash

Severity: **P0**, because altered frozen context can make an audited run's actual inputs diverge from its recorded hash/lineage.

---

## ER2-P1-01 — M03 Quant evidence is not bound to the frozen run/Snapshot

`app/agents/evidence.py` loads Quant using:

```sql
select ...
from quant_scores
where security_id=%s::uuid
order by run_id desc
limit 1
```

Problems:
- `run_id` is UUID, so descending UUID order is not chronological lineage.
- it is not constrained to `frozen_context.bottom_up.run_id`.
- it is not a `snapshot_item` and therefore is not covered by `snapshot.content_hash`.
- a top-down-only candidate can accidentally borrow a Quant score from an unrelated run.
- Quant evidence lacks explicit `run_id`, `security_id/ticker`, `rule_version`, and `input_hash` in the packet.

The submitted live MSFT final output itself noticed the consequence: it states the quantitative record lacks a ticker/company identifier and therefore cannot be attributed to MSFT.

### Required remediation

- Use the frozen `bottom_up_run_id` / exact Quant run lineage when available.
- If that exact run has no Quant record for the candidate, Quant must be absent rather than borrowed from another run.
- Include `run_id`, `security_id`, ticker, `rule_version`, `input_hash` with Quant evidence.
- Make Quant part of the frozen context hash or otherwise bind its exact record/hash into the multi-agent immutable input manifest.
- Add test with two Quant runs proving the frozen run's score is selected regardless of UUID/creation order.

Severity: **P1**.

---

## ER2-P1-02 — Final Selector can create an unchecked SELECTED judgment

Research QA and adversarial gates now exist, but there is no gate after the Final Selector.

Flow currently:

`Research QA PASS → Adversarial PASS → Final Selector → project_final_selector_to_judgment()`

`project_final_selector_to_judgment()` accepts the model's status/rationale/arrays and immediately inserts the judgment.

The Final Selector schema:
- requires arrays to exist but does not require them to be non-empty
- does not constrain `evidence_refs` to allowed evidence IDs
- there is no deterministic check that final rationale contains no new unsupported numeric/factual claims
- `SELECTED` does not require non-empty bear case, risks, invalidation conditions, or evidence refs

This weakens the existing project invariant that the final decision cannot introduce new unsupported facts and that a SELECTED result must carry risk/bear/invalidation evidence.

### Required remediation

Add deterministic `final_selector_gate` before judgment projection:
- every final `evidence_ref` must be in the frozen allowed set
- reject unsupported numeric facts/new claims, or restrict final rationale to QA-approved research claims
- SELECTED requires non-empty bear_case, risks, invalidation_conditions and evidence_refs
- gate FAIL must prevent judgment insertion/SELECTED
- persist the final gate result
- add negative tests for unknown evidence ref, empty SELECTED risk arrays, and new unsupported number

Severity: **P1**.

---

## ER2-P1-03 — M06 replay/holdout remains self-declared rather than actually evaluated

The governance storage/gate is improved: notes alone cannot approve and replay/holdout JSON objects must contain `status=PASS`, an ID and `metrics`.

However, `scripts/governance.py` simply loads arbitrary user-supplied JSON files and `_require_eval_pass()` trusts the `status` field.

Submitted artifacts are:

```json
{"status":"PASS","snapshot_id":"...","run_id":"...","metrics":{"n":1,"gate":"research_qa"}}
```

and

```json
{"status":"PASS","dataset_id":"lab-holdout-remediation","metrics":{"n":1,"thesis":"UNASSESSED"}}
```

There is no code in the bundle that executes a replay dataset or holdout dataset to produce these results. No evaluator version, evaluated artifact version, dataset hash, comparison baseline, threshold, output hash, or signed/derived provenance is required. Therefore a hand-authored JSON saying PASS is enough to freeze a version.

This does not satisfy the roadmap's actual `replay test + holdout + approval log + version freeze` control.

### Required remediation

- implement a deterministic replay/holdout evaluator command/service, or tightly bind governance to existing recorded evaluation jobs
- evaluator must produce the artifact itself rather than accept arbitrary PASS JSON as authority
- artifact should include at minimum:
  - evaluation_id
  - evaluator/rule version
  - candidate artifact/version
  - dataset/snapshot IDs + hash
  - sample count
  - metrics and baseline/comparator
  - acceptance thresholds
  - computed PASS/FAIL
  - generated_at / output hash
- governance should verify the DB-recorded evaluation ID/hash/status, not merely trust file fields
- negative test: manually authored `{"status":"PASS"...}` with no recorded evaluator run must be rejected

Severity: **P1**.

---

# Passed remediation

## M02 CPI

PASS. `fred_series.v0.2.yaml` requests `CPIAUCSL` with `units: pc1` and persists `value_unit: yoy_pct`. `score_industry()` rejects index-like values and semantic tests cover raw-index misuse.

## M04 lineage / thesis / as-of

PASS for the prior findings:
- M03 Final Selector result is projected to `judgments` with `multi_agent_run_id` lineage.
- Performance evaluation reads that judgment.
- `thesis_correctness` no longer infers thesis quality from price direction; default is `UNASSESSED`.
- `_load_prices()` and `forward_return()` cap observations to `<= as_of_date`.
- submitted remediation run tracks judgment `2fefdc00-...` and correctly returns INCOMPLETE rather than fabricating future returns.

## M05 structural linkage

The schema/API supports `judgment_id` and `performance_eval_id` linkage. The submitted `m05_error_link.json` does not itself expose the linked IDs, so this is accepted structurally but the review evidence could be stronger.

---

# Non-blocking findings

## ER2-P2-01 — Handoff review candidate metadata is stale

The bundle Git metadata correctly identifies review candidate `e0f4672`, but `REMEDIATION_HANDOFF.md` still says `review_candidate: 950582e`.

Update the handoff before final tagging.

## ER2-P2-02 — packaged Git status is not clean

`git/status.txt` shows:
- branch ahead of recorded origin by 4 commits
- one modified tracked web-server evidence log
- untracked review/delivery files

The source bundle itself is declared/generated from a clean `git archive` of HEAD, so this does not invalidate source review. Before final tag/handoff, make the repository state unambiguous and record the pushed candidate commit.

## ER2-P2-03 — FRED raw provenance is weak

`ingest_fred_series()` hashes/stores metadata (`series_id`, count, start, units, value_unit) rather than the returned observation values themselves. If FRED revises values without changing observation count, `raw_hash` can remain unchanged while DB values change.

Before production scheduling, include normalized/raw observation values (or provider response bytes/vintage metadata) in the source hash and preserve revision provenance.

---

# Regression/evidence assessment

Submitted evidence:
- secret_scan: PASS
- full pytest: **77 passed**, 3 warnings
- unit: **59 passed**
- web build: PASS
- cron remains DISABLED

Reviewer environment:
- Python source compile: PASS
- JSON schemas/YAML configs parse: PASS
- performance tracking unit tests: **5 passed**
- full suite could not be independently rerun because the reviewer environment does not contain the project's psycopg/Supabase runtime dependencies/credentials; submitted raw test output was inspected instead.

---

# Final disposition

**NO-GO for Post-MVP phase completion/tagging.**

Allowed work only:
1. ER2-P0-01 frozen context immutability
2. ER2-P1-01 Quant run/snapshot binding
3. ER2-P1-02 Final Selector deterministic gate
4. ER2-P1-03 real replay/holdout evaluator provenance
5. regression + live M03 re-run + M04/M05 linkage + M06 re-run
6. clean audit/handoff bundle and external re-review

Keep:
- production cron **DISABLED**
- Long-Term Optional **NOT STARTED**
- existing MVP tags unchanged

Do not create a Post-MVP PASS tag until external re-review clears P0/P1.
