# 보안·자격증명 위생 (스택 무관)

프로젝트에 지침을 붙일 때, 또는 에이전트가 파일을 커밋·ZIP·로그에 넣을 때 지킨다.

## 절대 커밋·첨부하지 말 것

- `.env`, `.env.*` (`.env.example` 제외)
- API 키, 관리자 토큰, 비밀번호, 서명 키
- `*.pem` / `*.p12` / `*.keystore` / `*.jks`
- `google-services.json`, `GoogleService-Info.plist`, `service-account*.json`
- `local.properties`, `credentials.json`
- SSH 개인키 (`id_rsa`, `id_ed25519` 등)

## 프로젝트 시작 체크

- [ ] 루트 `.gitignore`에 위 패턴이 있는지 (이 라이브러리 `.gitignore`를 복사·병합해도 됨)
- [ ] 예시 env는 `.env.example`만, 실값은 로컬만
- [ ] CI/시크릿은 호스트 secret store 사용 (파일로 저장소에 넣지 않음)

## 에이전트 규칙

- 비밀값이 대화·파일에 보이면 **재사용·커밋·이슈 ZIP에 넣지 말고** 사용자에게 알린다
- “동작하게” 하려고 키를 하드코딩하지 않는다
- push / force push / `--no-verify`는 사용자 명시 요청 없이 하지 않는다

## 스택별 추가

- **웹:** `10-web/git/55-git-workflow.mdc` + 이 문서
- **앱:** `20-app/cursor-rules/30-production-engineering.mdc` (Secret·개인정보·릴리즈)가 우선
- **Issue ZIP:** `20-app/cursor-rules/issue-bridge.mdc` — 비밀·환경파일 제외
