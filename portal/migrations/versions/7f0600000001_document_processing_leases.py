"""Recover interrupted document work with bounded leases.

Revision: 7f0600000001
Revises: 4283578082f1
"""
from alembic import op
import sqlalchemy as sa

revision = "7f0600000001"
down_revision = "4283578082f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("processing_token", sa.String(50), server_default="", nullable=False))
    op.add_column("documents", sa.Column("processing_until", sa.Integer(), server_default="0", nullable=False))
    op.add_column("documents", sa.Column("processing_attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("workflow_runs", sa.Column("execution_token", sa.String(50), server_default="", nullable=False))
    op.add_column("workflow_runs", sa.Column("execution_until", sa.Integer(), server_default="0", nullable=False))
    op.create_index('uq_approval_run', 'approvals', ['run_id'], unique=True)


def downgrade():
    op.drop_index('uq_approval_run', table_name='approvals')
    op.drop_column('workflow_runs', 'execution_until')
    op.drop_column('workflow_runs', 'execution_token')
    for name in ["processing_attempts", "processing_until", "processing_token"]:
        op.drop_column("documents", name)
