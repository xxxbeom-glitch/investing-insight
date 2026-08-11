# QA_REPORT

- status: **STOP** (not product PASS)
- P0: 0
- P1 (this live path): English month-day dates still FAIL L08 (see OPEN_ISSUES)

## AC

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 | PASS | test_claim_check AAPL billion fixtures |
| AC-2 | PASS | wrong value/scale/percent tests |
| AC-3 | PASS | date-digit + cross-value tests (ISO / other metric) |
| AC-4 | PASS | er11 + `close is 100.5B` still unsupported |
| AC-5 | PASS | self_remediate exit 0; FP=0 |
| AC-6 | **FAIL** | run `bac5e73f` Research QA FAIL |
| AC-7 | PASS | cron/tag/GO unchanged |

## Live FAIL cause (do not widen this PR)

LLM wrote raw `383,266,000,000` (unit-scale OK) plus prose dates `June 27, 2026` / `July 9, 2026`. Parser treats `27`, `9`, `10`, `2026` as absolute quantities. ISO dates were skipped; **English month-day dates were not**. 20× `numeric_not_in_packet_evidence`, all date fragments. Financial raw values themselves were not the failing numbers.
