# Thesis: Will Example City report measurable rain on 2026-06-01?

This is fake/example data for template demonstration only. It is not a real market recommendation.

## Validator fields

```yaml
title: "Will Example City report measurable rain on 2026-06-01?"
current_probability: 0.42
evidence:
  - "Example Weather Service 7-day outlook shows a weak front arriving near 2026-06-01."
  - "Example Climate Archive says measurable rain occurred on 9 of the last 30 comparable dates."
  - "Example local forecast discussion says model disagreement remains high."
```

## Market metadata

- **Market URL:** https://example.invalid/markets/example-city-rain-2026-06-01
- **Platform:** Example Markets
- **Date opened:** 2026-05-25
- **Planned review date:** 2026-05-29
- **Resolution date/window:** 2026-06-02 after official daily weather report
- **Resolution criteria, in my words:** The market resolves YES if the official Example City weather station records at least 0.01 inches of rain for calendar date 2026-06-01 local time. Trace precipitation does not count.

## Forecast

- **Market-implied probability:** 42%
- **My probability:** 48%
- **Direction:** YES
- **Estimated edge:** +6 percentage points; small possible edge from forecast update lag, but uncertainty is high.
- **Confidence:** low

## Evidence

### Sources supporting YES

- Example Weather Service, 2026-05-25: weak front may arrive near the target date.
- Example Ensemble Dashboard, 2026-05-25: 11 of 25 fake ensemble members show measurable rain.

### Sources supporting NO

- Example Climate Archive, accessed 2026-05-25: comparable late-May/early-June dates are often dry.
- Example Forecast Discussion, 2026-05-25: timing confidence is low and the front may pass north.

### Base rate / reference class

- Fake historical sample: measurable rain on 9 of 30 comparable dates, or 30%.
- Short-range forecast raises this above base rate, but not enough for a large position.

### Key uncertainty

- Whether the front arrives during the resolution window or after midnight.

## Risk and sizing

- **Experiment bankroll:** $50
- **Proposed dollars at risk:** $1
- **Total open risk after trade:** $4
- **Liquidity/spread note:** Fake order book shows a 40/44 spread; acceptable only with a 42% or better limit.
- **Worst-case loss:** $1
- **Rule check:** no thesis, no trade; no revenge trade; size within limits.

## Decision

- **Decision:** watch
- **Action:** No trade unless YES is available at 42% or lower and the forecast still supports at least 48%.
- **Limit/price constraint:** YES <= 42%
- **Reason for decision:** The thesis suggests a small edge, but the fake evidence is mixed and timing uncertainty is the dominant risk. A $1 maximum position is appropriate only if price is favorable; otherwise this is a useful watchlist market.

## Updates

### 2026-05-29

- **New evidence:** Fake updated model run shifted the front later by 12 hours.
- **Updated probability:** 38%
- **Action:** No trade; remove from active watch unless price becomes unusually favorable.

## Resolution review

- **Resolved outcome:** N/A in sample
- **P/L:** $0
- **Was the thesis directionally right?** N/A
- **What did I learn?** Weather timing markets need careful resolution-window analysis and should remain tiny even when the directional setup looks plausible.
- **Rule violations or near misses:** None.
