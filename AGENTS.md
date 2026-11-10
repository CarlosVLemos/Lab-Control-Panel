# Lab Control Panel — Development instructions

Read `SDD/rules.md` for task classification, ownership, approvals and validation.
Use Jarvis (coordination), Maquiavel (backend), Van Gogh (frontend) and Mefisto (independent review) only when the task needs them.

## Where to look
- `backend/app/` — FastAPI and domain
- `backend/tests/` — pytest
- `docs/PROJECT_SPEC.md` and `docs/ARCHITECTURE.md` — product decisions
- `SDD/` — development contracts and audit evidence
- `.agents/skills/` — issue implementation and PR review workflows

## Verify
- Backend: `python -m pip install -r backend/requirements-dev.txt` then `cd backend && python -m pytest -q`
- Compose config: `docker compose config -q`
- Execute only safe, authorized commands; state when a dependency/environment is unavailable.

Keep README short (objective + how to run). Prefer minimal diffs, deterministic tests, versioned evidence and a PR over direct changes to `main`. Never execute untrusted agent-generated code or expose credentials. Don't invent test results, delegation or benchmarks. These profiles help **develop** LCP; they are not the evaluated workloads.
