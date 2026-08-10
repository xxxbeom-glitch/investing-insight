# Failure Log (오답노트)

> 비슷한 작업 전 **유형 카드**만 본다.  
> 새 실패: 카드에 한 줄 + 아래에 날짜 상세.

## 유형 목차

| ID | 유형 | 이런 작업할 때 |
|----|------|----------------|
| L1 | 레이아웃·쉘·여백 | shell, gutter, full-bleed |
| L2 | Wrap 자식 정렬 | 사진+텍스트, grid |
| T1 | 텍스트 정렬 | title/head |
| G1 | gap·간격 | 카드 사이 |
| B1 | BG·overlay | 배경, 그라데이션 |
| M1 | 모바일 | gutter, grid |
| S1 | Secret·환경파일 | `.env`, 키, 자격증명 (실수 커밋/ZIP) |

프로젝트에 맞게 행을 추가·삭제한다. 웹 레이아웃 유형 예시의 채워진 카드는 `_variants/failure-log.kmong.full.md` 참고.

---

## S1 — Secret·환경파일

**증상 한 줄:** `.env`/키/자격증명이 커밋·ZIP·이슈 첨부에 포함됨

**하지 말 것**
- 비밀값을 코드·로그·issue ZIP에 넣기
- `RelatedFiles`에 `.env`, `*.pem`, `google-services.json` 등 포함

**할 것**
- 루트 `.gitignore`에 env/키 패턴 유지
- `00-common/SECURITY.md` 체크리스트 확인

---

## YYYY-MM-DD — 유형ID 짧은 제목

- **증상:**
- **원인:**
- **방지:**
- **규칙 링크:**
