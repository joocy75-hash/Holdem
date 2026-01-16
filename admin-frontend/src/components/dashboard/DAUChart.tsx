'use client';

import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { dashboardApi, DAUHistoryItem } from '@/lib/dashboard-api';

interface DAUChartProps {
  refreshInterval?: number; // ms
  days?: number;
}

export function DAUChart({ refreshInterval = 60000, days = 14 }: DAUChartProps) {
  const [data, setData] = useState<DAUHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDAU, setCurrentDAU] = useState(0);

  const fetchData = async () => {
    try {
      const [history, current] = await Promise.all([
        dashboardApi.getDAUHistory(days),
        dashboardApi.getDAU(),
      ]);
      setData(history);
      setCurrentDAU(current.dau);
    } catch (error) {
      console.error('Failed to fetch DAU data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, days]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DAU 추이</CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          <p className="text-gray-400">로딩 중...</p>
        </CardContent>
      </Card>
    );
  }

  // Format date for display
  const formattedData = data.map(item => ({
    ...item,
    displayDate: item.date.slice(5), // MM-DD format
  }));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>DAU 추이 ({days}일)</CardTitle>
        <span className="text-2xl font-bold text-green-600">
          {currentDAU.toLocaleString()}
        </span>
      </CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={formattedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="displayDate" 
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              formatter={(value) => [Number(value).toLocaleString(), 'DAU']}
              labelFormatter={(label) => `날짜: ${label}`}
            />
            <Bar
              dataKey="dau"
              fill="#22c55e"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
