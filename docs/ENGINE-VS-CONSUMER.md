# Engine vs consumer: mlb-edge and Fantasy

Written 2026-07-20. Compares this repository (`stike/mlb-edge`, the projection
engine) against `mrglennc64/Fantasy` at `origin/main` = `40ab36d` (the original
consumer app), and notes where `fantasy2` has since taken it.

This is not a code-quality review. It is a record of two programs that answered
the same question in opposite ways, and of which answer the data supported.

---

## 1. They are not competitors

Fantasy consumes this engine. From its README at `40ab36d`:

> *Pitcher strikeouts: `expected_ks` from the strike/mlb-edge slate (`pick6/feed.py`).*

Fantasy had no strikeout model of its own. It fetched `expected_ks`, converted
it to a probability, published it, and graded it against MLB StatsAPI finals.

So the comparison is really: **what the engine built, versus what the only
application measuring the engine concluded.**

| | mlb-edge | Fantasy @ 40ab36d |
|---|---|---|
| Python files | 220 | 33 |
| Dependencies | FastAPI, pandas, DuckDB, sklearn, pytest | stdlib only |
| Tests | pytest suites, smoke tests, fixtures | none |
| Blueprint PDFs at repo root | ~40 | 0 |
| One-off scripts | ~80 | 0 |
| Duplicate nested copy of itself | yes (`analytics/mlb-edge/analytics/`) | no |

---

## 2. The design inversion

The two repos give directly contradictory answers to "what should we publish?"

**mlb-edge** — `backend/app/model/gatekeeper.py`:

> *"Instead of predicting all games, only release projections where mathematical
> edge is meaningful. This prevents the model from having opinions on
> low-signal matchups."*
>
> A-Grade > 1.5 K · B-Grade 1.0–1.5 K · below 1.0 **silent, no projection released**

**Fantasy** — README:

> *"Nothing is filtered, suppressed, or toggled. Rows are ordered by confidence;
> low-information probabilities near 50% are shown as exactly that."*

### Why the Fantasy answer is the one that survives

Not as a matter of taste — as a matter of measurement.

**Suppression destroys the data needed to validate suppression.** If the engine
only publishes rows where `|projection − line| > 1.0`, it never observes the
suppressed population, and so can never fit whether that threshold carries
information. It conditions on the exact variable under test. The gatekeeper is
structurally self-confirming: nothing in its own output can refute it.

Fantasy publishes every matched row, so its record contains the full
distribution of `(projection, line, outcome)`, so `calibration/fit_mean.py` can
fit a slope across it. That is why Fantasy could produce a verdict about this
engine and this engine could not produce one about itself.

---

## 3. What each emits

| mlb-edge | Fantasy @ 40ab36d |
|---|---|
| expected_ks, edge vs line, Kelly stake, bankroll, risk, hedge, parlay matrix, arbitrage, A/B/No-Play grade | `predicted`, `P(more)` / `P(less)`, `lean`, `P` |

Fantasy ships four numbers. It got there by **subtraction** — the wagering
machinery was deliberately removed, and `pick6/config.py`'s platform
multipliers are explicitly *"context for analyses only, never an input to
scoring."*

---

## 4. Where the constants come from

This is the substantive engineering difference.

**mlb-edge sets constants by judgment and defends the judgment in prose.**

- Ensemble weights hand-assigned: opponent K profile 0.26, recent form 0.22,
  expected innings 0.18, lineup 0.09 (= 75% of the mass).
- `model/calibration.py`: the shrink factor `k` is *deliberately not fitted* —
  *"regularization toward the market, deliberately NOT a value fit to the
  (tiny) backtest sample."* `best_shrink()` exists but is labelled
  **MONITORING ONLY**.
- `model/gatekeeper.py`: the 1.0 / 1.5 K thresholds are hand-picked.

Each of these is defensible reasoning — "don't fit `k` to 50 games" is correct,
not lazy. The aggregate effect is nonetheless ~15 judgment-set constants that
have never been falsification-tested.

