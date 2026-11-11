"""Transactional persistence for the LCP-001 value objects."""

import json
import math
from contextlib import contextmanager

from pydantic import ValidationError
from sqlalchemy import cast, insert, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DataError, IntegrityError, StatementError

from app.db import schema
from app.domain import (
    CandidateVersion, DatasetVersion, EvaluationResult, ExecutionRun, Experiment,
    PolicyDecision, Project, RunStatus, assert_run_transition,
)


class PersistenceError(ValueError):
    pass


class InvalidPayload(PersistenceError):
    pass


class InvalidReference(PersistenceError):
    pass


class ConstraintViolation(PersistenceError):
    pass


class SnapshotIntegrityError(PersistenceError):
    pass


class ConcurrencyConflict(PersistenceError):
    pass


@contextmanager
def unit_of_work(session_factory):
    """Commit all writes together or roll back on any exception."""
    try:
        with session_factory.begin() as session:
            yield Repositories(session)
    except IntegrityError as exc:
        raise ConstraintViolation(f"Database constraint: {exc.orig.diag.constraint_name}") from exc
    except DataError as exc:
        raise InvalidPayload("Value is outside PostgreSQL's supported range") from exc
    except StatementError as exc:
        if isinstance(exc.orig, (TypeError, ValueError, OverflowError)):
            raise InvalidPayload("Value could not be encoded for PostgreSQL") from exc
        raise


