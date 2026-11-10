---
name: lcp-review-change
description: Review a Lab Control Panel code change or pull request for correctness, security, regressions, scope drift and test evidence. Use for independent validation; not for implementing the same patch.
---

# Evidence-led PR review

1. Read `AGENTS.md`, `SDD/rules.md`, the Issue, diff, test plan and frozen contract if present.
2. Separate observed facts from assumptions; inspect changed code, relevant call sites, tests, config, migrations and authorization boundaries. Never trust PR descriptions or agent claims without checking.
3. Prioritize actionable problems: broken behavior, schema/API incompatibility, races/idempotency, unsafe commands, secrets, regressions, lack of evidence and non-reproducible results.
4. Run **only safe and authorized** relevant checks. Report exact commands, outcomes and the commit tested. If unavailable, mark `NOT_RUN`; do not infer PASS.
5. For LLM experiments, check dataset/candidate/policy versions, baseline comparability, cost and uncertainty; for CODE workload, check command allowlists and isolation.
6. Report concrete findings with severity, path/line and reproduction. Rank `BLOCKER` > `HIGH` > `MEDIUM` > `LOW`. Do not invent findings.
7. Return `passed`, `failed`, `blocked` or `passed_with_restrictions`. An inconclusive or missing critical check cannot become an unconditional approval.

Output:

- Verdict and reviewed revision
- Findings (severity, evidence, impact, suggested correction)
- Checks run (command → actual result)
- Unverified or blocked checks
- Scope/contract drift
- Remaining risk and human merge decision
