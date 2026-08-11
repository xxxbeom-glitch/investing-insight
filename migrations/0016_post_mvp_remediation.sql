-- Post-MVP external review remediation (ER-P0-01, ER-P1-03, ER-P1-05, M02 unit)

alter table public.snapshots
  add column if not exists sealed boolean not null default false;

-- Seal existing rows
update public.snapshots set sealed = true where sealed = false;

create or replace function public.forbid_snapshot_items_mutation()
returns trigger language plpgsql as $$
begin
  raise exception 'snapshot_items are immutable after snapshot seal';
end;
$$;

drop trigger if exists snapshot_items_no_update on public.snapshot_items;
create trigger snapshot_items_no_update
before update or delete on public.snapshot_items
for each row execute function public.forbid_snapshot_items_mutation();

create or replace function public.forbid_snapshot_items_late_insert()
returns trigger language plpgsql as $$
declare
  is_sealed boolean;
begin
  select sealed into is_sealed from public.snapshots where snapshot_id = new.snapshot_id;
  if coalesce(is_sealed, false) then
    raise exception 'snapshot_items late insert forbidden (snapshot already sealed)';
  end if;
  return new;
end;
$$;

drop trigger if exists snapshot_items_no_late_insert on public.snapshot_items;
create trigger snapshot_items_no_late_insert
before insert on public.snapshot_items
for each row execute function public.forbid_snapshot_items_late_insert();

alter table public.multi_agent_runs
  add column if not exists context_hash text;

alter table public.macro_observations
  add column if not exists value_unit text;

alter table public.judgments
  alter column qa_id drop not null;
alter table public.judgments
  alter column final_execution_id drop not null;
alter table public.judgments
  add column if not exists multi_agent_run_id uuid references public.multi_agent_runs(multi_agent_run_id);
alter table public.judgments
  add column if not exists source_agent_output_id uuid;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'judgments_lineage_chk'
  ) then
    alter table public.judgments
      add constraint judgments_lineage_chk check (
        (qa_id is not null and final_execution_id is not null)
        or (multi_agent_run_id is not null and source_agent_output_id is not null)
      );
  end if;
end $$;

alter table public.change_proposals
  add column if not exists replay_eval jsonb;
alter table public.change_proposals
  add column if not exists holdout_eval jsonb;
alter table public.change_proposals
  add column if not exists replay_status text;
alter table public.change_proposals
  add column if not exists holdout_status text;
