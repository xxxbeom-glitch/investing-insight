-- M04 performance tracking
create table if not exists public.performance_evals (
  eval_id uuid primary key,
  judgment_id uuid not null references public.judgments(judgment_id),
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid not null references public.securities(security_id),
  judgment_status text not null,
  cohort text not null,
  as_of_date date not null,
  horizon text not null,
  trading_days int not null,
  entry_date date,
  exit_date date,
  entry_price double precision,
  exit_price double precision,
  abs_return double precision,
  spy_return double precision,
  qqq_return double precision,
  rel_spy double precision,
  rel_qqq double precision,
  price_outcome text,
  thesis_correctness text,
  status text not null check (status in ('COMPLETE', 'INCOMPLETE')),
  incomplete_reason text,
  rule_version text not null,
  created_at timestamptz not null default now(),
  unique (judgment_id, horizon, as_of_date)
);

create index if not exists performance_evals_run_idx
  on public.performance_evals (run_id, horizon);

create index if not exists performance_evals_cohort_idx
  on public.performance_evals (cohort, horizon);
