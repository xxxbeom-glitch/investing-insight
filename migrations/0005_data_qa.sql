-- L04 quarantine / validated markers
create table if not exists public.data_quarantine (
  quarantine_id uuid primary key default gen_random_uuid(),
  entity_type text not null,
  entity_ref text not null,
  reason text not null,
  payload jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.data_quality_checks (
  check_id uuid primary key default gen_random_uuid(),
  dataset text not null,
  check_name text not null,
  status text not null,
  details jsonb,
  ran_at timestamptz not null default now()
);
