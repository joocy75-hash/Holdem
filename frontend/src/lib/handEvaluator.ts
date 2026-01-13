/**
 * 텍사스 홀덤 핸드 평가기
 * 클라이언트 사이드에서 실시간 족보 표시용
 */

export interface Card {
  rank: string; // "2"-"9", "T", "J", "Q", "K", "A"
  suit: string; // "s", "h", "d", "c"
}

export interface HandResult {
  rank: number; // 1-10 (높을수록 강함)
  name: string; // 한글 족보 이름
  nameEn: string; // 영어 족보 이름
  description: string; // 상세 설명 (예: "에이스 원페어")
  bestFive: Card[]; // 최고 5장 조합
}

// 랭크 값 매핑 (2=2, ..., A=14)
const RANK_VALUES: Record<string, number> = {
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "6": 6,
  "7": 7,
  "8": 8,
  "9": 9,
  T: 10,
  J: 11,
  Q: 12,
  K: 13,
  A: 14,
};

// 랭크 이름 매핑
const RANK_NAMES: Record<string, string> = {
  "2": "2",
  "3": "3",
  "4": "4",
  "5": "5",
  "6": "6",
  "7": "7",
  "8": "8",
  "9": "9",
  T: "10",
  J: "J",
  Q: "Q",
  K: "K",
  A: "A",
};

// 족보 랭크
export const HAND_RANKS = {
  HIGH_CARD: 1,
  ONE_PAIR: 2,
  TWO_PAIR: 3,
  THREE_OF_A_KIND: 4,
  STRAIGHT: 5,
  FLUSH: 6,
  FULL_HOUSE: 7,
  FOUR_OF_A_KIND: 8,
  STRAIGHT_FLUSH: 9,
  ROYAL_FLUSH: 10,
} as const;

// 족보 이름
const HAND_NAMES: Record<number, { ko: string; en: string }> = {
  1: { ko: "하이카드", en: "High Card" },
  2: { ko: "원페어", en: "One Pair" },
  3: { ko: "투페어", en: "Two Pair" },
  4: { ko: "트리플", en: "Three of a Kind" },
  5: { ko: "스트레이트", en: "Straight" },
  6: { ko: "플러시", en: "Flush" },
  7: { ko: "풀하우스", en: "Full House" },
  8: { ko: "포카드", en: "Four of a Kind" },
  9: { ko: "스트레이트 플러시", en: "Straight Flush" },
  10: { ko: "로얄 플러시", en: "Royal Flush" },
};

/**
 * 카드 배열을 랭크 값 기준으로 내림차순 정렬
 */
function sortByRank(cards: Card[]): Card[] {
  return [...cards].sort(
    (a, b) => RANK_VALUES[b.rank] - RANK_VALUES[a.rank]
  );
}

/**
 * 랭크별 카드 그룹핑
 */
function groupByRank(cards: Card[]): Map<string, Card[]> {
  const groups = new Map<string, Card[]>();
  for (const card of cards) {
    const existing = groups.get(card.rank) || [];
    existing.push(card);
    groups.set(card.rank, existing);
  }
  return groups;
}

/**
 * 슈트별 카드 그룹핑
 */
function groupBySuit(cards: Card[]): Map<string, Card[]> {
  const groups = new Map<string, Card[]>();
  for (const card of cards) {
    const existing = groups.get(card.suit) || [];
    existing.push(card);
    groups.set(card.suit, existing);
  }
  return groups;
}

/**
 * 플러시 확인 (5장 이상 같은 슈트)
 */
function findFlush(cards: Card[]): Card[] | null {
  const suitGroups = groupBySuit(cards);
  for (const [, suited] of suitGroups) {
    if (suited.length >= 5) {
      return sortByRank(suited).slice(0, 5);
    }
  }
  return null;
}

/**
 * 스트레이트 확인
 */
