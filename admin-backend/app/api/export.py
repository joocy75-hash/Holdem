"""보고서 내보내기 API.

Excel 및 PDF 형식으로 데이터를 내보냅니다.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db, get_main_db
from app.models.admin_user import AdminUser
from app.services.export_service import (
    ExportService,
    export_users_report,
    export_transactions_report,
    export_audit_report,
    export_revenue_report,
)
from app.utils.dependencies import require_admin

router = APIRouter()


class ExportFormat(str, Enum):
    """내보내기 형식."""
    EXCEL = "excel"
    PDF = "pdf"


def _get_content_type(format: ExportFormat) -> str:
    """형식에 따른 Content-Type 반환."""
    if format == ExportFormat.EXCEL:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/pdf"


def _get_filename(report_type: str, format: ExportFormat) -> str:
    """파일명 생성."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = "xlsx" if format == ExportFormat.EXCEL else "pdf"
    return f"{report_type}_{timestamp}.{ext}"


@router.get("/users")
async def export_users(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="내보내기 형식"),
    is_active: bool | None = Query(None, description="활성 상태 필터"),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_main_db),
):
    """사용자 목록 내보내기."""
    # 사용자 데이터 조회
    query = text("""
        SELECT id, nickname, email, chips, is_active, 
               created_at, last_login
        FROM users
        WHERE (:is_active IS NULL OR is_active = :is_active)
        ORDER BY created_at DESC
        LIMIT 10000
    """)
    result = await db.execute(query, {"is_active": is_active})
    users = [
        {
            "id": str(row.id)[:8] + "...",
            "nickname": row.nickname,
            "email": row.email,
            "chips": row.chips,
            "is_active": "Y" if row.is_active else "N",
            "created_at": row.created_at,
            "last_login": row.last_login,
        }
        for row in result.fetchall()
    ]

    data = await export_users_report(users, format.value)

    return StreamingResponse(
        iter([data]),
        media_type=_get_content_type(format),
        headers={
            "Content-Disposition": f"attachment; filename={_get_filename('users', format)}"
        },
    )


@router.get("/transactions")
async def export_transactions(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="내보내기 형식"),
    transaction_type: str | None = Query(None, description="거래 유형 필터"),
    status: str | None = Query(None, description="상태 필터"),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_main_db),
):
    """거래 내역 내보내기."""
    query = text("""
        SELECT id, user_id, type, amount, status, created_at
        FROM transactions
        WHERE (:type IS NULL OR type = :type)
          AND (:status IS NULL OR status = :status)
        ORDER BY created_at DESC
        LIMIT 10000
    """)
    result = await db.execute(query, {"type": transaction_type, "status": status})
    transactions = [
        {
            "id": str(row.id)[:8] + "...",
            "user_id": str(row.user_id)[:8] + "...",
            "type": row.type,
            "amount": row.amount,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in result.fetchall()
    ]

    data = await export_transactions_report(transactions, format.value)

    return StreamingResponse(
        iter([data]),
        media_type=_get_content_type(format),
        headers={
            "Content-Disposition": f"attachment; filename={_get_filename('transactions', format)}"
        },
    )


@router.get("/audit-logs")
async def export_audit_logs(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="내보내기 형식"),
    action: str | None = Query(None, description="액션 필터"),
    admin_user_id: str | None = Query(None, description="관리자 ID 필터"),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """감사 로그 내보내기."""
    query = text("""
        SELECT id, admin_username, action, target_type, target_id, 
               ip_address, created_at
        FROM audit_logs
        WHERE (:action IS NULL OR action = :action)
          AND (:admin_user_id IS NULL OR admin_user_id = :admin_user_id)
        ORDER BY created_at DESC
        LIMIT 10000
    """)
    result = await db.execute(query, {"action": action, "admin_user_id": admin_user_id})
    audit_logs = [
        {
            "id": str(row.id)[:8] + "...",
            "admin_username": row.admin_username,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": str(row.target_id)[:8] + "..." if row.target_id else "",
            "ip_address": row.ip_address,
            "created_at": row.created_at,
        }
        for row in result.fetchall()
    ]

    data = await export_audit_report(audit_logs, format.value)

    return StreamingResponse(
        iter([data]),
        media_type=_get_content_type(format),
        headers={
            "Content-Disposition": f"attachment; filename={_get_filename('audit_logs', format)}"
        },
    )


@router.get("/revenue")
async def export_revenue(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="내보내기 형식"),
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_main_db),
):
    """수익 보고서 내보내기."""
    query = text("""
        SELECT
            DATE(created_at) as date,
            SUM(rake_amount) as total_rake,
            COUNT(*) as total_hands,
            COUNT(DISTINCT player_id) as unique_players
        FROM hand_results
        WHERE created_at >= NOW() - INTERVAL ':days days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """.replace(":days", str(days)))

    try:
        result = await db.execute(query)
        revenue_data = [
            {
                "date": row.date.strftime("%Y-%m-%d") if row.date else "",
                "total_rake": row.total_rake or 0,
                "total_hands": row.total_hands or 0,
                "unique_players": row.unique_players or 0,
                "avg_rake_per_hand": round(
                    (row.total_rake or 0) / (row.total_hands or 1), 2
                ),
            }
            for row in result.fetchall()
        ]
    except Exception:
        # 테이블이 없거나 오류 시 빈 데이터
        revenue_data = []

    data = await export_revenue_report(revenue_data, format.value)

    return StreamingResponse(
        iter([data]),
        media_type=_get_content_type(format),
        headers={
            "Content-Disposition": f"attachment; filename={_get_filename('revenue', format)}"
        },
    )


@router.get("/custom")
async def export_custom(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="내보내기 형식"),
    table: str = Query(..., description="테이블명"),
    columns: str = Query(..., description="컬럼 목록 (콤마 구분)"),
    limit: int = Query(1000, ge=1, le=10000, description="최대 행 수"),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_main_db),
):
    """커스텀 내보내기 (관리자 전용).
    
    주의: SQL 인젝션 방지를 위해 허용된 테이블만 사용 가능.
    """
    allowed_tables = {"users", "transactions", "rooms", "hand_results"}

    if table not in allowed_tables:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table not allowed. Allowed: {allowed_tables}",
        )

    # 컬럼 파싱 및 검증 (간단한 알파벳, 언더스코어만 허용)
    import re
    column_list = [c.strip() for c in columns.split(",")]
    for col in column_list:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid column name: {col}",
            )

    safe_columns = ", ".join(column_list)
    query = text(f"SELECT {safe_columns} FROM {table} LIMIT :limit")
    result = await db.execute(query, {"limit": limit})
    rows = result.fetchall()

    # 데이터 변환
    data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(column_list):
            val = row[i]
            if isinstance(val, datetime):
                row_dict[col] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                row_dict[col] = str(val) if val is not None else ""
        data.append(row_dict)

    col_defs = [{"key": c, "header": c} for c in column_list]

    service = ExportService()
    if format == ExportFormat.PDF:
        file_data = await service.export_to_pdf(
            data=data,
            columns=col_defs,
            title=f"{table.upper()} Report",
            orientation="landscape",
        )
    else:
        file_data = await service.export_to_excel(
            data=data,
            columns=col_defs,
            sheet_name=table.capitalize(),
            title=f"{table.upper()} Report",
        )

    return StreamingResponse(
        iter([file_data]),
        media_type=_get_content_type(format),
        headers={
            "Content-Disposition": f"attachment; filename={_get_filename(table, format)}"
        },
    )
