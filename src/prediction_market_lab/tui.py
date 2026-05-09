"""Guided terminal workflow for early Prediction Market Lab runs.

The TUI is deliberately lightweight and dependency-free. It does not automate
trading. Instead, it walks a human operator through the same analysis-only
steps the autonomous agent would take, showing the intended action before each
record is written.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable, Sequence

from prediction_market_lab.config import LabConfig
from prediction_market_lab.operator import (
    CandidateMarket,
    DecisionKind,
    OperatorStore,
    PositionEventKind,
    RecommendationKind,
    Thesis,
    validate_thesis,
)
from prediction_market_lab.research_agent import MarketIdea, propose_research_plan


@dataclass(frozen=True)
class CandidateEvaluation:
    """Structured quick-screen result for a candidate market."""

    status: str
    score: int
    strengths: tuple[str, ...]
    blockers: tuple[str, ...]
    next_steps: tuple[str, ...]


class PromptIO:
    """Small injectable input/output wrapper for deterministic tests."""

    def __init__(self, input_func: Callable[[str], str] = input, output_func: Callable[[str], None] = print) -> None:
        self._input = input_func
        self._output = output_func

    def write(self, message: str = "") -> None:
        self._output(message)

    def ask(self, prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        value = self._input(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        return default or ""

    def ask_required(self, prompt: str, default: str | None = None) -> str:
        while True:
            value = self.ask(prompt, default)
            if value.strip():
                return value.strip()
            self.write("This field is required.")

    def ask_float(self, prompt: str, default: float | None = None, *, required: bool = False) -> float | None:
        default_text = None if default is None else str(default)
        while True:
            raw = self.ask(prompt, default_text)
            if raw == "" and not required:
                return None
            try:
                value = float(raw)
            except ValueError:
                self.write("Enter a number between 0 and 1, or leave blank when optional.")
                continue
            if 0.0 <= value <= 1.0:
                return value
            self.write("Probability must be between 0 and 1.")

    def ask_choice(self, prompt: str, choices: Sequence[str], default: str | None = None) -> str:
        choices_text = "/".join(choices)
        while True:
            value = self.ask(f"{prompt} ({choices_text})", default)
            if value in choices:
                return value
            self.write(f"Choose one of: {choices_text}")

    def ask_many(self, prompt: str) -> tuple[str, ...]:
        self.write(f"{prompt}. Enter one per line; blank line finishes.")
        values: list[str] = []
        while True:
            value = self.ask("-", None)
            if not value:
                return tuple(values)
            values.append(value)

    def pause(self) -> None:
        self._input("Press Enter to continue...")


class OperatorTUI:
    """Menu-driven human-in-the-loop interface over the local operator store."""

    def __init__(self, store: OperatorStore, io: PromptIO | None = None) -> None:
        self.store = store
        self.io = io or PromptIO()

    def run(self) -> None:
        self.io.write("Prediction Market Lab TUI")
        self.io.write("Analysis-only: this interface records local research artifacts and never places trades.")
        while True:
            self.show_dashboard()
            choice = self.io.ask_choice(
                "Choose next step",
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "q"],
            )
            if choice == "1":
                self.autonomous_market_wizard()
            elif choice == "2":
                self.find_candidates_wizard()
            elif choice == "3":
                self.evaluate_candidate_wizard()
            elif choice == "4":
                self.thesis_wizard()
            elif choice == "5":
                self.create_candidate()
            elif choice == "6":
                self.create_thesis()
            elif choice == "7":
                self.validate_thesis()
            elif choice == "8":
                self.record_recommendation()
            elif choice == "9":
                self.record_decision()
            elif choice == "10":
                self.record_position_event()
            elif choice == "11":
                self.weekly_review()
            elif choice == "q":
                self.io.write("Goodbye.")
                return
            self.io.pause()

    def show_dashboard(self) -> None:
        data = self.store.data
        self.io.write("\n=== Current lab state ===")
        self.io.write(f"Candidates: {len(data['candidates'])}")
        self.io.write(f"Theses: {len(data['theses'])}")
        self.io.write(f"Recommendations: {len(data['recommendations'])}")
        self.io.write(f"Human decisions: {len(data['decisions'])}")
        self.io.write(f"Position events: {len(data['position_events'])}")
        self.io.write("\n1. Autonomous wizard: describe what you want to predict")
        self.io.write("2. Wizard: find candidate ideas")
        self.io.write("3. Wizard: evaluate a candidate")
        self.io.write("4. Wizard: build thesis + recommendation")
        self.io.write("5. Manual: create/import candidate")
        self.io.write("6. Manual: write or update thesis")
        self.io.write("7. Manual: validate thesis")
        self.io.write("8. Manual: record agent recommendation")
        self.io.write("9. Manual: record human final decision")
        self.io.write("10. Manual: record position update")
        self.io.write("11. Generate weekly review")
        self.io.write("q. Quit")

    def autonomous_market_wizard(self) -> dict[str, Any]:
        self.io.write("\n=== Autonomous market wizard ===")
        self.io.write("Tell the agent what kind of market you want to predict. Examples:")
        self.io.write("- weather in Austin next week")
        self.io.write("- Fed rate decision")
        self.io.write("- OpenAI product launch timing")
        self.io.write("- a boring policy/court/procedure market")
        interest = self.io.ask_required("What kind of market would you like to predict?")
        plan = propose_research_plan(interest)
        self.io.write(f"\nPlanning source: {plan.source}")
        self.io.write(f"Teaching note: {plan.teaching_note}")
        answers: dict[str, str] = {}
        for question in plan.clarifying_questions:
            self.io.write(f"\nWhy this matters: {question.why_it_matters}")
            answers[question.prompt] = self.io.ask(question.prompt, "")
        if answers:
            plan = propose_research_plan(interest, answers)
            self.io.write("\nUpdated plan after your answers:")
            self.io.write(f"Teaching note: {plan.teaching_note}")
        if not plan.market_ideas:
            self.io.write("No candidate ideas were produced. Try a narrower topic.")
            return {"status": "no-ideas", "plan": plan.to_dict()}
        self.io.write("\nCandidate ideas / search targets:")
        for index, idea in enumerate(plan.market_ideas, start=1):
            self._print_market_idea(index, idea)
        choice = self.io.ask_choice("Choose an idea to pursue, or skip", [*(str(i) for i in range(1, len(plan.market_ideas) + 1)), "skip"], "1")
        payload: dict[str, Any] = {"plan": plan.to_dict(), "answers": answers}
        if choice == "skip":
            self.io.write(f"Next action: {plan.next_action}")
            return payload
        idea = plan.market_ideas[int(choice) - 1]
        self.io.write("\nOpen or inspect the suggested URLs. Paste the actual market URL if you find one, or keep the search URL for now.")
        actual_url = self.io.ask("Actual market URL or search URL", idea.search_urls[0] if idea.search_urls else "")
        market_probability = self.io.ask_float("Current market-implied probability, 0-1 if visible", None)
        save = self.io.ask_choice("Save this as a candidate and continue to thesis wizard?", ["yes", "no"], "yes")
        if save == "yes":
            candidate_id = self.io.ask_required("Candidate id", self._next_id("cand", self.store.data["candidates"]))
            notes = "; ".join([
                f"type={idea.market_type}",
                f"why_promising={idea.why_promising}",
                "verify=" + " | ".join(idea.what_to_verify),
                "risks=" + " | ".join(idea.risks),
            ])
            candidate = CandidateMarket(candidate_id=candidate_id, title=idea.title, url=actual_url, platform="llm-assisted", market_probability=market_probability, notes=notes)
            self.store.upsert_candidate(candidate)
            payload["saved_candidate"] = self.store.data["candidates"][candidate_id]
            continue_to_thesis = self.io.ask_choice("Build a thesis for this candidate now?", ["yes", "no"], "yes")
            if continue_to_thesis == "yes":
                payload["thesis"] = self.thesis_wizard(candidate_id=candidate_id)
        self.io.write(f"Next action: {plan.next_action}")
        return payload

    def _print_market_idea(self, index: int, idea: MarketIdea) -> None:
        self.io.write(f"\n{index}. {idea.title}")
        self.io.write(f"   Type: {idea.market_type}")
        self.io.write(f"   Why it might be useful: {idea.why_promising}")
        self.io.write("   Verify:")
        for item in idea.what_to_verify:
            self.io.write(f"   - {item}")
        if idea.search_urls:
            self.io.write("   Suggested URLs/searches:")
            for url in idea.search_urls:
                self.io.write(f"   - {url}")
        if idea.risks:
            self.io.write("   Risks:")
            for risk in idea.risks:
                self.io.write(f"   - {risk}")

    def find_candidates_wizard(self) -> list[str]:
        self.io.write("\n=== Candidate discovery wizard ===")
        self.io.write("Autonomous mode would scan approved market sources and shortlist boring, researchable markets.")
        self.io.write("For now, use this checklist to know what to look for manually:")
        ideas = [
            "Official-data release markets: CPI, jobs reports, agency statistics, court calendars, product release windows.",
            "Deadline markets: whether a named event happens by a specific date with an unambiguous resolver.",
            "Settlement-rule confusion: markets where the crowd may misunderstand the exact YES/NO criteria.",
            "Low-attention procedural events: approvals, filings, hearings, votes, launches, or scheduled decisions.",
            "Weather/threshold markets only when a primary data source is named and the threshold is exact.",
        ]
        avoid = [
            "major elections, major sports, meme/news-cycle markets, insider-heavy markets, and vague settlement sources",
            "markets where the spread/fees are large enough to consume the expected edge",
            "anything chosen because it is exciting rather than analyzable",
        ]
        self.io.write("\nLook for:")
        for idea in ideas:
            self.io.write(f"- {idea}")
        self.io.write("\nAvoid:")
        for item in avoid:
            self.io.write(f"- {item}")
        self.io.write("\nWhen you find one candidate, choose option 2 to evaluate it or option 4 to save it directly.")
        return ideas

    def evaluate_candidate_wizard(self) -> dict[str, Any]:
        self.io.write("\n=== Candidate evaluation wizard ===")
        self.io.write("Autonomous mode would reject unclear markets before spending research time.")
        title = self.io.ask_required("Market title/question")
        platform = self.io.ask("Platform", "manual")
        url = self.io.ask("Market URL", "")
        market_probability = self.io.ask_float("Market-implied probability, 0-1", None)
        settlement_source = self.io.ask("Named primary settlement source", "")
        criteria = self.io.ask("Plain-English YES/NO criteria", "")
        resolution_date = self.io.ask("Close/resolution date", "")
        spread_ok = self.io.ask_choice("Is the spread/fee burden acceptable?", ["yes", "no", "unknown"], "unknown")
        why_wrong = self.io.ask("One-sentence reason the market may be wrong", "")
        evidence = self.io.ask_many("Primary source links or notes you already have")
        evaluation = evaluate_candidate(
            title=title,
            settlement_source=settlement_source,
            criteria=criteria,
            resolution_date=resolution_date,
            spread_ok=spread_ok,
            why_wrong=why_wrong,
            evidence=evidence,
        )
        payload = {"evaluation": asdict(evaluation)}
        self._print_json(payload)
        if evaluation.status != "reject":
            save = self.io.ask_choice("Save this candidate?", ["yes", "no"], "yes")
            if save == "yes":
                candidate_id = self.io.ask_required("Candidate id", self._next_id("cand", self.store.data["candidates"]))
                notes = "; ".join(filter(None, [f"settlement_source={settlement_source}", f"criteria={criteria}", f"resolution_date={resolution_date}", f"why_wrong={why_wrong}"]))
                candidate = CandidateMarket(candidate_id=candidate_id, title=title, url=url, platform=platform, market_probability=market_probability, notes=notes)
                self.store.upsert_candidate(candidate)
                payload["saved_candidate"] = self.store.data["candidates"][candidate_id]
                self._print_json({"status": "saved", "candidate": payload["saved_candidate"]})
        return payload

    def thesis_wizard(self, candidate_id: str | None = None) -> dict[str, Any]:
        self.io.write("\n=== Thesis builder wizard ===")
        self.io.write("Autonomous mode would turn a surviving candidate into a written thesis, validate it, and default to watchlist/no-trade unless the edge and evidence are clear.")
        candidate_id = candidate_id or self._choose_existing("candidate", self.store.data["candidates"])
        candidate = self.store.data["candidates"].get(candidate_id, {})
        thesis_id = self.io.ask_required("Thesis id", self._next_id("thesis", self.store.data["theses"]))
        question = self.io.ask_required("Market question", str(candidate.get("title", "")))
        self.io.write("Outside view = base rate / reference class. Inside view = specific facts about this case.")
        outside = self.io.ask_float("Outside-view probability, 0-1", None)
        inside = self.io.ask_float("Inside-view probability, 0-1", None)
        belief = self.io.ask_float("Final fair probability, 0-1", inside if inside is not None else outside)
        market_probability = self.io.ask_float("Market-implied probability, 0-1", candidate.get("market_probability"))
        settlement = self.io.ask_required("Exactly what resolves YES/NO?")
        horizon = self.io.ask_required("Resolution date or time horizon")
        evidence = self.io.ask_many("Primary evidence/source notes")
        risks = self.io.ask_many("Risks, ambiguities, and what would falsify this")
        edge_text = ""
        if belief is not None and market_probability is not None:
            edge_text = f"Fair probability {belief:.2f} vs market {market_probability:.2f}; edge {belief - market_probability:+.2f}."
            self.io.write(edge_text)
        expected_value_notes = self.io.ask_required("Expected-value / edge notes", edge_text)
        thesis = Thesis(
            thesis_id=thesis_id,
            candidate_id=candidate_id,
            question=question,
            belief_probability=belief,
            market_probability=market_probability,
            evidence=evidence,
            risks=risks,
            resolution_criteria=settlement,
            time_horizon=horizon,
            expected_value_notes=expected_value_notes,
        )
        self.store.upsert_thesis(thesis)
        result = validate_thesis(self.store.get_thesis(thesis_id))
        recommendation_kind, rationale = recommend_from_validation(result, belief, market_probability)
        recommendation = self.store.record_recommendation(thesis_id, recommendation_kind, rationale)
        payload = {
            "status": "saved",
            "thesis_status": result.status,
            "validation": asdict(result),
            "default_recommendation": recommendation,
        }
        self._print_json(payload)
        return payload

    def create_candidate(self) -> dict[str, Any]:
        self._explain("Autonomous mode would ingest candidate markets, filter for clear settlement, and persist promising candidates.")
        candidate_id = self.io.ask_required("Candidate id", self._next_id("cand", self.store.data["candidates"]))
        candidate = CandidateMarket(
            candidate_id=candidate_id,
            title=self.io.ask_required("Market title/question"),
            url=self.io.ask("Market URL", ""),
            platform=self.io.ask("Platform", "manual"),
            market_probability=self.io.ask_float("Market-implied probability, 0-1", None),
            notes=self.io.ask("Notes", ""),
        )
        self.store.upsert_candidate(candidate)
        record = self.store.data["candidates"][candidate_id]
        self._print_json({"status": "saved", "candidate": record})
        return record

    def create_thesis(self) -> dict[str, Any]:
        self._explain("Autonomous mode would research the candidate, write evidence/risk notes, estimate fair probability, then validate before recommending anything.")
        candidate_id = self._choose_existing("candidate", self.store.data["candidates"])
        thesis_id = self.io.ask_required("Thesis id", self._next_id("thesis", self.store.data["theses"]))
        candidate = self.store.data["candidates"].get(candidate_id, {})
        thesis = Thesis(
            thesis_id=thesis_id,
            candidate_id=candidate_id,
            question=self.io.ask_required("Question", str(candidate.get("title", ""))),
            belief_probability=self.io.ask_float("Our fair probability, 0-1", None),
            market_probability=self.io.ask_float(
                "Market-implied probability, 0-1",
                candidate.get("market_probability"),
            ),
            evidence=self.io.ask_many("Evidence / sources"),
            risks=self.io.ask_many("Risks / falsification notes"),
            resolution_criteria=self.io.ask_required("Plain-English resolution criteria"),
            time_horizon=self.io.ask_required("Resolution date or time horizon"),
            expected_value_notes=self.io.ask_required("Expected-value / edge notes"),
        )
        self.store.upsert_thesis(thesis)
        result = validate_thesis(self.store.get_thesis(thesis_id))
        payload = {"status": "saved", "thesis_status": result.status, "validation": asdict(result)}
        self._print_json(payload)
        return payload

    def validate_thesis(self) -> dict[str, Any]:
        self._explain("Autonomous mode would run the no-trade gate and refuse action when required fields or safety checks fail.")
        thesis_id = self._choose_existing("thesis", self.store.data["theses"])
        result = asdict(validate_thesis(self.store.get_thesis(thesis_id)))
        self._print_json(result)
        return result

    def record_recommendation(self) -> dict[str, Any]:
        self._explain("Autonomous mode would recommend trade/no-trade/watchlist, but it would not place a trade.")
        thesis_id = self._choose_existing("thesis", self.store.data["theses"])
        kind = self.io.ask_choice("Recommendation", ["trade", "no-trade", "watchlist"], "watchlist")
        rationale = self.io.ask_required("Rationale")
        record = self.store.record_recommendation(thesis_id, kind, rationale)  # type: ignore[arg-type]
        payload = {"status": "saved", "recommendation": record}
        self._print_json(payload)
        return payload

    def record_decision(self) -> dict[str, Any]:
        self._explain("Autonomous mode stops here for real-world action. The human records the final decision after independent review.")
        thesis_id = self._choose_existing("thesis", self.store.data["theses"])
        kind = self.io.ask_choice("Human decision", ["approved", "rejected", "deferred"], "deferred")
        rationale = self.io.ask_required("Human rationale")
        record = self.store.record_decision(thesis_id, kind, rationale)  # type: ignore[arg-type]
        payload = {"status": "saved", "decision": record}
        self._print_json(payload)
        return payload

    def record_position_event(self) -> dict[str, Any]:
        self._explain("Autonomous mode would only record position facts supplied by the human; it never calls exchange or betting APIs.")
        thesis_id = self._choose_existing("thesis", self.store.data["theses"])
        event = self.io.ask_choice("Position event", ["entry", "exit", "mark-to-market"], "mark-to-market")
        quantity = self._ask_non_negative_float("Quantity")
        price = self.io.ask_float("Price/probability, 0-1", required=True)
        notes = self.io.ask("Notes", "")
        record = self.store.record_position_event(thesis_id, event, quantity, float(price), notes)  # type: ignore[arg-type]
        payload = {"status": "saved", "position_event": record}
        self._print_json(payload)
        return payload

    def weekly_review(self) -> dict[str, Any]:
        self._explain("Autonomous mode would summarize process quality, blockers, and scale-gate status from stored records only.")
        start = self.io.ask("Week start YYYY-MM-DD", "") or None
        end = self.io.ask("Week end YYYY-MM-DD", "") or None
        review = self.store.weekly_review(start, end)
        self._print_json(review)
        return review

    def preview_agent_loop(self) -> list[str]:
        steps = [
            "1. Gather candidate markets from approved/manual sources.",
            "2. Filter for clear settlement, primary-source availability, liquidity, and boring analyzability.",
            "3. Draft a thesis with evidence, risks, probabilities, edge, and no-trade checks.",
            "4. Validate the thesis and produce structured blockers if non-actionable.",
            "5. Recommend trade, no-trade, or watchlist without executing anything.",
            "6. Wait for the human final decision before any real-world market action.",
            "7. Record manually supplied position updates and mark-to-market facts.",
            "8. Generate weekly review and scale-gate status from stored records.",
        ]
        self.io.write("\n=== Autonomous agent loop preview ===")
        for step in steps:
            self.io.write(step)
        return steps

    def _choose_existing(self, label: str, records: dict[str, Any]) -> str:
        if not records:
            raise ValueError(f"no {label} records exist yet")
        self.io.write(f"Available {label}s:")
        for key, value in records.items():
            title = value.get("title") or value.get("question") or ""
            self.io.write(f"- {key}: {title}")
        while True:
            selected = self.io.ask_required(f"{label.capitalize()} id")
            if selected in records:
                return selected
            self.io.write(f"Unknown {label} id: {selected}")

    def _ask_non_negative_float(self, prompt: str) -> float:
        while True:
            raw = self.io.ask_required(prompt)
            try:
                value = float(raw)
            except ValueError:
                self.io.write("Enter a number.")
                continue
            if value >= 0:
                return value
            self.io.write("Value must be non-negative.")

    def _next_id(self, prefix: str, records: dict[str, Any]) -> str:
        return f"{prefix}-{len(records) + 1:03d}"

    def _explain(self, message: str) -> None:
        self.io.write("\nWhat autonomous mode would do:")
        self.io.write(message)
        self.io.write("Human-in-the-loop mode: review each field below before saving.")

    def _print_json(self, payload: Any) -> None:
        self.io.write(json.dumps(payload, indent=2, sort_keys=True))


def evaluate_candidate(
    *,
    title: str,
    settlement_source: str,
    criteria: str,
    resolution_date: str,
    spread_ok: str,
    why_wrong: str,
    evidence: Sequence[str],
) -> CandidateEvaluation:
    """Score whether a candidate is worth thesis-building time."""
    strengths: list[str] = []
    blockers: list[str] = []
    next_steps: list[str] = []
    if title.strip():
        strengths.append("market question captured")
    if settlement_source.strip():
        strengths.append("primary settlement source identified")
    else:
        blockers.append("missing named primary settlement source")
        next_steps.append("Find the official resolver/source before writing a thesis.")
    if criteria.strip():
        strengths.append("YES/NO criteria described")
    else:
        blockers.append("missing plain-English YES/NO criteria")
        next_steps.append("Rewrite the settlement rule in your own words.")
    if resolution_date.strip():
        strengths.append("resolution timing captured")
    else:
        blockers.append("missing close/resolution date")
    if spread_ok == "yes":
        strengths.append("spread/fees appear acceptable")
    elif spread_ok == "no":
        blockers.append("spread/fees likely consume the edge")
    else:
        next_steps.append("Check bid/ask spread and fees before recommending a trade.")
    if why_wrong.strip():
        strengths.append("mispricing hypothesis stated")
    else:
        blockers.append("no reason the market may be wrong")
    if evidence:
        strengths.append("at least one evidence note/source captured")
    else:
        next_steps.append("Collect at least one primary evidence source.")
    score = len(strengths) - len(blockers)
    if any("settlement" in blocker for blocker in blockers) or any("YES/NO" in blocker for blocker in blockers):
        status = "reject"
    elif blockers:
        status = "research-more"
    else:
        status = "thesis-ready"
    return CandidateEvaluation(
        status=status,
        score=score,
        strengths=tuple(strengths),
        blockers=tuple(blockers),
        next_steps=tuple(next_steps),
    )


def recommend_from_validation(
    result: Any,
    belief_probability: float | None,
    market_probability: float | None,
) -> tuple[RecommendationKind, str]:
    """Create a conservative default recommendation from validation output."""
    if not result.actionable:
        return "no-trade", f"Thesis is non-actionable: {', '.join(result.errors)}"
    if belief_probability is None or market_probability is None:
        return "watchlist", "Actionable structure exists, but probability edge is not quantified."
    edge = abs(belief_probability - market_probability)
    if edge < 0.10:
        return "watchlist", f"Actionable thesis, but edge is only {edge:.1%}; policy requires at least 10 percentage points for trade consideration."
    return "watchlist", f"Actionable thesis with {edge:.1%} edge. Default remains watchlist for human review; no trade is placed automatically."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Guided human-in-the-loop TUI for Prediction Market Lab")
    parser.add_argument("--store", type=Path, default=None, help="local JSON store path; defaults to PML_DATA_DIR/operator_store.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store_path = args.store or LabConfig.from_env().data_dir / "operator_store.json"
    try:
        OperatorTUI(OperatorStore(store_path)).run()
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
