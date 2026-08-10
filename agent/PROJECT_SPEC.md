# PROJECT_SPEC

## 제품

- 이름: `investing-insight`
- 한 줄 설명: NYSE·NASDAQ 대상 AI 리서치·판단 감사 (개인 사용 · PC Web)
- 플랫폼: web (PC only)
- 스택: Next.js + TS / FastAPI + Python / PostgreSQL (설계서 권장 · **lock·버전은 L00에서 확정**)

## 범위

### 한다
- Universe 구축 · 일별 배치 ingest · Snapshot · Quant shortlist · LLM 리서치 · 불변 판단 저장 · PC UI로 근거·QA 확인
- Thin vertical slice MVP (`L00`~`L10`) 후 외부 검증 중단

### 안 한다 (1차 / V1)
- 자동매매·주문·타이밍·포지션
- 모바일/태블릿 QA
- 완성형 Multi-Agent debate (MVP는 주 LLM + 역할 분리 호출)
- Post-MVP 기능 자동 착수

## 위험 구역 (손대기 전 확인)

| 구역 | 왜 위험한지 | 건드릴 때 |
|------|-------------|-----------|
| Snapshot / Judgment immutability | 감사 무결성 | 설계·스키마 합의 후 |
| Future information leakage | 백테스트 오염 | cutoff·effective_at 규칙 준수 |
| LLM이 숫자 계산 | 비결정·환각 | Quant는 코드만 |
| Provider 결합 | 교체 비용 | adapter interface 먼저 |
| secrets / `storage/raw` | 유출·용량 | gitignore · SECURITY |

## Source of Truth

| 종류 | 경로 |
|------|------|
| 화면/기능 스펙 | `investing-insight-spec-v1.5/` |
| 확정 결정 | `…/00_PROJECT_DECISIONS.md` |
| Cursor 규칙 | `.cursor/rules/` |
| 현재 작업 계약 | `agent/TASK_CONTRACT.md` |
| 현황 1장 | `_docs/active-track.md` |

## 작업 전 질문 (에이전트)

1. 이번 변경의 Done When은? (Layer Acceptance인가?)
2. 만지면 안 되는 파일/불변 데이터는?
3. 검증 명령·감사 산출물은?
4. 설계 SoT와 충돌하지 않는가?
