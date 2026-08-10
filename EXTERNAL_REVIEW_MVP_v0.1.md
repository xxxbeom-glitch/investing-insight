# investing-insight MVP v0.1 External Review

- Review date: 2026-08-10
- Baseline tag: `mvp-v0.1-pass`
- Tag target commit (user-confirmed): `e98ff33`
- Prior freeze content commit: `67c9c2d`
- Spec: `investing-insight-spec-v1.6`
- Review scope: uploaded `audit.zip`, `MVP_HANDOFF.md`, `active-track.md`, `TASK_CONTRACT.md`, and v1.6 specification available in the review environment

## Verdict

**CONDITIONAL NO-GO for Post-MVP.**

Do not start Post-MVP. Reopen only the L10 closeout/acceptance-validation scope, resolve the blocking evidence gaps below, rerun regression, then request external re-review.

This is not a rejection of the architecture. The available audit evidence supports the intended fail-closed/immutable/deterministic design direction, but the current freeze package does not fully prove all v1.6 MVP exit conditions.

## Blocking Findings

### ER-P1-01 — Full NYSE/NASDAQ registry ingest not evidenced

Spec v1.6 L10 explicitly lists `full registry ingest` as an L10 run requirement, while the handoff says the MVP universe is a small lab fixture and not the full US registry.

Required remediation:
- Execute one full current NYSE/NASDAQ registry ingest using the implemented Universe rules.
- No full historical OHLCV backfill is required for this finding.
- Record counts: raw securities, NYSE, NASDAQ, included common stocks, ADRs, exclusions by reason, duplicates, unresolved identity/CIK mappings.
- Prove excluded-security leakage = 0 on the resulting registry QA rules, or document any actual exception as P0/P1/P2 according to the spec.

### ER-P1-02 — Representative live Research→QA→Judgment integration not evidenced

The handoff records `judgment_ids` as test-path only and says live judgment is optional depending on model availability. The MVP spec defines an Integration Mode with actual OpenAI connectivity and an end-to-end path through Research, QA, Judgment, and UI.

Required remediation:
- Run a minimal live OpenAI Responses API smoke/integration run for at least one candidate.
- Validate requested/resolved model, reasoning effort, profile version, prompt version, input/output hashes, schema validation, evidence refs, QA result, and final judgment persistence.
- If the live provider fails, preserve fail-closed behavior and do not mark the integration criterion PASS until the cause is resolved or the external reviewer explicitly changes the MVP requirement.

### ER-P1-03 — L09 UI acceptance evidence is insufficient

L09 QA claims evidence navigation, historical/latest distinction, QA FAIL visibility, and configuration visibility, but the uploaded L09 TEST_RESULTS only records backend pytest and successful Next build. A successful build does not itself prove runtime navigation acceptance criteria.

Required remediation:
- Either run a minimal Playwright/browser smoke test, or record a deterministic manual browser acceptance checklist with evidence.
- Required path: Dashboard → Run → Candidate → Company → Evidence/Audit → Settings.
- Verify QA FAIL visibility, historical/latest distinction, model/profile visibility, and no raw secret exposure.
- Full browser E2E automation suite may remain P2; only core acceptance proof is blocking here.

### ER-P1-04 — Audit content contract is incomplete from L03 onward

The v1.6 QA/Audit contract requires layer metadata including spec version, timestamps, status, current/previous commit, files changed, commands, config versions, acceptance criteria/evidence, and severity counts. The audit directory contains all required filenames, but many L03–L10 documents are only a few lines long and omit multiple required metadata fields.

Required remediation:
- Backfill audit metadata from actual Git history, commands, configs and test evidence.
- Do not invent historical facts. If a required fact cannot be recovered, rerun the relevant validation and record the new evidence.
- In particular, L07/L08 must record the LLM profile/model/reasoning, prompt/schema versions and execution hashes required by the spec.

## Non-blocking Findings

### ER-P2-01 — Handoff commit semantics should be clarified

The uploaded handoff lists `67c9c2d` as its Git commit, while the user-confirmed tag target is `e98ff33`. Do not force-move the existing annotated tag. Clarify the fields as:
- baseline tag target: `e98ff33`
- prior freeze content commit: `67c9c2d`

### ER-P2-02 — External review bundle is not independently reproducible from audit.zip alone

The uploaded audit archive contains audit markdowns, not the tagged source tree, migrations, actual versioned configs/schemas, or raw/machine-readable test outputs. A true code-level external review therefore cannot be completed from this archive alone.

Required for the next review bundle:
- source snapshot at the review candidate commit, excluding secrets/dependencies
- migrations 0001–0009
- `.env.example` only
- actual versioned configs and JSON schemas
- audit directory
- test/build/secret-scan outputs
- representative run identifiers and reproduction commands

## Positive Findings from Available Evidence

The audit material records the following controls as implemented and passing:
- snapshot cutoff/future-leak checks and stable content hash
- deterministic Quant with no LLM dependency
- dynamic evidence-linked Research Packet
- fail-closed LLM model behavior with no silent fallback
- unsupported numeric claim rejection
- QA FAIL blocking SELECTED
- immutable final judgment via DB trigger
- server-side secret boundary and secret scan
- 46-test regression result and successful web build

These are evidence claims from the supplied audit package; source code was not supplied in this review, so they were not independently executed by the reviewer.

## Allowed Next Work

Only a review-remediation pass is approved:

1. Full registry acceptance run.
2. One minimal live OpenAI Research→QA→Judgment run.
3. Core browser acceptance proof.
4. Audit metadata/package completion.
5. Full regression + secret scan + web build.
6. External re-review.

Do **not** implement FRED/macro, top-down industry engine, cloud deployment/scheduler, performance grading, additional agents, or other Post-MVP features during this remediation.

## Tagging Recommendation

Preserve `mvp-v0.1-pass` as historical evidence; do not rewrite/force-move it. Perform remediation on a review branch. After all blocking findings are resolved and re-reviewed, create a new immutable review tag such as `mvp-v0.1-review-pass`.
