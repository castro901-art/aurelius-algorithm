"""Core algorithm interface for the Aurelius AI research model.

The implementation in this file is intentionally small. It defines the contract
that future retrieval, ranking, synthesis, and citation components can extend.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResearchResult:
    """Structured output returned by an Aurelius research run."""

    question: str
    status: str
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)


class AureliusAlgorithm:
    """Entry point for the Aurelius research algorithm.

    This placeholder validates a research question and returns a structured
    result. Future versions can add retrieval, evidence scoring, synthesis, and
    citation support behind this stable interface.
    """

    def __init__(self, *, name: str = "Aurelius") -> None:
        self.name = name

    def research(self, question: str) -> ResearchResult:
        """Run a research request through the initial algorithm boundary."""

        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be empty")

        return ResearchResult(
            question=normalized_question,
            status="placeholder",
            answer=(
                "The Aurelius research pipeline is not connected yet. "
                "This result marks the validated entry point for future work."
            ),
            open_questions=[
                "Which retrieval sources should be used?",
                "How should evidence quality be scored?",
            ],
        )


if __name__ == "__main__":
    example = AureliusAlgorithm().research("What should Aurelius investigate first?")
    print(example)
