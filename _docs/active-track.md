# Active Track

> **갱신:** 2026-08-10 · 상세: `_logs/decision-log.md`  
> **진행 중:** 저장소 부트스트랩 · 설계서 v1.5 정렬 · L00 전 합의  
> **규칙 SoT:** `.cursor/rules/`  
> **설계 SoT:** `investing-insight-spec-v1.5/`

## 지금 쓰는 것

| 항목 | 값 |
|------|-----|
| **제품** | investing-insight (AI research + decision audit) |
| **폼팩터** | PC Web only (min ~1280, primary 1440) |
| **시장** | US · NYSE + NASDAQ · 보통주/ADR (ETF 등 제외) |
| **Web** | `apps/web/` · Next.js(설계) · **미생성** |
| **API** | `apps/api/` · FastAPI(설계) · **미생성** |
| **파이프라인** | `src/` · **미구현** |
| **절차** | `20-harness-workflow.mdc` · Layer = `07_MVP_LAYER_PLAN.md` |
| **QA** | UI `50` PC-only · Layer = `05_QA_LOOP_AUDIT.md` |
| **SEO/AEO** | **의도적 생략** (개인 리서치 툴) |
| **현재 Layer** | L00 진입 전 (골격만) |

## `_docs/` · 설계

| 경로 | 역할 |
|------|------|
| `_docs/active-track.md` | 현황 1장 (본 파일) |
| `_docs/design/` | 설계 포인터 |
| `investing-insight-spec-v1.5/` | 설계 본문 |

## 하지 않는 것 (V1)

자동 주문 · 매수/매도 타이밍 · 포지션 사이징 · 모바일 QA · Post-MVP 자동 착수
