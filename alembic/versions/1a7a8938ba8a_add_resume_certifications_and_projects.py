"""add resume certifications column and resume_projects table

Revision ID: 1a7a8938ba8a
Revises: b2616e8f9372
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1a7a8938ba8a'
down_revision: Union[str, Sequence[str], None] = 'b2616e8f9372'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Certifications are a simple list of strings, matching the
    # existing pattern already used for skills/job_titles/
    # organizations/technologies on this same table.
    op.add_column(
        'resumes',
        sa.Column(
            'certifications',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=False,
        ),
    )

    # Projects have multiple structured sub-fields (name,
    # description, technologies), so - consistent with how
    # experience/education are already modeled - they get their own
    # related table rather than a flat JSON column.
    op.create_table(
        'resume_projects',
        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'technologies',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['resume_id'],
            ['resumes.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_resume_projects_resume_id'),
        'resume_projects',
        ['resume_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_resume_projects_resume_id'),
        table_name='resume_projects',
    )
    op.drop_table('resume_projects')

    op.drop_column('resumes', 'certifications')
