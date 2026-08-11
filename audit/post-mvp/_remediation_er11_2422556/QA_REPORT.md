# QA REPORT — ER11

- status: remediating (await external re-review). Not GO.
- P0: 0
- P1: ER3-P1-01 remediating (structural triples); ER3-P1-02 CLOSED
- P2/P3: none opened this round

## Blocking Acceptance

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 true pair → field/equals/value | PASS | `test_er11_remediation.py::test_true_pair_structures_as_field_equals_value` |
| AC-2 copula variants | PASS | `test_copula_and_orientation_do_not_change_true_pair` / `test_generalized_attacks_fail_without_copula_list` |
| AC-3 reverse false pairs | PASS | ER10 + ER11 fixtures |
| AC-4 cross-mix / Unicode / X / wrapper | PASS | ER7–ER11 |
| AC-5 prior PASS fixtures | PASS | ER6–ER10 still green in full suite |
| AC-6 QA lie blocked | PASS | `test_false_copula_variant_cannot_reach_judgment_even_if_qa_lies` |
| AC-7 P1-02/cron/tag | PASS | lineage regime `889d1f45-…`; `scheduler_enable_allowed: false` |

## Notes

Cursor completion ≠ GO. No Post-MVP tag created.
