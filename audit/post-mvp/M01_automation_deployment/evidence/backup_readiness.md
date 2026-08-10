# Backup Readiness (Supabase Free / dump+restore)

Status: PASS

- Automatic Backup/PITR: unavailable on Free (not faked)
- Method: logical COPY dump → verify → restore drill → DROP
- Production schedulers: DISABLED

- generated_at: 2026-08-10T22:48:44.104215+00:00
- db_hostname: aws-0-ap-northeast-1.pooler.supabase.com
- dump_sha256: 5319e5d487958ca2c34ea34d02a2b13fdcc67bc6240a7ced5c4f72bf20c79398
- dump_bytes: 35267576
- verify_ok: True
- restore_ok: True
- scheduler_enable_allowed: false

Dump files: `storage/backups/` (gitignored). Never commit dumps or DB URLs.
