# Market Triage Checklist

Use this before writing a full thesis or placing any real-money trade.

## Validator fields to capture if promoted to thesis

```yaml
title: "<exact market question title>"
current_probability: 0.50
evidence:
  - "<initial source or evidence snippet>"
```

## 1. Scope and ethics

- [ ] Market is legal and available to the human operator.
- [ ] Market does not require private, non-public, or unethical information.
- [ ] Market is within the experiment's learning purpose.
- [ ] I am comfortable writing down the reasoning for this market.

## 2. Resolution clarity

- [ ] The title/question is unambiguous.
- [ ] The resolution source is named or inferable.
- [ ] The resolution date/window is clear.
- [ ] I can restate the resolution criteria in one or two sentences.
- [ ] I can identify at least one plausible ambiguity and decide whether it is acceptable.

Reject if resolution criteria are vague, subjective, or likely to be disputed.

## 3. Evidence availability

- [ ] At least two independent evidence sources are available or likely to become available.
- [ ] Evidence can be checked without special access.
- [ ] The evidence is timely enough for the market horizon.
- [ ] I can identify what evidence would change my mind.

Reject if the thesis would be mostly vibes, rumor, or inaccessible information.

## 4. Probability and edge

- [ ] Current market probability can be recorded as `current_probability` between 0.0 and 1.0.
- [ ] I can estimate my own probability before seeing or acting on size.
- [ ] The difference between my estimate and the market is explainable.
- [ ] The edge is not solely based on wanting action.

Reject if I cannot explain the edge simply.

## 5. Liquidity and cost

- [ ] Spread is acceptable for a $1-$2 test position.
- [ ] Fees, slippage, and exit difficulty do not erase the edge.
- [ ] Position can be entered without chasing price movement.
- [ ] I am willing to hold to resolution if exit liquidity disappears.

Reject if the only available fill requires a bad price.

## 6. Sizing and bankroll rules

- [ ] Default risk is $1.
- [ ] Maximum initial risk is $2.
- [ ] Total open risk after entry would be $10 or less.
- [ ] This is not a revenge trade.
- [ ] This is not an attempt to force volume for the experiment.

Reject if any sizing rule fails.

## 7. Decision

- [ ] Promote to thesis.
- [ ] Watch only.
- [ ] Reject.

### Notes

- **Reason:** <why promote/watch/reject>
- **Next check date:** <YYYY-MM-DD or N/A>
