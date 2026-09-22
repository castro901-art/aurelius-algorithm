# Aurelius research pipeline architecture

## Purpose

Aurelius is being built as an evidence-first research model. The current implementation is deterministic and dependency-free, which makes its behavior easy to test before network retrieval or model-backed synthesis is introduced.

## Pipeline

1. **Question normalization** converts raw input into a stable `ResearchQuestion` with normalized terms.
2. **Retrieval** is provided through the `Retriever` protocol. `InMemoryRetriever` is the local reference implementation; web, vector, and database adapters can implement the same contract.
3. **Source ranking** computes a transparent score from relevance, source credibility, and recency. The current weights are 55% relevance, 30% credibility, and 15% recency.
4. **Citation-aware synthesis** uses ranked excerpts rather than inventing unsupported claims. Every selected excerpt receives a stable inline citation label and URL mapping.
5. **Audit trace** records pipeline stages and candidate counts in `ResearchResult.trace` so callers can inspect what happened.

## Safety boundaries

- No evidence means `status="needs_sources"`, zero confidence, and an explicit open question.
- Confidence is a score for evidence support, not a probability that an answer is true.
- Low-credibility evidence is surfaced as an open question rather than silently discarded.
- The default implementation does not make network requests or claim to have searched the web.

## Extension points

- Implement `Retriever.search` for a trusted search API, local corpus, or vector index.
- Replace `SourceRanker` with a domain-specific ranker while preserving `RankedEvidence` fields.
- Add a model-backed synthesizer that must preserve citation links and return structured uncertainty.
- Add evaluation fixtures for retrieval recall, citation precision, and answer faithfulness.

## Running locally

```bash
python -m pytest
python -m src.algorithm
```
