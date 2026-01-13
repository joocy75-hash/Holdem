'use client';

import { useState, useEffect, useCallback } from 'react';

interface Banner {
  id: string;
  imageUrl: string;
  title: string;
  actionText?: string;
  onClick?: () => void;
}

interface BannerCarouselProps {
  banners: Banner[];
  autoPlayInterval?: number;
}

// Default placeholder banners
const defaultBanners: Banner[] = [
  {
    id: '1',
    imageUrl: '',
    title: '환영합니다!',
    actionText: '이벤트 참여',
  },
  {
    id: '2',
    imageUrl: '',
    title: '신규 유저 보너스',
    actionText: '보너스 받기',
  },
  {
    id: '3',
    imageUrl: '',
    title: '토너먼트 준비중',
    actionText: '알림 신청',
  },
];

export default function BannerCarousel({
  banners = defaultBanners,
  autoPlayInterval = 4000
}: BannerCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const displayBanners = banners.length > 0 ? banners : defaultBanners;

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % displayBanners.length);
  }, [displayBanners.length]);

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  // Auto-play
  useEffect(() => {
    if (isHovered || displayBanners.length <= 1) return;

    const interval = setInterval(goToNext, autoPlayInterval);
    return () => clearInterval(interval);
  }, [goToNext, autoPlayInterval, isHovered, displayBanners.length]);

  const currentBanner = displayBanners[currentIndex];

  return (
    <div
      className="banner-carousel"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Banner Content */}
      <div className="relative w-full h-full bg-gradient-to-br from-[var(--neon-purple-dark)] to-[var(--neon-purple)] rounded-xl overflow-hidden">
        {currentBanner.imageUrl ? (
          <img
            src={currentBanner.imageUrl}
            alt={currentBanner.title}
            className="banner-slide"
          />
        ) : (
          // Placeholder design when no image
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center">
            <div className="text-3xl font-bold text-white mb-2 drop-shadow-lg">
              {currentBanner.title}
            </div>
            {currentBanner.actionText && (
              <button
                onClick={currentBanner.onClick}
                className="mt-4 px-6 py-2 bg-white/20 hover:bg-white/30 rounded-full text-white font-semibold transition-all"
              >
                {currentBanner.actionText}
              </button>
            )}
          </div>
        )}

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent pointer-events-none" />
      </div>

      {/* Indicators */}
      {displayBanners.length > 1 && (
        <div className="banner-indicators">
          {displayBanners.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`banner-dot ${index === currentIndex ? 'active' : ''}`}
              aria-label={`배너 ${index + 1}로 이동`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
