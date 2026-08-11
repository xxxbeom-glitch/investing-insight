# Grounding eval harness (standalone)

A+D: pytest / M03–M06 / production agents에 연결하지 않는다.
GO/NO-GO, tag, cron을 바꾸지 않는다. FAIL이면 exit 1 + report만.

## Commands

```powershell
# Phase 1 — deterministic ER7–ER11 replay (no API)
.\apps\api\.venv\Scripts\python.exe scripts\evals\grounding\runner.py --replay-only

# Phase 2 — replay PASS 후 Red-Team + Judge (OPENAI_API_KEY in .env.local)
.\apps\api\.venv\Scripts\python.exe scripts\evals\grounding\runner.py --llm
```

External re-review bundle **직전** 루프:

```powershell
.\apps\api\.venv\Scripts\python.exe scripts\evals\grounding\self_remediate.py
```

- 내부: pytest → secret_scan → web build → replay → `--llm`
- max 3 attempts (`config/evals/grounding.yaml` `loop.max_attempts`)
- 같은 FP fingerprint 반복 → exit 2, 사람 보고
- FP 시 읽을 파일: `scripts/evals/grounding/out/report.json`
- exit 0 전에 M03~M06 / bundle 금지. GO/tag/cron 변경 금지.

Reports: `scripts/evals/grounding/out/` (gitignore `out/`). 키·raw reasoning 없음.

## FP gate

positive = `claim_is_supported` → SUPPORTED.

Judge=UNSUPPORTED / Gate=SUPPORTED → FALSE POSITIVE → exit 1.

Gate=UNSUPPORTED 공격은 Judge를 호출하지 않고 차단 성공(TN)으로 기록.

## Secrets

`.env.local`의 `OPENAI_API_KEY`만. fixture/report/bundle에 키를 넣지 말 것.
