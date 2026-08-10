-- M01 ops job ledger (scheduler dead-letter / audit)
create table if not exists public.ops_jobs (
  job_id uuid primary key,
  job_type text not null,
  stage text not null,
  status text not null check (status in ('running', 'success', 'failed', 'dead_letter')),
  error_code text,
  error_message text,
  retry_count int not null default 0,
  payload jsonb not null default '{}'::jsonb,
  result jsonb not null default '{}'::jsonb,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists ops_jobs_type_started_idx on public.ops_jobs (job_type, started_at desc);
create index if not exists ops_jobs_status_idx on public.ops_jobs (status);
