# Thesis: <market title>

## Validator fields

These fields must stay aligned with the current `MarketQuestion` validator/data structure.

```yaml
title: "<exact market question title>"
current_probability: 0.50
evidence:
  - "<source or evidence snippet 1>"
  - "<source or evidence snippet 2>"
```

## Market metadata

- **Market URL:** <link>
- **Platform:** <platform>
- **Date opened:** <YYYY-MM-DD>
- **Planned review date:** <YYYY-MM-DD>
- **Resolution date/window:** <YYYY-MM-DD or description>
- **Resolution criteria, in my words:** <clear restatement>

## Forecast

- **Market-implied probability:** <0-100%>
- **My probability:** <0-100%>
- **Direction:** <YES / NO / no trade / watch>
- **Estimated edge:** <difference and why it matters>
- **Confidence:** <low / medium / high>

## Evidence

### Sources supporting YES

- <source, date, key point>

### Sources supporting NO

- <source, date, key point>

### Base rate / reference class

- <reference class and rough base rate>

### Key uncertainty

- <what would most change this forecast?>

## Risk and sizing

- **Experiment bankroll:** $50
- **Proposed dollars at risk:** $<1 default, 2 maximum>
- **Total open risk after trade:** $<must be <=10 during first experiment>
- **Liquidity/spread note:** <acceptable / not acceptable and why>
- **Worst-case loss:** $<amount>
- **Rule check:** no thesis, no trade; no revenge trade; size within limits.

## Decision

- **Decision:** <trade / no trade / watch>
- **Action:** <buy YES, buy NO, no action, set reminder, etc.>
- **Limit/price constraint:** <price or N/A>
- **Reason for decision:** <short paragraph>

## Updates

### <YYYY-MM-DD>

- **New evidence:** <what changed?>
- **Updated probability:** <0-100%>
- **Action:** <hold / exit / reduce / add with new thesis / no action>

## Resolution review

- **Resolved outcome:** <YES / NO / N/A>
- **P/L:** $<amount>
- **Was the thesis directionally right?** <yes/no/mixed>
- **What did I learn?** <process lesson>
- **Rule violations or near misses:** <none or describe>
