'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { roomsApi, RoomDetail, RoomStatus } from '@/lib/rooms-api';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores/authStore';
import { hasPermission } from '@/lib/permissions';
import { EditRoomDialog } from '@/components/rooms/EditRoomDialog';
import { ForceCloseDialog } from '@/components/rooms/ForceCloseDialog';
import { SeatsTable } from '@/components/rooms/SeatsTable';

export default function RoomDetailPage() {
  const params = useParams();
  const router = useRouter();
  const roomId = params.id as string;
  const user = useAuthStore((state) => state.user);

  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [forceCloseDialogOpen, setForceCloseDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const canUpdate = user && hasPermission(user.role, 'update_room');
  const canDelete = user && hasPermission(user.role, 'delete_room');
  const canForceClose = user && hasPermission(user.role, 'force_close_room');

  const fetchRoom = useCallback(async () => {
    setLoading(true);
    try {
      const data = await roomsApi.getRoom(roomId);
      setRoom(data);
    } catch (error) {
      console.error('Failed to fetch room:', error);
      toast.error('방 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    fetchRoom();
  }, [fetchRoom]);

  const handleDelete = async () => {
    if (!room || room.playerCount > 0) {
      toast.error('플레이어가 있는 방은 종료할 수 없습니다. 강제 종료를 사용하세요.');
      return;
    }

    if (!confirm('정말로 이 방을 종료하시겠습니까?')) {
      return;
    }

    setDeleteLoading(true);
    try {
      await roomsApi.deleteRoom(roomId);
      toast.success('방이 종료되었습니다.');
      router.push('/rooms');
    } catch (error) {
      console.error('Failed to delete room:', error);
      toast.error('방 종료에 실패했습니다.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleEditSuccess = () => {
    setEditDialogOpen(false);
    fetchRoom();
    toast.success('방 정보가 수정되었습니다.');
  };

  const handleForceCloseSuccess = () => {
    setForceCloseDialogOpen(false);
    router.push('/rooms');
  };

  const getStatusBadge = (status: RoomStatus) => {
    switch (status) {
      case 'waiting':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">대기중</Badge>;
      case 'playing':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">게임중</Badge>;
      case 'paused':
        return <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">일시정지</Badge>;
      case 'closed':
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">종료</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-24" />
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!room) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground mb-4">방을 찾을 수 없습니다.</p>
        <Button variant="outline" onClick={() => router.push('/rooms')}>
          목록으로 돌아가기
        </Button>
      </div>
    );
  }

  const isClosed = room.status === 'closed';

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push('/rooms')}>
            ← 목록
          </Button>
          <h1 className="text-2xl font-bold">{room.name}</h1>
          {getStatusBadge(room.status)}
          {room.isPrivate && (
            <Badge variant="secondary">비공개</Badge>
          )}
        </div>
        {!isClosed && (
          <div className="flex gap-2">
            {canUpdate && (
              <Button variant="outline" onClick={() => setEditDialogOpen(true)}>
                수정
              </Button>
            )}
            {canDelete && room.playerCount === 0 && (
              <Button
                variant="outline"
                onClick={handleDelete}
                disabled={deleteLoading}
              >
                {deleteLoading ? '종료 중...' : '종료'}
              </Button>
            )}
            {canForceClose && room.playerCount > 0 && (
              <Button
                variant="destructive"
                onClick={() => setForceCloseDialogOpen(true)}
              >
                강제 종료
              </Button>
            )}
          </div>
        )}
      </div>

      {/* 기본 정보 카드 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>기본 정보</CardTitle>
            <CardDescription>방 설정 정보</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">방 ID</p>
                <p className="font-mono text-sm">{room.id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">타입</p>
                <Badge variant={room.roomType === 'cash' ? 'default' : 'secondary'}>
                  {room.roomType === 'cash' ? '캐시 게임' : '토너먼트'}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">블라인드</p>
                <p className="font-medium">{room.smallBlind} / {room.bigBlind}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">바이인</p>
                <p className="font-medium">
                  {room.buyInMin.toLocaleString()} ~ {room.buyInMax.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">좌석 수</p>
                <p className="font-medium">{room.maxPlayers}석</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">턴 타임아웃</p>
                <p className="font-medium">{room.turnTimeout}초</p>
              </div>
            </div>
            {room.description && (
              <div>
                <p className="text-sm text-muted-foreground">설명</p>
                <p className="text-sm">{room.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>상태 정보</CardTitle>
            <CardDescription>현재 방 상태</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">현재 플레이어</p>
                <p className="font-medium text-lg">{room.playerCount} / {room.maxPlayers}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">상태</p>
                <div className="mt-1">{getStatusBadge(room.status)}</div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">방장</p>
                <p className="font-medium">
                  {room.ownerNickname || <span className="text-muted-foreground">시스템</span>}
                </p>
              </div>
              {room.currentHandId && (
                <div>
                  <p className="text-sm text-muted-foreground">현재 핸드</p>
                  <p className="font-mono text-sm">{room.currentHandId}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">생성일</p>
                <p className="text-sm">
                  {new Date(room.createdAt).toLocaleString('ko-KR')}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">수정일</p>
                <p className="text-sm">
                  {new Date(room.updatedAt).toLocaleString('ko-KR')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 좌석 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>좌석 현황</CardTitle>
          <CardDescription>
            현재 착석자 정보 ({room.playerCount}명 착석)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SeatsTable seats={room.seats} />
        </CardContent>
      </Card>

      {/* 수정 다이얼로그 */}
      {room && (
        <EditRoomDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          room={room}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* 강제 종료 다이얼로그 */}
      {room && (
        <ForceCloseDialog
          open={forceCloseDialogOpen}
          onOpenChange={setForceCloseDialogOpen}
          room={room}
          onSuccess={handleForceCloseSuccess}
        />
      )}
    </div>
  );
}
