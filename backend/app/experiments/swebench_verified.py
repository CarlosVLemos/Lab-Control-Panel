"""Offline import of published mini-swe-agent SWE-bench Verified trajectories.

No network calls, execution, or benchmark re-evaluation occur here. Inputs are
untrusted data; the resulting JSON is evidence from the dataset publisher.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

DATASET = "tarsur385/swebench-verified-trajectories"
REVISION = "773748a7c1222e8a642a7059821498e14293562a"
FORMAT = "mini-swe-agent-1.1"
MAX_BYTES = 5_000_000
MODELS = frozenset({
    "claude-4.5-opus-high", "gemini-3-flash-high", "minimax-m2.5-high",
    "claude-opus-4.6", "gpt-5.2-codex", "gpt-5.2-high",
    "glm-5-high", "claude-4.5-haiku-high", "gpt-5-mini", "gemini-3-pro",
})
INSTANCE_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-[0-9]+\Z")
HEX_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class ImportErrorEvidence(ValueError):
    """The submitted evidence cannot be safely interpreted."""


def _required_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ImportErrorEvidence(f"{label} deve ser um objeto JSON")
    return value


def _source_path(path: Path) -> tuple[str, str, str]:
    """Reject files without the dataset's four-component relative layout."""
    parts = path.parts[-4:]
    if len(parts) != 4 or parts[0] != "swebench_verified_raw":
        raise ImportErrorEvidence("caminho inválido: esperado swebench_verified_raw/<modelo>/<issue>/<issue>.traj.json")
    root, model, instance, filename = parts
    if model not in MODELS or not INSTANCE_RE.fullmatch(instance):
        raise ImportErrorEvidence("modelo ou identificador de issue não reconhecido")
    if filename != f"{instance}.traj.json":
        raise ImportErrorEvidence("nome do arquivo não corresponde à issue")
    return model, instance, "/".join(parts)


def _optional_nonnegative(value: Any, label: str, *, integer: bool) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ImportErrorEvidence(f"{label} deve ser um número finito não negativo")
    if integer and (not isinstance(value, int)):
        raise ImportErrorEvidence(f"{label} deve ser inteiro")
    return value


def import_run(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    model, instance, relative = _source_path(path)
    try:
        with path.open("rb") as handle:
            payload = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ImportErrorEvidence(f"não foi possível ler {path}: {exc.strerror or exc}") from exc
    if len(payload) > MAX_BYTES:
        raise ImportErrorEvidence(f"arquivo excede {MAX_BYTES} bytes")
    sha = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None:
        if not HEX_SHA_RE.fullmatch(expected_sha256) or sha != expected_sha256:
            raise ImportErrorEvidence("SHA-256 local diferente do valor esperado")
    try:
        document = _required_object(json.loads(payload), "trajetória")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ImportErrorEvidence("arquivo JSON inválido") from exc
    if document.get("trajectory_format") != FORMAT:
        raise ImportErrorEvidence("formato de trajetória não suportado")
    if document.get("instance_id") != instance:
        raise ImportErrorEvidence("issue no conteúdo diverge do caminho")

    info = _required_object(document.get("info"), "info")
    docent = _required_object(info.get("docent"), "info.docent")
    if docent.get("model_label") != model:
        raise ImportErrorEvidence("modelo no conteúdo diverge do caminho")
    resolved = info.get("resolved")
    if not isinstance(resolved, bool):
        raise ImportErrorEvidence("info.resolved deve ser booleano")
    scores = info.get("scores")
    if isinstance(scores, dict) and "resolved" in scores:
        score = scores["resolved"]
        if type(score) is not int or score not in (0, 1) or bool(score) != resolved:
            raise ImportErrorEvidence("info.scores.resolved conflita com info.resolved")
    submission = info.get("submission")
    if not isinstance(submission, str):
        raise ImportErrorEvidence("info.submission deve ser texto (pode ser vazio)")
    exit_status = info.get("exit_status")
    if not isinstance(exit_status, str):
        raise ImportErrorEvidence("info.exit_status deve ser texto")
    stats = _required_object(info.get("model_stats"), "info.model_stats")
    cost = _optional_nonnegative(stats.get("instance_cost"), "instance_cost", integer=False)
    calls = _optional_nonnegative(stats.get("api_calls"), "api_calls", integer=True)
    messages = document.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ImportErrorEvidence("messages deve ser lista não vazia")
    events: list[dict[str, Any]] = []
    for idx, item in enumerate(messages):
        msg = _required_object(item, f"messages[{idx}]")
        role = msg.get("role")
        if role not in ("system", "user", "assistant", "tool"):
            raise ImportErrorEvidence(f"messages[{idx}].role desconhecido")
        content = msg.get("content")
        if content is not None and not isinstance(content, str):
            raise ImportErrorEvidence(f"messages[{idx}].content inválido")
        tool_calls = msg.get("tool_calls")
        if tool_calls is not None and not isinstance(tool_calls, list):
            raise ImportErrorEvidence(f"messages[{idx}].tool_calls inválido")
        events.append({
            "index": idx, "role": role, "content": content,
            "tool_calls": tool_calls if tool_calls is not None else [],
        })

    return {
        "model": model,
        "instance_id": instance,
        "published_resolved": resolved,
        "exit_status": exit_status,
        "patch": submission or None,
        "patch_status": "provided" if submission else "not_recorded",
        "reported_cost_usd": cost,
        "reported_api_calls": calls,
        "assistant_turns": sum(e["role"] == "assistant" for e in events),
        "message_count": len(events),
        "events": events,
        "source": {
            "dataset": DATASET, "revision": REVISION,
            "path": relative,
            "url": f"https://huggingface.co/datasets/{DATASET}/blob/{REVISION}/{relative}",
            "local_sha256": sha,
            "source_authenticity_verified": False,
        },
    }


def import_pair(left: Path, right: Path, *, left_sha256: str | None = None, right_sha256: str | None = None) -> dict[str, Any]:
    a = import_run(left, expected_sha256=left_sha256)
    b = import_run(right, expected_sha256=right_sha256)
    if a["instance_id"] != b["instance_id"]:
        raise ImportErrorEvidence("as tentativas devem pertencer à mesma issue")
    if a["model"] == b["model"]:
        raise ImportErrorEvidence("as tentativas devem identificar modelos diferentes")
    return {
        "schema_version": "exp-001/v1",
        "kind": "published_external_evidence",
        "benchmark_usage": "case_study_only_not_model_ranking",
        "instance_id": a["instance_id"],
        "comparability": "same_instance_only",
        "re_evaluated_locally": False,
        "runs": [a, b],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Importa duas trajetórias SWE-bench Verified locais, sem execução de código ou rede.")
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--left-sha256", default=None)
    parser.add_argument("--right-sha256", default=None)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in (args.left.resolve(), args.right.resolve()):
            raise ImportErrorEvidence("saída não pode sobrescrever uma trajetória de entrada")
        result = import_pair(args.left, args.right, left_sha256=args.left_sha256, right_sha256=args.right_sha256)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ImportErrorEvidence, OSError) as exc:
        parser.error(str(exc))
    print(f"Importadas 2 trajetórias para {result['instance_id']} em {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
