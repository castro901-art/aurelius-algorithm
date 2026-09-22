"""Public package exports for the Aurelius research algorithm."""

from .algorithm import (
    AureliusAlgorithm,
    Citation,
    CitationAwareSynthesizer,
    EvidenceRecord,
    InMemoryRetriever,
    RankedEvidence,
    ResearchQuestion,
    ResearchResult,
    SourceRanker,
)

__all__ = [
    "AureliusAlgorithm",
    "Citation",
    "CitationAwareSynthesizer",
    "EvidenceRecord",
    "InMemoryRetriever",
    "RankedEvidence",
    "ResearchQuestion",
    "ResearchResult",
    "SourceRanker",
]
