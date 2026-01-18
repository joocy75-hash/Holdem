"""KYC (Know Your Customer) / 성인 인증 모델.

사용자 본인 인증 및 성인 확인을 위한 데이터 모델.
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class KYCStatus(str, Enum):
    """KYC 인증 상태."""
    
    NONE = "none"           # 미인증
    PENDING = "pending"     # 검토 중
    VERIFIED = "verified"   # 인증 완료
    REJECTED = "rejected"   # 거부됨
    EXPIRED = "expired"     # 만료됨


class KYCProvider(str, Enum):
    """KYC 인증 제공자."""
    
    MANUAL = "manual"       # 수동 검토 (관리자)
    NICE = "nice"           # NICE 본인인증
    PASS = "pass"           # PASS 앱 인증
    KAKAO = "kakao"         # 카카오 인증
    TOSS = "toss"           # 토스 인증


class UserKYC(Base, UUIDMixin, TimestampMixin):
    """사용자 KYC 인증 정보.
    
    성인 인증 및 본인 확인 정보를 저장합니다.
    개인정보 보호를 위해 민감한 데이터는 해시 처리됩니다.
    """

    __tablename__ = "user_kyc"

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 사용자당 하나의 KYC 기록
        index=True,
    )

    # 인증 상태
    status: Mapped[str] = mapped_column(
        String(20),
        default=KYCStatus.NONE.value,
        nullable=False,
        index=True,
    )

    # 인증 제공자
    provider: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="KYC 인증 제공자 (nice, pass, kakao 등)",
    )

    # 본인 확인 정보 (암호화/해시 저장)
    # 실명 - 검색용으로 저장 (AES 암호화 권장)
    real_name_encrypted: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="암호화된 실명",
    )

    # 생년월일 - 성인 확인용
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="생년월일 (성인 확인용)",
    )

    # 휴대폰 번호 해시 - 중복 가입 방지용
    phone_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="휴대폰 번호 SHA-256 해시 (중복 방지)",
    )

    # CI (연계 정보) - 본인인증 고유 식별자
    ci_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
        comment="본인인증 CI 해시 (중복 계정 탐지)",
    )

    # DI (본인확인 정보) - 서비스별 고유 식별자
    di_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="본인인증 DI 해시",
    )

    # 성인 여부
    is_adult: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="만 19세 이상 성인 여부",
    )

    # 인증 일시
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="본인인증 완료 일시",
    )

    # 인증 만료일 (연 1회 재인증 권장)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="인증 만료 일시",
    )

    # 거부 사유 (거부된 경우)
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="인증 거부 사유",
    )

    # 인증 시도 횟수 (악용 방지)
    attempt_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="인증 시도 횟수",
    )

    # 마지막 시도 일시
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 검토 관리자 ID (수동 검토 시)
    reviewed_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="검토 관리자 ID",
    )

    # 관리자 메모
    admin_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="관리자 검토 메모",
    )

    # Relationship back to user
    user: Mapped["User"] = relationship("User", backref="kyc")

    def __repr__(self) -> str:
        return f"<UserKYC user={self.user_id[:8]}... status={self.status}>"

    @property
    def is_verified(self) -> bool:
        """인증 완료 여부 확인."""
        return self.status == KYCStatus.VERIFIED.value

    @property
    def is_expired(self) -> bool:
        """인증 만료 여부 확인."""
        if not self.expires_at:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def can_withdraw(self) -> bool:
        """출금 가능 여부 (KYC 인증 완료 + 성인)."""
        return self.is_verified and self.is_adult and not self.is_expired
