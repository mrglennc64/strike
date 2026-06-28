"""NHL shots-on-goal projector — the model, built on free MoneyPuck data.

    projected SOG = (player shots/60) x (projected TOI / 60) x (opponent factor)

- player shots/60   : the stable, persistent skill (year-over-year r ~ +0.90, see feasibility.py)
- projected TOI     : YOU supply this from tonight's lines/role when the season starts
                      (the one live input; offseason demo uses the player's own avg TOI)
- opponent factor   : opp team's SOG-against/game / league average (>1 = team allows
                      more shots = nudge the projection up; <1 = shot-suppressing)

The data-driven parts (rates, opponent factors) are built and validated now; in-season
you plug in projected TOI + compare the output to the posted line, and bet only the
divergences that survive a CLV test. Projecting SOG accurately is NOT the same as
beating the book (the book projects it well too) — the edge is in the residual the
book misprices (TOI/role changes, pace, back-to-backs), provable only vs live lines.

    python model.py
"""
from __future__ import annotations

import csv
import io
import os

DATA = os.path.join(os.path.dirname(__file__), "data")
SEASON = 2024


def load_players() -> dict:
    out = {}
    rows = csv.DictReader(open(os.path.join(DATA, f"skaters_{SEASON}.csv"), encoding="utf-8"))
    for r in rows:
        if r.get("situation") != "all":
            continue
        try:
            ice, sog, gp = float(r["icetime"]), float(r["I_F_shotsOnGoal"]), float(r["games_played"])
        except (KeyError, ValueError):
            continue
        if ice < 18000 or gp < 1:   # ~300+ min
            continue
        out[r["name"]] = {"sog_per60": sog / (ice / 3600.0),
                          "avg_toi_min": (ice / 60.0) / gp,
                          "team": r.get("team", "?")}
    return out


def load_team_factors() -> tuple[dict, float]:
    rows = [r for r in csv.DictReader(open(os.path.join(DATA, f"teams_{SEASON}.csv"), encoding="utf-8"))
            if r.get("situation") == "all"]
    per_game = {r["team"]: float(r["shotsOnGoalAgainst"]) / float(r["games_played"]) for r in rows}
    league_avg = sum(per_game.values()) / len(per_game)
    factors = {t: v / league_avg for t, v in per_game.items()}
    return factors, league_avg


def project_sog(player: dict, opp_factor: float, proj_toi_min: float) -> float:
    return player["sog_per60"] * (proj_toi_min / 60.0) * opp_factor


def main() -> None:
    players = load_players()
    factors, league_avg = load_team_factors()
    print(f"NHL SOG projector ({SEASON}) — {len(players)} skaters, "
          f"league avg {league_avg:.1f} SOG allowed/game\n")

    hi = max(factors, key=factors.get); lo = min(factors, key=factors.get)
    print(f"opponent extremes: {hi} allows most ({factors[hi]:.2f}x), "
          f"{lo} suppresses most ({factors[lo]:.2f}x)\n")

    print("Example projections (at each player's avg TOI):")
    print(f"  {'player':22}{'SOG/60':>7}{'TOI':>6}{'vs '+hi:>9}{'vs '+lo:>9}")
    for name in ["Brady Tkachuk", "Auston Matthews", "David Pastrnak", "Alex Ovechkin"]:
        p = players.get(name)
        if not p:
            continue
        t = p["avg_toi_min"]
        print(f"  {name:22}{p['sog_per60']:7.1f}{t:6.1f}"
              f"{project_sog(p, factors[hi], t):9.2f}{project_sog(p, factors[lo], t):9.2f}")

    # how to use it in-season
    print("\nIN-SEASON USE: pull tonight's projected TOI + opponent, then:")
    ex = players.get("Brady Tkachuk")
    if ex:
        proj = project_sog(ex, factors[hi], 19.5)
        line = 3.5
        side = "OVER" if proj > line else "UNDER"
        print(f"  e.g. Tkachuk, 19.5 min, vs {hi}: projected {proj:.2f} SOG  "
              f"vs line {line} -> lean {side} (edge {proj-line:+.2f})")
    print("  ...then log projection vs OPENING line, check vs CLOSE = the CLV test. "
          "Only bet if disagreements predict the close.")


if __name__ == "__main__":
    main()
