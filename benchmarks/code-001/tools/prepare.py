"""Prepare two clean local Git workspaces for a paired coding-agent experiment.

Never executes an agent. Never overwrites an existing experiment directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BENCHMARK = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, text=True, capture_output=True,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    if out.exists():
        parser.error("Output directory already exists; refusing to overwrite experiment")
    out.mkdir(parents=True)

    seed = out / "seed"
    seed.mkdir()
    shutil.copy2(BENCHMARK / "starter" / "checkout.py", seed / "checkout.py")
    shutil.copy2(BENCHMARK / "TASK.md", seed / "TASK.md")
    (seed / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n*.pyc\n")
    git("-C", str(seed), "init", "--quiet")
    git("-C", str(seed), "add", "--", "checkout.py", "TASK.md", ".gitignore")
    git("-C", str(seed), "-c", "user.name=LCP Benchmark",
        "-c", "user.email=lcp-benchmark@example.invalid",
        "commit", "--quiet", "-m", "code-001 frozen starter")
    base_sha = git("-C", str(seed), "rev-parse", "HEAD")

    for arm in ("without-spec", "with-spec"):
        git("clone", "--quiet", "--local", str(seed), str(out / arm))
        assert git("-C", str(out / arm), "rev-parse", "HEAD") == base_sha

    prompts = out / "prompts"
    prompts.mkdir()
    common = (
        "Modify only checkout.py to fully satisfy TASK.md. Do not commit. "
        "No network or external dependencies. Do not inspect files outside this workspace, "
        "especially the external evaluator's acceptance tests.\n"
    )
    (prompts / "WITHOUT_SPEC.txt").write_text(common)
    (prompts / "WITH_SPEC.txt").write_text(
        common + "\nAdditional design Spec (same requirements):\n\n"
        + (BENCHMARK / "SPEC.md").read_text()
    )

    protocol = {
        "schema_version": 1,
        "task_id": "code-001",
        "repository": "LCP-CODE-001/local-seed",
        "base_commit": base_sha,
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "starter_sha256": digest(BENCHMARK / "starter" / "checkout.py"),
        "task_sha256": digest(BENCHMARK / "TASK.md"),
        "spec_sha256": digest(BENCHMARK / "SPEC.md"),
        "acceptance_sha256": digest(BENCHMARK / "acceptance" / "test_checkout.py"),
        "agents_executed": False,
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    print(json.dumps({"base_commit": base_sha, "output_directory": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
