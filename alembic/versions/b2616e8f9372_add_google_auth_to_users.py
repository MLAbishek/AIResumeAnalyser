"""add google auth to users (google_sub, auth_provider, nullable password)

Revision ID: b2616e8f9372
Revises: 9b4f2a7c1d08
Create Date: 2026-08-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2616e8f9372'
down_revision: Union[str, Sequence[str], None] = '9b4f2a7c1d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Password accounts keep password_hash set; Google-only accounts
    # (auth_provider="google") never get one.
    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=True,
    )

    op.add_column(
        'users',
        sa.Column(
            'google_sub',
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.create_index(
        op.f('ix_users_google_sub'),
        'users',
        ['google_sub'],
        unique=True,
    )

    op.add_column(
        'users',
        sa.Column(
            'auth_provider',
            sa.String(length=20),
            server_default='password',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('users', 'auth_provider')

    op.drop_index(
        op.f('ix_users_google_sub'),
        table_name='users',
    )
    op.drop_column('users', 'google_sub')

    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=False,
    )
