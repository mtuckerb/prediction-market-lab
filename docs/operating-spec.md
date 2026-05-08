# Prediction Market Lab Operating Spec and Data Model

Status: initial implementation spec  
Experiment budget: **$50 bankroll**  
Normal stake: **$2–$3**  
Hard stake maximum: **$5**  
Open-exposure review threshold: **$15**  
Safety posture: **analyst/ops assistant only; human-directed trading only**

## 1. Purpose and operating boundaries

Prediction Market Lab is a small, deliberately constrained experiment for researching prediction-market opportunities, recording theses and human decisions, and measuring whether the process has enough calibration and discipline to justify scaling later.

The lab is not a trading bot, broker, wallet, exchange client, or credential manager. It may assist with analysis and recordkeeping only. A human must make every trade/no-trade decision and must execute any trade outside the system.

Hard experiment constants for the initial lab:

- Bankroll: **$50.00** total experiment capital.
- Normal stake: **$2.00–$3.00** per accepted position.
- Hard stake maximum: **$5.00** total exposure on any single market, including adds.
- Portfolio open-exposure review threshold: **$15.00** aggregate open exposure.
- Automated trading: forbidden.
- Credential storage: forbidden.
- Custody or movement of funds: forbidden.

## 2. Roles

- `analyst`: drafts candidates, theses, recommendations, mark notes, reviews, and scale-gate analysis.
- `operator`: records human decisions, manually entered fills, marks, resolutions, reviews, and discipline breaches.
- `human`: approves/rejects recommendations and executes any trade outside the system.

A software agent may act only as `analyst` or `operator`. It must never act as `human`.

## 3. Normative workflow

```text
candidate market
  -> thesis
  -> recommendation
  -> human decision
  -> position | no-trade | watchlist
  -> resolved
```

No trade record can exist without a prior candidate, thesis, recommendation, and approved human decision.

## 4. Data model

The persistence layer may be SQLite, Postgres, JSONL, or another durable store. The fields and validation rules below are normative. Store money as integer cents or exact decimals; do not use binary floating point for money. Store probabilities as decimals in `[0.0, 1.0]`.

Common fields on every persisted entity:

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `id` | UUID/string | yes | Stable primary key. |
| `created_at` | ISO-8601 datetime | yes | Creation time. |
| `updated_at` | ISO-8601 datetime | yes | Last mutation time. |
| `created_by` | string | yes | Actor id or role. |
| `notes` | markdown/string | no | Human-readable context. |

### 4.1 LabConfig

One active configuration controls bankroll limits, safety settings, and scale gates.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `id` | string | yes | Use `default` initially. |
| `status` | enum | yes | `draft`, `active`, `paused`, `closed`. |
| `bankroll_cents` | integer | yes | Must equal `5000` for the initial experiment. |
| `normal_stake_min_cents` | integer | yes | Must equal `200`. |
| `normal_stake_max_cents` | integer | yes | Must equal `300`. |
| `hard_stake_max_cents` | integer | yes | Must equal `500`. |
| `open_exposure_review_threshold_cents` | integer | yes | Must equal `1500`. |
| `base_currency` | string | yes | Initial value `USD`. |
| `allowed_platforms` | string[] | no | Empty means manually entered public platforms are allowed. |
| `automated_trading_enabled` | boolean | yes | Must be `false`. |
| `credential_storage_enabled` | boolean | yes | Must be `false`. |
| `fund_custody_enabled` | boolean | yes | Must be `false`. |
| `weekly_review_day` | enum/string | no | Suggested default `Sunday`. |
| `scale_gate_min_markets` | integer | yes | Initial value `20` resolved positions. |
| `scale_gate_min_weeks` | integer | yes | Initial value `8`. |
| `scale_gate_max_breach_rate` | decimal | yes | Initial value `0.05`. |
| `scale_gate_min_brier_improvement` | decimal | yes | Initial value `0.03`. |
| `scale_gate_min_net_roi` | decimal | yes | Initial value `0.00`. |

Initial config fixture:

