# CODE-001 — Paired coding-agent experiment

**Issue #40 · State: PREPARED — no agent/model was run.**

## Experiment

Question: Does a supplemental engineering Spec change the performance of a fixed coding agent on a checkout-event idempotency bug?

Both arms get the same starter code, task requirements, fixed acceptance tests, Python version, allowed tools, time/token budget, agent version and exact model ID. The only variation is the additional SPEC.md included in the WITH_SPEC arm prompt. One pair is exploratory, not a statistically conclusive study. Never call fixture smoke results real-agent evidence.

The starter deliberately fails 17 of 21 independent pytest acceptance cases on the initial validation. The task uses invented financial data; this is not production payment code.

## 1. Prepare

From the Lab-Control-Panel repository root, with Python 3.12+, pytest and Git installed:

~~~sh
export LCP_REPO="$PWD"
export RUN_DIR=/tmp/lcp-code001-first-trial
python benchmarks/code-001/tools/prepare.py --out "$RUN_DIR"
cat "$RUN_DIR/protocol.json"
~~~

Choose a fresh RUN_DIR that does not exist. The preparer creates one seed repository and two identical Git clones, without-spec and with-spec, with exactly the same HEAD commit. It writes the two prompts outside the clones. The frozen acceptance suite remains outside both agent directories, and the detailed Spec is only supplied through the WITH_SPEC prompt.

## 2. Run Codex in isolated workspaces

Requires an authenticated Codex CLI and available model/budget, none of which are available to the current ChatGPT execution environment. This command is a TEMPLATE, not evidence of execution. Set exactly the same model, agent version, reasoning effort and sandbox permissions for both arms. Record the Codex CLI version, settings and any failure.

~~~sh
export MODEL_ID=REPLACE_WITH_SUPPORTED_MODEL_ID
codex --version
(cd "$RUN_DIR/without-spec" && codex exec --model "$MODEL_ID" --sandbox workspace-write - < "$RUN_DIR/prompts/WITHOUT_SPEC.txt") > "$RUN_DIR/without-agent.log" 2>&1
printf '%s\n' "$?" > "$RUN_DIR/without-agent.exit"
(cd "$RUN_DIR/with-spec" && codex exec --model "$MODEL_ID" --sandbox workspace-write - < "$RUN_DIR/prompts/WITH_SPEC.txt") > "$RUN_DIR/with-agent.log" 2>&1
printf '%s\n' "$?" > "$RUN_DIR/with-agent.exit"
~~~

IMPORTANT: workspace-write is a write boundary, not proven read isolation. For blind evaluation run each agent in a disposable isolated machine/container, mounting only its clone and assigned prompt. Do NOT mount acceptance tests, other agent workspaces, host credentials or personal files. Avoid unrestricted execution or network access. Do not opportunistically retry a failing arm.

## 3. Run independent acceptance tests

Only after agent completion, run each generated program inside a disposable restricted test environment, never on a production server or through the LCP import process. Use identical external acceptance tests and preserve their outputs. A failing test command is useful evidence; record its real exit code. If shell has set -e, disable it around these commands.

~~~sh
mkdir -p "$RUN_DIR/test-results"
(cd "$RUN_DIR/without-spec"; PYTHONPATH="$PWD" python -m pytest -q "$LCP_REPO/benchmarks/code-001/acceptance/test_checkout.py" --junitxml="$RUN_DIR/test-results/without.xml")
printf '%s\n' "$?" > "$RUN_DIR/without-pytest.exit"
(cd "$RUN_DIR/with-spec"; PYTHONPATH="$PWD" python -m pytest -q "$LCP_REPO/benchmarks/code-001/acceptance/test_checkout.py" --junitxml="$RUN_DIR/test-results/with.xml")
printf '%s\n' "$?" > "$RUN_DIR/with-pytest.exit"
~~~

If a JUnit XML is absent or invalid, mark the execution BLOCKED rather than treating it as zero passed. Do not give the agent access to acceptance tests before it finishes.

## 4. Collect artifacts without executing code

~~~sh
export AGENT_ID='codex-cli EXACT_OBSERVED_VERSION'
python "$LCP_REPO/benchmarks/code-001/tools/collect.py" --experiment "$RUN_DIR" --strategy WITHOUT_SPEC --model "$MODEL_ID" --agent "$AGENT_ID" --junit "$RUN_DIR/test-results/without.xml" --log "$RUN_DIR/without-agent.log" --agent-exit "$(cat "$RUN_DIR/without-agent.exit")" --pytest-exit "$(cat "$RUN_DIR/without-pytest.exit")"
python "$LCP_REPO/benchmarks/code-001/tools/collect.py" --experiment "$RUN_DIR" --strategy WITH_SPEC --model "$MODEL_ID" --agent "$AGENT_ID" --junit "$RUN_DIR/test-results/with.xml" --log "$RUN_DIR/with-agent.log" --agent-exit "$(cat "$RUN_DIR/with-agent.exit")" --pytest-exit "$(cat "$RUN_DIR/with-pytest.exit")"
~~~

Collector validates frozen benchmark hashes and unchanged Git HEAD, reads the JUnit XML, generates diff and hashes the agent log. It does NOT verify the identity of a remote model, reexecute tests or verify the truth of submitted JUnit. Sanitize artifacts and logs before publication. Do not fabricate cost/tokens/duration.

## 5. Import results into LCP

~~~sh
cd "$LCP_REPO/backend"
python -m app.evaluation.code_artifacts "$RUN_DIR/evidence/without-spec/manifest.json" "$RUN_DIR/evidence/with-spec/manifest.json" > "$RUN_DIR/comparison.json"
cat "$RUN_DIR/comparison.json"
~~~

COMPARABLE means task/repo/base/agent/model and testcase IDs match. It does not mean PASS, better code, security, or statistical superiority. Record inputs, exit codes, resulting hashes, unknown metrics and limitations.

## Verification and status

~~~sh
cd backend
python -m pytest -q tests/test_code001_protocol.py
python -m pytest -q
~~~

Tests verify the local benchmark protocol, not genuine AI executions. If an authenticated Codex, proper isolated environment or budget is unavailable, report BLOCKED and provide the reproducible protocol. Nothing should be merged without human approval.
