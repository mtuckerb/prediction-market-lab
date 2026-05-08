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

## Operating spec

The implementation plan, operating workflow, and normative data model live in [`docs/operating-spec.md`](docs/operating-spec.md). It defines the $50 bankroll, $2–$3 normal stake, $5 hard stake max, $15 open-exposure review threshold, core entities, state transitions, validation rules, no-trade triggers, safety boundaries, metrics, and scale gates.

## Repository layout

```text
prediction-market-lab/
├── .env.example              # Non-secret local configuration template
├── .github/workflows/ci.yml  # First verification workflow
├── Makefile                  # Local check/test commands
├── README.md                 # Project purpose and operating boundaries
├── docs/operating-spec.md    # Operating spec and data model
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

## Safety boundary

This lab can generate research summaries and decision-support signals. It must not:

- Automatically place bets or trades.
- Treat model output as final trading advice.
- Store secrets in source control.
- Bypass human review for market participation.

A human operator must explicitly review and approve any real-world market action outside this repository.
