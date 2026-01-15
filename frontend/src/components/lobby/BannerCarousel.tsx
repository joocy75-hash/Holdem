"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

const quickSpring = { type: "spring" as const, stiffness: 400, damping: 20 };

const banners = [
  "/assets/images/banner1.png",
  "/assets/images/banner1.png", // TODO: banner2.png 추가 시 교체
  "/assets/images/banner1.png", // TODO: banner3.png 추가 시 교체
];

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? '100%' : '-100%',
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? '-100%' : '100%',
    opacity: 0,
  }),
};

export default function BannerCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  const goToSlide = useCallback((index: number) => {
    setDirection(index > currentIndex ? 1 : -1);
    setCurrentIndex(index);
  }, [currentIndex]);

  // 자동 슬라이드 (5초 간격)
  useEffect(() => {
    const timer = setInterval(() => {
      setDirection(1);
      setCurrentIndex((prev) => (prev + 1) % banners.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <motion.div
      whileHover={{ filter: 'brightness(1.05)' }}
      transition={{ duration: 0.2 }}
      style={{
        position: 'relative',
        width: '372px',
        height: '192px',
        borderRadius: '15px',
        boxShadow: 'var(--figma-shadow-card)',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
    >
      <AnimatePresence initial={false} custom={direction} mode="popLayout">
        <motion.img
          key={currentIndex}
          src={banners[currentIndex]}
          alt={`배너 ${currentIndex + 1}`}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.4, ease: 'easeInOut' }}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AnimatePresence>

      {/* 인디케이터 (dots) */}
      <div
        style={{
          position: 'absolute',
          bottom: 12,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 8,
          padding: '6px 12px',
          background: 'rgba(0, 0, 0, 0.4)',
          borderRadius: 12,
          backdropFilter: 'blur(4px)',
        }}
      >
        {banners.map((_, index) => (
          <motion.button
            key={index}
            onClick={(e) => {
              e.stopPropagation();
              goToSlide(index);
            }}
            whileHover={{ filter: 'brightness(1.3)' }}
            whileTap={{ filter: 'brightness(0.8)' }}
            animate={{
              width: currentIndex === index ? 20 : 8,
              background: currentIndex === index
                ? 'rgba(255, 255, 255, 1)'
                : 'rgba(255, 255, 255, 0.4)',
              boxShadow: currentIndex === index
                ? '0 0 6px rgba(255, 255, 255, 0.6)'
                : 'none',
            }}
            transition={quickSpring}
            style={{
              height: 8,
              borderRadius: 4,
              border: 'none',
              cursor: 'pointer',
              padding: 0,
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}
