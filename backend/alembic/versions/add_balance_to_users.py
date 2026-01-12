"""Add balance field to users table.

Revision ID: add_balance_001
Revises: e32e3e696448
Create Date: 2026-01-12

Security Fix: Add user balance tracking for chip management.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_balance_001'
down_revision = 'e32e3e696448'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add balance column with default value of 10000 chips for new users
    op.add_column(
        'users',
        sa.Column('balance', sa.Integer(), nullable=False, server_default='10000')
    )

    # Update existing users to have 10000 chips
    op.execute("UPDATE users SET balance = 10000 WHERE balance IS NULL OR balance = 0")


def downgrade() -> None:
    op.drop_column('users', 'balance')
