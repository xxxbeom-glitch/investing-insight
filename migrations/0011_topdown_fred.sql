-- M02 Top-down / FRED tables
create table if not exists public.macro_observations (
  observation_id uuid primary key,
  provider text not null,
  series_id text not null,
  role text,
  observation_date date not null,
  value double precision,
  collected_at timestamptz not null default now(),
  source_id uuid references public.sources(source_id),
  config_version text not null,
  unique (provider, series_id, observation_date)
);

create index if not exists macro_observations_series_date_idx
  on public.macro_observations (series_id, observation_date desc);

create table if not exists public.market_regimes (
  regime_id uuid primary key,
  as_of date not null,
  regime text not null,
  inputs jsonb not null default '{}'::jsonb,
  rule_version text not null,
  created_at timestamptz not null default now()
);

create index if not exists market_regimes_as_of_idx
  on public.market_regimes (as_of desc);

create table if not exists public.industry_assessments (
  assessment_id uuid primary key,
  industry_id text not null,
  as_of date not null,
  regime_id uuid references public.market_regimes(regime_id),
  demand_score double precision not null,
  capex_score double precision not null,
  supply_score double precision not null,
  pricing_score double precision not null,
  margin_score double precision not null,
  bottleneck_score double precision not null,
  overall_score double precision not null,
  details jsonb not null default '{}'::jsonb,
  rule_version text not null,
  created_at timestamptz not null default now()
);

create index if not exists industry_assessments_industry_as_of_idx
  on public.industry_assessments (industry_id, as_of desc);

create table if not exists public.industry_qa (
  qa_id uuid primary key,
  assessment_id uuid not null references public.industry_assessments(assessment_id),
  status text not null check (status in ('PASS', 'FAIL')),
  reasons jsonb not null default '[]'::jsonb,
  rule_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.value_chain_snapshots (
  snapshot_id uuid primary key,
  industry_id text not null,
  config_version text not null,
  nodes jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.topdown_candidates (
  candidate_id uuid primary key,
  assessment_id uuid not null references public.industry_assessments(assessment_id),
  industry_id text not null,
  ticker text not null,
  node_id text,
  security_id uuid references public.securities(security_id),
  qa_status text not null,
  created_at timestamptz not null default now()
);

create index if not exists topdown_candidates_assessment_idx
  on public.topdown_candidates (assessment_id);

create table if not exists public.shortlist_unions (
  union_id uuid primary key,
  as_of date not null,
  topdown_assessment_ids uuid[] not null default '{}',
  bottom_up_run_id uuid,
  members jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
