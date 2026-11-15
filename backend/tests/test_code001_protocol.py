"""CODE-001 protocol checks. Local smoke ≠ an actual AI agent execution."""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from app.evaluation.code_artifacts import compare_bundles, load_bundle

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmarks" / "code-001"
PREPARE = BENCH / "tools" / "prepare.py"
COLLECT = BENCH / "tools" / "collect.py"
ACCEPTANCE = BENCH / "acceptance" / "test_checkout.py"


def run(*args, cwd=None, env=None, expected=0):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    assert result.returncode == expected, (result.stdout, result.stderr)
    return result.stdout


def prepare(tmp_path):
    path = tmp_path / "trial"
    run(sys.executable, str(PREPARE), "--out", str(path))
    return path, json.loads((path / "protocol.json").read_text())


def test_prepared_workspaces_share_commit_and_hide_acceptance(tmp_path):
    trial, protocol = prepare(tmp_path)
    assert len(protocol["base_commit"]) == 40
    for name in ("without-spec", "with-spec"):
        workspace = trial / name
        assert run("git", "-C", str(workspace), "rev-parse", "HEAD").strip() == protocol["base_commit"]
        assert (workspace / "checkout.py").read_bytes() == (BENCH / "starter" / "checkout.py").read_bytes()
        assert not (workspace / "SPEC.md").exists()
        assert not (workspace / "acceptance").exists()
    without = (trial / "prompts" / "WITHOUT_SPEC.txt").read_text()
    with_spec = (trial / "prompts" / "WITH_SPEC.txt").read_text()
    assert with_spec.startswith(without)
    assert "Transition table" in with_spec
    assert "Transition table" not in without
    assert subprocess.run([sys.executable, str(PREPARE), "--out", str(trial)], capture_output=True).returncode != 0


def test_offline_smoke_packages_identical_failing_starters_without_claiming_agent_run(tmp_path):
    trial, protocol = prepare(tmp_path)
    for name, strategy in (("without-spec", "WITHOUT_SPEC"), ("with-spec", "WITH_SPEC")):
        workspace = trial / name
        junit = trial / f"{name}.xml"
        log = trial / f"{name}.log"
        log.write_text("LOCAL SMOKE - NOT A REAL AGENT RUN\n")
        env = dict(os.environ, PYTHONPATH=str(workspace))
        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(ACCEPTANCE), f"--junitxml={junit}"],
            cwd=workspace, env=env, capture_output=True, text=True,
        )
        assert p.returncode == 1
        assert len(ET.parse(junit).getroot().findall(".//testcase")) == 21
        run(sys.executable, str(COLLECT), "--experiment", str(trial),
            "--strategy", strategy, "--model", "SMOKE-NOT-A-MODEL",
            "--agent", "SMOKE-NOT-AN-AGENT", "--junit", str(junit),
            "--log", str(log), "--agent-exit", "0", "--pytest-exit", "1")
    a = load_bundle(trial / "evidence" / "without-spec" / "manifest.json")
    b = load_bundle(trial / "evidence" / "with-spec" / "manifest.json")
    assert compare_bundles(a, b)["status"] == "COMPARABLE"
    assert a.tests.total == b.tests.total == 21
    assert a.tests.passed == b.tests.passed == 4
    assert a.usage is None and b.usage is None
    assert a.base_commit == b.base_commit == protocol["base_commit"]
    assert a.diff == {"added_lines": 0, "removed_lines": 0}
