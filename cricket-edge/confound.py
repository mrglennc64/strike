"""Cricket-umpire LBW edge — CONFOUND CONTROL (gate before spending on odds).

feasibility.py proved per-umpire LBW share varies 7x and PERSISTS (split-half
r=+0.448). But raw share is confounded: subcontinent spin venues produce more LBWs
regardless of who officiates, and an umpire who works mostly there will look
"high-LBW" without any true trigger-finger effect. This is the same conditions
artifact that killed the tennis/horse/MLB models.

The ONLY question that decides whether to buy a cricket odds feed:
  After removing what VENUE and FORMAT explain, do umpires STILL persistently
  differ in LBW? (residual persistence > 0 = real umpire effect; ~0 = it was
  conditions all along).

Method:
  - Expected LBW share for a match = LBW rate of its (format, venue) cell, with a
    fallback to the format baseline for thin venues. This is the "conditions" model.
  - Umpire residual = (actual LBW - expected LBW) / dismissals, i.e. excess LBW per
    dismissal beyond what their venues/formats predict.
  - SIGNAL: spread of residuals across umpires (how much survives the control).
  - PERSISTENCE (the gate): split each umpire's matches by date; does first-half
    residual predict second-half residual? Compare this r to the raw +0.448.

    python confound.py
"""
from __future__ import annotations

import os
import statistics
from collections import defaultdict

from feasibility import SOURCES, MIN_DISMISSALS, DATA, _download, matches_from_zip


