"""FastAPI adapter for the Aurelius research pipeline.

The HTTP layer depends on the algorithm's Retriever protocol rather than on a
specific data source. Use ``create_app(retriever=...)`` to inject a live search
adapter when one is available.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .algorithm import AureliusAlgorithm, InMemoryRetriever, Retriever, ResearchResult


class ResearchRequest(BaseModel):
    """Request body accepted by POST /research."""

    question: str = Field(
        ...,
        min_length=1,
        description="The research question Aurelius should investigate.",
        examples=["How does retrieval improve research quality?"],
    )


class SourceResponse(BaseModel):
    """Ranked source metadata returned to API clients."""

    id: str
    title: str
    url: str
    score: float
    relevance: float
    credibility: float


class CitationResponse(BaseModel):
    """Citation mapping for an evidence excerpt used in the answer."""

    label: str
    evidence_id: str
    title: str
    url: str


class ResearchResponse(BaseModel):
    """Structured research output exposed by POST /research."""

    question: str
    status: str
    answer: str
    sources: list[SourceResponse]
    citations: list[CitationResponse]
    confidence: float = Field(ge=0.0, le=1.0)
    open_questions: list[str]
    trace: list[str]


class HealthResponse(BaseModel):
    """Response returned by GET /health."""

    status: str
    service: str


def get_retriever() -> Retriever:
    """Provide the default retriever.

    Replace this provider, or inject a retriever through ``create_app``, when a
    live search, vector index, or database-backed source is ready.
    """

    return InMemoryRetriever()


def get_algorithm(
    retriever: Annotated[Retriever, Depends(get_retriever)],
) -> AureliusAlgorithm:
    """Build an algorithm instance from the configured retriever."""

    return AureliusAlgorithm(retriever=retriever)


def _to_response(result: ResearchResult) -> ResearchResponse:
    """Convert the domain result into a validated API response."""

    return ResearchResponse(
        question=result.question,
        status=result.status,
        answer=result.answer,
        sources=[SourceResponse(**source) for source in result.sources],
        citations=[
            CitationResponse(
                label=citation.label,
                evidence_id=citation.evidence_id,
                title=citation.title,
                url=citation.url,
            )
            for citation in result.citations
        ],
        confidence=result.confidence,
        open_questions=result.open_questions,
        trace=result.trace,
    )


def create_app(retriever: Retriever | None = None) -> FastAPI:
    """Create the API application with an optional retriever override.

    Keeping application construction in a factory makes it straightforward to
    use an in-memory retriever in local development and inject a live adapter in
    production or tests without changing endpoint code.
    """

    api = FastAPI(
        title="Aurelius Research API",
        description="HTTP access to the citation-aware Aurelius research pipeline.",
        version="0.1.0",
    )
    if retriever is not None:
        api.dependency_overrides[get_retriever] = lambda: retriever

    @api.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        """Return a lightweight service health response."""

        return HealthResponse(status="ok", service="aurelius-api")

    @api.post(
        "/research",
        response_model=ResearchResponse,
        status_code=200,
        tags=["research"],
    )
    def research(
        payload: ResearchRequest,
        algorithm: Annotated[AureliusAlgorithm, Depends(get_algorithm)],
    ) -> ResearchResponse:
        """Run a question through retrieval, ranking, and synthesis."""

        question = payload.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="question must not be empty")
        try:
            return _to_response(algorithm.research(question))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return api


app = create_app()


__all__ = [
    "CitationResponse",
    "HealthResponse",
    "ResearchRequest",
    "ResearchResponse",
    "SourceResponse",
    "app",
    "create_app",
    "get_algorithm",
    "get_retriever",
]
