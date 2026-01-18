"""add_user_kyc_table

Revision ID: 5601e47219d1
Revises: 1723deb5781e
Create Date: 2026-01-18 14:44:56.762231

성인 인증 / KYC 테이블 추가
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5601e47219d1'
down_revision: Union[str, Sequence[str], None] = '1723deb5781e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # user_kyc 테이블 생성
    op.create_table('user_kyc',
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=True, comment='KYC 인증 제공자 (nice, pass, kakao 등)'),
        sa.Column('real_name_encrypted', sa.String(length=256), nullable=True, comment='암호화된 실명'),
        sa.Column('birth_date', sa.Date(), nullable=True, comment='생년월일 (성인 확인용)'),
        sa.Column('phone_hash', sa.String(length=64), nullable=True, comment='휴대폰 번호 SHA-256 해시 (중복 방지)'),
        sa.Column('ci_hash', sa.String(length=128), nullable=True, comment='본인인증 CI 해시 (중복 계정 탐지)'),
        sa.Column('di_hash', sa.String(length=128), nullable=True, comment='본인인증 DI 해시'),
        sa.Column('is_adult', sa.Boolean(), nullable=False, default=False, comment='만 19세 이상 성인 여부'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True, comment='본인인증 완료 일시'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='인증 만료 일시'),
        sa.Column('rejection_reason', sa.Text(), nullable=True, comment='인증 거부 사유'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, default=0, comment='인증 시도 횟수'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True, comment='검토 관리자 ID'),
        sa.Column('admin_note', sa.Text(), nullable=True, comment='관리자 검토 메모'),
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 인덱스 생성
    op.create_index(op.f('ix_user_kyc_ci_hash'), 'user_kyc', ['ci_hash'], unique=True)
    op.create_index(op.f('ix_user_kyc_di_hash'), 'user_kyc', ['di_hash'], unique=False)
    op.create_index(op.f('ix_user_kyc_phone_hash'), 'user_kyc', ['phone_hash'], unique=False)
    op.create_index(op.f('ix_user_kyc_status'), 'user_kyc', ['status'], unique=False)
    op.create_index(op.f('ix_user_kyc_user_id'), 'user_kyc', ['user_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # 인덱스 삭제
    op.drop_index(op.f('ix_user_kyc_user_id'), table_name='user_kyc')
    op.drop_index(op.f('ix_user_kyc_status'), table_name='user_kyc')
    op.drop_index(op.f('ix_user_kyc_phone_hash'), table_name='user_kyc')
    op.drop_index(op.f('ix_user_kyc_di_hash'), table_name='user_kyc')
    op.drop_index(op.f('ix_user_kyc_ci_hash'), table_name='user_kyc')
    
    # 테이블 삭제
    op.drop_table('user_kyc')
