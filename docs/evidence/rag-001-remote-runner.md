# RAG-001 Remote MVP — Implementation evidence (offline only)

**Track:** CRITICAL (external credentials/cost). **Contract:** FROZEN MVP v2, [PR #46 human approval](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/46#issuecomment-6853766192), source contract branch `feat/rag-001-remote-adapter-contract`. **Implementation:** [PR #47](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/47) stacked on contract, not merged.

## Scope implemented

- `backend/app/evaluation/rag_remote.py`: same fixed six questions, two arms, same model/prompt except retrieved top-k context, one batch embedding of fictional corpus, six query embeddings, paired requests; dataset+manifest SHA verified before provider construction.
- Default CLI prints frozen pilot metadata offline. Optional OpenAI SDK is loaded **only** after `--execute`, quota/price args, environment key and integrity checks.
- Pre-send conservative budget `Decimal` and hard request-count gate, `max_retries=0`, no automatic retry after timeout. Price reference is a snapshot, not confirmation of actual invoice. Unknown usage/error => inconclusive.
- JSONL + summary JSON/Markdown, with per-call input/output usage and separate indexing/query embedding estimates. A human reviewer must grade visible answers independently; no automatic semantic winner.
- No production API, database, frontend, cloud service, migrations, new dependencies in the default install or persistently stored embeddings.

## Verification

- GitHub Actions [PR CI](https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43431198099), head initially `12cf759ea1174b2fa642933afc6a70f6bd048f0d`: backend `cd backend && python -m pytest -q` completed **success** as observed on the GitHub job step. Frontend tests and build completed success. The [completed PR run](https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43433696018) and [push run](https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43433689854) for head `8c453dd202265767179325ecc3b2481d235dc6bd` both ended `completed/success`, including backend pytest, Compose restart, Playwright E2E, frontend tests and build. **Newer changes require their own CI result**, so this evidence is not transferable to later commits.
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

## Narrow follow-up: live-request envelope and retrieval evidence

- Budget guard now estimates tokens from the **same** serialized Responses API request object the SDK receives, including system instructions, JSON schema, document IDs/versions/text and framing. This removes an inconsistency between prompt size reservation and actual payload. The byte upper-bound with fixed overhead is conservative for this short fictional dataset; general-purpose token counting and other tokenizer families remain out of scope.
- Mocked SDK response/timeout/tier tests assert a single physical call, `max_retries=0`, and same request envelope. They do **not** prove compatibility with the remote provider. No live API was used.
- Each `SEMANTIC_RAG` record now reports `retrieval_recall_at_3` for answerable cases with expected sources. For missing/adversarial and all `NO_CONTEXT` cases it is `null`. This measures retrieval, not semantic answer correctness.
- The live pilot remains **blocked** without independent runtime review, verified model access, current price/region/tier and explicit financial approval. In particular the snapshot `PRICE_DATE=2026-11-13` is not an evergreen rate guarantee.

## Pricing attestation for the paid-mode gate (no network required to validate)

The CLI **requires** `--pricing-snapshot /absolute/path/to/pricing.json` on `--execute`. The file is intentionally local and **outside the repository**. It must be manually created/checked by the operator against the current official generation and embedding prices and the **account/endpoint region configuration**. The file itself is an operator attestation, **not cryptographic proof of the provider's future invoice**.

Example of the expected shape — **deliberately unusable as-is** (outdated timestamp, unconfirmed account and placeholder tariffs):

```json
{
  "schema": "rag-001-pricing-v1",
  "generation_model": "gpt-6-luna",
  "embedding_model": "text-embedding-3-small",
  "service_tier": "standard",
  "region": "global",
  "account_region_confirmed": false,
  "regional_surcharge_applies": false,
  "model_access_confirmed": false,
  "currency": "USD",
  "unit": "per_million_tokens",
  "generation_price_url": "https://developers.openai.com/api/docs/models/gpt-6-luna",
  "embedding_price_url": "https://developers.openai.com/api/docs/models/text-embedding-3-small",
  "multiplier": "1",
  "additional_fees_confirmed": "none",
  "verified_at_utc": "2000-01-01T00:00:00Z",
  "prices_usd_per_million": {
    "generation_input": "0.10",
    "generation_cache_read": "0.01",
    "generation_cache_write": "0.125",
    "generation_output": "0.50",
    "embedding_input": "0.02"
  }
}
```

Snapshot must be **absolute-path, not a symlink, outside the repo, UTC, verified within 24h, Standard/global with no regional surcharge, all rates present and not below 2026-11-13 baseline**. Unsupported or unverifiable conditions block before API-key read/SDK construction; no regional/priority mode is available in MVP. `OPENAI_BASE_URL` custom endpoints are rejected to avoid an unaccounted routing policy.

**Do not execute the pilot without separate budget approval**, even if a syntactically valid snapshot exists. Use `python -m app.evaluation.rag_remote` to verify the default offline mode safely.

### Runtime review follow-up

- Independent reviewer Mefisto flagged `failed` at SHA `c4348570...` for price/region gating and two MEDIUM test/evidence gaps ([review](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/47#issuecomment-6855024886)).
- Follow-up introduces pricing attestation gate, schema fields for per-attempt UTC timestamp, effective configuration, human rubric classifications, and fakes for HTTP failure classes and absent/incomplete usage.
- **These edits are not an independent approval**. Re-review the actual updated head and CI. Never claim remote price, model entitlement or paid results verified from offline fixtures.
