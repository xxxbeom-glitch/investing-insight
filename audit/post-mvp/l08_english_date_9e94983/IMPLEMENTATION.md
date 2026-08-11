# IMPLEMENTATION

- status: DONE (L08 live QA not FAIL; not product GO)
- checkpoint: 41c9a77
- live run_id: `4cc95063-07cf-45a3-944b-b93585f278c4`

## Code

1. `numeric_scale.py`: English month-day dates (`June 27, 2026`) are date spans, not quantities. ISO dates unchanged. Bare `2026`/`27` still FAIL.
2. `claim_support.py` leftover: only cited field vocab absorbs tokens (`100.5 is close date` FAIL).
3. Approx operators `≈` `~` fail-closed; structural_attacks include them.

## Live

Research QA `PASS_WITH_WARNING` (warning: `research_declared_unsupported_or_missing`). failed_claims 0. judgment WATCH.

## Not changed

GO / tag / cron / Optional / hosted
