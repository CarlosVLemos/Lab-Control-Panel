"""SQLAlchemy Core tables for the persistence adapter."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData(naming_convention={
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
})

WORKLOADS = "workload IN ('RESPONSE', 'TASK', 'CODE')"
VERDICTS = "verdict IN ('PASS', 'FAIL', 'INCONCLUSIVE', 'MANUAL_REVIEW')"


def table(name, *columns):
    return sa.Table(
        name, metadata,
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *columns,
    )


def required(name, kind=sa.Text):
    return sa.Column(name, kind, nullable=False)


def reference(name, target):
    return sa.Column(name, sa.Text, sa.ForeignKey(f"{target}.id", ondelete="RESTRICT"), nullable=False)


def check(name, expression):
    return sa.CheckConstraint(expression, name=name)


projects = table("projects", required("slug"), required("name"), sa.UniqueConstraint("slug"))
dataset_versions = table(
    "dataset_versions", reference("project_id", "projects"), required("dataset_id"),
    required("version"), required("cases", JSONB), required("canonical_payload"), required("fingerprint"),
    sa.UniqueConstraint("project_id", "dataset_id", "version"),
    check("cases", "jsonb_typeof(cases) = 'array' AND jsonb_array_length(cases) > 0"),
    check("fingerprint", "fingerprint ~ '^[0-9a-f]{64}$'"),
)
candidate_versions = table(
    "candidate_versions", reference("project_id", "projects"), required("model_id"),
    required("version"), required("workload"), required("config", JSONB),
    sa.Column("spec_sha256", sa.Text), sa.Column("source_commit", sa.Text), required("canonical_payload"), required("fingerprint"),
    sa.UniqueConstraint("project_id", "model_id", "version"),
    check("workload", WORKLOADS), check("fingerprint", "fingerprint ~ '^[0-9a-f]{64}$'"),
)
experiments = table(
    "experiments", reference("project_id", "projects"),
    reference("dataset_version_id", "dataset_versions"),
    reference("baseline_candidate_id", "candidate_versions"),
    required("candidate_ids", JSONB), required("hypothesis"),
)
execution_runs = table(
    "execution_runs", reference("experiment_id", "experiments"),
    reference("candidate_id", "candidate_versions"), required("test_case_id"),
    required("workload"), required("status"),
    sa.Column("started_at", sa.DateTime(timezone=True)),
    sa.Column("finished_at", sa.DateTime(timezone=True)),
    sa.Column("trace_id", sa.Text), required("artifact_refs", JSONB),
    sa.Column("input_tokens", sa.BigInteger), sa.Column("output_tokens", sa.BigInteger),
    sa.Column("duration_ms", sa.BigInteger), sa.Column("cost_usd_estimated", sa.Numeric),
    sa.Column("revision", sa.Integer, nullable=False, server_default="0"),
    check("workload", WORKLOADS),
    check("status_times", """
        (status = 'QUEUED' AND started_at IS NULL AND finished_at IS NULL) OR
        (status = 'RUNNING' AND started_at IS NOT NULL AND finished_at IS NULL) OR
        (status = 'COMPLETED' AND started_at IS NOT NULL AND finished_at IS NOT NULL) OR
        (status IN ('FAILED', 'CANCELLED') AND finished_at IS NOT NULL)
    """),
    check("time_order", "finished_at >= started_at"),
    check("usage", "input_tokens >= 0 AND output_tokens >= 0 AND duration_ms >= 0"),
    check("cost", "cost_usd_estimated >= 0 AND cost_usd_estimated < 'Infinity'::numeric"),
    check("revision", "revision >= 0"),
)
evaluation_results = table(
    "evaluation_results", reference("run_id", "execution_runs"), required("evaluator_id"),
    required("verdict"), required("evidence_refs", JSONB), required("metrics", JSONB),
    required("critical_failures", sa.Integer), check("verdict", VERDICTS),
    check("critical_failures", "critical_failures >= 0"),
)
policy_decisions = table(
    "policy_decisions", reference("subject_id", "candidate_versions"),
    required("policy_version_id"), required("verdict"), required("evaluation_ids", JSONB),
    required("evidence_refs", JSONB), required("reason"), required("critical_failures", sa.Integer),
    check("verdict", VERDICTS), check("critical_failures", "critical_failures >= 0"),
)
