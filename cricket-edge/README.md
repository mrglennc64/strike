# cricket-edge

Proprietary-data betting niche: **per-umpire LBW tendencies** from free Cricsheet
ball-by-ball data. Thesis: umpires differ systematically in LBW propensity, the
tendency is stable, nobody publishes the tables (total information asymmetry), and
"method of dismissal" markets may not price it.

## Feasibility result (2026-06-19) — SIGNAL CONFIRMED

`python feasibility.py` (downloads Cricsheet tests/t20s/ipl JSON, attributes each
match's dismissals to its on-field umpires):

```
7,208 matches · 107,660 dismissals · baseline LBW share = 10.5%
260 umpires (>=150 dismissals): LBW share 2.8% -> 19.7%  (7x spread)
STABILITY: split-half correlation (1st vs 2nd half of career) = +0.448  -> STRONG
```

**This is the FIRST signal in the whole betting program to pass the make-or-break
persistence test.** Tennis (vs Pinnacle close), horses (vs HK pool), and MLB
strikeouts all scored ~0 / negative. Umpire LBW tendency is real and persistent.

## Caveats (signal != profit — gates remaining)
1. **Confounding:** raw per-umpire LBW share is inflated by WHERE they officiate
   (subcontinent spin venues -> more LBW). Predictable, but the true umpire effect
   needs venue/format/era controls.
2. **DRS** overturns marginal LBWs in Tests/internationals -> signal strongest in
   domestic/franchise comps with limited/no DRS (also the softest lines).
3. **PRICING** (unknown): is umpire identity already in "method of dismissal"
   lines? Needs a cricket odds feed to test.
4. **MONETIZATION** (the real risk): these markets are in-play, low-limit,
   UK/exchange-based, US-restricted.

## Next steps
1. Disentangle umpire effect from conditions (control for venue/format).
2. Acquire a cricket odds feed (method-of-dismissal) -> test if umpire is priced.
3. Confirm market access + limits.

Data: Cricsheet (https://cricsheet.org), free, CC-BY. Not committed (data/ is large).
