# RAG-001 Remote MVP — Implementation evidence (offline only)

**Track:** CRITICAL (external credentials/cost). **Contract:** FROZEN MVP v2, [PR #46 human approval](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/46#issuecomment-6853766192), source contract branch `feat/rag-001-remote-adapter-contract`. **Implementation:** [PR #47](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/47) stacked on contract, not merged.

## Scope implemented

- `backend/app/evaluation/rag_remote.py`: same fixed six questions, two arms, same model/prompt except retrieved top-k context, one batch embedding of fictional corpus, six query embeddings, paired requests; dataset+manifest SHA verified before provider construction.
- Default CLI prints frozen pilot metadata offline. Optional OpenAI SDK is loaded **only** after `--execute`, quota/price args, environment key and integrity checks.
- Pre-send conservative budget `Decimal` and hard request-count gate, `max_retries=0`, no automatic retry after timeout. Price reference is a snapshot, not confirmation of actual invoice. Unknown usage/error => inconclusive.
- JSONL + summary JSON/Markdown, with per-call input/output usage and separate indexing/query embedding estimates. A human reviewer must grade visible answers independently; no automatic semantic winner.
- No production API, database, frontend, cloud service, migrations, new dependencies in the default install or persistently stored embeddings.

## Verification

- GitHub Actions [PR CI](https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43431198099), head initially `12cf759ea1174b2fa642933afc6a70f6bd048f0d`: backend `cd backend && python -m pytest -q` completed **success** as observed on the GitHub job step. Frontend tests and build completed success. **Whole workflow:** check final workflow result before reporting success (Compose restart/Playwright may still run).
- Included tests: `backend/tests/test_rag_remote.py` verify manifest hash, dry-run zero-network constructor, six pairs, index/query counts, 12+1 and N+1 quota saturation, token/budget blocking, secret sentinel in error output, no retries configured at SDK constructor, null telemetry and reports.
- Actual OpenAI generation, embeddings and account model availability: **NOT_RUN**. No API key accessed, no paid requests authorized. Real transport retry behavior needs independent review and transport-level mocked tests if future review identifies a gap.

## Safe commands (from backend directory)

```bash
python -m pytest -q tests/test_rag_remote.py tests/test_rag.py
python -m app.evaluation.rag_remote
```

Do **not** run `--execute` before separately approving the actual pilot's model availability, provider prices, region/tier, call budget and credentials.

## Limitations

- Six pairs are a connectivity/methodology pilot; not statistical proof of improvement.
- API SDK is optional and intentionally not installed by default. Adapter compatibility with a live account remains unverified.
- Local budget is a conservative preflight estimate, not a global billing ceiling.
- Outputs only include fictional dataset and visible answers after filtering; verify the artifacts manually before publishing to GitHub.
- Review semantics: `rag-32` allows a safe refusal or justified negative, not only a blank answer.
