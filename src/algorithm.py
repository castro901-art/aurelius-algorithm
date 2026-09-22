"""Deterministic research pipeline primitives for the Aurelius AI model.

The module deliberately avoids network access and model-provider dependencies.
It provides composable contracts for retrieval, source ranking, extractive
synthesis, citation tracking, and audit traces. Production integrations can
implement the ``Retriever`` protocol and keep the algorithm testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Iterable, Protocol, Sequence


_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_-]*")


@dataclass(frozen=True)
class ResearchQuestion:
    """Normalized research request used throughout the pipeline."""

    text: str
    terms: tuple[str, ...]

    @classmethod
    def from_text(cls, text: str) -> "ResearchQuestion":
        normalized = " ".join(text.split())
        if not normalized:
            raise ValueError("question must not be empty")
        terms = tuple(dict.fromkeys(word.lower() for word in _WORD_RE.findall(normalized)))
        return cls(text=normalized, terms=terms)


@dataclass(frozen=True)
class EvidenceRecord:
    """A traceable piece of evidence returned by a retrieval system."""

    id: str
    title: str
    url: str
    excerpt: str
    source_type: str = "unknown"
    credibility: float = 0.5
    published_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("evidence id must not be empty")
        if not self.title.strip() or not self.excerpt.strip():
            raise ValueError("evidence title and excerpt must not be empty")
        if not 0.0 <= self.credibility <= 1.0:
            raise ValueError("credibility must be between 0 and 1")


@dataclass(frozen=True)
class RankedEvidence:
    """Evidence with the scoring breakdown needed for auditability."""

    record: EvidenceRecord
    relevance: float
    recency: float
    score: float


@dataclass(frozen=True)
class Citation:
    """Citation label mapped to a source URL."""

    label: str
    evidence_id: str
    title: str
    url: str


@dataclass(frozen=True)
class ResearchResult:
    """Structured, citation-aware output from an Aurelius research run."""

    question: str
    status: str
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    open_questions: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


class Retriever(Protocol):
    """Contract for a retrieval backend such as web, vector, or database search."""

    def search(self, question: ResearchQuestion) -> Sequence[EvidenceRecord]:
        """Return candidate evidence for a normalized question."""


class InMemoryRetriever:
    """Small dependency-free retriever for tests, demos, and local development."""

    def __init__(self, records: Iterable[EvidenceRecord] = ()) -> None:
        self.records = list(records)

    def search(self, question: ResearchQuestion) -> Sequence[EvidenceRecord]:
        query_terms = set(question.terms)
        if not query_terms:
            return []
        matches = []
        for record in self.records:
            haystack = " ".join((record.title, record.excerpt)).lower()
            if query_terms.intersection(_WORD_RE.findall(haystack)):
                matches.append(record)
        return matches


class SourceRanker:
    """Rank evidence using transparent relevance, credibility, and recency signals."""

    def rank(
        self, records: Iterable[EvidenceRecord], question: ResearchQuestion
    ) -> list[RankedEvidence]:
        ranked = [self._score(record, question) for record in records]
        return sorted(ranked, key=lambda item: (-item.score, item.record.id))

    def _score(self, record: EvidenceRecord, question: ResearchQuestion) -> RankedEvidence:
        query_terms = set(question.terms)
        haystack = set(_WORD_RE.findall(f"{record.title} {record.excerpt}".lower()))
        relevance = len(query_terms.intersection(haystack)) / max(len(query_terms), 1)
        recency = self._recency_score(record.published_at)
        score = (0.55 * relevance) + (0.30 * record.credibility) + (0.15 * recency)
        return RankedEvidence(record=record, relevance=relevance, recency=recency, score=score)

    @staticmethod
    def _recency_score(published_at: str | None) -> float:
        if not published_at:
            return 0.5
        try:
            value = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            age_days = max((datetime.now(timezone.utc) - value).days, 0)
        except ValueError:
            return 0.5
        return max(0.0, 1.0 - min(age_days / 3650.0, 1.0))


class CitationAwareSynthesizer:
    """Create a conservative extractive answer with inline citation labels."""

    def synthesize(
        self, question: ResearchQuestion, ranked: Sequence[RankedEvidence], limit: int = 5
    ) -> tuple[str, list[Citation], float, list[str]]:
        selected = list(ranked[:limit])
        if not selected:
            return (
                "No supporting evidence was retrieved. Aurelius will not infer an answer without sources.",
                [],
                0.0,
                ["Retrieve at least one relevant source before drawing a conclusion."],
            )

        citations = [
            Citation(
                label=f"[{index}]",
                evidence_id=item.record.id,
                title=item.record.title,
                url=item.record.url,
            )
            for index, item in enumerate(selected, start=1)
        ]
        lines = [f"Research question: {question.text}", "", "Evidence summary:"]
        for citation, item in zip(citations, selected):
            lines.append(f"- {item.record.excerpt.strip()} {citation.label}")
        confidence = sum(item.score for item in selected) / len(selected)
        open_questions = []
        if len(selected) == 1:
            open_questions.append("Triangulate this finding with an independent source.")
        if any(item.record.credibility < 0.5 for item in selected):
            open_questions.append("Review lower-credibility sources before making a decision.")
        return "\n".join(lines), citations, round(min(confidence, 1.0), 4), open_questions


class AureliusAlgorithm:
    """Orchestrate retrieval, ranking, synthesis, citations, and an audit trace."""

    def __init__(
        self,
        *,
        retriever: Retriever | None = None,
        ranker: SourceRanker | None = None,
        synthesizer: CitationAwareSynthesizer | None = None,
        name: str = "Aurelius",
        max_sources: int = 5,
    ) -> None:
        if max_sources < 1:
            raise ValueError("max_sources must be at least 1")
        self.name = name
        self.max_sources = max_sources
        self.retriever = retriever or InMemoryRetriever()
        self.ranker = ranker or SourceRanker()
        self.synthesizer = synthesizer or CitationAwareSynthesizer()

    def research(self, question: str) -> ResearchResult:
        """Run a deterministic research request through the configured pipeline."""

        request = ResearchQuestion.from_text(question)
        trace = ["question_normalized"]
        candidates = list(self.retriever.search(request))
        trace.append(f"retrieved:{len(candidates)}")
        ranked = self.ranker.rank(candidates, request)
        trace.append(f"ranked:{len(ranked)}")
        answer, citations, confidence, open_questions = self.synthesizer.synthesize(
            request, ranked, self.max_sources
        )
        trace.append(f"synthesized:{len(citations)}_citations")
        status = "completed" if citations else "needs_sources"
        sources = [
            {
                "id": item.record.id,
                "title": item.record.title,
                "url": item.record.url,
                "score": round(item.score, 4),
                "relevance": round(item.relevance, 4),
                "credibility": item.record.credibility,
            }
            for item in ranked[: self.max_sources]
        ]
        return ResearchResult(
            question=request.text,
            status=status,
            answer=answer,
            sources=sources,
            citations=citations,
            confidence=confidence,
            open_questions=open_questions,
            trace=trace,
        )


if __name__ == "__main__":
    demo_record = EvidenceRecord(
        id="demo-1",
        title="Evidence-first research",
        url="https://example.com/evidence-first",
        excerpt="Evidence-first systems improve research quality by making sources traceable.",
        source_type="demo",
        credibility=0.8,
    )
    result = AureliusAlgorithm(retriever=InMemoryRetriever([demo_record])).research(
        "How can evidence improve research quality?"
    )
    print(result.answer)
