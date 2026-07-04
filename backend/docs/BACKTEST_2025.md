# 2025 Season Backtest — Retrosheet leak-free replay (2026-07-04)

Full-season out-of-sample replay of the production `project()` ensemble over the
2025 Retrosheet play-by-play (`C:\strike-data\retrosheet\2025\2025plays.csv`),
built with `app/fit/factor_backfill.build_factor_table(2025)` — the same
reconstruction validated on 2024 in `WEIGHT_FITTING.md`. Every start uses only
games strictly before its date. Table persisted to
`C:\strike-data\features\factor_projections_2025.parquet`.

Precondition: the Retrosheet-dependent test suite passes (33/33 —
`test_retrosheet_ingest`, `test_factor_backfill`, `test_group_prior`,
`test_grouping_features`, `test_matchup_matrix`).

## Coverage

- **3,972 starts reconstructed, 0 failures** (2024: 3,926).
- 3,710 scored after requiring ≥1 prior start for the trailing baseline.
- Actual Ks: mean 5.00, sd 2.44.

## MAE ladder (lower = better)

| predictor | 2025 MAE | 2024 MAE |
|---|---|---|
| league-avg constant | 1.935 | — |
| pitcher own trailing-5 mean | 1.951 | 1.975 |
| pitcher own expanding mean | 1.892 | — |
| **production ensemble (offline reconstruction)** | **1.837** | 1.866 |

The ensemble beats every baseline in both seasons, with near-identical margins —
the 2024 result replicates. (Offline reconstruction MAE runs ~0.4 above the live
pipeline's ~1.43 because minor-factor inputs are neutral-defaulted and opponent
windows are cruder; see the caveat in `WEIGHT_FITTING.md`.)

Aggregate bias is negligible (+0.019 K); corr(proj, actual) = 0.386.

## Headline finding: projections are overdispersed (slope 0.63)

Calibration by projected-K bucket shows a classic mean-reversion fan:

| bucket | n | mean proj | mean actual | gap |
|---|---|---|---|---|
| 3 | 421 | 3.07 | 3.82 | −0.75 |
| 4 | 942 | 4.03 | 4.32 | −0.29 |
| 5 | 964 | 4.97 | 5.00 | −0.03 |
| 6 | 701 | 5.97 | 5.52 | +0.44 |
| 7 | 383 | 6.93 | 6.27 | +0.66 |
| 8 | 151 | 7.92 | 6.94 | +0.98 |

Low projections are too low, high projections too high. Regressing actual on
projected gives **slope ≈ 0.60–0.63** (a well-calibrated model would be ~1.0).

**OOS-validated fix:** fit the linear recalibration on 2024
(`λ' = 0.604·λ + 1.967`), apply to 2025 unseen:

| | 2025 MAE |
|---|---|
| raw λ | 1.8539 |
| shrunk λ (2024-fit) | **1.8035** |

**+0.050 K OOS improvement** — larger than the group prior's +0.037 (not shipped)
and the weight fit's +0.0002 (not shipped), and it's one line of arithmetic, not a
new model. Before wiring in: re-measure the slope on **live** logged predictions
(`data/predictions.csv` expected_ks vs settled actuals) — the live pipeline's
richer inputs may already be partially shrunk via `PROB_SHRINKAGE`, and
double-shrinking would flip the bias. Ship the λ-recalibration behind a flag, same
pattern as `PROB_SHRINKAGE`, only after the live-log slope confirms overdispersion.

## Proxy prop grading

Synthetic line = trailing-5 mean forced to a half-K; bet the side the ensemble
projects; win if the actual lands that side:

- all 3,710 starts: **61.9%** wins
- when the model disagrees with the line by ≥0.5 K (n=1,876): **69.2%** wins

Directionally strong, but the proxy line is much softer than a real book's —
treat as an upper bound, not an expected hit rate. (Live 2026-07-01 slate went
11–8 = 57.9% on real DraftKings lines.)

## Collinearity re-confirmed on 2025

The eight matchup-family components again carry the identical correlation with
actual Ks (+0.3897 each — internal corr 1.000); only `pitcher_recent_form`
(+0.343) and `lineup_strength` (+0.393) are distinct. Same structural read as
2024 (`WEIGHT_FITTING.md`): the ensemble is effectively ~2–3 dimensional until
the minor factors get real data.

## Live-log slope measurement (2026-07-04 follow-up)

Joined the VPS `predictions.csv` (147 unique pitcher-dates, 2026-06-28 → 07-03)
to settled boxscore actuals (MLB Stats API; persisted to
`C:\strike-data\features\live_settled.csv`):

- **live slope 0.75** (SE ≈ 0.15) — overdispersion confirmed in direction, but
  milder than offline (0.60) and only ~1.6 SE below 1.0 at n=147.
- overall bias **+0.25 K high**, concentrated in the top half (projections above
  the median overshoot actuals by **+0.40 K**; bottom half only +0.11).
- The 2024-offline-fit recalibration does **not** transfer to live (MAE
  2.011 → 2.009, flat): the live pipeline's distribution differs from the
  reconstruction. A live-fit shrink helps in-sample (1.971) but n=147 is too
  small to ship.

**Decision: do not ship a λ recalibration yet.** Direction is consistent across
offline 2024, offline 2025, and live logs (slope < 1, high-λ overshoot — which
also matches the live over/under record: unders on high lines lose most). Keep
settling daily logs into `live_settled.csv` and re-fit at **n ≥ ~400** (≈3 more
weeks); ship behind a flag only if the live-fit slope stays materially < 1.

## Verdicts

1. **Ensemble replicates OOS on a second season** — beats all naive baselines in
   both 2024 and 2025 with stable margins.
2. **λ overdispersion is real in all three datasets** (offline 2024/2025 slope
   0.60, live slope 0.75, +0.050 K OOS gain offline) but the offline-fit
   correction does not transfer to live; accumulate settled logs to n≥400 and
   fit on live data before shipping.
3. Weight optimization and group priors remain dead ends (nothing here changes
   those verdicts).
