'use client';

import Link from 'next/link';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { SeatInfo } from '@/lib/rooms-api';

interface SeatsTableProps {
  seats: SeatInfo[];
}

export function SeatsTable({ seats }: SeatsTableProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">활성</Badge>;
      case 'folded':
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">폴드</Badge>;
      case 'all-in':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">올인</Badge>;
      case 'away':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">자리비움</Badge>;
      case 'empty':
        return <Badge variant="outline" className="text-muted-foreground">빈 좌석</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const occupiedSeats = seats.filter((s) => s.userId);
  const emptySeats = seats.filter((s) => !s.userId);

  return (
    <div className="space-y-4">
      {/* 착석자 테이블 */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">좌석</TableHead>
            <TableHead>유저</TableHead>
            <TableHead className="text-right">스택</TableHead>
            <TableHead className="w-24">상태</TableHead>
            <TableHead className="w-16">타입</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {occupiedSeats.length > 0 ? (
            occupiedSeats.map((seat) => (
              <TableRow key={seat.position}>
                <TableCell className="font-medium">{seat.position + 1}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {seat.userId ? (
                      <Link
                        href={`/users/${seat.userId}`}
                        className="text-blue-600 hover:underline"
                      >
                        {seat.nickname || '알 수 없음'}
                      </Link>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-mono">
                  {seat.stack.toLocaleString()}
                </TableCell>
                <TableCell>
                  {getStatusBadge(seat.status)}
                </TableCell>
                <TableCell>
                  {seat.isBot ? (
                    <Badge variant="secondary">봇</Badge>
                  ) : (
                    <Badge variant="outline">유저</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                착석한 플레이어가 없습니다
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {/* 빈 좌석 요약 */}
      {emptySeats.length > 0 && occupiedSeats.length > 0 && (
        <div className="text-sm text-muted-foreground">
          빈 좌석: {emptySeats.map((s) => s.position + 1).join(', ')}번
          ({emptySeats.length}석)
        </div>
      )}
    </div>
  );
}
