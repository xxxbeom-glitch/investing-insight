# investing-insight

PC Web 기반 미국 주식 AI 리서치·판단 감사 시스템.  
설계 SoT: [`investing-insight-spec-v1.6/`](./investing-insight-spec-v1.6/README.md)

## 현재

- **L00 Foundation** 구현 중/차단: 실 Supabase 프로젝트 URL 필요 (placeholder `xxxxx.supabase.co`면 DB health FAIL)
- 증거: `audit/mvp/L00_foundation/`

## 로컬 실행 (MVP lab)

```powershell
# 1) secrets
copy .env.example .env.local   # 실값 입력 (SUPABASE_* 등)

# 2) API
cd apps\api
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
cd ..\..
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\uvicorn app.main:app --app-dir apps\api --host 127.0.0.1 --port 8000

# 3) Web (다른 터미널)
cd apps\web
npm install
$env:API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## 테스트 / 유틸

```powershell
.\apps\api\.venv\Scripts\python.exe -m pytest tests -q
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
.\apps\api\.venv\Scripts\python.exe scripts\check_client_secrets.py
.\apps\api\.venv\Scripts\python.exe scripts\migrate.py --check
.\apps\api\.venv\Scripts\python.exe scripts\migrate.py   # needs SUPABASE_DB_URL
.\apps\api\.venv\Scripts\python.exe scripts\generate_audit_layer.py L01_universe
```

## 스택

| 영역 | 기술 |
|------|------|
| Web | Next.js 15 + TS (`apps/web`) |
| API | FastAPI (`apps/api`) |
| DB | Supabase PostgreSQL |
| Config | `config/*.yaml` (비-secret) |
