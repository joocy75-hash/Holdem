"""KYC (Know Your Customer) 서비스.

성인 인증 및 본인 확인 비즈니스 로직.
"""

import base64
import hashlib
import logging
import os
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kyc import KYCProvider, KYCStatus, UserKYC
from app.models.user import User

logger = logging.getLogger(__name__)

# ========== 암호화 설정 ==========

# 환경변수에서 암호화 키 로드
_KYC_ENCRYPTION_KEY = os.environ.get("KYC_ENCRYPTION_KEY")

# Fernet 인스턴스 (지연 초기화)
_fernet_instance: Fernet | None = None

# 키 유도 시 사용할 고정 salt (키 자체가 이미 강력하다고 가정)
# 프로덕션에서는 별도 환경변수로 관리 권장
_KDF_SALT = b"kyc_encryption_salt_v1"


class KYCEncryptionError(Exception):
    """KYC 암호화/복호화 관련 예외."""

    pass


def _derive_fernet_key(secret_key: str) -> bytes:
    """사용자 제공 키에서 Fernet 호환 32바이트 키 유도.

    PBKDF2를 사용하여 임의 길이의 비밀 키에서 안전한 32바이트 키를 생성.

    Args:
        secret_key: 환경변수에서 가져온 비밀 키

    Returns:
        Base64 인코딩된 32바이트 Fernet 키
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KDF_SALT,
        iterations=480000,  # OWASP 권장 (2023 기준)
    )
    key = kdf.derive(secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def _get_fernet() -> Fernet:
    """Fernet 인스턴스를 반환 (싱글톤).

    Returns:
        Fernet 인스턴스

    Raises:
        KYCEncryptionError: 암호화 키가 설정되지 않은 경우
    """
    global _fernet_instance

    if _fernet_instance is not None:
        return _fernet_instance

    if not _KYC_ENCRYPTION_KEY:
        raise KYCEncryptionError(
            "KYC_ENCRYPTION_KEY 환경변수가 설정되지 않았습니다. "
            "32자 이상의 안전한 키를 설정해주세요."
        )

    if len(_KYC_ENCRYPTION_KEY) < 32:
        raise KYCEncryptionError(
            "KYC_ENCRYPTION_KEY는 최소 32자 이상이어야 합니다. "
            f"현재: {len(_KYC_ENCRYPTION_KEY)}자"
        )

    try:
        fernet_key = _derive_fernet_key(_KYC_ENCRYPTION_KEY)
        _fernet_instance = Fernet(fernet_key)
        logger.info("KYC 암호화 모듈 초기화 완료")
        return _fernet_instance
    except Exception as e:
        raise KYCEncryptionError(f"Fernet 초기화 실패: {e}") from e


def _is_legacy_base64(data: str) -> bool:
    """데이터가 레거시 Base64 형식인지 확인.

    Fernet 토큰은 'gAAAAA'로 시작하는 특징이 있음.
    레거시 Base64는 이 패턴이 없음.

    Args:
        data: 확인할 데이터

    Returns:
        레거시 Base64 형식이면 True
    """
    # Fernet 토큰은 버전 바이트(0x80)로 시작하며 Base64 인코딩 시 'gAAAAA'로 시작
    if data.startswith("gAAAAA"):
        return False

    # 추가 검증: Fernet 토큰 길이는 최소 44자 이상 (16바이트 IV + 16바이트 최소 데이터 + 32바이트 HMAC)
    # 일반적인 한국 이름 Base64는 8-20자 정도
    if len(data) < 44:
        return True

    return False


def generate_encryption_key() -> str:
    """새로운 암호화 키 생성 (설정용 유틸리티).

    Returns:
        64자의 안전한 랜덤 키
    """
    return secrets.token_hex(32)

# 성인 기준 나이 (만 19세)
ADULT_AGE = 19

# KYC 인증 유효 기간 (1년)
KYC_VALIDITY_DAYS = 365

# 최대 인증 시도 횟수 (1일)
MAX_ATTEMPTS_PER_DAY = 5


class KYCError(Exception):
    """KYC 관련 예외."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class KYCService:
    """KYC 인증 서비스."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kyc_status(self, user_id: str) -> dict[str, Any]:
        """사용자 KYC 인증 상태 조회.

        Args:
            user_id: 사용자 ID

        Returns:
            KYC 상태 정보
        """
        kyc = await self._get_user_kyc(user_id)

        if not kyc:
            return {
                "status": KYCStatus.NONE.value,
                "is_verified": False,
                "is_adult": False,
                "can_withdraw": False,
                "message": "본인인증이 필요합니다.",
            }

        # 만료 체크
        is_expired = kyc.is_expired
        if is_expired and kyc.status == KYCStatus.VERIFIED.value:
            kyc.status = KYCStatus.EXPIRED.value
            await self.db.flush()

        return {
            "status": kyc.status,
            "is_verified": kyc.is_verified,
            "is_adult": kyc.is_adult,
            "can_withdraw": kyc.can_withdraw(),
            "verified_at": kyc.verified_at.isoformat() if kyc.verified_at else None,
            "expires_at": kyc.expires_at.isoformat() if kyc.expires_at else None,
            "rejection_reason": kyc.rejection_reason if kyc.status == KYCStatus.REJECTED.value else None,
            "message": self._get_status_message(kyc),
        }

    async def request_verification(
        self,
        user_id: str,
        provider: KYCProvider = KYCProvider.NICE,
    ) -> dict[str, Any]:
        """본인인증 요청 시작.

        외부 인증 서비스 연동 전 사전 검증 및 URL 생성.

        Args:
            user_id: 사용자 ID
            provider: 인증 제공자

        Returns:
            인증 요청 정보 (redirect_url 등)

        Raises:
            KYCError: 인증 요청 불가
        """
        kyc = await self._get_or_create_kyc(user_id)

        # 이미 인증 완료된 경우
        if kyc.is_verified and not kyc.is_expired:
            raise KYCError(
                "KYC_ALREADY_VERIFIED",
                "이미 본인인증이 완료되었습니다.",
                {"expires_at": kyc.expires_at.isoformat() if kyc.expires_at else None},
            )

        # 시도 횟수 체크
        if not self._can_attempt(kyc):
            raise KYCError(
                "KYC_TOO_MANY_ATTEMPTS",
                "일일 인증 시도 횟수를 초과했습니다. 내일 다시 시도해주세요.",
                {"max_attempts": MAX_ATTEMPTS_PER_DAY},
            )

        # 시도 횟수 증가
        kyc.attempt_count += 1
        kyc.last_attempt_at = datetime.now(timezone.utc)
        kyc.status = KYCStatus.PENDING.value
        kyc.provider = provider.value

        await self.db.flush()

        logger.info(
            f"KYC 인증 요청: user={user_id[:8]}... provider={provider.value} "
            f"attempt={kyc.attempt_count}"
        )

        # 실제 환경에서는 외부 인증 서비스 URL 생성
        # 현재는 mock 응답 반환
        return {
            "request_id": kyc.id,
            "provider": provider.value,
            "status": KYCStatus.PENDING.value,
            # 실제 구현 시 인증 서비스 redirect URL
            "redirect_url": f"/api/v1/kyc/verify/{kyc.id}",
            "message": "본인인증 페이지로 이동합니다.",
        }

    async def complete_verification(
        self,
        user_id: str,
        real_name: str,
        birth_date: date,
        phone_number: str,
        ci: str | None = None,
        di: str | None = None,
    ) -> dict[str, Any]:
        """본인인증 완료 처리.

        외부 인증 서비스 콜백 후 호출.

        Args:
            user_id: 사용자 ID
            real_name: 실명
            birth_date: 생년월일
            phone_number: 휴대폰 번호
            ci: 연계정보 (CI)
            di: 본인확인정보 (DI)

        Returns:
            인증 결과 정보

        Raises:
            KYCError: 인증 실패
        """
        kyc = await self._get_or_create_kyc(user_id)

        # 이미 인증 완료
        if kyc.is_verified and not kyc.is_expired:
            raise KYCError(
                "KYC_ALREADY_VERIFIED",
                "이미 본인인증이 완료되었습니다.",
            )

        # CI 중복 체크 (동일인 다중 계정 방지)
        if ci:
            ci_hash = self._hash_value(ci)
            existing = await self._find_by_ci(ci_hash, exclude_user_id=user_id)
            if existing:
                logger.warning(
                    f"KYC 중복 CI 감지: user={user_id[:8]}... existing_user={existing.user_id[:8]}..."
                )
                raise KYCError(
                    "KYC_DUPLICATE_CI",
                    "이미 다른 계정으로 인증된 정보입니다.",
                )
            kyc.ci_hash = ci_hash

        # DI 저장
        if di:
            kyc.di_hash = self._hash_value(di)

        # 성인 여부 확인
        is_adult = self._check_adult(birth_date)

        if not is_adult:
            kyc.status = KYCStatus.REJECTED.value
            kyc.rejection_reason = "만 19세 미만은 서비스를 이용할 수 없습니다."
            await self.db.flush()

            raise KYCError(
                "KYC_NOT_ADULT",
                "만 19세 이상만 이용 가능합니다.",
                {"required_age": ADULT_AGE},
            )

        # 인증 정보 저장
        kyc.real_name_encrypted = self._encrypt_name(real_name)
        kyc.birth_date = birth_date
        kyc.phone_hash = self._hash_value(phone_number)
        kyc.is_adult = True
        kyc.status = KYCStatus.VERIFIED.value
        kyc.verified_at = datetime.now(timezone.utc)
        kyc.expires_at = datetime.now(timezone.utc) + timedelta(days=KYC_VALIDITY_DAYS)
        kyc.rejection_reason = None

        await self.db.flush()

        logger.info(
            f"KYC 인증 완료: user={user_id[:8]}... is_adult={is_adult} "
            f"expires={kyc.expires_at.date()}"
        )

        return {
            "status": KYCStatus.VERIFIED.value,
            "is_verified": True,
            "is_adult": True,
            "can_withdraw": True,
            "verified_at": kyc.verified_at.isoformat(),
            "expires_at": kyc.expires_at.isoformat(),
            "message": "본인인증이 완료되었습니다.",
        }

    async def admin_verify(
        self,
        user_id: str,
        admin_id: str,
        is_adult: bool,
        note: str | None = None,
    ) -> dict[str, Any]:
        """관리자 수동 인증.

        Args:
            user_id: 사용자 ID
            admin_id: 관리자 ID
            is_adult: 성인 여부
            note: 관리자 메모

        Returns:
            인증 결과
        """
        kyc = await self._get_or_create_kyc(user_id)

        kyc.status = KYCStatus.VERIFIED.value
        kyc.provider = KYCProvider.MANUAL.value
        kyc.is_adult = is_adult
        kyc.verified_at = datetime.now(timezone.utc)
        kyc.expires_at = datetime.now(timezone.utc) + timedelta(days=KYC_VALIDITY_DAYS)
        kyc.reviewed_by = admin_id
        kyc.admin_note = note
        kyc.rejection_reason = None

        await self.db.flush()

        logger.info(
            f"KYC 관리자 인증: user={user_id[:8]}... admin={admin_id[:8]}... "
            f"is_adult={is_adult}"
        )

        return {
            "status": KYCStatus.VERIFIED.value,
            "is_verified": True,
            "is_adult": is_adult,
            "verified_at": kyc.verified_at.isoformat(),
            "message": "관리자에 의해 인증되었습니다.",
        }

    async def admin_reject(
        self,
        user_id: str,
        admin_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """관리자 인증 거부.

        Args:
            user_id: 사용자 ID
            admin_id: 관리자 ID
            reason: 거부 사유

        Returns:
            처리 결과
        """
        kyc = await self._get_or_create_kyc(user_id)

        kyc.status = KYCStatus.REJECTED.value
        kyc.rejection_reason = reason
        kyc.reviewed_by = admin_id

        await self.db.flush()

        logger.info(
            f"KYC 거부: user={user_id[:8]}... admin={admin_id[:8]}... reason={reason}"
        )

        return {
            "status": KYCStatus.REJECTED.value,
            "rejection_reason": reason,
            "message": "인증이 거부되었습니다.",
        }

    async def reset_kyc(self, user_id: str, admin_id: str) -> dict[str, Any]:
        """KYC 정보 초기화 (재인증 허용).

        Args:
            user_id: 사용자 ID
            admin_id: 관리자 ID

        Returns:
            처리 결과
        """
        kyc = await self._get_user_kyc(user_id)

        if not kyc:
            raise KYCError("KYC_NOT_FOUND", "KYC 정보가 없습니다.")

        old_status = kyc.status
        kyc.status = KYCStatus.NONE.value
        kyc.attempt_count = 0
        kyc.rejection_reason = None
        kyc.admin_note = f"관리자({admin_id[:8]}...)에 의해 초기화됨. 이전 상태: {old_status}"

        await self.db.flush()

        logger.info(f"KYC 초기화: user={user_id[:8]}... admin={admin_id[:8]}...")

        return {
            "status": KYCStatus.NONE.value,
            "message": "KYC 정보가 초기화되었습니다.",
        }

    # ========== Private Methods ==========

    async def _get_user_kyc(self, user_id: str) -> UserKYC | None:
        """사용자 KYC 정보 조회."""
        result = await self.db.execute(
            select(UserKYC).where(UserKYC.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_kyc(self, user_id: str) -> UserKYC:
        """사용자 KYC 정보 조회 또는 생성."""
        kyc = await self._get_user_kyc(user_id)

        if not kyc:
            # 사용자 존재 확인
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise KYCError("USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")

            kyc = UserKYC(
                user_id=user_id,
                status=KYCStatus.NONE.value,
            )
            self.db.add(kyc)
            await self.db.flush()

        return kyc

    async def _find_by_ci(
        self, ci_hash: str, exclude_user_id: str | None = None
    ) -> UserKYC | None:
        """CI 해시로 KYC 조회."""
        query = select(UserKYC).where(UserKYC.ci_hash == ci_hash)
        if exclude_user_id:
            query = query.where(UserKYC.user_id != exclude_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _can_attempt(self, kyc: UserKYC) -> bool:
        """인증 시도 가능 여부."""
        if not kyc.last_attempt_at:
            return True

        # 마지막 시도가 오늘인 경우 횟수 체크
        now = datetime.now(timezone.utc)
        if kyc.last_attempt_at.date() == now.date():
            return kyc.attempt_count < MAX_ATTEMPTS_PER_DAY

        # 다른 날이면 리셋
        kyc.attempt_count = 0
        return True

    def _check_adult(self, birth_date: date) -> bool:
        """성인 여부 확인 (만 19세 이상)."""
        today = date.today()
        age = today.year - birth_date.year

        # 생일이 지났는지 확인
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age >= ADULT_AGE

    def _hash_value(self, value: str) -> str:
        """값을 SHA-256 해시."""
        return hashlib.sha256(value.encode()).hexdigest()

    def _encrypt_name(self, name: str) -> str:
        """실명을 Fernet(AES-128-CBC + HMAC)으로 암호화.

        Fernet은 다음을 제공:
        - AES-128-CBC 암호화
        - HMAC-SHA256 인증
        - 타임스탬프 (선택적 TTL 지원)

        Args:
            name: 암호화할 실명

        Returns:
            Base64 인코딩된 암호문

        Raises:
            KYCEncryptionError: 암호화 키가 없거나 암호화 실패 시
        """
        if not name:
            raise KYCEncryptionError("암호화할 이름이 비어있습니다.")

        try:
            fernet = _get_fernet()
            encrypted_bytes = fernet.encrypt(name.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except KYCEncryptionError:
            # 키 관련 에러는 그대로 전파
            raise
        except Exception as e:
            logger.error(f"실명 암호화 실패: {e}")
            raise KYCEncryptionError(f"암호화 처리 중 오류 발생: {e}") from e

    def _decrypt_name(self, encrypted: str) -> str:
        """암호화된 실명을 복호화.

        레거시 Base64 데이터도 자동으로 처리 (마이그레이션 지원).

        Args:
            encrypted: 암호화된 문자열 (Fernet 또는 레거시 Base64)

        Returns:
            복호화된 실명

        Raises:
            KYCEncryptionError: 복호화 실패 시
        """
        if not encrypted:
            raise KYCEncryptionError("복호화할 데이터가 비어있습니다.")

        # 레거시 Base64 데이터 처리 (마이그레이션 호환)
        if _is_legacy_base64(encrypted):
            try:
                decoded = base64.b64decode(encrypted.encode("utf-8")).decode("utf-8")
                logger.warning(
                    "레거시 Base64 형식 데이터 감지. 보안을 위해 재암호화를 권장합니다."
                )
                return decoded
            except Exception as e:
                logger.error(f"레거시 Base64 복호화 실패: {e}")
                raise KYCEncryptionError(f"레거시 데이터 복호화 실패: {e}") from e

        # Fernet 복호화
        try:
            fernet = _get_fernet()
            decrypted_bytes = fernet.decrypt(encrypted.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            logger.error("Fernet 토큰 검증 실패 - 키가 변경되었거나 데이터가 손상됨")
            raise KYCEncryptionError(
                "복호화 실패: 암호화 키가 변경되었거나 데이터가 손상되었습니다."
            )
        except KYCEncryptionError:
            raise
        except Exception as e:
            logger.error(f"실명 복호화 실패: {e}")
            raise KYCEncryptionError(f"복호화 처리 중 오류 발생: {e}") from e

    async def migrate_legacy_encryption(self, user_id: str) -> bool:
        """레거시 Base64 암호화를 Fernet으로 마이그레이션.

        기존 Base64로 저장된 데이터를 안전한 Fernet 암호화로 업그레이드.

        Args:
            user_id: 사용자 ID

        Returns:
            마이그레이션 성공 여부
        """
        kyc = await self._get_user_kyc(user_id)

        if not kyc or not kyc.real_name_encrypted:
            return False

        # 이미 Fernet 형식이면 스킵
        if not _is_legacy_base64(kyc.real_name_encrypted):
            logger.debug(f"이미 Fernet 암호화 적용됨: user={user_id[:8]}...")
            return False

        try:
            # 레거시 복호화 후 새로운 암호화 적용
            decrypted_name = self._decrypt_name(kyc.real_name_encrypted)
            kyc.real_name_encrypted = self._encrypt_name(decrypted_name)
            await self.db.flush()

            logger.info(f"레거시 암호화 마이그레이션 완료: user={user_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"레거시 암호화 마이그레이션 실패: user={user_id[:8]}... error={e}")
            return False

    def _get_status_message(self, kyc: UserKYC) -> str:
        """상태별 메시지."""
        messages = {
            KYCStatus.NONE.value: "본인인증이 필요합니다.",
            KYCStatus.PENDING.value: "본인인증 진행 중입니다.",
            KYCStatus.VERIFIED.value: "본인인증이 완료되었습니다.",
            KYCStatus.REJECTED.value: f"본인인증이 거부되었습니다. 사유: {kyc.rejection_reason or '알 수 없음'}",
            KYCStatus.EXPIRED.value: "본인인증이 만료되었습니다. 재인증이 필요합니다.",
        }
        return messages.get(kyc.status, "알 수 없는 상태입니다.")
