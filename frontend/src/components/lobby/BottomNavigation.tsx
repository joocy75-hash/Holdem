"use client";

import { motion } from "framer-motion";

const quickSpring = { type: "spring" as const, stiffness: 400, damping: 20 };

export default function BottomNavigation() {
  const imgHomeGroup = "https://www.figma.com/api/mcp/asset/f171f6b2-ce17-411a-a0ca-de127a5cee45";

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

      {/* 홈 아이콘 그룹 */}
      <motion.div
        whileHover={{
          filter: 'brightness(1.2)',
        }}
        whileTap={{ filter: 'brightness(0.9)' }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: '22px',
          top: '7px',
          width: '55px',
          height: '55px',
          cursor: 'pointer',
        }}
      >
        <motion.img
          src={imgHomeGroup}
          alt="home"
          animate={{
            filter: 'drop-shadow(0 0 8px rgba(0, 170, 255, 0.6))',
          }}
          style={{
            width: '100%',
            height: '100%',
          }}
        />
      </motion.div>

      {/* 로비 텍스트 */}
      <motion.p
        whileHover={{
          textShadow: '0px 0px 10px #0af, 0px 0px 15px #005de0',
        }}
        transition={quickSpring}
        style={{
          position: 'absolute',
          left: '49px',
          top: '62px',
          margin: 0,
          fontFamily: 'Paperlogy, sans-serif',
          fontWeight: 600,
          fontSize: '12px',
          lineHeight: 'normal',
          color: 'white',
          textAlign: 'center',
          textShadow: 'var(--figma-text-shadow-lobby)',
          transform: 'translateX(-50%)',
          cursor: 'pointer',
        }}
      >
        로비
      </motion.p>
    </div>
  );
}
