"""add_performance_indexes

Revision ID: add_perf_indexes_001
Revises: add_balance_001
Create Date: 2026-01-12

Phase 3.1: 데이터베이스 인덱스 최적화
- rooms.created_at DESC: 최근 생성 방 조회 최적화
- hands.started_at DESC: 핸드 히스토리 조회 최적화
- 복합 인덱스: 자주 사용되는 쿼리 패턴 최적화
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_perf_indexes_001'
down_revision: Union[str, Sequence[str], None] = 'add_balance_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for 300-500 concurrent users."""
    # rooms.created_at DESC - 최근 생성 방 조회 최적화
    op.create_index(
        'ix_rooms_created_at_desc',
        'rooms',
        [sa.text('created_at DESC')],
        unique=False
    )

    # hands.started_at DESC - 핸드 히스토리 조회 최적화
    op.create_index(
        'ix_hands_started_at_desc',
        'hands',
        [sa.text('started_at DESC')],
        unique=False
    )

    # 복합 인덱스: rooms(status, created_at DESC) - 활성 방 최신순 조회
    op.create_index(
        'ix_rooms_status_created_at',
        'rooms',
        ['status', sa.text('created_at DESC')],
        unique=False
    )

    # 복합 인덱스: hands(table_id, started_at DESC) - 테이블별 핸드 히스토리
    op.create_index(
        'ix_hands_table_started_at',
        'hands',
        ['table_id', sa.text('started_at DESC')],
        unique=False
    )

    # 복합 인덱스: hand_events(hand_id, seq_no) - 핸드 이벤트 순서 조회
    op.create_index(
        'ix_hand_events_hand_seq',
        'hand_events',
        ['hand_id', 'seq_no'],
        unique=False
    )

    # sessions.expires_at - 만료 세션 정리용
    op.create_index(
        'ix_sessions_expires_at',
        'sessions',
        ['expires_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('ix_sessions_expires_at', table_name='sessions')
    op.drop_index('ix_hand_events_hand_seq', table_name='hand_events')
    op.drop_index('ix_hands_table_started_at', table_name='hands')
    op.drop_index('ix_rooms_status_created_at', table_name='rooms')
    op.drop_index('ix_hands_started_at_desc', table_name='hands')
    op.drop_index('ix_rooms_created_at_desc', table_name='rooms')
