# Lab Control Panel — Development instructions

Read `SDD/rules.md` for classification, ownership, approvals and validation. Use Jarvis (coordination), Maquiavel (backend), Van Gogh (frontend) and Mefisto (independent review) only when needed.

## Where to look
- `backend/app/` — FastAPI and domain
- `backend/tests/` — pytest
- `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md` — product decisions
- `SDD/` — contracts and evidence
- `.agents/skills/` — implementation/review workflows

## Verify
- Backend: install `backend/requirements-dev.txt`; run `cd backend && python -m pytest -q`
- Compose config: `docker compose config -q`
- Execute only safe, authorized commands; state when a dependency/environment is unavailable.

Keep README short. Prefer minimal diffs, deterministic tests, versioned evidence and PRs. Never execute untrusted agent code, expose credentials or invent results, delegation or benchmarks. Agent profiles develop LCP; they are not evaluated workloads.

## Operator-controlled local execution — explicit rule (2026-11-14)

Codex may inspect with shell/`git`/`gh` and edit, commit or push authorized code/docs.

Without explicit operator authorization for the exact operation/batch, Codex must not create environments; download models/browsers/packages; install dependencies; run tests, builds, Docker/Compose, migrations, GPU/LLM or paid calls. Prepare commands and mark `NOT_RUN` meanwhile. Push/PR-triggered CI also requires approval; use `[skip ci]` for eligible planning-only commits.

For LCP-OBS-001, first read its SDD spec and ADR-004. DRAFT documentation does not authorize implementation. Specify tests before each stage; the operator runs them afterward. Report exact evidence; NOT_RUN is neither FAIL nor PASS.
