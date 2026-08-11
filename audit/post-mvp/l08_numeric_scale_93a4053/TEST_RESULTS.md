# TEST_RESULTS

## Unit (this scope)

`pytest tests/unit/test_numeric_scale.py tests/unit/test_claim_check.py tests/unit/test_l08_m03_numeric_contract.py tests/unit/test_er11_remediation.py`

PASS (after holdout nested-score walk).

L08 PASS fixtures: raw `383266000000` ↔ `$383.266 billion` / `383.266B` / `383,266 million`; AAPL 6 live strings.

L08 FAIL fixtures: `$384.266 billion`, `$383.266 million`, `383.266%`, bare `383.266`, `383 billion` (0-decimal round 금지), date digits `2026`, cross-value `$107.520 billion` against assets-only packet.

## Full suite (self_remediate)

pytest **262 passed**. secret_scan PASS. client_secret_scan PASS. web build PASS.

## Grounding self-QA

replay 160/160. Red-Team 20/20. FP=0. exit 0.

## Live biweekly

See `live_result.json`. Research QA **FAIL** (new cause: English dates). AC-6 not met.
