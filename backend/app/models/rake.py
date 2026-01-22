"""Rake configuration model for dynamic rake settings.

Phase P1-1: 관리자 레이크 설정 UI
- 블라인드 레벨별 레이크 퍼센트/캡 설정
- 관리자가 실시간으로 변경 가능
"""

from decimal import Decimal

from sqlalchemy import Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class RakeConfig(Base, UUIDMixin, TimestampMixin):
    """레이크 설정 테이블.

    블라인드 레벨(SB/BB)별로 레이크 퍼센트와 캡을 설정합니다.
    DB에 설정이 없는 블라인드 레벨은 기본값(5%, 3BB)이 적용됩니다.

    Attributes:
        small_blind: 스몰 블라인드 금액 (KRW)
        big_blind: 빅 블라인드 금액 (KRW)
        percentage: 레이크 퍼센트 (0.05 = 5%)
        cap_bb: 레이크 캡 (빅 블라인드 단위)
        is_active: 활성화 여부
    """

    __tablename__ = "rake_configs"
    __table_args__ = (
        UniqueConstraint("small_blind", "big_blind", name="uq_rake_blind_level"),
    )

    small_blind: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="스몰 블라인드 금액 (KRW)",
    )
    big_blind: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="빅 블라인드 금액 (KRW)",
    )
    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),  # 최대 9.9999 (999.99%)
        nullable=False,
        default=Decimal("0.05"),
        comment="레이크 퍼센트 (0.05 = 5%)",
    )
    cap_bb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="레이크 캡 (빅 블라인드 단위)",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="활성화 여부",
    )

    def __repr__(self) -> str:
        return (
            f"<RakeConfig SB={self.small_blind} BB={self.big_blind} "
            f"{float(self.percentage)*100}% cap={self.cap_bb}BB>"
        )