**Fantasy sets constants by held-out test, and refuses when the test fails.**

- Every constant flows `data/params.json` → `pick6/params.py` → a promotion gate.
- The gate requires ≥1% relative improvement on **both** Brier and log-loss on
  walk-forward held-out days, ≥150 rows, ≥5 test days, **and** a slope 95% CI
  excluding 1.0.
- Failure leaves that source at identity and explicitly forbids inheriting
  another source's coefficients.
- Every promotion is snapshotted to `data/params_history/` and reversible by
  file copy.

| | mlb-edge | Fantasy |
|---|---|---|
| ensemble weights | hand-set | n/a (consumes upstream) |
| calibration shrink `k` | deliberately unfitted | fitted walk-forward on frozen slates |
| dispersion | Poisson-family | NB `r = 16.6`, PIT-validated, leak-guarded |
| release threshold | hand-picked 1.0 / 1.5 K | none — publish everything |
| null results shipped | none | `s = 0.00`, on the homepage |

Both repos take data leakage seriously, and both learned it the hard way:
mlb-edge via leak-free Retrosheet reconstruction (`app/fit/factor_backfill.py`),
Fantasy via *"never fit on `/v2/slate` re-projections of past dates — it once
drove the dispersion to r ≈ 500, i.e. fake Poisson."*

---

## 5. Two independent routes to the same verdict

**Structural** — this repo, `backend/app/fit/__init__.py`:

> *"The 10 components are near-perfectly COLLINEAR. Eight of them are literally
> the same number (matchup_estimate × a factor that is 1.0 when its data is
> neutral); the other two correlate 0.89–0.98 with it. The weight-optimization
> problem is therefore ~2-3 effective dimensions with a degenerate solution
> space."*

The 10-factor ensemble is a 2–3 factor model. Umpire, pitch mix, bullpen,
weather and catcher contribute nothing unless their data is non-neutral, which
it usually is not.

**Empirical** — Fantasy, `pick6/consensus.py` and its README:

> *"fit_mean.py (2026-07-08, 164 frozen starts) showed our expected_ks adds no
> information beyond the published line (anchor s = 0.00), so strikeout
> probabilities are currently anchored to the line."*

One route reads the design, the other grades 164 settled starts. Same answer.

Fantasy then did the obvious thing — commit `0a29e6b`, *"Own the model: kmodel
becomes primary, mlb-edge becomes a benchmark."* Roughly two weeks from first
grading loop to demoting its supplier.

---

## 6. Consequence: the gatekeeper runs backwards

Combine `s = 0.00` with the release rule.

The gatekeeper grades on `|projection − line|`: larger disagreement → higher
grade → "Max Bet". That logic is valid only if disagreement carries signal. At
`s = 0.00`, disagreement **is estimation error**. So the A-Grade tier does not
select the strongest edges; it selects the model's largest mistakes, and sizes
them up.

That is a mechanism, not a coincidence, for what `model/calibration.py` already
records: *"it claimed 60-68% win probability and actually won 36-41%."*
Anti-calibration is the expected result when the confidence metric is monotonic
in the error.

This is a **conditional** failure, not a coding bug. If a future projection ever
fits `s > 0`, the gatekeeper becomes correct again. The problem is that nothing
in this repo re-checks the assumption. Fantasy's gate re-asks it every Sunday.

---

## 7. Where mlb-edge is genuinely ahead

Not everything favours the smaller program.

- **CLV capture** — `backend/app/backtest/clv.py`, `app/data/line_capture.py`,
  three systemd timers, `frontend/src/pages/Clv.jsx`, a `/clv` API endpoint with
  a keep/kill decision checkpoint. Fantasy has no equivalent and structurally
  cannot: pick'em boards have no closing line.
- **Feature depth** — Statcast, arsenal, umpires, park, catcher, handedness
  splits, DuckDB analytics.
