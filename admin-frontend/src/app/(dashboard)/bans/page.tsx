'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { api } from '@/lib/api';

interface Ban {
  id: string;
  user_id: string;
  username: string;
  ban_type: string;
  reason: string;
  expires_at: string | null;
  created_by: string;
  created_at: string;
  lifted_at: string | null;
  lifted_by: string | null;
}

interface PaginatedBans {
  items: Ban[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function BansPage() {
  const [bans, setBans] = useState<PaginatedBans | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [page, setPage] = useState(1);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [liftingBanId, setLiftingBanId] = useState<string | null>(null);

  // Create ban form state
  const [newBan, setNewBan] = useState({
    user_id: '',
    ban_type: 'temporary',
    reason: '',
    duration_hours: 24,
  });

  const fetchBans = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
      });
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      const response = await api.get(`/bans?${params}`) as { data: PaginatedBans };
      setBans(response.data);
    } catch (error) {
      console.error('Failed to fetch bans:', error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => {
    fetchBans();
  }, [fetchBans]);

  const handleCreateBan = async () => {
    try {
      await api.post('/bans', {
        user_id: newBan.user_id,
        ban_type: newBan.ban_type,
        reason: newBan.reason,
        duration_hours: newBan.ban_type === 'temporary' ? newBan.duration_hours : null,
      });
      setCreateDialogOpen(false);
      setNewBan({ user_id: '', ban_type: 'temporary', reason: '', duration_hours: 24 });
      fetchBans();
    } catch (error) {
      console.error('Failed to create ban:', error);
    }
  };

  const handleLiftBan = async (banId: string) => {
    setLiftingBanId(banId);
    try {
      await api.delete(`/bans/${banId}`);
      fetchBans();
    } catch (error) {
      console.error('Failed to lift ban:', error);
    } finally {
      setLiftingBanId(null);
    }
  };

  const getBanTypeLabel = (type: string) => {
    switch (type) {
      case 'permanent': return '영구 제재';
      case 'temporary': return '임시 제재';
      case 'chat_only': return '채팅 금지';
      default: return type;
    }
  };

  const getBanStatus = (ban: Ban) => {
    if (ban.lifted_at) {
      return { label: '해제됨', color: 'bg-gray-100 text-gray-700' };
    }
    if (ban.expires_at && new Date(ban.expires_at) < new Date()) {
      return { label: '만료됨', color: 'bg-yellow-100 text-yellow-700' };
    }
    return { label: '활성', color: 'bg-red-100 text-red-700' };
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">제재 관리</h1>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>새 제재</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>새 제재 생성</DialogTitle>
              <DialogDescription>
                사용자에게 제재를 적용합니다.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="user_id">사용자 ID</Label>
                <Input
                  id="user_id"
                  value={newBan.user_id}
                  onChange={(e) => setNewBan({ ...newBan, user_id: e.target.value })}
                  placeholder="사용자 ID 입력"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ban_type">제재 유형</Label>
                <Select
                  value={newBan.ban_type}
                  onValueChange={(value) => setNewBan({ ...newBan, ban_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="temporary">임시 제재</SelectItem>
                    <SelectItem value="permanent">영구 제재</SelectItem>
                    <SelectItem value="chat_only">채팅 금지</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {newBan.ban_type === 'temporary' && (
                <div className="space-y-2">
                  <Label htmlFor="duration">기간 (시간)</Label>
                  <Input
                    id="duration"
                    type="number"
                    value={newBan.duration_hours}
                    onChange={(e) => setNewBan({ ...newBan, duration_hours: parseInt(e.target.value) || 24 })}
                    min={1}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="reason">사유</Label>
                <Textarea
                  id="reason"
                  value={newBan.reason}
                  onChange={(e) => setNewBan({ ...newBan, reason: e.target.value })}
                  placeholder="제재 사유를 입력하세요"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreateBan} disabled={!newBan.user_id || !newBan.reason}>
                제재 적용
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="상태" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체</SelectItem>
                <SelectItem value="active">활성</SelectItem>
                <SelectItem value="expired">만료됨</SelectItem>
                <SelectItem value="lifted">해제됨</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Bans Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            제재 목록 {bans && `(${bans.total}건)`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>사용자</TableHead>
                    <TableHead>유형</TableHead>
                    <TableHead>사유</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>만료일</TableHead>
                    <TableHead>생성일</TableHead>
                    <TableHead>작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bans?.items.map((ban) => {
                    const status = getBanStatus(ban);
                    return (
                      <TableRow key={ban.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{ban.username}</p>
                            <p className="text-xs text-gray-500 font-mono">
                              {ban.user_id.slice(0, 8)}...
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{getBanTypeLabel(ban.ban_type)}</TableCell>
                        <TableCell className="max-w-xs truncate">{ban.reason}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs ${status.color}`}>
                            {status.label}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {ban.expires_at
                            ? new Date(ban.expires_at).toLocaleString('ko-KR')
                            : '영구'}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {ban.created_at
                            ? new Date(ban.created_at).toLocaleDateString('ko-KR')
                            : '-'}
                        </TableCell>
                        <TableCell>
                          {!ban.lifted_at && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleLiftBan(ban.id)}
                              disabled={liftingBanId === ban.id}
                            >
                              {liftingBanId === ban.id ? '처리 중...' : '해제'}
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {bans?.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        제재 기록이 없습니다
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              {bans && bans.total_pages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    이전
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    {page} / {bans.total_pages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === bans.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    다음
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
