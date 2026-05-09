"""Local operator CLI for candidate, thesis, decision, and review workflows.

The CLI is intentionally analysis-only: it writes local JSON artifacts and never
places trades or calls exchange/betting APIs.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal, Sequence

from prediction_market_lab.config import LabConfig

RecommendationKind = Literal["trade", "no-trade", "watchlist"]
DecisionKind = Literal["approved", "rejected", "deferred"]
PositionEventKind = Literal["entry", "exit", "mark-to-market"]


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for a thesis."""

    thesis_id: str
    actionable: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        return "actionable" if self.actionable else "non-actionable"


@dataclass(frozen=True)
class CandidateMarket:
    """A manually captured candidate market."""

    candidate_id: str
    title: str
    url: str = ""
    platform: str = "manual"
    market_probability: float | None = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())


@dataclass(frozen=True)
class Thesis:
    """Research thesis attached to a candidate market."""

    thesis_id: str
    candidate_id: str
    question: str
    belief_probability: float | None = None
    market_probability: float | None = None
    evidence: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    resolution_criteria: str = ""
    time_horizon: str = ""
    expected_value_notes: str = ""
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())


class OperatorStore:
    """Tiny deterministic JSON store for local operator artifacts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "candidates": {},
                "theses": {},
                "recommendations": [],
                "decisions": [],
                "position_events": [],
            }
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def upsert_candidate(self, candidate: CandidateMarket) -> None:
        existing = self.data["candidates"].get(candidate.candidate_id, {})
        created_at = existing.get("created_at", candidate.created_at)
        self.data["candidates"][candidate.candidate_id] = {**asdict(candidate), "created_at": created_at, "updated_at": _now_iso()}
        self.save()

    def import_candidates(self, candidates: list[dict[str, Any]]) -> int:
        for raw in candidates:
            self.upsert_candidate(
                CandidateMarket(
                    candidate_id=_require_text(raw, "candidate_id"),
                    title=_require_text(raw, "title"),
                    url=str(raw.get("url", "")),
                    platform=str(raw.get("platform", "manual")),
                    market_probability=_optional_probability(raw.get("market_probability")),
                    notes=str(raw.get("notes", "")),
                )
            )
        return len(candidates)

    def upsert_thesis(self, thesis: Thesis) -> None:
        if thesis.candidate_id not in self.data["candidates"]:
            raise ValueError(f"unknown candidate_id: {thesis.candidate_id}")
        existing = self.data["theses"].get(thesis.thesis_id, {})
        created_at = existing.get("created_at", thesis.created_at)
        self.data["theses"][thesis.thesis_id] = {**asdict(thesis), "created_at": created_at, "updated_at": _now_iso()}
        self.save()

    def get_thesis(self, thesis_id: str) -> dict[str, Any]:
        try:
            return self.data["theses"][thesis_id]
        except KeyError as exc:
            raise ValueError(f"unknown thesis_id: {thesis_id}") from exc

    def record_recommendation(self, thesis_id: str, kind: RecommendationKind, rationale: str) -> dict[str, Any]:
        result = validate_thesis(self.get_thesis(thesis_id))
        if kind == "trade" and not result.actionable:
            raise ValueError(f"trade recommendation rejected: thesis is {result.status}: {', '.join(result.errors)}")
        record = {
            "id": _event_id("rec"),
            "thesis_id": thesis_id,
            "recommendation": kind,
            "rationale": rationale,
            "thesis_status": result.status,
            "validation_errors": list(result.errors),
            "created_at": _now_iso(),
        }
        self.data["recommendations"].append(record)
        self.save()
        return record

    def record_decision(self, thesis_id: str, decision: DecisionKind, rationale: str) -> dict[str, Any]:
        self.get_thesis(thesis_id)
        record = {
            "id": _event_id("decision"),
            "thesis_id": thesis_id,
            "decision": decision,
            "rationale": rationale,
            "created_at": _now_iso(),
        }
        self.data["decisions"].append(record)
        self.save()
        return record

    def record_position_event(
        self,
        thesis_id: str,
        event: PositionEventKind,
        quantity: float,
        price: float,
        notes: str,
    ) -> dict[str, Any]:
        self.get_thesis(thesis_id)
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        if not 0.0 <= price <= 1.0:
            raise ValueError("price must be between 0 and 1")
        record = {
            "id": _event_id("pos"),
            "thesis_id": thesis_id,
            "event": event,
            "quantity": quantity,
            "price": price,
            "notes": notes,
            "created_at": _now_iso(),
        }
        self.data["position_events"].append(record)
        self.save()
        return record

    def weekly_review(self, week_start: str | None = None, week_end: str | None = None) -> dict[str, Any]:
        start = week_start or date.today().isoformat()
        end = week_end or start
        validations = [validate_thesis(thesis) for thesis in self.data["theses"].values()]
        actionable = sum(1 for result in validations if result.actionable)
        non_actionable = len(validations) - actionable
        trade_recs = [r for r in self.data["recommendations"] if r["recommendation"] == "trade"]
        approved = [d for d in self.data["decisions"] if d["decision"] == "approved"]
        entries = [e for e in self.data["position_events"] if e["event"] == "entry"]
        exits = [e for e in self.data["position_events"] if e["event"] == "exit"]
        marks = [e for e in self.data["position_events"] if e["event"] == "mark-to-market"]
        return {
            "week_start": start,
            "week_end": end,
            "summary": {
                "candidate_count": len(self.data["candidates"]),
                "thesis_count": len(self.data["theses"]),
                "actionable_thesis_count": actionable,
                "non_actionable_thesis_count": non_actionable,
                "recommendation_count": len(self.data["recommendations"]),
                "trade_recommendation_count": len(trade_recs),
                "approved_decision_count": len(approved),
                "position_entry_count": len(entries),
                "position_exit_count": len(exits),
                "mark_to_market_count": len(marks),
            },
            "scale_gate_status": _scale_gate_status(
                actionable=actionable,
                non_actionable=non_actionable,
                trade_recommendations=len(trade_recs),
                approved_decisions=len(approved),
                position_entries=len(entries),
                mark_to_market=len(marks),
            ),
            "non_actionable_theses": [asdict(result) for result in validations if not result.actionable],
            "safety_boundary": "analysis-only; no trades placed and no exchange/betting APIs called",
        }


def validate_thesis(raw: dict[str, Any]) -> ValidationResult:
    """Return whether a thesis is complete enough to be actionable."""
    errors: list[str] = []
    warnings: list[str] = []
    required_text = ["thesis_id", "candidate_id", "question", "resolution_criteria", "time_horizon", "expected_value_notes"]
    for key in required_text:
        if not str(raw.get(key, "")).strip():
            errors.append(f"{key} is required")
    for key in ["belief_probability", "market_probability"]:
        value = raw.get(key)
        if value is None:
            errors.append(f"{key} is required")
        elif not isinstance(value, int | float) or not 0.0 <= float(value) <= 1.0:
            errors.append(f"{key} must be between 0 and 1")
    if not raw.get("evidence"):
        errors.append("at least one evidence item is required")
    if not raw.get("risks"):
        errors.append("at least one risk/caveat is required")
    if raw.get("belief_probability") is not None and raw.get("market_probability") is not None:
        edge = abs(float(raw["belief_probability"]) - float(raw["market_probability"]))
        if edge < 0.03:
            warnings.append("probability edge is below 3 percentage points")
    return ValidationResult(
        thesis_id=str(raw.get("thesis_id", "")),
        actionable=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local analysis-only operator workflow for Prediction Market Lab")
    parser.add_argument("--store", type=Path, default=None, help="local JSON store path; defaults to PML_DATA_DIR/operator_store.json")
    sub = parser.add_subparsers(dest="command", required=True)

    candidate = sub.add_parser("candidate", help="create or import candidate markets")
    candidate_sub = candidate.add_subparsers(dest="candidate_command", required=True)
    candidate_create = candidate_sub.add_parser("create", help="manually create/update a candidate market")
    candidate_create.add_argument("--id", required=True)
    candidate_create.add_argument("--title", required=True)
    candidate_create.add_argument("--url", default="")
    candidate_create.add_argument("--platform", default="manual")
    candidate_create.add_argument("--market-probability", type=float)
    candidate_create.add_argument("--notes", default="")
    candidate_import = candidate_sub.add_parser("import-json", help="import candidate markets from a JSON list")
    candidate_import.add_argument("path", type=Path)

    thesis = sub.add_parser("thesis", help="create/update or validate theses")
    thesis_sub = thesis.add_subparsers(dest="thesis_command", required=True)
    thesis_upsert = thesis_sub.add_parser("upsert", help="create or update a thesis")
    thesis_upsert.add_argument("--id", required=True)
    thesis_upsert.add_argument("--candidate-id", required=True)
    thesis_upsert.add_argument("--question", required=True)
    thesis_upsert.add_argument("--belief-probability", type=float)
    thesis_upsert.add_argument("--market-probability", type=float)
    thesis_upsert.add_argument("--evidence", action="append", default=[])
    thesis_upsert.add_argument("--risk", action="append", default=[])
    thesis_upsert.add_argument("--resolution-criteria", default="")
    thesis_upsert.add_argument("--time-horizon", default="")
    thesis_upsert.add_argument("--expected-value-notes", default="")
    thesis_validate = thesis_sub.add_parser("validate", help="validate a thesis and label actionability")
    thesis_validate.add_argument("--id", required=True)

    recommendation = sub.add_parser("recommendation", help="record trade/no-trade/watchlist recommendations")
    recommendation.add_argument("--thesis-id", required=True)
    recommendation.add_argument("--kind", choices=["trade", "no-trade", "watchlist"], required=True)
    recommendation.add_argument("--rationale", required=True)

    decision = sub.add_parser("decision", help="record the human final decision")
    decision.add_argument("--thesis-id", required=True)
    decision.add_argument("--kind", choices=["approved", "rejected", "deferred"], required=True)
    decision.add_argument("--rationale", required=True)

    position = sub.add_parser("position", help="record position entry/exit/mark-to-market updates")
    position.add_argument("--thesis-id", required=True)
    position.add_argument("--event", choices=["entry", "exit", "mark-to-market"], required=True)
    position.add_argument("--quantity", type=float, required=True)
    position.add_argument("--price", type=float, required=True)
    position.add_argument("--notes", default="")

    review = sub.add_parser("weekly-review", help="generate weekly review summary with scale-gate status")
    review.add_argument("--week-start")
    review.add_argument("--week-end")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store_path = args.store or LabConfig.from_env().data_dir / "operator_store.json"
    store = OperatorStore(store_path)
    try:
        output = _run(args, store)
    except ValueError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def _run(args: argparse.Namespace, store: OperatorStore) -> dict[str, Any]:
    if args.command == "candidate" and args.candidate_command == "create":
        candidate = CandidateMarket(
            candidate_id=args.id,
            title=args.title,
            url=args.url,
            platform=args.platform,
            market_probability=_optional_probability(args.market_probability),
            notes=args.notes,
        )
        store.upsert_candidate(candidate)
        return {"status": "ok", "candidate": store.data["candidates"][candidate.candidate_id]}
    if args.command == "candidate" and args.candidate_command == "import-json":
        count = store.import_candidates(json.loads(args.path.read_text(encoding="utf-8")))
        return {"status": "ok", "imported": count}
    if args.command == "thesis" and args.thesis_command == "upsert":
        thesis = Thesis(
            thesis_id=args.id,
            candidate_id=args.candidate_id,
            question=args.question,
            belief_probability=_optional_probability(args.belief_probability),
            market_probability=_optional_probability(args.market_probability),
            evidence=tuple(args.evidence),
            risks=tuple(args.risk),
            resolution_criteria=args.resolution_criteria,
            time_horizon=args.time_horizon,
            expected_value_notes=args.expected_value_notes,
        )
        store.upsert_thesis(thesis)
        result = validate_thesis(store.get_thesis(thesis.thesis_id))
        return {"status": "ok", "thesis_status": result.status, "validation": asdict(result)}
    if args.command == "thesis" and args.thesis_command == "validate":
        return asdict(validate_thesis(store.get_thesis(args.id)))
    if args.command == "recommendation":
        return {"status": "ok", "recommendation": store.record_recommendation(args.thesis_id, args.kind, args.rationale)}
    if args.command == "decision":
        return {"status": "ok", "decision": store.record_decision(args.thesis_id, args.kind, args.rationale)}
    if args.command == "position":
        return {"status": "ok", "position_event": store.record_position_event(args.thesis_id, args.event, args.quantity, args.price, args.notes)}
    if args.command == "weekly-review":
        return store.weekly_review(args.week_start, args.week_end)
    raise ValueError(f"unsupported command: {args.command}")


def _scale_gate_status(
    *,
    actionable: int,
    non_actionable: int,
    trade_recommendations: int,
    approved_decisions: int,
    position_entries: int,
    mark_to_market: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    if non_actionable:
        blockers.append("non-actionable theses remain in the review set")
    if trade_recommendations > approved_decisions:
        blockers.append("some trade recommendations do not have recorded human final decisions")
    if position_entries and mark_to_market == 0:
        blockers.append("open position entries lack mark-to-market updates")
    if blockers:
        status = "hold"
    elif actionable >= 10 and approved_decisions >= 5 and mark_to_market >= position_entries:
        status = "eligible-for-human-scale-review"
    else:
        status = "observe-only"
    return {
        "status": status,
        "blockers": blockers,
        "policy": "Scaling requires human review; this CLI only summarizes local records.",
    }


def _optional_probability(value: Any) -> float | None:
    if value is None or value == "":
        return None
    probability = float(value)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability values must be between 0 and 1")
    return probability


def _require_text(raw: dict[str, Any], key: str) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _event_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
