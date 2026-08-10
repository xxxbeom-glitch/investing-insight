# 01. System Architecture

## 1. Architecture Goal

MVP는 로컬/개인 사용 환경에서 안정적으로 실행되고, 이후 자동화·배포·Multi-Agent 확장에 무리 없이 연결되는 구조를 사용한다.

## 2. Recommended Stack

정확한 라이브러리 버전은 구현 시작 시 current stable을 확인하고 lock file로 고정한다.

### Web
- Next.js + TypeScript
- App Router
- PC-first layout
- API 호출과 상태 관리를 단순화하고, 모바일 최적화는 하지 않는다.

### API / Research Backend
- Python
- FastAPI
- Pydantic 계열 schema validation
- Quant / data processing은 Python에서 수행

### Database
- PostgreSQL
- JSONB는 provider raw metadata 및 flexible research payload에 제한적으로 사용
- 핵심 비교 가능한 필드는 정규 컬럼으로 저장

### Raw Evidence Storage
MVP는 로컬 filesystem 기반 immutable raw store를 허용한다.

예:
`storage/raw/{provider}/{date}/{sha256}.{json|txt}`

향후 S3-compatible object storage로 교체 가능하도록 storage adapter를 둔다.

### Scheduler
MVP는 복잡한 queue system을 도입하지 않는다.
- CLI command
- OS cron / local scheduler
- backend job runner

중 하나로 일별 ingest와 격주 research run을 호출할 수 있게 한다.

### LLM
Provider adapter를 둔다.
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`

코드가 특정 모델명에 강하게 결합되지 않도록 한다.

## 3. Repository Layout

```text
investing-insight/
├─ apps/
│  ├─ web/                 # PC Web
│  └─ api/                 # FastAPI + research API
├─ packages/
│  └─ schemas/             # API contract / shared schemas when useful
├─ src/
│  ├─ ingestion/
│  ├─ normalization/
│  ├─ qa/
│  ├─ snapshot/
│  ├─ quant/
│  ├─ research/
│  ├─ reporting/
│  └─ audit/
├─ migrations/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ fixtures/
│  └─ e2e/
├─ storage/
│  └─ raw/
├─ audit/
│  └─ mvp/
├─ docs/
├─ scripts/
├─ .env.example
├─ docker-compose.yml
└─ README.md
```

실제 프로젝트 구조가 프레임워크 제약상 달라져도 역할 경계는 유지한다.

## 4. Logical Layers

```text
[External Sources]
 Market Provider / SEC / LLM
        ↓
[Ingestion]
        ↓
[Raw Store + Hash]
        ↓
[Normalization]
        ↓
[Data QA Gate]
        ↓
[Historical PostgreSQL]
        ↓
[Snapshot Engine]
        ↓
[Snapshot QA Gate]
        ↓
[Quant Engine]
        ↓
[Candidate Shortlist]
        ↓
[Research Packet]
        ↓
[LLM Research]
        ↓
[Research QA]
        ↓
[Final Selection + Thesis]
        ↓
[Immutable Judgment]
        ↓
[PC Web]
```

## 5. Provider Boundary

외부 공급자는 언제든 바뀔 수 있다. 따라서 아래 interface를 먼저 정의하고 provider 구현을 연결한다.

### MarketDataProvider
- list_securities()
- get_daily_bars()
- get_security_details()
- get_corporate_actions() when available

### FilingProvider
- map_company_identifier()
- get_company_facts()
- get_filings_metadata()
- get_filing_document()

### LLMProvider
- analyze_company(packet, prompt_version)
- review_research(input, prompt_version)

MVP의 초기 후보는:
- Market Data: Massive 계열 provider adapter
- Official filings/facts: SEC EDGAR / data.sec.gov

단, endpoint와 plan 제약은 구현 시 공식 문서를 재확인한다.

## 6. Orchestrator

MVP에는 하나의 Research Run Orchestrator가 있다.

```text
create_run(cutoff)
→ check_ingestion_health()
→ create_snapshot()
→ run_snapshot_qa()
→ run_quant()
→ build_shortlist()
→ build_research_packets()
→ run_llm_research()
→ run_research_qa()
→ create_final_judgments()
→ generate_report()
→ close_run()
```

각 step은 idempotent하게 설계한다. 동일 run_id에 대해 재실행하더라도 중복 record를 만들지 않고, 이전 step 결과를 명시적으로 versioning한다.

## 7. Non-Goals for MVP

- Realtime WebSocket price feed
- Intraday trading signals
- Distributed job queue
- Kubernetes
- Multi-region deployment
- Complex vector DB as mandatory dependency
- Fully autonomous multi-agent debate
- Broker order execution