```json
{
  "id": "default",
  "status": "active",
  "bankroll_cents": 5000,
  "normal_stake_min_cents": 200,
  "normal_stake_max_cents": 300,
  "hard_stake_max_cents": 500,
  "open_exposure_review_threshold_cents": 1500,
  "base_currency": "USD",
  "allowed_platforms": [],
  "automated_trading_enabled": false,
  "credential_storage_enabled": false,
  "fund_custody_enabled": false,
  "weekly_review_day": "Sunday",
  "scale_gate_min_markets": 20,
  "scale_gate_min_weeks": 8,
  "scale_gate_max_breach_rate": 0.05,
  "scale_gate_min_brier_improvement": 0.03,
  "scale_gate_min_net_roi": 0.0
}
```

### 4.2 CandidateMarket

A public market under consideration before a formal thesis exists.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `platform` | string | yes | Venue name only; no private account ids. |
| `external_market_id` | string | no | Public market identifier only. |
| `url` | string | no | Public URL only; no tokens/session ids. |
| `question` | string | yes | Exact market question. |
| `description` | string | no | Market description or summary. |
| `resolution_criteria` | string | yes | Must be explicit enough to score. |
| `close_time` | ISO-8601 datetime | no | Trading close. |
| `resolution_time` | ISO-8601 datetime | no | Expected resolution. |
| `outcomes` | object[] | yes | At least one tradable outcome. |
| `market_price` | decimal | no | Current target-side price/probability. |
| `liquidity_notes` | string | no | Spread, depth, fees, fill caveats. |
| `source_links` | string[] | no | Public research links. |
| `status` | enum | yes | See state machine. |
| `rejection_reason` | enum/string | no | Required when rejected. |

### 4.3 Thesis

A forecast and rationale for a candidate market.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `candidate_market_id` | FK | yes | Links to CandidateMarket. |
| `target_outcome` | string | yes | Outcome being evaluated. |
| `market_price_at_thesis` | decimal | yes | In `[0.0, 1.0]`. |
| `estimated_probability` | decimal | yes | In `[0.0, 1.0]`. |
| `edge` | decimal | yes | `estimated_probability - market_price_at_thesis` for YES-style buys; document inversion for NO. |
| `confidence` | enum | yes | `low`, `medium`, `high`; never bypasses caps. |
| `time_horizon` | string | yes | Expected hold/resolution horizon. |
| `evidence_for` | string[] | yes | At least one item. |
| `evidence_against` | string[] | yes | At least one item. |
| `base_rates` | string | no | Relevant base-rate reference. |
| `assumptions` | string[] | yes | At least one item. |
| `disconfirming_signals` | string[] | yes | At least one item. |
| `validation_status` | enum | yes | `pending`, `valid`, `invalid`. |
| `validation_errors` | string[] | no | Required if invalid. |
| `status` | enum | yes | See state machine. |

Theses are append-only after recommendation. Material post-recommendation edits require a new thesis version or a `post_hoc_thesis_edit` discipline breach.

### 4.4 Recommendation

The analyst's proposed action derived from a valid thesis.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `thesis_id` | FK | yes | Must reference a valid thesis. |
| `action` | enum | yes | `buy_yes`, `buy_no`, `sell_or_reduce`, `hold`, `watchlist`, `no_trade`. |
| `recommended_stake_cents` | integer | no | Required for buy actions; normal `200`–`300`, hard max `500`. |
| `stake_rationale` | string | conditional | Required if stake is outside normal range. |
| `max_acceptable_price` | decimal | conditional | Required for buy actions. |
| `min_acceptable_price` | decimal | conditional | Required for sell/reduce actions. |
| `expected_value_notes` | string | yes | Explain edge and downside. |
| `risk_notes` | string | yes | Include liquidity, ambiguity, correlation, and exposure. |
| `no_trade_triggers_checked` | string[] | yes | List all evaluated triggers. |
| `open_exposure_before_cents` | integer | yes | Computed at recommendation time. |
| `open_exposure_after_if_accepted_cents` | integer | yes | Computed for buy actions. |
| `requires_exposure_review` | boolean | yes | True if after-accepted exposure is `>= 1500`. |
| `status` | enum | yes | `draft`, `ready_for_decision`, `withdrawn`, `decided`. |

### 4.5 Decision

A human's decision about a recommendation.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `recommendation_id` | FK | yes | Must be `ready_for_decision`. |
| `decision` | enum | yes | `approved`, `rejected`, `deferred`, `watchlist`, `no_trade`. |
| `decided_by` | string | yes | Human identifier; must not be an agent/system id. |
| `decided_at` | ISO-8601 datetime | yes | Decision time. |
| `approved_stake_cents` | integer | conditional | Required for approved buy; must be `> 0` and `<= 500`. |
| `approved_limit_price` | decimal | conditional | Required for approved buy/sell. |
| `rationale` | string | yes | Human rationale or acknowledgement. |
| `conditions` | string[] | no | e.g. only if price stays below limit. |

