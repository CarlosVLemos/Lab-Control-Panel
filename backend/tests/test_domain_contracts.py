from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain import (
    CandidateVersion,
    DatasetVersion,
    EvaluationResult,
    ExecutionRun,
    Experiment,
    PolicyDecision,
    Project,
    RunStatus,
    RunUsage,
    TestCase as DomainTestCase,
    Verdict,
    WorkloadType,
    assert_run_transition,
)
from app.domain.provenance import content_fingerprint

NOW = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)


def case(case_id: str = "case-1") -> DomainTestCase:
    return DomainTestCase(id=case_id, input={"prompt": "Olá"}, expected={"intent": "greeting"})


def run(**changes) -> ExecutionRun:
    data = dict(
        id="run-1", experiment_id="exp-1", test_case_id="case-1", candidate_id="candidate-1",
        workload=WorkloadType.RESPONSE,
    )
    data.update(changes)
    return ExecutionRun(**data)


def test_dataset_hash_deterministic_and_sensitive_to_inputs():
    a = DatasetVersion(id="dv-1", dataset_id="dataset", version="v1", cases=(case(),))
    b = DatasetVersion(id="dv-1", dataset_id="dataset", version="v1", cases=(case(),))
    c = DatasetVersion(id="dv-2", dataset_id="dataset", version="v2", cases=(case(),))
    assert a.fingerprint == b.fingerprint
    assert a.fingerprint != c.fingerprint
    assert len(a.fingerprint) == 64
    assert content_fingerprint({"a": 1, "b": 2}) == content_fingerprint({"b": 2, "a": 1})


def test_dataset_rejects_duplicate_cases_and_empty_dataset():
    with pytest.raises(ValidationError, match="unique"):
        DatasetVersion(id="dv", dataset_id="d", version="v1", cases=(case(), case()))
    with pytest.raises(ValidationError):
        DatasetVersion(id="dv", dataset_id="d", version="v1", cases=())


def test_candidate_fingerprint_tracks_spec_and_configuration():
    base = dict(id="candidate", version="v1", workload=WorkloadType.CODE, model_id="test/model")
    a = CandidateVersion(**base, config={"temperature": 0})
    b = CandidateVersion(**base, config={"temperature": 1})
    c = CandidateVersion(**base, config={"temperature": 0}, spec_sha256="b" * 64)
    assert len({a.fingerprint, b.fingerprint, c.fingerprint}) == 3
    with pytest.raises(ValidationError):
        CandidateVersion(**base, spec_sha256="invalid")


def test_experiment_requires_distinct_candidates():
    valid = dict(id="exp", project_id="project", dataset_version_id="dv", baseline_candidate_id="base", hypothesis="testar spec")
    assert Experiment(**valid, candidate_ids=("v2",)).baseline_candidate_id == "base"
    with pytest.raises(ValidationError, match="baseline"):
        Experiment(**valid, candidate_ids=("base",))
    with pytest.raises(ValidationError, match="unique"):
        Experiment(**valid, candidate_ids=("v2", "v2"))


def test_project_slug_and_contract_forbid_unknown_fields():
    assert Project(id="p1", slug="lab-control", name="Lab Control").slug == "lab-control"
    with pytest.raises(ValidationError):
        Project(id="p1", slug="Lab Control", name="Lab Control")
    with pytest.raises(ValidationError):
        Project(id="p1", slug="lab", name="Lab", secret="oops")


def test_valid_status_transitions():
    for source, target in [
        (RunStatus.QUEUED, RunStatus.RUNNING),
        (RunStatus.QUEUED, RunStatus.CANCELLED),
        (RunStatus.RUNNING, RunStatus.COMPLETED),
        (RunStatus.RUNNING, RunStatus.FAILED),
    ]:
        assert_run_transition(source, target)


@pytest.mark.parametrize("source,target", [
    (RunStatus.QUEUED, RunStatus.COMPLETED),
    (RunStatus.QUEUED, RunStatus.QUEUED),
    (RunStatus.COMPLETED, RunStatus.RUNNING),
    (RunStatus.CANCELLED, RunStatus.RUNNING),
    (RunStatus.FAILED, RunStatus.COMPLETED),
])
def test_reject_invalid_status_transition(source, target):
    with pytest.raises(ValueError, match="invalid run status transition"):
        assert_run_transition(source, target)


def test_run_timing_invariants():
    assert run().status is RunStatus.QUEUED
    assert run(status=RunStatus.RUNNING, started_at=NOW).started_at == NOW
    assert run(status=RunStatus.COMPLETED, started_at=NOW, finished_at=NOW + timedelta(seconds=1)).status is RunStatus.COMPLETED
    with pytest.raises(ValidationError, match="requires started_at"):
        run(status=RunStatus.RUNNING)
    with pytest.raises(ValidationError, match="timezone"):
        run(status=RunStatus.RUNNING, started_at=datetime(2026, 11, 10))
    with pytest.raises(ValidationError, match="precede"):
        run(status=RunStatus.COMPLETED, started_at=NOW, finished_at=NOW - timedelta(seconds=1))
    with pytest.raises(ValidationError, match="cannot have timestamps"):
        run(started_at=NOW)
    assert run(status=RunStatus.CANCELLED, finished_at=NOW).started_at is None


def test_usage_keeps_missing_values_distinct_from_zero():
    assert RunUsage().input_tokens is None
    usage = RunUsage(input_tokens=0, output_tokens=10, cost_usd_estimated=Decimal("0.01"))
    assert usage.input_tokens == 0
    with pytest.raises(ValidationError):
        RunUsage(input_tokens=-1)


def test_fail_closed_for_evaluation():
    with pytest.raises(ValidationError, match="critical failures"):
        EvaluationResult(id="ev", run_id="run", evaluator_id="pytest", verdict=Verdict.PASS, evidence_refs=("artifact",), critical_failures=1)
    with pytest.raises(ValidationError, match="requires evidence"):
        EvaluationResult(id="ev", run_id="run", evaluator_id="pytest", verdict=Verdict.PASS)
    assert EvaluationResult(id="ev", run_id="run", evaluator_id="pytest", verdict=Verdict.INCONCLUSIVE).verdict is Verdict.INCONCLUSIVE


def test_fail_closed_for_policy_decision():
    base = dict(id="pd", policy_version_id="p1", subject_id="candidate", reason="tests passed")
    with pytest.raises(ValidationError, match="requires evaluation"):
        PolicyDecision(**base, verdict=Verdict.PASS)
    with pytest.raises(ValidationError, match="critical failures"):
        PolicyDecision(**base, verdict=Verdict.PASS, evaluation_ids=("ev",), evidence_refs=("artifact",), critical_failures=1)
    assert PolicyDecision(**base, verdict=Verdict.PASS, evaluation_ids=("ev",), evidence_refs=("artifact",)).verdict is Verdict.PASS


def test_contract_models_prevent_field_replacement():
    project = Project(id="p", slug="project", name="Project")
    with pytest.raises(ValidationError, match="frozen"):
        project.slug = "other"
