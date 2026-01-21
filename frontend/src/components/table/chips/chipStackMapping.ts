/**
 * 칩 스택 이미지 매핑
 *
 * 금액에 따라 미리 생성된 칩 스택 이미지를 반환합니다.
 * 20단계의 이미지가 있으며, 금액 범위에 따라 적절한 이미지가 선택됩니다.
 *
 * 설계 원칙:
 * - 하위 금액(1-100)에 더 많은 단계 배치 (7단계)
 * - 중간 금액(100-1000)에 적당한 단계 (6단계)
 * - 상위 금액(1000+)에 넓은 간격 (7단계)
 * - BB 기반 게임에서 1BB~100BB+ 범위 커버
 */

// 금액 범위 → 이미지 매핑 테이블 (하위 금액 촘촘하게)
export const CHIP_STACK_THRESHOLDS = [
  // 1-100 범위 (7단계) - BB 단위 베팅 커버
  { min: 0, max: 5, image: 'stack_01.webp' },      // 1-5: 1칩
  { min: 6, max: 10, image: 'stack_02.webp' },     // 6-10: 2칩
  { min: 11, max: 20, image: 'stack_03.webp' },    // 11-20: 3칩
  { min: 21, max: 30, image: 'stack_04.webp' },    // 21-30: 4칩
  { min: 31, max: 50, image: 'stack_05.webp' },    // 31-50: 5칩
  { min: 51, max: 75, image: 'stack_06.webp' },    // 51-75: 6칩
  { min: 76, max: 100, image: 'stack_07.webp' },   // 76-100: 7칩

  // 100-1000 범위 (6단계)
  { min: 101, max: 150, image: 'stack_08.webp' },  // 101-150: 8칩
  { min: 151, max: 200, image: 'stack_10.webp' },  // 151-200: 10칩
  { min: 201, max: 300, image: 'stack_12.webp' },  // 201-300: 12칩
  { min: 301, max: 500, image: 'stack_15.webp' },  // 301-500: 15칩
  { min: 501, max: 750, image: 'stack_18.webp' },  // 501-750: 18칩
  { min: 751, max: 1000, image: 'stack_20.webp' }, // 751-1000: 20칩

  // 1000+ 범위 (7단계)
  { min: 1001, max: 1500, image: 'stack_25.webp' },  // 1001-1500: 25칩
  { min: 1501, max: 2500, image: 'stack_30.webp' },  // 1501-2500: 30칩
  { min: 2501, max: 5000, image: 'stack_35.webp' },  // 2501-5000: 35칩
  { min: 5001, max: 10000, image: 'stack_40.webp' }, // 5001-10000: 40칩
  { min: 10001, max: 25000, image: 'stack_50.webp' }, // 10001-25000: 50칩
  { min: 25001, max: 100000, image: 'stack_60.webp' }, // 25001-100000: 60칩
  { min: 100001, max: Infinity, image: 'stack_max.webp' }, // 100001+: 최대
] as const;

// 이미지 경로 기본값
const CHIP_STACKS_BASE_PATH = '/assets/chips/stacks';

/**
 * 금액에 해당하는 칩 스택 이미지 경로 반환
 * O(1) 룩업 (12개 이하의 비교)
 */
export function getChipStackImage(amount: number): string {
  // 빈 금액 처리
  if (amount <= 0) {
    return `${CHIP_STACKS_BASE_PATH}/stack_01.webp`;
  }

  // 테이블에서 해당 범위 찾기
  const threshold = CHIP_STACK_THRESHOLDS.find(
    (t) => amount >= t.min && amount <= t.max
  );

  return `${CHIP_STACKS_BASE_PATH}/${threshold?.image ?? 'stack_01.webp'}`;
}

/**
 * 모든 칩 스택 이미지 경로 목록 (프리로딩용)
 */
export function getAllChipStackImages(): string[] {
  return CHIP_STACK_THRESHOLDS.map(
    (t) => `${CHIP_STACKS_BASE_PATH}/${t.image}`
  );
}

// 프리로딩 상태 추적
let preloadPromise: Promise<void> | null = null;

/**
 * 모든 칩 스택 이미지를 미리 로드
 * 한 번만 실행되며, 중복 호출 시 기존 Promise 반환
 */
export function preloadChipStackImages(): Promise<void> {
  if (preloadPromise) {
    return preloadPromise;
  }

  const images = getAllChipStackImages();

  preloadPromise = Promise.all(
    images.map(
      (src) =>
        new Promise<void>((resolve) => {
          const img = new Image();
          img.onload = () => resolve();
          img.onerror = () => resolve(); // 에러 시에도 계속 진행
          img.src = src;
        })
    )
  ).then(() => {
    // 완료 시 아무것도 반환하지 않음
  });

  return preloadPromise;
}
