-- M05 error database
create table if not exists public.error_events (
  error_id uuid primary key,
  error_type text not null,
  severity text not null check (severity in ('P0', 'P1', 'P2', 'P3')),
  summary text not null,
  details jsonb not null default '{}'::jsonb,
  run_id uuid references public.research_runs(run_id),
  judgment_id uuid references public.judgments(judgment_id),
  security_id uuid references public.securities(security_id),
  performance_eval_id uuid references public.performance_evals(eval_id),
  taxonomy_version text not null,
  created_at timestamptz not null default now()
);

create index if not exists error_events_type_idx on public.error_events (error_type, created_at desc);
create index if not exists error_events_judgment_idx on public.error_events (judgment_id);
