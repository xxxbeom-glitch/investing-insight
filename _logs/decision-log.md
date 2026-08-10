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
| SEO/AEO | 의도적 생략 | 개인 툴 |
| 현재 Layer | L00 전 (골격) | |
| 지침 출처 | `D:\project\markdown` pack `web` + 커스텀 | 2026-08-10 |

---

## 2026-08-10 — 저장소 부트스트랩

| # | 결정 |
|---|------|
| 1 | markdown `web` pack + fonts를 가져오고 kmong `site/` 경로를 본 제품 트리로 교체 |
| 2 | QA·반응형은 PC-only (모바일 비대상) |
| 3 | 설계서 v1.5를 SoT로 두고, 런타임 앱은 L00 합의 후 생성 |
| 4 | harness 로그는 `_logs/`, 설계 본문은 `investing-insight-spec-v1.5/` 유지 |
