"""Tests for the predictions CSV log — schema migration on append.

Pins the fix for the mixed-layout log: appending current-schema rows to a file
written under an older FIELDS list must first rewrite that file to the current
header (old file kept as .bak), never interleave two layouts in one CSV.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.log.predictions import FIELDS, log_predictions

ROW = {
    "date": "2026-07-04", "pitcher": "Test Arm", "pitcher_id": "123456",
    "game_pk": "825000", "opponent": "Foes", "venue": "Test Park",
    "expected_ks": 5.5, "line": 4.5, "bookmaker": "draftkings", "side": "over",
    "model_prob": 0.6, "fair_prob": 0.5, "over_odds": 100, "under_odds": -120,
    "edge": 0.1, "kelly": 0.02, "bet": True, "low_confidence": False,
}


def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_append_to_current_schema_file_leaves_it_alone(tmp_path):
    path = tmp_path / "predictions.csv"
    log_predictions([ROW], str(path))
    log_predictions([ROW], str(path))
    rows = _read(path)
    assert len(rows) == 2
    assert not list(tmp_path.glob("*.bak"))


def test_append_migrates_old_schema_file(tmp_path):
    path = tmp_path / "predictions.csv"
    old_fields = [f for f in FIELDS if f != "game_pk"]  # v1: pre-game_pk layout
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=old_fields)
        writer.writeheader()
        writer.writerow({f: ROW.get(f, "x") for f in old_fields} | {"logged_at": "t0"})

    log_predictions([ROW], str(path))

    with open(path, newline="", encoding="utf-8") as f:
        assert next(csv.reader(f)) == FIELDS  # single, current header
    rows = _read(path)
    assert len(rows) == 2
    assert rows[0]["game_pk"] == ""            # old row: new column backfilled empty
    assert rows[0]["pitcher"] == ROW["pitcher"]  # old values land under right names
    assert rows[1]["game_pk"] == str(ROW["game_pk"])
    assert len(list(tmp_path.glob("predictions.csv.pre-migrate-*.bak"))) == 1
