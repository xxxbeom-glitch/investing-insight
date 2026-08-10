# 보안·자격증명 위생

에이전트가 커밋·로그·audit·UI에 넣을 때 지킨다.

## 절대 커밋·첨부하지 말 것

- `.env`, `.env.local`, `.env.*` (`.env.example` 제외)
- API 키, 토큰, 비밀번호, 서명 키
- `SUPABASE_SECRET_KEY`, `OPENAI_API_KEY`, `MASSIVE_API_KEY` 실값
- `*.pem` / `*.p12` / `*.keystore` / `*.jks`
- `credentials.json`, SSH 개인키, `service-account*.json`

## 이 프로젝트 (v1.6)

- 실 secret은 **`.env.local`** (또는 secret store)
- `.env.example`에는 변수명만 (`investing-insight-spec-v1.6/config_examples/.env.example`와 동기화)
- 모델명·reasoning은 `config/`에 두고 Git에 포함 (secret 아님)
- Supabase **secret key → 서버만** · 브라우저/`NEXT_PUBLIC_*` 금지
- OpenAI/Massive key → 서버 전용
- SEC: key 없음 · `SEC_USER_AGENT` + rate limit
- secret을 audit · screenshot · error payload · report에 남기지 않음

## 에이전트

- 비밀값이 보이면 재사용·커밋하지 말고 사용자에게 알린다
- 키 하드코딩 금지
- 일반 `commit` + `push`는 프로젝트 규칙(`55-git-workflow`)상 **자동**
- `force push` / `--no-verify` / 파괴적 git은 명시 요청 없이 금지
