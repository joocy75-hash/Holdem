"""Telegram notification service for deposit events.

Sends notifications to users and admins about deposit status changes
using the aiogram library.
"""

import logging
from decimal import Decimal
from typing import Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from app.config import get_settings
from app.models.deposit_request import DepositRequest, DepositRequestStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramNotifier:
    """Telegram notification service for deposit events.
    
    Sends formatted messages to users and admin chat about
    deposit confirmations, expirations, and other events.
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        admin_chat_id: Optional[str] = None,
    ):
        """Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token (from config if not provided)
            admin_chat_id: Admin chat ID for notifications
        """
        self.bot_token = bot_token or settings.telegram_bot_token
        self.admin_chat_id = admin_chat_id or settings.telegram_admin_chat_id
        self._bot: Optional[Bot] = None
    
    @property
    def bot(self) -> Bot:
        """Get or create bot instance."""
        if self._bot is None:
            if not self.bot_token:
                raise ValueError("Telegram bot token not configured")
            self._bot = Bot(token=self.bot_token)
        return self._bot
    
    @property
    def is_configured(self) -> bool:
        """Check if notifier is properly configured."""
        return bool(self.bot_token) and self.bot_token not in ("", "your-bot-token")
    
    async def close(self):
        """Close bot session."""
        if self._bot:
            await self._bot.session.close()
            self._bot = None
    
    # ==================== User Notifications ====================
    
    async def notify_deposit_confirmed(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> bool:
        """Notify user that their deposit was confirmed.
        
        Args:
            request: The confirmed deposit request
            tx_hash: Transaction hash
            
        Returns:
            bool: True if notification sent successfully
        """
        if not request.telegram_id:
            logger.debug(f"No telegram_id for request {request.memo}, skipping user notification")
            return False
        
        message = self._format_deposit_confirmed_message(request, tx_hash)
        
        return await self._send_message(request.telegram_id, message)
    
    async def notify_deposit_expired(
        self,
        request: DepositRequest,
    ) -> bool:
        """Notify user that their deposit request expired.
        
        Args:
            request: The expired deposit request
            
        Returns:
            bool: True if notification sent successfully
        """
        if not request.telegram_id:
            logger.debug(f"No telegram_id for request {request.memo}, skipping user notification")
            return False
        
        message = self._format_deposit_expired_message(request)
        
        return await self._send_message(request.telegram_id, message)
    
    async def notify_deposit_created(
        self,
        request: DepositRequest,
    ) -> bool:
        """Notify user that their deposit request was created.
        
        Args:
            request: The created deposit request
            
        Returns:
            bool: True if notification sent successfully
        """
        if not request.telegram_id:
            logger.debug(f"No telegram_id for request {request.memo}, skipping user notification")
            return False
        
        message = self._format_deposit_created_message(request)
        
        return await self._send_message(request.telegram_id, message)
    
    async def send_deposit_reminder(
        self,
        request: DepositRequest,
        minutes_remaining: int,
    ) -> bool:
        """Send reminder about expiring deposit.
        
        Args:
            request: The deposit request
            minutes_remaining: Minutes until expiry
            
        Returns:
            bool: True if notification sent successfully
        """
        if not request.telegram_id:
            return False
        
        message = self._format_deposit_reminder_message(request, minutes_remaining)
        
        return await self._send_message(request.telegram_id, message)
    
    # ==================== Admin Notifications ====================
    
    async def notify_admin_deposit_confirmed(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> bool:
        """Notify admin chat about confirmed deposit.
        
        Args:
            request: The confirmed deposit request
            tx_hash: Transaction hash
            
        Returns:
            bool: True if notification sent successfully
        """
        if not self.admin_chat_id:
            logger.debug("No admin_chat_id configured, skipping admin notification")
            return False
        
        message = self._format_admin_deposit_confirmed_message(request, tx_hash)
        
        return await self._send_message(int(self.admin_chat_id), message)
    
    async def notify_admin_large_deposit(
        self,
        request: DepositRequest,
        tx_hash: str,
        threshold: Decimal = Decimal("1000"),
    ) -> bool:
        """Notify admin about large deposit (above threshold).
        
        Args:
            request: The deposit request
            tx_hash: Transaction hash
            threshold: USDT threshold for "large" deposit
            
        Returns:
            bool: True if notification sent successfully
        """
        if request.calculated_usdt < threshold:
            return False
        
        if not self.admin_chat_id:
            return False
        
        message = self._format_admin_large_deposit_message(request, tx_hash)
        
        return await self._send_message(int(self.admin_chat_id), message)
    
    async def notify_admin_manual_review_needed(
        self,
        request: DepositRequest,
        reason: str,
    ) -> bool:
        """Notify admin that manual review is needed.
        
        Args:
            request: The deposit request
            reason: Reason for manual review
            
        Returns:
            bool: True if notification sent successfully
        """
        if not self.admin_chat_id:
            return False
        
        message = self._format_admin_manual_review_message(request, reason)
        
        return await self._send_message(int(self.admin_chat_id), message)
    
    # ==================== Message Formatting ====================
    
    def _format_deposit_confirmed_message(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> str:
        """Format deposit confirmed message for user."""
        return (
            "✅ <b>입금이 확인되었습니다!</b>\n\n"
            f"💰 입금 금액: <b>{request.requested_krw:,} KRW</b>\n"
            f"💵 USDT: <b>{request.calculated_usdt:.2f} USDT</b>\n"
            f"📊 적용 환율: {request.exchange_rate:.2f} KRW/USDT\n\n"
            f"🔗 TX: <code>{tx_hash[:16]}...</code>\n\n"
            "잔액이 충전되었습니다. 즐거운 게임 되세요! 🎰"
        )
    
    def _format_deposit_expired_message(
        self,
        request: DepositRequest,
    ) -> str:
        """Format deposit expired message for user."""
        return (
            "⏰ <b>입금 요청이 만료되었습니다</b>\n\n"
            f"💰 요청 금액: {request.requested_krw:,} KRW\n"
            f"💵 USDT: {request.calculated_usdt:.2f} USDT\n"
            f"📝 메모: <code>{request.memo}</code>\n\n"
            "30분 내에 입금이 확인되지 않아 요청이 만료되었습니다.\n"
            "새로운 입금을 원하시면 /deposit 명령어를 사용해주세요."
        )
    
    def _format_deposit_created_message(
        self,
        request: DepositRequest,
    ) -> str:
        """Format deposit created message for user."""
        return (
            "📥 <b>입금 요청이 생성되었습니다</b>\n\n"
            f"💰 입금 금액: <b>{request.requested_krw:,} KRW</b>\n"
            f"💵 송금할 USDT: <b>{request.calculated_usdt:.2f} USDT</b>\n"
            f"📊 적용 환율: {request.exchange_rate:.2f} KRW/USDT\n\n"
            f"📝 메모 (필수): <code>{request.memo}</code>\n"
            f"⏰ 만료: {request.remaining_seconds // 60}분 후\n\n"
            "⚠️ <b>중요:</b> 송금 시 반드시 위 메모를 입력해주세요!\n"
            "메모가 없으면 자동 입금 처리가 불가능합니다."
        )
    
    def _format_deposit_reminder_message(
        self,
        request: DepositRequest,
        minutes_remaining: int,
    ) -> str:
        """Format deposit reminder message."""
        return (
            f"⏰ <b>입금 요청이 {minutes_remaining}분 후 만료됩니다!</b>\n\n"
            f"💵 송금할 USDT: <b>{request.calculated_usdt:.2f} USDT</b>\n"
            f"📝 메모: <code>{request.memo}</code>\n\n"
            "아직 입금하지 않으셨다면 서둘러주세요!"
        )
    
    def _format_admin_deposit_confirmed_message(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> str:
        """Format deposit confirmed message for admin."""
        return (
            "✅ <b>[입금 확인]</b>\n\n"
            f"👤 User: <code>{request.user_id}</code>\n"
            f"💰 KRW: {request.requested_krw:,}\n"
            f"💵 USDT: {request.calculated_usdt:.2f}\n"
            f"📊 Rate: {request.exchange_rate:.2f}\n"
            f"📝 Memo: <code>{request.memo}</code>\n"
            f"🔗 TX: <code>{tx_hash}</code>"
        )
    
    def _format_admin_large_deposit_message(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> str:
        """Format large deposit alert for admin."""
        return (
            "🚨 <b>[대량 입금 알림]</b>\n\n"
            f"👤 User: <code>{request.user_id}</code>\n"
            f"💰 KRW: <b>{request.requested_krw:,}</b>\n"
            f"💵 USDT: <b>{request.calculated_usdt:.2f}</b>\n"
            f"📊 Rate: {request.exchange_rate:.2f}\n"
            f"📝 Memo: <code>{request.memo}</code>\n"
            f"🔗 TX: <code>{tx_hash}</code>\n\n"
            "⚠️ 대량 입금입니다. 확인이 필요할 수 있습니다."
        )
    
    def _format_admin_manual_review_message(
        self,
        request: DepositRequest,
        reason: str,
    ) -> str:
        """Format manual review needed message for admin."""
        return (
            "⚠️ <b>[수동 검토 필요]</b>\n\n"
            f"👤 User: <code>{request.user_id}</code>\n"
            f"💰 KRW: {request.requested_krw:,}\n"
            f"💵 USDT: {request.calculated_usdt:.2f}\n"
            f"📝 Memo: <code>{request.memo}</code>\n"
            f"📋 Status: {request.status.value}\n\n"
            f"❓ 사유: {reason}\n\n"
            "관리자 대시보드에서 확인해주세요."
        )
    
    # ==================== Internal Methods ====================
    
    async def _send_message(
        self,
        chat_id: int,
        text: str,
    ) -> bool:
        """Send message to a chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text (HTML format)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_configured:
            logger.warning("Telegram notifier not configured, skipping message")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
            logger.info(f"Sent Telegram message to {chat_id}")
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False


# Singleton instance for convenience
_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> TelegramNotifier:
    """Get or create singleton notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


async def notify_deposit_confirmed(
    request: DepositRequest,
    tx_hash: str,
) -> bool:
    """Convenience function to notify about confirmed deposit.
    
    Sends notifications to both user and admin.
    
    Args:
        request: The confirmed deposit request
        tx_hash: Transaction hash
        
    Returns:
        bool: True if at least one notification was sent
    """
    notifier = get_telegram_notifier()
    
    user_sent = await notifier.notify_deposit_confirmed(request, tx_hash)
    admin_sent = await notifier.notify_admin_deposit_confirmed(request, tx_hash)
    
    # Also check for large deposit
    await notifier.notify_admin_large_deposit(request, tx_hash)
    
    return user_sent or admin_sent


async def notify_deposit_expired(request: DepositRequest) -> bool:
    """Convenience function to notify about expired deposit.
    
    Args:
        request: The expired deposit request
        
    Returns:
        bool: True if notification was sent
    """
    notifier = get_telegram_notifier()
    return await notifier.notify_deposit_expired(request)
