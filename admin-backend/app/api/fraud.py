"""
Fraud Monitoring API - 부정 행위 모니터링 엔드포인트

Provides endpoints for:
- Listing suspicious activities
- Getting fraud detection statistics
- Updating suspicious activity status
"""
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import json
import uuid

from fastapi import APIRouter, Query, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db, get_main_db
from app.utils.dependencies import require_operator
from app.models.admin_user import AdminUser
from app.services.audit_service import AuditService


router = APIRouter()


# ============================================================================
# Enums and Models
# ============================================================================

class SuspiciousActivityStatus(str, Enum):
    """Suspicious activity status."""
    PENDING = "pending"
    REVIEWING = "reviewing"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class SeverityLevel(str, Enum):
    """Severity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SuspiciousActivityResponse(BaseModel):
    """Suspicious activity response."""
    id: str
    detection_type: str
    user_ids: list[str]
    details: dict
    severity: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    reviewed_by: Optional[str] = None


class PaginatedSuspiciousActivities(BaseModel):
    """Paginated suspicious activities response."""
    items: list[SuspiciousActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FraudStatisticsResponse(BaseModel):
    """Fraud detection statistics response."""
    total_suspicious: int
    pending_count: int
    confirmed_count: int
    dismissed_count: int
    by_detection_type: dict[str, int]
    by_severity: dict[str, int]
    recent_24h: int
    recent_7d: int


class UpdateStatusRequest(BaseModel):
    """Request body for updating suspicious activity status."""
    status: SuspiciousActivityStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, max_length=1000, description="Review notes")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/suspicious", response_model=PaginatedSuspiciousActivities)
async def list_suspicious_activities(
    status: Optional[SuspiciousActivityStatus] = Query(None, description="Filter by status"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity"),
    detection_type: Optional[str] = Query(None, description="Filter by detection type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    """
    List suspicious activities with optional filters.
    
    **Validates: Requirements 7.1**
    """
    params = {"limit": page_size, "offset": (page - 1) * page_size}
    where_clauses = []
    
    if status:
        where_clauses.append("status = :status")
        params["status"] = status.value
    
    if severity:
        where_clauses.append("severity = :severity")
        params["severity"] = severity.value
    
    if detection_type:
        where_clauses.append("detection_type = :detection_type")
        params["detection_type"] = detection_type
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    try:
        # Count total
        count_query = text(f"SELECT COUNT(*) FROM suspicious_activities WHERE {where_sql}")
        count_result = await admin_db.execute(count_query, params)
        total = count_result.scalar() or 0
        
        # Get items
        list_query = text(f"""
            SELECT id, detection_type, user_ids, details, severity, status, 
                   created_at, updated_at, reviewed_by
            FROM suspicious_activities
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await admin_db.execute(list_query, params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            details = row.details
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    details = {"raw": details}
            
            user_ids = row.user_ids
            if isinstance(user_ids, str):
                try:
                    user_ids = json.loads(user_ids)
                except json.JSONDecodeError:
                    user_ids = [user_ids]
            
            items.append(SuspiciousActivityResponse(
                id=row.id,
                detection_type=row.detection_type,
                user_ids=user_ids if isinstance(user_ids, list) else [str(user_ids)],
                details=details if isinstance(details, dict) else {"raw": str(details)},
                severity=row.severity,
                status=row.status,
                created_at=row.created_at.isoformat() if row.created_at else "",
                updated_at=row.updated_at.isoformat() if row.updated_at else None,
                reviewed_by=row.reviewed_by,
            ))
        
        return PaginatedSuspiciousActivities(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list suspicious activities: {str(e)}"
        )


@router.get("/statistics", response_model=FraudStatisticsResponse)
async def get_fraud_statistics(
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    """
    Get fraud detection statistics.
    
    **Validates: Requirements 7.2**
    """
    try:
        # Total counts by status
        status_query = text("""
            SELECT status, COUNT(*) as count
            FROM suspicious_activities
            GROUP BY status
        """)
        status_result = await admin_db.execute(status_query)
        status_rows = status_result.fetchall()
        
        status_counts = {row.status: row.count for row in status_rows}
        total = sum(status_counts.values())
        
        # Counts by detection type
        type_query = text("""
            SELECT detection_type, COUNT(*) as count
            FROM suspicious_activities
            GROUP BY detection_type
        """)
        type_result = await admin_db.execute(type_query)
        type_rows = type_result.fetchall()
        by_detection_type = {row.detection_type: row.count for row in type_rows}
        
        # Counts by severity
        severity_query = text("""
            SELECT severity, COUNT(*) as count
            FROM suspicious_activities
            GROUP BY severity
        """)
        severity_result = await admin_db.execute(severity_query)
        severity_rows = severity_result.fetchall()
        by_severity = {row.severity: row.count for row in severity_rows}
        
        # Recent counts
        now = datetime.now(timezone.utc)
        
        recent_24h_query = text("""
            SELECT COUNT(*) FROM suspicious_activities
            WHERE created_at >= :since_24h
        """)
        recent_24h_result = await admin_db.execute(
            recent_24h_query,
            {"since_24h": now.replace(hour=now.hour - 24 if now.hour >= 24 else 0)}
        )
        recent_24h = recent_24h_result.scalar() or 0
        
        recent_7d_query = text("""
            SELECT COUNT(*) FROM suspicious_activities
            WHERE created_at >= :since_7d
        """)
        from datetime import timedelta
        recent_7d_result = await admin_db.execute(
            recent_7d_query,
            {"since_7d": now - timedelta(days=7)}
        )
        recent_7d = recent_7d_result.scalar() or 0
        
        return FraudStatisticsResponse(
            total_suspicious=total,
            pending_count=status_counts.get("pending", 0),
            confirmed_count=status_counts.get("confirmed", 0),
            dismissed_count=status_counts.get("dismissed", 0),
            by_detection_type=by_detection_type,
            by_severity=by_severity,
            recent_24h=recent_24h,
            recent_7d=recent_7d,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fraud statistics: {str(e)}"
        )


@router.patch("/suspicious/{activity_id}", response_model=SuspiciousActivityResponse)
async def update_suspicious_activity_status(
    activity_id: str,
    request: UpdateStatusRequest,
    req: Request,
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    """
    Update suspicious activity status.
    
    **Validates: Requirements 7.4**
    """
    try:
        # Check if activity exists
        check_query = text("""
            SELECT id, detection_type, user_ids, details, severity, status, created_at
            FROM suspicious_activities
            WHERE id = :id
        """)
        check_result = await admin_db.execute(check_query, {"id": activity_id})
        existing = check_result.fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Suspicious activity {activity_id} not found"
            )
        
        # Update status
        now = datetime.now(timezone.utc)
        update_query = text("""
            UPDATE suspicious_activities
            SET status = :status, updated_at = :updated_at, reviewed_by = :reviewed_by
            WHERE id = :id
        """)
        await admin_db.execute(update_query, {
            "id": activity_id,
            "status": request.status.value,
            "updated_at": now,
            "reviewed_by": str(current_user.id),
        })
        await admin_db.commit()
        
        # Log audit
        audit_service = AuditService(admin_db)
        await audit_service.log_action(
            admin_user_id=str(current_user.id),
            admin_username=current_user.username,
            action="update_suspicious_activity",
            target_type="suspicious_activity",
            target_id=activity_id,
            details={
                "old_status": existing.status,
                "new_status": request.status.value,
                "notes": request.notes,
            },
            ip_address=req.client.host if req.client else None,
        )
        
        # Parse details
        details = existing.details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {"raw": details}
        
        user_ids = existing.user_ids
        if isinstance(user_ids, str):
            try:
                user_ids = json.loads(user_ids)
            except json.JSONDecodeError:
                user_ids = [user_ids]
        
        return SuspiciousActivityResponse(
            id=existing.id,
            detection_type=existing.detection_type,
            user_ids=user_ids if isinstance(user_ids, list) else [str(user_ids)],
            details=details if isinstance(details, dict) else {"raw": str(details)},
            severity=existing.severity,
            status=request.status.value,
            created_at=existing.created_at.isoformat() if existing.created_at else "",
            updated_at=now.isoformat(),
            reviewed_by=str(current_user.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update suspicious activity: {str(e)}"
        )


@router.get("/suspicious/{activity_id}", response_model=SuspiciousActivityResponse)
async def get_suspicious_activity(
    activity_id: str,
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    """
    Get a specific suspicious activity by ID.
    """
    try:
        query = text("""
            SELECT id, detection_type, user_ids, details, severity, status, 
                   created_at, updated_at, reviewed_by
            FROM suspicious_activities
            WHERE id = :id
        """)
        result = await admin_db.execute(query, {"id": activity_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Suspicious activity {activity_id} not found"
            )
        
        details = row.details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {"raw": details}
        
        user_ids = row.user_ids
        if isinstance(user_ids, str):
            try:
                user_ids = json.loads(user_ids)
            except json.JSONDecodeError:
                user_ids = [user_ids]
        
        return SuspiciousActivityResponse(
            id=row.id,
            detection_type=row.detection_type,
            user_ids=user_ids if isinstance(user_ids, list) else [str(user_ids)],
            details=details if isinstance(details, dict) else {"raw": str(details)},
            severity=row.severity,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
            reviewed_by=row.reviewed_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suspicious activity: {str(e)}"
        )
