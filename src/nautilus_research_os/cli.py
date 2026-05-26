from __future__ import annotations

import argparse
import json
from pathlib import Path

from nautilus_trader.model.objects import Price, Quantity

from .ledger import SQLiteLedger
from .replay import generate_baseline_candidates, load_candidates_csv, replay_candidates, write_result_json

DEFAULT_PAPER_CONFIG = {
    "paper": {
        "starting_cash": 100000,
        "max_position_notional": 5000,
        "max_total_exposure": 15000,
        "max_daily_drawdown": 1000,
        "max_orders_per_hour": 20,
        "max_open_positions": 5,
        "stale_feed_seconds": 30,
        "allow_short": False,
        "allow_leverage": False,
    }
}


def smoke_paper(db_path: str) -> dict[str, object]:
    ledger = SQLiteLedger(db_path)
    try:
        ledger.init_schema()
        # Touch Nautilus domain objects now so the CLI proves the installed engine is importable.
        entry_price = Price.from_str("100.25")
        quantity = Quantity.from_str("1.5")

        session = ledger.create_session(
            strategy_name="smoke_momentum_v0",
            strategy_version="0.1.0",
            instrument_id="BTCUSDT-PERP.TEST",
            venue="SIM",
            config=DEFAULT_PAPER_CONFIG,
        )
        order_id = ledger.record_order(
            session_id=session.id,
            instrument_id=session.instrument_id,
            side="buy",
            order_type="market",
            quantity=float(str(quantity)),
            status="filled",
            strategy_reason="smoke test controlled entry",
            payload={"nautilus_price_repr": str(entry_price), "boundary": "paper_live_internal_only"},
        )
        fill_id = ledger.record_fill(
            session_id=session.id,
            order_id=order_id,
            instrument_id=session.instrument_id,
            side="buy",
            quantity=float(str(quantity)),
            price=float(str(entry_price)),
            fill_model="next_tick_mid_smoke",
            slippage_bps=0,
            payload={"reference_price": float(str(entry_price)), "liquidity_assumption": "smoke_test"},
        )
        ledger.upsert_position(
            session_id=session.id,
            instrument_id=session.instrument_id,
            quantity=float(str(quantity)),
            avg_entry_price=float(str(entry_price)),
            mark_price=101.00,
            unrealized_pnl=(101.00 - float(str(entry_price))) * float(str(quantity)),
            payload={"source": "smoke_test"},
        )
        ledger.add_agent_note(
            session_id=session.id,
            note_type="paper_session_review",
            content="Smoke paper session verified: one internal paper order, fill, and position were recorded. No real broker/live order path used.",
            metadata={"safety_boundary": "paper_live_internal_only"},
        )
        return {"db": str(Path(db_path).resolve()), "session_id": session.id, "order_id": order_id, "fill_id": fill_id, "counts": ledger.counts()}
    finally:
        ledger.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="npro")
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke-paper", help="Write one internal paper session/order/fill/position to the local ledger.")
    smoke.add_argument("--db", default=".local/ledger.sqlite3", help="SQLite ledger path for local development.")

    replay = subparsers.add_parser("replay-r", help="Replay R-multiple candidates with daily paper-risk gates.")
    replay.add_argument("--input-csv", help="CSV with ts,r_multiple,setup columns. If omitted, uses the baseline fixture.")
    replay.add_argument("--output-json", default="runs/basic-r-replay/result.json", help="Where to write replay JSON output.")

    args = parser.parse_args(argv)
    if args.command == "smoke-paper":
        print(json.dumps(smoke_paper(args.db), indent=2, sort_keys=True))
        return 0
    if args.command == "replay-r":
        candidates = load_candidates_csv(args.input_csv) if args.input_csv else generate_baseline_candidates()
        result = replay_candidates(candidates)
        write_result_json(result, args.output_json)
        print(json.dumps({"output_json": str(Path(args.output_json).resolve()), "metrics": result.to_dict()["metrics"]}, indent=2, sort_keys=True))
        return 0
    raise AssertionError(f"Unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
