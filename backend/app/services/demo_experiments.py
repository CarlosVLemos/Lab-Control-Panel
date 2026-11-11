"""Persistence-backed API service for the deterministic Response demo."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db import schema
from app.demo.response_fixture import (
    BASELINE, CANDIDATE, DATASET_ID, DATASET_VERSION, EXPERIMENT_ID, RESPONSE_CASES,
)
from app.domain import (
    CandidateVersion, DatasetVersion, EvaluationResult, ExecutionRun, Experiment,
    Project, RunStatus, RunUsage, TestCase, Verdict, WorkloadType,
)
from app.evaluation.response import build_response_report
from app.repositories.persistence import InvalidReference, Repositories, unit_of_work

PROJECT_ID = "demo-project"
DATASET_VERSION_ID = "demo-support-intents-v1"
BASELINE_VERSION_ID = "demo-baseline-v1"
CANDIDATE_VERSION_ID = "demo-candidate-v2"
_OUTPUT_REF = "synthetic-output:"


class DemoNotFound(ValueError):
    pass


def _run_id(candidate_id: str, case_id: str) -> str:
    return f"{EXPERIMENT_ID}:{candidate_id}:{case_id}"


def _output_ref(label: str) -> str:
    return f"{_OUTPUT_REF}{label}"


def _saved_output(artifact_refs: list[str]) -> dict[str, str]:
    for ref in artifact_refs:
        if ref.startswith(_OUTPUT_REF):
            return {"label": ref.removeprefix(_OUTPUT_REF)}
    raise RuntimeError("Persisted demo run has no synthetic output reference")


def _fixture_report() -> dict:
    """Execute the controlled fixture once, before its observed outputs are stored."""
    return build_response_report(
        experiment_id=EXPERIMENT_ID,
        dataset_id=DATASET_ID,
        dataset_version=DATASET_VERSION,
        baseline=BASELINE,
        candidate=CANDIDATE,
        cases=RESPONSE_CASES,
    )


def _exists(repo, experiment_id: str) -> bool:
    try:
        repo.get_experiment(experiment_id)
    except InvalidReference:
        return False
    return True


def create_demo_experiment(session_factory) -> dict:
    """Persist one semantic demo execution atomically, returning the stored report.

    The stable experiment ID makes repeated POSTs idempotent; it never overwrites
    previous rows. GET reconstruction below intentionally does not call adapters.
    """
    with unit_of_work(session_factory) as repo:
        if _exists(repo, EXPERIMENT_ID):
            return load_demo_experiment(session_factory, EXPERIMENT_ID)

        report = _fixture_report()
        project = Project(id=PROJECT_ID, slug="lcp-demo", name="LCP deterministic demo")
        dataset = DatasetVersion(
            id=DATASET_VERSION_ID, dataset_id=DATASET_ID, version=DATASET_VERSION,
            cases=tuple(TestCase(id=case.id, input=case.input_json(), expected=case.expected_json())
                        for case in RESPONSE_CASES),
        )
        baseline = CandidateVersion(
            id=BASELINE_VERSION_ID, model_id=BASELINE.id, version="v1",
            workload=WorkloadType.RESPONSE,
            config={"adapter": "deterministic-synthetic", "display_label": BASELINE.label},
        )
        candidate = CandidateVersion(
            id=CANDIDATE_VERSION_ID, model_id=CANDIDATE.id, version="v2",
            workload=WorkloadType.RESPONSE,
            config={"adapter": "deterministic-synthetic", "display_label": CANDIDATE.label},
        )
        experiment = Experiment(
            id=EXPERIMENT_ID, project_id=project.id, dataset_version_id=dataset.id,
            baseline_candidate_id=baseline.id, candidate_ids=(candidate.id,),
            hypothesis="The deterministic candidate recognizes all six synthetic intents",
        )
        repo.create_project(project)
        repo.create_dataset_version(project.id, dataset, fingerprint=dataset.fingerprint)
        repo.create_candidate_version(project.id, baseline, fingerprint=baseline.fingerprint)
        repo.create_candidate_version(project.id, candidate, fingerprint=candidate.fingerprint)
        repo.create_experiment(experiment)

        observed_at = datetime.now(timezone.utc)
        for case in report["cases"]:
            for candidate_version, key in ((baseline, "baseline"), (candidate, "candidate")):
                result = case[key]
                run = ExecutionRun(
                    id=_run_id(candidate_version.id, case["id"]), experiment_id=experiment.id,
                    candidate_id=candidate_version.id, test_case_id=case["id"],
                    workload=WorkloadType.RESPONSE,
                )
                repo.create_run(run)
                revision = repo.transition_run(
                    run.id, RunStatus.QUEUED, 0, RunStatus.RUNNING, started_at=observed_at,
                )
                repo.transition_run(
                    run.id, RunStatus.RUNNING, revision, RunStatus.COMPLETED,
                    finished_at=observed_at,
                    artifact_refs=(_output_ref(result["output"].get("label", "unavailable")),),
                    usage=RunUsage(input_tokens=0, output_tokens=0, duration_ms=0,
                                   cost_usd_estimated=Decimal("0")),
                )
                repo.create_evaluation(EvaluationResult(
                    id=f"evaluation:{run.id}", run_id=run.id,
                    evaluator_id="synthetic-exact-label-v1",
                    verdict=Verdict.PASS if result["passed"] else Verdict.FAIL,
                    evidence_refs=(f"synthetic-ground-truth:{case['id']}:{case['expected']['label']}",),
                    metrics={"exact_label_match": Decimal(int(result["passed"]))},
                ))

    return load_demo_experiment(session_factory, EXPERIMENT_ID)


def load_demo_experiment(session_factory, experiment_id: str) -> dict:
    """Rebuild the API DTO solely from snapshots and observed persisted results."""
    with session_factory() as session:
        repo = Repositories(session)
        try:
            experiment = repo.get_experiment(experiment_id)
            dataset = repo.get_dataset_version(experiment.dataset_version_id)
            baseline = repo.get_candidate_version(experiment.baseline_candidate_id)
            candidate = repo.get_candidate_version(experiment.candidate_ids[0])
        except InvalidReference as exc:
            raise DemoNotFound(experiment_id) from exc
        rows = session.execute(select(schema.execution_runs).where(
            schema.execution_runs.c.experiment_id == experiment_id,
            schema.execution_runs.c.status == RunStatus.COMPLETED,
        )).mappings().all()

    by_case_candidate = {(row["test_case_id"], row["candidate_id"]): row for row in rows}
    cases = []
    for item in dataset.cases:
        baseline_run = by_case_candidate.get((item.id, baseline.id))
        candidate_run = by_case_candidate.get((item.id, candidate.id))
        if baseline_run is None or candidate_run is None:
            raise RuntimeError("Persisted demo experiment is incomplete")
        baseline_output = _saved_output(list(baseline_run["artifact_refs"]))
        candidate_output = _saved_output(list(candidate_run["artifact_refs"]))
        cases.append({
            "id": item.id, "input": item.input, "expected": item.expected,
            "baseline": {"output": baseline_output, "passed": baseline_output == item.expected},
            "candidate": {"output": candidate_output, "passed": candidate_output == item.expected},
        })
    return {
        "experimentId": experiment.id, "synthetic": True,
        "dataset": {"id": dataset.dataset_id, "version": dataset.version},
        "baseline": {"id": baseline.model_id, "label": baseline.config["display_label"]},
        "candidate": {"id": candidate.model_id, "label": candidate.config["display_label"]},
        "summary": {
            "baseline": {"passed": sum(case["baseline"]["passed"] for case in cases), "total": len(cases)},
            "candidate": {"passed": sum(case["candidate"]["passed"] for case in cases), "total": len(cases)},
        },
        "cases": cases,
    }
