# RAG-001 offline foundation

Track: STANDARD. This foundation is offline-only: no HTTP endpoint, persistence, paid embedding, generation call, Docker, or vector database.

## Frozen inputs

- Corpus: 12 fictional marketplace policies in `app.evaluation.rag.POLICIES`, including versioned delivery rules and an embedded untrusted payment instruction used only for adversarial coverage.
- Cases: 36: 20 factual (incluindo negativas fundamentadas), 6 multi-document synthesis, 4 missing-information abstentions, and 6 adversarial abstentions. Every synthesis case names at least two sources and two canonical facts. The delivery-version synthesis compares both versions and records the current six-day credit explicitly.
- Fingerprint: generated from ordered corpus/cases by SHA-256; reproduce with `PYTHONPATH=. python -m app.evaluation.rag_cli --dry-run`. Frozen fingerprint: `af2f2af7a4ceddba16f7caff52b3b85ef30862fc12aaa716c3e0255b84d827f5`.
- Conditions: cosine search in memory, configurable positive top-k, test-only fake embeddings.

## Acceptance

Deterministic evaluation checks structured `facts_match`, expected-source coverage (`expected_sources_present`), exact citation scope (`citations_match_expected`), and correct abstention. Source coverage does not validate extra citations; any citation outside the frozen expected set makes `citations_match_expected` false. It does not establish the semantic correctness of free-form generated text: that field is explicitly `NOT_EVALUATED` pending a separate semantic protocol. Telemetry fields are optional and default to `None`; they are not zero-filled or claimed as measurements.

## Commands and limitations

```sh
cd backend
PYTHONPATH=. python -m app.evaluation.rag_cli --dry-run --top-k 2
PYTHONPATH=. python -m pytest -q tests/test_rag.py
```

The dry-run and standard-library smoke were executed. `pytest` was unavailable in this notebook, so the pytest command remains pending CI. Real embeddings/generation require separately authorized credentials and budget; no result from this foundation compares model quality.
