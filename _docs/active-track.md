# Active Track

> **갱신:** 2026-08-10 · 상세: `_logs/decision-log.md`  
> **진행 중:** 설계서 **v1.6** 반영 · **L00 미착수**  
> **규칙 SoT:** `.cursor/rules/`  
> **설계 SoT:** `investing-insight-spec-v1.6/`  
> **Layer 증거:** `audit/mvp/`

## 지금 쓰는 것

| 항목 | 값 |
|------|-----|
| **제품** | investing-insight (AI research + decision audit) |
| **폼팩터** | PC Web only (min ~1280, primary 1440) |
| **시장** | US · NYSE + NASDAQ · 보통주/ADR |
| **DB** | Supabase PostgreSQL (Firebase 금지) |
| **Providers** | Massive · SEC · OpenAI Responses |
| **LLM profile** | `config/llm_profiles.v0.1.yaml` (Terra 역할 분리) |
| **Web / API** | `apps/web` · `apps/api` · **미생성** |
| **Secret** | `.env.local` (커밋 금지) |
| **루프** | `25-layer-audit.mdc` · `agent/LAYER_CHECKLIST.md` |
| **불변식** | `15-product-invariants.mdc` (v1.6) |
| **현재 Layer** | L00 전 |

## 하지 않는 것 (MVP)

자동 주문 · 모바일 QA · Firebase · MVP 중 공개 배포/클라우드 스케줄러 · Post-MVP 자동 착수 · 기업별 영구 JSON 파일 SoR
