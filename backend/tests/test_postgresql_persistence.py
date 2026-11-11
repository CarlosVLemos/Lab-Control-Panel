import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import event, inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db import schema
from app.db.session import create_database_engine, create_session_factory, database_url
from app.domain import (
    CandidateVersion, DatasetVersion, EvaluationResult, ExecutionRun, Experiment,
    PolicyDecision, Project, RunStatus, RunUsage, TestCase as DomainCase,
)
from app.main import app
from app.repositories.persistence import (
    ConcurrencyConflict, ConstraintViolation, InvalidPayload, InvalidReference,
    SnapshotIntegrityError, unit_of_work,
)

NOW = datetime(2026, 11, 11, tzinfo=timezone.utc)


@pytest.fixture
def postgres(monkeypatch):
    raw_url = os.environ.get("LCP_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set LCP_TEST_DATABASE_URL to a disposable PostgreSQL database")
    url = database_url(raw_url)
    if not url.database or not url.database.endswith("_test"):
        pytest.fail("Integration tests require a disposable database ending in _test")
    namespace = f"lcp_{uuid4().hex}"
    admin = create_database_engine(url)
    with admin.begin() as connection:
        connection.execute(CreateSchema(namespace))
    scoped_url = url.update_query_dict({"options": f"-csearch_path={namespace}"})
    monkeypatch.setenv("DATABASE_URL", scoped_url.render_as_string(hide_password=False))
    engine = create_database_engine(scoped_url)
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
        assert inspect(engine).get_table_names() == []
        config = Config("alembic.ini")
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) == set(schema.metadata.tables) | {"alembic_version"}
        yield engine, create_session_factory(engine)
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(DropSchema(namespace, cascade=True))
        admin.dispose()


def seed(factory):
    project = Project(id="p", slug="lab", name="Lab")
    dataset = DatasetVersion(id="d", dataset_id="responses", version="v1", cases=(
        DomainCase(id="z", input={"prompt": "Olá", "number": -0.0}, expected={}),
        DomainCase(id="a", input={}, expected={}),
    ))
    baseline, challenger, extra = (
        CandidateVersion(id=name, model_id=name, version="v1", workload="RESPONSE",
                         config={"temperature": 1e-7})
        for name in ("baseline", "z-candidate", "a-candidate")
    )
    experiment = Experiment(id="exp", project_id=project.id, dataset_version_id=dataset.id,
                            baseline_candidate_id=baseline.id, candidate_ids=(challenger.id, extra.id),
                            hypothesis="Compare ordered candidates")
    run = ExecutionRun(id="run", experiment_id=experiment.id, candidate_id=challenger.id,
                       test_case_id="z", workload="RESPONSE")
    with unit_of_work(factory) as repo:
        repo.create_project(project)
        repo.create_dataset_version(project.id, dataset, fingerprint=dataset.fingerprint)
        for candidate in (baseline, challenger, extra):
            repo.create_candidate_version(project.id, candidate, fingerprint=candidate.fingerprint)
        repo.create_experiment(experiment)
        repo.create_run(run)
    return project, dataset, challenger, experiment, run


def test_roundtrip_and_snapshot_integrity(postgres):
    engine, factory = postgres
    project, dataset, candidate, experiment, run = seed(factory)
    engine.dispose()
    with unit_of_work(factory) as repo:
        assert repo.get_project(project.id) == project
        assert repo.get_dataset_version(dataset.id).fingerprint == dataset.fingerprint
        assert repo.get_candidate_version(candidate.id).fingerprint == candidate.fingerprint
        assert repo.get_experiment(experiment.id) == experiment
        assert repo.get_run(run.id) == (run, 0)
    with pytest.raises(SnapshotIntegrityError), unit_of_work(factory) as repo:
        repo.create_dataset_version(project.id, dataset, fingerprint="0" * 64)
    with engine.begin() as connection:
        connection.execute(update(schema.candidate_versions)
                           .where(schema.candidate_versions.c.id == candidate.id)
                           .values(fingerprint="0" * 64))
    with pytest.raises(SnapshotIntegrityError), unit_of_work(factory) as repo:
        repo.get_candidate_version(candidate.id)
    with engine.begin() as connection:
        connection.execute(update(schema.candidate_versions)
                           .where(schema.candidate_versions.c.id == candidate.id)
                           .values(canonical_payload="{"))
    with pytest.raises(SnapshotIntegrityError), unit_of_work(factory) as repo:
        repo.get_candidate_version(candidate.id)


def test_constraints_and_transaction_rollback(postgres):
    engine, factory = postgres
    project, dataset, candidate, experiment, run = seed(factory)
    with pytest.raises(ConstraintViolation), unit_of_work(factory) as repo:
        repo.create_project(Project(id="rollback", slug="rollback", name="Rollback"))
        repo.create_project(Project(id="duplicate", slug=project.slug, name="Duplicate"))
    with pytest.raises(InvalidReference), unit_of_work(factory) as repo:
        repo.get_project("rollback")
    with pytest.raises(ConstraintViolation), unit_of_work(factory) as repo:
        repo.create_dataset_version("missing", DatasetVersion.model_validate({
            **dataset.model_dump(exclude={"fingerprint"}), "id": "orphan",
        }))
    for column, value in (("status", "UNKNOWN"), ("workload", "UNKNOWN"),
                          ("cost_usd_estimated", Decimal("-1")),
                          ("cost_usd_estimated", Decimal("NaN")),
                          ("cost_usd_estimated", Decimal("Infinity"))):
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(update(schema.execution_runs).where(schema.execution_runs.c.id == run.id)
                               .values({column: value}))


