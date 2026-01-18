"""통계 서비스 테스트."""

import pytest

from app.services.statistics import PlayerStats, StatisticsService


class TestPlayerStats:
    """PlayerStats 테스트."""

    def test_default_values(self):
        """기본값 확인."""
        stats = PlayerStats()
        assert stats.total_hands == 0
        assert stats.vpip == 0.0
        assert stats.pfr == 0.0
        assert stats.win_rate == 0.0

    def test_custom_values(self):
        """커스텀 값 설정."""
        stats = PlayerStats(
            total_hands=100,
            vpip=25.5,
            pfr=18.2,
            win_rate=12.3,
        )
        assert stats.total_hands == 100
        assert stats.vpip == 25.5
        assert stats.pfr == 18.2


class TestPlayStyleAnalysis:
    """플레이 스타일 분석 테스트."""

    def test_tag_style(self):
        """TAG (Tight-Aggressive) 스타일."""
        stats = PlayerStats(
            total_hands=100,
            vpip=20.0,  # < 25 (tight)
            pfr=18.0,   # > 15 (aggressive)
        )
        service = StatisticsService(None)  # type: ignore
        result = service._analyze_play_style(stats)
        
        assert result["style"] == "TAG"
        assert "타이트-어그레시브" in result["description"]
        assert result["emoji"] == "🦈"

    def test_lag_style(self):
        """LAG (Loose-Aggressive) 스타일."""
        stats = PlayerStats(
            total_hands=100,
            vpip=35.0,  # > 25 (loose)
            pfr=20.0,   # > 15 (aggressive)
        )
        service = StatisticsService(None)  # type: ignore
        result = service._analyze_play_style(stats)
        
        assert result["style"] == "LAG"
        assert "루즈-어그레시브" in result["description"]
        assert result["emoji"] == "🔥"

    def test_nit_style(self):
        """Nit (Tight-Passive) 스타일."""
        stats = PlayerStats(
            total_hands=100,
            vpip=15.0,  # < 25 (tight)
            pfr=8.0,    # < 15 (passive)
        )
        service = StatisticsService(None)  # type: ignore
        result = service._analyze_play_style(stats)
        
        assert result["style"] == "Nit"
        assert "타이트-패시브" in result["description"]
        assert result["emoji"] == "🐢"

    def test_calling_station_style(self):
        """Calling Station (Loose-Passive) 스타일."""
        stats = PlayerStats(
            total_hands=100,
            vpip=40.0,  # > 25 (loose)
            pfr=10.0,   # < 15 (passive)
        )
        service = StatisticsService(None)  # type: ignore
        result = service._analyze_play_style(stats)
        
        assert result["style"] == "Calling Station"
        assert "루즈-패시브" in result["description"]
        assert result["emoji"] == "🐟"

    def test_unknown_style_insufficient_hands(self):
        """핸드 수 부족 시 알 수 없음."""
        stats = PlayerStats(
            total_hands=30,  # < 50
            vpip=25.0,
            pfr=15.0,
        )
        service = StatisticsService(None)  # type: ignore
        result = service._analyze_play_style(stats)
        
        assert result["style"] == "unknown"
        assert "부족" in result["description"]


class TestStatsBoundaries:
    """경계값 테스트."""

    def test_vpip_boundary_at_25(self):
        """VPIP 25% 경계값."""
        service = StatisticsService(None)  # type: ignore

        # 정확히 25는 loose 아님
        stats_25 = PlayerStats(total_hands=100, vpip=25.0, pfr=20.0)
        result = service._analyze_play_style(stats_25)
        assert result["style"] == "TAG"

        # 25 초과는 loose
        stats_26 = PlayerStats(total_hands=100, vpip=26.0, pfr=20.0)
        result = service._analyze_play_style(stats_26)
        assert result["style"] == "LAG"

    def test_pfr_boundary_at_15(self):
        """PFR 15% 경계값."""
        service = StatisticsService(None)  # type: ignore

        # 정확히 15는 aggressive 아님
        stats_15 = PlayerStats(total_hands=100, vpip=20.0, pfr=15.0)
        result = service._analyze_play_style(stats_15)
        assert result["style"] == "Nit"

        # 15 초과는 aggressive
        stats_16 = PlayerStats(total_hands=100, vpip=20.0, pfr=16.0)
        result = service._analyze_play_style(stats_16)
        assert result["style"] == "TAG"

    def test_minimum_hands_boundary(self):
        """최소 핸드 수 경계값."""
        service = StatisticsService(None)  # type: ignore

        # 49핸드는 부족
        stats_49 = PlayerStats(total_hands=49, vpip=20.0, pfr=18.0)
        result = service._analyze_play_style(stats_49)
        assert result["style"] == "unknown"

        # 50핸드면 분석 가능
        stats_50 = PlayerStats(total_hands=50, vpip=20.0, pfr=18.0)
        result = service._analyze_play_style(stats_50)
        assert result["style"] == "TAG"


class TestStatsDataclass:
    """PlayerStats dataclass 테스트."""

    def test_all_fields_present(self):
        """모든 필드 존재 확인."""
        stats = PlayerStats()
        
        # 기본 정보
        assert hasattr(stats, 'total_hands')
        assert hasattr(stats, 'total_winnings')
        assert hasattr(stats, 'hands_won')
        assert hasattr(stats, 'biggest_pot')
        
        # 스타일 지표
        assert hasattr(stats, 'vpip')
        assert hasattr(stats, 'pfr')
        assert hasattr(stats, 'three_bet')
        
        # 공격성
        assert hasattr(stats, 'af')
        assert hasattr(stats, 'agg_freq')
        
        # 쇼다운
        assert hasattr(stats, 'wtsd')
        assert hasattr(stats, 'wsd')
        
        # 수익성
        assert hasattr(stats, 'win_rate')
        assert hasattr(stats, 'bb_per_100')

    def test_stats_are_numeric(self):
        """통계 값이 숫자 타입인지 확인."""
        stats = PlayerStats(
            total_hands=100,
            vpip=25.5,
            pfr=18.2,
            af=2.5,
        )
        
        assert isinstance(stats.total_hands, int)
        assert isinstance(stats.vpip, float)
        assert isinstance(stats.pfr, float)
        assert isinstance(stats.af, float)
