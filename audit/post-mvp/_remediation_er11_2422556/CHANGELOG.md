# CHANGELOG — ER11

- Replaced copula/token-bag claim support with inventory span-match → `field/operator/value` triples.
- Added `parse_claim` / `ClaimTriple`. Operator is `equals`; copulas are not parsed as syntax.
- Generalized tests: copula variants, reverse pairs, Unicode, 1-char, numbers/dates, wrapper/meta.
- Prompt one-liners: restate payload field/value only.
- `bind_union_lineage` not modified.
