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

## Operator-controlled local execution — explicit rule (2026-11-14)

The Codex **may** run lightweight shell inspection, `git`, `gh`/GitHub CLI, inspect files and repository history, and edit/commit/push authorized code/docs. Do not mistake this for a ban on terminal access.

The Codex **must not initiate** environment creation, `python -m venv`, package/model/browser downloads, dependency installation, `pip install`, `npm ci/install`, test suites (`pytest`, `vitest`, Playwright), builds, Docker/Compose workloads, database migrations, GPU/LLM execution or paid API calls **unless the operator explicitly authorizes the exact operation or batch**. Even if a task asks for tests, prepare the tests and commands and mark `NOT_RUN` until the operator runs/authorizes them. GitHub Actions triggered by push/PR count as automated heavy tests/installations: obtain approval before triggering; use `[skip ci]` for docs-only planning commits where supported.

For LCP-OBS-001, read `SDD/spec/LCP-OBS-001/` and ADR-004 first. The contract is DRAFT; no implementation authorized by the documentation update. Tests are specified before each stage, then executed **by the operator at the end of each stage**. Report exact execution evidence; never treat NOT_RUN as FAIL or PASS.
