"""Tests for the aggregate CLV scoreboard (clv_report / the /clv route)."""

from __future__ import annotations

import csv

from app import main
from app.backtest.clv import clv_report
from fastapi.testclient import TestClient

PRED_FIELDS = [
    "date", "pitcher", "side", "line", "over_odds", "under_odds", "bet",
]
CLOSE_FIELDS = ["date", "captured_at", "tag", "pitcher", "line", "over_odds", "under_odds"]


def _write(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def test_clv_report_scores_flagged_bets_against_close(tmp_path):
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"

    # One flagged over bet we took at -110/-110; the market closed -130/+110,
    # i.e. the close implies a HIGHER over probability than we paid -> positive CLV.
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-20", "pitcher": "Gerrit Cole", "side": "over", "line": 6.5,
         "over_odds": -110, "under_odds": -110, "bet": "True"},
        # A non-bet row must be ignored entirely.
        {"date": "2026-06-20", "pitcher": "Some Body", "side": "over", "line": 6.5,
         "over_odds": -110, "under_odds": -110, "bet": "False"},
    ])
    _write(close, CLOSE_FIELDS, [
        # An open snapshot for the same pitcher must be filtered out by tag.
        {"date": "2026-06-20", "captured_at": "2026-06-20T15:00:00Z", "tag": "open",
         "pitcher": "Gerrit Cole", "line": 6.5, "over_odds": 100, "under_odds": -120},
        {"date": "2026-06-20", "captured_at": "2026-06-20T22:00:00Z", "tag": "close",
         "pitcher": "Gerrit Cole", "line": 6.5, "over_odds": -130, "under_odds": 110},
    ])

    rep = clv_report(str(pred), str(close))
    assert rep.n_bets == 1
    assert rep.n_unmatched == 0
    assert rep.n_unmeasurable == 0
    assert rep.mean_clv is not None and rep.mean_clv > 0  # bought below the close
    assert rep.pct_positive == 1.0
    assert rep.bets[0].beat_close is True


def test_clv_report_flags_line_move_as_unmeasurable(tmp_path):
    # We bet UNDER 5.5; the market closed at 4.5 (line moved a full K). Comparing
    # under-5.5 to under-4.5 is two different bets, so it must NOT be scored — it's
    # excluded as unmeasurable, not counted as a (misleading) negative CLV.
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-29", "pitcher": "Eduardo Rodriguez", "side": "under", "line": 5.5,
         "over_odds": 126, "under_odds": -162, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": "2026-06-29", "captured_at": "2026-06-29T22:50:00Z", "tag": "close",
         "pitcher": "Eduardo Rodriguez", "line": 4.5, "over_odds": -134, "under_odds": 105},
    ])
    rep = clv_report(str(pred), str(close))
    assert rep.n_bets == 0
    assert rep.n_unmatched == 0
    assert rep.n_unmeasurable == 1
    assert rep.mean_clv is None
    assert rep.unmeasurable[0].bet_line == 5.5
    assert rep.unmeasurable[0].close_line == 4.5
    assert "line moved" in rep.unmeasurable[0].reason


def test_clv_report_missing_line_is_unmeasurable(tmp_path):
    # A bet row with no line can't be confirmed to match the close -> unmeasurable.
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, ["date", "pitcher", "side", "over_odds", "under_odds", "bet"], [
        {"date": "2026-06-20", "pitcher": "Gerrit Cole", "side": "over",
         "over_odds": -110, "under_odds": -110, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": "2026-06-20", "captured_at": "2026-06-20T22:00:00Z", "tag": "close",
         "pitcher": "Gerrit Cole", "line": 6.5, "over_odds": -130, "under_odds": 110},
    ])
    rep = clv_report(str(pred), str(close))
    assert rep.n_bets == 0
    assert rep.n_unmeasurable == 1


def test_clv_report_counts_unmatched_when_no_close(tmp_path):
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-20", "pitcher": "Gerrit Cole", "side": "over", "line": 5.5,
         "over_odds": -110, "under_odds": -110, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": "2026-06-20", "captured_at": "2026-06-20T22:00:00Z", "tag": "close",
         "pitcher": "Different Pitcher", "line": 5.5, "over_odds": -110, "under_odds": -110},
    ])
    rep = clv_report(str(pred), str(close))
    assert rep.n_bets == 0
    assert rep.n_unmatched == 1
    assert rep.mean_clv is None
    assert "capture closing lines" in rep.verdict


