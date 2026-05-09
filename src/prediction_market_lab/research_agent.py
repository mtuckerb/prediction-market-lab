"""LLM-assisted market research planning for Prediction Market Lab.

This module does not place trades and does not scrape market platforms. It turns a
free-form user interest into a structured research plan, candidate discovery
queries, clarifying questions, and conservative next actions. When an OpenAI
compatible API key is configured it can ask an LLM for the plan; otherwise it
falls back to deterministic local heuristics so the wizard remains usable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from typing import Any, Sequence
from urllib import parse, request


@dataclass(frozen=True)
class ResearchQuestion:
    """A question the agent should ask before committing research effort."""

    prompt: str
    why_it_matters: str


@dataclass(frozen=True)
class MarketIdea:
    """A candidate market idea or search target proposed by the agent."""

    title: str
    market_type: str
    why_promising: str
    what_to_verify: tuple[str, ...]
    search_urls: tuple[str, ...]
    risks: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchPlan:
    """Structured plan returned to the TUI wizard."""

    user_interest: str
    teaching_note: str
    clarifying_questions: tuple[ResearchQuestion, ...]
    market_ideas: tuple[MarketIdea, ...]
    no_trade_warnings: tuple[str, ...]
    next_action: str
    source: str = "offline"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LLMPlanClient:
    """Tiny OpenAI-compatible JSON client with no third-party dependencies."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("PML_OPENAI_API_KEY")
        self.model = model or os.getenv("PML_OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("PML_OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    def available(self) -> bool:
        return bool(self.api_key)

    def create_plan(self, user_interest: str, answers: dict[str, str] | None = None) -> ResearchPlan:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY or PML_OPENAI_API_KEY is not configured")
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an analysis-only prediction-market research assistant. "
                        "Return only JSON matching this schema: {teaching_note: string, "
                        "clarifying_questions: [{prompt, why_it_matters}], market_ideas: "
                        "[{title, market_type, why_promising, what_to_verify: [string], "
                        "search_urls: [string], risks: [string]}], no_trade_warnings: [string], "
                        "next_action: string}. Do not claim URLs are live verified unless the user "
                        "provided them. Prefer search URLs and official-source URLs when unsure. "
                        "Never recommend automatic trading."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"interest": user_interest, "answers": answers or {}}, sort_keys=True),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=30) as response:  # nosec: user-configured LLM endpoint
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return plan_from_mapping(user_interest, parsed, source="llm")


def propose_research_plan(user_interest: str, answers: dict[str, str] | None = None, client: LLMPlanClient | None = None) -> ResearchPlan:
    """Return an LLM plan when configured, otherwise deterministic guidance."""
    llm = client or LLMPlanClient()
    if llm.available():
        try:
            return llm.create_plan(user_interest, answers)
        except Exception as exc:  # pragma: no cover - network/provider failures are environment-specific
            fallback = offline_research_plan(user_interest, answers)
            return ResearchPlan(
                user_interest=fallback.user_interest,
                teaching_note=f"LLM planning failed ({exc}); using offline fallback. {fallback.teaching_note}",
                clarifying_questions=fallback.clarifying_questions,
                market_ideas=fallback.market_ideas,
                no_trade_warnings=fallback.no_trade_warnings,
                next_action=fallback.next_action,
                source="offline-after-llm-error",
            )
    return offline_research_plan(user_interest, answers)


