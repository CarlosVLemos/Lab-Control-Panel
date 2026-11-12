# CODE-001 real evaluation view

## Scope

STANDARD frontend change on `feat/code-001-real-evaluation-view`. The change adds an offline Vue 3/TypeScript presentation of the versioned CODE-001 v1a importer output. It does not add an API, endpoint, migration, dependency, code execution, or change to the existing Response data contract.

## Evidence source

`frontend/src/data/code-001-import.json` is the observed JSON output of `app.evaluation.code_artifacts` for the CODE-001 bundles. It records `COMPARABLE`, two candidates, their JUnit summaries, diff counts, provenance and SHA-256 source hashes. The source records `usage: null` and `UNKNOWN-NOT-RECORDED` for agent/model identity; the UI presents these as unknown rather than as zero or a measured value.

`COMPARABLE` is displayed as structural comparability only. The view separately displays “SEM VENCEDOR” for the experimental conclusion, as importer acceptance and textual diff counts do not establish strategy superiority.

## Checks

Executed in `frontend/` with Node dependencies already present:

```sh
npm test
npm run build
```

Observed result: Vitest 2.1.9, 3 files / 9 tests passed; production Vue type-check and Vite build passed. The adapter test covers valid, missing, invalid and INCONCLUSIVE imports. Existing Response-domain and source tests also passed.

## Limitations

The fixture is a presentation fixture, not a new data-ingestion path. It cannot verify JUnit or diffs itself and does not expose an execution control. There are no observed agent token, cost, model, or duration metrics, so those fields remain unknown. Human review and merge remain required.