def _require_finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise InvalidPayload("Snapshot JSON cannot contain NaN or Infinity")
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite_json(key)
            _require_finite_json(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _require_finite_json(item)


class Repositories:
    def __init__(self, session):
        self._session = session

    def _insert(self, table, fields):
        self._session.execute(insert(table).values(**fields))

    def _find(self, table, record_id, *extra):
        row = self._session.execute(
            select(*table.c, *extra).where(table.c.id == record_id)
        ).mappings().one_or_none()
        if row is None:
            raise InvalidReference(f"{table.name} record {record_id!r} does not exist")
        return row

    def _get(self, table, model, record_id):
        row = self._find(table, record_id)
        return model.model_validate({key: row[key] for key in model.model_fields})

    def _create_snapshot(self, table, model_type, model, project_id, fingerprint):
        try:
            raw = model.model_dump(exclude={"fingerprint"})
            _require_finite_json(raw)
            payload = model_type.model_validate(raw)
            data = payload.model_dump(mode="json", exclude={"fingerprint"})
            canonical = json.dumps(data, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":"), allow_nan=False)
            computed = payload.fingerprint
        except (TypeError, ValueError, OverflowError) as exc:
            raise InvalidPayload("Snapshot cannot be serialized as canonical JSON") from exc
        if fingerprint is not None and fingerprint != computed:
            raise SnapshotIntegrityError("Supplied fingerprint does not match snapshot")
        self._insert(table, dict(data, project_id=project_id, fingerprint=computed,
                                 canonical_payload=canonical))

    def _get_snapshot(self, table, model_type, record_id, json_fields):
        # PostgreSQL compares the JSONB projections without a float round-trip.
        payload_json = cast(table.c.canonical_payload, JSONB)
        projections_match = [
            table.c[field] == payload_json[field] for field in json_fields
        ]
        try:
            row = self._find(table, record_id, *(expr.label(f"matches_{i}")
                                               for i, expr in enumerate(projections_match)))
        except DataError as exc:
            raise SnapshotIntegrityError("Stored snapshot is not valid PostgreSQL JSON") from exc
        try:
            model = model_type.model_validate_json(row["canonical_payload"])
            data = model.model_dump(mode="json", exclude={"fingerprint"})
            canonical = json.dumps(data, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":"), allow_nan=False)
            matches = (
                canonical == row["canonical_payload"]
                and model.fingerprint == row["fingerprint"]
                and all(row[key] == value for key, value in data.items() if key not in json_fields)
                and all(row[f"matches_{i}"] is True for i in range(len(json_fields)))
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise SnapshotIntegrityError("Invalid stored snapshot") from exc
        if not matches:
            raise SnapshotIntegrityError("Stored snapshot, projection or fingerprint differs")
        return model

    def create_project(self, project):
        self._insert(schema.projects, project.model_dump())

    def get_project(self, project_id):
        return self._get(schema.projects, Project, project_id)

    def create_dataset_version(self, project_id, dataset, *, fingerprint=None):
        self._create_snapshot(schema.dataset_versions, DatasetVersion, dataset, project_id, fingerprint)

    def get_dataset_version(self, dataset_id):
        return self._get_snapshot(schema.dataset_versions, DatasetVersion, dataset_id, ("cases",))

    def create_candidate_version(self, project_id, candidate, *, fingerprint=None):
        self._create_snapshot(schema.candidate_versions, CandidateVersion, candidate, project_id, fingerprint)

    def get_candidate_version(self, candidate_id):
        return self._get_snapshot(schema.candidate_versions, CandidateVersion, candidate_id, ("config",))

    def create_experiment(self, experiment):
        dataset = self._find(schema.dataset_versions, experiment.dataset_version_id)
        if dataset["project_id"] != experiment.project_id:
            raise InvalidReference("Dataset version belongs to another project")
        baseline = self._find(schema.candidate_versions, experiment.baseline_candidate_id)
        for candidate_id in (experiment.baseline_candidate_id, *experiment.candidate_ids):
            candidate = baseline if candidate_id == experiment.baseline_candidate_id else self._find(
                schema.candidate_versions, candidate_id
            )
            if candidate["project_id"] != experiment.project_id or candidate["workload"] != baseline["workload"]:
                raise InvalidReference("Candidate project or workload does not match experiment")
        self._insert(schema.experiments, experiment.model_dump(mode="json"))

    def get_experiment(self, experiment_id):
        return self._get(schema.experiments, Experiment, experiment_id)

    def create_run(self, run):
        if run.status is not RunStatus.QUEUED:
            raise InvalidPayload("A new run must be QUEUED")
        experiment = self.get_experiment(run.experiment_id)
        if run.candidate_id not in (experiment.baseline_candidate_id, *experiment.candidate_ids):
            raise InvalidReference("Candidate is outside experiment")
        dataset = self.get_dataset_version(experiment.dataset_version_id)
        if not any(case.id == run.test_case_id for case in dataset.cases):
            raise InvalidReference("Case is outside experiment dataset version")
        if self.get_candidate_version(run.candidate_id).workload != run.workload:
            raise InvalidReference("Run workload does not match candidate")
        self._insert(schema.execution_runs, self._run_fields(run))

    @staticmethod
    def _run_fields(run):
        fields = run.model_dump(exclude={"usage"})
        fields.update(run.usage.model_dump())
        return fields

    def get_run(self, run_id):
        """Return the domain run and the revision required for a transition."""
        row = self._find(schema.execution_runs, run_id)
        run = ExecutionRun.model_validate({
            **{key: row[key] for key in ExecutionRun.model_fields if key != "usage"},
            "usage": {key: row[key] for key in ("input_tokens", "output_tokens",
                                              "duration_ms", "cost_usd_estimated")},
        })
        return run, row["revision"]

    def transition_run(self, run_id, expected_status, expected_revision, target_status, **changes):
        expected_status = RunStatus(expected_status)
        target_status = RunStatus(target_status)
        assert_run_transition(expected_status, target_status)
        if set(changes) - {"started_at", "finished_at", "trace_id", "artifact_refs", "usage"}:
            raise InvalidPayload("Run transition contains immutable or unknown fields")
        try:
            current, revision = self.get_run(run_id)
        except InvalidReference as exc:
            raise ConcurrencyConflict("Run no longer matches the expected revision") from exc
        if current.status != expected_status or revision != expected_revision:
            raise ConcurrencyConflict("Run no longer matches the expected revision")
        if "started_at" in changes and target_status is not RunStatus.RUNNING:
            raise InvalidPayload("Only the transition to RUNNING may set started_at")
        updated = ExecutionRun.model_validate(
            {**current.model_dump(), **changes, "status": target_status}
        )
        values = self._run_fields(updated)
        for key in ("id", "experiment_id", "test_case_id", "candidate_id", "workload"):
            del values[key]
        table = schema.execution_runs
        new_revision = self._session.execute(
            update(table).where(table.c.id == run_id, table.c.status == expected_status,
                                table.c.revision == expected_revision)
            .values(**values, revision=table.c.revision + 1).returning(table.c.revision)
        ).scalar_one_or_none()
        if new_revision is None:
            raise ConcurrencyConflict("Run no longer matches the expected revision")
        return new_revision

    def create_evaluation(self, evaluation):
        try:
            evaluation = EvaluationResult.model_validate(evaluation.model_dump())
        except ValidationError as exc:
            raise InvalidPayload("Invalid evaluation or Decimal metric") from exc
        fields = evaluation.model_dump(mode="json", exclude={"metrics"})
        fields["metrics"] = {key: str(value) for key, value in evaluation.metrics.items()}
        self._insert(schema.evaluation_results, fields)

    def get_evaluation(self, evaluation_id):
        return self._get(schema.evaluation_results, EvaluationResult, evaluation_id)

    def create_decision(self, decision):
        subject = self._find(schema.candidate_versions, decision.subject_id)
        evaluation = schema.evaluation_results
        run = schema.execution_runs
        experiment = schema.experiments
        if decision.evaluation_ids:
            matching_ids = set(self._session.scalars(
                select(evaluation.c.id)
                .join(run, evaluation.c.run_id == run.c.id)
                .join(experiment, run.c.experiment_id == experiment.c.id)
                .where(evaluation.c.id.in_(decision.evaluation_ids),
                       experiment.c.project_id == subject["project_id"])
            ))
            if matching_ids != set(decision.evaluation_ids):
                raise InvalidReference("Decision references missing or cross-project evaluations")
        self._insert(schema.policy_decisions, decision.model_dump(mode="json"))

    def get_decision(self, decision_id):
        return self._get(schema.policy_decisions, PolicyDecision, decision_id)
