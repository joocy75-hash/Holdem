"""Add hand_participants table for fraud detection and history.

Revision ID: add_hand_participants_001
Revises: phase5_wallet_001
Create Date: 2026-01-16

This migration adds:
- hand_participants table for storing participant details per hand
- Indexes for efficient querying by hand_id and user_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_hand_participants_001"
down_revision = "phase5_wallet_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create hand_participants table."""
    op.create_table(
        "hand_participants",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "hand_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hands.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Seat position
        sa.Column("seat", sa.Integer(), nullable=False),
        # Hole cards (JSON string: '["As", "Ad"]')
        sa.Column(
            "hole_cards",
            sa.String(50),
            nullable=True,
            comment="Hole cards as JSON array string",
        ),
        # Betting amounts
        sa.Column(
            "bet_amount",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total amount bet in this hand",
        ),
        sa.Column(
            "won_amount",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Amount won in this hand",
        ),
        # Final action
        sa.Column(
            "final_action",
            sa.String(30),
            nullable=False,
            server_default="fold",
            comment="Final action: fold, showdown, all_in_won, timeout, etc.",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        comment="Hand participant details for fraud detection and history",
    )

    # Create composite index for efficient user hand history queries
    op.create_index(
        "ix_hand_participants_user_created",
        "hand_participants",
        ["user_id", "created_at"],
        postgresql_using="btree",
    )

    # Create composite index for hand + seat uniqueness check
    op.create_index(
        "ix_hand_participants_hand_seat",
        "hand_participants",
        ["hand_id", "seat"],
        unique=True,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Drop hand_participants table."""
    op.drop_index("ix_hand_participants_hand_seat", table_name="hand_participants")
    op.drop_index("ix_hand_participants_user_created", table_name="hand_participants")
    op.drop_table("hand_participants")