function findStraight(cards: Card[]): Card[] | null {
  // 유니크한 랭크만 추출하고 정렬
  const uniqueRanks = new Map<number, Card>();
  for (const card of cards) {
    const value = RANK_VALUES[card.rank];
    if (!uniqueRanks.has(value)) {
      uniqueRanks.set(value, card);
    }
  }

  const sortedValues = Array.from(uniqueRanks.keys()).sort((a, b) => b - a);

  // A-2-3-4-5 (휠) 처리를 위해 A를 1로도 추가
  if (uniqueRanks.has(14)) {
    sortedValues.push(1);
  }

  // 연속된 5개 찾기
  for (let i = 0; i <= sortedValues.length - 5; i++) {
    let consecutive = true;
    for (let j = 0; j < 4; j++) {
      if (sortedValues[i + j] - sortedValues[i + j + 1] !== 1) {
        consecutive = false;
        break;
      }
    }
    if (consecutive) {
      const straightCards: Card[] = [];
      for (let j = 0; j < 5; j++) {
        const value = sortedValues[i + j];
        // 휠의 경우 1은 A로 매핑
        const card = uniqueRanks.get(value === 1 ? 14 : value);
        if (card) straightCards.push(card);
      }
      return straightCards;
    }
  }
  return null;
}

/**
 * 스트레이트 플러시 확인
 */
function findStraightFlush(cards: Card[]): { cards: Card[]; isRoyal: boolean } | null {
  const suitGroups = groupBySuit(cards);

  for (const [, suited] of suitGroups) {
    if (suited.length >= 5) {
      const straight = findStraight(suited);
      if (straight) {
        // 로얄 플러시 확인 (A-K-Q-J-T)
        const values = straight.map((c) => RANK_VALUES[c.rank]);
        const isRoyal = values.includes(14) && values.includes(13) &&
                        values.includes(12) && values.includes(11) && values.includes(10);
        return { cards: straight, isRoyal };
      }
    }
  }
  return null;
}

/**
 * N개 같은 랭크 찾기
 */
function findOfAKind(cards: Card[], count: number): { rank: string; cards: Card[] } | null {
  const groups = groupByRank(cards);
  const sorted = Array.from(groups.entries())
    .filter(([, g]) => g.length >= count)
    .sort((a, b) => RANK_VALUES[b[0]] - RANK_VALUES[a[0]]);

  if (sorted.length > 0) {
    return { rank: sorted[0][0], cards: sorted[0][1].slice(0, count) };
  }
  return null;
}

/**
 * 페어들 찾기 (투페어용)
 */
function findPairs(cards: Card[]): { rank: string; cards: Card[] }[] {
  const groups = groupByRank(cards);
  return Array.from(groups.entries())
    .filter(([, g]) => g.length >= 2)
    .map(([rank, g]) => ({ rank, cards: g.slice(0, 2) }))
    .sort((a, b) => RANK_VALUES[b.rank] - RANK_VALUES[a.rank]);
}

/**
 * 키커 카드 선택 (사용된 카드 제외하고 높은 순서대로)
 */
function getKickers(cards: Card[], usedCards: Card[], count: number): Card[] {
  const usedSet = new Set(usedCards.map((c) => `${c.rank}${c.suit}`));
  return sortByRank(cards)
    .filter((c) => !usedSet.has(`${c.rank}${c.suit}`))
    .slice(0, count);
}

/**
 * 핸드 평가 메인 함수
 */
