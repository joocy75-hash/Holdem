"""Add deposit_requests table for TON/USDT deposits

Revision ID: 002
Revises: 001
Create Date: 2026-01-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create deposit status enum
    op.execute(
        "CREATE TYPE depositrequeststatus AS ENUM ('pending', 'confirmed', 'expired', 'cancelled')"
    )

    # Create deposit_requests table
    op.create_table(
        "deposit_requests",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("requested_krw", sa.BigInteger(), nullable=False),
        sa.Column("calculated_usdt", sa.Numeric(20, 6), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("memo", sa.String(100), nullable=False),
        sa.Column("qr_data", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "confirmed", "expired", "cancelled",
                name="depositrequeststatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tx_hash", sa.String(66), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("memo"),
    )

    # Create indexes
    op.create_index("ix_deposit_requests_user_id", "deposit_requests", ["user_id"])
    op.create_index("ix_deposit_requests_memo", "deposit_requests", ["memo"], unique=True)
    op.create_index(
        "ix_deposit_requests_status_expires",
        "deposit_requests",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_deposit_requests_status_expires", table_name="deposit_requests")
    op.drop_index("ix_deposit_requests_memo", table_name="deposit_requests")
    op.drop_index("ix_deposit_requests_user_id", table_name="deposit_requests")

    # Drop table
    op.drop_table("deposit_requests")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS depositrequeststatus")