### 4.6 Position

A manually entered record of an externally executed trade. The system must not execute trades.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `decision_id` | FK | yes | Must reference an approved human decision. |
| `candidate_market_id` | FK | yes | Denormalized for query convenience. |
| `side` | enum/string | yes | `yes`, `no`, or platform outcome id. |
| `status` | enum | yes | `open`, `reduced`, `closed`, `resolved_won`, `resolved_lost`, `voided`. |
| `opened_at` | ISO-8601 datetime | yes | Must be after decision time. |
| `stake_cents` | integer | yes | `> 0`; total market stake/adds must be `<= 500`. |
| `avg_entry_price` | decimal | yes | In `[0.0, 1.0]`. |
| `shares` | decimal | yes | Manual entry. |
| `fees_cents` | integer | no | Default `0`. |
| `max_loss_cents` | integer | yes | Counts toward open exposure. |
| `current_mark_price` | decimal | no | Latest mark. |
| `unrealized_pnl_cents` | integer | no | Optional computed value. |
| `realized_pnl_cents` | integer | conditional | Required on closed/resolved. |
| `resolution_outcome` | string | conditional | Required on resolved. |
| `resolved_at` | ISO-8601 datetime | conditional | Required on resolved. |

### 4.7 MarketMark

A timestamped market state snapshot.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `candidate_market_id` | FK | yes | Market being marked. |
| `position_id` | FK | no | Required for position-specific P/L marks. |
| `marked_at` | ISO-8601 datetime | yes | Observation time. |
| `price` | decimal | yes | In `[0.0, 1.0]`. |
| `bid` | decimal | no | In `[0.0, 1.0]`. |
| `ask` | decimal | no | In `[0.0, 1.0]`. |
| `liquidity_notes` | string | no | Spread, depth, fill risk. |
| `source` | enum/string | yes | `manual`, `public_page`, `csv_import`; never private credentials. |
| `mark_notes` | string | no | Context. |

### 4.8 WeeklyReview

A periodic operating review.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `period_start` | date | yes | Inclusive. |
| `period_end` | date | yes | Inclusive and non-overlapping with other reviews. |
| `bankroll_start_cents` | integer | yes | Manual/computed. |
| `bankroll_end_cents` | integer | yes | Manual/computed. |
| `open_exposure_cents` | integer | yes | Computed from open positions. |
| `positions_opened` | integer | yes | Count. |
| `positions_resolved` | integer | yes | Count. |
| `realized_pnl_cents` | integer | yes | Period realized P/L. |
| `unrealized_pnl_cents` | integer | no | Optional mark-to-market. |
| `brier_score_lab` | decimal | no | For resolved positions with thesis probabilities. |
| `brier_score_market` | decimal | no | Market baseline. |
| `discipline_breach_count` | integer | yes | Include zero. |
| `lessons` | string[] | yes | At least one item. |
| `next_week_adjustments` | string[] | no | Cannot loosen hard caps without config migration. |

### 4.9 DisciplineBreach

A rule violation, near miss, or manual override.

| Field | Type | Required | Rule |
|---|---:|---:|---|
| `breach_type` | enum | yes | See list below. |
| `severity` | enum | yes | `minor`, `major`, `critical`. |
| `related_entity_type` | enum | no | Entity type. |
| `related_entity_id` | string | no | Entity id. |
| `occurred_at` | ISO-8601 datetime | yes | Time of breach/near miss. |
| `description` | string | yes | What happened. |
| `impact_cents` | integer | no | Financial impact if any. |
| `corrective_action` | string | yes | Required. |
| `resolved_at` | ISO-8601 datetime | no | Required before closing critical breach. |

Initial breach types:

- `stake_above_normal_without_rationale`
- `stake_above_hard_max`
- `open_exposure_review_missed`
- `trade_without_recorded_decision`
- `credential_or_custody_boundary_risk`
- `automated_trading_boundary_risk`
- `ambiguous_resolution_ignored`
- `missing_weekly_review`
- `post_hoc_thesis_edit`
- `other`

## 5. State machines

### 5.1 CandidateMarket status

