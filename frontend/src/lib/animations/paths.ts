/**
 * Animation Path Utilities
 * 베지어 곡선 및 경로 계산 유틸리티
 */

export interface Point {
  x: number;
  y: number;
}

export interface CurvedPathOptions {
  /** 곡률 (0-1, 높을수록 더 휘어짐) */
  curvature?: number;
  /** 곡선 방향 ('up' | 'down' | 'auto') */
  direction?: 'up' | 'down' | 'auto';
}

/**
 * 두 점 사이의 곡선 경로를 계산합니다.
 * 칩 이동 애니메이션에 사용됩니다.
 */
export function calculateCurvedPath(
  start: Point,
  end: Point,
  options: CurvedPathOptions = {}
): Point[] {
  const { curvature = 0.3, direction = 'auto' } = options;
  
  // 중간점 계산
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;
  
  // 거리 계산
  const distance = Math.sqrt(
    Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)
  );
  
  // 곡선 높이 계산
  const curveHeight = distance * curvature;
  
  // 방향 결정
  let curveDirection: number;
  if (direction === 'auto') {
    // 자동: 위쪽으로 휘어짐 (포물선 효과)
    curveDirection = -1;
  } else {
    curveDirection = direction === 'up' ? -1 : 1;
  }
  
  // 제어점 계산 (베지어 곡선용)
  const controlPoint: Point = {
    x: midX,
    y: midY + (curveHeight * curveDirection),
  };
  
  // 경로 포인트 생성 (10개 포인트)
  const points: Point[] = [];
  const steps = 10;
  
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const point = quadraticBezier(start, controlPoint, end, t);
    points.push(point);
  }
  
  return points;
}

/**
 * 2차 베지어 곡선 계산
 */
function quadraticBezier(
  p0: Point,
  p1: Point,
  p2: Point,
  t: number
): Point {
  const x = Math.pow(1 - t, 2) * p0.x + 
            2 * (1 - t) * t * p1.x + 
            Math.pow(t, 2) * p2.x;
  const y = Math.pow(1 - t, 2) * p0.y + 
            2 * (1 - t) * t * p1.y + 
            Math.pow(t, 2) * p2.y;
  return { x, y };
}

/**
 * 아크(호) 경로 계산
 * 팟 수거 애니메이션에 사용됩니다.
 */
export function calculateArcPath(
  start: Point,
  end: Point,
  arcHeight: number = 50
): string {
  const midX = (start.x + end.x) / 2;
  const midY = Math.min(start.y, end.y) - arcHeight;
  
  // SVG path 문자열 반환
  return `M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`;
}

/**
 * 원형 경로 계산
 * 칩 수거 애니메이션에 사용됩니다.
 */
export function calculateCircularPath(
  center: Point,
  radius: number,
  startAngle: number,
  endAngle: number,
  steps: number = 20
): Point[] {
  const points: Point[] = [];
  const angleStep = (endAngle - startAngle) / steps;
  
  for (let i = 0; i <= steps; i++) {
    const angle = startAngle + (angleStep * i);
    const radians = (angle * Math.PI) / 180;
    points.push({
      x: center.x + radius * Math.cos(radians),
      y: center.y + radius * Math.sin(radians),
    });
  }
  
  return points;
}

/**
 * 플레이어 좌석 위치에서 테이블 중앙까지의 경로 생성
 */
export function createChipToTablePath(
  seatPosition: Point,
  tableCenter: Point,
  curvature: number = 0.25
): Point[] {
  return calculateCurvedPath(seatPosition, tableCenter, {
    curvature,
    direction: 'up',
  });
}

/**
 * 테이블 중앙에서 승자 좌석까지의 경로 생성
 */
export function createPotToWinnerPath(
  tableCenter: Point,
  winnerPosition: Point,
  curvature: number = 0.2
): Point[] {
  return calculateCurvedPath(tableCenter, winnerPosition, {
    curvature,
    direction: 'up',
  });
}

/**
 * 여러 칩의 흩어진 위치 생성
 */
export function generateScatteredPositions(
  center: Point,
  count: number,
  radius: number = 30
): Point[] {
  const positions: Point[] = [];
  
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * 2 * Math.PI + Math.random() * 0.5;
    const r = radius * (0.5 + Math.random() * 0.5);
    positions.push({
      x: center.x + r * Math.cos(angle),
      y: center.y + r * Math.sin(angle),
    });
  }
  
  return positions;
}

/**
 * Framer Motion keyframes 형식으로 경로 변환
 */
export function pathToKeyframes(points: Point[]): { x: number[]; y: number[] } {
  return {
    x: points.map(p => p.x),
    y: points.map(p => p.y),
  };
}
