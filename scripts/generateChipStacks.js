/**
 * 칩 스택 이미지 생성 스크립트
 *
 * 기존 단일 칩 SVG(bluechip, greenchip, chip_stack)를 조합하여
 * 20개의 칩 스택 이미지를 생성합니다.
 *
 * 배치: 3줄 (앞2 뒤1)
 *       [뒤]
 *    [앞좌][앞우]
 *
 * 사용법: node scripts/generateChipStacks.js
 * 의존성: npm install sharp
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// 경로 설정
const CHIPS_DIR = path.join(__dirname, '../frontend/public/assets/chips');
const OUTPUT_DIR = path.join(CHIPS_DIR, 'stacks');

// 기존 단일 칩 SVG 파일
const CHIP_SVGS = {
  red: path.join(CHIPS_DIR, 'chip_stack.svg'),    // 빨간색 칩
  green: path.join(CHIPS_DIR, 'greenchip.svg'),   // 초록색 칩
  blue: path.join(CHIPS_DIR, 'bluechip.svg'),     // 파란색 칩
};

// 칩 스택 정의 (파일명, 칩 개수)
const CHIP_STACKS = [
  { name: 'stack_01', count: 1 },
  { name: 'stack_02', count: 2 },
  { name: 'stack_03', count: 3 },
  { name: 'stack_04', count: 4 },
  { name: 'stack_05', count: 5 },
  { name: 'stack_06', count: 6 },
  { name: 'stack_07', count: 7 },
  { name: 'stack_08', count: 8 },
  { name: 'stack_10', count: 10 },
  { name: 'stack_12', count: 12 },
  { name: 'stack_15', count: 15 },
  { name: 'stack_18', count: 18 },
  { name: 'stack_20', count: 20 },
  { name: 'stack_25', count: 25 },
  { name: 'stack_30', count: 30 },
  { name: 'stack_35', count: 35 },
  { name: 'stack_40', count: 40 },
  { name: 'stack_50', count: 50 },
  { name: 'stack_60', count: 60 },
  { name: 'stack_max', count: 80 },
];

// 칩 크기 설정
const CHIP_WIDTH = 32;
const CHIP_HEIGHT = 19;
const CHIP_VERTICAL_OVERLAP = 14; // 세로 겹침 (칩이 쌓이는 효과)
const STACK_HORIZONTAL_GAP = 8;   // 스택 간 가로 간격
const STACK_VERTICAL_OFFSET = 6;  // 앞뒤 스택 세로 오프셋

/**
 * 단일 칩 PNG 버퍼 생성
 */
async function getChipPNG(color) {
  const svgPath = CHIP_SVGS[color];
  return sharp(svgPath)
    .resize(CHIP_WIDTH, CHIP_HEIGHT)
    .png()
    .toBuffer();
}

/**
 * 칩 개수를 3개 스택으로 분배
 */
function distributeChips(totalCount) {
  if (totalCount <= 2) {
    // 1-2개: 스택 1개만
    return [totalCount, 0, 0];
  } else if (totalCount <= 5) {
    // 3-5개: 스택 2개 (앞좌, 앞우)
    const left = Math.ceil(totalCount / 2);
    const right = totalCount - left;
    return [0, left, right];
  } else {
    // 6개 이상: 스택 3개 (뒤, 앞좌, 앞우)
    const back = Math.ceil(totalCount / 3);
    const frontLeft = Math.ceil((totalCount - back) / 2);
    const frontRight = totalCount - back - frontLeft;
    return [back, frontLeft, frontRight];
  }
}

/**
 * 색상 패턴 결정
 */
function getColorPattern(chipCount) {
  if (chipCount <= 5) {
    return ['red'];  // 빨강만
  } else if (chipCount <= 12) {
    return ['red', 'red', 'red', 'green'];  // 빨강 + 초록
  } else if (chipCount <= 25) {
    return ['red', 'green', 'green', 'green'];  // 초록 위주
  } else if (chipCount <= 40) {
    return ['green', 'green', 'blue', 'blue'];  // 초록 + 파랑
  } else {
    return ['green', 'blue', 'blue', 'blue'];  // 파랑 위주
  }
}

/**
 * 단일 스택의 칩들 생성
 */
function createStackComposites(chipCount, baseX, baseY, chipBuffers, colorPattern) {
  const composites = [];

  for (let i = 0; i < chipCount; i++) {
    // 아래부터 쌓임 (맨 아래 칩이 먼저)
    const y = baseY - i * (CHIP_HEIGHT - CHIP_VERTICAL_OVERLAP);
    const color = colorPattern[i % colorPattern.length];

    composites.push({
      input: chipBuffers[color],
      top: Math.round(y),
      left: Math.round(baseX),
    });
  }

  return composites;
}

/**
 * 칩 스택 이미지 생성 (3줄 배치)
 */
