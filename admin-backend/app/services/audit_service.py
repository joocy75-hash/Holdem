"""
Audit Service - 감사 로그 관리 서비스
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import json

logger = logging.getLogger(__name__)


class AuditServiceError(Exception):
    """Exception raised for audit service errors."""
    pass


class AuditService:
    """감사 로그 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        admin_user_id: str,
        admin_username: str,
        action: str,
        target_type: str,
        target_id: str,
        details: dict,
        ip_address: Optional[str] = None
    ) -> dict:
        """
        관리자 액션 기록
        
        Args:
            admin_user_id: 관리자 ID
            admin_username: 관리자 사용자명
            action: 액션 유형 (create_ban, lift_ban, update_user, etc.)
            target_type: 대상 유형 (user, ban, room, etc.)
            target_id: 대상 ID
            details: 추가 상세 정보
            ip_address: 요청 IP 주소
        
        Returns:
            생성된 감사 로그
        """
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        try:
            query = text("""
                INSERT INTO audit_logs 
                (id, admin_user_id, admin_username, action, target_type, target_id, details, ip_address, created_at)
                VALUES (:id, :admin_user_id, :admin_username, :action, :target_type, :target_id, :details, :ip_address, :created_at)
            """)
            await self.db.execute(query, {
                "id": log_id,
                "admin_user_id": admin_user_id,
                "admin_username": admin_username,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "details": json.dumps(details),
                "ip_address": ip_address,
                "created_at": now
            })
            await self.db.commit()
            
            return {
                "id": log_id,
                "admin_user_id": admin_user_id,
                "admin_username": admin_username,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "details": details,
                "ip_address": ip_address,
                "created_at": now.isoformat()
            }
        except Exception as e:
            # 감사 로그 실패는 주요 작업을 중단시키지 않음
            # 하지만 반드시 로깅하여 추적 가능하게 함
            logger.error(
                f"Failed to log audit action: action={action}, "
                f"admin_user_id={admin_user_id}, target_type={target_type}, "
                f"target_id={target_id}, error={e}",
                exc_info=True
            )
            return {
                "id": log_id,
                "admin_user_id": admin_user_id,
                "admin_username": admin_username,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "details": details,
                "ip_address": ip_address,
                "created_at": now.isoformat(),
                "error": str(e)
            }
    
    async def list_logs(
        self,
        action: Optional[str] = None,
        admin_user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        감사 로그 목록 조회
        
        Args:
            action: 액션 유형 필터
            admin_user_id: 관리자 ID 필터
            target_type: 대상 유형 필터
            page: 페이지 번호
            page_size: 페이지 크기
        
        Returns:
            페이지네이션된 감사 로그 목록
        """
        offset = (page - 1) * page_size
        params = {"limit": page_size, "offset": offset}
        
        where_clauses = []
        
        if action:
            where_clauses.append("action = :action")
            params["action"] = action
        
        if admin_user_id:
            where_clauses.append("admin_user_id = :admin_user_id")
            params["admin_user_id"] = admin_user_id
        
        if target_type:
            where_clauses.append("target_type = :target_type")
            params["target_type"] = target_type
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        try:
            # 총 개수 조회
            count_query = text(f"SELECT COUNT(*) FROM audit_logs WHERE {where_sql}")
            count_result = await self.db.execute(count_query, params)
            total = count_result.scalar() or 0
            
            # 로그 목록 조회
            list_query = text(f"""
                SELECT id, admin_user_id, admin_username, action, 
                       target_type, target_id, details, ip_address, created_at
                FROM audit_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            result = await self.db.execute(list_query, params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                details = row.details
                if isinstance(details, str):
                    try:
                        details = json.loads(details)
                    except json.JSONDecodeError:
                        details = {}
                
                items.append({
                    "id": row.id,
                    "admin_user_id": row.admin_user_id,
                    "admin_username": row.admin_username,
                    "action": row.action,
                    "target_type": row.target_type,
                    "target_id": row.target_id,
                    "details": details,
                    "ip_address": row.ip_address,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Failed to list audit logs: {e}", exc_info=True)
            raise AuditServiceError(f"Failed to list audit logs: {e}") from e
    
    async def get_user_activity(self, admin_user_id: str, limit: int = 50) -> list:
        """특정 관리자의 최근 활동 조회"""
        try:
            query = text("""
                SELECT id, action, target_type, target_id, details, ip_address, created_at
                FROM audit_logs
                WHERE admin_user_id = :admin_user_id
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            result = await self.db.execute(query, {
                "admin_user_id": admin_user_id,
                "limit": limit
            })
            rows = result.fetchall()
            
            items = []
            for row in rows:
                details = row.details
                if isinstance(details, str):
                    try:
                        details = json.loads(details)
                    except json.JSONDecodeError:
                        details = {}
                
                items.append({
                    "id": row.id,
                    "action": row.action,
                    "target_type": row.target_type,
                    "target_id": row.target_id,
                    "details": details,
                    "ip_address": row.ip_address,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })
            
            return items
        except Exception as e:
            logger.error(f"Failed to get user activity for admin {admin_user_id}: {e}", exc_info=True)
            raise AuditServiceError(f"Failed to get user activity: {e}") from e
