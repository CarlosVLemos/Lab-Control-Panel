---
name: lcp-implement-issue
description: Implement or fix a Lab Control Panel GitHub Issue using risk-based planning, scoped edits, deterministic tests and a reviewable PR. Use for coding tasks; do not use for standalone research or code review.
---

# Implement a Lab Control Panel issue

1. Read `AGENTS.md` and `SDD/rules.md`; identify Issue number, acceptance criteria, base branch and current working tree. Do not overwrite unrelated edits.
2. Classify QUICK/STANDARD/CRITICAL. If CRITICAL, stop before writing code until the user approves a `FROZEN` Spec and allowed paths. For STANDARD, write a short plan. For QUICK, proceed with a focused change.
3. Locate existing implementation, tests, callers and contract. State which files may change, who owns them, and what must **not** change.
4. Use the smallest reversible patch; maintain typed contracts, fail-closed behavior and safe defaults. No extra frameworks, new dependencies or speculative abstractions without justification.
5. Validate with the smallest relevant test set; inspect failures, fix root causes, run appropriate regression/lint/Compose checks. If commands cannot run, record `NOT_RUN` with the reason.
6. Ask Mefisto (or use the review skill with a separate review pass) when risk warrants independent review. Do not treat a model statement as evidence of a test pass.
7. Submit a PR, not a direct main commit. Summarize acceptance checks, exact verification commands and actual results, unresolved risks and affected paths.

**Stop conditions:** missing frozen approval for CRITICAL; unclear permission to edit protected files; destructive command requirement; untrusted execution; contract drift requiring Change Request; tests fail with no safe fix.

Template for a compact issue handoff:

- Goal and risk track:
- Changes and paths:
- Tests (command → actual outcome):
- Not run / limitations:
- Risks / next action:
