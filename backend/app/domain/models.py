"""Versioned, framework-independent contracts for the MVP.

These are transport/domain value objects, not database entities. Persisted versions
must be append-only; Pydantic's frozen=True prevents field replacement, but does
not deep-freeze arbitrary JSON dictionaries.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field, model_validator

from .provenance import content_fingerprint

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
JsonObject = dict[str, Any]


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class WorkloadType(StrEnum):
    RESPONSE = "RESPONSE"
    TASK = "TASK"
    CODE = "CODE"


class RunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


_ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.QUEUED: frozenset({RunStatus.RUNNING, RunStatus.FAILED, RunStatus.CANCELLED}),
    RunStatus.RUNNING: frozenset({RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}),
    RunStatus.COMPLETED: frozenset(),
    RunStatus.FAILED: frozenset(),
    RunStatus.CANCELLED: frozenset(),
}


def assert_run_transition(current: RunStatus, target: RunStatus) -> None:
    """Reject invalid or repeated run-state transitions; storage handles concurrency."""
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid run status transition: {current} -> {target}")


def _aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


class Project(Contract):
    id: Identifier
    slug: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    name: Identifier


class TestCase(Contract):
    id: Identifier
    input: JsonObject
    expected: JsonObject
    tags: tuple[Identifier, ...] = ()


class DatasetVersion(Contract):
    id: Identifier
    dataset_id: Identifier
    version: Identifier
    cases: tuple[TestCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cases(self) -> DatasetVersion:
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("dataset case IDs must be unique")
        return self

    @computed_field
    @property
    def fingerprint(self) -> str:
        return content_fingerprint({
            "dataset_id": self.dataset_id,
            "version": self.version,
            "cases": [case.model_dump(mode="json") for case in self.cases],
        })


class CandidateVersion(Contract):
    id: Identifier
    version: Identifier
    workload: WorkloadType
    model_id: Identifier
    config: JsonObject = Field(default_factory=dict)
    spec_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{7,40}$")

    @computed_field
    @property
    def fingerprint(self) -> str:
        return content_fingerprint(self.model_dump(mode="json", exclude={"fingerprint"}))


class Experiment(Contract):
    id: Identifier
    project_id: Identifier
    dataset_version_id: Identifier
    baseline_candidate_id: Identifier
    candidate_ids: tuple[Identifier, ...] = Field(min_length=1)
    hypothesis: Identifier

    @model_validator(mode="after")
    def validate_candidates(self) -> Experiment:
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate IDs must be unique")
        if self.baseline_candidate_id in self.candidate_ids:
            raise ValueError("baseline must not appear in candidate IDs")
        return self


class RunUsage(Contract):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd_estimated: Decimal | None = Field(default=None, ge=0)
    duration_ms: int | None = Field(default=None, ge=0)


class ExecutionRun(Contract):
    id: Identifier
    experiment_id: Identifier
    test_case_id: Identifier
    candidate_id: Identifier
    workload: WorkloadType
    status: RunStatus = RunStatus.QUEUED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    trace_id: Identifier | None = None
    artifact_refs: tuple[Identifier, ...] = ()
    usage: RunUsage = Field(default_factory=RunUsage)

    @model_validator(mode="after")
    def validate_timing(self) -> ExecutionRun:
        for field_name, timestamp in (("started_at", self.started_at), ("finished_at", self.finished_at)):
            if timestamp is not None and not _aware(timestamp):
                raise ValueError(f"{field_name} must include a timezone")
        if self.status is RunStatus.QUEUED and (self.started_at or self.finished_at):
            raise ValueError("QUEUED runs cannot have timestamps")
        if self.status is RunStatus.RUNNING and (not self.started_at or self.finished_at):
            raise ValueError("RUNNING requires started_at and forbids finished_at")
        if self.status in (RunStatus.COMPLETED, RunStatus.FAILED) and not self.finished_at:
            raise ValueError("terminal runs require finished_at")
        if self.status is RunStatus.COMPLETED and not self.started_at:
            raise ValueError("COMPLETED runs require started_at")
        if self.status is RunStatus.CANCELLED and not self.finished_at:
            raise ValueError("CANCELLED runs require finished_at")
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        return self


class EvaluationResult(Contract):
    id: Identifier
    run_id: Identifier
    evaluator_id: Identifier
    verdict: Verdict
    evidence_refs: tuple[Identifier, ...] = ()
    critical_failures: int = Field(default=0, ge=0)
    metrics: dict[str, Decimal] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_evaluation(self) -> EvaluationResult:
        if self.verdict is Verdict.PASS and self.critical_failures:
            raise ValueError("critical failures cannot produce PASS")
        if self.verdict is Verdict.PASS and not self.evidence_refs:
            raise ValueError("PASS requires evidence")
        return self


class PolicyDecision(Contract):
    id: Identifier
    policy_version_id: Identifier
    subject_id: Identifier
    verdict: Verdict
    evaluation_ids: tuple[Identifier, ...] = ()
    evidence_refs: tuple[Identifier, ...] = ()
    reason: Identifier
    critical_failures: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_decision(self) -> PolicyDecision:
        if self.verdict is Verdict.PASS and self.critical_failures:
            raise ValueError("critical failures cannot produce PASS")
        if self.verdict is Verdict.PASS and (not self.evidence_refs or not self.evaluation_ids):
            raise ValueError("PASS requires evaluation IDs and evidence")
        return self
