-- L02 daily market bars
create table if not exists public.daily_prices (
  security_id uuid not null references public.securities(security_id),
  trading_date date not null,
  open numeric not null,
  high numeric not null,
  low numeric not null,
  close numeric not null,
  adjusted_close numeric,
  volume numeric not null,
  currency text not null default 'USD',
  source_id uuid references public.sources(source_id),
  source_version text,
  collected_at timestamptz not null default now(),
  primary key (security_id, trading_date)
);

create index if not exists daily_prices_date_idx on public.daily_prices (trading_date);
