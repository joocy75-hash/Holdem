"""Add indexes for user activity queries

Revision ID: 003_add_activity_indexes
Revises: 002_add_deposit_requests
Create Date: 2026-01-19

인덱스 추가:
- login_history(user_id, created_at DESC): 로그인 기록 조회 최적화
- transactions(user_id, created_at DESC): 거래 내역 조회 최적화
- hand_participants(user_id, created_at DESC): 핸드 기록 조회 최적화
- bans(user_id, created_at DESC): 제재 기록 조회 최적화
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_add_activity_indexes'
down_revision: Union[str, None] = '002_add_deposit_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """인덱스 추가"""
    # login_history 테이블 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_login_history_user_created
        ON login_history(user_id, created_at DESC);
    """)
    
    # transactions 테이블 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_user_created
        ON transactions(user_id, created_at DESC);
    """)
    
    # hand_participants 테이블 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hand_participants_user_created
        ON hand_participants(user_id, created_at DESC);
    """)
    
    # bans 테이블 인덱스 (admin_db에 있으므로 별도 마이그레이션 필요 시 주석 해제)
    # op.execute("""
    #     CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bans_user_created
    #     ON bans(user_id, created_at DESC);
    # """)
    
    # 복합 인덱스: 상태 필터 + 페이지네이션
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_banned_created
        ON users(is_banned, created_at DESC);
    """)


def downgrade() -> None:
    """인덱스 삭제"""
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_login_history_user_created;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_transactions_user_created;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_hand_participants_user_created;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_users_banned_created;")
