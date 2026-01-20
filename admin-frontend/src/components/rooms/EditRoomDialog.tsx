'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { roomsApi, RoomDetail, UpdateRoomData } from '@/lib/rooms-api';
import { toast } from 'sonner';

interface EditRoomDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  room: RoomDetail;
  onSuccess: () => void;
}

interface FormData {
  // 기본 정보
  name: string;
  description: string;
  isPrivate: boolean;
  password: string;
  // 게임 설정
  smallBlind: number;
  bigBlind: number;
  buyInMin: number;
  buyInMax: number;
  turnTimeout: number;
  // 테이블 설정
  maxSeats: 6 | 9;
}

export function EditRoomDialog({ open, onOpenChange, room, onSuccess }: EditRoomDialogProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    name: room.name,
    description: room.description || '',
    isPrivate: room.isPrivate,
    password: '',
    smallBlind: room.smallBlind,
    bigBlind: room.bigBlind,
    buyInMin: room.buyInMin,
    buyInMax: room.buyInMax,
    turnTimeout: room.turnTimeout,
    maxSeats: room.maxPlayers as 6 | 9,
  });

  // 다이얼로그가 열릴 때 방 정보로 초기화
  useEffect(() => {
    if (open) {
      setFormData({
        name: room.name,
        description: room.description || '',
        isPrivate: room.isPrivate,
        password: '',
        smallBlind: room.smallBlind,
        bigBlind: room.bigBlind,
        buyInMin: room.buyInMin,
        buyInMax: room.buyInMax,
        turnTimeout: room.turnTimeout,
        maxSeats: room.maxPlayers as 6 | 9,
      });
    }
  }, [open, room]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name?.trim()) {
      toast.error('방 이름을 입력해주세요.');
      return;
    }

    if (formData.smallBlind >= formData.bigBlind) {
      toast.error('스몰 블라인드는 빅 블라인드보다 작아야 합니다.');
      return;
    }

    if (formData.buyInMin >= formData.buyInMax) {
      toast.error('최소 바이인은 최대 바이인보다 작아야 합니다.');
      return;
    }

    // 비공개로 전환 시 비밀번호 필수
    if (formData.isPrivate && !room.isPrivate && !formData.password) {
      toast.error('비공개 방으로 변경 시 비밀번호가 필요합니다.');
      return;
    }

    setLoading(true);
    try {
      const data: UpdateRoomData = {};

      // 변경된 값만 전송
      if (formData.name !== room.name) data.name = formData.name;
      if (formData.description !== (room.description || '')) data.description = formData.description;
      if (formData.isPrivate !== room.isPrivate) data.isPrivate = formData.isPrivate;
      if (formData.password) data.password = formData.password;
      if (formData.smallBlind !== room.smallBlind) data.smallBlind = formData.smallBlind;
      if (formData.bigBlind !== room.bigBlind) data.bigBlind = formData.bigBlind;
      if (formData.buyInMin !== room.buyInMin) data.buyInMin = formData.buyInMin;
      if (formData.buyInMax !== room.buyInMax) data.buyInMax = formData.buyInMax;
      if (formData.turnTimeout !== room.turnTimeout) data.turnTimeout = formData.turnTimeout;
      if (formData.maxSeats !== room.maxPlayers) data.maxSeats = formData.maxSeats;

      await roomsApi.updateRoom(room.id, data);
      onSuccess();
    } catch (error) {
      console.error('Failed to update room:', error);
      toast.error('방 수정에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const hasPlayers = room.playerCount > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>방 수정</DialogTitle>
          <DialogDescription>
            방의 모든 설정을 수정할 수 있습니다.
            {hasPlayers && ' (좌석 수는 플레이어가 없을 때만 변경 가능)'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* 기본 정보 */}
            <div className="text-sm font-medium text-muted-foreground">기본 정보</div>

            {/* 방 이름 */}
            <div className="grid gap-2">
              <Label htmlFor="edit-name">방 이름 *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="방 이름을 입력하세요"
                maxLength={100}
              />
            </div>

            {/* 설명 */}
            <div className="grid gap-2">
              <Label htmlFor="edit-description">설명</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="방 설명 (선택)"
                rows={2}
              />
            </div>

            {/* 비공개 설정 */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>비공개 방</Label>
                <p className="text-sm text-muted-foreground">
                  비밀번호를 입력해야 입장
                </p>
              </div>
              <Switch
                checked={formData.isPrivate}
                onCheckedChange={(checked) => setFormData({ ...formData, isPrivate: checked })}
              />
            </div>

            {/* 비밀번호 */}
            {formData.isPrivate && (
              <div className="grid gap-2">
                <Label htmlFor="edit-password">
                  비밀번호 {!room.isPrivate && '*'}
                </Label>
                <Input
                  id="edit-password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder={room.isPrivate ? '변경 시에만 입력' : '비밀번호 입력'}
                />
              </div>
            )}

            <Separator />

            {/* 게임 설정 */}
            <div className="text-sm font-medium text-muted-foreground">게임 설정</div>

            {/* 블라인드 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-sb">스몰 블라인드</Label>
                <Input
                  id="edit-sb"
                  type="number"
                  value={formData.smallBlind}
                  onChange={(e) => setFormData({ ...formData, smallBlind: parseInt(e.target.value) || 0 })}
                  min={1}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-bb">빅 블라인드</Label>
                <Input
                  id="edit-bb"
                  type="number"
                  value={formData.bigBlind}
                  onChange={(e) => setFormData({ ...formData, bigBlind: parseInt(e.target.value) || 0 })}
                  min={2}
                />
              </div>
            </div>

            {/* 바이인 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-buyin-min">최소 바이인</Label>
                <Input
                  id="edit-buyin-min"
                  type="number"
                  value={formData.buyInMin}
                  onChange={(e) => setFormData({ ...formData, buyInMin: parseInt(e.target.value) || 0 })}
                  min={1}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-buyin-max">최대 바이인</Label>
                <Input
                  id="edit-buyin-max"
                  type="number"
                  value={formData.buyInMax}
                  onChange={(e) => setFormData({ ...formData, buyInMax: parseInt(e.target.value) || 0 })}
                  min={1}
                />
              </div>
            </div>

            {/* 턴 타임아웃 */}
            <div className="grid gap-2">
              <Label htmlFor="edit-timeout">턴 타임아웃 (초)</Label>
              <Input
                id="edit-timeout"
                type="number"
                value={formData.turnTimeout}
                onChange={(e) => setFormData({ ...formData, turnTimeout: parseInt(e.target.value) || 30 })}
                min={10}
                max={120}
              />
            </div>

            <Separator />

            {/* 테이블 설정 */}
            <div className="text-sm font-medium text-muted-foreground">테이블 설정</div>

            {/* 좌석 수 */}
            <div className="grid gap-2">
              <Label>좌석 수</Label>
              <Select
                value={String(formData.maxSeats)}
                onValueChange={(value) => setFormData({ ...formData, maxSeats: parseInt(value) as 6 | 9 })}
                disabled={hasPlayers}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="6">6인석</SelectItem>
                  <SelectItem value="9">9인석</SelectItem>
                </SelectContent>
              </Select>
              {hasPlayers && (
                <p className="text-xs text-muted-foreground">
                  플레이어가 있어 좌석 수를 변경할 수 없습니다
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '저장 중...' : '저장'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
