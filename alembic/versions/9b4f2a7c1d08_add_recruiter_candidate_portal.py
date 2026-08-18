"""add recruiter/candidate portal (job ownership, status, applications)

Revision ID: 9b4f2a7c1d08
Revises: c39e3ef8adf6
Create Date: 2026-08-18 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b4f2a7c1d08'
down_revision: Union[str, Sequence[str], None] = 'c39e3ef8adf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- jobs: ownership + lifecycle status ---
    op.add_column(
        'jobs',
        sa.Column(
            'created_by_user_id',
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f('ix_jobs_created_by_user_id'),
        'jobs',
        ['created_by_user_id'],
        unique=False,
    )
    op.create_foreign_key(
        'fk_jobs_created_by_user_id_users',
        'jobs',
        'users',
        ['created_by_user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.add_column(
        'jobs',
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='open',
            nullable=False,
        ),
    )

    # --- resumes: candidate ownership ---
    op.add_column(
        'resumes',
        sa.Column(
            'owner_user_id',
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f('ix_resumes_owner_user_id'),
        'resumes',
        ['owner_user_id'],
        unique=False,
    )
    op.create_foreign_key(
        'fk_resumes_owner_user_id_users',
        'resumes',
        'users',
        ['owner_user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # --- applications: candidate <-> job business relationship ---
    op.create_table(
        'applications',
        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column(
            'candidate_user_id',
            sa.Integer(),
            nullable=False,
        ),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column(
            'screening_id',
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            'status',
            sa.String(length=30),
            server_default='applied',
            nullable=False,
        ),
        sa.Column(
            'applied_at',
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['job_id'],
            ['jobs.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['candidate_user_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['resume_id'],
            ['resumes.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['screening_id'],
            ['screening_results.id'],
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'job_id',
            'candidate_user_id',
            name='uq_application_job_candidate',
        ),
    )
    op.create_index(
        op.f('ix_applications_job_id'),
        'applications',
        ['job_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_applications_candidate_user_id'),
        'applications',
        ['candidate_user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_applications_screening_id'),
        'applications',
        ['screening_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_applications_screening_id'),
        table_name='applications',
    )
    op.drop_index(
        op.f('ix_applications_candidate_user_id'),
        table_name='applications',
    )
    op.drop_index(
        op.f('ix_applications_job_id'),
        table_name='applications',
    )
    op.drop_table('applications')

    op.drop_constraint(
        'fk_resumes_owner_user_id_users',
        'resumes',
        type_='foreignkey',
    )
    op.drop_index(
        op.f('ix_resumes_owner_user_id'),
        table_name='resumes',
    )
    op.drop_column('resumes', 'owner_user_id')

    op.drop_column('jobs', 'status')

    op.drop_constraint(
        'fk_jobs_created_by_user_id_users',
        'jobs',
        type_='foreignkey',
    )
    op.drop_index(
        op.f('ix_jobs_created_by_user_id'),
        table_name='jobs',
    )
    op.drop_column('jobs', 'created_by_user_id')
