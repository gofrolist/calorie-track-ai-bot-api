create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  telegram_id bigint unique,
  handle text,
  locale text,
  created_at timestamptz default now()
);

create table if not exists photos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  tigris_key text not null,
  status text not null default 'uploaded',
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists estimates (
  id uuid primary key default gen_random_uuid(),
  photo_id uuid references photos(id) on delete cascade,
  kcal_mean numeric,
  kcal_min numeric,
  kcal_max numeric,
  items jsonb,
  confidence numeric,
  status text default 'done',
  created_at timestamptz default now()
);

create table if not exists meals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  meal_date date not null,
  meal_type text not null,
  kcal_total numeric not null,
  source text not null,
  estimate_id uuid references estimates(id),
  created_at timestamptz default now()
);

create table if not exists goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  daily_kcal_target integer not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_photos_user_created on photos(user_id, created_at);
create index if not exists idx_meals_user_date on meals(user_id, meal_date);
create index if not exists idx_goals_user_id on goals(user_id);
