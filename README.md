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

With Nix flakes:

```bash
nix develop
make check
python -m prediction_market_lab.tui
```

With classic Nix:

```bash
nix-shell
make check
python -m prediction_market_lab.tui
```

Without Nix, no install step is required for the initial scaffold. From the repository root, run:

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

By default, generated lab data is written outside the repository at:

```text
~/.local/share/prediction-market-lab/operator_store.json
```

This gives the TUI/CLI a permanent writable home and avoids permission problems with a repo-local `data/` directory. Override it with `PML_DATA_DIR` or pass `--store path/to/operator_store.json`.

## Guided TUI

For early proof-of-process work, use the guided terminal UI to step through what an autonomous agent would do while keeping a human in control:

```bash
PYTHONPATH=src python -m prediction_market_lab.tui
```

The TUI shows the current lab state, explains the autonomous action it is simulating, then prompts for the human-reviewed fields before saving anything. It can:

1. ask what kind of market you want to predict, use an LLM when configured, and propose candidate market searches/URLs,
2. ask clarifying questions and teach why each question matters,
3. save an approved candidate and automatically continue into thesis-building,
4. evaluate whether a candidate is worth thesis-building time,
5. build a thesis with guided prompts and a conservative default recommendation,
6. create a candidate manually,
7. write or update a thesis manually,
8. validate the thesis/no-trade gate,
9. record the agent recommendation,
10. record the human final decision,
11. record manual position updates, and
12. generate the weekly review.

The autonomous wizard uses `OPENAI_API_KEY` or `PML_OPENAI_API_KEY` when available. Without an API key, it falls back to deterministic offline guidance with search URLs. LLM-suggested URLs are treated as discovery/search targets until you verify the real market page and settlement rules. The wizard path is intended for early days when the human does not yet know how to find/evaluate candidates or write a thesis. It defaults to `watchlist` or `no-trade`; it does not auto-approve trades. This is intentionally human-in-the-loop. It never places trades and never calls exchange or betting APIs.

## Operator CLI

The local operator CLI stores deterministic JSON records under `~/.local/share/prediction-market-lab/operator_store.json` by default. It is for research bookkeeping only: it never places trades and never calls exchange or betting APIs.

Run guided mode with `PYTHONPATH=src python -m prediction_market_lab.tui` or run command-by-command with `PYTHONPATH=src python -m prediction_market_lab.operator ...`. Add `--store path/to/file.json` before the subcommand to use a different local store.

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
