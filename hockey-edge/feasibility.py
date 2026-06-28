"""NHL shots-on-goal (SOG) model — FEASIBILITY TEST (offseason build).

The bettable model is: projected SOG = shots/60 x projected TOI x opp shot-suppression.
Its whole foundation is one assumption: a player's SHOT RATE is a stable, predictable
skill (unlike goals, which are noisy). Before building the live projector, this tests
that assumption on free MoneyPuck data the same way cricket-edge tested umpire LBW:

  PERSISTENCE: does a player's shots/60 (and SOG/game) in season N predict season N+1?
    high year-over-year correlation -> shot rate is real skill, model has a foundation.
    ~0 -> it's noise and the model is dead (the way the MLB K model died).

Also reports the spread across players (is there enough variation to find soft props?).

Data: MoneyPuck season-summary skater CSVs (free). situation='all'.

    python feasibility.py
"""
from __future__ import annotations

import csv
import io
import os
import statistics
import urllib.request

DATA = os.path.join(os.path.dirname(__file__), "data")
SEASONS = [2021, 2022, 2023, 2024]
URL = ("https://moneypuck.com/moneypuck/playerData/seasonSummary/"
       "{yr}/regular/skaters.csv")
MIN_ICETIME_SEC = 30000  # ~500 min: qualified-skater threshold for stable rates


def _get(yr: int) -> str:
    path = os.path.join(DATA, f"skaters_{yr}.csv")
    if not os.path.exists(path):
        print(f"  downloading skaters_{yr}.csv ...", flush=True)
        req = urllib.request.Request(URL.format(yr=yr), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, "wb").write(r.read())
    return open(path, encoding="utf-8").read()


def load(yr: int) -> dict:
    """player_id -> dict(name, sog_per60, sog_per_game, toi_min) for situation='all'."""
    out = {}
    for r in csv.DictReader(io.StringIO(_get(yr))):
        if r.get("situation") != "all":
            continue
        try:
            ice = float(r["icetime"])             # seconds
            sog = float(r["I_F_shotsOnGoal"])
            gp = float(r["games_played"])
        except (KeyError, ValueError):
            continue
        if ice < MIN_ICETIME_SEC or gp < 1:
            continue
        pid = r.get("playerId") or r.get("name")
        out[pid] = {
            "name": r.get("name", "?"),
            "sog_per60": sog / (ice / 3600.0),
            "sog_per_game": sog / gp,
            "toi_min": ice / 60.0,
        }
    return out


def corr(xs, ys):
    return statistics.correlation(xs, ys) if len(xs) >= 5 else float("nan")


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    byyr = {yr: load(yr) for yr in SEASONS}
    for yr in SEASONS:
        print(f"  {yr}: {len(byyr[yr])} qualified skaters (>= {MIN_ICETIME_SEC//60} min)")

    latest = byyr[SEASONS[-1]]
    rates = sorted((d["sog_per60"], d["name"]) for d in latest.values())
    print(f"\n=== SPREAD ({SEASONS[-1]}) — shots per 60 min ===")
    vals = [r[0] for r in rates]
    print(f"  min {min(vals):.1f}  median {statistics.median(vals):.1f}  "
          f"max {max(vals):.1f}  stdev {statistics.pstdev(vals):.2f}")
    print("  top shooters:")
    for v, n in rates[-5:][::-1]:
        print(f"    {n:24} {v:.1f} SOG/60")

    # PERSISTENCE: pool consecutive-season pairs
    p60_a, p60_b, pg_a, pg_b = [], [], [], []
    for i in range(len(SEASONS) - 1):
        a, b = byyr[SEASONS[i]], byyr[SEASONS[i + 1]]
        for pid in a.keys() & b.keys():
            p60_a.append(a[pid]["sog_per60"]); p60_b.append(b[pid]["sog_per60"])
            pg_a.append(a[pid]["sog_per_game"]); pg_b.append(b[pid]["sog_per_game"])

    print(f"\n=== PERSISTENCE (year N -> N+1, {len(p60_a)} player-season pairs) ===")
    r60 = corr(p60_a, p60_b)
    rpg = corr(pg_a, pg_b)
    print(f"  shots/60      correlation = {r60:+.3f}")
    print(f"  SOG per game  correlation = {rpg:+.3f}")
    best = max(r60, rpg)
    verdict = ("STRONG — shot rate is a stable skill, model has a real foundation"
               if best > 0.6 else
               "MODERATE — predictable but noisy" if best > 0.4 else
               "WEAK — mostly noise, model foundation shaky" if best > 0.2 else
               "NONE — shot rate doesn't persist; model is dead")
    print(f"  -> {verdict}")
    print("\n(For comparison: cricket umpire LBW persistence was +0.448; "
          "goals year-over-year are notoriously ~0.3-0.4. Shots should beat both.)")


if __name__ == "__main__":
    main()
