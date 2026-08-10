# 03. Data Model & Pipeline

## 1. Core Principle

데이터는 `raw → normalized → validated → historical → snapshot` 순서로 이동한다.

검증 전 데이터가 분석 테이블에 바로 들어가면 안 된다.

## 2. Identity Model

### companies
경제적 실체인 회사를 표현한다.

필수 개념 필드:
- company_id
- legal_name
- country_of_incorporation
- sec_cik nullable
- active_status
- created_at

### securities
거래되는 증권을 표현한다.

- security_id
- company_id
- ticker
- exchange
- security_type
- is_adr
- active_from
- active_to
- provider_symbol identifiers

한 company가 여러 security를 가질 수 있다는 구조를 허용한다.

## 3. Universe Membership

### universe_memberships
- security_id
- universe_name
- included
- inclusion_reason
- exclusion_reason
- valid_from
- valid_to
- evaluated_at

Universe 결과를 overwrite하지 않고 역사화한다.

## 4. Market Data

### daily_prices
- security_id
- trading_date
- open
- high
- low
- close
- adjusted_close nullable
- volume
- currency
- source_id
- collected_at

Unique constraint:
`security_id + trading_date + source_version`

## 5. Financial Facts

### financial_facts
- company_id
- metric_key
- value
- unit
- currency nullable
- fiscal_year
- fiscal_quarter nullable
- period_start
- period_end
- form_type
- filed_at
- published_at
- source_id
- source_version

핵심은 `period_end`와 `published_at`을 분리하는 것이다.

## 6. Filings

### filings
- company_id
- accession_number
- form_type
- filed_at
- accepted_at when available
- period_of_report
- source_uri
- raw_hash

MVP는 전체 filing text를 DB에 강제로 저장하지 않아도 된다. metadata + immutable raw evidence reference를 저장한다.

## 7. Sources & Raw Evidence

### sources
- source_id
- provider
- source_type
- external_id
- source_uri
- published_at
- collected_at
- raw_hash
- storage_path

모든 핵심 fact는 source_id로 역추적 가능해야 한다.

## 8. Snapshots

### research_runs
- run_id
- status
- cutoff_at
- created_at
- quant_rule_version
- prompt_version
- llm_provider
- llm_model
- code_commit_hash

### snapshots
- snapshot_id
- run_id
- cutoff_at
- content_hash
- qa_status
- data_quality_score nullable
- created_at

### snapshot_items
분석에 실제 사용된 record를 고정한다.
- snapshot_id
- entity_type
- entity_id
- source_record_id
- eligible_at
- source_hash

MVP 구현상 모든 row를 복제할 필요는 없다. 재현 가능한 immutable reference + version/hash 방식도 허용한다. 단, 이후 source record가 변경되어도 과거 Snapshot 재현이 가능해야 한다.

## 9. Quant Tables

### quant_scores
- run_id
- security_id
- total_score
- growth_score
- quality_score
- cashflow_score
- health_score
- valuation_score
- momentum_score
- peer_group
- rank_market
- rank_peer
- rule_version
- input_hash

## 10. Research Tables

### research_packets
- packet_id
- run_id
- security_id
- packet_version
- input_hash
- payload_json

### ai_research
- research_id
- run_id
- security_id
- agent_role
- prompt_version
- model
- output_json
- output_hash
- created_at

### research_qa
- qa_id
- research_id
- status
- failed_claims
- warnings
- output_json

### judgments
- judgment_id
- run_id
- security_id
- status: SELECTED | WATCH | REJECT
- selection_price
- quant_score
- thesis
- bear_case
- risks
- invalidation_conditions
- evidence_quality
- data_completeness
- uncertainty
- immutable_hash
- created_at

judgment는 UPDATE하지 않는다. 새 research run에서 새 judgment를 추가한다.

## 11. FACT vs ASSESSMENT

### FACT
provider, SEC, 계산 엔진 등으로 검증된 값.

### ASSESSMENT
LLM의 해석 또는 분류.

UI와 DB 모두 두 유형을 구분한다.

## 12. Normalization Rules

- 날짜: UTC 저장 + display timezone 별도 처리
- 미국 시장 cutoff: New York market context를 명시적으로 기록
- currency: ISO currency code
- numeric scale: raw value 기준 저장, UI에서 K/M/B 표현
- ticker는 company identity로 사용하지 않는다.
- metric naming은 내부 canonical key 사용
- missing과 zero를 구분
- restatement는 기존 row overwrite 금지, 새 source_version 추가

## 13. Corporate Actions

MVP에서는 최소한 stock split이 과거 가격 비교를 깨뜨리지 않도록 raw/adjusted 구분을 지원한다.

Post-MVP에서 merger, spin-off, symbol change, delisting 처리 범위를 확장한다.

## 14. Data Ingestion Flow

```text
Fetch
↓
write raw payload + hash
↓
parse
↓
normalize
↓
mechanical QA
↓
PASS → historical DB
FAIL → quarantine + audit issue
```

실패 데이터를 조용히 버리지 않는다.
