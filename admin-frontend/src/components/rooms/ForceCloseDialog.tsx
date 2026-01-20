'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { roomsApi, RoomDetail, ForceCloseResult } from '@/lib/rooms-api';
import { toast } from 'sonner';

interface ForceCloseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  room: RoomDetail;
  onSuccess: () => void;
}

export function ForceCloseDialog({ open, onOpenChange, room, onSuccess }: ForceCloseDialogProps) {
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState('');
  const [result, setResult] = useState<ForceCloseResult | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!reason.trim()) {
      toast.error('종료 사유를 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const closeResult = await roomsApi.forceCloseRoom(room.id, reason);
      setResult(closeResult);
      toast.success(`방이 강제 종료되었습니다. ${closeResult.playersAffected}명에게 ${closeResult.totalRefunded.toLocaleString()} 칩 환불됨`);
    } catch (error) {
      console.error('Failed to force close room:', error);
      toast.error('방 강제 종료에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setResult(null);
    onOpenChange(false);
    if (result) {
      onSuccess();
    }
  };

  // 현재 착석자 스택 합계 계산
  const totalStacks = room.seats
    .filter((s) => s.userId)
    .reduce((sum, s) => sum + s.stack, 0);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>방 강제 종료</DialogTitle>
          <DialogDescription>
            {result
              ? '방이 강제 종료되었습니다.'
              : '진행 중인 게임을 강제 종료하고 플레이어에게 환불합니다.'}
          </DialogDescription>
        </DialogHeader>

        {!result ? (
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              {/* 경고 메시지 */}
              <Alert variant="destructive">
                <AlertTitle>주의</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside space-y-1 mt-2">
                    <li>진행 중인 핸드가 즉시 취소됩니다</li>
                    <li>팟의 모든 칩은 각 플레이어에게 환불됩니다</li>
                    <li>현재 {room.playerCount}명의 플레이어에게 총 {totalStacks.toLocaleString()} 칩이 환불됩니다</li>
                    <li>이 작업은 되돌릴 수 없습니다</li>
                  </ul>
                </AlertDescription>
              </Alert>

              {/* 현재 착석자 */}
              <div className="text-sm">
                <p className="font-medium mb-2">현재 착석자 ({room.playerCount}명)</p>
                <div className="rounded border max-h-32 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">좌석</TableHead>
                        <TableHead>닉네임</TableHead>
                        <TableHead className="text-right">스택</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {room.seats
                        .filter((s) => s.userId)
                        .map((seat) => (
                          <TableRow key={seat.position}>
                            <TableCell>{seat.position + 1}</TableCell>
                            <TableCell>{seat.nickname}</TableCell>
                            <TableCell className="text-right">
                              {seat.stack.toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* 종료 사유 */}
              <div className="grid gap-2">
                <Label htmlFor="reason">종료 사유 *</Label>
                <Textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="플레이어에게 표시될 종료 사유를 입력하세요"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                취소
              </Button>
              <Button type="submit" variant="destructive" disabled={loading}>
                {loading ? '종료 중...' : '강제 종료'}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <div className="grid gap-4 py-4">
            {/* 결과 표시 */}
            <Alert>
              <AlertTitle>완료</AlertTitle>
              <AlertDescription>
                {result.playersAffected}명의 플레이어에게 총 {result.totalRefunded.toLocaleString()} 칩이 환불되었습니다.
              </AlertDescription>
            </Alert>

            {/* 환불 내역 */}
            {result.refunds.length > 0 && (
              <div>
                <p className="font-medium mb-2">환불 내역</p>
                <div className="rounded border max-h-48 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">좌석</TableHead>
                        <TableHead>닉네임</TableHead>
                        <TableHead className="text-right">환불액</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.refunds.map((refund) => (
                        <TableRow key={refund.user_id}>
                          <TableCell>{refund.seat + 1}</TableCell>
                          <TableCell>{refund.nickname}</TableCell>
                          <TableCell className="text-right font-medium text-green-600">
                            +{refund.amount.toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button onClick={handleClose}>
                확인
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
