# 01. System Architecture

## 1. Architecture Goal

MVP는 개발 PC에서 안정적으로 실행되되 핵심 DB를 Supabase PostgreSQL에 두고, 검증 후 운영 자동화·웹 배포·Top-down·Multi-Agent 확장으로 연결되는 구조를 사용한다.

## 2. Recommended Stack

구현 시작 시 current stable을 공식 문서로 확인하고 lock file로 고정한다.

### Web
- Next.js + TypeScript
- App Router
- PC-first, 1280px+ core support
- 모바일 최적화는 MVP 제외

### API / Research Backend
- Python
- FastAPI
- Pydantic 계열 schema validation
- Quant/data processing은 Python

### Database
- Supabase PostgreSQL
- PostgreSQL을 system of record로 사용
- JSONB는 flexible payload/raw metadata에 제한 사용
- 핵심 비교 필드는 정규 컬럼
- Firebase/Firestore는 사용하지 않음

### Raw Evidence Storage
MVP는 로컬 immutable raw store를 허용한다.

`storage/raw/{provider}/{date}/{sha256}.{json|txt}`

Post-MVP에 S3-compatible object storage로 이전 가능하도록 adapter를 둔다.

### Scheduler
MVP는 자동 운영 전 단계이므로 CLI/manual runner가 기준이다.
- CLI command
- backend job runner

OS cron/cloud scheduler는 Production Readiness 이후.

## 3. Secret & Config Separation

### Secret: `.env.local`
```text
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
MASSIVE_API_KEY=
OPENAI_API_KEY=
SEC_USER_AGENT="investing-insight/0.1 contact@example.com"
FRED_API_KEY=  # Post-MVP optional
```

### Versioned non-secret config
```text
config/
├─ llm_profiles.v0.1.yaml
├─ quant_rules.v0.1.yaml
├─ research_limits.v0.1.yaml
└─ provider_policy.v0.1.yaml
```

모델명/reasoning은 secret이 아니며 연구 재현성에 필요한 실험 변수이므로 `.env`가 아니라 Git versioned config로 관리한다.

## 4. LLM Profiles

MVP source of truth 예:

```yaml
version: llm-profile-v0.1
api: responses

company_research:
  model: gpt-5.6-terra
  reasoning_effort: medium

research_qa:
  model: gpt-5.6-terra
  reasoning_effort: high

final_judgment:
  model: gpt-5.6-terra
  reasoning_effort: high
```

규칙:
- 코드에 모델명을 hard-code하지 않는다.
- `reasoning.effort`만 공식 설정값으로 전달한다.
- profile 변경 시 version을 올린다.
- unavailable model에 silent fallback 금지.
- 실제 호출 결과에 resolved model/profile version을 저장한다.

## 5. Repository Layout

```text
investing-insight/
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  └─ schemas/
├─ config/
│  ├─ llm_profiles.v0.1.yaml
│  ├─ quant_rules.v0.1.yaml
│  └─ research_limits.v0.1.yaml
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
├─ storage/raw/
├─ audit/mvp/
├─ docs/
├─ scripts/
├─ .env.example
└─ README.md
```

## 6. Logical Layers

```text
[Massive] [SEC] [OpenAI]
      ↓
[Ingestion]
      ↓
[Raw Store + Hash]
      ↓
[Normalization]
      ↓
[Data QA Gate]
      ↓
[Supabase PostgreSQL Historical DB]
      ↓
[Snapshot Engine]
      ↓
[Snapshot QA Gate]
      ↓
[Quant Engine]
      ↓
[Candidate Shortlist]
      ↓
[Dynamic Research Packet JSON]
      ↓
[Company Research / Terra medium]
      ↓
[Research QA / Terra high]
      ↓
[Final Judgment / Terra high]
      ↓
[Immutable Judgment]
      ↓
[PC Web]
```

## 7. Provider Boundary

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
- execute_structured(role, packet, prompt_version, llm_profile_version)

실제 role별 wrapper:
- analyze_company(...)
- review_research(...)
- finalize_judgment(...)

### MacroProvider
Post-MVP interface. FRED adapter 예정.

## 8. SEC Client Policy

- `SEC_USER_AGENT` 필수
- 요청 header에 프로젝트명/버전/연락처를 명시
- client limiter는 10 req/s 미만 또는 이하로 강제
- retry/backoff 사용
- 403/429 등을 silent success로 처리하지 않음

## 9. Supabase Boundary

- 브라우저가 필요한 공개/제한 기능에만 publishable key 사용
- secret key는 API/backend에서만 사용
- secret key를 `NEXT_PUBLIC_*`에 넣지 않음
- server-only module boundary를 둠
- MVP 1인용이라도 RLS/권한을 무시하지 않고 최소권한 설계를 기록

## 10. Orchestrator

```text
create_run(cutoff)
→ check_provider_health()
→ create_snapshot()
→ run_snapshot_qa()
→ run_quant()
→ build_shortlist()
→ build_research_packets()
→ run_company_research()
→ run_research_qa()
→ run_final_judgment()
→ persist_immutable_judgments()
→ generate_report()
→ close_run()
```

각 step은 idempotent하고 상태·입력hash·config version을 기록한다.

## 11. Non-Goals for MVP

- Realtime WebSocket
- Intraday signals
- Distributed queue/Kubernetes
- Full autonomous agent swarm
- FRED Macro engine
- News API aggregation
- Broker execution
- Cloud scheduler / public web deployment
