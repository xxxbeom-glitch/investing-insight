# Active Track

> **갱신:** 2026-08-10 · 상세: `_logs/decision-log.md`  
> **진행 중:** Cursor 하네스를 설계서 Loop/Audit에 정렬 완료 · **L00 미착수**  
> **규칙 SoT:** `.cursor/rules/`  
> **설계 SoT:** `investing-insight-spec-v1.5/`  
> **Layer 증거:** `audit/mvp/`

## 지금 쓰는 것

| 항목 | 값 |
|------|-----|
| **제품** | investing-insight (AI research + decision audit) |
| **폼팩터** | PC Web only (min ~1280, primary 1440) |
| **시장** | US · NYSE + NASDAQ · 보통주/ADR |
| **Web / API** | `apps/web` · `apps/api` · **미생성** |
| **파이프라인** | `src/` · **미구현** |
| **루프** | `25-layer-audit.mdc` · 체크리스트 `agent/LAYER_CHECKLIST.md` |
| **불변식** | `15-product-invariants.mdc` |
| **UI QA** | `50` PC-only |
| **현재 Layer** | L00 전 |
| **제거된 규칙** | Figma/정적HTML/모션프리셋/SEO (`30`/`40`/`45`/`46`/`73`) |

## 하지 않는 것 (V1)

자동 주문 · 매수/매도 타이밍 · 포지션 · 모바일 QA · Post-MVP 자동 착수
