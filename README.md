# investing-insight

PC Web 기반 미국 주식 AI 리서치·판단 감사 시스템.  
자동매매/주문 실행이 아니라, **선별 근거를 재현·검증**하는 것이 V1 목표다.

## 설계 SoT

`investing-insight-spec-v1.5/` — [README](./investing-insight-spec-v1.5/README.md) 읽기 순서 따름.

## 현재 상태

- 설계서 v1.5 SoT · Cursor 규칙은 **Layer Loop/Audit + 제품 불변식**에 정렬
- 저장소 골격만 존재 — **런타임 앱·의존성 미설치**
- 다음: **L00 Foundation** (`07_MVP_LAYER_PLAN.md` · `agent/LAYER_CHECKLIST.md`)

현황 1장: `_docs/active-track.md`

## 권장 스택 (설계서)

| 영역 | 스택 |
|------|------|
| Web | Next.js + TypeScript (App Router), PC-only |
| API | Python FastAPI + Pydantic |
| DB | PostgreSQL |
| Raw evidence | `storage/raw/` (로컬 FS, 이후 object storage 교체 가능) |

## 폴더 요약

| 경로 | 역할 |
|------|------|
| `apps/web` | PC UI |
| `apps/api` | FastAPI |
| `src/*` | ingest → quant → research 파이프라인 |
| `audit/` | Layer 감사 산출물 |
| `agent/` | Cursor 작업 계약·핸드오프 |
| `_logs/` | harness decision/change/qa/failure |
| `fonts/` | Pretendard · SUIT |

## 보안

비밀·키는 커밋하지 않는다. `SECURITY.md` · `.env.example`만 저장소에 둔다.