export function evaluateHand(cards: Card[]): HandResult | null {
  if (cards.length < 2) {
    return null;
  }

  // 프리플랍 (2장만 있을 때) - 특별 처리
  if (cards.length === 2) {
    return evaluatePreflopHand(cards);
  }

  // 스트레이트 플러시 / 로얄 플러시
  const straightFlush = findStraightFlush(cards);
  if (straightFlush) {
    if (straightFlush.isRoyal) {
      return {
        rank: HAND_RANKS.ROYAL_FLUSH,
        name: HAND_NAMES[10].ko,
        nameEn: HAND_NAMES[10].en,
        description: "로얄 플러시",
        bestFive: straightFlush.cards,
      };
    }
    const highCard = straightFlush.cards[0];
    return {
      rank: HAND_RANKS.STRAIGHT_FLUSH,
      name: HAND_NAMES[9].ko,
      nameEn: HAND_NAMES[9].en,
      description: `${RANK_NAMES[highCard.rank]} 하이 스트레이트 플러시`,
      bestFive: straightFlush.cards,
    };
  }

  // 포카드
  const quads = findOfAKind(cards, 4);
  if (quads) {
    const kickers = getKickers(cards, quads.cards, 1);
    return {
      rank: HAND_RANKS.FOUR_OF_A_KIND,
      name: HAND_NAMES[8].ko,
      nameEn: HAND_NAMES[8].en,
      description: `${RANK_NAMES[quads.rank]} 포카드`,
      bestFive: [...quads.cards, ...kickers],
    };
  }

  // 풀하우스
  const trips = findOfAKind(cards, 3);
  if (trips) {
    const remainingCards = cards.filter(
      (c) => !trips.cards.some((t) => t.rank === c.rank && t.suit === c.suit)
    );
    const pair = findOfAKind(remainingCards, 2);
    if (pair) {
      return {
        rank: HAND_RANKS.FULL_HOUSE,
        name: HAND_NAMES[7].ko,
        nameEn: HAND_NAMES[7].en,
        description: `${RANK_NAMES[trips.rank]} 풀 오브 ${RANK_NAMES[pair.rank]}`,
        bestFive: [...trips.cards, ...pair.cards],
      };
    }
  }

  // 플러시
  const flush = findFlush(cards);
  if (flush) {
    const highCard = flush[0];
    return {
      rank: HAND_RANKS.FLUSH,
      name: HAND_NAMES[6].ko,
      nameEn: HAND_NAMES[6].en,
      description: `${RANK_NAMES[highCard.rank]} 하이 플러시`,
      bestFive: flush,
    };
  }

  // 스트레이트
  const straight = findStraight(cards);
  if (straight) {
    const highCard = straight[0];
    // 휠(A-2-3-4-5)인 경우 5 하이
    const isWheel = RANK_VALUES[highCard.rank] === 14 &&
                    straight.some((c) => RANK_VALUES[c.rank] === 5);
    return {
      rank: HAND_RANKS.STRAIGHT,
      name: HAND_NAMES[5].ko,
      nameEn: HAND_NAMES[5].en,
      description: isWheel ? "5 하이 스트레이트" : `${RANK_NAMES[highCard.rank]} 하이 스트레이트`,
      bestFive: straight,
    };
  }

  // 트리플
  if (trips) {
    const kickers = getKickers(cards, trips.cards, 2);
    return {
      rank: HAND_RANKS.THREE_OF_A_KIND,
      name: HAND_NAMES[4].ko,
      nameEn: HAND_NAMES[4].en,
      description: `${RANK_NAMES[trips.rank]} 트리플`,
      bestFive: [...trips.cards, ...kickers],
    };
  }

  // 투페어
  const pairs = findPairs(cards);
  if (pairs.length >= 2) {
    const topTwo = pairs.slice(0, 2);
    const usedCards = [...topTwo[0].cards, ...topTwo[1].cards];
    const kickers = getKickers(cards, usedCards, 1);
    return {
      rank: HAND_RANKS.TWO_PAIR,
      name: HAND_NAMES[3].ko,
      nameEn: HAND_NAMES[3].en,
      description: `${RANK_NAMES[topTwo[0].rank]}와 ${RANK_NAMES[topTwo[1].rank]} 투페어`,
      bestFive: [...topTwo[0].cards, ...topTwo[1].cards, ...kickers],
    };
  }

  // 원페어
  if (pairs.length === 1) {
    const kickers = getKickers(cards, pairs[0].cards, 3);
    return {
      rank: HAND_RANKS.ONE_PAIR,
      name: HAND_NAMES[2].ko,
      nameEn: HAND_NAMES[2].en,
      description: `${RANK_NAMES[pairs[0].rank]} 원페어`,
      bestFive: [...pairs[0].cards, ...kickers],
    };
  }

  // 하이카드
  const sorted = sortByRank(cards).slice(0, 5);
  return {
    rank: HAND_RANKS.HIGH_CARD,
    name: HAND_NAMES[1].ko,
    nameEn: HAND_NAMES[1].en,
    description: `${RANK_NAMES[sorted[0].rank]} 하이카드`,
    bestFive: sorted,
  };
}