Allowed statuses: `discovered`, `screening`, `rejected`, `thesis_opened`, `watchlist`, `recommended`, `position_opened`, `no_trade`, `resolved`, `archived`.

| From | To | Required conditions |
|---|---|---|
| none | `discovered` | Candidate has question and platform. |
| `discovered` | `screening` | Resolution criteria and outcomes added. |
| `discovered`, `screening` | `rejected` | `rejection_reason` set. |
| `screening` | `thesis_opened` | Thesis created. |
| `screening`, `thesis_opened` | `watchlist` | Watchlist recommendation/decision exists. |
| `thesis_opened` | `recommended` | Valid thesis and ready recommendation. |
| `recommended` | `position_opened` | Approved decision and manually recorded position. |
| `recommended`, `watchlist`, `thesis_opened` | `no_trade` | No-trade recommendation or human decision recorded. |
| `position_opened`, `no_trade`, `watchlist` | `resolved` | Resolution outcome recorded or market concluded. |
| `rejected`, `resolved`, `no_trade` | `archived` | No active work remains. |

### 5.2 Thesis status

Allowed statuses: `draft`, `validating`, `valid`, `invalid`, `recommended`, `retired`, `resolved`.

| From | To | Required conditions |
|---|---|---|
| none | `draft` | Candidate exists. |
| `draft` | `validating` | Required thesis fields present. |
| `validating` | `valid` | Validation passes. |
| `validating`, `draft` | `invalid` | Validation errors recorded. |
| `valid` | `recommended` | Recommendation created. |
| `valid`, `recommended` | `retired` | Reason recorded. |
| `recommended`, `retired` | `resolved` | Market resolved and forecast scored if applicable. |

### 5.3 Recommendation status

Allowed statuses: `draft`, `ready_for_decision`, `withdrawn`, `decided`.

| From | To | Required conditions |
|---|---|---|
| none | `draft` | Valid thesis exists. |
| `draft` | `ready_for_decision` | Validation passes and no-trade triggers evaluated. |
| `ready_for_decision` | `withdrawn` | Analyst withdraws before decision; reason recorded. |
| `ready_for_decision` | `decided` | Human decision recorded. |

### 5.4 Decision outcome routing

| Decision | Next state |
|---|---|
| `approved` | Await manual position entry, then CandidateMarket `position_opened`. |
| `rejected` | CandidateMarket `no_trade` unless explicitly watchlisted. |
| `deferred` | CandidateMarket `watchlist`. |
| `watchlist` | CandidateMarket `watchlist`. |
| `no_trade` | CandidateMarket `no_trade`. |

### 5.5 Position status

Allowed statuses: `open`, `reduced`, `closed`, `resolved_won`, `resolved_lost`, `voided`.

| From | To | Required conditions |
|---|---|---|
| none | `open` | Approved decision and manual fill details. |
| `open` | `reduced` | Manual reduction recorded; remaining shares > 0. |
| `open`, `reduced` | `closed` | Manual exit recorded before resolution. |
| `open`, `reduced` | `resolved_won` | Resolution recorded; realized P/L computed. |
| `open`, `reduced` | `resolved_lost` | Resolution recorded; realized P/L computed. |
| `open`, `reduced` | `voided` | Market void/cancel recorded. |

## 6. Validation rules

### 6.1 Candidate validation

A candidate can enter `screening` only if:

- `platform`, `question`, `resolution_criteria`, and `outcomes` are present.
- `outcomes` contains at least one tradable outcome.
- Stored URLs are public and contain no tokens, session ids, API keys, account ids, or private query parameters.

Reject or no-trade if resolution is ambiguous, liquidity is insufficient for a $2–$3 trade, information access is inappropriate, or the market appears illegal/platform-prohibited/jurisdictionally questionable.

### 6.2 Thesis validation

A thesis can become `valid` only if:

- Candidate is active for analysis.
- `estimated_probability` and `market_price_at_thesis` are in `[0.0, 1.0]`.
- `edge` is present and computable.
- Evidence exists both for and against.
- At least one assumption and one disconfirming signal are listed.
- Resolution criteria remain clear.
- The thesis was created before recommendation and before any position entry.

### 6.3 Recommendation validation

A recommendation can become `ready_for_decision` only if:

