# Nautilus Paper Research OS

Replay-first, paper-live trading research system.

## Safety boundary

- Supports: replay, internal live-paper simulation, local ledger, dashboard hooks.
- Explicitly out of scope for v1: real-money orders, live broker endpoints, private-key custody, autonomous live promotion.

## V1 spine

1. Start a paper session from CLI.
2. Record session/order/fill/position/risk events in a local append-first ledger.
3. Keep schema compatible with a later Supabase/Postgres backend.
4. Feed Perspective dashboard views from ledger tables.
5. Add Hermes research notes/review loop after the paper spine is stable.

## Bybit options direction

The Nautilus Bybit options tutorials are captured in `docs/bybit-options-path.md`. Treat them as architecture input for read-only options data, Greeks dashboards, and internal paper delta-neutral simulation. Do not run the live delta-neutral Bybit example as-is; it is mainnet-oriented and can submit hedge orders if credentials/existing positions are present.

## Interactive Brokers options direction

Because Bybit may not be available for US users, the likely US-compatible options path is Interactive Brokers. Notes are captured in `docs/interactive-brokers-options-path.md`. The current venv has `nautilus_trader[ib,docker]` installed, but v1 remains read-only data + internal paper simulation; no IB order submission path is enabled.

## Local commands

```bash
source /home/matt/venvs/nautilus-perspective/bin/activate
pip install -e '.[dev]'
npro smoke-paper --db ./.local/ledger.sqlite3
pytest -q
```
