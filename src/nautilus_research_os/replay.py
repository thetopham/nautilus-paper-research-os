from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


@dataclass(frozen=True)
class TradeCandidate:
    """A strategy signal outcome expressed in R multiples before daily gates."""

    ts: datetime
    r_multiple: float
    setup: str = "baseline"

    @property
    def trade_date(self) -> date:
        return self.ts.date()


@dataclass(frozen=True)
class ExecutedTrade:
    ts: datetime
    trade_date: date
    sequence_in_day: int
    r_multiple: float
    setup: str

    @property
    def is_win(self) -> bool:
        return self.r_multiple > 0


@dataclass(frozen=True)
class ReplayRules:
    risk_fraction: float = 0.01
    max_trades_per_day: int = 2
    stop_after_first_win: bool = True
    allow_second_trade_after_loss: bool = True


@dataclass(frozen=True)
class ReplayMetrics:
    total_r: float
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    avg_trade_r: float
    profit_factor: float
    sharpe: float
    max_consecutive_losses: int
    max_drawdown_r: float


@dataclass(frozen=True)
class ReplayResult:
    rules: ReplayRules
    trades: list[ExecutedTrade]
    metrics: ReplayMetrics

    def to_dict(self) -> dict[str, object]:
        return {
            "rules": asdict(self.rules),
            "metrics": asdict(self.metrics),
            "trades": [
                {
                    "ts": t.ts.isoformat(),
                    "trade_date": t.trade_date.isoformat(),
                    "sequence_in_day": t.sequence_in_day,
                    "r_multiple": t.r_multiple,
                    "setup": t.setup,
                    "is_win": t.is_win,
                }
                for t in self.trades
            ],
        }


def apply_daily_gates(candidates: Iterable[TradeCandidate], rules: ReplayRules) -> list[ExecutedTrade]:
    """Apply the user's daily execution rules to ordered candidates.

    Rules modeled:
    - same model/setup can emit repeated candidates;
    - every trade risks 1R / 1% by default;
    - max two trades per day;
    - if the first trade wins, stop for the day;
    - if the first trade loses, allow another trade.
    """

    executed: list[ExecutedTrade] = []
    day_counts: defaultdict[date, int] = defaultdict(int)
    day_has_win: defaultdict[date, bool] = defaultdict(bool)

    for candidate in sorted(candidates, key=lambda item: item.ts):
        day = candidate.trade_date
        if day_counts[day] >= rules.max_trades_per_day:
            continue
        if rules.stop_after_first_win and day_has_win[day]:
            continue
        if day_counts[day] >= 1 and not rules.allow_second_trade_after_loss:
            continue

        sequence = day_counts[day] + 1
        trade = ExecutedTrade(
            ts=candidate.ts,
            trade_date=day,
            sequence_in_day=sequence,
            r_multiple=candidate.r_multiple,
            setup=candidate.setup,
        )
        executed.append(trade)
        day_counts[day] = sequence
        if trade.is_win:
            day_has_win[day] = True

    return executed


def calculate_metrics(trades: list[ExecutedTrade]) -> ReplayMetrics:
    values = [trade.r_multiple for trade in trades]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    total_r = sum(values)
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = math.inf if gross_loss == 0 and gross_profit > 0 else (gross_profit / gross_loss if gross_loss else 0.0)

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    max_consecutive_losses = 0
    current_losses = 0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        if value < 0:
            current_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
        else:
            current_losses = 0

    if len(values) > 1:
        sigma = pstdev(values)
        sharpe = 0.0 if sigma == 0 else mean(values) / sigma * math.sqrt(len(values))
    else:
        sharpe = 0.0

    return ReplayMetrics(
        total_r=round(total_r, 4),
        trade_count=len(values),
        win_count=len(wins),
        loss_count=len(losses),
        win_rate=round(len(wins) / len(values), 4) if values else 0.0,
        avg_win_r=round(mean(wins), 4) if wins else 0.0,
        avg_loss_r=round(mean(losses), 4) if losses else 0.0,
        avg_trade_r=round(mean(values), 4) if values else 0.0,
        profit_factor=round(profit_factor, 4) if math.isfinite(profit_factor) else math.inf,
        sharpe=round(sharpe, 4),
        max_consecutive_losses=max_consecutive_losses,
        max_drawdown_r=round(max_drawdown, 4),
    )


def replay_candidates(candidates: Iterable[TradeCandidate], rules: ReplayRules | None = None) -> ReplayResult:
    rules = rules or ReplayRules()
    trades = apply_daily_gates(candidates, rules)
    return ReplayResult(rules=rules, trades=trades, metrics=calculate_metrics(trades))


def load_candidates_csv(path: str | Path) -> list[TradeCandidate]:
    rows: list[TradeCandidate] = []
    with Path(path).open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                TradeCandidate(
                    ts=datetime.fromisoformat(row["ts"]),
                    r_multiple=float(row["r_multiple"]),
                    setup=row.get("setup") or "baseline",
                )
            )
    return rows


def write_result_json(result: ReplayResult, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")


def generate_baseline_candidates() -> list[TradeCandidate]:
    """Generate a deterministic candidate set approximating the supplied benchmark.

    Target benchmark supplied by the user:
    - +187R total
    - 231 trades
    - ~60% win rate
    - ~2R average winner
    - ~3.05 profit factor
    - ~6 Sharpe
    - 4 max consecutive losses

    This fixture is not market data. It is a reproducible acceptance fixture for the
    replay/risk-gating harness until a real Nautilus data source is wired in.
    """

    outcomes: list[float] = []
    wins_remaining = 139
    losses_remaining = 92

    # 127 regular winners plus 12 large winners keeps average winner at 2R.
    # 92 slightly-better-than--1R losses gives approximately:
    # net +187R, PF 3.05, and Sharpe ~6 for this finite sample.
    large_winners = 12
    large_win_r = 8.0
    regular_win_r = (278.0 - large_winners * large_win_r) / (139 - large_winners)
    loss_r = -91.15 / 92

    # Start with four losses to prove the max-consecutive-loss metric can catch the supplied limit.
    outcomes.extend([loss_r, loss_r, loss_r, loss_r])
    losses_remaining -= 4

    pattern = [regular_win_r, loss_r, regular_win_r, loss_r, regular_win_r]
    large_winners_remaining = large_winners
    while wins_remaining > large_winners_remaining or losses_remaining > 0:
        for value in pattern:
            if value > 0 and wins_remaining > large_winners_remaining:
                outcomes.append(value)
                wins_remaining -= 1
            elif value < 0 and losses_remaining > 0:
                outcomes.append(value)
                losses_remaining -= 1
            if wins_remaining <= large_winners_remaining and losses_remaining <= 0:
                break
    outcomes.extend([large_win_r] * large_winners_remaining)

    candidates: list[TradeCandidate] = []
    current_day = date(2026, 1, 2)
    for idx, value in enumerate(outcomes):
        # One candidate per day guarantees win-and-done never suppresses this fixture.
        ts = datetime.combine(current_day, datetime.min.time()).replace(hour=9, minute=30)
        candidates.append(TradeCandidate(ts=ts, r_multiple=value, setup="baseline_r_model"))
        current_day += timedelta(days=1)
    return candidates
