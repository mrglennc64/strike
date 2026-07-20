#!/usr/bin/env bash
# Pull the irreplaceable records off the VPS. Run from the workstation.
#
#   bash deploy/backup_pull.sh
#
# WHY PULL, NOT PUSH. The files below are the only copy of every graded outcome
# either app has ever produced. They are gitignored (correctly — cron_daily.sh
# does `git reset --hard origin/main` every half hour, so a tracked file would be
# reverted), which means git history is NOT the audit trail for them. As of
# 2026-07-20 the box had no /root/backups, no backup cron, and the only
# redundancy was same-directory .bak files on the same disk — which one failure
# takes with it. Pulling to OneDrive puts a copy on a different machine AND in
# cloud storage, without needing outbound credentials on the server.
#
# WHAT IS AND IS NOT HERE. Only the unreproducible rows. /opt/strike/data is
# ~119M, almost all of it re-downloadable (Statcast pulls, s2.7z, umpire JSON).
# Backing that up would bury the 110K that actually matters. Everything listed
# below is an append-only record of something that happened once:
#
#   strike/line_history.csv     open+close line snapshots. Lines are EPHEMERAL —
#                               a missed capture can never be backfilled, and
#                               this file is the entire CLV experiment (82 of
#                               200 graded on 2026-07-20).
#   strike/predictions.csv      the engine's pre-game projections, frozen.
#   fantasy/predictions_log.csv the graded accuracy record; training data for
#                               every refit in fantasy's calibration/.
#   fantasy/params_history/     immutable snapshots of promoted constants. Empty
#                               until the weekly refits get --write; copied
#                               anyway so the first promotion is covered.
#
# Restore is a file copy back to the same path. No tooling required, which is
# the point.
set -euo pipefail

SERVER="${STRIKE_SERVER:-newvps}"
DEST_ROOT="${STRIKE_BACKUP_DIR:-$HOME/OneDrive/Dokument/stike/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$DEST_ROOT/$STAMP"

mkdir -p "$DEST/strike" "$DEST/fantasy"

echo "pulling from $SERVER -> $DEST"

# scp, not rsync: rsync is not installed on every fresh box and these files are
# ~110K total, so there is nothing to gain from a delta transfer.
scp -q "$SERVER:/opt/strike/data/line_history.csv"        "$DEST/strike/"    || echo "  MISS strike/line_history.csv"
scp -q "$SERVER:/opt/strike/data/predictions.csv"         "$DEST/strike/"    || echo "  MISS strike/predictions.csv"
scp -q "$SERVER:/opt/fantasy/data/predictions_log.csv"    "$DEST/fantasy/"   || echo "  MISS fantasy/predictions_log.csv"
scp -q "$SERVER:/opt/fantasy/data/params.json"            "$DEST/fantasy/"   2>/dev/null || true
scp -qr "$SERVER:/opt/fantasy/data/params_history"        "$DEST/fantasy/"   2>/dev/null || true

# A row count per file, so a truncated pull is visible at a glance instead of
# being discovered months later when the record is needed.
echo "--- pulled ---"
find "$DEST" -type f -name '*.csv' -print0 | while IFS= read -r -d '' f; do
    printf '  %6s  %s\n' "$(wc -l < "$f")" "${f#"$DEST"/}"
done

# Latest-pointer so a restore does not have to guess which stamp is newest.
ln -sfn "$STAMP" "$DEST_ROOT/latest" 2>/dev/null || printf '%s\n' "$STAMP" > "$DEST_ROOT/latest.txt"

# Keep a quarter of history. These are ~110K a run; pruning is about keeping the
# directory readable, not about space.
find "$DEST_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +90 -exec rm -rf {} + 2>/dev/null || true

echo "ok: $DEST"
