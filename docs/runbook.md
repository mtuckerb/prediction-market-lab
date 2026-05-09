# First $50 Prediction-Market Experiment Runbook

This runbook describes the human operating workflow for the first small-bankroll prediction-market experiment. The repository is a research and decision-support lab, not an automated trading system: a human must make every final trade/no-trade decision.

## Experiment purpose

Use a fixed $50 bankroll to test whether a disciplined thesis-writing process improves judgment quality and trading discipline in prediction markets.

The primary learning target is process quality, not profit. Profit/loss is evidence, but a tiny sample can be noisy.

## Hard safety rules

1. **Human-only execution:** no agent, script, or model may place trades.
2. **Fixed initial bankroll:** start with exactly **$50** allocated to this experiment.
3. **Position sizing:**
   - Default position: **$1** risked per approved thesis.
   - Maximum initial position: **$2** risked on any single market.
   - Maximum total open risk: **$10** across all markets during the first $50 experiment.
   - Never increase a position unless a new thesis entry is written and the market still passes the triage checklist.
4. **No revenge trading:** after a loss, surprise, bad fill, or emotional spike, do not immediately place a compensating trade. Stop for the session, write the event in the log, and wait until the next scheduled review window before considering any new trade.
5. **No thesis, no trade:** every real-money trade must have a completed thesis file before entry.
6. **No ambiguous resolution:** skip markets whose resolution criteria cannot be restated clearly in the thesis.
7. **No secret leakage:** do not put credentials, account balances beyond the experiment bankroll, or private account identifiers in thesis files.

## Daily workflow

Use this once per day on days when you are actively monitoring markets.

1. **Open the session intentionally**
   - Record the date and available time.
   - Confirm the session goal: triage, thesis writing, monitoring, or weekly review.
   - Confirm emotional state is acceptable: no acute frustration, fatigue, or urgency to win back losses.

2. **Review existing open positions**
   - Read each active thesis.
   - Check whether any new evidence changes the original forecast.
   - Record only material changes: new evidence, probability update, decision to hold, reduce, exit, or do nothing.
   - Do not add exposure unless the updated thesis justifies it and position-size limits still permit it.

3. **Triage candidate markets**
   - Use `docs/market-triage-checklist.md`.
   - Reject markets that fail resolution clarity, source availability, liquidity/spread sanity, or ethical/legal comfort.
   - For any market that passes triage, create a thesis from `docs/thesis-template.md`.

4. **Write or update thesis before any action**
   - Fill the validator-aligned fields exactly: `title`, `current_probability`, and `evidence`.
   - Add market URL, resolution criteria, base rate, source notes, forecast, edge, risk, and planned action.
   - State the maximum dollars at risk before trading.

5. **Decision gate**
   - Trade only if all are true:
     - The thesis is complete.
     - The market passes triage.
     - The edge is explainable without hand-waving.
     - The proposed risk is within limits.
     - You would still accept the trade after a 10-minute delay.
   - Otherwise record `Decision: no trade` or `Decision: watch`.

6. **Session close**
   - Record trades made, no-trade decisions, and open questions.
   - Note any rule violations or near misses.
   - Stop once the session budget is used. Do not keep browsing markets to force action.

## Per-session workflow

Use this shorter checklist at the start of each focused session.

- [ ] I know whether this is a triage, thesis, monitoring, or review session.
- [ ] I am not trying to recover a recent loss.
- [ ] I have the current bankroll and open-risk totals.
- [ ] I will not place a trade without a completed thesis.
- [ ] I will cap new risk at $1 by default and $2 maximum per market.
- [ ] I will stop if I feel urgency, frustration, or compulsion.

## Thesis numbering and storage

Suggested naming pattern:

```text
theses/YYYY-MM-DD-short-market-slug.md
```

Each thesis should be independently readable. If a market is revisited later, append an update section instead of overwriting the original reasoning.

## Week 1 review: continue, pause, or scale

At the end of week 1, complete `docs/weekly-review-template.md` and choose one path.

### Continue at the same size

Continue with the same $50 bankroll and same limits if:

- At least 5 theses were written or the week had a clear reason for fewer opportunities.
- 100% of trades had completed theses before entry.
- No revenge trades occurred.
- No single-market risk exceeded $2.
- Notes are detailed enough that a future reviewer can understand the decision.
- Losses, if any, were inside planned risk limits.

### Pause

Pause new trades for at least one week if any are true:

- A revenge trade occurred.
- A trade was placed without a thesis.
- Position-size limits were broken.
- Multiple theses are too thin to audit.
- Emotional state or time pressure is driving decisions.
- You cannot explain whether losses came from bad luck, bad process, or unclear resolution.

During a pause, paper-trade only and improve templates/checklists.

### Scale

Do **not** scale above the $50 experiment solely because week 1 was profitable. Scaling after week 1 is allowed only as a process scale, not a bankroll scale:

- increase the number of paper theses,
- improve sourcing,
- tighten triage,
- add review cadence.

Keep real-money position limits unchanged until at least 20 completed theses exist.

## 20+ thesis review: continue, pause, or scale

After 20 or more completed theses, review process and outcomes together.

### Continue at current size

Continue with the $50 bankroll and existing limits if:

- Rule compliance is perfect or near-perfect with documented corrective actions.
- Calibration notes show learning, even if P/L is noisy.
- Average thesis quality is improving.
- No unresolved market caused avoidable confusion.

### Pause

Pause real-money activity if:

- Any rule violation repeats.
- Most outcomes cannot be evaluated against the original reasoning.
- Losses cluster around avoidable errors: unclear resolution, bad sources, chasing, or oversizing.
- The process feels compulsive rather than analytical.

### Scale cautiously

Consider scaling only if all are true:

- At least 20 theses are complete.
- At least 10 real-money trades followed the process, or the no-trade decisions were explicitly useful.
- No revenge trades occurred.
- No position-size rule was broken.
- Expected-value reasoning was recorded before each trade.
- Review shows at least one repeatable edge or repeatable avoidance rule.

If scaling is approved, scale slowly:

- Increase bankroll by no more than 2x at a time.
- Keep maximum risk per market at 2% to 4% of bankroll.
- Keep a hard total-open-risk cap of 20% of bankroll.
- Re-run the 20-thesis review before each future scale-up.

## Metrics to track

- Thesis count.
- Number of trades and no-trade decisions.
- Rule violations and near misses.
- Realized P/L and unresolved marked-to-market P/L.
- Brier score or simple calibration buckets if enough resolved predictions exist.
- Most common reasons for skipping markets.
- Evidence sources that were useful or misleading.

## What good looks like

A good first experiment ends with a small set of auditable theses, clear examples of good and bad market selection, and no broken discipline rules. A profitable but sloppy run is a failed process. An unprofitable but disciplined run can still be a useful experiment.
