'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CCUChart, DAUChart, RevenueChart, ServerHealthCard, MetricCard } from '@/components/dashboard';
import { dashboardApi, DashboardSummary, ExchangeRateResponse } from '@/lib/dashboard-api';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';
import Link from 'next/link';

const navItems = [
  { href: '/', label: '대시보드', icon: '📊' },
  { href: '/users', label: '사용자', icon: '👥' },
  { href: '/rooms', label: '방 관리', icon: '🎮' },
  { href: '/hands', label: '핸드 기록', icon: '🃏' },
  { href: '/bans', label: '제재 관리', icon: '🚫' },
  { href: '/deposits', label: '입금 관리', icon: '📥' },
  { href: '/suspicious', label: '의심 사용자', icon: '⚠️' },
  { href: '/announcements', label: '공지사항', icon: '📢' },
];

interface AuthState {
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
  } | null;
  accessToken: string | null;
  isAuthenticated: boolean;
}

export default function Home() {
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [exchangeRate, setExchangeRate] = useState<ExchangeRateResponse | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [dataLoading, setDataLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = () => {
      try {
        const stored = localStorage.getItem('admin-auth');
        console.log('[Home] Checking auth, stored:', stored ? 'exists' : 'null');
        
        if (stored) {
          const parsed = JSON.parse(stored);
          console.log('[Home] Parsed auth state:', parsed.state?.isAuthenticated);
          
          if (parsed.state?.isAuthenticated && parsed.state?.accessToken) {
            console.log('[Home] Auth valid, showing dashboard');
            setAuthState(parsed.state);
            setIsLoading(false);
            return;
          }
        }
        
        console.log('[Home] Not authenticated, redirecting to login');
        router.replace('/login');
      } catch (e) {
        console.error('[Home] Error checking auth:', e);
        router.replace('/login');
      }
    };

    // Small delay to ensure localStorage is available
    const timer = setTimeout(checkAuth, 100);
    return () => clearTimeout(timer);
  }, [router]);

  // Time ticker
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    if (!authState?.isAuthenticated) return;

    const fetchSummary = async () => {
      try {
        const data = await dashboardApi.getSummary();
        setSummary(data);
      } catch (error) {
        console.error('Failed to fetch dashboard summary:', error);
      } finally {
        setDataLoading(false);
      }
    };

    fetchSummary();
    const interval = setInterval(fetchSummary, 5000);
    return () => clearInterval(interval);
  }, [authState?.isAuthenticated]);

  // Fetch exchange rate
  useEffect(() => {
    if (!authState?.isAuthenticated) return;

    const fetchExchangeRate = async () => {
      try {
        const data = await dashboardApi.getExchangeRate();
        setExchangeRate(data);
      } catch (error) {
        console.error('Failed to fetch exchange rate:', error);
      }
    };

    fetchExchangeRate();
    const interval = setInterval(fetchExchangeRate, 60000); // 1분마다 갱신
    return () => clearInterval(interval);
  }, [authState?.isAuthenticated]);

  const handleLogout = () => {
    localStorage.removeItem('admin-auth');
    router.replace('/login');
  };

  // Show loading screen while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    );
  }

  // Don't render if not authenticated (redirect already triggered)
  if (!authState?.isAuthenticated) {
    return null;
  }

  // Fallback data
  const displaySummary = summary || {
    ccu: 0,
    dau: 0,
    activeRooms: 0,
    totalPlayers: 0,
    serverHealth: {
      cpu: 0,
      memory: 0,
      latency: 0,
      status: 'unknown' as const,
    },
  };

  const displayRate = exchangeRate || {
    rate: 1400,
    source: 'currency-api',
    timestamp: new Date().toISOString(),
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md">
        <div className="p-4">
          <h1 className="text-xl font-bold text-gray-800">🎰 Admin</h1>
          <p className="text-sm text-gray-500">Holdem Management</p>
        </div>
        <Separator />
        <nav className="p-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100"
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
          <div />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {authState?.user?.username?.charAt(0).toUpperCase() || 'A'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm">{authState?.user?.username}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem disabled>
                역할: {authState?.user?.role}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>
                로그아웃
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">대시보드</h1>
              <p className="text-sm text-gray-500">
                {currentTime.toLocaleString('ko-KR')}
              </p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="동시 접속자 (CCU)"
                value={displaySummary.ccu}
                icon="👥"
              />
              <MetricCard
                title="일일 활성 사용자 (DAU)"
                value={displaySummary.dau}
                icon="📊"
              />
              <MetricCard
                title="활성 방"
                value={displaySummary.activeRooms}
                subtitle={`${displaySummary.totalPlayers}명 플레이 중`}
                icon="🎮"
              />
              <MetricCard
                title="USDT/KRW 환율"
                value={`₩${displayRate.rate.toLocaleString()}`}
                subtitle={`출처: ${displayRate.source}`}
                icon="💱"
              />
            </div>

            {/* Server Health */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <CCUChart refreshInterval={5000} />
              </div>
              <ServerHealthCard refreshInterval={10000} />
            </div>

            {/* DAU Chart */}
            <DAUChart refreshInterval={60000} days={14} />

            {/* Revenue Chart */}
            <RevenueChart />

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    오늘 핸드 수
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">-</p>
                  <p className="text-xs text-gray-400">통계 API 연동 후 표시</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    오늘 레이크
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">-</p>
                  <p className="text-xs text-gray-400">통계 API 연동 후 표시</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    대기 중 출금
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">-</p>
                  <p className="text-xs text-gray-400">암호화폐 API 연동 후 표시</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
