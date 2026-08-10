-- L00 bootstrap metadata (idempotent)
create table if not exists public.app_bootstrap (
  id bigserial primary key,
  key text not null unique,
  value text not null,
  created_at timestamptz not null default now()
);

insert into public.app_bootstrap (key, value)
values ('schema_bootstrap', 'l00')
on conflict (key) do update set value = excluded.value;

create table if not exists public.schema_migrations (
  id text primary key,
  applied_at timestamptz not null default now()
);
