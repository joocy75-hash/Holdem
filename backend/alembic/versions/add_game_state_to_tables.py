"""Add game_state field to tables.

Revision ID: add_game_state_001
Revises: add_two_factor_auth
Create Date: 2026-01-13

Adds game_state JSONB column for storing active hand state.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_game_state_001'
down_revision: Union[str, None] = 'add_two_factor_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add game_state column to tables."""
    op.add_column(
        'tables',
        sa.Column('game_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    """Remove game_state column from tables."""
    op.drop_column('tables', 'game_state')
