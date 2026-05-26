from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


SQLITE_SCHEMA = """
create table if not exists paper_sessions (
  id text primary key,
  created_at text not null,
  strategy_name text not null,
  strategy_version text,
  instrument_id text not null,
  venue text,
  status text not null check (status in ('pending', 'running', 'paused', 'stopped', 'failed')) default 'pending',
  config text not null default '{}',
  started_at text,
  stopped_at text,
  stop_reason text
);

create table if not exists paper_orders (
  id text primary key,
  created_at text not null,
  session_id text references paper_sessions(id),
  ts_event text not null,
  client_order_id text not null,
  instrument_id text not null,
  side text not null check (side in ('buy', 'sell')),
  order_type text not null,
  quantity real not null,
  limit_price real,
  status text not null,
  strategy_reason text,
  payload text not null default '{}'
);

create table if not exists paper_fills (
  id text primary key,
  created_at text not null,
  session_id text references paper_sessions(id),
  order_id text references paper_orders(id),
  ts_event text not null,
  instrument_id text not null,
  side text not null check (side in ('buy', 'sell')),
  quantity real not null,
  price real not null,
  fee real not null default 0,
  slippage_bps real,
  fill_model text not null,
  payload text not null default '{}'
);

create table if not exists paper_positions (
  id text primary key,
  updated_at text not null,
  session_id text references paper_sessions(id),
  instrument_id text not null,
  quantity real not null,
  avg_entry_price real,
  mark_price real,
  unrealized_pnl real,
  realized_pnl real not null default 0,
  payload text not null default '{}',
  unique (session_id, instrument_id)
);

create table if not exists paper_risk_events (
  id text primary key,
  created_at text not null,
  session_id text references paper_sessions(id),
  severity text not null check (severity in ('info', 'warning', 'critical')),
  event_type text not null,
  message text not null,
  payload text not null default '{}'
);

create table if not exists agent_notes (
  id text primary key,
  created_at text not null,
  session_id text references paper_sessions(id),
  agent_name text not null default 'hermes',
  note_type text not null,
  content text not null,
  metadata text not null default '{}'
);
"""


@dataclass(frozen=True)
class PaperSession:
    id: str
    strategy_name: str
    instrument_id: str
    status: str


class SQLiteLedger:
    """Small local ledger matching the future Supabase paper-live shape."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("pragma foreign_keys = on")

    def close(self) -> None:
        self.conn.close()

    def init_schema(self) -> None:
        self.conn.executescript(SQLITE_SCHEMA)
        self.conn.commit()

    def create_session(
        self,
        *,
        strategy_name: str,
        instrument_id: str,
        venue: str,
        config: dict[str, Any],
        strategy_version: str | None = None,
    ) -> PaperSession:
        session_id = new_id()
        now = utc_now()
        self.conn.execute(
            """
            insert into paper_sessions (
              id, created_at, strategy_name, strategy_version, instrument_id, venue,
              status, config, started_at
            ) values (?, ?, ?, ?, ?, ?, 'running', ?, ?)
            """,
            (session_id, now, strategy_name, strategy_version, instrument_id, venue, json.dumps(config), now),
        )
        self.conn.commit()
        return PaperSession(id=session_id, strategy_name=strategy_name, instrument_id=instrument_id, status="running")

    def record_order(
        self,
        *,
        session_id: str,
        instrument_id: str,
        side: str,
        order_type: str,
        quantity: float,
        status: str,
        strategy_reason: str,
        limit_price: float | None = None,
        payload: dict[str, Any] | None = None,
        client_order_id: str | None = None,
        ts_event: str | None = None,
    ) -> str:
        order_id = new_id()
        self.conn.execute(
            """
            insert into paper_orders (
              id, created_at, session_id, ts_event, client_order_id, instrument_id,
              side, order_type, quantity, limit_price, status, strategy_reason, payload
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                utc_now(),
                session_id,
                ts_event or utc_now(),
                client_order_id or f"paper-{order_id}",
                instrument_id,
                side,
                order_type,
                quantity,
                limit_price,
                status,
                strategy_reason,
                json.dumps(payload or {}),
            ),
        )
        self.conn.commit()
        return order_id

    def record_fill(
        self,
        *,
        session_id: str,
        order_id: str,
        instrument_id: str,
        side: str,
        quantity: float,
        price: float,
        fill_model: str,
        fee: float = 0,
        slippage_bps: float | None = None,
        payload: dict[str, Any] | None = None,
        ts_event: str | None = None,
    ) -> str:
        fill_id = new_id()
        self.conn.execute(
            """
            insert into paper_fills (
              id, created_at, session_id, order_id, ts_event, instrument_id,
              side, quantity, price, fee, slippage_bps, fill_model, payload
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fill_id,
                utc_now(),
                session_id,
                order_id,
                ts_event or utc_now(),
                instrument_id,
                side,
                quantity,
                price,
                fee,
                slippage_bps,
                fill_model,
                json.dumps(payload or {}),
            ),
        )
        self.conn.commit()
        return fill_id

    def upsert_position(
        self,
        *,
        session_id: str,
        instrument_id: str,
        quantity: float,
        avg_entry_price: float,
        mark_price: float,
        unrealized_pnl: float,
        realized_pnl: float = 0,
        payload: dict[str, Any] | None = None,
    ) -> str:
        row = self.conn.execute(
            "select id from paper_positions where session_id = ? and instrument_id = ?",
            (session_id, instrument_id),
        ).fetchone()
        position_id = row["id"] if row else new_id()
        self.conn.execute(
            """
            insert into paper_positions (
              id, updated_at, session_id, instrument_id, quantity, avg_entry_price,
              mark_price, unrealized_pnl, realized_pnl, payload
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(session_id, instrument_id) do update set
              updated_at = excluded.updated_at,
              quantity = excluded.quantity,
              avg_entry_price = excluded.avg_entry_price,
              mark_price = excluded.mark_price,
              unrealized_pnl = excluded.unrealized_pnl,
              realized_pnl = excluded.realized_pnl,
              payload = excluded.payload
            """,
            (
                position_id,
                utc_now(),
                session_id,
                instrument_id,
                quantity,
                avg_entry_price,
                mark_price,
                unrealized_pnl,
                realized_pnl,
                json.dumps(payload or {}),
            ),
        )
        self.conn.commit()
        return position_id

    def add_agent_note(self, *, session_id: str, note_type: str, content: str, metadata: dict[str, Any] | None = None) -> str:
        note_id = new_id()
        self.conn.execute(
            """
            insert into agent_notes (id, created_at, session_id, agent_name, note_type, content, metadata)
            values (?, ?, ?, 'hermes', ?, ?, ?)
            """,
            (note_id, utc_now(), session_id, note_type, content, json.dumps(metadata or {})),
        )
        self.conn.commit()
        return note_id

    def counts(self) -> dict[str, int]:
        tables = ["paper_sessions", "paper_orders", "paper_fills", "paper_positions", "paper_risk_events", "agent_notes"]
        return {table: int(self.conn.execute(f"select count(*) from {table}").fetchone()[0]) for table in tables}
