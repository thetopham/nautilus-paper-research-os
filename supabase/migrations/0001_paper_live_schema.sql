-- Nautilus Paper Research OS v1 schema seed.
-- Designed for Supabase/Postgres; local development uses an equivalent SQLite schema.

create table if not exists paper_sessions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  strategy_name text not null,
  strategy_version text,
  instrument_id text not null,
  venue text,
  status text not null check (status in ('pending', 'running', 'paused', 'stopped', 'failed')) default 'pending',
  config jsonb not null default '{}',
  started_at timestamptz,
  stopped_at timestamptz,
  stop_reason text
);

create table if not exists paper_orders (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  session_id uuid references paper_sessions(id),
  ts_event timestamptz not null,
  client_order_id text not null,
  instrument_id text not null,
  side text not null check (side in ('buy', 'sell')),
  order_type text not null,
  quantity numeric not null,
  limit_price numeric,
  status text not null,
  strategy_reason text,
  payload jsonb not null default '{}'
);

create table if not exists paper_fills (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  session_id uuid references paper_sessions(id),
  order_id uuid references paper_orders(id),
  ts_event timestamptz not null,
  instrument_id text not null,
  side text not null check (side in ('buy', 'sell')),
  quantity numeric not null,
  price numeric not null,
  fee numeric not null default 0,
  slippage_bps numeric,
  fill_model text not null,
  payload jsonb not null default '{}'
);

create table if not exists paper_positions (
  id uuid primary key default gen_random_uuid(),
  updated_at timestamptz not null default now(),
  session_id uuid references paper_sessions(id),
  instrument_id text not null,
  quantity numeric not null,
  avg_entry_price numeric,
  mark_price numeric,
  unrealized_pnl numeric,
  realized_pnl numeric not null default 0,
  payload jsonb not null default '{}',
  unique (session_id, instrument_id)
);

create table if not exists paper_risk_events (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  session_id uuid references paper_sessions(id),
  severity text not null check (severity in ('info', 'warning', 'critical')),
  event_type text not null,
  message text not null,
  payload jsonb not null default '{}'
);

create table if not exists agent_notes (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  session_id uuid references paper_sessions(id),
  agent_name text not null default 'hermes',
  note_type text not null,
  content text not null,
  metadata jsonb not null default '{}'
);