- Linked thesis is `valid`.
- Buy actions include stake, max acceptable price, EV notes, and risk notes.
- `recommended_stake_cents <= 500`.
- Stakes outside `200`–`300` cents include explicit rationale.
- Open exposure before and after acceptance are computed.
- If after-accepted exposure is `>= 1500`, `requires_exposure_review` is true and risk notes include the exposure review.
- All no-trade triggers were evaluated.

### 6.4 Decision validation

A decision can be recorded only if:

- Recommendation is `ready_for_decision`.
- `decided_by` is a human identifier, not an agent/system identifier.
- Approved buy decisions include stake and limit price.
- Approved stake is `> 0` and `<= 500`.
- Approved stake does not cause the market's total stake/adds to exceed `500` cents.
- Approval does not bypass a required exposure review.

### 6.5 Position validation

A position can be opened only if:

- An approved human decision exists.
- Fill details are manually entered after the decision time.
- Total stake/adds for the market remain `<= 500` cents.
- Aggregate open exposure is recomputed after entry.
- If aggregate open exposure is `>= 1500` cents, an immediate or weekly exposure-review item is created.

### 6.6 Mark, review, and scoring validation

- Market marks must be timestamped and source-labeled.
- Weekly reviews must cover non-overlapping ranges.
- Weekly reviews must include breach count, even if zero.
- Resolved positions must have outcome and realized P/L.
- Brier scoring uses the thesis probability recorded before decision/entry; never use post-resolution edited probabilities.

## 7. No-trade triggers

### 7.1 Hard no-trade triggers

Hard triggers cannot be overridden inside the lab:

- Automated trading would be required.
- Credential storage, API keys, private sessions, or custody of funds would be required.
- Stake would exceed **$5.00** for a single market.
- Trade would exceed available experiment bankroll.
- Trade would violate platform rules, law, or jurisdictional constraints.
- Resolution depends on non-public, private, or improperly obtained information.
- Market terms are too ambiguous to score honestly.
- Human decision is absent.

### 7.2 Soft no-trade or watchlist triggers

These should force `no_trade` or `watchlist` unless a human records an explicit rationale and no hard trigger applies:

- Edge is too small after spread/fees/slippage.
- Liquidity is insufficient for a $2–$3 stake without material price impact.
- Thesis relies on a single fragile source.
- Evidence against is stronger than evidence for.
- Resolution date is too far away for the experiment's learning cycle.
- Correlated exposure would dominate the $50 bankroll.
- Open exposure after trade would be **$15.00 or more** and has not been reviewed.
- Market price moved beyond the approved limit.
- Recommendation is stale; default stale threshold is 48 hours unless configured otherwise.

## 8. Safety boundaries and implementation guardrails

Allowed:

- Public market discovery.
- Manual candidate entry.
- Thesis drafting and validation.
- Recommendation drafting.
- Human decision recording.
- Manual fill/position recording after external human execution.
- Manual market marks and weekly reviews.
- Metrics and scale-gate reporting.

Forbidden:

- Automated trade placement.
- Semi-automated order placement requiring only confirmation.
- Storing exchange credentials, API keys, session cookies, private account identifiers, seed phrases, payment details, or bank information.
- Custodying or moving funds.
- Scraping private/account pages.
- Circumventing rate limits, platform controls, geofencing, KYC, or terms of service.
- Presenting recommendations as guaranteed returns or financial advice.

Implementation guardrails:

- Do not implement broker/exchange API clients.
- Do not add secrets management for market venues.
- Do not add payment or wallet primitives.
- Keep all execution/fill fields manual-entry only.
- Add tests that assert `automated_trading_enabled`, `credential_storage_enabled`, and `fund_custody_enabled` cannot be true in the initial lab config.

## 9. Metrics and scale gates

Scale gates determine whether the experiment is eligible for a larger bankroll or broader analysis automation. They do not authorize automated trading.

### 9.1 Required raw metrics

