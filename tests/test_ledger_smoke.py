from nautilus_research_os.cli import smoke_paper


def test_smoke_paper_records_minimum_live_paper_spine(tmp_path):
    result = smoke_paper(str(tmp_path / "ledger.sqlite3"))

    assert result["session_id"]
    assert result["order_id"]
    assert result["fill_id"]
    assert result["counts"] == {
        "paper_sessions": 1,
        "paper_orders": 1,
        "paper_fills": 1,
        "paper_positions": 1,
        "paper_risk_events": 0,
        "agent_notes": 1,
    }