def test_membership_and_workload(postgres):
    _, factory = postgres
    project, dataset, candidate, experiment, run = seed(factory)
    with unit_of_work(factory) as repo:
        repo.create_project(Project(id="other", slug="other", name="Other"))
        repo.create_candidate_version("other", CandidateVersion(
            id="foreign", model_id="foreign", version="v1", workload="RESPONSE"))
        repo.create_candidate_version(project.id, CandidateVersion(
            id="code", model_id="code", version="v1", workload="CODE"))
    for candidate_ids in (("foreign",), ("code",), ("missing",)):
        with pytest.raises(InvalidReference), unit_of_work(factory) as repo:
            repo.create_experiment(Experiment.model_validate({
                **experiment.model_dump(), "id": "invalid", "candidate_ids": candidate_ids,
            }))
    for changes in ({"candidate_id": "code"}, {"test_case_id": "missing"}, {"workload": "CODE"}):
        with pytest.raises(InvalidReference), unit_of_work(factory) as repo:
            repo.create_run(ExecutionRun.model_validate({
                **run.model_dump(), "id": "invalid", **changes,
            }))
    with pytest.raises(InvalidReference), unit_of_work(factory) as repo:
        repo.get_experiment("invalid")


def test_decisions_and_exact_decimals(postgres):
    engine, factory = postgres
    project, _, candidate, _, run = seed(factory)
    evaluation = EvaluationResult(id="eval", run_id=run.id, evaluator_id="rules", verdict="PASS",
                                  evidence_refs=("artifact",),
                                  metrics={"precision": Decimal("0.9500"), "loss": Decimal("1E-7")})
    decision = PolicyDecision(id="decision", subject_id=candidate.id, policy_version_id="demo-v1",
                              verdict="PASS", evidence_refs=("artifact",),
                              evaluation_ids=(evaluation.id, evaluation.id), reason="Checks passed")
    with pytest.raises(ValidationError):
        EvaluationResult.model_validate({**evaluation.model_dump(), "critical_failures": 1})
    with pytest.raises(ValidationError):
        PolicyDecision.model_validate({**decision.model_dump(), "evidence_refs": ()})
    with pytest.raises(InvalidReference), unit_of_work(factory) as repo:
        repo.create_decision(decision)
    cost = Decimal("0.12345678901234567890")
    with unit_of_work(factory) as repo:
        assert repo.get_run(run.id)[0].usage.cost_usd_estimated is None
        repo.transition_run(run.id, "QUEUED", 0, "RUNNING", started_at=NOW, usage=RunUsage(cost_usd_estimated=0))
        assert repo.get_run(run.id)[0].usage.cost_usd_estimated == Decimal(0)
        repo.transition_run(run.id, "RUNNING", 1, "COMPLETED", finished_at=NOW, usage=RunUsage(cost_usd_estimated=cost))
        repo.create_evaluation(evaluation)
        repo.create_decision(decision)
    engine.dispose()
    with unit_of_work(factory) as repo:
        assert repo.get_run(run.id)[0].usage.cost_usd_estimated == cost
        assert repo.get_evaluation(evaluation.id) == evaluation
        assert repo.get_decision(decision.id) == decision
    with engine.connect() as connection:
        assert connection.scalar(select(schema.evaluation_results.c.metrics)) == {
            "precision": "0.9500", "loss": "1E-7",
        }
    for value in ("\0", float("nan"), float("inf")):
        with pytest.raises(InvalidPayload), unit_of_work(factory) as repo:
            repo.create_candidate_version(project.id, CandidateVersion(
                id="bad", model_id="bad", version="v1", workload="RESPONSE",
                config={"nested": [value]}))


def test_concurrent_compare_and_swap(postgres):
    engine, factory = postgres
    *_, run = seed(factory)
    ready = Barrier(2)

    def before_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE execution_runs"):
            ready.wait(timeout=10)

    def transition():
        try:
            with unit_of_work(factory) as repo:
                return repo.transition_run(run.id, "QUEUED", 0, "RUNNING", started_at=NOW)
        except ConcurrencyConflict:
            return "conflict"

    event.listen(engine, "before_cursor_execute", before_execute)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            assert set(workers.map(lambda _: transition(), range(2))) == {1, "conflict"}
    finally:
        event.remove(engine, "before_cursor_execute", before_execute)
    with unit_of_work(factory) as repo:
        current, revision = repo.get_run(run.id)
        assert current.status is RunStatus.RUNNING and revision == 1
    with pytest.raises(InvalidPayload), unit_of_work(factory) as repo:
        repo.transition_run(run.id, "RUNNING", 1, "COMPLETED", started_at=None, finished_at=NOW)