- **Tests** — Fantasy has none.
- **Arbitrage** — the only component in the whole program with demonstrated edge.
- **Leak-free Retrosheet reconstruction** — genuinely hard, correctly done.

---

## 8. Live CLV status (measured 2026-07-20 via `GET /api/clv`)

The engine's own truth metric, on 82 graded bets from 2026-06-28 to 2026-07-17:

```
n_bets        82          (target 200)
mean CLV      +0.0073     (+0.73 probability points)
median CLV    +0.002
pct_positive  51.2%
95% CI        [-0.0028, +0.0174]      <-- includes zero
decision      gathering · 41% · NOT YET DECIDED
```

Read plainly: **not yet distinguishable from no edge.** 51.2% beating the close
is a coin flip; the confidence interval covers zero; 118 more graded bets are
needed to reach the pre-set decision point. This is the correct state for the
experiment to be in — it is collecting, and it has not yet been allowed to
conclude anything.

Two issues in how it reports itself:

**8.1 — The `verdict` string overclaims and contradicts the `decision` block.**
The same payload returns:

- `verdict`: *"…mean CLV +0.73 prob-points, 51% of bets beat the close ->
  **real price edge**."*
- `decision.headline`: *"…**NOT YET DECIDED (no edge yet)** — 118 more to a call."*

The `verdict` string asserts a real edge from a mean whose 95% CI includes zero,
while the decision gate immediately below it correctly refuses. Two different
answers to the same question in one response, and the more confident one is
wrong. `verdict` should be derived from `decision.signal`, not computed
independently — this is exactly the class of unconditioned claim the Fantasy
promotion gate exists to prevent.

**8.2 — The unmeasurable exclusion is non-random, and it biases the estimate
down.** 23 of 105 matched bets (22%) are dropped because the line moved between
bet and close. Of those 23, **15 moved toward our side** and 8 against — so the
excluded rows lean favourable, and the reported +0.73 points is, if anything,
conservative.

The exclusion is methodologically defensible: de-vigged CLV at a fixed line is
undefined when the line itself moved. But a 22% non-random exclusion should be
stated as a known downward bias, and the moves it discards are precisely the
largest market disagreements — the most informative rows in the sample. A
**line-value** metric (did the number move our way?) would capture them; a
**price-value** metric cannot. Worth adding alongside, not instead.

---

## 9. Summary

mlb-edge answers *"how do I turn a projection into bets?"* — thoroughly, with
real infrastructure — but it built the decision layer before validating the
projection layer, and its gatekeeper is designed so that validation can never
happen from its own output.

Fantasy @ `40ab36d` answers *"does the projection carry information?"* — and
shipped the answer, which was no. It is the smaller, less capable, more correct
program.

**The engine's infrastructure is the asset** (CLV capture, odds and de-vig, line
capture, arbitrage, Statcast pipeline). **The consumer's method is the asset**
(frozen snapshots, walk-forward gates, provenance, reversible constants,
publishing null results).

The merge worth making is mlb-edge's data infrastructure under Fantasy's
promotion discipline.

### Concrete next steps, in order

1. **Derive `verdict` from `decision`** so one payload cannot both claim and deny
   an edge (§8.1). Smallest change, largest credibility gain.
2. **Report the unmeasurable exclusion as a bias**, with the 15/8 split, and add
   a line-value companion metric (§8.2).
3. **Stop the gatekeeper suppressing the rows needed to test the gatekeeper** —
   either gate on a fitted slope rather than raw `|proj − line|`, or log the
   suppressed rows even when they are not displayed (§6). Without this, the
   engine can never fit its own release rule.
4. **Keep the CLV run going to n = 200.** It is the only measurement in either
   repo that can distinguish "no edge" from "edge not yet proven", it is 41%
   complete, and MLB is in season. Do not touch the decision threshold
   mid-experiment.
5. **Back up `predictions_log.csv` and `params_history/` off-host.** Both are
   gitignored, single-copy, VPS-local, with same-directory backups pruned at 14
   days. Every conclusion in this document depends on files that live on one
   disk.
