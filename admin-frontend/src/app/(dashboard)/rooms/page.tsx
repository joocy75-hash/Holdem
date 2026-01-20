'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import { roomsApi, Room, PaginatedRooms, RoomStatus } from '@/lib/rooms-api';
import { toast } from 'sonner';
import { TableSkeleton } from '@/components/ui/table-skeleton';
import { useAuthStore } from '@/stores/authStore';
import { hasPermission } from '@/lib/permissions';
import { CreateRoomDialog } from '@/components/rooms/CreateRoomDialog';

export default function RoomsPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const [rooms, setRooms] = useState<PaginatedRooms | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const canCreate = user && hasPermission(user.role, 'create_room');

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        search: search || undefined,
        status: statusFilter === 'all' ? undefined : (statusFilter as RoomStatus),
        includeClosed: statusFilter === 'closed',
        page,
        pageSize: 20,
      };
      const data = await roomsApi.listRooms(params);
      setRooms(data);
    } catch (error) {
      console.error('Failed to fetch rooms:', error);
      toast.error('방 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, page]);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchRooms();
  };

  const handleRoomClick = (roomId: string) => {
    router.push(`/rooms/${roomId}`);
  };

  const handleCreateSuccess = () => {
    setCreateDialogOpen(false);
    fetchRooms();
    toast.success('방이 생성되었습니다.');
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">방 관리</h1>
        {canCreate && (
          <Button onClick={() => setCreateDialogOpen(true)}>
            + 방 생성
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>방 목록</CardTitle>
        </CardHeader>
        <CardContent>
          {/* 검색 및 필터 */}
          <div className="flex gap-4 mb-6">
            <form onSubmit={handleSearch} className="flex-1">
              <Input
                placeholder="방 이름으로 검색..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </form>
            <Select value={statusFilter} onValueChange={(value) => { setStatusFilter(value); setPage(1); }}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="상태 필터" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체</SelectItem>
                <SelectItem value="waiting">대기중</SelectItem>
                <SelectItem value="playing">게임중</SelectItem>
                <SelectItem value="closed">종료</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchRooms}>
              새로고침
            </Button>
          </div>

          {/* 테이블 */}
          {loading ? (
            <TableSkeleton columns={7} rows={10} />
          ) : rooms && rooms.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>방 이름</TableHead>
                    <TableHead>플레이어</TableHead>
                    <TableHead>블라인드</TableHead>
                    <TableHead>바이인</TableHead>
                    <TableHead>타입</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>생성일</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rooms.items.map((room) => (
                    <TableRow
                      key={room.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleRoomClick(room.id)}
                    >
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          {room.name}
                          {room.isPrivate && (
                            <Badge variant="secondary" className="text-xs">비공개</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {room.playerCount} / {room.maxPlayers}
                      </TableCell>
                      <TableCell>
                        {room.smallBlind}/{room.bigBlind}
                      </TableCell>
                      <TableCell>
                        {room.buyInMin.toLocaleString()} ~ {room.buyInMax.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={room.roomType === 'cash' ? 'default' : 'secondary'}>
                          {room.roomType === 'cash' ? '캐시' : '토너먼트'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(room.status)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(room.createdAt).toLocaleDateString('ko-KR')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* 페이지네이션 */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  전체 {rooms.total}개 중 {(page - 1) * 20 + 1} - {Math.min(page * 20, rooms.total)}개 표시
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    이전
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= rooms.totalPages}
                  >
                    다음
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              {search || statusFilter !== 'all' ? (
                <p>검색 결과가 없습니다.</p>
              ) : (
                <p>등록된 방이 없습니다.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 방 생성 다이얼로그 */}
      <CreateRoomDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
}
