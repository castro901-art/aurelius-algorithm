# Aurelius Algorithm

Aurelius Algorithm is the core research and reasoning layer for Aurelius, an AI model designed to investigate questions, organize evidence, and produce clear, traceable research outputs.

The repository now contains a deterministic, dependency-free research pipeline foundation. It is deliberately explicit about what it knows, what sources support it, and when evidence is missing. Network retrieval and model-backed synthesis remain replaceable integrations rather than hidden behavior.

## Project goals

- Build transparent and reproducible research workflows.
- Separate question normalization, evidence retrieval, source ranking, synthesis, and answer generation.
- Make source attribution, confidence, and uncertainty visible in model outputs.
- Provide a testable foundation for future retrieval, ranking, and reasoning components.

## Repository structure

```text
.
├── src/
│   ├── __init__.py
│   └── algorithm.py       # Research pipeline and public interfaces
├── docs/
│   ├── architecture.md    # Pipeline design and extension points
│   └── .gitkeep
├── tests/
│   ├── test_algorithm.py  # Deterministic behavior and safety tests
│   └── .gitkeep
├── .gitignore
├── LICENSE
└── README.md
```

## Getting started

Python 3.10 or newer is recommended. The core implementation uses only the standard library. Install `pytest` to run the test suite.

```bash
git clone https://github.com/castro901-art/aurelius-algorithm.git
cd aurelius-algorithm
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install pytest
python -m pytest
```

## Research pipeline

The public `AureliusAlgorithm` coordinates five stages:

1. Normalize the research question.
2. Retrieve candidate `EvidenceRecord` objects through a pluggable `Retriever`.
3. Rank evidence with transparent relevance, credibility, and recency signals.
4. Produce an extractive, citation-aware synthesis.
5. Return sources, confidence, open questions, and an audit trace.

```python
from src.algorithm import AureliusAlgorithm, EvidenceRecord, InMemoryRetriever

records = [
    EvidenceRecord(
        id="paper-1",
        title="Evidence-first research",
        url="https://example.com/paper-1",
        excerpt="Traceable evidence makes research outputs easier to audit.",
        source_type="paper",
        credibility=0.9,
    )
]
model = AureliusAlgorithm(retriever=InMemoryRetriever(records))
result = model.research("How does evidence improve research outputs?")
print(result.answer)
print(result.citations)
```

When no relevant evidence is available, the algorithm returns `status="needs_sources"` with zero confidence instead of fabricating an answer.

## Development principles

1. **Evidence before confidence:** conclusions should be grounded in traceable sources.
2. **Explicit uncertainty:** incomplete or conflicting evidence should be represented, not hidden.
3. **Modular design:** retrieval, ranking, synthesis, and presentation should remain independently testable.
4. **Reproducibility:** important outputs should be explainable from inputs, configuration, and source records.
5. **Responsible research:** the system should distinguish facts, interpretations, and open questions.

## Roadmap

- Add trusted retrieval adapters and source deduplication.
- Add citation-aware model-backed synthesis with faithfulness checks.
- Add evaluation datasets for retrieval recall, citation precision, and answer quality.
- Add conflict detection for contradictory evidence.
- Document threat models, limitations, and responsible-use guidance.

## Contributing

Contributions are welcome as the project develops. Please open an issue before substantial changes so that the proposed direction can be discussed. New functionality should include tests and documentation where appropriate.

## License

Aurelius Algorithm is released under the MIT License. See [LICENSE](LICENSE) for the complete text.
