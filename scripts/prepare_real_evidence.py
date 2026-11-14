"""Prepare compact frontend evidence from operator-provided real datasets.

The script only reads JSON/JSONL and writes normalized JSON. It never executes
commands or patches found in trajectories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.experiments.swebench_verified import import_pair

SWE_LEFT = Path(
    "swebench/swebench_verified_raw/gpt-5.2-codex/astropy__astropy-12907/"
    "astropy__astropy-12907.traj.json"
)
SWE_RIGHT = Path(
    "swebench/swebench_verified_raw/gpt-5-mini/astropy__astropy-12907/"
    "astropy__astropy-12907.traj.json"
)
AGENTTRACE_SAMPLE = Path("agenttrace/agenttrace-sample.jsonl")
MAX_SOURCE_BYTES = 5_000_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_entries(dataset_dir: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest.files must be a list")
    return {entry["path"]: entry for entry in entries if isinstance(entry, dict) and isinstance(entry.get("path"), str)}


def _verified_path(dataset_dir: Path, relative: Path, entries: dict[str, dict[str, Any]]) -> tuple[Path, str]:
    entry = entries.get(relative.as_posix())
    if entry is None:
        raise ValueError(f"manifest entry missing for {relative}")
    path = dataset_dir / relative
    size = path.stat().st_size
    if size > MAX_SOURCE_BYTES or size != entry.get("bytes"):
        raise ValueError(f"size mismatch for {relative}")
    digest = _sha256(path)
    if digest != entry.get("sha256"):
        raise ValueError(f"SHA-256 mismatch for {relative}")
    return path, digest


def _select(record: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: record.get(key) for key in keys}


def _prepare_agenttrace(input_path: Path, digest: str) -> dict[str, Any]:
    traces: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict) or not isinstance(raw.get("spans"), list) or not isinstance(raw.get("llm_steps"), list):
            raise ValueError(f"invalid AgentTrace object on line {line_number}")
        spans = []
        for span in raw["spans"]:
            if not isinstance(span, dict):
                raise ValueError(f"invalid span on line {line_number}")
            compact = _select(span, (
                "span_id", "type", "tool_name", "tool_input", "tool_output", "start_ns", "end_ns",
                "duration_ms", "exit_code", "parent_span_id",
            ))
            telemetry = span.get("telemetry")
            compact["telemetry"] = _select(telemetry, (
                "user_time_s", "system_time_s", "max_rss_bytes", "read_bytes", "write_bytes",
            )) if isinstance(telemetry, dict) else None
            spans.append(compact)
        steps = []
        for step in raw["llm_steps"]:
            if not isinstance(step, dict):
                raise ValueError(f"invalid LLMStep on line {line_number}")
            steps.append(_select(step, ("step_id", "step_number", "duration_ms", "input_tokens", "output_tokens")))
        metadata = raw.get("metadata")
        traces.append({
            **_select(raw, (
                "trace_id", "timestamp_utc", "prompt", "model", "dataset_name", "task_id", "run_id",
                "total_duration_ms", "tool_span_count", "llm_step_count", "raw_file", "source_row_idx",
            )),
            "spans": spans,
            "llm_steps": steps,
            "metadata": _select(metadata, ("schema_version", "collector_version", "platform", "git_commit"))
            if isinstance(metadata, dict) else None,
        })
    if not traces:
        raise ValueError("AgentTrace sample has no traces")
    return {
        "schema_version": "obs-002/real-sample-v1",
        "source": {
            "dataset": "pagarsky/agent-trace",
            "revision": None,
            "revision_note": "The local manifest did not record a Hugging Face revision.",
            "path": AGENTTRACE_SAMPLE.as_posix(),
            "local_sha256": digest,
            "license": "Apache-2.0; upstream prompt-source terms also apply",
            "source_authenticity_verified": False,
            "reasoning_content_included": False,
        },
        "traces": traces,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare EXP-002 and OBS-002 real evidence without executing it.")
    parser.add_argument("--datasets-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    dataset_dir = args.datasets_dir.resolve()
    entries = _manifest_entries(dataset_dir)
    left, left_sha = _verified_path(dataset_dir, SWE_LEFT, entries)
    right, right_sha = _verified_path(dataset_dir, SWE_RIGHT, entries)
    agenttrace, agenttrace_sha = _verified_path(dataset_dir, AGENTTRACE_SAMPLE, entries)

    experiment = import_pair(left, right, left_sha256=left_sha, right_sha256=right_sha)
    observations = _prepare_agenttrace(agenttrace, agenttrace_sha)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "exp-002-astropy-12907.json").write_text(
        json.dumps(experiment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "obs-002-agenttrace-sample.json").write_text(
        json.dumps(observations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared 2 SWE-bench runs and {len(observations['traces'])} AgentTrace traces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
