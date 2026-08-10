-- L03 SEC facts (immutable inserts by fact_id)
create table if not exists public.financial_facts (
  fact_id uuid primary key,
  company_id uuid not null references public.companies(company_id),
  metric_key text not null,
  value numeric not null,
  unit text,
  currency text,
  fiscal_year int,
  fiscal_quarter text,
  period_end date not null,
  form_type text,
  filed_at date,
  published_at date,
  source_id uuid references public.sources(source_id),
  source_version text,
  accn text,
  created_at timestamptz not null default now()
);

create index if not exists financial_facts_company_metric_idx
  on public.financial_facts (company_id, metric_key, period_end);
