# Supabase PITR / Backup Confirmation (M01 AC-5)

Status: PENDING

## Instructions (operator)
1. Open Supabase project → Database → Backups / Point-in-time recovery.
2. Confirm daily backups or PITR is enabled.
3. Fill fields below (hostname only — **no passwords**).
4. Change Status line to: `Status: CONFIRMED`
5. Re-run: `python scripts/backup_supabase_check.py` (must exit 0).

## Record
- Project hostname (from SUPABASE_URL or DB host): 
- Backup / PITR enabled: yes/no
- Retention (days): 
- Confirmed by: 
- Confirmed at (UTC): 

## Scheduler gate
Production cron / Cloud Scheduler must stay **disabled** until Status is CONFIRMED.
