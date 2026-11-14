"""Contract tests with synthetic inputs; no claim of external benchmark execution."""

import json
from pathlib import Path

import pytest

from app.experiments.swebench_verified import ImportErrorEvidence, import_pair, import_run, main

INSTANCE = "astropy__astropy-12907"


def create_run(tmp_path: Path, model: str, *, instance: str = INSTANCE, **changes):
    path = tmp_path / "swebench_verified_raw" / model / instance / f"{instance}.traj.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "trajectory_format": "mini-swe-agent-1.1",
        "instance_id": instance,
        "messages": [
            {"role": "user", "content": "issue summary"},
            {"role": "assistant", "content": "plan", "tool_calls": [{"function": "bash", "arguments": {"command": "echo test"}}]},
            {"role": "tool", "content": "exit 0"},
        ],
        "info": {
            "resolved": True,
            "submission": "",
            "exit_status": "Submitted",
            "scores": {"resolved": 1},
            "model_stats": {"instance_cost": 0.3, "api_calls": 4},
            "docent": {"model_label": model},
        },
    }
    for key, value in changes.items():
        record[key] = value
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_import_retains_publisher_outcome_without_inventing_patch(tmp_path):
    path = create_run(tmp_path, "gpt-5.2-codex")
    result = import_run(path)
    assert result["published_resolved"] is True
    assert result["patch"] is None and result["patch_status"] == "not_recorded"
    assert result["reported_cost_usd"] == 0.3
    assert result["reported_api_calls"] == 4
    assert result["assistant_turns"] == 1
    assert result["events"][1]["tool_calls"][0]["function"] == "bash"
    assert len(result["source"]["local_sha256"]) == 64
    assert result["source"]["source_authenticity_verified"] is False


def test_pair_same_issue_different_models_only(tmp_path):
    a = create_run(tmp_path, "gpt-5.2-codex")
    b = create_run(tmp_path, "gpt-5-mini")
    result = import_pair(a, b)
    assert result["instance_id"] == INSTANCE
    assert result["re_evaluated_locally"] is False
    assert [r["model"] for r in result["runs"]] == ["gpt-5.2-codex", "gpt-5-mini"]
    with pytest.raises(ImportErrorEvidence, match="modelos diferentes"):
        import_pair(a, a)


def test_rejects_different_issues(tmp_path):
    a = create_run(tmp_path, "gpt-5.2-codex")
    b = create_run(tmp_path, "gpt-5-mini", instance="django__django-10097")
    with pytest.raises(ImportErrorEvidence, match="mesma issue"):
        import_pair(a, b)


def test_rejects_wrong_model_metadata(tmp_path):
    path = create_run(tmp_path, "gpt-5-mini")
    data = json.loads(path.read_text())
    data["info"]["docent"]["model_label"] = "gpt-5.2-codex"
    path.write_text(json.dumps(data))
    with pytest.raises(ImportErrorEvidence, match="modelo no conteúdo"):
        import_run(path)


def test_rejects_conflicting_resolved_labels(tmp_path):
    path = create_run(tmp_path, "gpt-5-mini")
    data = json.loads(path.read_text())
    data["info"]["scores"]["resolved"] = 0
    path.write_text(json.dumps(data))
    with pytest.raises(ImportErrorEvidence, match="conflita"):
        import_run(path)


def test_rejects_invalid_format_and_path(tmp_path):
    path = create_run(tmp_path, "gpt-5-mini", trajectory_format="different")
    with pytest.raises(ImportErrorEvidence, match="não suportado"):
        import_run(path)
    with pytest.raises(ImportErrorEvidence, match="caminho inválido"):
        import_run(tmp_path / "invalid.json")


def test_checks_sha256_when_provided(tmp_path):
    path = create_run(tmp_path, "gpt-5-mini")
    with pytest.raises(ImportErrorEvidence, match="SHA-256"):
        import_run(path, expected_sha256="a" * 64)


def test_rejects_non_finite_reported_cost(tmp_path):
    path = create_run(tmp_path, "gpt-5-mini")
    data = json.loads(path.read_text())
    data["info"]["model_stats"]["instance_cost"] = float("nan")
    path.write_text(json.dumps(data))
    with pytest.raises(ImportErrorEvidence, match="finito"):
        import_run(path)


def test_cli_writes_json_without_execution(tmp_path):
    left = create_run(tmp_path, "gpt-5.2-codex")
    right = create_run(tmp_path, "gpt-5-mini")
    out = tmp_path / "paired.json"
    assert main(["--left", str(left), "--right", str(right), "--output", str(out)]) == 0
    data = json.loads(out.read_text())
    assert len(data["runs"]) == 2
    assert data["benchmark_usage"] == "case_study_only_not_model_ranking"


def test_cli_does_not_overwrite_inputs(tmp_path):
    left = create_run(tmp_path, "gpt-5.2-codex")
    right = create_run(tmp_path, "gpt-5-mini")
    with pytest.raises(SystemExit):
        main(["--left", str(left), "--right", str(right), "--output", str(left)])
    assert json.loads(left.read_text())["instance_id"] == INSTANCE
