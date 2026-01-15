"use client";

import { useState } from "react";
import { motion } from "framer-motion";

const quickSpring = { type: "spring" as const, stiffness: 400, damping: 20 };

export type TabType = 'all' | 'tournament' | 'holdem';

interface GameTabsProps {
  onTabChange?: (tab: TabType) => void;
}

interface TabConfig {
  key: TabType;
  label: string;
  width: number;
  gradient: string;
  border: string;
  shadow: string;
  hoverGlow: string;
}

const tabs: TabConfig[] = [
  {
    key: 'all',
    label: '전체',
    width: 104,
    gradient: 'var(--figma-gradient-tab-all)',
    border: 'var(--figma-tab-border-gray)',
    shadow: 'var(--figma-shadow-card), var(--figma-shadow-tab-inset)',
    hoverGlow: '0 0 15px rgba(255, 255, 255, 0.2)',
  },
  {
    key: 'tournament',
    label: '토너먼트',
    width: 139,
    gradient: 'var(--figma-gradient-tab-tournament)',
    border: 'var(--figma-tab-border-blue)',
    shadow: 'var(--figma-shadow-tab-blue-inset)',
    hoverGlow: '0 0 18px rgba(0, 95, 248, 0.4)',
  },
  {
    key: 'holdem',
    label: '홀덤',
    width: 116,
    gradient: 'var(--figma-gradient-tab-holdem)',
    border: 'var(--figma-tab-border-purple)',
    shadow: 'var(--figma-shadow-card), var(--figma-shadow-tab-purple-inset)',
    hoverGlow: '0 0 18px rgba(98, 20, 255, 0.4)',
  },
];

export default function GameTabs({ onTabChange }: GameTabsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('all');

  const handleTabClick = (tab: TabType) => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '6px',
        alignItems: 'center',
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;

        return (
          <motion.div
            key={tab.key}
            onClick={() => handleTabClick(tab.key)}
            whileHover={{
              filter: 'brightness(1.15)',
              boxShadow: `${tab.shadow}, ${tab.hoverGlow}`,
            }}
            whileTap={{ filter: 'brightness(0.9)' }}
            animate={{
              filter: isActive ? 'brightness(1.1)' : 'brightness(1)',
              opacity: isActive ? 1 : 0.85,
            }}
            transition={quickSpring}
            style={{
              position: 'relative',
              width: tab.width,
              height: 28,
              background: tab.gradient,
              border: `1px solid ${tab.border}`,
              borderRadius: 15,
              boxShadow: tab.shadow,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <p
              style={{
                margin: 0,
                fontFamily: 'Paperlogy, sans-serif',
                fontWeight: 600,
                fontSize: 13,
                lineHeight: 'normal',
                color: 'white',
                textAlign: 'center',
              }}
            >
              {tab.label}
            </p>
          </motion.div>
        );
      })}
    </div>
  );
}
