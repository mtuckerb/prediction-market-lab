# Prediction Market Lab

Prediction Market Lab is a small, deterministic local codebase for researching prediction-market questions, capturing evidence, and producing decision-support outputs for a human operator.

This repository is intentionally **not** an automated betting or trading system. It may help organize market hypotheses, evidence, probability estimates, and review notes, but **a human makes every final trade decision**.

## Minimal stack

- Python 3.11+ standard library only for the initial scaffold.
- `unittest` for tests.
- `compileall` as the first local syntax/check gate.
- `make` as the command runner.

The initial stack avoids package-manager and network dependency variance so local agent runs stay deterministic.

## Human / agent responsibility split

Humans are responsible for:

- Choosing which markets are in scope.
- Reviewing source quality, risk, and ethical/legal constraints.
- Making final trade/no-trade decisions.
- Supplying any real credentials through local environment variables only.

Agents are responsible for:

- Maintaining deterministic, testable code and documentation.
- Producing transparent analysis artifacts and caveats.
- Refusing to place trades or automate betting decisions.
- Keeping secrets out of the repository.

## Repository layout

```text
prediction-market-lab/
├── .env.example              # Non-secret local configuration template
├── .github/workflows/ci.yml  # First verification workflow
├── Makefile                  # Local check/test commands
├── README.md                 # Project purpose and operating boundaries
├── src/prediction_market_lab/
│   ├── __init__.py
│   ├── config.py
│   └── market.py
└── tests/
    ├── __init__.py
    ├── test_config.py
    └── test_market.py
```

## Local setup

No install step is required for the initial scaffold. From the repository root, run:

```bash
make check
```

This runs:

```bash
python -m compileall src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Configuration

Copy `.env.example` to `.env` for local overrides if needed. The sample contains no secrets and is safe to commit. Do not commit `.env` or real API credentials.

## Operator CLI

The local operator CLI stores deterministic JSON records under `data/operator_store.json` by default. It is for research bookkeeping only: it never places trades and never calls exchange or betting APIs.

Run commands with `PYTHONPATH=src python -m prediction_market_lab.operator ...`. Add `--store path/to/file.json` before the subcommand to use a different local store.

### Candidate markets

Create or update a manually sourced candidate market:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator candidate create \
  --id cand-001 \
  --title "Will the sample event resolve YES by 2026-06-01?" \
  --platform manual \
  --url "https://example.invalid/market" \
  --market-probability 0.42 \
  --notes "Imported by human operator"
```

Import a JSON list of candidates:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator candidate import-json candidates.json
```

Each imported item must include `candidate_id` and `title`; optional fields are `url`, `platform`, `market_probability`, and `notes`.

### Theses

Create or update a thesis:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator thesis upsert \
  --id thesis-001 \
  --candidate-id cand-001 \
  --question "Will the sample event resolve YES by 2026-06-01?" \
  --belief-probability 0.57 \
  --market-probability 0.42 \
  --evidence "Primary source supports YES" \
  --evidence "Comparable historical base rate is 60%" \
  --risk "Resolution wording is ambiguous" \
  --resolution-criteria "Official market resolver posts YES" \
  --time-horizon "2026-06-01" \
  --expected-value-notes "15 percentage point edge before costs"
```

Validate a thesis:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator thesis validate --id thesis-001
```

A thesis is labeled `non-actionable` unless it has a question, belief probability, market probability, evidence, risks/caveats, resolution criteria, time horizon, and expected-value notes. Invalid probabilities are rejected clearly. `trade` recommendations are refused for non-actionable theses; `no-trade` and `watchlist` records may still be captured with the validation errors attached.

### Recommendations and human decisions

Record an analysis recommendation:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator recommendation \
  --thesis-id thesis-001 \
  --kind watchlist \
  --rationale "Edge exists, but wait for stronger source confirmation"
```

Allowed recommendation kinds are `trade`, `no-trade`, and `watchlist`.

Record the human final decision:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator decision \
  --thesis-id thesis-001 \
  --kind deferred \
  --rationale "Human operator wants another source before acting"
```

Allowed decision kinds are `approved`, `rejected`, and `deferred`.

### Position records

Record a manually executed position entry, exit, or mark-to-market update:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator position \
  --thesis-id thesis-001 \
  --event mark-to-market \
  --quantity 10 \
  --price 0.46 \
  --notes "Manual update from operator's own records"
```

Allowed position events are `entry`, `exit`, and `mark-to-market`. This command records what a human did elsewhere; it does not place or modify any real position.

### Weekly review

Generate a weekly review summary, including scale-gate status:

```bash
PYTHONPATH=src python -m prediction_market_lab.operator weekly-review \
  --week-start 2026-05-04 \
  --week-end 2026-05-10
```

Scale-gate status is one of:

- `hold` — blockers exist, such as non-actionable theses, trade recommendations without recorded human final decisions, or entries without mark-to-market updates.
- `observe-only` — no blockers, but the local sample is still too small for scale review.
- `eligible-for-human-scale-review` — the local record has enough actionable theses, decisions, and mark-to-market coverage to ask a human whether scaling is appropriate.

## Safety boundary

This lab can generate research summaries and decision-support signals. It must not:

- Automatically place bets or trades.
- Treat model output as final trading advice.
- Store secrets in source control.
- Bypass human review for market participation.

A human operator must explicitly review and approve any real-world market action outside this repository.
