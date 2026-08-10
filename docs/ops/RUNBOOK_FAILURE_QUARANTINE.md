# Runbook — Failure / Quarantine / Retry

## Data path
`raw → normalized → validated → snapshot → quant → research`

## Quarantine
- Bad rows go to `data_quarantine` with reason; validated layer must not proceed with FAIL=0 violated.
- Operator: inspect quarantine, fix source/ingest, re-run QA runner.

## LLM fail-closed
- Unavailable / remapped model → `ModelUnavailableError` (no silent fallback).
- QA FAIL → cannot SELECTED (`JudgmentPolicyError`).

## Ingest failure (manual MVP / future scheduler)
1. Capture exit code + provider HTTP status (no API keys in logs).
2. Do not mark run `snapshot_ready` if upstream failed.
3. Re-run idempotent ingest after cooldown (Massive 429 → respect throttle).

## Dead-letter (M1 requirement)
When schedulers land: failed jobs must persist job_id, stage, error_code, retry_count; infinite silent retry forbidden.
