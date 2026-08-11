-- M06 V1→V2 governance
create table if not exists public.change_proposals (
  proposal_id uuid primary key,
  artifact_type text not null check (artifact_type in (
    'score_rule', 'prompt', 'model', 'llm_profile', 'quant_rule', 'other'
  )),
  artifact_ref text not null,
  from_version text,
  to_version text not null,
  rationale text not null,
  replay_notes text,
  holdout_notes text,
  status text not null check (status in (
    'draft', 'proposed', 'approved', 'rejected', 'frozen'
  )),
  approval_log jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists change_proposals_status_idx
  on public.change_proposals (status, created_at desc);
