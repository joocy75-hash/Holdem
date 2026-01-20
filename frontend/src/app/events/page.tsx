'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { announcementsApi, ActiveAnnouncement } from '@/lib/api';
import { useAnnouncementStore } from '@/stores/announcement';
import BottomNavigation from '@/components/lobby/BottomNavigation';

const TYPE_LABELS: Record<string, string> = {
  notice: '공지',
  event: '이벤트',
  maintenance: '점검',
  urgent: '긴급',
};

// 공지에 포함될 타입들
const NOTICE_TYPES = ['notice', 'maintenance', 'urgent'];

export default function EventsPage() {
  const router = useRouter();
  const [announcements, setAnnouncements] = useState<ActiveAnnouncement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<ActiveAnnouncement | null>(null);

  const { markAsRead } = useAnnouncementStore();

  const fetchAnnouncements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await announcementsApi.getActive(50);
      setAnnouncements(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch announcements:', err);
      setError('공지사항을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  // 이벤트와 공지 분리
  const events = useMemo(() => {
    return announcements.filter((item) => item.announcement_type === 'event');
  }, [announcements]);

  const notices = useMemo(() => {
    return announcements.filter((item) => NOTICE_TYPES.includes(item.announcement_type));
  }, [announcements]);

  const handleSelect = (item: ActiveAnnouncement) => {
    setSelectedAnnouncement(item);
    markAsRead(item.id);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // 아이템 렌더링 컴포넌트
  const renderItem = (item: ActiveAnnouncement) => (
    <motion.div
      key={item.id}
      whileTap={{ scale: 0.99 }}
      onClick={() => handleSelect(item)}
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: '10px',
        padding: '14px 16px',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span
          style={{
            fontSize: '11px',
            color: 'rgba(255,255,255,0.5)',
            background: 'rgba(255,255,255,0.06)',
            padding: '3px 8px',
            borderRadius: '4px',
            fontWeight: 500,
          }}
        >
          {TYPE_LABELS[item.announcement_type] || '공지'}
        </span>
        {item.priority === 'critical' && (
          <span
            style={{
              fontSize: '10px',
              color: '#f87171',
              fontWeight: 600,
            }}
          >
            긴급
          </span>
        )}
      </div>
      <h3
        style={{
          color: '#fff',
          fontSize: '14px',
          fontWeight: 500,
          margin: '0 0 4px 0',
          lineHeight: 1.4,
        }}
      >
        {item.title}
      </h3>
      <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '12px', margin: 0 }}>
        {formatDate(item.created_at)}
      </p>
    </motion.div>
  );

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        maxWidth: '430px',
        minHeight: '100vh',
        margin: '0 auto',
        background: '#0f172a',
        paddingBottom: '100px',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          background: '#0f172a',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        <button
          onClick={() => router.back()}
          style={{
            background: 'transparent',
            border: 'none',
            padding: '8px 12px',
            color: 'rgba(255,255,255,0.6)',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          ← 뒤로
        </button>
        <h1 style={{ color: '#fff', fontSize: '17px', fontWeight: 600, margin: 0 }}>
          이벤트/공지
        </h1>
      </div>

      {/* Content */}
      <div style={{ padding: '16px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                border: '2px solid rgba(255,255,255,0.1)',
                borderTopColor: 'rgba(255,255,255,0.5)',
                borderRadius: '50%',
                margin: '0 auto 16px',
                animation: 'spin 1s linear infinite',
              }}
            />
            <style jsx>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', margin: 0 }}>
              로딩 중...
            </p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', margin: '0 0 16px 0' }}>
              {error}
            </p>
            <button
              onClick={fetchAnnouncements}
              style={{
                padding: '10px 20px',
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                color: 'rgba(255,255,255,0.7)',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              다시 시도
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* 이벤트 섹션 */}
            <div>
              <h2
                style={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '13px',
                  fontWeight: 600,
                  margin: '0 0 12px 4px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                이벤트 ({events.length})
              </h2>
              {events.length === 0 ? (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '32px 20px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: '10px',
                    border: '1px solid rgba(255,255,255,0.04)',
                  }}
                >
                  <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '13px', margin: 0 }}>
                    진행 중인 이벤트가 없습니다.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {events.map(renderItem)}
                </div>
              )}
            </div>

            {/* 공지 섹션 */}
            <div>
              <h2
                style={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '13px',
                  fontWeight: 600,
                  margin: '0 0 12px 4px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                공지 ({notices.length})
              </h2>
              {notices.length === 0 ? (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '32px 20px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: '10px',
                    border: '1px solid rgba(255,255,255,0.04)',
                  }}
                >
                  <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '13px', margin: 0 }}>
                    공지사항이 없습니다.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {notices.map(renderItem)}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedAnnouncement && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedAnnouncement(null)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.7)',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 30, stiffness: 400 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                width: 'calc(100% - 32px)',
                maxWidth: '380px',
                maxHeight: '70vh',
                background: '#1e293b',
                borderRadius: '16px',
                padding: '24px 20px',
                overflowY: 'auto',
              }}
            >
              {/* Type Badge */}
              <div style={{ marginBottom: '12px' }}>
                <span
                  style={{
                    fontSize: '11px',
                    color: 'rgba(255,255,255,0.5)',
                    background: 'rgba(255,255,255,0.08)',
                    padding: '4px 10px',
                    borderRadius: '4px',
                    fontWeight: 500,
                  }}
                >
                  {TYPE_LABELS[selectedAnnouncement.announcement_type] || '공지'}
                </span>
              </div>

              {/* Title */}
              <h2
                style={{
                  color: '#fff',
                  fontSize: '18px',
                  fontWeight: 600,
                  margin: '0 0 6px 0',
                  lineHeight: 1.4,
                }}
              >
                {selectedAnnouncement.title}
              </h2>

              {/* Date */}
              <p
                style={{
                  color: 'rgba(255,255,255,0.35)',
                  fontSize: '12px',
                  margin: '0 0 20px 0',
                }}
              >
                {formatDate(selectedAnnouncement.created_at)}
                {selectedAnnouncement.end_time && ` ~ ${formatDate(selectedAnnouncement.end_time)}`}
              </p>

              {/* Content */}
              <div
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '10px',
                  padding: '16px',
                  marginBottom: '20px',
                }}
              >
                <p
                  style={{
                    color: 'rgba(255,255,255,0.75)',
                    fontSize: '14px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.7,
                    margin: 0,
                  }}
                >
                  {selectedAnnouncement.content}
                </p>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setSelectedAnnouncement(null)}
                style={{
                  width: '100%',
                  padding: '14px',
                  background: 'rgba(255,255,255,0.1)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                닫기
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Navigation */}
      <BottomNavigation />
    </div>
  );
}
