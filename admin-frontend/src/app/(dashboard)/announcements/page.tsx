'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  announcementsApi,
  Announcement,
  AnnouncementType,
  AnnouncementPriority,
  CreateAnnouncementRequest,
} from '@/lib/announcements-api';

const TYPE_LABELS: Record<AnnouncementType, string> = {
  notice: '일반 공지',
  event: '이벤트',
  maintenance: '점검',
  urgent: '긴급',
};

const TYPE_COLORS: Record<AnnouncementType, string> = {
  notice: 'bg-gray-100 text-gray-700',
  event: 'bg-blue-100 text-blue-700',
  maintenance: 'bg-yellow-100 text-yellow-700',
  urgent: 'bg-red-100 text-red-700',
};

const PRIORITY_LABELS: Record<AnnouncementPriority, string> = {
  low: '낮음',
  normal: '보통',
  high: '높음',
  critical: '긴급',
};

const TARGET_LABELS: Record<string, string> = {
  all: '전체',
  vip: 'VIP',
  specific_room: '특정 방',
};

// 공지 탭에 포함될 타입들
const NOTICE_TYPES: AnnouncementType[] = ['notice', 'maintenance', 'urgent'];

export default function AnnouncementsPage() {
  const [allAnnouncements, setAllAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<Announcement | null>(null);

  // Form states
  const [formData, setFormData] = useState<CreateAnnouncementRequest>({
    title: '',
    content: '',
    announcement_type: 'notice',
    priority: 'normal',
    target: 'all',
    broadcast_immediately: false,
  });
  const [actionLoading, setActionLoading] = useState(false);

  const fetchAnnouncements = useCallback(async () => {
    setLoading(true);
    try {
      const data = await announcementsApi.list({
        includeExpired: true,
        page: 1,
        pageSize: 100,
      });
      setAllAnnouncements(data.items);
    } catch (error) {
      console.error('Failed to fetch announcements:', error);
      toast.error('공지 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  // 이벤트와 공지 분리
  const events = useMemo(() => {
    return allAnnouncements.filter((item) => item.announcementType === 'event');
  }, [allAnnouncements]);

  const notices = useMemo(() => {
    return allAnnouncements.filter((item) => NOTICE_TYPES.includes(item.announcementType));
  }, [allAnnouncements]);

  const handleCreate = async () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      toast.error('제목과 내용을 입력해주세요.');
      return;
    }

    setActionLoading(true);
    try {
      await announcementsApi.create(formData);
      setCreateModalOpen(false);
      resetForm();
      toast.success('공지가 생성되었습니다.');
      fetchAnnouncements();
    } catch (error) {
      console.error('Failed to create announcement:', error);
      toast.error('공지 생성에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleBroadcast = async (id: string) => {
    setActionLoading(true);
    try {
      const result = await announcementsApi.broadcast(id);
      if (result.success) {
        toast.success(`공지가 브로드캐스트되었습니다.`);
        fetchAnnouncements();
        setDetailModalOpen(false);
      } else {
        toast.error(result.error || '브로드캐스트 실패');
      }
    } catch (error) {
      console.error('Failed to broadcast:', error);
      toast.error('브로드캐스트에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
      await announcementsApi.delete(id);
      setDetailModalOpen(false);
      toast.success('공지가 삭제되었습니다.');
      fetchAnnouncements();
    } catch (error) {
      console.error('Failed to delete:', error);
      toast.error('삭제에 실패했습니다.');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      announcement_type: 'notice',
      priority: 'normal',
      target: 'all',
      broadcast_immediately: false,
    });
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('ko-KR');
  };

  const handleRowClick = async (announcement: Announcement) => {
    setSelectedAnnouncement(announcement);
    setDetailModalOpen(true);
  };

  // 테이블 렌더링 컴포넌트
  const renderTable = (items: Announcement[], emptyMessage: string) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-24">유형</TableHead>
          <TableHead>제목</TableHead>
          <TableHead className="w-20">상태</TableHead>
          <TableHead className="w-20">발송</TableHead>
          <TableHead className="w-36">생성일</TableHead>
          <TableHead className="w-28">액션</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow
            key={item.id}
            className="cursor-pointer hover:bg-gray-50"
            onClick={() => handleRowClick(item)}
          >
            <TableCell>
              <span className={`px-2 py-1 rounded text-xs ${TYPE_COLORS[item.announcementType]}`}>
                {TYPE_LABELS[item.announcementType]}
              </span>
            </TableCell>
            <TableCell className="font-medium">{item.title}</TableCell>
            <TableCell>
              {item.isActive ? (
                <span className="text-green-600 text-sm">활성</span>
              ) : (
                <span className="text-gray-400 text-sm">비활성</span>
              )}
            </TableCell>
            <TableCell>
              <span className="text-sm text-gray-500">{item.broadcastCount}회</span>
            </TableCell>
            <TableCell className="text-sm text-gray-500">{formatDate(item.createdAt)}</TableCell>
            <TableCell>
              <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBroadcast(item.id)}
                  disabled={actionLoading}
                >
                  발송
                </Button>
                <Button size="sm" variant="destructive" onClick={() => handleDelete(item.id)}>
                  삭제
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
        {items.length === 0 && (
          <TableRow>
            <TableCell colSpan={6} className="text-center py-8 text-gray-500">
              {emptyMessage}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">이벤트/공지 관리</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchAnnouncements}>
            새로고침
          </Button>
          <Button onClick={() => setCreateModalOpen(true)}>+ 새 공지 작성</Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : (
        <>
          {/* 이벤트 섹션 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">이벤트 ({events.length}건)</CardTitle>
            </CardHeader>
            <CardContent>{renderTable(events, '이벤트가 없습니다.')}</CardContent>
          </Card>

          {/* 공지 섹션 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">공지 ({notices.length}건)</CardTitle>
            </CardHeader>
            <CardContent>{renderTable(notices, '공지가 없습니다.')}</CardContent>
          </Card>
        </>
      )}

      {/* Create Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>새 공지 작성</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>제목</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="공지 제목을 입력하세요"
              />
            </div>
            <div>
              <Label>내용</Label>
              <Textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                rows={5}
                placeholder="공지 내용을 입력하세요"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>유형</Label>
                <Select
                  value={formData.announcement_type}
                  onValueChange={(v) =>
                    setFormData({ ...formData, announcement_type: v as AnnouncementType })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="notice">일반 공지</SelectItem>
                    <SelectItem value="event">이벤트</SelectItem>
                    <SelectItem value="maintenance">점검</SelectItem>
                    <SelectItem value="urgent">긴급</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>우선순위</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(v) =>
                    setFormData({ ...formData, priority: v as AnnouncementPriority })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">낮음</SelectItem>
                    <SelectItem value="normal">보통</SelectItem>
                    <SelectItem value="high">높음</SelectItem>
                    <SelectItem value="critical">긴급</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>대상</Label>
              <Select
                value={formData.target}
                onValueChange={(v) =>
                  setFormData({ ...formData, target: v as 'all' | 'vip' | 'specific_room' })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체 사용자</SelectItem>
                  <SelectItem value="vip">VIP 사용자</SelectItem>
                  <SelectItem value="specific_room">특정 방</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.target === 'specific_room' && (
              <div>
                <Label>방 ID</Label>
                <Input
                  value={formData.target_room_id || ''}
                  onChange={(e) => setFormData({ ...formData, target_room_id: e.target.value })}
                  placeholder="방 ID를 입력하세요"
                />
              </div>
            )}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="broadcast_immediately"
                checked={formData.broadcast_immediately}
                onChange={(e) =>
                  setFormData({ ...formData, broadcast_immediately: e.target.checked })
                }
              />
              <Label htmlFor="broadcast_immediately" className="cursor-pointer">
                생성 즉시 브로드캐스트
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateModalOpen(false)}>
              취소
            </Button>
            <Button onClick={handleCreate} disabled={actionLoading || !formData.title.trim()}>
              {actionLoading ? '생성 중...' : '생성'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>공지 상세</DialogTitle>
          </DialogHeader>
          {selectedAnnouncement && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-gray-500">유형</Label>
                  <div>
                    <span
                      className={`px-2 py-1 rounded text-xs ${TYPE_COLORS[selectedAnnouncement.announcementType]}`}
                    >
                      {TYPE_LABELS[selectedAnnouncement.announcementType]}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-gray-500">우선순위</Label>
                  <div>{PRIORITY_LABELS[selectedAnnouncement.priority]}</div>
                </div>
                <div>
                  <Label className="text-gray-500">대상</Label>
                  <div>{TARGET_LABELS[selectedAnnouncement.target] || selectedAnnouncement.target}</div>
                </div>
                <div>
                  <Label className="text-gray-500">상태</Label>
                  <div>
                    {selectedAnnouncement.isActive ? (
                      <span className="text-green-600">활성</span>
                    ) : (
                      <span className="text-gray-400">비활성</span>
                    )}
                  </div>
                </div>
                <div className="col-span-2">
                  <Label className="text-gray-500">제목</Label>
                  <div className="font-medium">{selectedAnnouncement.title}</div>
                </div>
                <div className="col-span-2">
                  <Label className="text-gray-500">내용</Label>
                  <div className="whitespace-pre-wrap bg-gray-50 p-3 rounded border text-sm">
                    {selectedAnnouncement.content}
                  </div>
                </div>
                <div>
                  <Label className="text-gray-500">브로드캐스트 횟수</Label>
                  <div>{selectedAnnouncement.broadcastCount}회</div>
                </div>
                <div>
                  <Label className="text-gray-500">마지막 발송</Label>
                  <div>{formatDate(selectedAnnouncement.broadcastedAt)}</div>
                </div>
                <div>
                  <Label className="text-gray-500">생성일</Label>
                  <div>{formatDate(selectedAnnouncement.createdAt)}</div>
                </div>
                <div>
                  <Label className="text-gray-500">수정일</Label>
                  <div>{formatDate(selectedAnnouncement.updatedAt)}</div>
                </div>
              </div>
              <DialogFooter className="gap-2">
                <Button
                  variant="destructive"
                  onClick={() => handleDelete(selectedAnnouncement.id)}
                >
                  삭제
                </Button>
                <Button
                  onClick={() => handleBroadcast(selectedAnnouncement.id)}
                  disabled={actionLoading}
                >
                  {actionLoading ? '발송 중...' : '재발송'}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
