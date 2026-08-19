"""add job responsibilities column

Revision ID: d3d0f168238b
Revises: 1a7a8938ba8a
Create Date: 2026-08-19 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd3d0f168238b'
down_revision: Union[str, Sequence[str], None] = '1a7a8938ba8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Responsibility bullets are a simple list of strings, matching
    # the existing pattern already used for required_skills/
    # preferred_skills/etc. on this same table. The JD parser has
    # always extracted this - it was simply never persisted.
    op.add_column(
        'jobs',
        sa.Column(
            'responsibilities',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('jobs', 'responsibilities')
