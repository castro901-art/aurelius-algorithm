"""Tests for the deterministic Aurelius research pipeline."""

import pytest

from src.algorithm import (
    AureliusAlgorithm,
    EvidenceRecord,
    InMemoryRetriever,
    ResearchQuestion,
    SourceRanker,
)


@pytest.fixture
def evidence() -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            id="official-1",
            title="Official retrieval evaluation",
            url="https://example.com/official",
            excerpt="Retrieval evaluation measures whether research systems find relevant evidence.",
            source_type="official",
            credibility=0.95,
            published_at="2026-01-01T00:00:00Z",
        ),
        EvidenceRecord(
            id="commentary-1",
            title="Research commentary",
            url="https://example.com/commentary",
            excerpt="Research workflows benefit from transparent evidence records.",
            source_type="commentary",
            credibility=0.6,
            published_at="2024-01-01T00:00:00Z",
        ),
    ]


def test_question_normalization_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        ResearchQuestion.from_text("   ")


def test_ranker_prefers_relevant_credible_evidence(evidence: list[EvidenceRecord]) -> None:
    question = ResearchQuestion.from_text("retrieval evaluation evidence")
    ranked = SourceRanker().rank(evidence, question)
    assert ranked[0].record.id == "official-1"
    assert ranked[0].relevance > 0
    assert ranked[0].score > ranked[1].score


def test_pipeline_returns_citations_and_trace(evidence: list[EvidenceRecord]) -> None:
    result = AureliusAlgorithm(retriever=InMemoryRetriever(evidence)).research(
        "How does retrieval evaluation use evidence?"
    )
    assert result.status == "completed"
    assert len(result.citations) == 2
    assert "[1]" in result.answer
    assert result.trace == ["question_normalized", "retrieved:2", "ranked:2", "synthesized:2_citations"]
    assert result.sources[0]["id"] == "official-1"


def test_pipeline_is_explicit_when_sources_are_missing() -> None:
    result = AureliusAlgorithm().research("What is the next research priority?")
    assert result.status == "needs_sources"
    assert result.confidence == 0.0
    assert result.citations == []
    assert result.open_questions
