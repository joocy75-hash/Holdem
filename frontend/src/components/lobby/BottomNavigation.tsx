"use client";

import { useRouter, usePathname } from "next/navigation";
import { motion } from "framer-motion";

const quickSpring = { type: "spring" as const, stiffness: 400, damping: 20 };

// 로비 아이콘과 동일한 다층 글로우 효과 (4단계 드롭 섀도우)
const createMultiLayerGlow = (r: number, g: number, b: number) =>
  `drop-shadow(0 0 2.55px rgba(${r}, ${g}, ${b}, 0.8)) ` +
  `drop-shadow(0 0 4.05px rgba(${r}, ${g}, ${b}, 0.6)) ` +
  `drop-shadow(0 0 1.55px rgba(${r}, ${g}, ${b}, 0.9)) ` +
  `drop-shadow(0 0 5px rgba(${r}, ${g}, ${b}, 0.5))`;

// 로비와 동일한 파란색 글로우 (모든 아이콘 통일)
const activeGlow = createMultiLayerGlow(0, 170, 255);

// 다층 텍스트 섀도우 (로비 스타일 - 파란색)
const activeTextShadow =
  `0 0 2.5px rgba(0, 170, 255, 0.9), ` +
  `0 0 5px rgba(0, 170, 255, 0.7), ` +
  `0 0 10px rgba(0, 170, 255, 0.5)`;

export default function BottomNavigation() {
  const router = useRouter();
  const pathname = usePathname();

  const imgHomeGroup = "https://www.figma.com/api/mcp/asset/f171f6b2-ce17-411a-a0ca-de127a5cee45";

  const isLobbyActive = pathname === '/lobby';
  const isWalletActive = pathname === '/wallet';
  const isHistoryActive = pathname === '/history';
  const isProfileActive = pathname === '/profile';
  const isSettingsActive = pathname === '/settings';

  // 5개 아이콘 균등 배치: 390px / 5 = 78px 간격, 센터 위치
  const centers = [39, 117, 195, 273, 351];

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: '50%',
        transform: 'translateX(-50%)',
        width: '390px',
        height: '102px',
        background: 'var(--figma-gradient-footer)',
        border: '1px solid var(--figma-footer-border)',
        borderRadius: '35px 35px 0 0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10,
      }}
    >
      {/* footer inset shadow */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          borderRadius: 'inherit',
          boxShadow: 'var(--figma-shadow-footer-inset)',
        }}
      />

      {/* 1. 로비 아이콘 (기존 유지) */}
      <motion.div
        onClick={() => router.push('/lobby')}
        whileHover={{ filter: 'brightness(1.2)' }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[0]}px`,
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
          transform: 'translateX(-50%)',
        }}
      >
        <motion.img
          src={imgHomeGroup}
          alt="home"
          animate={{
            filter: isLobbyActive
              ? 'drop-shadow(0 0 8px rgba(0, 170, 255, 0.6))'
              : 'none',
            opacity: isLobbyActive ? 1 : 0.5,
          }}
          style={{
            width: '100%',
            height: '100%',
          }}
        />
      </motion.div>
      <motion.p
        onClick={() => router.push('/lobby')}
        whileHover={{ textShadow: '0px 0px 10px #0af, 0px 0px 15px #005de0' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[0]}px`,
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          color: isLobbyActive ? 'white' : 'rgba(255,255,255,0.5)',
          textShadow: isLobbyActive ? 'var(--figma-text-shadow-lobby)' : 'none',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        로비
      </motion.p>

      {/* 2. 지갑 아이콘 (충전/환전) */}
      <motion.div
        onClick={() => router.push('/wallet')}
        whileHover={{ filter: 'brightness(1.2)' }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[1]}px`,
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <motion.svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          animate={{
            filter: isWalletActive ? activeGlow : 'none',
            opacity: isWalletActive ? 1 : 0.5,
          }}
          fill="white"
        >
          <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
        </motion.svg>
      </motion.div>
      <motion.p
        onClick={() => router.push('/wallet')}
        whileHover={{ textShadow: '0px 0px 10px #048565, 0px 0px 15px #036b50' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[1]}px`,
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          color: isWalletActive ? 'white' : 'rgba(255,255,255,0.5)',
          textShadow: isWalletActive ? activeTextShadow : 'none',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        지갑
      </motion.p>

      {/* 3. 기록 아이콘 */}
      <motion.div
        onClick={() => router.push('/history')}
        whileHover={{ filter: 'brightness(1.2)' }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[2]}px`,
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <motion.svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          animate={{
            filter: isHistoryActive ? activeGlow : 'none',
            opacity: isHistoryActive ? 1 : 0.5,
          }}
          fill="white"
        >
          <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
        </motion.svg>
      </motion.div>
      <motion.p
        onClick={() => router.push('/history')}
        whileHover={{ textShadow: '0px 0px 10px #f59e0b, 0px 0px 15px #d97706' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[2]}px`,
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          color: isHistoryActive ? 'white' : 'rgba(255,255,255,0.5)',
          textShadow: isHistoryActive ? activeTextShadow : 'none',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        기록
      </motion.p>

      {/* 4. 마이 아이콘 */}
      <motion.div
        onClick={() => router.push('/profile')}
        whileHover={{ filter: 'brightness(1.2)' }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[3]}px`,
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <motion.svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          animate={{
            filter: isProfileActive ? activeGlow : 'none',
            opacity: isProfileActive ? 1 : 0.5,
          }}
          fill="white"
        >
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
        </motion.svg>
      </motion.div>
      <motion.p
        onClick={() => router.push('/profile')}
        whileHover={{ textShadow: '0px 0px 10px #667eea, 0px 0px 15px #764ba2' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[3]}px`,
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          color: isProfileActive ? 'white' : 'rgba(255,255,255,0.5)',
          textShadow: isProfileActive ? activeTextShadow : 'none',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        마이
      </motion.p>

      {/* 5. 설정 아이콘 */}
      <motion.div
        onClick={() => router.push('/settings')}
        whileHover={{ filter: 'brightness(1.2)' }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[4]}px`,
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <motion.svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          animate={{
            filter: isSettingsActive ? activeGlow : 'none',
            opacity: isSettingsActive ? 1 : 0.5,
          }}
          fill="white"
        >
          <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </motion.svg>
      </motion.div>
      <motion.p
        onClick={() => router.push('/settings')}
        whileHover={{ textShadow: '0px 0px 10px #6b7280, 0px 0px 15px #4b5563' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: `${centers[4]}px`,
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          color: isSettingsActive ? 'white' : 'rgba(255,255,255,0.5)',
          textShadow: isSettingsActive ? activeTextShadow : 'none',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        설정
      </motion.p>
    </div>
  );
}
