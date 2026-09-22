"""HTTP contract tests for the Aurelius FastAPI layer."""

from fastapi.testclient import TestClient

from src.algorithm import EvidenceRecord, InMemoryRetriever
from src.api import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "aurelius-api"}


def test_research_endpoint_returns_structured_result() -> None:
    retriever = InMemoryRetriever(
        [
            EvidenceRecord(
                id="source-1",
                title="Evidence-first research",
                url="https://example.com/source-1",
                excerpt="Traceable evidence improves research quality.",
                credibility=0.9,
            )
        ]
    )
    client = TestClient(create_app(retriever=retriever))

    response = client.post(
        "/research",
        json={"question": "How does evidence improve research quality?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["citations"][0]["label"] == "[1]"
    assert body["sources"][0]["id"] == "source-1"
    assert body["confidence"] > 0
    assert body["trace"][-1] == "synthesized:1_citations"


def test_research_endpoint_validates_blank_questions() -> None:
    client = TestClient(create_app())

    response = client.post("/research", json={"question": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "question must not be empty"
