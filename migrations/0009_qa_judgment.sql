-- L08 research QA + immutable judgments
create table if not exists public.research_qa (
  qa_id uuid primary key,
  execution_id uuid not null references public.llm_executions(execution_id),
  research_id uuid not null references public.ai_research(research_id),
  status text not null,
  failed_claims jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  output_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.judgments (
  judgment_id uuid primary key,
  run_id uuid not null references public.research_runs(run_id),
  security_id uuid not null references public.securities(security_id),
  status text not null,
  selection_price numeric,
  quant_score numeric,
  thesis text not null,
  bear_case jsonb not null,
  risks jsonb not null,
  invalidation_conditions jsonb not null,
  evidence_quality text not null,
  data_completeness numeric not null,
  uncertainty text not null,
  final_execution_id uuid not null references public.llm_executions(execution_id),
  qa_id uuid not null references public.research_qa(qa_id),
  output_json jsonb not null,
  immutable_hash text not null,
  created_at timestamptz not null default now(),
  unique (run_id, security_id, immutable_hash)
);

-- prevent overwrite of a judgment row (insert-only semantics enforced in app + no update grants expected)
create or replace function public.forbid_judgment_update()
returns trigger language plpgsql as $$
begin
  raise exception 'judgments are immutable';
end;
$$;

drop trigger if exists judgments_no_update on public.judgments;
create trigger judgments_no_update
before update on public.judgments
for each row execute function public.forbid_judgment_update();
