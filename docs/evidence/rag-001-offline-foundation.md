# RAG-001 offline foundation

Track: STANDARD. This foundation is offline-only: no HTTP endpoint, persistence, paid embedding, generation call, Docker, or vector database.

## Frozen inputs

- Corpus: six fictional marketplace policies in `app.evaluation.rag.POLICIES`.
- Cases: 36 (`30` grounded and `6` adversarial/answerless) in `CASES`.
- Fingerprint: generated from ordered corpus/cases by SHA-256; reproduce with `PYTHONPATH=. python -m app.evaluation.rag_cli --dry-run`.
- Conditions: cosine search in memory, configurable positive top-k, test-only fake embeddings.

## Acceptance

Deterministic evaluation checks exact structured answer, expected source inclusion, and correct abstention. Telemetry fields are optional and default to `None`; they are not zero-filled or claimed as measurements.

## Commands and limitations

```sh
cd backend
PYTHONPATH=. python -m app.evaluation.rag_cli --dry-run --top-k 2
PYTHONPATH=. python -m pytest -q tests/test_rag.py
```

The dry-run and standard-library smoke were executed. `pytest` was unavailable in this notebook, so the pytest command remains pending CI. Real embeddings/generation require separately authorized credentials and budget; no result from this foundation compares model quality.
