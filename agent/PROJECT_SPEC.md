# PROJECT_SPEC

## 제품

- 이름: `investing-insight`
- 한 줄 설명: NYSE·NASDAQ 대상 AI 리서치·판단 감사 (개인 사용 · PC Web)
- 플랫폼: web (PC only · 로컬 MVP)
- 스택: Next.js + TS / FastAPI + Python / **Supabase PostgreSQL** / OpenAI Responses · Massive · SEC  
  (lock·버전은 L00에서 확정)

## 범위

### 한다
- Universe · ingest · Snapshot · Quant · LLM research/QA/judgment · 불변 판단 · PC UI
- Thin vertical slice MVP (`L00`~`L10`) 후 외부 검증 중단

### 안 한다 (MVP / V1)
- 자동매매·주문·타이밍·포지션
- 모바일 QA · Firebase · MVP 중 공개 배포/클라우드 스케줄러
- 기업별 영구 JSON 파일 SoR · 모델 silent fallback
- Post-MVP 자동 착수

## 위험 구역

| 구역 | 왜 위험한지 | 건드릴 때 |
|------|-------------|-----------|
| Snapshot / Judgment immutability | 감사 무결성 | 설계·스키마 합의 후 |
| Future information leakage | 백테스트 오염 | cutoff 규칙 |
| LLM이 숫자 계산 | 비결정·환각 | Quant는 코드만 |
| Supabase secret in client | 키 유출 | server-only boundary |
| silent model fallback | 재현성 붕괴 | Fail Closed |
| secrets / `storage/raw` | 유출·용량 | `.env.local` · SECURITY |

## Source of Truth

| 종류 | 경로 |
|------|------|
| 설계 | `investing-insight-spec-v1.6/` |
| 확정 결정 | `…/00_PROJECT_DECISIONS.md` |
| LLM profile | `config/llm_profiles.*` |
| Schema 예시 | `packages/schemas/` |
| Cursor 규칙 | `.cursor/rules/` |
| Layer 체크리스트 | `agent/LAYER_CHECKLIST.md` |
| 현황 1장 | `_docs/active-track.md` |

## 작업 전 질문 (에이전트)

1. Done When은? (Layer Acceptance인가?)
2. 만지면 안 되는 불변 데이터/secret은?
3. 검증 명령·audit 산출물은?
4. 설계 SoT v1.6과 충돌하지 않는가?
