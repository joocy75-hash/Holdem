"""Telegram Bot for TON/USDT deposit management.

Provides commands for users to request deposits and check status.
Uses aiogram 3.x for Telegram Bot API integration.
"""

import logging
from decimal import Decimal
from typing import Optional
from io import BytesIO
import base64

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.database import get_admin_db
from app.services.crypto.deposit_request_service import DepositRequestService
from app.services.crypto.ton_exchange_rate import TonExchangeRateService
from app.services.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)
settings = get_settings()

# Router for deposit commands
deposit_router = Router(name="deposit")


class DepositStates(StatesGroup):
    """FSM states for deposit flow."""
    waiting_for_amount = State()


# ==================== Command Handlers ====================

@deposit_router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "👋 <b>안녕하세요!</b>\n\n"
        "TON/USDT 입금 봇입니다.\n\n"
        "📥 <b>/deposit</b> - 입금 요청\n"
        "📊 <b>/status</b> - 입금 상태 확인\n"
        "💱 <b>/rate</b> - 현재 환율 확인\n"
        "❓ <b>/help</b> - 도움말\n\n"
        "입금을 원하시면 /deposit 명령어를 입력해주세요.",
        parse_mode=ParseMode.HTML,
    )


@deposit_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "📖 <b>도움말</b>\n\n"
        "<b>명령어 목록:</b>\n"
        "• /deposit - 새 입금 요청 생성\n"
        "• /status - 최근 입금 상태 확인\n"
        "• /rate - 현재 USDT/KRW 환율 확인\n"
        "• /cancel - 진행 중인 작업 취소\n\n"
        "<b>입금 방법:</b>\n"
        "1. /deposit 명령어 입력\n"
        "2. 원하는 금액(KRW) 입력\n"
        "3. QR 코드 스캔 또는 주소로 송금\n"
        "4. 메모 필수 입력!\n"
        "5. 자동 확인 후 잔액 충전\n\n"
        "⚠️ <b>주의:</b> 메모 없이 송금하면 자동 처리가 불가능합니다.",
        parse_mode=ParseMode.HTML,
    )


@deposit_router.message(Command("rate"))
async def cmd_rate(message: Message):
    """Handle /rate command - show current exchange rate."""
    try:
        exchange_service = TonExchangeRateService()
        rate = await exchange_service.get_usdt_krw_rate()
        await exchange_service.close()
        
        await message.answer(
            "💱 <b>현재 환율</b>\n\n"
            f"1 USDT = <b>{rate:,.2f} KRW</b>\n\n"
            f"예시:\n"
            f"• 100,000 KRW → {100000/float(rate):.2f} USDT\n"
            f"• 500,000 KRW → {500000/float(rate):.2f} USDT\n"
            f"• 1,000,000 KRW → {1000000/float(rate):.2f} USDT\n\n"
            "💡 환율은 실시간으로 변동됩니다.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Error fetching rate: {e}")
        await message.answer(
            "❌ 환율 조회 중 오류가 발생했습니다.\n"
            "잠시 후 다시 시도해주세요.",
            parse_mode=ParseMode.HTML,
        )


@deposit_router.message(Command("deposit"))
async def cmd_deposit(message: Message, state: FSMContext):
    """Handle /deposit command - start deposit flow."""
    await state.set_state(DepositStates.waiting_for_amount)
    
    await message.answer(
        "💰 <b>입금 요청</b>\n\n"
        "입금할 금액을 <b>원(KRW)</b> 단위로 입력해주세요.\n\n"
        "예시:\n"
        "• 100000 (10만원)\n"
        "• 500000 (50만원)\n"
        "• 1000000 (100만원)\n\n"
        "최소 입금액: 10,000 KRW\n"
        "최대 입금액: 10,000,000 KRW\n\n"
        "취소하려면 /cancel 을 입력하세요.",
        parse_mode=ParseMode.HTML,
    )


