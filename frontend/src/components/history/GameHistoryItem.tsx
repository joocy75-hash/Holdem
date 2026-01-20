'use client';

import { HandHistory } from '@/lib/api';

interface GameHistoryItemProps {
  hand: HandHistory;
}

// 카드 렌더링 헬퍼
function renderCard(card: string) {
  const suit = card.slice(-1);
  const rank = card.slice(0, -1);

  const suitColors: Record<string, string> = {
    'h': '#ef4444',
    'd': '#3b82f6',
    'c': '#22c55e',
    's': '#374151',
  };

  const suitSymbols: Record<string, string> = {
    'h': '♥',
    'd': '♦',
    'c': '♣',
    's': '♠',
  };

  return (
    <span
      key={card}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '28px',
        height: '36px',
        background: 'linear-gradient(180deg, #ffffff 0%, #f3f4f6 100%)',
        borderRadius: '5px',
        fontSize: '12px',
        fontWeight: 700,
        color: suitColors[suit] || '#000',
        marginRight: '4px',
        boxShadow: '0 2px 6px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.8)',
        border: '1px solid rgba(0,0,0,0.1)',
      }}
    >
      {rank}{suitSymbols[suit]}
    </span>
  );
}

export default function GameHistoryItem({ hand }: GameHistoryItemProps) {
  const isWin = hand.net_result > 0;
  const isLose = hand.net_result < 0;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const actionLabels: Record<string, string> = {
    'fold': '폴드',
    'showdown': '쇼다운',
    'all_in_won': '올인 승리',
    'timeout': '타임아웃',
  };

  return (
    <div
      className="glass-card"
      style={{
        padding: '16px',
        marginBottom: '12px',
        borderColor: isWin
          ? 'rgba(34, 197, 94, 0.3)'
          : isLose
          ? 'rgba(239, 68, 68, 0.3)'
          : undefined,
        background: isWin
          ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(255,255,255,0.03) 100%)'
          : isLose
          ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(255,255,255,0.03) 100%)'
          : undefined,
      }}
    >
      {/* 헤더 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '14px',
        }}
      >
        <div>
          <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 500 }}>
            핸드 #{hand.hand_number}
          </span>
          <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '12px', marginLeft: '10px' }}>
            {formatDate(hand.started_at)}
          </span>
        </div>
        <span
          style={{
            padding: '5px 10px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: isWin
              ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)'
              : isLose
              ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(220, 38, 38, 0.15) 100%)'
              : 'rgba(255,255,255,0.08)',
            color: isWin ? '#4ade80' : isLose ? '#f87171' : 'rgba(255,255,255,0.6)',
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
          }}
        >
          {actionLabels[hand.user_final_action] || hand.user_final_action}
        </span>
      </div>

      {/* 카드 */}
      <div style={{ marginBottom: '14px' }}>
        <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center' }}>
          <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '11px', marginRight: '10px', minWidth: '50px' }}>
            홀카드
          </span>
          <div style={{ display: 'flex' }}>
            {hand.user_hole_cards?.map(renderCard)}
          </div>
        </div>
        {hand.community_cards && hand.community_cards.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '11px', marginRight: '10px', minWidth: '50px' }}>
              커뮤니티
            </span>
            <div style={{ display: 'flex' }}>
              {hand.community_cards.map(renderCard)}
            </div>
          </div>
        )}
      </div>

      {/* 결과 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '14px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div>
          <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px' }}>베팅: </span>
          <span style={{ color: 'white', fontSize: '14px', fontWeight: 500 }}>
            {hand.user_bet_amount.toLocaleString()}
          </span>
        </div>
        <div>
          <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px' }}>결과: </span>
          <span
            className={isWin ? 'glow-text-green' : ''}
            style={{
              color: isWin ? '#4ade80' : isLose ? '#f87171' : 'white',
              fontSize: '18px',
              fontWeight: 700,
            }}
          >
            {hand.net_result > 0 ? '+' : ''}{hand.net_result.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
