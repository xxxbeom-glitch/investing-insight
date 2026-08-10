-- L01 identity & universe registry
create extension if not exists pgcrypto;

create table if not exists public.companies (
  company_id uuid primary key,
  legal_name text not null,
  country_of_incorporation text,
  sec_cik text,
  active_status boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists companies_sec_cik_uq
  on public.companies (sec_cik) where sec_cik is not null;

create table if not exists public.securities (
  security_id uuid primary key,
  company_id uuid not null references public.companies(company_id),
  ticker text not null,
  exchange text not null,
  security_type text not null,
  is_adr boolean not null default false,
  active_from date,
  active_to date,
  provider_ticker text,
  composite_figi text,
  share_class_figi text,
  locale text,
  currency_name text,
  active_status boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists securities_exchange_ticker_uq
  on public.securities (exchange, ticker);

create table if not exists public.sources (
  source_id uuid primary key,
  provider text not null,
  source_type text not null,
  external_id text,
  source_uri text,
  published_at timestamptz,
  collected_at timestamptz not null default now(),
  raw_hash text not null,
  storage_path text,
  created_at timestamptz not null default now()
);

create unique index if not exists sources_provider_hash_uq
  on public.sources (provider, raw_hash);

create table if not exists public.universe_memberships (
  membership_id uuid primary key default gen_random_uuid(),
  security_id uuid not null references public.securities(security_id),
  universe_name text not null,
  included boolean not null,
  inclusion_reason text,
  exclusion_reason text,
  valid_from timestamptz not null default now(),
  valid_to timestamptz,
  evaluated_at timestamptz not null default now(),
  rule_version text not null,
  source_id uuid references public.sources(source_id)
);

create index if not exists universe_memberships_security_idx
  on public.universe_memberships (security_id, universe_name, evaluated_at desc);
