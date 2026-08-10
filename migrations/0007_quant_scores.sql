-- L06 quant scores (deterministic, snapshot-bound)
create table if not exists public.quant_scores (
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid not null references public.securities(security_id),
  total_score numeric not null,
  growth_score numeric not null,
  quality_score numeric not null,
  cashflow_score numeric not null,
  health_score numeric not null,
  valuation_score numeric not null,
  momentum_score numeric not null,
  peer_group text,
  rank_market int,
  rank_peer int,
  rule_version text not null,
  input_hash text not null,
  missing_components jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  primary key (run_id, security_id)
);

create index if not exists quant_scores_run_rank_idx
  on public.quant_scores (run_id, rank_market);
