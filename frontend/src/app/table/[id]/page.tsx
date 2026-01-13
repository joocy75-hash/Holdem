'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { wsClient } from '@/lib/websocket';
import { analyzeHand, HandResult } from '@/lib/handEvaluator';

interface Card {
  rank: string;
  suit: string;
}

// 백엔드 TABLE_SNAPSHOT 구조에 맞춤
interface SeatInfo {
  position: number;
  player: {
    userId: string;
    nickname: string;
    avatarUrl?: string;
  } | null;
  stack: number;
  status: 'empty' | 'active' | 'waiting' | 'folded';
  betAmount: number;
}

interface TableConfig {
  maxSeats: number;
  smallBlind: number;
  bigBlind: number;
  minBuyIn: number;
  maxBuyIn: number;
  turnTimeoutSeconds: number;
}

// 이전 호환성을 위한 인터페이스
interface Player {
  id: string;
  username: string;
  chips: number;
  cards: Card[];
  bet: number;
  folded: boolean;
  isActive: boolean;
  seatIndex: number;
  hasCards?: boolean; // 카드를 받았는지 여부 (봇 카드 뒷면 표시용)
  isWinner?: boolean; // 승자 여부 (WIN 표시용)
  winAmount?: number; // 승리 금액
}

interface GameState {
  tableId: string;
  players: Player[];
  communityCards: Card[];
  pot: number;
  currentPlayer: string | null;
  phase: 'waiting' | 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
  smallBlind: number;
  bigBlind: number;
  minRaise: number;
  currentBet: number;
}

// 카드 형식 변환 함수 (문자열 "As", "Kh" → Card 객체)
function parseCard(card: string | Card | null | undefined): Card | null {
  if (!card) return null;
  if (typeof card === 'object' && card.rank && card.suit) {
    return card;
  }
  if (typeof card === 'string' && card.length >= 2) {
    return { rank: card.slice(0, -1), suit: card.slice(-1) };
  }
  return null;
}

function parseCards(cards: (string | Card | null | undefined)[] | null | undefined): Card[] {
  if (!cards || !Array.isArray(cards)) return [];
  return cards.map(parseCard).filter((c): c is Card => c !== null);
}

const SUIT_SYMBOLS: Record<string, string> = {
  hearts: '♥',
  diamonds: '♦',
  clubs: '♣',
  spades: '♠',
  h: '♥',
  d: '♦',
  c: '♣',
  s: '♠',
};

const SUIT_COLORS: Record<string, string> = {
  hearts: 'card-suit-red',
  diamonds: 'card-suit-red',
  clubs: 'card-suit-black',
  spades: 'card-suit-black',
  h: 'card-suit-red',
  d: 'card-suit-red',
  c: 'card-suit-black',
  s: 'card-suit-black',
};

function PlayingCard({ card, faceDown = false }: { card?: Card; faceDown?: boolean }) {
  if (faceDown || !card) {
    return <div className="playing-card face-down animate-card-deal" />;
  }

  // 카드 데이터 유효성 검사
  if (!card.suit || !card.rank) {
    console.warn('Invalid card data:', card);
    return <div className="playing-card face-down animate-card-deal" />;
  }

  const suitLower = card.suit.toLowerCase();
  const suitSymbol = SUIT_SYMBOLS[suitLower] || card.suit;
  const suitColor = SUIT_COLORS[suitLower] || 'card-suit-black';

  return (
    <div className={`playing-card animate-card-deal ${suitColor}`}>
      <span>{card.rank}</span>
      <span>{suitSymbol}</span>
    </div>
  );
}

// 액션 라벨 매핑 (한글)
const ACTION_LABELS: Record<string, { text: string; className: string }> = {
  fold: { text: '폴드', className: 'bg-red-500/80' },
  check: { text: '체크', className: 'bg-gray-500/80' },
  call: { text: '콜', className: 'bg-blue-500/80' },
  bet: { text: '베팅', className: 'bg-green-500/80' },
  raise: { text: '레이즈', className: 'bg-yellow-500/80' },
  all_in: { text: '올인', className: 'bg-purple-500/80' },
};

// 허용된 액션 타입 인터페이스
interface AllowedAction {
  type: string;
  amount?: number;    // 콜 금액 등
  minAmount?: number; // 최소 베팅/레이즈 금액
  maxAmount?: number; // 최대 베팅/레이즈 금액
}

// 턴 타이머 설정
const TURN_GRACE_PERIOD = 5; // 5초 대기
const TURN_COUNTDOWN = 5; // 5초 카운트다운
const TOTAL_TURN_TIME = TURN_GRACE_PERIOD + TURN_COUNTDOWN; // 총 10초

