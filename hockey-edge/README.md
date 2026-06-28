# hockey-edge

NHL player **shots-on-goal (SOG)** prop model. The one sport-prediction angle that's
both modelable AND cashable from the US (US-legal, liquid, real limits) — the winner
of the multi-sport edge sweep.

## Model
    projected SOG = (player shots/60) x (projected TOI / 60) x (opponent factor)
- **shots/60** — the player's shot rate (stable skill).
- **projected TOI** — the one live input; supply from tonight's lines/role in-season.
- **opponent factor** — opp team SOG-against/game ÷ league avg (>1 allows more, <1 suppresses).

Data: free MoneyPuck season-summary CSVs (`skaters_YYYY.csv`, `teams_YYYY.csv`).
`feasibility.py` = the foundation test; `model.py` = the projector.

## Feasibility result (2026-06-19) — STRONGEST FOUNDATION OF ANY SPORT TESTED
`feasibility.py` over 4 seasons (~615 qualified skaters each):
```
shots/60 spread 1.6 -> 13.5 (Tkachuk, Ovechkin, Pastrnak top — data validated)
PERSISTENCE year N -> N+1:  shots/60 = +0.898 | SOG/game = +0.888  (1,536 pairs)
```
Shot rate is one of the most stable, predictable quantities in sports — vs cricket
umpire LBW +0.45 and goals ~0.35. The model's core input is rock-solid.

## The honest catch (foundation != edge)
A +0.90 persistence means the model PROJECTS SOG accurately — but so does the book
(SOG is the *easiest* stat to project, which cuts both ways). The edge is NOT in
projecting accurately; it's in the **residual the book misprices**: TOI/role changes
(injury, line shuffle, PP promotion), pace, back-to-backs, slow line moves on a
low-attention market. That is only testable against **live lines via CLV** — and
**NHL is offseason until ~October**, so this is a *build-now, prove-in-fall* play.

Also: edge is small (juice -115/-130), books limit prop winners, won't be $5k/mo alone.

## Next steps
1. DONE (offseason): foundation validated, projector built.
2. Sept: capture NHL SOG lines (opener->close) via the existing the-odds-api key (covers NHL).
3. Oct: CLV test over ~150-200 player-games — does the model's disagreement with the
   OPENER predict the CLOSE? Only bet if yes.

Data: MoneyPuck (moneypuck.com), free.
