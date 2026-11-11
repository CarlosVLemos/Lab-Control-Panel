"""initial persistence"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('projects',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
        sa.UniqueConstraint('slug', name=op.f('uq_projects_slug'))
    )
    op.create_table('candidate_versions',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', sa.Text(), nullable=False),
        sa.Column('model_id', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.Column('workload', sa.Text(), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('spec_sha256', sa.Text(), nullable=True),
        sa.Column('source_commit', sa.Text(), nullable=True),
        sa.Column('canonical_payload', sa.Text(), nullable=False),
        sa.Column('fingerprint', sa.Text(), nullable=False),
        sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_candidate_versions_fingerprint')),
        sa.CheckConstraint("workload IN ('RESPONSE', 'TASK', 'CODE')", name=op.f('ck_candidate_versions_workload')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_candidate_versions_project_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_candidate_versions')),
        sa.UniqueConstraint('project_id', 'model_id', 'version', name=op.f('uq_candidate_versions_project_id'))
    )
    op.create_table('dataset_versions',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', sa.Text(), nullable=False),
        sa.Column('dataset_id', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.Column('cases', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('canonical_payload', sa.Text(), nullable=False),
        sa.Column('fingerprint', sa.Text(), nullable=False),
        sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_dataset_versions_fingerprint')),
        sa.CheckConstraint("jsonb_typeof(cases) = 'array' AND jsonb_array_length(cases) > 0", name=op.f('ck_dataset_versions_cases')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_dataset_versions_project_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_dataset_versions')),
        sa.UniqueConstraint('project_id', 'dataset_id', 'version', name=op.f('uq_dataset_versions_project_id'))
    )
    op.create_table('experiments',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('project_id', sa.Text(), nullable=False),
        sa.Column('dataset_version_id', sa.Text(), nullable=False),
        sa.Column('baseline_candidate_id', sa.Text(), nullable=False),
        sa.Column('candidate_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['baseline_candidate_id'], ['candidate_versions.id'], name=op.f('fk_experiments_baseline_candidate_id'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], name=op.f('fk_experiments_dataset_version_id'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_experiments_project_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_experiments'))
    )
    op.create_table('policy_decisions',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('subject_id', sa.Text(), nullable=False),
        sa.Column('policy_version_id', sa.Text(), nullable=False),
        sa.Column('verdict', sa.Text(), nullable=False),
        sa.Column('evaluation_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('critical_failures', sa.Integer(), nullable=False),
        sa.CheckConstraint("verdict IN ('PASS', 'FAIL', 'INCONCLUSIVE', 'MANUAL_REVIEW')", name=op.f('ck_policy_decisions_verdict')),
        sa.CheckConstraint('critical_failures >= 0', name=op.f('ck_policy_decisions_critical_failures')),
        sa.ForeignKeyConstraint(['subject_id'], ['candidate_versions.id'], name=op.f('fk_policy_decisions_subject_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_policy_decisions'))
    )
    op.create_table('execution_runs',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('experiment_id', sa.Text(), nullable=False),
        sa.Column('candidate_id', sa.Text(), nullable=False),
        sa.Column('test_case_id', sa.Text(), nullable=False),
        sa.Column('workload', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trace_id', sa.Text(), nullable=True),
        sa.Column('artifact_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('input_tokens', sa.BigInteger(), nullable=True),
        sa.Column('output_tokens', sa.BigInteger(), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('cost_usd_estimated', sa.Numeric(), nullable=True),
        sa.Column('revision', sa.Integer(), server_default='0', nullable=False),
        sa.CheckConstraint("\n        (status = 'QUEUED' AND started_at IS NULL AND finished_at IS NULL) OR\n        (status = 'RUNNING' AND started_at IS NOT NULL AND finished_at IS NULL) OR\n        (status = 'COMPLETED' AND started_at IS NOT NULL AND finished_at IS NOT NULL) OR\n        (status IN ('FAILED', 'CANCELLED') AND finished_at IS NOT NULL)\n    ", name=op.f('ck_execution_runs_status_times')),
        sa.CheckConstraint("cost_usd_estimated >= 0 AND cost_usd_estimated < 'Infinity'::numeric", name=op.f('ck_execution_runs_cost')),
        sa.CheckConstraint("workload IN ('RESPONSE', 'TASK', 'CODE')", name=op.f('ck_execution_runs_workload')),
        sa.CheckConstraint('finished_at >= started_at', name=op.f('ck_execution_runs_time_order')),
        sa.CheckConstraint('input_tokens >= 0 AND output_tokens >= 0 AND duration_ms >= 0', name=op.f('ck_execution_runs_usage')),
        sa.CheckConstraint('revision >= 0', name=op.f('ck_execution_runs_revision')),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidate_versions.id'], name=op.f('fk_execution_runs_candidate_id'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], name=op.f('fk_execution_runs_experiment_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_execution_runs'))
    )
    op.create_table('evaluation_results',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('run_id', sa.Text(), nullable=False),
        sa.Column('evaluator_id', sa.Text(), nullable=False),
        sa.Column('verdict', sa.Text(), nullable=False),
        sa.Column('evidence_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('critical_failures', sa.Integer(), nullable=False),
        sa.CheckConstraint("verdict IN ('PASS', 'FAIL', 'INCONCLUSIVE', 'MANUAL_REVIEW')", name=op.f('ck_evaluation_results_verdict')),
        sa.CheckConstraint('critical_failures >= 0', name=op.f('ck_evaluation_results_critical_failures')),
        sa.ForeignKeyConstraint(['run_id'], ['execution_runs.id'], name=op.f('fk_evaluation_results_run_id'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_evaluation_results'))
    )


def downgrade():
    op.drop_table('evaluation_results')
    op.drop_table('execution_runs')
    op.drop_table('policy_decisions')
    op.drop_table('experiments')
    op.drop_table('dataset_versions')
    op.drop_table('candidate_versions')
    op.drop_table('projects')