function PlayerSeat({
  player,
  position,
  isCurrentUser,
  isActive,
  lastAction,
  turnStartTime,
  onAutoFold,
  handResult,
  draws,
}: {
  player?: Player;
  position: { top: string; left: string };
  isCurrentUser: boolean;
  isActive: boolean;
  lastAction?: { type: string; amount?: number; timestamp: number } | null;
  turnStartTime?: number | null; // 턴 시작 시간 (Date.now())
  onAutoFold?: () => void; // 자동 폴드 콜백
  handResult?: HandResult | null; // 현재 족보 (자기 자신만)
  draws?: string[]; // 드로우 가능성 (플러시 드로우 등)
}) {
  // 액션 표시 여부 관리 (3초 후 자동 숨김)
  const [visibleAction, setVisibleAction] = useState<typeof lastAction>(null);
  // 턴 타이머 상태
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [showCountdown, setShowCountdown] = useState(false);

  // 액션 표시 효과
  useEffect(() => {
    // lastAction이 null이면 visibleAction도 즉시 null로 설정 (새 핸드 시작 시)
    if (!lastAction) {
      setVisibleAction(null);
      return;
    }

    const showTimer = setTimeout(() => {
      setVisibleAction(lastAction);
    }, 0);

    const hideTimer = setTimeout(() => {
      setVisibleAction(null);
    }, 3000);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
    };
  }, [lastAction]);

  // 턴 타이머 효과
  useEffect(() => {
    if (!isActive || !turnStartTime) {
      // 비동기로 상태 리셋
      const resetTimer = setTimeout(() => {
        setTimeRemaining(null);
        setShowCountdown(false);
      }, 0);
      return () => clearTimeout(resetTimer);
    }

    let autoFoldTriggered = false;

    const updateTimer = () => {
      const elapsed = (Date.now() - turnStartTime) / 1000;
      const remaining = TOTAL_TURN_TIME - elapsed;

      if (remaining <= 0) {
        setTimeRemaining(0);
        setShowCountdown(false);
        // 자동 폴드 (현재 유저만, 한 번만)
        if (isCurrentUser && onAutoFold && !autoFoldTriggered) {
          autoFoldTriggered = true;
          onAutoFold();
        }
        return;
      }

      setTimeRemaining(remaining);
      // 5초 대기 후 카운트다운 시작
      setShowCountdown(elapsed >= TURN_GRACE_PERIOD);
    };

    // 첫 업데이트도 비동기로
    const initTimer = setTimeout(updateTimer, 0);
    const interval = setInterval(updateTimer, 100);

    return () => {
      clearTimeout(initTimer);
      clearInterval(interval);
    };
  }, [isActive, turnStartTime, isCurrentUser, onAutoFold]);

  const showAction = visibleAction !== null;
  const actionInfo = visibleAction ? ACTION_LABELS[visibleAction.type.toLowerCase()] || { text: visibleAction.type.toUpperCase(), className: 'bg-gray-500/80' } : null;

  // 타이머 진행률 계산 (카운트다운 구간만)
  const timerProgress = timeRemaining !== null && showCountdown
    ? Math.max(0, (timeRemaining / TURN_COUNTDOWN) * 100)
    : 100;

  if (!player) {
    return (
      <div className="player-seat" style={position}>
        <div className="player-avatar bg-[var(--surface-hover)] opacity-50">
          <span className="text-2xl">+</span>
        </div>
        <div className="player-info flex flex-col items-center">
          <span className="player-name text-[var(--text-muted)]">빈 자리</span>
        </div>
      </div>
    );
  }

  // 폴드 상태 스타일
  const foldedClass = player.folded ? 'opacity-40 grayscale' : '';
  // 액션 표시 중일 때 z-index 높임 (다른 player-seat 위에 표시)
  const actionZIndex = showAction ? 'z-50' : '';

  return (
    <div className={`player-seat ${foldedClass} ${actionZIndex}`} style={position}>
      {/* 아바타 wrapper - 액션 모달과 타이머의 기준점 */}
      <div className="relative flex items-center justify-center">
        {/* 액션 표시 (아바타 바로 위 정중앙) */}
        {showAction && actionInfo && visibleAction && (
          <div
            className="absolute z-50"
            style={{
              bottom: '100%',
              left: '50%',
              transform: 'translateX(-50%)',
              marginBottom: '8px',
            }}
          >
            <div className={`px-3 py-1.5 rounded-full text-white text-sm font-bold shadow-xl animate-bounce-in whitespace-nowrap ${actionInfo.className}`}>
              {actionInfo.text}
              {visibleAction.amount && visibleAction.amount > 0 && ` ${visibleAction.amount.toLocaleString()}`}
            </div>
          </div>
        )}

        {/* 타이머 게이지 (카운트다운 시) */}
        {isActive && showCountdown && (
          <div
            className="absolute"
            style={{
              top: '-4px',
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
            <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
              {/* 배경 원 */}
              <circle
                cx="28"
                cy="28"
                r="24"
                fill="none"
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="4"
              />
              {/* 진행 원 */}
              <circle
                cx="28"
                cy="28"
                r="24"
                fill="none"
                stroke={timerProgress > 40 ? '#22c55e' : timerProgress > 20 ? '#f59e0b' : '#ef4444'}
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={`${(timerProgress / 100) * 150.8} 150.8`}
                className="transition-all duration-100"
              />
            </svg>
            {/* 카운트다운 숫자 */}
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-lg font-bold ${timerProgress > 40 ? 'text-green-400' : timerProgress > 20 ? 'text-yellow-400' : 'text-red-400'}`}>
                {Math.ceil(timeRemaining || 0)}
              </span>
            </div>
          </div>
        )}

        {/* 프로필 아바타 */}
        <div className={`player-avatar ${isActive && !showCountdown ? 'active' : ''} ${isCurrentUser ? 'border-[var(--primary)]' : ''} ${player.folded ? 'bg-gray-600' : ''}`}>
          {player.username.charAt(0).toUpperCase()}
        </div>
      </div>

      {/* 다른 플레이어 카드 (프로필 아래, 겹침 허용) */}
      {!isCurrentUser && !player.folded && (
        player.cards.length > 0 ? (
          <div className="flex -space-x-2 -mt-1">
            {player.cards.map((card, i) => (
              <div key={i} className="w-[18px] h-[25px]">
                <PlayingCard card={card} />
              </div>
            ))}
          </div>
        ) : player.hasCards ? (
          <div className="flex -space-x-2 -mt-1">
            <div className="w-[18px] h-[25px]"><PlayingCard faceDown /></div>
            <div className="w-[18px] h-[25px]"><PlayingCard faceDown /></div>
          </div>
        ) : null
      )}

      {/* 닉네임 → 보유금액 순서 */}
      <div className="player-info flex flex-col items-center gap-0.5">
        <span className={`player-name text-sm font-medium ${player.folded ? 'line-through text-gray-500' : ''}`}>{player.username}</span>
        <span className="player-chips text-xs text-[var(--accent)]">{player.chips.toLocaleString()}</span>
      </div>

      {/* ========================================
          내 카드 영역 (고정 높이: 76px)
          - 카드 56px + 족보 18px + 마진
          - 카드 없어도 공간 유지하여 레이아웃 시프트 방지
          ======================================== */}
      {isCurrentUser && (
        <div className="h-[76px] flex flex-col items-center justify-start mt-1">
          {player.cards.length > 0 && !player.folded && (
            <>
              <div className="flex gap-1">
                {player.cards.map((card, i) => (
                  <div key={i} className="w-[40px] h-[56px]">
                    <PlayingCard card={card} />
                  </div>
                ))}
              </div>
              {/* 족보 표시 (고정 높이: 18px) */}
              <div className="h-[18px] flex items-center justify-center mt-1">
                {handResult && (
                  <div className="px-2 py-0.5 bg-black/60 backdrop-blur-sm rounded text-center">
                    <span className="text-xs font-bold text-yellow-400">
                      {handResult.description}
                    </span>
                    {draws && draws.length > 0 && (
                      <span className="text-xs text-cyan-400 ml-1">
                        + {draws[0]}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* WIN 배지 - 절대 위치 (레이아웃에 영향 없음) */}
      {player.isWinner && (
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 px-4 py-2 bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-sm font-bold rounded-lg shadow-lg animate-bounce z-10">
          <div className="text-center">WIN!</div>
          {player.winAmount !== undefined && player.winAmount > 0 && (
            <div className="text-xs text-yellow-900">+{player.winAmount.toLocaleString()}</div>
          )}
        </div>
      )}

      {/* ========================================
          베팅/폴드 표시 영역 (고정 높이: 20px)
          - 베팅 또는 폴드 상태 표시
          - 둘 다 없어도 공간 유지
          ======================================== */}
      <div className="h-[20px] flex items-center justify-center mt-1">
        {player.folded ? (
          <span className="px-2 py-0.5 bg-red-500/30 text-red-400 text-xs font-bold rounded">
            FOLD
          </span>
        ) : player.bet > 0 ? (
          <span className="text-xs text-[var(--accent)]">
            Bet: {player.bet.toLocaleString()}
          </span>
        ) : null}
      </div>
    </div>
  );
}

// Seat positions for 9-max table - vertical layout
// Top: 2, Sides: 2-2-2, Bottom: 1 (player)
const SEAT_POSITIONS = [
  { top: '72%', left: '50%' },   // 0 - bottom center (ME/Player)
  { top: '62%', left: '12%' },   // 1 - lower left
  { top: '62%', left: '88%' },   // 2 - lower right
  { top: '48%', left: '5%' },    // 3 - mid left
  { top: '48%', left: '95%' },   // 4 - mid right
  { top: '34%', left: '12%' },   // 5 - upper left
  { top: '34%', left: '88%' },   // 6 - upper right
  { top: '22%', left: '35%' },   // 7 - top left
  { top: '22%', left: '65%' },   // 8 - top right
];

// 바이인 모달 컴포넌트
function BuyInModal({
  config,
  userBalance,
  onConfirm,
  onCancel,
  isLoading,
}: {
  config: TableConfig;
  userBalance: number;
  onConfirm: (buyIn: number) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const minBuyIn = config.minBuyIn || 400;
  const maxBuyIn = Math.min(config.maxBuyIn || 2000, userBalance);
  const [buyIn, setBuyIn] = useState(Math.min(minBuyIn, maxBuyIn));

  const isValidBuyIn = buyIn >= minBuyIn && buyIn <= maxBuyIn;
  const insufficientBalance = userBalance < minBuyIn;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 animate-fade-in">
      <div className="card w-full max-w-sm animate-scale-in">
        <div className="mb-4">
          <h3 className="text-lg font-bold">게임 참여</h3>
          <p className="text-xs text-[var(--text-secondary)]">
            블라인드: {config.smallBlind}/{config.bigBlind}
          </p>
        </div>

        {insufficientBalance ? (
          <div className="mb-4 p-3 rounded-lg bg-[var(--error-bg)] text-[var(--error)] text-sm">
            잔액이 부족합니다. 최소 바이인: {minBuyIn.toLocaleString()}
          </div>
        ) : (
          <>
            <div className="mb-4">
              <label className="block text-xs font-medium mb-2 text-[var(--text-secondary)]">
                바이인 금액
              </label>
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="range"
                  min={minBuyIn}
                  max={maxBuyIn}
                  value={buyIn}
                  onChange={(e) => setBuyIn(parseInt(e.target.value))}
                  className="flex-1"
                />
              </div>
              <input
                type="number"
                value={buyIn}
                onChange={(e) => setBuyIn(parseInt(e.target.value) || minBuyIn)}
                className="input text-center"
                min={minBuyIn}
                max={maxBuyIn}
              />
            </div>

            <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-4">
              <span>최소: {minBuyIn.toLocaleString()}</span>
              <span>내 잔액: {userBalance.toLocaleString()}</span>
              <span>최대: {maxBuyIn.toLocaleString()}</span>
            </div>
          </>
        )}

        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="btn btn-secondary flex-1"
          >
            취소
          </button>
          <button
            onClick={() => onConfirm(buyIn)}
            disabled={isLoading || !isValidBuyIn || insufficientBalance}
            className="btn btn-primary flex-1"
          >
            {isLoading ? '참여 중...' : `${buyIn.toLocaleString()} 참여`}
          </button>
        </div>
      </div>
    </div>
  );
}

// 개발용 어드민 패널 컴포넌트
function DevAdminPanel({
  tableId,
  onReset,
  onAddBot,
  isResetting,
  isAddingBot,
}: {
  tableId: string;
  onReset: () => void;
  onAddBot: () => void;
  isResetting: boolean;
  isAddingBot: boolean;
}) {
  const [isOpen, setIsOpen] = useState(true); // 기본 펼침

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* 패널 (기본 펼침) */}
      {isOpen ? (
        <div className="w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>🛠</span> DEV 패널
            </h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2">
            {/* 봇 추가 */}
            <button
              onClick={onAddBot}
              disabled={isAddingBot}
              className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:opacity-50 text-white text-sm rounded transition-colors flex items-center justify-center gap-2"
            >
              {isAddingBot ? (
                <>
                  <span className="animate-spin">⏳</span> 추가 중...
                </>
              ) : (
                <>
                  <span>🤖</span> 봇 추가
                </>
              )}
            </button>

            {/* 전체 리셋 (봇 제거 + 테이블 리셋 통합) */}
            <button
              onClick={onReset}
              disabled={isResetting}
              className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-900 disabled:opacity-50 text-white text-sm rounded transition-colors flex items-center justify-center gap-2"
            >
              {isResetting ? (
                <>
                  <span className="animate-spin">⏳</span> 리셋 중...
                </>
              ) : (
                <>
                  <span>🔄</span> 전체 리셋
                </>
              )}
            </button>

            {/* 테이블 ID 표시 */}
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-500">Table ID:</p>
              <p className="text-xs text-gray-400 font-mono truncate">{tableId}</p>
            </div>
          </div>
        </div>
      ) : (
        /* 토글 버튼 (접힘 상태) */
        <button
          onClick={() => setIsOpen(true)}
          className="w-12 h-12 rounded-full bg-gray-800 border border-gray-600 text-white flex items-center justify-center shadow-lg hover:bg-gray-700 transition-colors"
          title="개발자 도구"
        >
          ⚙
        </button>
      )}
    </div>
  );
}

export default function TablePage() {
  const params = useParams();
  const router = useRouter();
  const tableId = params.id as string;

  const { user, fetchUser } = useAuthStore();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [tableConfig, setTableConfig] = useState<TableConfig | null>(null);
  const [seats, setSeats] = useState<SeatInfo[]>([]);
  const [myPosition, setMyPosition] = useState<number | null>(null);
  const [raiseAmount, setRaiseAmount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [showBuyInModal, setShowBuyInModal] = useState(false);
  const [isAddingBot, setIsAddingBot] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [myHoleCards, setMyHoleCards] = useState<Card[]>([]);
  const [currentTurnPosition, setCurrentTurnPosition] = useState<number | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  // 각 플레이어의 마지막 액션 저장 { position: { type: 'call', amount: 100 } }
  const [playerActions, setPlayerActions] = useState<Record<number, { type: string; amount?: number; timestamp: number }>>({});
  // 턴 시작 시간 추적
  const [turnStartTime, setTurnStartTime] = useState<number | null>(null);
  // 자동 폴드 방지 (중복 호출 방지)
  const [hasAutoFolded, setHasAutoFolded] = useState(false);
  // 서버에서 받은 허용된 액션 목록
  const [allowedActions, setAllowedActions] = useState<AllowedAction[]>([]);
  // 대기 중인 턴 위치 (액션 효과 후 적용)
  const [pendingTurnPosition, setPendingTurnPosition] = useState<number | null>(null);
  // 액션 효과 표시 중 여부
  const [isShowingActionEffect, setIsShowingActionEffect] = useState(false);
  // DEV 패널 상태
  const [isResetting, setIsResetting] = useState(false);
  // 쇼다운 상태 (핸드 결과)
  const [winnerPositions, setWinnerPositions] = useState<number[]>([]);
  const [winnerAmounts, setWinnerAmounts] = useState<Record<number, number>>({}); // position -> 승리 금액
  const [showdownCards, setShowdownCards] = useState<Record<number, Card[]>>({}); // position -> cards
  // 쇼다운 표시 상태 (TABLE_SNAPSHOT의 phase 덮어쓰기와 별개로 관리)
  const [isShowdownDisplay, setIsShowdownDisplay] = useState(false);

  // 관전자 여부: myPosition이 null이면 관전자
  const isSpectator = myPosition === null;
  const isMyTurn = currentTurnPosition !== null && currentTurnPosition === myPosition;

  // Connect to WebSocket
  useEffect(() => {
    fetchUser();

    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    wsClient
      .connect(token)
      .then(() => {
        setIsConnected(true);
        // Subscribe to table (백엔드는 tableId를 기대)
        wsClient.send('SUBSCRIBE_TABLE', { tableId: tableId });
      })
      .catch((err) => {
        setError('서버 연결에 실패했습니다.');
        console.error(err);
      });

    // Event handlers
    const unsubTableSnapshot = wsClient.on('TABLE_SNAPSHOT', (data) => {
      console.log('TABLE_SNAPSHOT received:', data);
      // 백엔드 TABLE_SNAPSHOT 구조 처리
      if (data.config) {
        setTableConfig(data.config);
      }
      if (data.seats) {
        setSeats(data.seats);
      }
      // state.players에서 좌석 업데이트 (personalized state 형식)
      if (data.state?.players) {
        const playersArray = Array.isArray(data.state.players)
          ? data.state.players
          : Object.values(data.state.players);
        const formattedSeats = playersArray
          .filter((p: any) => p !== null)
          .map((p: any) => ({
            position: p.seat ?? p.position,
            player: {
              userId: p.userId,
              nickname: p.username || p.nickname,
            },
            stack: p.stack,
            status: p.status,
            betAmount: p.bet || 0,
          }));
        if (formattedSeats.length > 0) {
          setSeats(formattedSeats);
        }
      }
      // myPosition 설정: null은 관전자, 숫자는 착석 위치
      // data.myPosition이 명시적으로 제공되면 그 값 사용 (null 포함)
      if ('myPosition' in data) {
        setMyPosition(data.myPosition);  // null이면 관전자
      } else if (data.state && 'myPosition' in data.state) {
        setMyPosition(data.state.myPosition);
      }
      // myHoleCards 추출 (직접 필드 또는 state 내부에서)
      if (data.myHoleCards && data.myHoleCards.length > 0) {
        // 카드 형식 변환 ("As" -> { rank: "A", suit: "s" })
        const cards = data.myHoleCards.map((card: string | Card) => {
          if (typeof card === 'string') {
            return { rank: card.slice(0, -1), suit: card.slice(-1) };
          }
          return card;
        });
        setMyHoleCards(cards);
      } else if (data.state?.players && data.state?.myPosition !== undefined) {
        // action.py의 _broadcast_personalized_states에서 오는 형식
        const myPlayer = data.state.players[data.state.myPosition];
        if (myPlayer?.holeCards && myPlayer.holeCards.length > 0) {
          const cards = myPlayer.holeCards.map((card: string | Card) => {
            if (typeof card === 'string') {
              return { rank: card.slice(0, -1), suit: card.slice(-1) };
            }
            return card;
          });
          setMyHoleCards(cards);
        }
      }
      // hand 정보 또는 state 정보에서 phase, pot 등 업데이트
      const stateData = data.hand || data.state || data;
      if (stateData.pot !== undefined || stateData.phase) {
        setGameState((prev) => ({
          ...(prev || {
            tableId: data.tableId,
            players: [],
            communityCards: [],
            pot: 0,
            currentPlayer: null,
            phase: 'waiting' as const,
            smallBlind: data.config?.smallBlind || stateData.smallBlind || 10,
            bigBlind: data.config?.bigBlind || stateData.bigBlind || 20,
            minRaise: 0,
            currentBet: 0,
          }),
          phase: stateData.phase || 'waiting',
          pot: stateData.pot ?? prev?.pot ?? 0,
          communityCards: parseCards(stateData.communityCards),
          currentBet: stateData.currentBet ?? prev?.currentBet ?? 0,
        }));
        if (stateData.currentTurn !== undefined) {
          setCurrentTurnPosition(stateData.currentTurn);
        }
      }
    });

    const unsubTableUpdate = wsClient.on('TABLE_STATE_UPDATE', (data) => {
      const changes = data.changes || {};
      const updateType = data.updateType;

      console.log('TABLE_STATE_UPDATE received:', { updateType, changes });

      // seat_taken 처리: 새 플레이어가 착석했을 때
      if (updateType === 'seat_taken' && changes.position !== undefined) {
        setSeats((prevSeats) => {
          // 이미 해당 위치에 플레이어가 있는지 확인
          const existingIdx = prevSeats.findIndex(s => s.position === changes.position);
          const newSeat: SeatInfo = {
            position: changes.position,
            player: {
              userId: changes.userId,
              nickname: changes.nickname || changes.userId,
            },
            stack: changes.stack || 0,
            status: 'active',
            betAmount: 0,
          };

          if (existingIdx >= 0) {
            // 기존 좌석 업데이트
            const updated = [...prevSeats];
            updated[existingIdx] = newSeat;
            return updated;
          } else {
            // 새 좌석 추가
            return [...prevSeats, newSeat];
          }
        });

        // 현재 유저가 착석한 경우 myPosition 업데이트
        if (changes.userId === user?.id) {
          setMyPosition(changes.position);
        }
      }

      // player_left 처리: 플레이어가 떠났을 때
      if (updateType === 'player_left' && changes.position !== undefined) {
        setSeats((prevSeats) => prevSeats.filter(s => s.position !== changes.position));
        if (changes.userId === user?.id) {
          setMyPosition(null);
        }
      }

      // bot_added 처리: 봇이 추가됐을 때
      if (updateType === 'bot_added' && changes.position !== undefined) {
        setSeats((prevSeats) => {
          const existingIdx = prevSeats.findIndex(s => s.position === changes.position);
          const newSeat: SeatInfo = {
            position: changes.position,
            player: {
              userId: changes.botId,
              nickname: changes.nickname || `Bot_${changes.botId?.slice(-4)}`,
            },
            stack: changes.stack || 0,
            status: 'active',
            betAmount: 0,
          };

          if (existingIdx >= 0) {
            const updated = [...prevSeats];
            updated[existingIdx] = newSeat;
            return updated;
          } else {
            return [...prevSeats, newSeat];
          }
        });
      }

      // gameState 업데이트 (pot, phase, currentBet 등)
      setGameState((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          pot: changes.pot ?? prev.pot,
          phase: changes.phase ?? prev.phase,
          currentBet: changes.currentBet ?? prev.currentBet,
          currentPlayer: changes.currentPlayer ?? prev.currentPlayer,
        };
      });

      // 플레이어 스택/베팅 실시간 업데이트
      if (changes.players && Array.isArray(changes.players)) {
        setSeats((prevSeats) => {
          return prevSeats.map((seat) => {
            const playerUpdate = changes.players.find(
              (p: { position: number }) => p.position === seat.position
            );
            if (playerUpdate && seat.player) {
              return {
                ...seat,
                stack: playerUpdate.stack ?? seat.stack,
                betAmount: playerUpdate.bet ?? seat.betAmount,
                status: playerUpdate.status ?? seat.status,
              };
            }
            return seat;
          });
        });
      }

      // seats 업데이트가 있으면 반영
      if (changes.seats) {
        setSeats(changes.seats);
      }

      // lastAction이 있으면 플레이어 액션 표시 (시퀀싱 처리)
      if (changes.lastAction) {
        const { type, amount, position } = changes.lastAction;

        // 1. 액션 효과 표시 시작
        setIsShowingActionEffect(true);
        setPlayerActions((prev) => ({
          ...prev,
          [position]: { type, amount, timestamp: Date.now() },
        }));

        // 2. currentPlayer가 있으면 대기열에 저장 (즉시 적용 안 함)
        // 중요: 턴 변경 시 타이머는 TURN_PROMPT에서 설정됨
        if (changes.currentPlayer !== undefined) {
          setPendingTurnPosition(changes.currentPlayer);
          // 턴이 변경되므로 이전 타이머 즉시 무효화
          setTurnStartTime(null);
        }

        // 3. 액션 효과 표시 후 턴 전환 (1초 후)
        setTimeout(() => {
          setIsShowingActionEffect(false);
          // 대기 중인 턴 위치가 있으면 적용
          // 주의: 타이머는 여기서 설정하지 않음 (TURN_PROMPT에서 설정)
          setPendingTurnPosition((pending) => {
            if (pending !== null) {
              setCurrentTurnPosition(pending);
            }
            return null;
          });
        }, 1000);
      } else {
        // lastAction 없이 currentPlayer만 변경되면 즉시 적용
        if (changes.currentPlayer !== undefined) {
          // 턴 변경 시 타이머 리셋 (TURN_PROMPT에서 새로 설정됨)
          setTurnStartTime(null);
          setCurrentTurnPosition(changes.currentPlayer);
        }
      }
    });

    // ACTION_RESULT 핸들러 - 액션 결과 처리
    // 주의: playerActions 업데이트는 TABLE_STATE_UPDATE에서만 처리 (중복 방지)
    const unsubActionResult = wsClient.on('ACTION_RESULT', (data) => {
      console.log('ACTION_RESULT received:', data);
      if (data.success && data.action) {
        // 타이머 즉시 정지 - 액션이 완료되면 카운트다운 종료
        setTurnStartTime(null);
        // 내 액션이 성공하면 allowedActions 초기화 (버튼 숨김)
        setAllowedActions([]);
        // 주의: playerActions 업데이트는 TABLE_STATE_UPDATE에서 처리
        // 여기서 하지 않음으로써 중복 효과 방지
      } else if (!data.success) {
        setError(data.errorMessage || '액션 처리에 실패했습니다.');
        // should_refresh 플래그가 있으면 게임 상태 갱신
        if (data.shouldRefresh) {
          console.log('Refreshing game state due to action error...');
          wsClient.send('SUBSCRIBE_TABLE', { tableId: tableId });
        }
      }
    });

    // SEAT_RESULT 핸들러 - 바이인 후 좌석 배정 결과
    const unsubSeatResult = wsClient.on('SEAT_RESULT', (data) => {
      setIsJoining(false);
      if (data.success) {
        setMyPosition(data.position);
        setShowBuyInModal(false);
        // 테이블 상태 새로고침
        wsClient.send('SUBSCRIBE_TABLE', { tableId: tableId });
      } else {
        setError(data.errorMessage || '좌석 배정에 실패했습니다.');
      }
    });

    const unsubError = wsClient.on('ERROR', (data) => {
      // 백엔드 ERROR 형식: { errorCode, errorMessage, details }
      setError(data.errorMessage || data.message || '오류가 발생했습니다.');
      setIsLeaving(false); // Reset leaving state on error
    });

    const unsubLeaveResult = wsClient.on('LEAVE_RESULT', (data) => {
      if (data.success) {
        router.push('/lobby');
      } else if (data.errorCode === 'TABLE_NOT_SEATED') {
        // 관전자(앉지 않은 사용자)도 로비로 이동 가능
        router.push('/lobby');
      } else {
        setError(data.errorMessage || '테이블 퇴장에 실패했습니다.');
        setIsLeaving(false);
      }
    });

    // ADD_BOT_RESULT 핸들러 - 봇 추가 결과
    const unsubAddBotResult = wsClient.on('ADD_BOT_RESULT', (data) => {
      setIsAddingBot(false);
      if (data.success) {
        // 테이블 상태 새로고침
        wsClient.send('SUBSCRIBE_TABLE', { tableId: tableId });
      } else {
        setError(data.errorMessage || '봇 추가에 실패했습니다.');
      }
    });

    // GAME_STARTING 핸들러 - 게임 시작 카운트다운
    const unsubGameStarting = wsClient.on('GAME_STARTING', (data) => {
      console.log('GAME_STARTING received:', data);
      const countdownSeconds = data.countdownSeconds || 5;
      setCountdown(countdownSeconds);

      // 카운트다운 타이머
      let remaining = countdownSeconds;
      const timer = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
          clearInterval(timer);
          setCountdown(null);
        } else {
          setCountdown(remaining);
        }
      }, 1000);
    });

    // HAND_STARTED 핸들러 - 새 핸드 시작 (백엔드에서 HAND_STARTED 이벤트 전송)
    const unsubHandStart = wsClient.on('HAND_STARTED', (data) => {
      console.log('HAND_STARTED received:', data);

      // 카운트다운 종료
      setCountdown(null);

      // 이전 핸드 액션 초기화
      setPlayerActions({});
      setAllowedActions([]); // 허용된 액션도 초기화

      // 시퀀싱 상태 초기화
      setPendingTurnPosition(null);
      setIsShowingActionEffect(false);

      // 타이머 초기화 (새 핸드 시작)
      setTurnStartTime(null);
      setCurrentTurnPosition(null);

      // 쇼다운 상태 완전 초기화
      setWinnerPositions([]);
      setWinnerAmounts({});
      setShowdownCards({});
      setIsShowdownDisplay(false);

      // 이전 핸드 카드 초기화 (새 카드가 오기 전까지 빈 상태)
      setMyHoleCards([]);

      // 게임 상태 업데이트
      setGameState((prev) => {
        const base = prev || {
          tableId: data.tableId,
          players: [],
          communityCards: [],
          pot: 0,
          currentPlayer: null,
          phase: 'waiting' as const,
          smallBlind: 10,
          bigBlind: 20,
          minRaise: 0,
          currentBet: 0,
        };
        return {
          ...base,
          tableId: data.tableId,
          phase: data.phase || 'preflop',
          pot: data.pot || 0,
          communityCards: parseCards(data.communityCards),
        };
      });

      // 내 위치 업데이트
      if (data.myPosition !== null && data.myPosition !== undefined) {
        setMyPosition(data.myPosition);
      }

      // 내 홀카드 저장
      if (data.myHoleCards && data.myHoleCards.length > 0) {
        setMyHoleCards(data.myHoleCards);
      }

      // 현재 턴 위치 저장
      if (data.currentTurn !== null && data.currentTurn !== undefined) {
        setCurrentTurnPosition(data.currentTurn);
      }

      // seats 업데이트
      if (data.seats) {
        const formattedSeats = data.seats.map((s: any) => ({
          position: s.position,
          player: {
            userId: s.userId,
            nickname: s.nickname,
          },
          stack: s.stack,
          status: s.status,
          betAmount: s.betAmount || 0,
        }));
        setSeats(formattedSeats);
      }
    });

    // TURN_PROMPT 핸들러 - 차례 알림
    // 서버에서 제공하는 turnStartTime을 사용하여 모든 클라이언트가 동일한 타이머를 표시
    const unsubTurnPrompt = wsClient.on('TURN_PROMPT', (data) => {
      console.log('TURN_PROMPT received:', data);

      // currentBet 업데이트 (항상 즉시)
      if (data.currentBet !== undefined) {
        setGameState((prev) => {
          if (!prev) return prev;
          return { ...prev, currentBet: data.currentBet };
        });
      }

      // minRaise 업데이트
      const raiseAction = data.allowedActions?.find((a: any) => a.type === 'raise' || a.type === 'bet');
      if (raiseAction?.minAmount) {
        setGameState((prev) => {
          if (!prev) return prev;
          return { ...prev, minRaise: raiseAction.minAmount };
        });
        setRaiseAmount(raiseAction.minAmount);
      }

      // 턴 위치 및 액션 업데이트 함수
      // 중요: TURN_PROMPT를 받으면 항상 타이머를 새로 시작
      const applyTurnPrompt = () => {
        // 턴 위치 설정
        setCurrentTurnPosition(data.position);
        // 타이머 새로 시작 (클라이언트 시간 사용)
        setTurnStartTime(Date.now());
        // 자동 폴드 플래그 리셋
        setHasAutoFolded(false);
        // 허용된 액션 설정
        if (data.allowedActions) {
          setAllowedActions(data.allowedActions);
        }
      };

      // 액션 효과 표시 중이면 대기
      setIsShowingActionEffect((showing) => {
        if (showing) {
          // 액션 효과 표시 중 - 대기열에 저장하고 나중에 적용
          setPendingTurnPosition(data.position);
          setTimeout(() => {
            applyTurnPrompt();
          }, 800); // 액션 효과 끝난 후 적용
        } else {
          // 액션 효과 없음 - 즉시 적용
          applyTurnPrompt();
        }
        return showing;
      });
    });

    // TURN_CHANGED 핸들러 - 봇 플레이 중 턴 변경
    // 액션 효과가 표시 중이면 대기열에 저장
    const unsubTurnChanged = wsClient.on('TURN_CHANGED', (data) => {
      console.log('TURN_CHANGED received:', data);

      // currentBet 업데이트 (항상 즉시)
      if (data.currentBet !== undefined) {
        setGameState((prev) => {
          if (!prev) return prev;
          return { ...prev, currentBet: data.currentBet };
        });
      }

      // 턴이 변경되면 타이머 초기화 (다음 TURN_PROMPT에서 새로 시작)
      setTurnStartTime(null);

      // 턴 위치 업데이트 (액션 효과 표시 중이면 대기열에 저장)
      if (data.currentPlayer !== undefined && data.currentPlayer !== null) {
        setIsShowingActionEffect((showing) => {
          if (showing) {
            // 액션 효과 표시 중 - 대기열에 저장
            setPendingTurnPosition(data.currentPlayer);
          } else {
            // 액션 효과 없음 - 즉시 적용
            setCurrentTurnPosition(data.currentPlayer);
          }
          return showing;
        });
      }
    });

    // COMMUNITY_CARDS 핸들러 - 커뮤니티 카드 업데이트 (플롭/턴/리버)
    const unsubCommunityCards = wsClient.on('COMMUNITY_CARDS', (data) => {
      console.log('COMMUNITY_CARDS received:', data);
      if (data.cards) {
        setGameState((prev) => {
          if (!prev) return prev;
          return { ...prev, communityCards: parseCards(data.cards), phase: data.phase || prev.phase };
        });
      }
    });

    // HAND_RESULT 핸들러 - 핸드 종료 및 쇼다운
    const unsubHandResult = wsClient.on('HAND_RESULT', (data) => {
      console.log('HAND_RESULT received:', data);

      // 타이머 및 턴 완전 초기화 (핸드 종료)
      setTurnStartTime(null);
      setCurrentTurnPosition(null);
      setAllowedActions([]);

      // 시퀀싱 상태 초기화
      setPendingTurnPosition(null);
      setIsShowingActionEffect(false);

      // 페이즈를 showdown으로 변경
      setGameState((prev) => {
        if (!prev) return prev;
        return { ...prev, phase: 'showdown' };
      });

      // 쇼다운 표시 활성화 (TABLE_SNAPSHOT 덮어쓰기와 별개로 유지)
      setIsShowdownDisplay(true);

      // 승자 위치 및 금액 저장
      if (data.winners && data.winners.length > 0) {
        const winnerSeats = data.winners.map((w: { seat: number }) => w.seat);
        setWinnerPositions(winnerSeats);

        // 승리 금액 저장
        const amounts: Record<number, number> = {};
        data.winners.forEach((w: { seat: number; amount: number }) => {
          amounts[w.seat] = w.amount;
        });
        setWinnerAmounts(amounts);
        console.log('Winners set:', winnerSeats, 'Amounts:', amounts);
      }

      // 쇼다운 카드 저장 (상대방 카드 공개)
      if (data.showdown && data.showdown.length > 0) {
        const cardsMap: Record<number, Card[]> = {};
        data.showdown.forEach((sd: { seat: number; position: number; holeCards: string[] }) => {
          const pos = sd.seat ?? sd.position;
          if (sd.holeCards && sd.holeCards.length > 0) {
            cardsMap[pos] = sd.holeCards.map((card: string) => ({
              rank: card.slice(0, -1),
              suit: card.slice(-1),
            }));
          }
        });
        setShowdownCards(cardsMap);
      }
    });

    // Handle reconnection - update connected state
    const unsubConnectionState = wsClient.on('CONNECTION_STATE', (data) => {
      if (data.state === 'connected') {
        setIsConnected(true);
        // Re-subscribe to table after reconnection
        wsClient.send('SUBSCRIBE_TABLE', { tableId: tableId });
      } else {
        setIsConnected(false);
      }
    });

    // Handle send failures - notify user when actions fail to send
    const unsubSendFailed = wsClient.on('SEND_FAILED', (data) => {
      if (data.event !== 'PING') { // Ignore PING failures
        setError(`액션 전송 실패: 서버에 연결되지 않았습니다.`);
      }
    });

    // Handle connection lost
    const unsubConnectionLost = wsClient.on('CONNECTION_LOST', () => {
      setIsConnected(false);
      setError('서버와의 연결이 끊어졌습니다. 페이지를 새로고침해주세요.');
    });

    return () => {
      unsubTableSnapshot();
      unsubTableUpdate();
      unsubActionResult();
      unsubSeatResult();
      unsubError();
      unsubLeaveResult();
      unsubAddBotResult();
      unsubGameStarting();
      unsubHandStart();
      unsubTurnPrompt();
      unsubTurnChanged();
      unsubCommunityCards();
      unsubHandResult();
      unsubConnectionState();
      unsubSendFailed();
      unsubConnectionLost();
      wsClient.send('UNSUBSCRIBE_TABLE', { tableId: tableId });
    };
  }, [tableId, router, fetchUser, user?.id]);

  // Action handlers - 백엔드는 tableId, actionType을 기대
  const handleFold = useCallback(() => {
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'fold',
    });
  }, [tableId]);

  const handleCheck = useCallback(() => {
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'check',
    });
  }, [tableId]);

  const handleCall = useCallback(() => {
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'call',
    });
  }, [tableId]);

  const handleRaise = useCallback(() => {
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'raise',
      amount: raiseAmount,
    });
  }, [tableId, raiseAmount]);

  const handleAllIn = useCallback(() => {
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'all_in',
    });
  }, [tableId]);

  // 자동 폴드 핸들러 (타이머 만료 시)
  const handleAutoFold = useCallback(() => {
    if (hasAutoFolded) return; // 중복 호출 방지
    setHasAutoFolded(true);
    console.log('Auto-fold triggered');
    wsClient.send('ACTION_REQUEST', {
      tableId: tableId,
      actionType: 'fold',
    });
  }, [tableId, hasAutoFolded]);

  const handleLeave = useCallback(() => {
    if (isLeaving) return;
    setIsLeaving(true);
    setError(null);
    wsClient.send('LEAVE_REQUEST', { tableId: tableId });
    // Navigation will happen in LEAVE_RESULT handler
  }, [tableId, isLeaving]);

  // 참여하기 버튼 클릭 - 바이인 모달 표시
  const handleJoinClick = useCallback(() => {
    setError(null);
    setShowBuyInModal(true);
  }, []);

  // 바이인 확인 - SEAT_REQUEST 전송
  const handleBuyInConfirm = useCallback((buyIn: number) => {
    setIsJoining(true);
    wsClient.send('SEAT_REQUEST', {
      tableId: tableId,
      buyInAmount: buyIn,
    });
  }, [tableId]);

  // 바이인 취소
  const handleBuyInCancel = useCallback(() => {
    setShowBuyInModal(false);
  }, []);

  // 게임 시작 핸들러
  const handleStartGame = useCallback(() => {
    wsClient.send('START_GAME', { tableId: tableId });
  }, [tableId]);

  // 봇 추가 핸들러
  const handleAddBot = useCallback(() => {
    if (isAddingBot) return;
    setIsAddingBot(true);
    setError(null);
    wsClient.send('ADD_BOT_REQUEST', {
      tableId: tableId,
      buyIn: tableConfig?.minBuyIn || 1000,
    });
  }, [tableId, tableConfig, isAddingBot]);

  // [DEV] 전체 리셋 핸들러 (봇 제거 + 테이블 리셋 통합)
  const handleDevReset = useCallback(async () => {
    if (isResetting) return;
    setIsResetting(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // 1. 먼저 봇 제거
      await fetch(`${baseUrl}/api/v1/rooms/${tableId}/dev/remove-bots`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      // 2. 테이블 리셋
      const res = await fetch(`${baseUrl}/api/v1/rooms/${tableId}/dev/reset`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success) {
        // 상태 초기화
        setSeats([]);
        setMyPosition(null);
        setMyHoleCards([]);
        setCurrentTurnPosition(null);
        setPlayerActions({});
        setAllowedActions([]);
        setGameState(null);
        // 테이블 다시 구독
        wsClient.send('SUBSCRIBE_TABLE', { tableId });
      } else {
        setError(data.message || '리셋 실패');
      }
    } catch (err) {
      setError('리셋 중 오류 발생');
    } finally {
      setIsResetting(false);
    }
  }, [tableId, isResetting]);

  // 내 좌석 정보 가져오기
  const mySeat = seats.find((s) => s.player?.userId === user?.id);
  const myStack = mySeat?.stack || 0;

  // 실시간 족보 계산 (내 홀카드 + 커뮤니티 카드)
  const myHandAnalysis = useMemo(() => {
    if (myHoleCards.length === 0) return { hand: null, draws: [] };
    const communityCards = gameState?.communityCards || [];
    return analyzeHand(myHoleCards, communityCards);
  }, [myHoleCards, gameState?.communityCards]);

  // 서버에서 받은 allowedActions 기반으로 액션 정보 추출
  const canFold = allowedActions.some(a => a.type === 'fold');
  const canCheck = allowedActions.some(a => a.type === 'check');
  const canCall = allowedActions.some(a => a.type === 'call');
  const canBet = allowedActions.some(a => a.type === 'bet');
  const canRaise = allowedActions.some(a => a.type === 'raise');

  // 콜 금액은 서버에서 받은 값 사용
  const callAction = allowedActions.find(a => a.type === 'call');
  const callAmount = callAction?.minAmount || callAction?.amount || 0;

  // 레이즈/베팅 최소/최대값
  const raiseOrBetAction = allowedActions.find(a => a.type === 'raise' || a.type === 'bet');
  const minRaiseAmount = raiseOrBetAction?.minAmount || gameState?.minRaise || 0;
  const maxRaiseAmount = raiseOrBetAction?.maxAmount || myStack;

  // 좌석 데이터를 Player 형식으로 변환 (상대적 위치 적용)
  const getRelativePosition = (playerSeatIndex: number) => {
    if (myPosition === null) return playerSeatIndex; // 관전자는 그대로
    const totalSeats = tableConfig?.maxSeats || 9;
    return (playerSeatIndex - myPosition + totalSeats) % totalSeats;
  };

  return (
    <div className="min-h-screen flex justify-center bg-[#1a1a2e]">
      {/* Mobile container - max width 500px for mobile-first design */}
      <div
        className="w-full max-w-[500px] min-h-screen flex flex-col bg-cover bg-center bg-no-repeat relative"
        style={{ backgroundImage: "url('/assets/images/backgrounds/background_game.webp')" }}
      >
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <button
            onClick={handleLeave}
            disabled={isLeaving}
            className="btn btn-secondary btn-sm"
          >
            {isLeaving ? '퇴장 중...' : '← 로비로 돌아가기'}
          </button>

          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-xs text-[var(--text-muted)]">블라인드</div>
              <div className="text-sm font-bold">
                {gameState?.smallBlind || 0} / {gameState?.bigBlind || 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-[var(--text-muted)]">팟</div>
              <div className="text-sm font-bold text-[var(--accent)]">
                {gameState?.pot?.toLocaleString() || 0}
              </div>
            </div>
            <div
              className={`badge ${
                isConnected ? 'badge-success' : 'badge-error'
              }`}
            >
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-[var(--error-bg)] text-[var(--error)] p-3 text-center text-sm">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 underline"
          >
            닫기
          </button>
        </div>
      )}

      {/* Game Table */}
      <main className="flex-1 relative">
          {/* Community Cards - centered on table felt */}
          <div className="absolute top-[48%] left-1/2 -translate-x-1/2 -translate-y-1/2 flex gap-1">
            {gameState?.communityCards?.map((card, i) => (
              <div key={i} className="w-[40px] h-[56px]">
                <PlayingCard card={card} />
              </div>
            ))}
            {/* Placeholder cards */}
            {Array.from({
              length: 5 - (gameState?.communityCards?.length || 0),
            }).map((_, i) => (
              <div
                key={`placeholder-${i}`}
                className="w-[40px] h-[56px] rounded-md border-2 border-dashed border-white/20"
              />
            ))}
          </div>

          {/* Pot Display */}
          <div className="absolute top-[38%] left-1/2 -translate-x-1/2 text-center">
            <div className="text-white/70 text-xs drop-shadow-lg">POT</div>
            <div className="text-white font-bold text-xl drop-shadow-lg">
              {gameState?.pot?.toLocaleString() || 0}
            </div>
          </div>

          {/* Phase Indicator */}
          <div className="absolute top-[58%] left-1/2 -translate-x-1/2">
            <span className="badge badge-info uppercase">
              {gameState?.phase || 'waiting'}
            </span>
          </div>

          {/* Countdown Overlay */}
          {countdown !== null && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
              <div className="text-center animate-pulse">
                <div className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
                  {countdown}
                </div>
                <div className="text-xl text-white/80 drop-shadow-lg">
                  게임이 곧 시작됩니다!
                </div>
              </div>
            </div>
          )}

          {/* Player Seats - 상대적 위치 적용 */}
          {SEAT_POSITIONS.map((pos, visualIndex) => {
            // seats 배열에서 해당 시각적 위치에 맞는 플레이어 찾기
            const seat = seats.find((s) => getRelativePosition(s.position) === visualIndex);

            // 현재 유저인지 확인
            const isCurrentUser = seat?.player?.userId === user?.id;

            // 게임이 진행 중인지 확인 (waiting이 아니면 카드를 받은 상태)
            const gameInProgress = gameState?.phase && gameState.phase !== 'waiting';

            // 쇼다운 시 상대방 카드 (공개된 카드) - showdown phase일 때만 표시
            // isShowdownDisplay 사용 (TABLE_SNAPSHOT 덮어쓰기와 별개로 유지)
            const showdownPlayerCards = (seat && isShowdownDisplay) ? showdownCards[seat.position] : undefined;

            // 카드 결정: 내 카드 / 쇼다운 시 공개된 카드 / 빈 배열
            const playerCards = isCurrentUser
              ? myHoleCards
              : (showdownPlayerCards || []);

            // seat 데이터를 Player 형식으로 변환
            const player = seat?.player ? {
              id: seat.player.userId,
              username: seat.player.nickname,
              chips: seat.stack,
              cards: playerCards,
              bet: seat.betAmount,
              folded: seat.status === 'folded',
              isActive: seat.status === 'active',
              seatIndex: seat.position,
              // 게임 진행 중이고 폴드하지 않았으면 카드를 가진 것
              hasCards: !!(gameInProgress && seat.status !== 'folded' && seat.status !== 'waiting'),
              // 승자 여부 - isShowdownDisplay 사용 (TABLE_SNAPSHOT 덮어쓰기와 별개)
              isWinner: isShowdownDisplay && winnerPositions.includes(seat.position),
              // 승리 금액
              winAmount: isShowdownDisplay ? winnerAmounts[seat.position] : undefined,
            } : undefined;

            // 현재 턴인지 확인 (position 기반)
            const isActiveTurn = seat?.position === currentTurnPosition;

            // 해당 플레이어의 마지막 액션
            const lastAction = seat ? playerActions[seat.position] : null;

            return (
              <PlayerSeat
                key={visualIndex}
                player={player}
                position={pos}
                isCurrentUser={isCurrentUser}
                isActive={isActiveTurn}
                lastAction={lastAction}
                turnStartTime={isActiveTurn ? turnStartTime : null}
                onAutoFold={isCurrentUser && isActiveTurn ? handleAutoFold : undefined}
                handResult={isCurrentUser ? myHandAnalysis.hand : null}
                draws={isCurrentUser ? myHandAnalysis.draws : []}
              />
            );
          })}
      </main>

      {/* ========================================
          하단 액션 패널 (고정 높이: 120px)
          - 모든 상태에서 동일한 높이 유지
          - 레이아웃 시프트 방지
          ======================================== */}
      <footer className="border-t border-[var(--border)] bg-[var(--surface)] px-4 py-2">
        <div className="max-w-4xl mx-auto h-[120px] flex flex-col justify-center">
          {/* 관전자 모드: 참여하기 버튼 */}
          {isSpectator ? (
            <div className="text-center">
              <p className="text-[var(--text-secondary)] mb-2 text-sm">
                현재 관전 중입니다
              </p>
              <button
                onClick={handleJoinClick}
                className="btn btn-primary"
              >
                게임 참여하기
              </button>
            </div>
          ) : isMyTurn ? (
            <div className="flex flex-col gap-2 h-full justify-center">
              {/* 슬라이더 영역 (고정 높이: 40px) - 없어도 공간 유지 */}
              <div className="h-[40px] flex items-center">
                {(canRaise || canBet) && (
                  <div className="flex items-center gap-4 w-full">
                    <span className="text-sm text-[var(--text-secondary)] w-14">
                      {canBet ? '베팅:' : '레이즈:'}
                    </span>
                    <input
                      type="range"
                      min={minRaiseAmount}
                      max={maxRaiseAmount}
                      value={raiseAmount}
                      onChange={(e) => setRaiseAmount(parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <input
                      type="number"
                      value={raiseAmount}
                      onChange={(e) => setRaiseAmount(parseInt(e.target.value) || minRaiseAmount)}
                      className="input w-20 text-center text-sm"
                      min={minRaiseAmount}
                      max={maxRaiseAmount}
                    />
                  </div>
                )}
              </div>

              {/* 액션 버튼 영역 (고정 높이: 48px) */}
              <div className="h-[48px] flex gap-2 justify-center items-center flex-wrap">
                {/* 폴드 버튼 - 콜해야 할 때만 표시 */}
                {canFold && (
                  <button
                    onClick={handleFold}
                    className="btn action-btn action-fold"
                  >
                    폴드
                  </button>
                )}

                {/* 체크 버튼 - 체크 가능할 때만 표시 */}
                {canCheck && (
                  <button
                    onClick={handleCheck}
                    className="btn action-btn action-check"
                  >
                    체크
                  </button>
                )}

                {/* 콜 버튼 - 콜해야 할 때만 표시 */}
                {canCall && (
                  <button
                    onClick={handleCall}
                    className="btn action-btn action-call"
                  >
                    콜 {callAmount > 0 ? callAmount.toLocaleString() : ''}
                  </button>
                )}

                {/* 베팅 버튼 - 첫 베팅일 때 (아무도 베팅 안 했을 때) */}
                {canBet && (
                  <button
                    onClick={handleRaise}
                    disabled={raiseAmount < minRaiseAmount}
                    className="btn action-btn action-raise"
                  >
                    베팅 {raiseAmount.toLocaleString()}
                  </button>
                )}

                {/* 레이즈 버튼 - 누군가 베팅했을 때 */}
                {canRaise && (
                  <button
                    onClick={handleRaise}
                    disabled={raiseAmount < minRaiseAmount}
                    className="btn action-btn action-raise"
                  >
                    레이즈 {raiseAmount.toLocaleString()}
                  </button>
                )}

                {/* 올인 버튼 - 항상 표시 (레이즈/베팅 가능하거나 콜 가능할 때) */}
                {(canRaise || canBet || canCall) && (
                  <button
                    onClick={handleAllIn}
                    className="btn action-btn action-allin"
                  >
                    올인
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* 내 턴이 아닐 때 - 대기 상태 */
            <div className="flex flex-col items-center justify-center h-full">
              {currentTurnPosition !== null ? (
                <p className="text-[var(--text-secondary)] text-sm">
                  다른 플레이어의 차례를 기다리는 중...
                </p>
              ) : gameState?.phase === 'waiting' || !gameState?.phase ? (
                <div className="flex flex-col items-center gap-2">
                  <p className="text-[var(--text-secondary)] text-sm">
                    참가자: {seats.filter(s => s.player && s.status !== 'empty').length}명
                  </p>
                  <button
                    onClick={handleStartGame}
                    disabled={seats.filter(s => s.player && s.status !== 'empty').length < 2}
                    className="px-6 py-2 rounded-lg font-bold text-black bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:via-yellow-400 hover:to-amber-400 disabled:from-gray-500 disabled:via-gray-600 disabled:to-gray-700 disabled:text-gray-400 disabled:cursor-not-allowed shadow-lg transition-all duration-200"
                  >
                    게임 시작
                  </button>
                  {seats.filter(s => s.player && s.status !== 'empty').length < 2 && (
                    <p className="text-xs text-[var(--text-muted)]">
                      2명 이상이 필요합니다
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-[var(--text-secondary)] text-sm">
                  게임 진행 중...
                </p>
              )}
            </div>
          )}

        </div>
      </footer>

      {/* 바이인 모달 */}
      {showBuyInModal && user && (
        <BuyInModal
          config={tableConfig || {
            maxSeats: 9,
            smallBlind: 10,
            bigBlind: 20,
            minBuyIn: 400,
            maxBuyIn: 2000,
            turnTimeoutSeconds: 30,
          }}
          userBalance={user.balance || 0}
          onConfirm={handleBuyInConfirm}
          onCancel={handleBuyInCancel}
          isLoading={isJoining}
        />
      )}

      </div>

      {/* DEV 어드민 패널 - 최상위 레벨에 배치 */}
      <DevAdminPanel
        tableId={tableId}
        onReset={handleDevReset}
        onAddBot={handleAddBot}
        isResetting={isResetting}
        isAddingBot={isAddingBot}
      />
    </div>
  );
}
