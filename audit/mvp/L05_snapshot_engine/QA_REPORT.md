# QA_REPORT
- cutoff 이후 daily_price/financial_fact 0
- same cutoff+input → same content_hash + snapshot_id reuse
- restatement: content_hash 동일 시 insert 없이 reuse (old snapshot 불변)
- source_versions / config_versions 역추적
- snapshot_manifest.schema.json keys PASS
- P0=0 P1=0
