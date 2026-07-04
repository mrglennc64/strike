"""Append evaluated predictions to a CSV log.

This is the seed for the future backtest / CLV layer: without a record of what the
model said (line, probability, edge) at prediction time, "edge" can never be checked
against results or closing lines. Every evaluated start is logged once.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

FIELDS = [
    "logged_at",
    "date",
    "pitcher",
    "pitcher_id",
    "game_pk",
    "opponent",
    "venue",
    "expected_ks",
    "line",
    "bookmaker",
    "side",
    "model_prob",
    "fair_prob",
    "over_odds",
    "under_odds",
    "edge",
    "kelly",
    "bet",
    "low_confidence",
]


def _migrate_schema(path: str) -> None:
    """Rewrite an existing log whose header predates the current FIELDS.

    Without this, appending current-schema rows to an old-schema file silently
    mixes layouts in one CSV (this happened when game_pk was added). Old rows are
    remapped by column name — missing new columns become "" — and the original
    file is kept as a timestamped .bak.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames == FIELDS:
            return
        old_rows = list(reader)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    os.replace(path, f"{path}.pre-migrate-{stamp}.bak")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in old_rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def log_predictions(rows: list[dict], path: str) -> None:
    if not rows:
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    if not new_file:
        _migrate_schema(path)
    stamp = datetime.now(timezone.utc).isoformat()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({"logged_at": stamp, **row})
