# Decision Log

> 작업 **시작 전** 「현재 유효 결정」표만 본다.

## 현재 유효 결정 (빠른 조회)

| 주제 | 현재 값 | 비고 |
|------|---------|------|
| 제품 | AI research + decision audit · 비매매 | `00_PROJECT_DECISIONS` |
| UI | PC only · primary 1440 · min 1280 | `06_PC_WEB_UI` |
| 시장 | US NYSE+NASDAQ · 보통주/ADR | ETF 등 제외 |
| 스택 | Next.js · FastAPI · **Supabase PG** | Firebase 금지 |
| Providers | Massive · SEC · OpenAI Responses | FRED=Post-MVP |
| LLM | Terra 역할 분리 · `config/llm_profiles.*` | silent fallback 금지 |
| Secret | `.env.local` | key만 env |
| 설계 SoT | `investing-insight-spec-v1.6/` | |
| 코드 경로 | `apps/*` · `src/` · `config/` | |
| Cursor 하네스 | Layer audit + 불변식 · **자동 commit/push** | |
| 현재 Layer | L00 전 | |

---

## 2026-08-10 — 자동 commit/push

| # | 결정 |
|---|------|
| 1 | 작업 단위 종료 시 허락 없이 commit |
| 2 | commit 성공 후 즉시 `git push` (upstream 없으면 `-u`) |
| 3 | force push · 훅 우회 · 파괴적 git은 명시 요청 있을 때만 |

---

## 2026-08-10 — 설계서 v1.6 반영

| # | 결정 |
|---|------|
| 1 | SoT를 `investing-insight-spec-v1.6/`로 전환 (v1.5 제거) |
| 2 | DB=Supabase · 로컬 Web/API · Firebase 금지 · MVP 중 공개 배포 금지 |
| 3 | `.env.example`/secret 정책·`config/`·schema 예시를 설계서와 동기화 |
| 4 | 불변식에 Fail Closed · 기업별 JSON SoR 금지 · Responses API 반영 |

---

## 2026-08-10 — Cursor 하네스 설계서 정렬

| # | 결정 |
|---|------|
| 1 | `30`/`40`/`45`/`46`/`73` 삭제 |
| 2 | `15-product-invariants` · `25-layer-audit` 추가 |
| 3 | Git은 Layer PASS/FREEZE + HANDOFF hash |
| 4 | Layer 증거는 `audit/mvp/` 우선 |

---

## 2026-08-10 — 저장소 부트스트랩

| # | 결정 |
|---|------|
| 1 | markdown web pack + 제품 트리 커스터마이즈 |
| 2 | QA PC-only |
| 3 | 런타임 앱은 L00 이후 |
