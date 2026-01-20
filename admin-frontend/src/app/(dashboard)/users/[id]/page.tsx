'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usersApi, UserDetail, Transaction, LoginHistory, HandHistory } from '@/lib/users-api';
import { toast } from 'sonner';

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;

  const [user, setUser] = useState<UserDetail | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loginHistory, setLoginHistory] = useState<LoginHistory[]>([]);
  const [hands, setHands] = useState<HandHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('info');

  // Modal states
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Form states
  const [newPassword, setNewPassword] = useState('');
  const [editForm, setEditForm] = useState({ nickname: '', email: '' });

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await usersApi.getUser(userId);
        setUser(data);
      } catch (error) {
        console.error('Failed to fetch user:', error);
        toast.error('사용자 정보를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [userId]);

  useEffect(() => {
    const fetchTabData = async () => {
      try {
        if (activeTab === 'transactions') {
          const data = await usersApi.getUserTransactions(userId);
          setTransactions(data.items);
        } else if (activeTab === 'logins') {
          const data = await usersApi.getUserLoginHistory(userId);
          setLoginHistory(data.items);
        } else if (activeTab === 'hands') {
          const data = await usersApi.getUserHands(userId);
          setHands(data.items);
        }
      } catch (error) {
        console.error('Failed to fetch tab data:', error);
        const tabNames: Record<string, string> = {
          transactions: '거래 내역',
          logins: '로그인 기록',
          hands: '핸드 기록',
        };
        toast.error(`${tabNames[activeTab] || '데이터'}을(를) 불러오는데 실패했습니다.`);
      }
    };
    if (userId) fetchTabData();
  }, [userId, activeTab]);

  // Refresh user data
  const refreshUser = async () => {
    try {
      const data = await usersApi.getUser(userId);
      setUser(data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  // Status change handler
  const handleStatusChange = async (newStatus: 'active' | 'suspended') => {
    setActionLoading(true);
    try {
      await usersApi.updateUserStatus(userId, newStatus);
      toast.success(`사용자 상태가 ${newStatus === 'active' ? '활성' : '정지'}로 변경되었습니다`);
      setStatusModalOpen(false);
      refreshUser();
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error(error instanceof Error ? error.message : '상태 변경에 실패했습니다');
    } finally {
      setActionLoading(false);
    }
  };

  // Password reset handler
  const handlePasswordReset = async () => {
    if (newPassword.length < 8) {
      toast.error('비밀번호는 최소 8자 이상이어야 합니다');
      return;
    }

    setActionLoading(true);
    try {
      await usersApi.resetPassword(userId, newPassword);
      toast.success('비밀번호가 초기화되었습니다');
      setPasswordModalOpen(false);
      setNewPassword('');
    } catch (error) {
      console.error('Failed to reset password:', error);
      toast.error(error instanceof Error ? error.message : '비밀번호 초기화에 실패했습니다');
    } finally {
      setActionLoading(false);
    }
  };

  // Edit profile handler
  const handleEditProfile = async () => {
    if (!editForm.nickname && !editForm.email) {
      toast.error('수정할 항목을 입력해주세요');
      return;
    }

    setActionLoading(true);
    try {
      const updateData: { nickname?: string; email?: string } = {};
      if (editForm.nickname) updateData.nickname = editForm.nickname;
      if (editForm.email) updateData.email = editForm.email;

      await usersApi.updateUser(userId, updateData);
      toast.success('프로필이 수정되었습니다');
      setEditModalOpen(false);
      setEditForm({ nickname: '', email: '' });
      refreshUser();
    } catch (error) {
      console.error('Failed to update profile:', error);
      toast.error(error instanceof Error ? error.message : '프로필 수정에 실패했습니다');
    } finally {
      setActionLoading(false);
    }
  };

  // Delete user handler
  const handleDeleteUser = async () => {
    setActionLoading(true);
    try {
      await usersApi.deleteUser(userId);
      toast.success('사용자가 삭제되었습니다');
      router.push('/users');
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error(error instanceof Error ? error.message : '사용자 삭제에 실패했습니다');
    } finally {
      setActionLoading(false);
    }
  };

  // Open edit modal with current data
  const openEditModal = () => {
    setEditForm({
      nickname: user?.username || '',
      email: user?.email || '',
    });
    setEditModalOpen(true);
  };

  if (loading) {
    return <div className="text-center py-8">로딩 중...</div>;
  }

  if (!user) {
    return <div className="text-center py-8">사용자를 찾을 수 없습니다</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>← 뒤로</Button>
          <h1 className="text-2xl font-bold">{user.username}</h1>
          {user.isBanned && (
            <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-sm">
              제재됨
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">관리 메뉴 ▼</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={openEditModal}>
                프로필 수정
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setPasswordModalOpen(true)}>
                비밀번호 초기화
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setStatusModalOpen(true)}>
                {user.isBanned ? '사용자 활성화' : '사용자 정지'}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => setDeleteModalOpen(true)}
                className="text-red-600"
              >
                사용자 삭제
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* User Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>기본 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">ID</p>
              <p className="font-mono text-sm">{user.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">이메일</p>
              <p>{user.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">잔액</p>
              <p className="text-xl font-bold">{user.balance.toLocaleString()} USDT</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">가입일</p>
              <p>{user.createdAt ? new Date(user.createdAt).toLocaleDateString('ko-KR') : '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">최근 로그인</p>
              <p>{user.lastLogin ? new Date(user.lastLogin).toLocaleString('ko-KR') : '-'}</p>
            </div>
            {user.isBanned && user.banReason && (
              <div className="col-span-2">
                <p className="text-sm text-gray-500">제재 사유</p>
                <p className="text-red-600">{user.banReason}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="info">정보</TabsTrigger>
          <TabsTrigger value="transactions">거래 내역</TabsTrigger>
          <TabsTrigger value="logins">로그인 기록</TabsTrigger>
          <TabsTrigger value="hands">핸드 기록</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardContent className="pt-6">
              <p className="text-gray-500">추가 정보가 여기에 표시됩니다.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transactions">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>유형</TableHead>
                    <TableHead className="text-right">금액</TableHead>
                    <TableHead className="text-right">이전 잔액</TableHead>
                    <TableHead className="text-right">이후 잔액</TableHead>
                    <TableHead>설명</TableHead>
                    <TableHead>일시</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell>{tx.type}</TableCell>
                      <TableCell className={`text-right ${tx.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.amount >= 0 ? '+' : ''}{tx.amount.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">{tx.balanceBefore.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{tx.balanceAfter.toLocaleString()}</TableCell>
                      <TableCell>{tx.description || '-'}</TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {tx.createdAt ? new Date(tx.createdAt).toLocaleString('ko-KR') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {transactions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        거래 내역이 없습니다
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logins">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>IP 주소</TableHead>
                    <TableHead>User Agent</TableHead>
                    <TableHead>결과</TableHead>
                    <TableHead>일시</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loginHistory.map((login) => (
                    <TableRow key={login.id}>
                      <TableCell className="font-mono">{login.ipAddress || '-'}</TableCell>
                      <TableCell className="text-sm max-w-xs truncate">{login.userAgent || '-'}</TableCell>
                      <TableCell>
                        {login.success ? (
                          <span className="text-green-600">성공</span>
                        ) : (
                          <span className="text-red-600">실패</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {login.createdAt ? new Date(login.createdAt).toLocaleString('ko-KR') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {loginHistory.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                        로그인 기록이 없습니다
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hands">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>핸드 ID</TableHead>
                    <TableHead>포지션</TableHead>
                    <TableHead>카드</TableHead>
                    <TableHead className="text-right">베팅</TableHead>
                    <TableHead className="text-right">획득</TableHead>
                    <TableHead className="text-right">팟</TableHead>
                    <TableHead>일시</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {hands.map((hand) => (
                    <TableRow key={hand.id}>
                      <TableCell className="font-mono text-xs">{hand.handId.slice(0, 8)}...</TableCell>
                      <TableCell>{hand.position ?? '-'}</TableCell>
                      <TableCell className="font-mono">{hand.cards || '-'}</TableCell>
                      <TableCell className="text-right">{hand.betAmount.toLocaleString()}</TableCell>
                      <TableCell className={`text-right ${hand.wonAmount > 0 ? 'text-green-600' : ''}`}>
                        {hand.wonAmount.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">{hand.potSize.toLocaleString()}</TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {hand.createdAt ? new Date(hand.createdAt).toLocaleString('ko-KR') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {hands.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        핸드 기록이 없습니다
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Status Change Modal */}
      <Dialog open={statusModalOpen} onOpenChange={setStatusModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>사용자 상태 변경</DialogTitle>
            <DialogDescription>
              {user.isBanned
                ? '이 사용자를 다시 활성화하시겠습니까?'
                : '이 사용자를 정지하시겠습니까?'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusModalOpen(false)}>
              취소
            </Button>
            <Button
              onClick={() => handleStatusChange(user.isBanned ? 'active' : 'suspended')}
              disabled={actionLoading}
              variant={user.isBanned ? 'default' : 'destructive'}
            >
              {actionLoading ? '처리 중...' : user.isBanned ? '활성화' : '정지'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Password Reset Modal */}
      <Dialog open={passwordModalOpen} onOpenChange={setPasswordModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>비밀번호 초기화</DialogTitle>
            <DialogDescription>
              새 비밀번호를 입력해주세요 (최소 8자).
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="grid gap-2">
              <Label htmlFor="newPassword">새 비밀번호</Label>
              <Input
                id="newPassword"
                type="password"
                placeholder="새 비밀번호 입력"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setPasswordModalOpen(false);
                setNewPassword('');
              }}
            >
              취소
            </Button>
            <Button onClick={handlePasswordReset} disabled={actionLoading}>
              {actionLoading ? '처리 중...' : '초기화'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Profile Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>프로필 수정</DialogTitle>
            <DialogDescription>
              사용자 프로필을 수정합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="editNickname">닉네임</Label>
              <Input
                id="editNickname"
                placeholder="새 닉네임"
                value={editForm.nickname}
                onChange={(e) => setEditForm({ ...editForm, nickname: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="editEmail">이메일</Label>
              <Input
                id="editEmail"
                type="email"
                placeholder="새 이메일"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditModalOpen(false);
                setEditForm({ nickname: '', email: '' });
              }}
            >
              취소
            </Button>
            <Button onClick={handleEditProfile} disabled={actionLoading}>
              {actionLoading ? '처리 중...' : '저장'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>사용자 삭제</DialogTitle>
            <DialogDescription>
              정말 이 사용자를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              취소
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteUser}
              disabled={actionLoading}
            >
              {actionLoading ? '삭제 중...' : '삭제'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
