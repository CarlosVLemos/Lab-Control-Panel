"""Offline comparison of observed Code task artifacts.

This module does NOT execute imported code, commands or tests. JUnit XML is an
untrusted self-reported artifact, not proof of independent test verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

MAX_MANIFEST_BYTES = 32 * 1024
MAX_JUNIT_BYTES = 2 * 1024 * 1024
MAX_DIFF_BYTES = 2 * 1024 * 1024
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")
STRATEGIES = frozenset({"WITH_SPEC", "WITHOUT_SPEC"})


class EvidenceError(ValueError):
    """Invalid, ambiguous, unsafe or incomplete imported evidence."""


@dataclass(frozen=True)
class TestSummary:
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    ids: frozenset[str]

    def to_dict(self) -> dict[str, int]:
        return {k: getattr(self, k) for k in ("total", "passed", "failed", "errors", "skipped")}


@dataclass(frozen=True)
class ArtifactBundle:
    task_id: str
    repository: str
    base_commit: str
    agent: str
    model: str
    strategy: str
    provenance: str
    tests: TestSummary
    diff: dict[str, int]
    source_hashes: dict[str, str]
    usage: dict[str, int | str] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repository": self.repository,
            "base_commit": self.base_commit,
            "agent": self.agent,
            "model": self.model,
            "strategy": self.strategy,
            "provenance": self.provenance,
            "tests": self.tests.to_dict(),
            "diff": self.diff,
            "source_hashes": self.source_hashes,
            "usage": self.usage,
        }


def _read(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"Cannot read evidence: {path.name}") from exc
    if len(data) > limit:
        raise EvidenceError(f"Evidence exceeds {limit} bytes: {path.name}")
    return data


def _artifact_path(manifest_path: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise EvidenceError("Artifact path must be a nonempty relative filename")
    path = Path(value)
    if path.is_absolute() or len(path.parts) != 1 or value in (".", ".."):
        raise EvidenceError("Artifact must be a filename beside the manifest")
    candidate = manifest_path.parent / path
    if candidate.is_symlink() or not candidate.is_file():
        raise EvidenceError("Artifact must be an existing regular file, not a symlink")
    return candidate


def _required(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"Missing or invalid manifest field: {key}")
    return value.strip()


def _usage(data: Any) -> dict[str, int | str] | None:
    if data is None:
        return None
    if not isinstance(data, dict) or not data:
        raise EvidenceError("usage must be a nonempty object or null")
    allowed = {"input_tokens", "output_tokens", "duration_ms", "cost_usd"}
    if not set(data).issubset(allowed):
        raise EvidenceError("usage contains unknown metrics")
    out: dict[str, int | str] = {}
    for key, value in data.items():
        if key == "cost_usd":
            try:
                if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                    raise InvalidOperation()
                decimal_value = Decimal(str(value))
                if not decimal_value.is_finite() or decimal_value < 0:
                    raise InvalidOperation()
                out[key] = str(decimal_value)
            except (InvalidOperation, ValueError) as exc:
                raise EvidenceError("cost_usd must be a finite nonnegative decimal") from exc
        else:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise EvidenceError(f"{key} must be a nonnegative integer")
            out[key] = value
    return out


def _tests(xml: bytes) -> TestSummary:
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)\b", xml, re.IGNORECASE):
        raise EvidenceError("DTD/entities forbidden in untrusted JUnit evidence")
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise EvidenceError("Invalid JUnit XML") from exc
    if root.tag not in ("testsuite", "testsuites"):
        raise EvidenceError("JUnit root must be testsuite or testsuites")
    cases = root.findall(".//testcase")
    if not cases:
        raise EvidenceError("JUnit evidence has no testcase elements")
    if len(cases) > 10000:
        raise EvidenceError("JUnit evidence exceeds testcase limit")
    ids: set[str] = set()
    failed = errors = skipped = 0
    for case in cases:
        name = case.get("name")
        if not name:
            raise EvidenceError("JUnit testcase is missing name")
        test_id = f"{case.get('classname', '')}::{name}"
        if test_id in ids:
            raise EvidenceError("JUnit testcase identity is duplicated")
        ids.add(test_id)
        children = {child.tag for child in case}
        statuses = children & {"failure", "error", "skipped"}
        if len(statuses) > 1:
            raise EvidenceError("JUnit testcase has ambiguous status")
        failed += int("failure" in statuses)
        errors += int("error" in statuses)
        skipped += int("skipped" in statuses)
    total = len(cases)
    return TestSummary(total, total - failed - errors - skipped, failed, errors, skipped, frozenset(ids))


def _diff_counts(data: bytes) -> dict[str, int]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise EvidenceError("Unified diff must be UTF-8") from exc
    added = removed = 0
    for line in lines:
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        added += int(line.startswith("+"))
        removed += int(line.startswith("-"))
    return {"added_lines": added, "removed_lines": removed}


def load_bundle(manifest_path: str | Path) -> ArtifactBundle:
    """Read local evidence only; no subprocesses, remote access or artifact execution."""
    path = Path(manifest_path)
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("Manifest must be a regular file, not a symlink")
    raw = _read(path, MAX_MANIFEST_BYTES)
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("Invalid JSON manifest") from exc
    if not isinstance(manifest, dict):
        raise EvidenceError("Manifest must be a JSON object")
    required = ("task_id", "repository", "base_commit", "agent", "model",
                "strategy", "provenance", "junit_file", "diff_file")
    for key in required:
        _required(manifest, key)
    if not SHA_PATTERN.fullmatch(manifest["base_commit"]):
        raise EvidenceError("base_commit must be a lowercase 7-40 character hex SHA")
    if manifest["strategy"] not in STRATEGIES:
        raise EvidenceError("strategy must be WITH_SPEC or WITHOUT_SPEC")

    junit_bytes = _read(_artifact_path(path, manifest["junit_file"]), MAX_JUNIT_BYTES)
    diff_bytes = _read(_artifact_path(path, manifest["diff_file"]), MAX_DIFF_BYTES)
    return ArtifactBundle(
        task_id=manifest["task_id"], repository=manifest["repository"],
        base_commit=manifest["base_commit"], agent=manifest["agent"],
        model=manifest["model"], strategy=manifest["strategy"],
        provenance=manifest["provenance"], tests=_tests(junit_bytes),
        diff=_diff_counts(diff_bytes),
        source_hashes={
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "junit_sha256": hashlib.sha256(junit_bytes).hexdigest(),
            "diff_sha256": hashlib.sha256(diff_bytes).hexdigest(),
        },
        usage=_usage(manifest.get("usage")),
    )


def compare_bundles(left: ArtifactBundle, right: ArtifactBundle) -> dict[str, Any]:
    """Compare observations, not code quality or efficacy of a strategy."""
    reasons: list[str] = []
    for field in ("task_id", "repository", "base_commit", "agent", "model"):
        if getattr(left, field) != getattr(right, field):
            reasons.append(f"Different {field}")
    if {left.strategy, right.strategy} != STRATEGIES:
        reasons.append("Comparison requires one WITH_SPEC and one WITHOUT_SPEC execution")
    if left.tests.ids != right.tests.ids:
        reasons.append("Testcase identities differ between executions")
    return {
        "status": "INCONCLUSIVE" if reasons else "COMPARABLE",
        "reasons": reasons,
        "observed": [left.to_dict(), right.to_dict()],
        "interpretation": (
            "Imported JUnit results were not independently reexecuted. "
            "Line counts do not indicate code quality; no statistical superiority is claimed."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two imported Code artifact bundles offline")
    parser.add_argument("without_spec", type=Path)
    parser.add_argument("with_spec", type=Path)
    args = parser.parse_args(argv)
    try:
        result = compare_bundles(load_bundle(args.without_spec), load_bundle(args.with_spec))
    except EvidenceError as exc:
        print(f"Invalid evidence: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == "COMPARABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
