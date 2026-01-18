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
import { useAuthStore } from '@/stores/authStore';
import { toast } from 'sonner';
import {
  BulkActionResultDialog,
  BulkActionResult,
  executeBulkAction,
} from '@/components/ui/bulk-action-result';
import { BansEmptyState } from '@/components/ui/empty-state';

// camelCase로 변환된 API 응답 인터페이스
interface Ban {
  id: string;
  userId: string;
  username: string;
  banType: string;
  reason: string;
  expiresAt: string | null;
  createdBy: string;
  createdAt: string;
  liftedAt: string | null;
  liftedBy: string | null;
}

interface PaginatedBans {
  items: Ban[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export default function BansPage() {
  const [bans, setBans] = useState<PaginatedBans | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [page, setPage] = useState(1);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [liftingBanId, setLiftingBanId] = useState<string | null>(null);

  // Bulk action state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState<BulkActionResult | null>(null);
  const [bulkResultOpen, setBulkResultOpen] = useState(false);

  const getToken = () => useAuthStore.getState().accessToken || undefined;

  // Create ban form state
  const [newBan, setNewBan] = useState({
    userId: '',
    banType: 'temporary',
    reason: '',
    durationHours: 24,
  });

  // Bulk selection handlers
  const toggleSelectAll = () => {
    if (!bans) return;
    const activeBans = bans.items.filter((ban) => !ban.liftedAt);
    if (selectedIds.size === activeBans.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(activeBans.map((ban) => ban.id)));
    }
  };

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  // Bulk unban handler
  const handleBulkUnban = async () => {
    if (selectedIds.size === 0) return;

    setBulkActionLoading(true);
    try {
      const banMap = new Map(bans?.items.map((b) => [b.id, b]) || []);
      
      const result = await executeBulkAction(
        Array.from(selectedIds),
        async (id) => {
          await api.delete(`/api/bans/${id}`, { token: getToken() });
          const ban = banMap.get(id);
          return { id, label: ban?.username || id };
        },
        {
          concurrency: 3,
          onProgress: (completed, total) => {
            // 진행 상황 표시 (optional)
          },
        }
      );

      setBulkResult(result);
      setBulkResultOpen(true);
      setSelectedIds(new Set());
      fetchBans();

      if (result.failed === 0) {
        toast.success(`${result.successful}개 제재가 해제되었습니다.`);
      } else if (result.successful > 0) {
        toast.warning(`${result.successful}개 성공, ${result.failed}개 실패`);
      } else {
        toast.error('모든 제재 해제가 실패했습니다.');
      }
    } catch (error) {
      console.error('Bulk unban failed:', error);
      toast.error('일괄 해제 중 오류가 발생했습니다.');
    } finally {
      setBulkActionLoading(false);
    }
  };

  // Retry failed items
  const handleRetryFailed = async (failedIds: string[]) => {
    setSelectedIds(new Set(failedIds));
    setBulkResultOpen(false);
    await handleBulkUnban();
  };

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
      const data = await api.get<PaginatedBans>(`/api/bans?${params}`, { token: getToken() });
      setBans(data);
    } catch (error) {
      console.error('Failed to fetch bans:', error);
      toast.error('제재 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => {
    fetchBans();
  }, [fetchBans]);

  const handleCreateBan = async () => {
    try {
      await api.post('/api/bans', {
        user_id: newBan.userId,
        ban_type: newBan.banType,
        reason: newBan.reason,
        duration_hours: newBan.banType === 'temporary' ? newBan.durationHours : null,
      }, { token: getToken() });
      setCreateDialogOpen(false);
      setNewBan({ userId: '', banType: 'temporary', reason: '', durationHours: 24 });
      toast.success('제재가 적용되었습니다.');
      fetchBans();
    } catch (error) {
      console.error('Failed to create ban:', error);
      toast.error('제재 적용에 실패했습니다.');
    }
  };

  const handleLiftBan = async (banId: string) => {
    setLiftingBanId(banId);
    try {
      await api.delete(`/api/bans/${banId}`, { token: getToken() });
      toast.success('제재가 해제되었습니다.');
      fetchBans();
    } catch (error) {
      console.error('Failed to lift ban:', error);
      toast.error('제재 해제에 실패했습니다.');
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
    if (ban.liftedAt) {
      return { label: '해제됨', color: 'bg-gray-100 text-gray-700' };
    }
    if (ban.expiresAt && new Date(ban.expiresAt) < new Date()) {
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
                <Label htmlFor="userId">사용자 ID</Label>
                <Input
                  id="userId"
                  value={newBan.userId}
                  onChange={(e) => setNewBan({ ...newBan, userId: e.target.value })}
                  placeholder="사용자 ID 입력"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="banType">제재 유형</Label>
                <Select
                  value={newBan.banType}
                  onValueChange={(value) => setNewBan({ ...newBan, banType: value })}
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
              {newBan.banType === 'temporary' && (
                <div className="space-y-2">
                  <Label htmlFor="duration">기간 (시간)</Label>
                  <Input
                    id="duration"
                    type="number"
                    value={newBan.durationHours}
                    onChange={(e) => setNewBan({ ...newBan, durationHours: parseInt(e.target.value) || 24 })}
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
              <Button onClick={handleCreateBan} disabled={!newBan.userId || !newBan.reason}>
                제재 적용
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters & Bulk Actions */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex justify-between items-center">
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
            
            {/* Bulk Action Buttons */}
            {selectedIds.size > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">
                  {selectedIds.size}개 선택됨
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedIds(new Set())}
                >
                  선택 해제
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBulkUnban}
                  disabled={bulkActionLoading}
                >
                  {bulkActionLoading ? '처리 중...' : '일괄 해제'}
                </Button>
              </div>
            )}
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
                    <TableHead className="w-10">
                      <input
                        type="checkbox"
                        checked={
                          bans?.items.filter((b) => !b.liftedAt).length === selectedIds.size &&
                          selectedIds.size > 0
                        }
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300"
                      />
                    </TableHead>
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
                    const isActive = !ban.liftedAt;
                    return (
                      <TableRow key={ban.id} className={selectedIds.has(ban.id) ? 'bg-blue-50' : ''}>
                        <TableCell>
                          {isActive && (
                            <input
                              type="checkbox"
                              checked={selectedIds.has(ban.id)}
                              onChange={() => toggleSelect(ban.id)}
                              className="rounded border-gray-300"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{ban.username}</p>
                            <p className="text-xs text-gray-500 font-mono">
                              {ban.userId.slice(0, 8)}...
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{getBanTypeLabel(ban.banType)}</TableCell>
                        <TableCell className="max-w-xs truncate">{ban.reason}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs ${status.color}`}>
                            {status.label}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {ban.expiresAt
                            ? new Date(ban.expiresAt).toLocaleString('ko-KR')
                            : '영구'}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {ban.createdAt
                            ? new Date(ban.createdAt).toLocaleDateString('ko-KR')
                            : '-'}
                        </TableCell>
                        <TableCell>
                          {isActive && (
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
                      <TableCell colSpan={8} className="p-0">
                        <BansEmptyState onCreate={() => setCreateDialogOpen(true)} />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              {bans && bans.totalPages > 1 && (
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
                    {page} / {bans.totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === bans.totalPages}
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

      {/* Bulk Action Result Dialog */}
      <BulkActionResultDialog
        open={bulkResultOpen}
        onClose={() => setBulkResultOpen(false)}
        title="일괄 제재 해제 결과"
        result={bulkResult}
        onRetry={handleRetryFailed}
      />
    </div>
  );
}
