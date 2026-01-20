'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import BottomNavigation from '@/components/lobby/BottomNavigation';
import SoundSettings from '@/components/settings/SoundSettings';
import NotificationSettings from '@/components/settings/NotificationSettings';
import SecuritySettings from '@/components/settings/SecuritySettings';
import AppInfo from '@/components/settings/AppInfo';

export default function SettingsPage() {
  const router = useRouter();

  return (
    <div className="page-bg-gradient" style={{ width: '390px', minHeight: '100vh', margin: '0 auto', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* 노이즈 텍스처 */}
      <div className="noise-overlay" />

      {/* 배경 장식 */}
      <div
        style={{
          position: 'absolute',
          top: '20%',
          right: '-20%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '30%',
          left: '-15%',
          width: '250px',
          height: '250px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* 헤더 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.85) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          position: 'relative',
          zIndex: 10,
        }}
      >
        <motion.button
          onClick={() => router.back()}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.05 }}
          style={{
            background: 'rgba(255,255,255,0.08)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '10px',
            padding: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </motion.button>
        <h1
          style={{
            flex: 1,
            textAlign: 'center',
            color: 'white',
            fontSize: '18px',
            fontWeight: 700,
            margin: 0,
            marginRight: '38px',
            textShadow: '0 2px 8px rgba(0,0,0,0.3)',
            letterSpacing: '0.5px',
          }}
        >
          설정
        </h1>
      </div>

      {/* 설정 내용 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          paddingBottom: '100px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* 사운드 설정 */}
        <SoundSettings />

        {/* 알림 설정 */}
        <NotificationSettings />

        {/* 보안 설정 */}
        <SecuritySettings />

        {/* 앱 정보 */}
        <AppInfo />
      </div>

      {/* 하단 네비게이션 */}
      <BottomNavigation />
    </div>
  );
}