def offline_research_plan(user_interest: str, answers: dict[str, str] | None = None) -> ResearchPlan:
    """Deterministic fallback that teaches the candidate-search process."""
    interest = user_interest.strip() or "general current events"
    normalized = interest.lower()
    query = parse.quote_plus(interest)
    questions = [
        ResearchQuestion("What platform(s) are you willing and legally able to use?", "The agent should only inspect markets you can actually use."),
        ResearchQuestion("Do you prefer near-term markets, slow research markets, or either?", "Time horizon affects whether we favor deadline/event markets or weekly review items."),
        ResearchQuestion("What sources would you trust as primary settlement evidence?", "No primary source means no trade."),
    ]
    warnings = (
        "Do not trade unless settlement criteria are clear in plain English.",
        "Do not trade if spread/fees consume the estimated edge.",
        "The agent can shortlist and draft theses, but a human must approve any real-world action.",
    )
    ideas: list[MarketIdea] = []
    if any(word in normalized for word in ["weather", "temperature", "rain", "snow", "hurricane"]):
        ideas.append(_idea("Weather threshold market", "weather/event threshold", interest, "NOAA or named official weather station"))
    if any(word in normalized for word in ["fed", "inflation", "cpi", "jobs", "economy", "rate"]):
        ideas.append(_idea("Official economic-data release market", "official data release", interest, "BLS, BEA, FRED, or Federal Reserve release calendar"))
    if any(word in normalized for word in ["product", "launch", "apple", "tesla", "openai", "release"]):
        ideas.append(_idea("Product or policy release-window market", "deadline/release window", interest, "official company, agency, or product announcement channel"))
    if any(word in normalized for word in ["court", "law", "bill", "vote", "policy", "election"]):
        ideas.append(_idea("Procedural legal/policy deadline market", "low-attention procedural", interest, "court docket, legislature calendar, agency notice, or official election office"))
    if not ideas:
        ideas.extend([
            _idea("Deadline market based on your topic", "deadline", interest, "official source named in the market rules"),
            _idea("Settlement-rule confusion market", "settlement-rule confusion", interest, "market rule text plus resolver source"),
            _idea("Official-source event market", "official data/procedure", interest, "primary publication source"),
        ])
    return ResearchPlan(
        user_interest=interest,
        teaching_note=(
            "Start by turning your interest into boring, checkable markets: a clear event, a clear deadline, "
            "and a named settlement source. The edge should come from source work, not vibes."
        ),
        clarifying_questions=tuple(questions),
        market_ideas=tuple(ideas[:4]),
        no_trade_warnings=warnings,
        next_action="Open the search URLs, choose one real market with clear rules, then let the wizard evaluate and draft a thesis.",
        source="offline",
    )


def plan_from_mapping(user_interest: str, raw: dict[str, Any], *, source: str) -> ResearchPlan:
    """Convert untrusted LLM JSON into typed, bounded plan data."""
    questions = tuple(
        ResearchQuestion(prompt=str(item.get("prompt", "")), why_it_matters=str(item.get("why_it_matters", "")))
        for item in raw.get("clarifying_questions", [])[:6]
        if str(item.get("prompt", "")).strip()
    )
    ideas = tuple(
        MarketIdea(
            title=str(item.get("title", "Untitled market idea")),
            market_type=str(item.get("market_type", "unknown")),
            why_promising=str(item.get("why_promising", "")),
            what_to_verify=tuple(str(value) for value in item.get("what_to_verify", [])[:8]),
            search_urls=tuple(str(value) for value in item.get("search_urls", [])[:8]),
            risks=tuple(str(value) for value in item.get("risks", [])[:8]),
        )
        for item in raw.get("market_ideas", [])[:6]
    )
    return ResearchPlan(
        user_interest=user_interest,
        teaching_note=str(raw.get("teaching_note", "Use clear settlement rules and primary sources before any recommendation.")),
        clarifying_questions=questions,
        market_ideas=ideas,
        no_trade_warnings=tuple(str(value) for value in raw.get("no_trade_warnings", [])[:8]),
        next_action=str(raw.get("next_action", "Choose one candidate and evaluate it.")),
        source=source,
    )


def _idea(title: str, market_type: str, interest: str, primary_source_hint: str) -> MarketIdea:
    query = parse.quote_plus(interest)
    return MarketIdea(
        title=f"{title}: {interest}",
        market_type=market_type,
        why_promising="This can be evaluated if the market has an exact deadline, objective criteria, and a primary settlement source.",
        what_to_verify=(
            "Exact market question and YES/NO rules",
            f"Primary source: {primary_source_hint}",
            "Current bid/ask spread and fees",
            "Why the crowd price may be wrong",
        ),
        search_urls=(
            f"https://kalshi.com/markets?search={query}",
            f"https://polymarket.com/search?query={query}",
            f"https://www.google.com/search?q={query}+prediction+market",
        ),
        risks=("Search URLs are discovery starting points, not verified tradable market URLs.",),
    )