def test_verdict_never_claims_edge_the_decision_gate_refuses(tmp_path):
    """The regression this guards: on 2026-07-20 the live /clv payload said
    "real price edge" in `verdict` and "NOT YET DECIDED (no edge yet)" in
    `decision`, off the same 82 bets whose 95% CI covered zero. `verdict` was
    computed from the sign of the mean; the gate was computed from the interval.
    One positive bet below target_n reproduces exactly that shape.
    """
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-20", "pitcher": "Gerrit Cole", "side": "over", "line": 6.5,
         "over_odds": -110, "under_odds": -110, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": "2026-06-20", "captured_at": "2026-06-20T22:00:00Z", "tag": "close",
         "pitcher": "Gerrit Cole", "line": 6.5, "over_odds": -130, "under_odds": 110},
    ])
    rep = clv_report(str(pred), str(close))
    assert rep.mean_clv > 0                        # the point estimate IS positive
    assert rep.decision.decided is False           # but nowhere near decision-grade n
    assert "NOT YET DECIDED" in rep.verdict
    assert "real price edge" not in rep.verdict


def test_verdict_claims_an_edge_only_once_the_gate_does(tmp_path):
    """The other side of the same rule: at decision-grade n with the whole CI
    above zero, the prose must actually say so — a gate that can only ever
    refuse is not a gate."""
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    # Identical +CLV bets, so the CI is tight and strictly above zero.
    _write(pred, PRED_FIELDS, [
        {"date": f"2026-06-{20 + i // 12:02d}", "pitcher": f"Pitcher {i}", "side": "over",
         "line": 6.5, "over_odds": -110, "under_odds": -110, "bet": "True"}
        for i in range(4)
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": f"2026-06-{20 + i // 12:02d}", "captured_at": "2026-06-20T22:00:00Z",
         "tag": "close", "pitcher": f"Pitcher {i}", "line": 6.5,
         "over_odds": -130, "under_odds": 110}
        for i in range(4)
    ])
    rep = clv_report(str(pred), str(close), target_n=4)
    assert rep.decision.decided is True and rep.decision.signal == "keep"
    assert "real price edge" in rep.verdict
    assert "NOT YET DECIDED" not in rep.verdict


def test_verdict_states_which_way_the_excluded_line_moves_lean(tmp_path):
    """A bare count of unmeasurable rows hides a non-random exclusion. Two
    unders whose lines dropped moved TOWARD our side, so their absence makes the
    reported mean conservative — the verdict has to say which way it leans."""
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-29", "pitcher": f"Pitcher {i}", "side": "under", "line": 5.5,
         "over_odds": 126, "under_odds": -162, "bet": "True"}
        for i in range(2)
    ] + [
        {"date": "2026-06-29", "pitcher": "Against Us", "side": "under", "line": 5.5,
         "over_odds": 126, "under_odds": -162, "bet": "True"},
        {"date": "2026-06-29", "pitcher": "Scored One", "side": "over", "line": 6.5,
         "over_odds": -110, "under_odds": -110, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        # under 5.5 closing at 4.5 = market came to us
        {"date": "2026-06-29", "captured_at": "2026-06-29T22:50:00Z", "tag": "close",
         "pitcher": f"Pitcher {i}", "line": 4.5, "over_odds": -134, "under_odds": 105}
        for i in range(2)
    ] + [
        # under 5.5 closing at 6.5 = market moved away from us
        {"date": "2026-06-29", "captured_at": "2026-06-29T22:50:00Z", "tag": "close",
         "pitcher": "Against Us", "line": 6.5, "over_odds": -134, "under_odds": 105},
        {"date": "2026-06-29", "captured_at": "2026-06-29T22:50:00Z", "tag": "close",
         "pitcher": "Scored One", "line": 6.5, "over_odds": -130, "under_odds": 110},
    ])
    rep = clv_report(str(pred), str(close))
    assert rep.n_bets == 1 and rep.n_unmeasurable == 3
    assert "2 moved toward our side, 1 against" in rep.verdict
    assert "conservative" in rep.verdict


def test_clv_report_missing_files_is_empty(tmp_path):
    rep = clv_report(str(tmp_path / "nope.csv"), str(tmp_path / "nope2.csv"))
    assert rep.n_bets == 0 and rep.n_unmatched == 0


def test_clv_route_returns_json(monkeypatch, tmp_path):
    pred = tmp_path / "predictions.csv"
    close = tmp_path / "line_history.csv"
    _write(pred, PRED_FIELDS, [
        {"date": "2026-06-20", "pitcher": "Gerrit Cole", "side": "over", "line": 6.5,
         "over_odds": -110, "under_odds": -110, "bet": "True"},
    ])
    _write(close, CLOSE_FIELDS, [
        {"date": "2026-06-20", "captured_at": "2026-06-20T22:00:00Z", "tag": "close",
         "pitcher": "Gerrit Cole", "line": 6.5, "over_odds": -130, "under_odds": 110},
    ])
    monkeypatch.setattr(main.settings, "predictions_log", str(pred), raising=False)
    monkeypatch.setattr(main.settings, "line_history_log", str(close), raising=False)

    client = TestClient(main.app)
    r = client.get("/clv")
    assert r.status_code == 200
    body = r.json()
    assert body["n_bets"] == 1 and body["pct_positive"] == 1.0
