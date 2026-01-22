"""Fraud Detection Celery Tasks - 부정행위 탐지 주기적 태스크.

주기적으로 부정행위 데이터를 분석하고 의심 사용자를 차단합니다.

Tasks:
- fraud_scan_task: 5분마다 실시간 데이터 분석
- fraud_deep_analysis_task: 1시간마다 심층 분석
- fraud_cleanup_task: 24시간마다 오래된 데이터 정리
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.fraud_detection.fraud_scan_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fraud_scan_task(self) -> dict[str, Any]:
    """실시간 부정행위 스캔 태스크 (5분마다).

    메모리에 축적된 실시간 데이터를 분석하고
    임계값을 초과한 사용자를 차단합니다.

    Returns:
        스캔 결과 요약
    """
    try:
        # asyncio.run()은 새 이벤트 루프를 생성하고 정리까지 처리
        result = asyncio.run(_run_fraud_scan())
        return result

    except Exception as exc:
        logger.error(f"Fraud scan failed: {exc}")
        raise self.retry(exc=exc)


async def _run_fraud_scan() -> dict[str, Any]:
    """실제 부정행위 스캔 로직."""
    from app.services.fraud_auto_blocker import get_fraud_blocker

    blocker = get_fraud_blocker()
    if not blocker or not blocker.enabled:
        logger.debug("FraudAutoBlocker not enabled, skipping scan")
        return {"status": "skipped", "reason": "blocker_disabled"}

    # 현재 추적 중인 사용자 수
    tracked_users = len(blocker._fraud_scores)
    high_risk_users = []
    blocked_users = []

    # 높은 위험 점수를 가진 사용자 확인
    for user_id, score in list(blocker._fraud_scores.items()):
        if score.total_score >= 50:  # 50점 이상은 모니터링
            high_risk_users.append({
                "user_id": user_id,
                "score": score.total_score,
                "primary_risk": score.get_primary_reason().value,
            })

        # 자동 차단 체크
        if score.should_auto_block(blocker.block_threshold):
            if await blocker._check_and_block_user(user_id):
                blocked_users.append(user_id)

    result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tracked_users": tracked_users,
        "high_risk_count": len(high_risk_users),
        "blocked_count": len(blocked_users),
        "high_risk_users": high_risk_users[:10],  # 상위 10명만
        "blocked_users": blocked_users,
    }

    if blocked_users:
        logger.warning(f"Fraud scan 완료: {len(blocked_users)}명 자동 차단")
    else:
        logger.info(f"Fraud scan 완료: 추적 {tracked_users}명, 고위험 {len(high_risk_users)}명")

    return result


@celery_app.task(
    name="app.tasks.fraud_detection.fraud_deep_analysis_task",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def fraud_deep_analysis_task(self) -> dict[str, Any]:
    """심층 부정행위 분석 태스크 (1시간마다).

    DB에서 과거 데이터를 분석하여 패턴을 탐지합니다:
    - 담합 패턴 (같은 테이블에서 자주 만나는 사용자 쌍)
    - 비정상 승률 (특정 상대에게만 높은 승률)
    - 비정상 활동 시간 (봇 의심)

    Returns:
        분석 결과 요약
    """
    try:
        result = asyncio.run(_run_deep_analysis())
        return result

    except Exception as exc:
        logger.error(f"Fraud deep analysis failed: {exc}")
        raise self.retry(exc=exc)


async def _run_deep_analysis() -> dict[str, Any]:
    """심층 분석 로직."""
    from app.utils.db import async_session_factory

    suspicious_patterns = []

    try:
        async with async_session_factory() as db:
            # 1. 담합 패턴 분석: 같은 테이블에서 자주 만나는 사용자 쌍
            collusion_suspects = await _analyze_frequent_opponents(db)
            suspicious_patterns.extend(collusion_suspects)

            # 2. 비정상 승률 분석
            winrate_suspects = await _analyze_abnormal_winrate(db)
            suspicious_patterns.extend(winrate_suspects)

            # 3. 비정상 활동 패턴 분석
            activity_suspects = await _analyze_activity_pattern(db)
            suspicious_patterns.extend(activity_suspects)

    except Exception as e:
        logger.error(f"Deep analysis DB error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "suspicious_patterns": len(suspicious_patterns),
        "patterns": suspicious_patterns[:20],  # 상위 20개만
    }

    if suspicious_patterns:
        logger.warning(f"Deep analysis: {len(suspicious_patterns)}개 의심 패턴 발견")

    return result


async def _analyze_frequent_opponents(db: AsyncSession) -> list[dict]:
    """같은 테이블에서 자주 만나는 사용자 쌍 분석."""
    # 최근 7일간 핸드 히스토리에서 분석
    query = text("""
        WITH opponent_pairs AS (
            SELECT
                LEAST(hp1.user_id, hp2.user_id) as user1,
                GREATEST(hp1.user_id, hp2.user_id) as user2,
                COUNT(*) as hands_together,
                COUNT(DISTINCT hp1.hand_id) as unique_hands
            FROM hand_participants hp1
            JOIN hand_participants hp2
                ON hp1.hand_id = hp2.hand_id
                AND hp1.user_id < hp2.user_id
            JOIN hands h ON h.id = hp1.hand_id
            WHERE h.created_at > NOW() - INTERVAL '7 days'
            GROUP BY LEAST(hp1.user_id, hp2.user_id),
                     GREATEST(hp1.user_id, hp2.user_id)
            HAVING COUNT(*) > 50
        )
        SELECT user1, user2, hands_together
        FROM opponent_pairs
        WHERE hands_together > 100
        ORDER BY hands_together DESC
        LIMIT 20
    """)

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        suspects = []
        for row in rows:
            suspects.append({
                "type": "frequent_opponents",
                "user1": str(row.user1),
                "user2": str(row.user2),
                "hands_together": row.hands_together,
                "risk_level": "high" if row.hands_together > 200 else "medium",
            })

        return suspects

    except Exception as e:
        logger.debug(f"Frequent opponents analysis skipped: {e}")
        return []


async def _analyze_abnormal_winrate(db: AsyncSession) -> list[dict]:
    """특정 상대에 대한 비정상 승률 분석."""
    query = text("""
        WITH user_vs_user AS (
            SELECT
                hp1.user_id as user_id,
                hp2.user_id as opponent_id,
                SUM(CASE WHEN hp1.won_amount > 0 THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total_hands,
                SUM(hp1.won_amount) as total_won,
                SUM(hp1.bet_amount) as total_bet
            FROM hand_participants hp1
            JOIN hand_participants hp2
                ON hp1.hand_id = hp2.hand_id
                AND hp1.user_id != hp2.user_id
            JOIN hands h ON h.id = hp1.hand_id
            WHERE h.created_at > NOW() - INTERVAL '30 days'
            GROUP BY hp1.user_id, hp2.user_id
            HAVING COUNT(*) >= 20
        )
        SELECT
            user_id,
            opponent_id,
            wins,
            total_hands,
            ROUND(wins::numeric / total_hands * 100, 2) as winrate,
            total_won,
            total_bet
        FROM user_vs_user
        WHERE (wins::numeric / total_hands) >= 0.75
           OR (wins::numeric / total_hands) <= 0.15
        ORDER BY total_hands DESC
        LIMIT 20
    """)

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        suspects = []
        for row in rows:
            winrate = float(row.winrate)
            suspects.append({
                "type": "abnormal_winrate",
                "user_id": str(row.user_id),
                "opponent_id": str(row.opponent_id),
                "winrate": winrate,
                "total_hands": row.total_hands,
                "risk_level": "high" if winrate >= 85 or winrate <= 10 else "medium",
                "pattern": "always_wins" if winrate >= 75 else "always_loses",
            })

        return suspects

    except Exception as e:
        logger.debug(f"Winrate analysis skipped: {e}")
        return []


async def _analyze_activity_pattern(db: AsyncSession) -> list[dict]:
    """활동 패턴 분석 (봇 의심)."""
    # 24시간 연속 활동, 새벽 시간대 집중 활동 등
    query = text("""
        WITH hourly_activity AS (
            SELECT
                user_id,
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as actions
            FROM hand_participants hp
            JOIN hands h ON h.id = hp.hand_id
            WHERE h.created_at > NOW() - INTERVAL '7 days'
            GROUP BY user_id, EXTRACT(HOUR FROM created_at)
        ),
        user_activity_stats AS (
            SELECT
                user_id,
                COUNT(DISTINCT hour) as active_hours,
                SUM(CASE WHEN hour BETWEEN 2 AND 6 THEN actions ELSE 0 END) as night_actions,
                SUM(actions) as total_actions
            FROM hourly_activity
            GROUP BY user_id
            HAVING SUM(actions) >= 100
        )
        SELECT
            user_id,
            active_hours,
            night_actions,
            total_actions,
            ROUND(night_actions::numeric / NULLIF(total_actions, 0) * 100, 2) as night_ratio
        FROM user_activity_stats
        WHERE active_hours >= 20
           OR (night_actions::numeric / NULLIF(total_actions, 0)) >= 0.4
        ORDER BY total_actions DESC
        LIMIT 20
    """)

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        suspects = []
        for row in rows:
            night_ratio = float(row.night_ratio) if row.night_ratio else 0
            suspects.append({
                "type": "suspicious_activity",
                "user_id": str(row.user_id),
                "active_hours": row.active_hours,
                "night_ratio": night_ratio,
                "total_actions": row.total_actions,
                "risk_level": "high" if row.active_hours >= 22 else "medium",
                "pattern": "24h_active" if row.active_hours >= 22 else "night_owl",
            })

        return suspects

    except Exception as e:
        logger.debug(f"Activity pattern analysis skipped: {e}")
        return []


@celery_app.task(
    name="app.tasks.fraud_detection.fraud_cleanup_task",
    bind=True,
    max_retries=2,
)
def fraud_cleanup_task(self) -> dict[str, Any]:
    """오래된 부정행위 데이터 정리 태스크 (매일 4시).

    메모리에 축적된 오래된 데이터를 정리합니다.

    Returns:
        정리 결과 요약
    """
    try:
        result = asyncio.run(_run_cleanup())
        return result

    except Exception as exc:
        logger.error(f"Fraud cleanup failed: {exc}")
        raise self.retry(exc=exc)


async def _run_cleanup() -> dict[str, Any]:
    """정리 로직."""
    from app.services.fraud_auto_blocker import get_fraud_blocker

    blocker = get_fraud_blocker()
    if not blocker:
        return {"status": "skipped", "reason": "blocker_not_initialized"}

    # 24시간 이상 된 낮은 점수 데이터 정리
    cleaned = await blocker.cleanup_old_data(max_age_hours=24)

    # IP 추적 데이터 정리 (72시간 이상)
    old_ips = [
        ip for ip, users in blocker._ip_to_users.items()
        if len(users) == 0
    ]
    for ip in old_ips:
        del blocker._ip_to_users[ip]

    result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cleaned_scores": cleaned,
        "cleaned_ips": len(old_ips),
    }

    logger.info(f"Fraud cleanup 완료: 점수 {cleaned}개, IP {len(old_ips)}개 정리")

    return result


@celery_app.task(name="app.tasks.fraud_detection.process_fraud_block_event")
def process_fraud_block_event(event_data: dict) -> dict[str, Any]:
    """부정행위 차단 이벤트 처리 (Redis에서 수신).

    admin-backend에서 차단 승인 후 실제 DB 차단을 수행합니다.

    Args:
        event_data: 차단 이벤트 데이터

    Returns:
        처리 결과
    """
    try:
        result = asyncio.run(_process_block(event_data))
        return result

    except Exception as exc:
        logger.error(f"Process fraud block failed: {exc}")
        return {"status": "error", "error": str(exc)}


async def _process_block(event_data: dict) -> dict[str, Any]:
    """실제 차단 처리."""
    from app.utils.db import async_session_factory
    from app.services.fraud_auto_blocker import BlockReason, get_fraud_blocker

    user_id = event_data.get("user_id")
    reason_str = event_data.get("block_reason", "")
    evidence = event_data.get("evidence", [])

    if not user_id:
        return {"status": "error", "error": "user_id required"}

    # 문자열을 enum으로 변환
    try:
        reason = BlockReason(reason_str)
    except ValueError:
        reason = BlockReason.MANUAL_ADMIN

    blocker = get_fraud_blocker()
    if not blocker:
        return {"status": "error", "error": "blocker_not_initialized"}

    async with async_session_factory() as db:
        success = await blocker.block_user_db(
            db=db,
            user_id=user_id,
            reason=reason,
            evidence=evidence,
        )
        await db.commit()

    return {
        "status": "success" if success else "failed",
        "user_id": user_id,
        "reason": reason.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