async function generateChipStack(name, totalCount, chipBuffers) {
  const [backCount, frontLeftCount, frontRightCount] = distributeChips(totalCount);
  const colorPattern = getColorPattern(totalCount);

  // 각 스택의 높이 계산
  const backHeight = backCount > 0 ? CHIP_HEIGHT + (backCount - 1) * (CHIP_HEIGHT - CHIP_VERTICAL_OVERLAP) : 0;
  const frontLeftHeight = frontLeftCount > 0 ? CHIP_HEIGHT + (frontLeftCount - 1) * (CHIP_HEIGHT - CHIP_VERTICAL_OVERLAP) : 0;
  const frontRightHeight = frontRightCount > 0 ? CHIP_HEIGHT + (frontRightCount - 1) * (CHIP_HEIGHT - CHIP_VERTICAL_OVERLAP) : 0;

  // 캔버스 크기 계산
  let canvasWidth, canvasHeight;

  if (backCount === 0 && frontRightCount === 0) {
    // 스택 1개 (앞좌만)
    canvasWidth = CHIP_WIDTH;
    canvasHeight = frontLeftHeight;
  } else if (backCount === 0) {
    // 스택 2개 (앞좌, 앞우)
    canvasWidth = CHIP_WIDTH * 2 + STACK_HORIZONTAL_GAP;
    canvasHeight = Math.max(frontLeftHeight, frontRightHeight);
  } else {
    // 스택 3개
    canvasWidth = CHIP_WIDTH * 2 + STACK_HORIZONTAL_GAP;
    canvasHeight = Math.max(backHeight, frontLeftHeight, frontRightHeight) + STACK_VERTICAL_OFFSET;
  }

  const composites = [];

  // 뒤 스택 (중앙 상단) - 먼저 그려서 뒤에 배치
  if (backCount > 0) {
    const backX = (canvasWidth - CHIP_WIDTH) / 2;
    const backBaseY = canvasHeight - backHeight;
    composites.push(...createStackComposites(backCount, backX, backBaseY + backHeight - CHIP_HEIGHT, chipBuffers, colorPattern));
  }

  // 앞 왼쪽 스택
  if (frontLeftCount > 0) {
    const frontLeftX = 0;
    const frontLeftBaseY = canvasHeight - frontLeftHeight + (backCount > 0 ? STACK_VERTICAL_OFFSET : 0);
    composites.push(...createStackComposites(frontLeftCount, frontLeftX, frontLeftBaseY + frontLeftHeight - CHIP_HEIGHT, chipBuffers, colorPattern));
  }

  // 앞 오른쪽 스택
  if (frontRightCount > 0) {
    const frontRightX = CHIP_WIDTH + STACK_HORIZONTAL_GAP;
    const frontRightBaseY = canvasHeight - frontRightHeight + (backCount > 0 ? STACK_VERTICAL_OFFSET : 0);
    composites.push(...createStackComposites(frontRightCount, frontRightX, frontRightBaseY + frontRightHeight - CHIP_HEIGHT, chipBuffers, colorPattern));
  }

  // 캔버스 생성 및 합성
  const outputPath = path.join(OUTPUT_DIR, `${name}.webp`);

  await sharp({
    create: {
      width: Math.round(canvasWidth),
      height: Math.round(canvasHeight),
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  })
    .composite(composites)
    .webp({ quality: 90 })
    .toFile(outputPath);

  const distribution = `[${backCount}|${frontLeftCount}|${frontRightCount}]`;
  console.log(`✓ ${name}.webp (${totalCount}개 ${distribution}, ${Math.round(canvasWidth)}x${Math.round(canvasHeight)}px)`);
}

/**
 * 메인 실행
 */
async function main() {
  console.log('🎰 칩 스택 이미지 생성 시작 (3줄 배치: 앞2 뒤1)...\n');

  // 출력 디렉토리 확인
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // 기존 SVG 파일 확인
  for (const [color, svgPath] of Object.entries(CHIP_SVGS)) {
    if (!fs.existsSync(svgPath)) {
      console.error(`❌ 칩 SVG 파일을 찾을 수 없습니다: ${svgPath}`);
      process.exit(1);
    }
    console.log(`✓ 발견: ${color} 칩 (${path.basename(svgPath)})`);
  }
  console.log('');

  // 단일 칩 PNG 버퍼 미리 생성
  console.log('📦 단일 칩 PNG 변환 중...');
  const chipBuffers = {
    red: await getChipPNG('red'),
    green: await getChipPNG('green'),
    blue: await getChipPNG('blue'),
  };
  console.log('');

  // 모든 스택 생성
  console.log('🔨 스택 이미지 생성 중...');
  for (const stack of CHIP_STACKS) {
    await generateChipStack(stack.name, stack.count, chipBuffers);
  }

  console.log(`\n✅ 완료! ${CHIP_STACKS.length}개 이미지가 생성되었습니다.`);
  console.log(`📁 출력 위치: ${OUTPUT_DIR}`);
}

main().catch(console.error);
