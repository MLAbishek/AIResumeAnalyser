"""add pipeline execution state

Revision ID: 464f8152188b
Revises: 3596cb85451b
Create Date: 2026-08-17 00:19:46.833882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '464f8152188b'
down_revision: Union[str, Sequence[str], None] = '3596cb85451b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_executions",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "execution_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "current_stage",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "total_candidates",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "completed_candidates",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "state",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_pipeline_executions_execution_id",
        "pipeline_executions",
        ["execution_id"],
        unique=True,
    )

    op.create_index(
        "ix_pipeline_executions_job_id",
        "pipeline_executions",
        ["job_id"],
        unique=False,
    )

    op.create_index(
        "ix_pipeline_executions_status",
        "pipeline_executions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pipeline_executions_status",
        table_name="pipeline_executions",
    )

    op.drop_index(
        "ix_pipeline_executions_job_id",
        table_name="pipeline_executions",
    )

    op.drop_index(
        "ix_pipeline_executions_execution_id",
        table_name="pipeline_executions",
    )

    op.drop_table(
        "pipeline_executions"
    )