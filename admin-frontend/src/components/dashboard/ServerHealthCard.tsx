'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { dashboardApi, ServerHealth } from '@/lib/dashboard-api';
import { cn } from '@/lib/utils';

interface ServerHealthCardProps {
  refreshInterval?: number;
  onAlert?: (message: string, severity: 'warning' | 'critical') => void;
}

export function ServerHealthCard({ refreshInterval = 10000, onAlert }: ServerHealthCardProps) {
  const [health, setHealth] = useState<ServerHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertShown, setAlertShown] = useState<string | null>(null);

  const checkThresholds = useCallback((data: ServerHealth) => {
    const alerts: string[] = [];
    let severity: 'warning' | 'critical' = 'warning';

    if (data.cpu > 90) {
      alerts.push(`CPU 사용률 위험: ${data.cpu.toFixed(1)}%`);
      severity = 'critical';
    } else if (data.cpu > 70) {
      alerts.push(`CPU 사용률 주의: ${data.cpu.toFixed(1)}%`);
    }

    if (data.memory > 90) {
      alerts.push(`메모리 사용률 위험: ${data.memory.toFixed(1)}%`);
      severity = 'critical';
    } else if (data.memory > 70) {
      alerts.push(`메모리 사용률 주의: ${data.memory.toFixed(1)}%`);
    }

    if (data.latency > 500) {
      alerts.push(`레이턴시 위험: ${data.latency.toFixed(0)}ms`);
      severity = 'critical';
    } else if (data.latency > 200) {
      alerts.push(`레이턴시 주의: ${data.latency.toFixed(0)}ms`);
    }

    if (alerts.length > 0) {
      const alertKey = alerts.join('|');
      if (alertKey !== alertShown && onAlert) {
        onAlert(alerts.join(', '), severity);
        setAlertShown(alertKey);
      }
    } else {
      setAlertShown(null);
    }
  }, [alertShown, onAlert]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await dashboardApi.getServerHealth();
        setHealth(data);
        checkThresholds(data);
      } catch (error) {
        console.error('Failed to fetch server health:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, checkThresholds]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100 animate-pulse';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '정상';
      case 'warning':
        return '⚠️ 주의';
      case 'critical':
        return '🚨 위험';
      default:
        return '알 수 없음';
    }
  };

  const getProgressColor = (value: number) => {
    if (value > 90) return 'bg-red-500';
    if (value > 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getLatencyColor = (latency: number) => {
    if (latency > 500) return 'text-red-600 font-bold';
    if (latency > 200) return 'text-yellow-600';
    if (latency > 100) return 'text-yellow-500';
    return 'text-green-600';
  };

  if (loading || !health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>서버 상태</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <p className="text-gray-400">로딩 중...</p>
        </CardContent>
      </Card>
    );
  }

  const isCritical = health.status === 'critical';

  return (
    <Card className={cn(isCritical && 'border-red-500 border-2')}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>서버 상태</CardTitle>
        <span className={cn(
          'px-2 py-1 rounded-full text-xs font-medium',
          getStatusColor(health.status)
        )}>
          {getStatusText(health.status)}
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* CPU */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-500">CPU</span>
            <span className={cn(
              'font-medium',
              health.cpu > 90 ? 'text-red-600 font-bold' : 
              health.cpu > 70 ? 'text-yellow-600' : ''
            )}>
              {health.cpu.toFixed(1)}%
              {health.cpu > 90 && ' ⚠️'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn('h-2 rounded-full transition-all', getProgressColor(health.cpu))}
              style={{ width: `${Math.min(health.cpu, 100)}%` }}
            />
          </div>
        </div>

        {/* Memory */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-500">메모리</span>
            <span className={cn(
              'font-medium',
              health.memory > 90 ? 'text-red-600 font-bold' : 
              health.memory > 70 ? 'text-yellow-600' : ''
            )}>
              {health.memory.toFixed(1)}%
              {health.memory > 90 && ' ⚠️'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn('h-2 rounded-full transition-all', getProgressColor(health.memory))}
              style={{ width: `${Math.min(health.memory, 100)}%` }}
            />
          </div>
        </div>

        {/* Latency */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-500">레이턴시</span>
            <span className={cn('font-medium', getLatencyColor(health.latency))}>
              {health.latency.toFixed(0)}ms
              {health.latency > 500 && ' ⚠️'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1">
            <div
              className={cn(
                'h-1 rounded-full transition-all',
                health.latency > 500 ? 'bg-red-500' :
                health.latency > 200 ? 'bg-yellow-500' : 'bg-green-500'
              )}
              style={{ width: `${Math.min(health.latency / 10, 100)}%` }}
            />
          </div>
        </div>

        {/* Alert Banner */}
        {health.status === 'critical' && (
          <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
            🚨 서버 상태가 위험합니다. 즉시 확인이 필요합니다.
          </div>
        )}
        {health.status === 'warning' && (
          <div className="mt-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-xs text-yellow-700">
            ⚠️ 서버 리소스 사용량이 높습니다.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
