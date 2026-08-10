-- L05 research runs + immutable snapshots
create table if not exists public.research_runs (
  run_id uuid primary key,
  status text not null,
  cutoff_at timestamptz not null,
  created_at timestamptz not null default now(),
  quant_rule_version text,
  prompt_bundle_version text,
  llm_profile_version text,
  code_commit_hash text,
  universe_rule_version text
);

create table if not exists public.snapshots (
  snapshot_id uuid primary key,
  run_id uuid not null references public.research_runs(run_id),
  cutoff_at timestamptz not null,
  content_hash text not null,
  manifest jsonb not null,
  created_at timestamptz not null default now(),
  unique (run_id)
);

create table if not exists public.snapshot_items (
  snapshot_id uuid not null references public.snapshots(snapshot_id),
  item_type text not null,
  item_ref text not null,
  payload jsonb not null,
  source_ids jsonb,
  primary key (snapshot_id, item_type, item_ref)
);
