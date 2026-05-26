from datetime import datetime

from nautilus_research_os.replay import ReplayRules, TradeCandidate, generate_baseline_candidates, replay_candidates


def test_daily_gates_stop_after_first_win():
    result = replay_candidates(
        [
            TradeCandidate(datetime.fromisoformat("2026-01-02T09:30:00"), 2.0),
            TradeCandidate(datetime.fromisoformat("2026-01-02T10:30:00"), -1.0),
        ]
    )

    assert [trade.r_multiple for trade in result.trades] == [2.0]
    assert result.trades[0].sequence_in_day == 1


def test_daily_gates_allow_second_trade_after_first_loss_then_stop_at_two():
    result = replay_candidates(
        [
            TradeCandidate(datetime.fromisoformat("2026-01-02T09:30:00"), -1.0),
            TradeCandidate(datetime.fromisoformat("2026-01-02T10:30:00"), 2.0),
            TradeCandidate(datetime.fromisoformat("2026-01-02T11:30:00"), 2.0),
        ]
    )

    assert [trade.r_multiple for trade in result.trades] == [-1.0, 2.0]
    assert [trade.sequence_in_day for trade in result.trades] == [1, 2]


def test_rules_can_disable_second_trade_after_loss():
    result = replay_candidates(
        [
            TradeCandidate(datetime.fromisoformat("2026-01-02T09:30:00"), -1.0),
            TradeCandidate(datetime.fromisoformat("2026-01-02T10:30:00"), 2.0),
        ],
        ReplayRules(allow_second_trade_after_loss=False),
    )

    assert [trade.r_multiple for trade in result.trades] == [-1.0]


def test_baseline_fixture_approximates_supplied_replay_stats():
    result = replay_candidates(generate_baseline_candidates())
    metrics = result.metrics

    assert metrics.trade_count == 231
    assert metrics.win_count == 139
    assert metrics.loss_count == 92
    assert metrics.win_rate == 0.6017
    assert metrics.total_r == 186.85
    assert metrics.avg_win_r == 2.0
    assert metrics.avg_loss_r == -0.9908
    assert metrics.profit_factor == 3.0499
    assert metrics.max_consecutive_losses == 4
    assert 5.9 <= metrics.sharpe <= 6.1
