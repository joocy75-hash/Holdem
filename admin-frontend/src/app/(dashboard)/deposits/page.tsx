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
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  depositsApi,
  DepositListItem,
  PaginatedDeposits,
  DepositStats,
  DepositDetail,
} from '@/lib/deposits-api';

type DepositStatus = 'pending' | 'confirmed' | 'expired' | 'cancelled';

const STATUS_LABELS: Record<DepositStatus, string> = {
  pending: '대기중',
  confirmed: '완료',
  expired: '만료',
  cancelled: '취소',
};

const STATUS_COLORS: Record<DepositStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-green-100 text-green-700',
  expired: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-700',
};

export default function DepositsPage() {
  const [deposits, setDeposits] = useState<PaginatedDeposits | null>(null);
  const [stats, setStats] = useState<DepositStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  
  // Modal states
  const [selectedDeposit, setSelectedDeposit] = useState<DepositDetail | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [txHash, setTxHash] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDeposits = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        status: statusFilter === 'all' ? undefined : statusFilter,
        page,
        pageSize: 20,
      };
      const data = await depositsApi.listDeposits(params);
      setDeposits(data);
    } catch (error) {
      console.error('Failed to fetch deposits:', error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await depositsApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  useEffect(() => {
    fetchDeposits();
    fetchStats();
  }, [fetchDeposits, fetchStats]);

  const handleRowClick = async (deposit: DepositListItem) => {
    try {
      const detail = await depositsApi.getDeposit(deposit.id);
      setSelectedDeposit(detail);
      setDetailModalOpen(true);
    } catch (error) {
      console.error('Failed to fetch deposit detail:', error);
    }
  };

  const handleApprove = async () => {
    if (!selectedDeposit || !txHash.trim()) return;
    
    setActionLoading(true);
    try {
      await depositsApi.approveDeposit(selectedDeposit.id, txHash.trim());
      setApproveModalOpen(false);
      setDetailModalOpen(false);
      setTxHash('');
      fetchDeposits();
      fetchStats();
    } catch (error) {
      console.error('Failed to approve deposit:', error);
      alert('승인 처리 중 오류가 발생했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedDeposit || !rejectReason.trim()) return;
    
    setActionLoading(true);
    try {
      await depositsApi.rejectDeposit(selectedDeposit.id, rejectReason.trim());
      setRejectModalOpen(false);
      setDetailModalOpen(false);
      setRejectReason('');
      fetchDeposits();
      fetchStats();
    } catch (error) {
      console.error('Failed to reject deposit:', error);
      alert('거부 처리 중 오류가 발생했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount: number, currency: string) => {
    if (currency === 'KRW') {
      return `₩${amount.toLocaleString()}`;
    }
    return `${amount.toFixed(2)} USDT`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">입금 관리</h1>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">대기중</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.totalPending}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">오늘 완료</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.todayConfirmedCount}</div>
              <div className="text-sm text-gray-500">{stats.todayConfirmedUsdt.toFixed(2)} USDT</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">총 완료</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalConfirmed}</div>
              <div className="text-sm text-gray-500">{stats.totalUsdtConfirmed.toFixed(2)} USDT</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">만료/취소</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">
                {stats.totalExpired + stats.totalCancelled}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="상태" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체</SelectItem>
                <SelectItem value="pending">대기중</SelectItem>
                <SelectItem value="confirmed">완료</SelectItem>
                <SelectItem value="expired">만료</SelectItem>
                <SelectItem value="cancelled">취소</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => { fetchDeposits(); fetchStats(); }}>
              새로고침
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Deposits Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            입금 요청 목록 {deposits && `(${deposits.total}건)`}
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
                    <TableHead>요청일시</TableHead>
                    <TableHead>사용자</TableHead>
                    <TableHead>메모</TableHead>
                    <TableHead className="text-right">요청금액 (KRW)</TableHead>
                    <TableHead className="text-right">USDT</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>만료시간</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deposits?.items.map((deposit) => (
                    <TableRow
                      key={deposit.id}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => handleRowClick(deposit)}
                    >
                      <TableCell className="text-sm">
                        {formatDate(deposit.createdAt)}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {deposit.userId.slice(0, 8)}...
                      </TableCell>
                      <TableCell className="font-mono text-xs text-blue-600">
                        {deposit.memo}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(deposit.requestedKrw, 'KRW')}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {deposit.calculatedUsdt.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[deposit.status]}`}>
                          {STATUS_LABELS[deposit.status]}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {formatDate(deposit.expiresAt)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {deposits?.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        입금 요청이 없습니다
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              {deposits && deposits.totalPages > 1 && (
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
                    {page} / {deposits.totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === deposits.totalPages}
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

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>입금 요청 상세</DialogTitle>
          </DialogHeader>
          {selectedDeposit && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-gray-500">요청 ID</Label>
                  <div className="font-mono text-xs">{selectedDeposit.id}</div>
                </div>
                <div>
                  <Label className="text-gray-500">상태</Label>
                  <div>
                    <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[selectedDeposit.status]}`}>
                      {STATUS_LABELS[selectedDeposit.status]}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-gray-500">사용자 ID</Label>
                  <div className="font-mono text-xs">{selectedDeposit.userId}</div>
                </div>
                <div>
                  <Label className="text-gray-500">Telegram ID</Label>
                  <div>{selectedDeposit.telegramId || '-'}</div>
                </div>
                <div>
                  <Label className="text-gray-500">요청금액</Label>
                  <div className="font-medium">{formatCurrency(selectedDeposit.requestedKrw, 'KRW')}</div>
                </div>
                <div>
                  <Label className="text-gray-500">USDT 금액</Label>
                  <div className="font-medium">{selectedDeposit.calculatedUsdt.toFixed(2)} USDT</div>
                </div>
                <div>
                  <Label className="text-gray-500">환율</Label>
                  <div>{selectedDeposit.exchangeRate.toFixed(2)} KRW/USDT</div>
                </div>
                <div>
                  <Label className="text-gray-500">메모</Label>
                  <div className="font-mono text-blue-600">{selectedDeposit.memo}</div>
                </div>
                <div>
                  <Label className="text-gray-500">요청일시</Label>
                  <div>{formatDate(selectedDeposit.createdAt)}</div>
                </div>
                <div>
                  <Label className="text-gray-500">만료일시</Label>
                  <div>{formatDate(selectedDeposit.expiresAt)}</div>
                </div>
                {selectedDeposit.confirmedAt && (
                  <div>
                    <Label className="text-gray-500">완료일시</Label>
                    <div>{formatDate(selectedDeposit.confirmedAt)}</div>
                  </div>
                )}
                {selectedDeposit.txHash && (
                  <div className="col-span-2">
                    <Label className="text-gray-500">TX Hash</Label>
                    <div className="font-mono text-xs break-all">{selectedDeposit.txHash}</div>
                  </div>
                )}
              </div>
              
              {selectedDeposit.status === 'pending' && (
                <DialogFooter className="gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setRejectModalOpen(true)}
                  >
                    거부
                  </Button>
                  <Button
                    onClick={() => setApproveModalOpen(true)}
                  >
                    수동 승인
                  </Button>
                </DialogFooter>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Approve Modal */}
      <Dialog open={approveModalOpen} onOpenChange={setApproveModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>수동 승인</DialogTitle>
            <DialogDescription>
              입금을 수동으로 승인합니다. TX Hash를 입력해주세요.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="txHash">TX Hash</Label>
              <Input
                id="txHash"
                value={txHash}
                onChange={(e) => setTxHash(e.target.value)}
                placeholder="트랜잭션 해시 입력"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApproveModalOpen(false)}>
              취소
            </Button>
            <Button onClick={handleApprove} disabled={!txHash.trim() || actionLoading}>
              {actionLoading ? '처리중...' : '승인'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Modal */}
      <Dialog open={rejectModalOpen} onOpenChange={setRejectModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>입금 거부</DialogTitle>
            <DialogDescription>
              입금 요청을 거부합니다. 거부 사유를 입력해주세요.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="reason">거부 사유</Label>
              <Textarea
                id="reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="거부 사유 입력"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectModalOpen(false)}>
              취소
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={!rejectReason.trim() || actionLoading}
            >
              {actionLoading ? '처리중...' : '거부'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
