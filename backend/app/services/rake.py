"""Rake Service for calculating and collecting rake from poker hands.

Phase 6.1: Rake & Economy System
Phase P1-1: 관리자 레이크 설정 UI

Features:
- Configurable rake percentages per blind level
- Rake caps per blind level
- No Flop No Drop (NFND) logic
- Proportional rake distribution among winners
- Admin API for managing rake configs (P1-1)
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rake import RakeConfig
from app.models.wallet import TransactionType
from app.services.wallet import WalletService

if TYPE_CHECKING:
    from app.engine.state import GamePhase, HandResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RakeConfigData:
    """Rake configuration data for a blind level.

    Attributes:
        percentage: Rake percentage (e.g., 0.05 = 5%)
        cap_bb: Rake cap in big blinds (e.g., 3 = 3 BB max rake)
    """
    percentage: Decimal
    cap_bb: int


# Rake configurations by blind level (small_blind, big_blind)
# Format: (small_blind, big_blind) -> RakeConfigData(percentage, cap_in_bb)
# NOTE: DB 설정이 있으면 DB 설정이 우선 적용됨
RAKE_CONFIGS: dict[tuple[int, int], RakeConfigData] = {
    # Micro stakes: 5% rake, 3 BB cap
    (500, 1000): RakeConfigData(Decimal("0.05"), 3),
    (1000, 2000): RakeConfigData(Decimal("0.05"), 3),

    # Low stakes: 5% rake, 4 BB cap
    (2500, 5000): RakeConfigData(Decimal("0.05"), 4),
    (5000, 10000): RakeConfigData(Decimal("0.05"), 4),

    # Mid stakes: 4.5% rake, 5 BB cap
    (10000, 20000): RakeConfigData(Decimal("0.045"), 5),
    (25000, 50000): RakeConfigData(Decimal("0.04"), 5),

    # High stakes: 4% rake, 5 BB cap
    (50000, 100000): RakeConfigData(Decimal("0.04"), 5),
    (100000, 200000): RakeConfigData(Decimal("0.035"), 5),
}

# Default rake config for unlisted blind levels
DEFAULT_RAKE_CONFIG = RakeConfigData(Decimal("0.05"), 3)


@dataclass
class RakeResult:
    """Result of rake calculation.
    
    Attributes:
        total_rake: Total rake collected from the pot
        rake_per_winner: Dict mapping winner position to their rake contribution
        pot_after_rake: Pot amount after rake deduction
        applied_nfnd: Whether No Flop No Drop was applied (no rake)
    """
    total_rake: int
    rake_per_winner: dict[int, int]  # position -> rake amount
    pot_after_rake: int
    applied_nfnd: bool


class RakeService:
    """Service for calculating and collecting rake from poker hands.
    
    Implements:
    - Percentage-based rake with caps per blind level
    - No Flop No Drop (NFND): No rake if hand ends before flop
    - Proportional rake distribution among winners
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize rake service.
        
        Args:
            session: Database session for wallet operations
        """
        self.session = session
        self._wallet_service = WalletService(session)
    
    def get_rake_config(
        self,
        small_blind: int,
        big_blind: int,
    ) -> RakeConfigData:
        """Get rake configuration for blind level (하드코딩 기본값).

        DB 설정을 사용하려면 get_rake_config_from_db()를 사용하세요.

        Args:
            small_blind: Small blind amount in KRW
            big_blind: Big blind amount in KRW

        Returns:
            RakeConfigData for the blind level
        """
        config = RAKE_CONFIGS.get((small_blind, big_blind))
        if config:
            return config

        # Find closest matching config by big blind
        closest_config = DEFAULT_RAKE_CONFIG
        closest_diff = float('inf')

        for (sb, bb), cfg in RAKE_CONFIGS.items():
            diff = abs(bb - big_blind)
            if diff < closest_diff:
                closest_diff = diff
                closest_config = cfg

        return closest_config

    async def get_rake_config_from_db(
        self,
        small_blind: int,
        big_blind: int,
    ) -> RakeConfigData:
        """DB에서 레이크 설정 조회, 없으면 하드코딩 기본값 사용.

        Args:
            small_blind: Small blind amount in KRW
            big_blind: Big blind amount in KRW

        Returns:
            RakeConfigData for the blind level
        """
        # DB에서 활성화된 설정 조회
        result = await self.session.execute(
            select(RakeConfig).where(
                RakeConfig.small_blind == small_blind,
                RakeConfig.big_blind == big_blind,
                RakeConfig.is_active == True,  # noqa: E712
            )
        )
        db_config = result.scalar_one_or_none()

        if db_config:
            logger.debug(
                f"Using DB rake config: SB={small_blind} BB={big_blind} "
                f"{float(db_config.percentage)*100}% cap={db_config.cap_bb}BB"
            )
            return RakeConfigData(
                percentage=db_config.percentage,
                cap_bb=db_config.cap_bb,
            )

        # DB에 없으면 하드코딩 기본값 사용
        return self.get_rake_config(small_blind, big_blind)
    
    def calculate_rake(
        self,
        pot_total: int,
        small_blind: int,
        big_blind: int,
        phase: "GamePhase",
        winners: list[dict],
        config: RakeConfigData | None = None,
    ) -> RakeResult:
        """Calculate rake for a completed hand.

        Args:
            pot_total: Total pot amount in KRW
            small_blind: Small blind amount
            big_blind: Big blind amount
            phase: Final phase of the hand (for NFND check)
            winners: List of winner dicts with 'position' and 'amount' keys
            config: Optional rake config (DB에서 가져온 설정)

        Returns:
            RakeResult with calculated rake amounts
        """
        from app.engine.state import GamePhase

        # No Flop No Drop: No rake if hand ended before flop
        if phase == GamePhase.PREFLOP or phase == GamePhase.FINISHED:
            # Check if we actually saw a flop
            # FINISHED phase could mean everyone folded preflop
            # We need to check if there was only one winner (everyone else folded)
            if len(winners) == 1 and pot_total <= big_blind * 3:
                # Likely a preflop fold - no rake
                logger.debug(
                    f"NFND applied: pot={pot_total}, winners={len(winners)}, "
                    f"phase={phase}"
                )
                return RakeResult(
                    total_rake=0,
                    rake_per_winner={},
                    pot_after_rake=pot_total,
                    applied_nfnd=True,
                )

        # Get rake config for this blind level
        if config is None:
            config = self.get_rake_config(small_blind, big_blind)

        # Calculate raw rake
        raw_rake = int(Decimal(pot_total) * config.percentage)

        # Apply cap (in big blinds)
        max_rake = big_blind * config.cap_bb
        total_rake = min(raw_rake, max_rake)

        # Minimum rake threshold (don't collect tiny amounts)
        if total_rake < 100:  # Less than ₩100
            return RakeResult(
                total_rake=0,
                rake_per_winner={},
                pot_after_rake=pot_total,
                applied_nfnd=False,
            )

        # Distribute rake proportionally among winners
        rake_per_winner = self._distribute_rake(winners, total_rake)

        logger.info(
            f"Rake calculated: pot={pot_total:,} rake={total_rake:,} "
            f"({config.percentage*100}%, cap={max_rake:,})"
        )

        return RakeResult(
            total_rake=total_rake,
            rake_per_winner=rake_per_winner,
            pot_after_rake=pot_total - total_rake,
            applied_nfnd=False,
        )
    
    def _distribute_rake(
        self,
        winners: list[dict],
        total_rake: int,
    ) -> dict[int, int]:
        """Distribute rake proportionally among winners.
        
        Args:
            winners: List of winner dicts with 'position' and 'amount'
            total_rake: Total rake to distribute
            
        Returns:
            Dict mapping position to rake amount
        """
        if not winners or total_rake <= 0:
            return {}
        
        total_winnings = sum(w.get("amount", 0) for w in winners)
        if total_winnings <= 0:
            return {}
        
        rake_per_winner = {}
        distributed = 0
        
        for i, winner in enumerate(winners):
            position = winner.get("position")
            amount = winner.get("amount", 0)
            
            if position is None or amount <= 0:
                continue
            
            # Calculate proportional rake
            if i == len(winners) - 1:
                # Last winner gets remainder to avoid rounding issues
                rake_share = total_rake - distributed
            else:
                proportion = Decimal(amount) / Decimal(total_winnings)
                rake_share = int(Decimal(total_rake) * proportion)
            
            if rake_share > 0:
                rake_per_winner[position] = rake_share
                distributed += rake_share
        
        return rake_per_winner
    
    async def collect_rake(
        self,
        table_id: str,
        hand_id: str,
        rake_result: RakeResult,
        position_to_user_id: dict[int, str],
    ) -> list[dict]:
        """Collect rake from winners and record transactions.
        
        Args:
            table_id: Table ID
            hand_id: Hand ID
            rake_result: Calculated rake result
            position_to_user_id: Mapping of seat position to user ID
            
        Returns:
            List of transaction records
        """
        if rake_result.total_rake <= 0:
            return []
        
        transactions = []
        
        for position, rake_amount in rake_result.rake_per_winner.items():
            user_id = position_to_user_id.get(position)
            if not user_id:
                logger.warning(
                    f"No user_id for position {position}, skipping rake"
                )
                continue
            
            try:
                tx = await self._wallet_service.deduct_rake(
                    user_id=user_id,
                    amount=rake_amount,
                    table_id=table_id,
                    hand_id=hand_id,
                )
                if tx:
                    transactions.append({
                        "user_id": user_id,
                        "position": position,
                        "amount": rake_amount,
                        "transaction_id": tx.id,
                    })
                    logger.info(
                        f"Rake collected: user={user_id[:8]}... "
                        f"amount={rake_amount:,} KRW"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to collect rake from user {user_id}: {e}"
                )
        
        return transactions
    
    async def process_hand_rake(
        self,
        table_id: str,
        hand_id: str,
        pot_total: int,
        small_blind: int,
        big_blind: int,
        phase: "GamePhase",
        winners: list[dict],
        position_to_user_id: dict[int, str],
    ) -> RakeResult:
        """Calculate and collect rake for a completed hand.

        This is the main entry point for rake processing.
        DB에 설정이 있으면 DB 설정을 우선 사용합니다.

        Args:
            table_id: Table ID
            hand_id: Hand ID
            pot_total: Total pot amount
            small_blind: Small blind amount
            big_blind: Big blind amount
            phase: Final hand phase
            winners: List of winners with position and amount
            position_to_user_id: Position to user ID mapping

        Returns:
            RakeResult with collection details
        """
        # DB에서 레이크 설정 조회 (없으면 하드코딩 기본값)
        config = await self.get_rake_config_from_db(small_blind, big_blind)

        # Calculate rake
        rake_result = self.calculate_rake(
            pot_total=pot_total,
            small_blind=small_blind,
            big_blind=big_blind,
            phase=phase,
            winners=winners,
            config=config,
        )

        # Collect rake if applicable
        if rake_result.total_rake > 0:
            await self.collect_rake(
                table_id=table_id,
                hand_id=hand_id,
                rake_result=rake_result,
                position_to_user_id=position_to_user_id,
            )

        return rake_result


# ============================================================================
# Rake Config Service (P1-1)
# ============================================================================


class RakeConfigService:
    """레이크 설정 관리 서비스.

    관리자가 블라인드 레벨별 레이크 설정을 CRUD할 수 있습니다.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_configs(
        self,
        include_inactive: bool = False,
    ) -> list[RakeConfig]:
        """레이크 설정 목록 조회."""
        query = select(RakeConfig)
        if not include_inactive:
            query = query.where(RakeConfig.is_active == True)  # noqa: E712
        query = query.order_by(RakeConfig.small_blind, RakeConfig.big_blind)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_config(self, config_id: str) -> RakeConfig | None:
        """레이크 설정 조회."""
        result = await self.session.execute(
            select(RakeConfig).where(RakeConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_config_by_blind_level(
        self,
        small_blind: int,
        big_blind: int,
    ) -> RakeConfig | None:
        """블라인드 레벨로 레이크 설정 조회."""
        result = await self.session.execute(
            select(RakeConfig).where(
                RakeConfig.small_blind == small_blind,
                RakeConfig.big_blind == big_blind,
            )
        )
        return result.scalar_one_or_none()

    async def create_config(
        self,
        small_blind: int,
        big_blind: int,
        percentage: float,
        cap_bb: int,
        is_active: bool = True,
    ) -> RakeConfig:
        """레이크 설정 생성."""
        config = RakeConfig(
            small_blind=small_blind,
            big_blind=big_blind,
            percentage=Decimal(str(percentage)),
            cap_bb=cap_bb,
            is_active=is_active,
        )
        self.session.add(config)
        await self.session.flush()
        return config

    async def update_config(
        self,
        config_id: str,
        percentage: float | None = None,
        cap_bb: int | None = None,
        is_active: bool | None = None,
    ) -> RakeConfig | None:
        """레이크 설정 수정."""
        config = await self.get_config(config_id)
        if not config:
            return None

        if percentage is not None:
            config.percentage = Decimal(str(percentage))
        if cap_bb is not None:
            config.cap_bb = cap_bb
        if is_active is not None:
            config.is_active = is_active

        await self.session.flush()
        return config

    async def delete_config(self, config_id: str) -> bool:
        """레이크 설정 삭제."""
        config = await self.get_config(config_id)
        if not config:
            return False

        await self.session.delete(config)
        await self.session.flush()
        return True
