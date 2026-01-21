'use client';

import { memo } from 'react';
import { getChipStackImage } from './chipStackMapping';

interface ChipStackProps {
  /** 베팅 금액 */
  amount: number;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 칩 스택 컴포넌트
 *
 * 금액에 따라 미리 생성된 칩 스택 이미지를 표시합니다.
 * 기존의 동적 칩 계산/렌더링 대신 단일 이미지를 사용하여 성능을 최적화합니다.
 *
 * @example
 * <ChipStack amount={500} />
 * <ChipStack amount={10000} className="opacity-80" />
 */
export const ChipStack = memo(function ChipStack({
  amount,
  className = '',
}: ChipStackProps) {
  if (amount <= 0) return null;

  const imageSrc = getChipStackImage(amount);

  return (
    <img
      src={imageSrc}
      alt=""
      className={className}
      style={{
        width: 32,
        height: 'auto',
        imageRendering: 'crisp-edges',
      }}
      loading="eager"
      decoding="async"
      draggable={false}
    />
  );
});

export default ChipStack;
