"""Cricket-umpire LBW edge — FEASIBILITY TEST (make-or-break).

The proprietary-data thesis: umpires differ in LBW trigger-finger, the tendency is
stable, and nobody publishes the tables. Before building anything, this answers the
ONLY question that matters: is per-umpire LBW variation REAL and PERSISTENT, or is
it noise (the way every prediction model in this program turned out)?

Method (free Cricsheet ball-by-ball JSON):
  - For each match, read info.officials.umpires + every wicket's kind.
  - Attribute the match's dismissals to BOTH on-field umpires (Cricsheet doesn't
    say which umpire made each call), so per-umpire = "LBW share of dismissals in
    matches this umpire stood in." Confounded by conditions, but a valid first
    signal test: if there's no variation here, the niche is dead.
  - SIGNAL: spread of per-umpire LBW share vs the baseline.
  - STABILITY (the real test): split each umpire's matches by date into halves;
    does first-half LBW share predict second-half? (correlation > 0 = persistent
    skill/tendency; ~0 = noise). This is the test the tennis/horse models failed.

    python feasibility.py
"""
from __future__ import annotations

import io
import json
import os
import statistics
import urllib.request
import zipfile
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "data")
SOURCES = {  # competition -> Cricsheet zip
    "tests": "https://cricsheet.org/downloads/tests_json.zip",
    "t20s": "https://cricsheet.org/downloads/t20s_json.zip",
    "ipl": "https://cricsheet.org/downloads/ipl_json.zip",
}
MIN_DISMISSALS = 150  # umpire inclusion threshold for stable rates


def _download(url: str, path: str) -> None:
    if os.path.exists(path):
        return
    print(f"  downloading {os.path.basename(path)} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())


def matches_from_zip(path: str):
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".json") and n != "README.txt":
                try:
                    yield json.loads(z.read(n))
                except Exception:
                    continue


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    # per umpire: list of (date, n_dismissals, n_lbw) one tuple per match
    ump = defaultdict(list)
    tot_dis = tot_lbw = n_matches = 0

    for comp, url in SOURCES.items():
        zpath = os.path.join(DATA, f"{comp}.zip")
        _download(url, zpath)
        for m in matches_from_zip(zpath):
            info = m.get("info", {})
            umps = (info.get("officials", {}) or {}).get("umpires") or []
            if not umps:
                continue
            date = (info.get("dates") or ["?"])[0]
            dis = lbw = 0
            for inn in m.get("innings", []):
                for over in inn.get("overs", []):
                    for d in over.get("deliveries", []):
                        for w in d.get("wickets", []):
                            dis += 1
                            if w.get("kind") == "lbw":
                                lbw += 1
            if dis == 0:
                continue
            n_matches += 1
            tot_dis += dis
            tot_lbw += lbw
            for u in umps:
                ump[u].append((date, dis, lbw))

    baseline = tot_lbw / tot_dis
    print(f"\nparsed {n_matches} matches, {tot_dis} dismissals, "
          f"{tot_lbw} LBW.  BASELINE LBW share = {baseline:.3%}\n")

    # per-umpire LBW share (qualified)
    rates = []
    for u, games in ump.items():
        d = sum(g[1] for g in games)
        l = sum(g[2] for g in games)
        if d >= MIN_DISMISSALS:
            rates.append((u, l / d, d, len(games)))
    rates.sort(key=lambda x: x[1])
    print(f"=== SIGNAL: {len(rates)} umpires with >= {MIN_DISMISSALS} dismissals ===")
    vals = [r[1] for r in rates]
    print(f"  LBW share  min {min(vals):.1%}  median {statistics.median(vals):.1%}  "
          f"max {max(vals):.1%}  stdev {statistics.pstdev(vals):.3f}")
    print("  lowest-LBW umpires:")
    for u, r, d, g in rates[:4]:
        print(f"    {u:24} {r:.1%}  ({d} dis, {g} matches)")
    print("  highest-LBW umpires:")
    for u, r, d, g in rates[-4:][::-1]:
        print(f"    {u:24} {r:.1%}  ({d} dis, {g} matches)")

    # STABILITY: split each umpire's matches by date, correlate halves
    h1, h2 = [], []
    for u, games in ump.items():
        games = sorted(games, key=lambda g: g[0])
        mid = len(games) // 2
        a, b = games[:mid], games[mid:]
        da, la = sum(g[1] for g in a), sum(g[2] for g in a)
        db, lb = sum(g[1] for g in b), sum(g[2] for g in b)
        if da >= MIN_DISMISSALS and db >= MIN_DISMISSALS:
            h1.append(la / da)
            h2.append(lb / db)
    print(f"\n=== STABILITY: {len(h1)} umpires with >= {MIN_DISMISSALS} dismissals "
          "in BOTH halves of their career ===")
    if len(h1) >= 5:
        r = statistics.correlation(h1, h2)
        print(f"  split-half correlation (1st-half LBW% vs 2nd-half) = {r:+.3f}")
        verdict = ("STRONG persistent signal" if r > 0.4 else
                   "moderate persistent signal" if r > 0.2 else
                   "WEAK / mostly noise" if r > 0.05 else "NO persistence (noise)")
        print(f"  -> {verdict}")
    else:
        print("  too few umpires with both halves qualified — need more data")


if __name__ == "__main__":
    main()