| Metric | Definition |
|---|---|
| `starting_bankroll_cents` | Fixed initial bankroll: `5000`. |
| `current_bankroll_cents` | Cash plus realized P/L, excluding unresolved mark-to-market unless separately reported. |
| `open_exposure_cents` | Sum of `max_loss_cents` for open/reduced positions. |
| `open_exposure_pct_bankroll` | `open_exposure_cents / 5000`. |
| `position_count_opened` | Count of positions opened. |
| `position_count_resolved` | Count resolved won/lost/voided. |
| `position_count_no_trade` | Count of no-trade outcomes. |
| `watchlist_count` | Count of watchlist outcomes. |
| `total_staked_cents` | Sum stake for opened positions. |
| `gross_realized_pnl_cents` | Sum realized P/L before fees, if tracked. |
| `fees_cents` | Sum fees. |
| `net_realized_pnl_cents` | Realized P/L after fees. |
| `net_roi` | `net_realized_pnl_cents / total_staked_cents`. |
| `bankroll_return` | `net_realized_pnl_cents / 5000`. |
| `hit_rate` | Resolved wins / resolved non-void positions. |
| `avg_stake_cents` | Mean stake. |
| `max_stake_cents` | Maximum stake; must be `<= 500`. |
| `largest_loss_cents` | Worst realized position P/L. |
| `brier_score_lab` | Mean `(forecast_probability - outcome)^2` for resolved positions. |
| `brier_score_market` | Mean `(market_probability_at_thesis_or_entry - outcome)^2`. |
| `brier_improvement` | `brier_score_market - brier_score_lab`; positive means lab forecasts beat market baseline. |
| `calibration_by_bucket` | Forecast bucket, count, average forecast, observed frequency. |
| `closing_line_value` | Difference between entry price and later mark/close price where available. |
| `discipline_breach_count` | Total breaches. |
| `discipline_breach_rate` | Breaches / recommendations or positions; denominator must be stated. |
| `hard_breach_count` | Count of critical safety/cap breaches; must be zero to scale. |
| `weekly_review_completion_rate` | Completed weekly reviews / expected weekly reviews. |

### 9.2 Scale-gate eligibility

The lab is eligible to recommend scaling only if all are true:

1. At least **8 operating weeks** have elapsed.
2. At least **20 positions** have resolved.
3. `hard_breach_count == 0`.
4. `max_stake_cents <= 500`.
5. No automated trading, credential storage, or custody boundary breach occurred.
6. Weekly review completion rate is at least `0.90`.
7. Discipline breach rate is no more than `0.05`.
8. Net ROI is at least `0.00` after fees.
9. Brier improvement is at least `0.03`.
10. A human-readable scale review explains whether results appear repeatable or luck/concentration-driven.

Passing scale gates must not automatically increase limits. Scaling requires a new human-approved LabConfig migration.

## 10. CLI/API workflows to implement

A developer should be able to implement these commands/endpoints directly from this spec:

1. `config show`
2. `config validate`
3. `candidate create`
4. `candidate screen`
5. `candidate reject`
6. `thesis create`
7. `thesis validate`
8. `recommendation create`
9. `recommendation validate`
10. `decision record`
11. `position record-open`
12. `mark record`
13. `position resolve`
14. `review weekly-create`
15. `breach record`
16. `metrics report`
17. `scale-gate evaluate`

Required command behavior:

- Every command validates state transitions before writing.
- Every write updates `updated_at`.
- Recommendation validation computes exposure from currently open positions.
- Position opening is impossible without an approved human decision.
- Metrics can be rebuilt from persisted entities without hidden state.
- All financial values use cents or exact decimal types.

## 11. Minimum test cases

- Lab config rejects bankroll other than `5000` for initial experiment.
- Lab config rejects `automated_trading_enabled=true`.
- Lab config rejects `credential_storage_enabled=true`.
- Lab config rejects `fund_custody_enabled=true`.
- Candidate cannot become thesis-ready without resolution criteria.
- Thesis cannot become valid without evidence for and against.
- Recommendation cannot be ready if stake exceeds `500` cents.
- Recommendation outside `200`–`300` cents requires rationale.
- Recommendation at or above `1500` cents open exposure requires exposure review.
- Decision cannot be approved by an agent/system actor.
- Position cannot open without approved decision.
- Position cannot exceed `500` cents total market stake.
- Resolved position requires outcome and realized P/L.
- Brier score uses pre-entry thesis probability.
- Scale gate fails with any critical breach.

## 12. Open implementation choices

These choices do not block the first implementation:

- Persistence backend: SQLite is recommended for deterministic local CLI workflows; JSONL is acceptable only for a tiny prototype.
- Entity versioning: recommended for Thesis and LabConfig.
- Public market data import: manual-first; CSV/public-page import can be added later without credentials.
- Mark-to-market policy: decide whether weekly reviews use bid, ask, midpoint, or conservative exit estimate.
