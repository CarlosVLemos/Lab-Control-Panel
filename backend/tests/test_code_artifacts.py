"""Focused tests for the offline Code evidence comparison boundary."""
import json

import pytest

from app.evaluation.code_artifacts import EvidenceError, compare_bundles, load_bundle, main


JUNIT_BASE = """<testsuite name="acceptance" tests="3">
  <testcase classname="test_api" name="test_success"/>
  <testcase classname="test_api" name="test_failure"><failure message="wrong output"/></testcase>
  <testcase classname="test_api" name="test_skipped"><skipped/></testcase>
</testsuite>"""
JUNIT_CANDIDATE = """<testsuites><testsuite name="acceptance">
  <testcase classname="test_api" name="test_success"/>
  <testcase classname="test_api" name="test_failure"/>
  <testcase classname="test_api" name="test_skipped"><skipped/></testcase>
</testsuite></testsuites>"""
DIFF = """diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,2 +1,3 @@
-old_line
+new_line
+another_line
 context
"""


def bundle(tmp_path, folder, strategy, *, junit=JUNIT_BASE, diff=DIFF, **changes):
    directory = tmp_path / folder
    directory.mkdir()
    (directory / "tests.xml").write_text(junit, encoding="utf-8")
    (directory / "changes.diff").write_text(diff, encoding="utf-8")
    manifest = {
        "task_id": "code-001",
        "repository": "example/service",
        "base_commit": "a" * 40,
        "agent": "mini-swe-agent",
        "model": "same-model",
        "strategy": strategy,
        "provenance": "local-run-with-recorded-artifacts",
        "junit_file": "tests.xml",
        "diff_file": "changes.diff",
    }
    manifest.update(changes)
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_comparable_real_imported_artifacts_are_summarized_without_invented_usage(tmp_path):
    baseline = load_bundle(bundle(tmp_path, "a", "WITHOUT_SPEC"))
    candidate = load_bundle(bundle(tmp_path, "b", "WITH_SPEC", junit=JUNIT_CANDIDATE))
    result = compare_bundles(baseline, candidate)
    assert result["status"] == "COMPARABLE"
    assert result["reasons"] == []
    assert baseline.tests.to_dict() == {
        "total": 3, "passed": 1, "failed": 1, "errors": 0, "skipped": 1,
    }
    assert candidate.tests.to_dict() == {
        "total": 3, "passed": 2, "failed": 0, "errors": 0, "skipped": 1,
    }
    assert baseline.diff == {"added_lines": 2, "removed_lines": 1}
    assert baseline.usage is None and candidate.usage is None
    assert len(baseline.source_hashes["junit_sha256"]) == 64
    assert baseline.source_hashes["junit_sha256"] != candidate.source_hashes["junit_sha256"]


def test_mismatch_in_task_repository_base_model_or_testcases_is_inconclusive(tmp_path):
    reference = load_bundle(bundle(tmp_path, "a", "WITHOUT_SPEC"))
    candidate = load_bundle(bundle(
        tmp_path, "b", "WITH_SPEC", task_id="other", repository="other/repo",
        base_commit="b" * 40, model="different",
        junit="<testsuite><testcase classname='other' name='test_other'/></testsuite>",
    ))
    result = compare_bundles(reference, candidate)
    assert result["status"] == "INCONCLUSIVE"
    assert "Different task_id" in result["reasons"]
    assert "Different base_commit" in result["reasons"]
    assert "Different model" in result["reasons"]
    assert "Testcase identities differ between executions" in result["reasons"]


def test_two_identical_strategies_are_not_a_valid_comparison(tmp_path):
    a = load_bundle(bundle(tmp_path, "a", "WITHOUT_SPEC"))
    b = load_bundle(bundle(tmp_path, "b", "WITHOUT_SPEC"))
    assert compare_bundles(a, b)["status"] == "INCONCLUSIVE"


@pytest.mark.parametrize("junit", [
    "<testsuite/>",
    "<testsuite><testcase name='a'/><testcase name='a'/></testsuite>",
    "<testsuite><testcase/></testsuite>",
    "<testsuite><testcase name='a'><failure/><error/></testcase></testsuite>",
    "<!DOCTYPE testsuite [<!ENTITY boom 'expanded'>]><testsuite><testcase name='a'/></testsuite>",
    "<untrusted><testcase name='a'/></untrusted>",
    "<testsuite><testcase name='broken'></testsuite>",
])
def test_rejects_invalid_or_ambiguous_junit_evidence(tmp_path, junit):
    path = bundle(tmp_path, "bad", "WITH_SPEC", junit=junit)
    with pytest.raises(EvidenceError):
        load_bundle(path)


def test_rejects_path_traversal_and_symlink(tmp_path):
    path = bundle(tmp_path, "bad", "WITH_SPEC", junit_file="../outside.xml")
    with pytest.raises(EvidenceError):
        load_bundle(path)

    valid = bundle(tmp_path, "good", "WITH_SPEC")
    link = valid.parent / "linked.xml"
    link.symlink_to(valid.parent / "tests.xml")
    data = json.loads(valid.read_text())
    data["junit_file"] = "linked.xml"
    valid.write_text(json.dumps(data))
    with pytest.raises(EvidenceError):
        load_bundle(valid)


def test_rejects_oversized_evidence(tmp_path):
    path = bundle(tmp_path, "big", "WITH_SPEC")
    (path.parent / "tests.xml").write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(EvidenceError, match="exceeds"):
        load_bundle(path)


@pytest.mark.parametrize("invalid_usage", [
    {"input_tokens": -1},
    {"input_tokens": True},
    {"duration_ms": 3.5},
    {"cost_usd": "NaN"},
    {"cost_usd": "-1"},
    {"cost_usd": "Infinity"},
    {"unrecognized": 20},
    {},
])
def test_rejects_invalid_usage(tmp_path, invalid_usage):
    path = bundle(tmp_path, "bad", "WITH_SPEC", usage=invalid_usage)
    with pytest.raises(EvidenceError):
        load_bundle(path)


def test_preserves_provided_usage_without_fabrication(tmp_path):
    path = bundle(tmp_path, "usage", "WITH_SPEC", usage={
        "input_tokens": 174, "cost_usd": "0.0025",
    })
    assert load_bundle(path).usage == {"input_tokens": 174, "cost_usd": "0.0025"}


def test_cli_outputs_json_and_returns_inconclusive_exit_code(tmp_path, capsys):
    without = bundle(tmp_path, "without", "WITHOUT_SPEC")
    with_spec = bundle(tmp_path, "with", "WITH_SPEC", junit=JUNIT_CANDIDATE)
    assert main([str(without), str(with_spec)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "COMPARABLE"
    assert len(payload["observed"]) == 2

    with_spec.write_text(with_spec.read_text().replace('"code-001"', '"other-task"'))
    assert main([str(without), str(with_spec)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "INCONCLUSIVE"