def collect():
    """One pass: per match gather (date, format, venue, dis, lbw, umpires)."""
    matches = []
    for comp, url in SOURCES.items():
        zpath = os.path.join(DATA, f"{comp}.zip")
        _download(url, zpath)
        for m in matches_from_zip(zpath):
            info = m.get("info", {})
            umps = (info.get("officials", {}) or {}).get("umpires") or []
            if not umps:
                continue
            fmt = info.get("match_type") or comp
            venue = info.get("venue") or "?"
            date = (info.get("dates") or ["?"])[0]
            dis = lbw = 0
            for inn in m.get("innings", []):
                for over in inn.get("overs", []):
                    for d in over.get("deliveries", []):
                        for w in d.get("wickets", []):
                            dis += 1
                            if w.get("kind") == "lbw":
                                lbw += 1
            if dis:
                matches.append((date, fmt, venue, dis, lbw, umps))
    return matches


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    matches = collect()
    tot_dis = sum(m[3] for m in matches)
    tot_lbw = sum(m[4] for m in matches)
    base = tot_lbw / tot_dis
    print(f"\nparsed {len(matches)} matches, {tot_dis} dismissals, "
          f"{tot_lbw} LBW.  baseline LBW share = {base:.3%}\n")

    # --- conditions model: LBW rate per (format, venue), fallback to format ---
    fmt_dis, fmt_lbw = defaultdict(int), defaultdict(int)
    cell_dis, cell_lbw = defaultdict(int), defaultdict(int)
    for date, fmt, venue, dis, lbw, umps in matches:
        fmt_dis[fmt] += dis
        fmt_lbw[fmt] += lbw
        cell_dis[(fmt, venue)] += dis
        cell_lbw[(fmt, venue)] += lbw

    MIN_CELL = 200  # dismissals before a venue cell is trusted over the format mean

    def expected(fmt, venue):
        if cell_dis[(fmt, venue)] >= MIN_CELL:
            return cell_lbw[(fmt, venue)] / cell_dis[(fmt, venue)]
        if fmt_dis[fmt]:
            return fmt_lbw[fmt] / fmt_dis[fmt]
        return base

    # how much do conditions alone vary? (sanity: the confound is real if wide)
    cell_rates = [cell_lbw[c] / cell_dis[c] for c in cell_dis if cell_dis[c] >= MIN_CELL]
    print(f"=== conditions model: {len(cell_rates)} (format,venue) cells "
          f">= {MIN_CELL} dismissals ===")
    print(f"  venue LBW rate  min {min(cell_rates):.1%}  "
          f"median {statistics.median(cell_rates):.1%}  max {max(cell_rates):.1%}  "
          f"stdev {statistics.pstdev(cell_rates):.3f}   <- the confound to remove\n")

    # --- per umpire: actual vs expected LBW, plus per-match residual record ---
    # ump -> list of (date, dis, lbw, exp_lbw)
    ump = defaultdict(list)
    for date, fmt, venue, dis, lbw, umps in matches:
        e = expected(fmt, venue)
        for u in umps:
            ump[u].append((date, dis, lbw, dis * e))

    # raw vs adjusted spread across qualified umpires
    raw_rates, adj_resid = [], []
    for u, gs in ump.items():
        d = sum(g[1] for g in gs)
        if d < MIN_DISMISSALS:
            continue
        l = sum(g[2] for g in gs)
        el = sum(g[3] for g in gs)
        raw_rates.append(l / d)
        adj_resid.append((l - el) / d)   # excess LBW per dismissal vs conditions
    print(f"=== SIGNAL after control: {len(raw_rates)} umpires "
          f">= {MIN_DISMISSALS} dismissals ===")
    print(f"  RAW   LBW share spread:  stdev {statistics.pstdev(raw_rates):.3f}  "
          f"({min(raw_rates):.1%} -> {max(raw_rates):.1%})")
    print(f"  ADJ   residual spread:   stdev {statistics.pstdev(adj_resid):.3f}  "
          f"({min(adj_resid):+.1%} -> {max(adj_resid):+.1%})")
    shrink = 1 - statistics.pstdev(adj_resid) / statistics.pstdev(raw_rates)
    print(f"  -> conditions explain {shrink:.0%} of the raw spread\n")

    # --- THE GATE: split-half persistence of the ADJUSTED residual ---
    h1, h2 = [], []
    for u, gs in ump.items():
        gs = sorted(gs, key=lambda g: g[0])
        mid = len(gs) // 2
        a, b = gs[:mid], gs[mid:]
        da, db = sum(g[1] for g in a), sum(g[1] for g in b)
        if da >= MIN_DISMISSALS and db >= MIN_DISMISSALS:
            ra = (sum(g[2] for g in a) - sum(g[3] for g in a)) / da
            rb = (sum(g[2] for g in b) - sum(g[3] for g in b)) / db
            h1.append(ra)
            h2.append(rb)
    print(f"=== PERSISTENCE of ADJUSTED residual: {len(h1)} umpires qualified "
          "in BOTH halves ===")
    if len(h1) >= 5:
        r = statistics.correlation(h1, h2)
        print(f"  split-half correlation (1st-half residual vs 2nd-half) = {r:+.3f}")
        print(f"  (raw, uncontrolled, was +0.448)")

    # --- LEAVE-ONE-OUT robustness: exclude each umpire's OWN matches from the
    #     venue expectation, so a high-LBW umpire can't deflate their own residual.
    #     This is the unbiased version; if it ALSO collapses, the verdict is firm.
    u_cell_dis, u_cell_lbw = defaultdict(int), defaultdict(int)
    for date, fmt, venue, dis, lbw, umps in matches:
        for u in umps:
            u_cell_dis[(u, fmt, venue)] += dis
            u_cell_lbw[(u, fmt, venue)] += lbw

    def expected_loo(u, fmt, venue):
        d = cell_dis[(fmt, venue)] - u_cell_dis[(u, fmt, venue)]
        l = cell_lbw[(fmt, venue)] - u_cell_lbw[(u, fmt, venue)]
        if d >= MIN_CELL:
            return l / d
        return fmt_lbw[fmt] / fmt_dis[fmt] if fmt_dis[fmt] else base

    # rebuild per-match expected with umpire-specific (leave-one-out) baseline
    ump_loo = defaultdict(list)
    for date, fmt, venue, dis, lbw, umps in matches:
        for u in umps:
            ump_loo[u].append((date, dis, lbw, dis * expected_loo(u, fmt, venue)))
    l1, l2 = [], []
    for u, gs in ump_loo.items():
        gs = sorted(gs, key=lambda g: g[0])
        mid = len(gs) // 2
        a, b = gs[:mid], gs[mid:]
        da, db = sum(g[1] for g in a), sum(g[1] for g in b)
        if da >= MIN_DISMISSALS and db >= MIN_DISMISSALS:
            l1.append((sum(g[2] for g in a) - sum(g[3] for g in a)) / da)
            l2.append((sum(g[2] for g in b) - sum(g[3] for g in b)) / db)
    if len(l1) >= 5:
        rloo = statistics.correlation(l1, l2)
        print(f"  leave-one-out (unbiased) split-half correlation     = {rloo:+.3f}  "
              f"({len(l1)} umpires)")
        verdict = ("REAL umpire effect survives the control — buy the odds feed"
                   if rloo > 0.3 else
                   "partial: effect survives but weakened — borderline" if rloo > 0.15 else
                   "COLLAPSED: signal was mostly conditions — do NOT spend on odds")
        print(f"  -> {verdict}")
    else:
        print("  too few umpires qualified in both halves")


if __name__ == "__main__":
    main()
