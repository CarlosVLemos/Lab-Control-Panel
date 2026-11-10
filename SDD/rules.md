# SDD — Agent Governance

This is the **single normative source** for developing Lab Control Panel with AI agents. Every new Spec lives under `SDD/spec/<id>/`. The GitHub issue or PR links to that Spec; neither replaces its contract.

## Ownership

| Agent | Responsibilities | Boundaries |
| --- | --- | --- |
| **Jarvis** | Plan and own Spec lifecycle, dependency map, handoffs and closure | No self-approval of implementation |
| **Maquiavel** | Python domain, backend, workers, database and CI/backend infrastructure | Must not silently change frontend contracts |
| **Van Gogh** | Vue/TypeScript, UX, traces and experiment visualization | Must not silently change API/domain contracts |
| **Mefisto** | Independent QA, security, audit, test evidence and technical verdict | Does not implement the same task it approves or close Specs |

A temporary specialty must be assigned to one of these four owners; do not create a fifth permanent development persona. The names are project roles, not proof that a tool actually spawned an independent process.

## Phase 1 — Planning (mandatory)

Jarvis creates `spec.md` and `tasks.md` from the templates. Maquiavel and Van Gogh propose a joint `contract.md` where applicable, including data schemas, routes, errors, frontend states, permissions, deployment and data migration implications. Mefisto defines independent tests in `tests.md`.

- Choose `SINGLE_WRITER` or `PARALLEL_SAFE` and name one primary owner per task.
- Record `Allowed paths`, explicit exclusions, dependencies and acceptance criteria.
- **Human gate:** user reviews the plan and contract; only explicit approval marks the contract `FROZEN`. No code execution phase begins before that.
- Don't activate a new Spec if an existing one is `in_progress` without user-approved carry-over.

## Phase 2 — Execution

Only approved executors modify files inside their assigned `Allowed paths`. A `PARALLEL_SAFE` Spec may use at most two writers, on non-overlapping files with a frozen shared contract. Otherwise use `SINGLE_WRITER`.

- Work on feature branches; avoid commits straight to `main`.
- Avoid shell/network/destructive operations unless explicitly authorized and appropriate to the task.
- Do not run code emitted by evaluated agents. Controlled fixture execution follows LCP runner policies, not these developer-agent profiles.
- Each owner reports a concise handoff: changed paths, decisions, unverified assumptions and risks.
- A change to frozen schemas, routes, shared types, privileges, security boundaries or owned paths requires a **Change Request**. Jarvis moves the Spec back to planning; no silent drift.

## Phase 3 — Independent validation

Mefisto evaluates the diff against `contract.md` and `tests.md`, records exact commands, expected/actual results and missing evidence in `validation-result.md`, and produces `review.md`.

Allowed verdicts: `passed`, `failed`, `blocked`, `passed_with_restrictions`. Individual checks: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`. Missing evidence never becomes PASS. A validator must not claim to have executed local commands unless those outputs are available.

Jarvis updates the Spec state and index after reviewing Mefisto's evidence. Human approval is required before merge/release.

## State machine

`draft → ready → in_progress → done` is the normal path.
Alternative states: `paused`, `blocked`, `cancelled`, `superseded`, `rejected`. `rejected` applies only to `draft` before human approval.

Keep `SDD/index.md` current. Link validation evidence from `review.md`.

## Separation from product evaluation

The **LCP product** executes Response, Task and Code workloads under independent, versioned evaluation policies. The **development agents** here are simply contributor roles. Their internal verdicts do not supersede product PolicyDecision or automated test evidence.

## Stack reference

Python 3.12+, FastAPI, Pydantic v2, PostgreSQL/SQLAlchemy/Alembic, Redis/RQ, Vue 3/TypeScript/Vite, Docker Compose, pytest and GitHub Actions. Do not introduce frameworks for agent orchestration solely to make the architecture look complex.
