"""Package previously executed JUnit, agent-log hash and git diff for LCP v1a.

This script NEVER runs an agent, imports generated code, or executes tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

BENCHMARK = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(workspace: Path, *args: str) -> str:
    return subprocess.run(
        ("git", "-C", str(workspace), *args),
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def valid_file(path: Path, max_bytes: int = MAX_BYTES) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError(f"Missing, symlinked or oversized evidence: {path}")


def nonnegative_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected exit code integer") from exc
    if result < 0:
        raise argparse.ArgumentTypeError("exit code must be nonnegative")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, type=Path)
    parser.add_argument("--strategy", required=True, choices=("WITH_SPEC", "WITHOUT_SPEC"))
    parser.add_argument("--agent", required=True, help="Observed agent name and exact version")
    parser.add_argument("--model", required=True, help="Observed model name and version")
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--agent-exit", required=True, type=nonnegative_int)
    parser.add_argument("--pytest-exit", required=True, type=nonnegative_int)
    args = parser.parse_args(argv)

    trial = args.experiment.expanduser().resolve()
    arm = "with-spec" if args.strategy == "WITH_SPEC" else "without-spec"
    workspace = trial / arm
    protocol_file = trial / "protocol.json"
    valid_file(protocol_file, 32768)
    protocol = json.loads(protocol_file.read_text())
    if protocol.get("task_id") != "code-001" or not isinstance(protocol.get("base_commit"), str):
        raise ValueError("Unknown benchmark protocol")
    if protocol["acceptance_sha256"] != digest(BENCHMARK / "acceptance" / "test_checkout.py"):
        raise ValueError("Acceptance suite hash mismatch")
    if protocol["task_sha256"] != digest(BENCHMARK / "TASK.md"):
        raise ValueError("Task hash mismatch")
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("Missing or invalid agent workspace")
    if git(workspace, "rev-parse", "HEAD") != protocol["base_commit"]:
        raise ValueError("Agent must not commit; trial base changed")
    if git(workspace, "diff", "--name-only", "HEAD") not in ("", "checkout.py"):
        raise ValueError("Tracked changes outside checkout.py")
    if git(workspace, "ls-files", "--others", "--exclude-standard"):
        raise ValueError("Untracked files present: review before collection")
    valid_file(args.junit)
    valid_file(args.log)
    if not args.agent.strip() or not args.model.strip():
        raise ValueError("Agent/model identity is required")

    patch = subprocess.run(
        ("git", "-C", str(workspace), "diff", "--no-ext-diff", "HEAD", "--", "checkout.py"),
        check=True, capture_output=True,
    ).stdout
    if len(patch) > MAX_BYTES:
        raise ValueError("Diff exceeds size limit")

    destination = trial / "evidence" / arm
    if destination.exists():
        raise ValueError("Evidence directory already exists, will not overwrite")
    destination.mkdir(parents=True)
    shutil.copyfile(args.junit, destination / "tests.xml")
    (destination / "changes.diff").write_bytes(patch)
    manifest = {
        "task_id": protocol["task_id"],
        "repository": protocol["repository"],
        "base_commit": protocol["base_commit"],
        "agent": args.agent.strip(),
        "model": args.model.strip(),
        "strategy": args.strategy,
        "provenance": f"local-codex-run:sha256:{digest(args.log)}",
        "junit_file": "tests.xml",
        "diff_file": "changes.diff",
        "agent_exit_code": args.agent_exit,
        "acceptance_pytest_exit_code": args.pytest_exit,
        "task_sha256": protocol["task_sha256"],
        "spec_sha256": protocol["spec_sha256"] if args.strategy == "WITH_SPEC" else None,
        "acceptance_sha256": protocol["acceptance_sha256"],
    }
    # Do not invent usage/tokens, cost or duration. LCP v1a ignores extra metadata.
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(destination / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
