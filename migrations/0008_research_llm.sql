-- L07 research packets + LLM execution + AI research
create table if not exists public.research_packets (
  packet_id uuid primary key,
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid not null references public.securities(security_id),
  snapshot_id uuid not null references public.snapshots(snapshot_id),
  packet_schema_version text not null,
  packet_version text not null,
  input_hash text not null,
  payload_json jsonb not null,
  created_at timestamptz not null default now(),
  unique (run_id, security_id, packet_version)
);

create table if not exists public.llm_executions (
  execution_id uuid primary key,
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid references public.securities(security_id),
  agent_role text not null,
  prompt_version text not null,
  llm_profile_version text not null,
  requested_model text not null,
  resolved_model text,
  reasoning_effort text not null,
  response_id text,
  input_hash text not null,
  output_hash text,
  schema_version text not null,
  status text not null,
  token_usage jsonb,
  estimated_cost numeric,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  error_code text
);

create table if not exists public.ai_research (
  research_id uuid primary key,
  execution_id uuid not null references public.llm_executions(execution_id),
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid not null references public.securities(security_id),
  output_json jsonb not null,
  output_hash text not null,
  created_at timestamptz not null default now()
);
