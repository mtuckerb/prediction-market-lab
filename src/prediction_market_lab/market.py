"""Core market-research data structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketQuestion:
    """A prediction-market question under human review."""

    title: str
    current_probability: float
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be blank")
        if not 0.0 <= self.current_probability <= 1.0:
            raise ValueError("current_probability must be between 0 and 1")

    def evidence_count(self) -> int:
        """Return the number of evidence snippets attached to the question."""
        return len(self.evidence)
