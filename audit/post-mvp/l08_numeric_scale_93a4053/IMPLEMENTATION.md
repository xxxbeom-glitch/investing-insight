# IMPLEMENTATION

- status: STOP (unit-scale code PASS; live Research QA still FAIL)
- completed_at: 2026-08-11T15:05:00+00:00
- previous: 93a4053 / checkpoint e5e6762
- choice: **A** — share `numeric_scale.py` only. L08 bag vs M03 triples 유지.

## Cause confirmed

Live AAPL `31835b24` packet `value` is string `"383266000000"`. Claim `$383.266 billion` extracted `383.266` into the old number bag → `numeric_not_in_packet_evidence`.

## Contract

Supported claim absolute units: none (raw), million(s)/M, billion(s)/B. `$`, thousands `,`, sign, decimals.

- `places==0`: exact `evidence == mantissa * scale`
- `places>=1`: `|evidence - mantissa*scale| <= 0.5 * 10^(-places) * scale`
- `%` never matches absolute
- ISO `YYYY-MM-DD` is not a quantity
- glued non-unit letter (`81.32A`) is not a quantity

## Files

- `apps/api/app/research/numeric_scale.py` (new)
- `apps/api/app/research/claim_check.py` (uses shared magnitudes)
- `apps/api/app/agents/claim_support.py` (same magnitude spans; schema/operator 불변)
- tests: `test_numeric_scale.py`, `test_claim_check.py`, `test_l08_m03_numeric_contract.py`

bundle_sha256: `bea2a767f3881e46976cb8d2eefc1dfcdfc62a78cc685a8590d543745372fd15`

## Not changed

GO / tag / cron / Optional / M03 claim schema / gate relaxation / English month-day date parsing
