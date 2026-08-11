-- ER2-P0-01 frozen_context immutability
-- ER2-P1-02 final_selector gate type
-- ER2-P1-03 recorded governance evaluations

create or replace function public.forbid_multi_agent_context_mutation()
returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'multi_agent_runs are immutable (delete forbidden)';
  end if;
  if new.frozen_context is distinct from old.frozen_context
     or new.context_hash is distinct from old.context_hash
     or new.union_id is distinct from old.union_id
     or new.bottom_up_run_id is distinct from old.bottom_up_run_id
     or new.regime_id is distinct from old.regime_id
     or new.snapshot_id is distinct from old.snapshot_id
     or new.run_id is distinct from old.run_id
     or new.llm_profile_version is distinct from old.llm_profile_version
     or new.multi_agent_run_id is distinct from old.multi_agent_run_id then
    raise exception 'multi_agent frozen context/lineage columns are immutable';
  end if;
  return new;
end;
$$;

drop trigger if exists multi_agent_runs_freeze_context on public.multi_agent_runs;
create trigger multi_agent_runs_freeze_context
before update or delete on public.multi_agent_runs
for each row execute function public.forbid_multi_agent_context_mutation();

alter table public.agent_gates drop constraint if exists agent_gates_gate_type_check;
alter table public.agent_gates
  add constraint agent_gates_gate_type_check
  check (gate_type in ('research_qa', 'adversarial', 'final_selector'));

create table if not exists public.governance_evaluations (
  evaluation_id uuid primary key,
  eval_kind text not null check (eval_kind in ('replay', 'holdout')),
  evaluator_version text not null,
  artifact_type text not null,
  artifact_ref text not null,
  candidate_version text not null,
  dataset_id text not null,
  dataset_hash text not null,
  sample_count int not null,
  metrics jsonb not null,
  baseline jsonb,
  thresholds jsonb not null,
  status text not null check (status in ('PASS', 'FAIL')),
  output_hash text not null,
  generated_at timestamptz not null default now()
);

create index if not exists governance_evaluations_kind_idx
  on public.governance_evaluations (eval_kind, generated_at desc);

alter table public.change_proposals
  add column if not exists replay_evaluation_id uuid references public.governance_evaluations(evaluation_id);
alter table public.change_proposals
  add column if not exists holdout_evaluation_id uuid references public.governance_evaluations(evaluation_id);
