"""
Statistics API - 매출 및 게임 통계 엔드포인트
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_main_db
from app.utils.dependencies import require_viewer
from app.models.admin_user import AdminUser
from app.services.statistics_service import StatisticsService


router = APIRouter()


def parse_date(date_str: Optional[str], param_name: str) -> Optional[datetime]:
    """Parse date string with proper error handling.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        param_name: Parameter name for error message
        
    Returns:
        datetime object or None if date_str is None
        
    Raises:
        HTTPException: If date format is invalid
    """
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format for '{param_name}'. Expected YYYY-MM-DD, got '{date_str}'"
        )


# Response Models
class PeriodInfo(BaseModel):
    start: str
    end: str


class RevenueSummaryResponse(BaseModel):
    total_rake: float
    total_hands: int
    unique_rooms: int
    period: PeriodInfo


class DailyRevenueItem(BaseModel):
    date: str
    rake: float
    hands: int


class WeeklyRevenueItem(BaseModel):
    week_start: str
    rake: float
    hands: int


class MonthlyRevenueItem(BaseModel):
    month: str
    rake: float
    hands: int


class TopPlayerItem(BaseModel):
    user_id: str
    total_rake: float
    hands_played: int


class TodayStats(BaseModel):
    hands: int
    rake: float
    rooms: int


class TotalStats(BaseModel):
    hands: int
    rake: float


class GameStatisticsResponse(BaseModel):
    today: TodayStats
    total: TotalStats


class RoomStatisticsResponse(BaseModel):
    total_rooms: int
    active_rooms: int
    waiting_rooms: int
    closed_rooms: int


class PlayerDistributionItem(BaseModel):
    stake_level: str
    player_count: int
    room_count: int


class TodayActivity(BaseModel):
    active_players: int
    total_actions: int


class WeekActivity(BaseModel):
    active_players: int


class MonthActivity(BaseModel):
    active_players: int


class PlayerActivitySummaryResponse(BaseModel):
    today: TodayActivity
    week: WeekActivity
    month: MonthActivity


class HourlyActivityItem(BaseModel):
    hour: str
    unique_players: int
    total_hands: int


class StakeLevelStatsItem(BaseModel):
    stake_level: str
    total_hands: int
    total_rake: float
    avg_pot_size: float


# Endpoints
@router.get("/revenue/summary", response_model=RevenueSummaryResponse)
async def get_revenue_summary(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """매출 요약 조회"""
    service = StatisticsService(db)
    
    start = parse_date(start_date, "start_date")
    end = parse_date(end_date, "end_date")
    
    data = await service.get_revenue_summary(start, end)
    return RevenueSummaryResponse(
        total_rake=data["total_rake"],
        total_hands=data["total_hands"],
        unique_rooms=data["unique_rooms"],
        period=PeriodInfo(**data["period"])
    )


@router.get("/revenue/daily", response_model=list[DailyRevenueItem])
async def get_daily_revenue(
    days: int = Query(30, ge=1, le=365, description="조회 일수"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """일별 매출 조회"""
    service = StatisticsService(db)
    data = await service.get_daily_revenue(days)
    return [DailyRevenueItem(**item) for item in data]


@router.get("/revenue/weekly", response_model=list[WeeklyRevenueItem])
async def get_weekly_revenue(
    weeks: int = Query(12, ge=1, le=52, description="조회 주수"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """주별 매출 조회"""
    service = StatisticsService(db)
    data = await service.get_weekly_revenue(weeks)
    return [WeeklyRevenueItem(**item) for item in data]


@router.get("/revenue/monthly", response_model=list[MonthlyRevenueItem])
async def get_monthly_revenue(
    months: int = Query(12, ge=1, le=24, description="조회 월수"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """월별 매출 조회"""
    service = StatisticsService(db)
    data = await service.get_monthly_revenue(months)
    return [MonthlyRevenueItem(**item) for item in data]


@router.get("/top-players", response_model=list[TopPlayerItem])
async def get_top_players(
    limit: int = Query(10, ge=1, le=100, description="조회 수"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """레이크 기여 상위 플레이어 조회"""
    service = StatisticsService(db)
    data = await service.get_top_players_by_rake(limit)
    return [TopPlayerItem(**item) for item in data]


@router.get("/game", response_model=GameStatisticsResponse)
async def get_game_statistics(
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """게임 통계 요약 조회"""
    service = StatisticsService(db)
    data = await service.get_game_statistics()
    return GameStatisticsResponse(
        today=TodayStats(**data["today"]),
        total=TotalStats(**data["total"])
    )


@router.get("/rooms", response_model=RoomStatisticsResponse)
async def get_room_statistics(
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """방 통계 조회"""
    service = StatisticsService(db)
    data = await service.get_room_statistics()
    return RoomStatisticsResponse(**data)


@router.get("/players/distribution", response_model=list[PlayerDistributionItem])
async def get_player_distribution(
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """플레이어 분포 조회 (스테이크별)"""
    service = StatisticsService(db)
    data = await service.get_player_distribution()
    return [PlayerDistributionItem(**item) for item in data]


@router.get("/players/activity", response_model=PlayerActivitySummaryResponse)
async def get_player_activity_summary(
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """플레이어 활동 요약 조회"""
    service = StatisticsService(db)
    data = await service.get_player_activity_summary()
    return PlayerActivitySummaryResponse(
        today=TodayActivity(**data["today"]),
        week=WeekActivity(**data["week"]),
        month=MonthActivity(**data["month"])
    )


@router.get("/players/hourly", response_model=list[HourlyActivityItem])
async def get_hourly_player_activity(
    hours: int = Query(24, ge=1, le=168, description="조회 시간 범위"),
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """시간별 플레이어 활동 조회"""
    service = StatisticsService(db)
    data = await service.get_hourly_player_activity(hours)
    return [HourlyActivityItem(**item) for item in data]


@router.get("/stake-levels", response_model=list[StakeLevelStatsItem])
async def get_stake_level_statistics(
    current_user: AdminUser = Depends(require_viewer),
    db: AsyncSession = Depends(get_main_db),
):
    """스테이크 레벨별 통계 조회"""
    service = StatisticsService(db)
    data = await service.get_stake_level_statistics()
    return [StakeLevelStatsItem(**item) for item in data]
