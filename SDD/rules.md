# SDD — Development governance

This file is the single normative source for AI-assisted development of Lab Control Panel. GitHub Issues define desired outcomes; tests and observed evidence prove completion. Do not confuse development agents with the Response, Task and Code workloads evaluated by the product.

## Owners

| Agent | Primary responsibility | Boundary |
| --- | --- | --- |
| **Jarvis** | Analyze requests, plan, assign scope, coordinate handoffs and maintain Spec state | Never self-approves code |
| **Maquiavel** | Python domain, API, persistence, jobs, runner and backend tests | Must not silently alter UI contracts |
| **Van Gogh** | Vue/TypeScript UI, UX, error/empty/loading and evidence visualization | Must not silently alter API contracts |
| **Mefisto** | Independent correctness, security, regression and test-evidence review | Must not implement the work it judges |

These are roles, not evidence that a tool spawned separate processes. Use an actual subagent only when the current Codex client supports it and task independence justifies the extra context/tokens. At most two simultaneous writing agents, each on disjoint files. Use `SINGLE_WRITER` by default; select `PARALLEL_SAFE` only after proving separate ownership and a frozen shared contract.

## Task classification

Classify by **highest risk**, not file count; document the selection in the PR.

| Track | Use when | Mandatory artifacts |
| --- | --- | --- |
| **QUICK** | Small isolated change, no public contract, schema, auth, execution-boundary or release impact | Issue/goal, acceptance check, focused test and short PR summary. No formal Spec. |
| **STANDARD** | Multi-file feature or nontrivial refactor; bounded risks; no critical boundary change | Short plan, affected paths, acceptance criteria and tests. Spec/contract only if cross-module interface changes. |
| **CRITICAL** | Database migration with data implications; public API/schema contract; auth/tenancy; code execution; policy gates, rollout, security controls or irreversible effects | Full `SDD/spec/<id>/` documents, explicitly approved `FROZEN` contract before implementation, independent Mefisto review and human merge decision. |

Escalate QUICK -> STANDARD -> CRITICAL when evidence or scope changes; never downgrade solely to skip tests. For CRITICAL, classify an interface-breaking change as requiring a Change Request even if the code change is short.

## Context before changing code

1. Read this file and the user request/Issue; inspect `git status`, the current branch and directly affected files.
2. Read `docs/PROJECT_SPEC.md` or `docs/ARCHITECTURE.md` only when the task touches those decisions. Consult active Spec/ADRs when they apply.
3. Search for nearby patterns, tests and call sites. Prefer changing the smallest coherent surface.
4. Use `.agents/skills/lcp-implement-issue/SKILL.md` for implementation and `.agents/skills/lcp-review-change/SKILL.md` for independent review; these are optional repeatable procedures, not automatic permission grants.
5. If crucial information is absent, name the assumption and select the least risky reversible interpretation; do not silently invent APIs or metrics.

Keep prompts/task plans bounded: objective, scope, paths, non-goals, checks and stop conditions. Avoid loading the entire repository or pasting long logs unless needed.

## Planning and execution

- QUICK: one owner implements and validates; a distinct review perspective is still desirable for risky changes.
- STANDARD: Jarvis writes a concise plan; Maquiavel/Van Gogh own non-overlapping implementation. Freeze shared contracts when both touch an API boundary.
- CRITICAL: Jarvis creates `spec.md` and `tasks.md`; Maquiavel + Van Gogh define `contract.md` as applicable; Mefisto defines `tests.md`. Human approval marks contract `FROZEN` before edits. Do not begin another CRITICAL Spec while one is `in_progress` without approved carry-over.
- Work on a feature branch. Keep edits inside declared **Allowed paths**. No uncontrolled package changes, shell/network, destructive commands, migration execution, untrusted code or secret access.
- Only parallelize independent reads or writing on disjoint paths after a shared contract is settled. Extra agents cost tokens and can create conflicting edits.
- If frozen routes, schemas, safety limits, privileges or owned paths must change, stop and record a **Change Request** before resuming implementation.
- Maquiavel documents backend responses/errors for Van Gogh; Van Gogh documents visual states for Mefisto. Handoffs should be concise and factual.

## Verification before claiming Done

- Test the changed behavior and at least one relevant regression path; run the narrowest useful commands first, then full checks if feasible.
- Prefer deterministic checks and contract tests. For probabilistic LLM features, record dataset version, candidate configuration, repetitions, costs and uncertainty instead of treating one output as proof.
- Record commands, environment, exit status and actual evidence; `NOT_RUN` and `BLOCKED` are not `PASS`.
- Mefisto reviews the diff against acceptance criteria, security boundaries and test plan when required. Verdicts: `passed`, `failed`, `blocked`, `passed_with_restrictions`; checks: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`.
- A green CI proves only the checks actually configured. Manual review is required before merge/release; do not self-merge or close Issues merely because an agent reports success.
- Write final handoff: what changed, verification evidence, limitations, remaining risks and PR link.

## Spec lifecycle for CRITICAL work

`draft → ready → in_progress → done` is the normal path. Alternative states: `paused`, `blocked`, `cancelled`, `superseded`, `rejected` (`draft` only). Maintain `SDD/index.md`; use `SDD/templates/` for contract, tasks, tests, validation-result and review. Human approval gates contract freeze and merge.

## Product boundaries

Production evaluation/policy remains separate from the developer workflow. `INCONCLUSIVE` must not promote a release; LLM-as-judge does not replace deterministic security checks. LCP's code runner accepts only controlled fixtures until isolation and a threat model are verified. Development-agent verdicts do not supersede product PolicyDecision or automated checks. A hash is a fingerprint, not signed provenance.