/**
 * 프리플랍 핸드 평가 (2장만)
 */
function evaluatePreflopHand(cards: Card[]): HandResult {
  const [c1, c2] = cards;
  const r1 = c1.rank;
  const r2 = c2.rank;
  const suited = c1.suit === c2.suit;
  const v1 = RANK_VALUES[r1];
  const v2 = RANK_VALUES[r2];

  // 포켓 페어
  if (r1 === r2) {
    return {
      rank: HAND_RANKS.ONE_PAIR,
      name: HAND_NAMES[2].ko,
      nameEn: HAND_NAMES[2].en,
      description: `포켓 ${RANK_NAMES[r1]}`,
      bestFive: cards,
    };
  }

  // 하이카드 (높은 카드 먼저)
  const sorted = v1 > v2 ? [c1, c2] : [c2, c1];
  const highRank = sorted[0].rank;
  const lowRank = sorted[1].rank;
  const suitedStr = suited ? " 수딧" : "";

  return {
    rank: HAND_RANKS.HIGH_CARD,
    name: HAND_NAMES[1].ko,
    nameEn: HAND_NAMES[1].en,
    description: `${RANK_NAMES[highRank]}-${RANK_NAMES[lowRank]} 하이카드${suitedStr}`,
    bestFive: sorted,
  };
}

/**
 * 드로우 가능성 평가 (플러시 드로우, 스트레이트 드로우)
 */
export function evaluateDraws(cards: Card[]): string[] {
  const draws: string[] = [];

  if (cards.length < 4) return draws;

  // 플러시 드로우 (4장 같은 슈트)
  const suitGroups = groupBySuit(cards);
  for (const [, suited] of suitGroups) {
    if (suited.length === 4) {
      draws.push("플러시 드로우");
      break;
    }
  }

  // 스트레이트 드로우 확인
  const uniqueValues = [...new Set(cards.map((c) => RANK_VALUES[c.rank]))].sort(
    (a, b) => a - b
  );

  // A도 1로 사용 가능
  if (uniqueValues.includes(14)) {
    uniqueValues.unshift(1);
  }

  // 오픈엔드 스트레이트 드로우 (4장 연속)
  for (let i = 0; i <= uniqueValues.length - 4; i++) {
    const slice = uniqueValues.slice(i, i + 4);
    if (slice[3] - slice[0] === 3) {
      // 양쪽 모두 카드가 올 수 있는지 확인
      const lowEnd = slice[0] - 1;
      const highEnd = slice[3] + 1;
      if (lowEnd >= 1 && highEnd <= 14) {
        draws.push("오픈엔드 스트레이트 드로우");
        break;
      }
    }
  }

  // 거셧 스트레이트 드로우 (중간에 1장 빠짐)
  if (!draws.includes("오픈엔드 스트레이트 드로우")) {
    for (let i = 0; i <= uniqueValues.length - 4; i++) {
      const slice = uniqueValues.slice(i, i + 4);
      if (slice[3] - slice[0] === 4) {
        // 4장 사이에 1개의 갭
        draws.push("거셧 스트레이트 드로우");
        break;
      }
    }
  }

  return draws;
}

/**
 * 완전한 핸드 분석 (족보 + 드로우)
 */
export function analyzeHand(holeCards: Card[], communityCards: Card[]): {
  hand: HandResult | null;
  draws: string[];
} {
  const allCards = [...holeCards, ...communityCards];
  const hand = evaluateHand(allCards);
  const draws = communityCards.length >= 3 && communityCards.length < 5
    ? evaluateDraws(allCards)
    : [];

  return { hand, draws };
}
