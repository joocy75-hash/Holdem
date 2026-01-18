'use client';

import { useState } from 'react';
import { Button } from './button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog';
import { Badge } from './badge';

export interface BulkActionItem {
  id: string;
  label: string;
  success: boolean;
  error?: string;
}

export interface BulkActionResult {
  total: number;
  successful: number;
  failed: number;
  items: BulkActionItem[];
}

interface BulkActionResultDialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  result: BulkActionResult | null;
  onRetry?: (failedIds: string[]) => void;
}

export function BulkActionResultDialog({
  open,
  onClose,
  title,
  result,
  onRetry,
}: BulkActionResultDialogProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (!result) return null;

  const { total, successful, failed, items } = result;
  const failedItems = items.filter((item) => !item.success);
  const successItems = items.filter((item) => item.success);

  const isAllSuccess = failed === 0;
  const isAllFailed = successful === 0;
  const isPartialSuccess = !isAllSuccess && !isAllFailed;

  const getStatusColor = () => {
    if (isAllSuccess) return 'bg-green-50 border-green-200';
    if (isAllFailed) return 'bg-red-50 border-red-200';
    return 'bg-yellow-50 border-yellow-200';
  };

  const getStatusIcon = () => {
    if (isAllSuccess) return '✅';
    if (isAllFailed) return '❌';
    return '⚠️';
  };

  const getStatusText = () => {
    if (isAllSuccess) return '모든 작업이 성공했습니다';
    if (isAllFailed) return '모든 작업이 실패했습니다';
    return '일부 작업이 실패했습니다';
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {total}개 항목 중 {successful}개 성공, {failed}개 실패
          </DialogDescription>
        </DialogHeader>

        {/* Status Summary */}
        <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getStatusIcon()}</span>
            <div>
              <p className="font-medium">{getStatusText()}</p>
              <div className="flex gap-2 mt-1">
                <Badge variant="outline" className="bg-green-100 text-green-700">
                  성공: {successful}
                </Badge>
                {failed > 0 && (
                  <Badge variant="outline" className="bg-red-100 text-red-700">
                    실패: {failed}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Failed Items List */}
        {failed > 0 && (
          <div className="space-y-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-blue-600 hover:underline flex items-center gap-1"
            >
              {showDetails ? '▼' : '▶'} 실패 항목 상세보기 ({failed}개)
            </button>

            {showDetails && (
              <div className="max-h-48 overflow-y-auto space-y-2 p-2 bg-gray-50 rounded-md">
                {failedItems.map((item) => (
                  <div
                    key={item.id}
                    className="p-2 bg-white rounded border border-red-100 text-sm"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-medium">{item.label}</span>
                      <Badge variant="destructive" className="text-xs">
                        실패
                      </Badge>
                    </div>
                    {item.error && (
                      <p className="text-red-600 text-xs mt-1">{item.error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Success Items (collapsed by default) */}
        {successful > 0 && showDetails && (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">성공 항목 ({successful}개)</p>
            <div className="max-h-32 overflow-y-auto space-y-1 p-2 bg-green-50 rounded-md">
              {successItems.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-2 text-sm text-green-700"
                >
                  <span>✓</span>
                  <span>{item.label}</span>
                </div>
              ))}
              {successItems.length > 5 && (
                <p className="text-xs text-green-600">
                  ...외 {successItems.length - 5}개
                </p>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="gap-2">
          {failed > 0 && onRetry && (
            <Button
              variant="outline"
              onClick={() => onRetry(failedItems.map((item) => item.id))}
            >
              실패 항목 재시도
            </Button>
          )}
          <Button onClick={onClose}>확인</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Bulk Action 실행 헬퍼 함수
 *
 * @example
 * const result = await executeBulkAction(
 *   selectedIds,
 *   async (id) => {
 *     await api.delete(`/bans/${id}`);
 *     return { id, label: `Ban ${id}` };
 *   }
 * );
 */
export async function executeBulkAction<T extends { id: string; label: string }>(
  ids: string[],
  action: (id: string) => Promise<T>,
  options?: {
    concurrency?: number;
    onProgress?: (completed: number, total: number) => void;
  }
): Promise<BulkActionResult> {
  const { concurrency = 3, onProgress } = options || {};
  const items: BulkActionItem[] = [];
  let completed = 0;

  // 동시성 제한으로 실행
  const chunks: string[][] = [];
  for (let i = 0; i < ids.length; i += concurrency) {
    chunks.push(ids.slice(i, i + concurrency));
  }

  for (const chunk of chunks) {
    const results = await Promise.allSettled(
      chunk.map(async (id) => {
        const result = await action(id);
        return result;
      })
    );

    results.forEach((result, index) => {
      const id = chunk[index];
      if (result.status === 'fulfilled') {
        items.push({
          id,
          label: result.value.label,
          success: true,
        });
      } else {
        items.push({
          id,
          label: `ID: ${id.slice(0, 8)}...`,
          success: false,
          error: result.reason?.message || '알 수 없는 오류',
        });
      }
      completed++;
      onProgress?.(completed, ids.length);
    });
  }

  return {
    total: ids.length,
    successful: items.filter((item) => item.success).length,
    failed: items.filter((item) => !item.success).length,
    items,
  };
}