@deposit_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle /cancel command - cancel current operation."""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("취소할 작업이 없습니다.")
        return
    
    await state.clear()
    await message.answer(
        "✅ 작업이 취소되었습니다.\n"
        "새로운 입금을 원하시면 /deposit 을 입력해주세요.",
        parse_mode=ParseMode.HTML,
    )


@deposit_router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """Process deposit amount input."""
    # Validate amount
    try:
        amount_text = message.text.strip().replace(",", "")
        amount = int(amount_text)
    except (ValueError, AttributeError):
        await message.answer(
            "❌ 올바른 금액을 입력해주세요.\n"
            "숫자만 입력 가능합니다. (예: 100000)",
            parse_mode=ParseMode.HTML,
        )
        return
    
    # Check limits
    if amount < 10000:
        await message.answer(
            "❌ 최소 입금액은 <b>10,000 KRW</b>입니다.",
            parse_mode=ParseMode.HTML,
        )
        return
    
    if amount > 10000000:
        await message.answer(
            "❌ 최대 입금액은 <b>10,000,000 KRW</b>입니다.\n"
            "더 큰 금액은 고객센터로 문의해주세요.",
            parse_mode=ParseMode.HTML,
        )
        return
    
    # Clear state
    await state.clear()
    
    # Create deposit request
    try:
        await message.answer("⏳ 입금 요청을 생성 중입니다...")
        
        # Get database session
        async for db in get_admin_db():
            service = DepositRequestService(db)
            
            # Create request with telegram_id
            request = await service.create_request(
                user_id=str(message.from_user.id),
                requested_krw=amount,
                telegram_id=message.from_user.id,
            )
            
            # Decode QR image from base64
            qr_base64 = request.qr_data
            if qr_base64.startswith("data:image/png;base64,"):
                qr_base64 = qr_base64.split(",")[1]
            
            qr_bytes = base64.b64decode(qr_base64)
            qr_file = BufferedInputFile(qr_bytes, filename="deposit_qr.png")
            
            # Send QR code with instructions
            await message.answer_photo(
                photo=qr_file,
                caption=(
                    "✅ <b>입금 요청이 생성되었습니다!</b>\n\n"
                    f"💰 입금 금액: <b>{amount:,} KRW</b>\n"
                    f"💵 송금할 USDT: <b>{request.calculated_usdt:.2f} USDT</b>\n"
                    f"📊 적용 환율: {request.exchange_rate:.2f} KRW/USDT\n\n"
                    f"📝 <b>메모 (필수!):</b>\n"
                    f"<code>{request.memo}</code>\n\n"
                    f"⏰ 만료: <b>{request.remaining_seconds // 60}분</b> 후\n\n"
                    "⚠️ <b>중요:</b>\n"
                    "• 위 QR 코드를 스캔하거나\n"
                    "• TON 지갑에서 직접 송금 시\n"
                    "• <b>반드시 메모를 입력</b>해주세요!\n\n"
                    "메모 없이 송금하면 자동 처리가 불가능합니다."
                ),
                parse_mode=ParseMode.HTML,
            )
            
            break
            
    except Exception as e:
        logger.error(f"Error creating deposit request: {e}")
        await message.answer(
            "❌ 입금 요청 생성 중 오류가 발생했습니다.\n"
            "잠시 후 다시 시도해주세요.",
            parse_mode=ParseMode.HTML,
        )


@deposit_router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show recent deposit status."""
    try:
        async for db in get_admin_db():
            from sqlalchemy import select, desc
            from app.models.deposit_request import DepositRequest
            
            # Get recent deposits for this user
            result = await db.execute(
                select(DepositRequest)
                .where(DepositRequest.telegram_id == message.from_user.id)
                .order_by(desc(DepositRequest.created_at))
                .limit(5)
            )
            deposits = result.scalars().all()
            
            if not deposits:
                await message.answer(
                    "📭 입금 내역이 없습니다.\n"
                    "새로운 입금을 원하시면 /deposit 을 입력해주세요.",
                    parse_mode=ParseMode.HTML,
                )
                return
            
            # Format deposit list
            status_icons = {
                "pending": "⏳",
                "confirmed": "✅",
                "expired": "⏰",
                "cancelled": "❌",
            }
            
            status_text = "📊 <b>최근 입금 내역</b>\n\n"
            
            for deposit in deposits:
                icon = status_icons.get(deposit.status.value, "❓")
                status_text += (
                    f"{icon} <b>{deposit.requested_krw:,} KRW</b>\n"
                    f"   └ {deposit.calculated_usdt:.2f} USDT | "
                    f"{deposit.status.value}\n"
                    f"   └ {deposit.created_at.strftime('%m/%d %H:%M')}\n\n"
                )
            
            await message.answer(status_text, parse_mode=ParseMode.HTML)
            break
            
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        await message.answer(
            "❌ 상태 조회 중 오류가 발생했습니다.\n"
            "잠시 후 다시 시도해주세요.",
            parse_mode=ParseMode.HTML,
        )


# ==================== Bot Setup ====================

class DepositBot:
    """Telegram Bot for deposit management.
    
    Handles user commands for deposit requests and status checks.
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
    ):
        """Initialize deposit bot.
        
        Args:
            bot_token: Telegram bot token (from config if not provided)
        """
        self.bot_token = bot_token or settings.telegram_bot_token
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if bot is properly configured."""
        return bool(self.bot_token) and self.bot_token not in ("", "your-bot-token")
    
    def setup(self) -> tuple[Bot, Dispatcher]:
        """Set up bot and dispatcher.
        
        Returns:
            Tuple of (Bot, Dispatcher)
        """
        if not self.is_configured:
            raise ValueError("Telegram bot token not configured")
        
        self._bot = Bot(token=self.bot_token)
        self._dp = Dispatcher(storage=MemoryStorage())
        
        # Register routers
        self._dp.include_router(deposit_router)
        
        logger.info("Deposit bot configured")
        return self._bot, self._dp
    
    async def start_polling(self):
        """Start bot polling.
        
        Runs continuously until stopped.
        """
        if not self._bot or not self._dp:
            self.setup()
        
        logger.info("Starting deposit bot polling...")
        await self._dp.start_polling(self._bot)
    
    async def stop(self):
        """Stop bot and clean up."""
        if self._dp:
            await self._dp.stop_polling()
        
        if self._bot:
            await self._bot.session.close()
        
        logger.info("Deposit bot stopped")


# Singleton instance
_bot_instance: Optional[DepositBot] = None


def get_deposit_bot() -> DepositBot:
    """Get or create singleton bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = DepositBot()
    return _bot_instance


async def run_bot():
    """Run the deposit bot.
    
    Entry point for running the bot as a standalone process.
    """
    bot = get_deposit_bot()
    
    if not bot.is_configured:
        logger.error("Bot token not configured. Set TELEGRAM_BOT_TOKEN in .env")
        return
    
    try:
        await bot.start_polling()
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.stop()
