# 03. Data Model & Pipeline

## 1. Core Principle

`raw → normalized → validated → historical → snapshot → research packet` 순서다.

검증 전 데이터가 분석에 사용되면 안 된다.

## 2. Identity Model

### companies
- company_id
- legal_name
- country_of_incorporation
- sec_cik nullable
- active_status
- created_at

### securities
- security_id
- company_id
- ticker
- exchange
- security_type
- is_adr
- active_from
- active_to
- provider identifiers

Ticker는 identity가 아니다.

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
- rule_version

Overwrite 금지, 역사화.

## 4. Market Data

### daily_prices
- security_id
- trading_date
- open/high/low/close
- adjusted_close nullable
- volume
- currency
- source_id
- source_version
- collected_at

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

`period_end`와 `published_at`을 분리한다.

## 6. Filings

### filings
- company_id
- accession_number
- form_type
- filed_at
- accepted_at
- period_of_report
- source_uri
- raw_hash

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

핵심 fact는 source_id로 역추적 가능해야 한다.

## 8. Research Runs & Snapshots

### research_runs
- run_id
- status
- cutoff_at
- created_at
- quant_rule_version
- prompt_bundle_version
- llm_profile_version
- code_commit_hash
- universe_rule_version

### snapshots
- snapshot_id
- run_id
- cutoff_at
- content_hash
- qa_status
- data_quality_score nullable
- created_at

### snapshot_items
- snapshot_id
- entity_type
- entity_id
- source_record_id
- eligible_at
- source_hash
- source_version

과거 source가 restate되어도 old snapshot이 변하지 않아야 한다.

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

## 10. Research Packet

### research_packets
- packet_id
- run_id
- security_id
- snapshot_id
- packet_schema_version
- packet_version
- input_hash
- payload_json
- created_at

`payload_json`은 분석 시 동적으로 생성된 패킷이다. 기업별 영구 JSON 파일을 system of record로 사용하지 않는다.

## 11. LLM Execution Records

### llm_executions
- execution_id
- run_id
- security_id nullable
- agent_role
- prompt_version
- llm_profile_version
- requested_model
- resolved_model
- reasoning_effort
- response_id nullable
- input_hash
- output_hash
- schema_version
- status
- token_usage nullable
- estimated_cost nullable
- started_at
- completed_at
- error_code nullable

모델/profile 변경을 추적하기 위한 핵심 테이블이다.

### ai_research
- research_id
- execution_id
- run_id
- security_id
- output_json
- output_hash
- created_at

### research_qa
- qa_id
- execution_id
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
- final_execution_id
- immutable_hash
- created_at

Judgment UPDATE 금지.

## 12. FACT vs ASSESSMENT

- FACT: provider/SEC/code-calculation으로 검증된 값
- ASSESSMENT: LLM 해석/분류

DB와 UI에서 분리한다.

## 13. JSON Schema Contracts

최소 contracts:
- `company_analysis_input.schema.json`
- `company_analysis_output.schema.json`
- `research_qa_output.schema.json`
- `final_judgment_output.schema.json`
- `snapshot_manifest.schema.json`

Schema version을 packet/execution에 저장한다.

## 14. Normalization Rules

- DB timestamps: UTC
- 시장 문맥: America/New_York 별도 기록/표시
- currency: ISO code
- raw numeric value 저장, UI만 K/M/B formatting
- missing != zero
- metric_key canonicalization
- restatement overwrite 금지
- provider symbol != internal identity

## 15. Corporate Actions

MVP 최소:
- stock split raw/adjusted 구분
- historical return 계산 시 adjusted basis 명시

Post-MVP:
- merger/spin-off/ticker change/delisting 강화

## 16. Data Ingestion Flow

```text
Fetch
↓
write immutable raw + hash
↓
parse
↓
normalize
↓
mechanical/data QA
↓
PASS → historical DB
FAIL → quarantine + audit issue
```

실패를 조용히 버리지 않는다.
