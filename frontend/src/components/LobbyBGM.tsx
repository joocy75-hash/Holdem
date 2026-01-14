"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

const TARGET_VOLUME = 0.3;
const FADE_DURATION = 3000; // 3초 페이드아웃
const FADE_INTERVAL = 50; // 50ms 간격으로 볼륨 조정

export default function LobbyBGM() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fadeIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pathname = usePathname();

  // 게임방(/table/*), 로그인 페이지에서는 BGM 비활성화
  const isMuted = pathname?.startsWith("/table/") || pathname === "/login";

  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio("/sounds/bgm/lobby_bgm.webm");
      audioRef.current.loop = true;
      audioRef.current.volume = TARGET_VOLUME;
    }

    const audio = audioRef.current;

    // 이전 페이드 인터벌 정리
    if (fadeIntervalRef.current) {
      clearInterval(fadeIntervalRef.current);
      fadeIntervalRef.current = null;
    }

    if (isMuted) {
      // 페이드아웃 (3초에 걸쳐 서서히 볼륨 감소)
      const steps = FADE_DURATION / FADE_INTERVAL;
      const volumeStep = audio.volume / steps;

      fadeIntervalRef.current = setInterval(() => {
        if (audio.volume > volumeStep) {
          audio.volume = Math.max(0, audio.volume - volumeStep);
        } else {
          audio.volume = 0;
          audio.pause();
          if (fadeIntervalRef.current) {
            clearInterval(fadeIntervalRef.current);
            fadeIntervalRef.current = null;
          }
        }
      }, FADE_INTERVAL);
    } else {
      // 볼륨 복구 및 재생
      audio.volume = TARGET_VOLUME;
      // 사용자 인터랙션 후 재생 시도
      const playAudio = () => {
        audio.play().catch(() => {
          // 자동재생 차단시 클릭 이벤트로 재생
          const handleClick = () => {
            audio.play();
            document.removeEventListener("click", handleClick);
          };
          document.addEventListener("click", handleClick);
        });
      };
      playAudio();
    }

    return () => {
      // 컴포넌트 언마운트 시에도 오디오 유지 (페이지 이동 시 끊김 방지)
    };
  }, [isMuted]);

  // 페이지 이탈 시 오디오 정리
  useEffect(() => {
    return () => {
      if (fadeIntervalRef.current) {
        clearInterval(fadeIntervalRef.current);
        fadeIntervalRef.current = null;
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return null;
}
