-- M03 multi-agent binding + role outputs + gates
create table if not exists public.multi_agent_runs (
  multi_agent_run_id uuid primary key,
  run_id uuid not null references public.research_runs(run_id),
  snapshot_id uuid not null references public.snapshots(snapshot_id),
  union_id uuid,
  bottom_up_run_id uuid,
  regime_id uuid,
  llm_profile_version text not null,
  frozen_context jsonb not null,
  status text not null check (status in ('running', 'blocked', 'completed', 'failed')),
  block_reason text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists multi_agent_runs_snapshot_idx
  on public.multi_agent_runs (snapshot_id);

create table if not exists public.agent_outputs (
  output_id uuid primary key,
  multi_agent_run_id uuid not null references public.multi_agent_runs(multi_agent_run_id),
  run_id uuid not null references public.research_runs(run_id),
  snapshot_id uuid not null references public.snapshots(snapshot_id),
  security_id uuid references public.securities(security_id),
  agent_role text not null,
  execution_id uuid references public.llm_executions(execution_id),
  schema_version text not null,
  input_hash text not null,
  output_json jsonb not null,
  output_hash text not null,
  created_at timestamptz not null default now(),
  unique (multi_agent_run_id, agent_role, security_id)
);

create index if not exists agent_outputs_run_role_idx
  on public.agent_outputs (multi_agent_run_id, agent_role);

create table if not exists public.agent_gates (
  gate_id uuid primary key,
  multi_agent_run_id uuid not null references public.multi_agent_runs(multi_agent_run_id),
  gate_type text not null check (gate_type in ('research_qa', 'adversarial')),
  status text not null check (status in ('PASS', 'FAIL')),
  reasons jsonb not null default '[]'::jsonb,
  source_output_id uuid references public.agent_outputs(output_id),
  created_at timestamptz not null default now()
);
