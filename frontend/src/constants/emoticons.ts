/**
 * 이모티콘 상수 정의
 * backend/app/services/emoticon.py와 동기화
 */

export type EmoticonCategory = 'basic' | 'poker' | 'emotion' | 'celebration' | 'taunt';

export interface Emoticon {
  id: string;
  name: string;
  emoji: string;
  imageUrl: string | null;
  category: EmoticonCategory;
  soundUrl: string | null;
  isPremium: boolean;
}

export const EMOTICON_CATEGORIES: { id: EmoticonCategory; name: string; icon: string }[] = [
  { id: 'basic', name: '기본', icon: '👋' },
  { id: 'poker', name: '포커', icon: '🃏' },
  { id: 'emotion', name: '감정', icon: '😊' },
  { id: 'celebration', name: '축하', icon: '🎉' },
  { id: 'taunt', name: '도발', icon: '🤣' },
];

export const EMOTICONS: Emoticon[] = [
  // 기본 감정
  {
    id: 'thumbs_up',
    name: '좋아요',
    emoji: '👍',
    imageUrl: '/assets/emoticons/thumbs_up.png',
    category: 'basic',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'thumbs_down',
    name: '별로',
    emoji: '👎',
    imageUrl: '/assets/emoticons/thumbs_down.png',
    category: 'basic',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'clap',
    name: '박수',
    emoji: '👏',
    imageUrl: '/assets/emoticons/clap.png',
    category: 'basic',
    soundUrl: '/sounds/clap.webm',
    isPremium: false,
  },
  {
    id: 'wave',
    name: '인사',
    emoji: '👋',
    imageUrl: '/assets/emoticons/wave.png',
    category: 'basic',
    soundUrl: null,
    isPremium: false,
  },

  // 포커 관련
  {
    id: 'good_game',
    name: 'GG',
    emoji: '🎰',
    imageUrl: '/assets/emoticons/good_game.png',
    category: 'poker',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'nice_hand',
    name: '나이스 핸드',
    emoji: '🃏',
    imageUrl: '/assets/emoticons/nice_hand.png',
    category: 'poker',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'all_in',
    name: '올인!',
    emoji: '💰',
    imageUrl: '/assets/emoticons/all_in.png',
    category: 'poker',
    soundUrl: '/sounds/all_in.webm',
    isPremium: false,
  },
  {
    id: 'bluff',
    name: '블러프',
    emoji: '🎭',
    imageUrl: '/assets/emoticons/bluff.png',
    category: 'poker',
    soundUrl: null,
    isPremium: false,
  },

  // 감정 표현
  {
    id: 'smile',
    name: '웃음',
    emoji: '😊',
    imageUrl: '/assets/emoticons/smile.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'cry',
    name: '울음',
    emoji: '😢',
    imageUrl: '/assets/emoticons/cry.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'angry',
    name: '화남',
    emoji: '😠',
    imageUrl: '/assets/emoticons/angry.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'shocked',
    name: '놀람',
    emoji: '😱',
    imageUrl: '/assets/emoticons/shocked.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'thinking',
    name: '생각중',
    emoji: '🤔',
    imageUrl: '/assets/emoticons/thinking.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'cool',
    name: '쿨',
    emoji: '😎',
    imageUrl: '/assets/emoticons/cool.png',
    category: 'emotion',
    soundUrl: null,
    isPremium: false,
  },

  // 축하/승리
  {
    id: 'trophy',
    name: '트로피',
    emoji: '🏆',
    imageUrl: '/assets/emoticons/trophy.png',
    category: 'celebration',
    soundUrl: '/sounds/winner.webm',
    isPremium: false,
  },
  {
    id: 'party',
    name: '파티',
    emoji: '🎉',
    imageUrl: '/assets/emoticons/party.png',
    category: 'celebration',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'fire',
    name: '불꽃',
    emoji: '🔥',
    imageUrl: '/assets/emoticons/fire.png',
    category: 'celebration',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'money_bag',
    name: '돈주머니',
    emoji: '💵',
    imageUrl: '/assets/emoticons/money_bag.png',
    category: 'celebration',
    soundUrl: null,
    isPremium: false,
  },

  // 도발
  {
    id: 'laugh',
    name: '웃김',
    emoji: '🤣',
    imageUrl: '/assets/emoticons/laugh.png',
    category: 'taunt',
    soundUrl: null,
    isPremium: false,
  },
  {
    id: 'slow',
    name: '빨리빨리',
    emoji: '🐢',
    imageUrl: '/assets/emoticons/slow.png',
    category: 'taunt',
    soundUrl: null,
    isPremium: false,
  },
];

// ID로 이모티콘 빠른 조회
export const EMOTICON_MAP: Record<string, Emoticon> = EMOTICONS.reduce(
  (acc, emoticon) => {
    acc[emoticon.id] = emoticon;
    return acc;
  },
  {} as Record<string, Emoticon>
);

// 카테고리별 이모티콘 조회
export function getEmoticonsByCategory(category: EmoticonCategory): Emoticon[] {
  return EMOTICONS.filter((e) => e.category === category);
}

// ID로 이모티콘 조회
export function getEmoticonById(id: string): Emoticon | undefined {
  return EMOTICON_MAP[id];
}
