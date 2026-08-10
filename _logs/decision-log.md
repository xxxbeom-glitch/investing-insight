# Decision Log

> 작업 **시작 전** 「현재 유효 결정」표만 본다.

## 현재 유효 결정 (빠른 조회)

| 주제 | 현재 값 | 비고 |
|------|---------|------|
| 제품 | AI research + decision audit · 비매매 | `00_PROJECT_DECISIONS` |
| UI | PC only · primary 1440 · min 1280 | `06_PC_WEB_UI` |
| 시장 | US NYSE+NASDAQ · 보통주/ADR | ETF 등 제외 |
| 권장 스택 | Next.js · FastAPI · PostgreSQL | 버전·lock은 L00 |
| 설계 SoT | `investing-insight-spec-v1.5/` | |
| 코드 경로 | `apps/web` · `apps/api` · `src/` | |
| SEO/AEO | 의도적 생략 · 규칙 파일 제거 | 2026-08-10 |
| Cursor 하네스 | Layer audit + 불변식 · 템플릿 웹 규칙 제거 | 2026-08-10 |
| 현재 Layer | L00 전 (골격) | |

---

## 2026-08-10 — Cursor 하네스 설계서 정렬

| # | 결정 |
|---|------|
| 1 | `30`/`40`/`45`/`46`/`73` 삭제 (본 제품과 무관) |
| 2 | `15-product-invariants` · `25-layer-audit` alwaysApply 추가 |
| 3 | Git은 Layer PASS/FREEZE + HANDOFF hash 기준 (`55`) |
| 4 | Layer 증거는 `audit/mvp/` 우선, `_logs/`는 harness 메모 |

---

## 2026-08-10 — 저장소 부트스트랩

| # | 결정 |
|---|------|
| 1 | markdown `web` pack + fonts를 가져오고 kmong `site/` 경로를 본 제품 트리로 교체 |
| 2 | QA·반응형은 PC-only (모바일 비대상) |
| 3 | 설계서 v1.5를 SoT로 두고, 런타임 앱은 L00 합의 후 생성 |
| 4 | harness 로그는 `_logs/`, 설계 본문은 `investing-insight-spec-v1.5/` 유지 |
