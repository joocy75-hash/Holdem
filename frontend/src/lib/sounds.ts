// 오디오 스프라이트 기반 사운드 매니저
type SpriteKey = 'fold' | 'check' | 'call' | 'raise' | 'allin';

interface SpriteData {
  src: string[];
  sprite: Record<SpriteKey, [number, number]>;
}

const SPRITE_DATA: SpriteData = {
  src: ['/sounds/actions/actions_sprite.webm', '/sounds/actions/actions_sprite.m4a'],
  sprite: {
    fold: [0, 701],
    check: [701, 634],
    call: [1335, 701],
    raise: [2036, 767],
    allin: [2803, 1401],
  },
};

class SoundManager {
  private audio: HTMLAudioElement | null = null;
  private isReady = false;
  private volume = 0.5;

  init() {
    if (this.audio || typeof window === 'undefined') return;

    // WebM 지원 여부 확인
    const testAudio = document.createElement('audio');
    const canPlayWebm = testAudio.canPlayType('audio/webm; codecs=opus');
    const src = canPlayWebm ? SPRITE_DATA.src[0] : SPRITE_DATA.src[1];

    this.audio = new Audio(src);
    this.audio.volume = this.volume;
    this.audio.preload = 'auto';

    this.audio.addEventListener('canplaythrough', () => {
      this.isReady = true;
    });

    // 프리로드
    this.audio.load();
  }

  play(action: string | { type: string }) {
    if (!this.audio) this.init();
    if (!this.audio) return;

    // 액션 타입 추출 (객체 또는 문자열)
    const actionType = typeof action === 'string' ? action : action.type;
    if (!actionType) return;

    // 액션 타입 매핑
    let key = actionType.replace('_', '') as SpriteKey;
    // bet은 raise와 같은 사운드 사용 (둘 다 돈을 거는 행위)
    if (key === 'bet') key = 'raise';
    const sprite = SPRITE_DATA.sprite[key];

    if (!sprite) {
      console.warn(`Unknown action sound: ${actionType}`);
      return;
    }

    const [start, duration] = sprite;

    // 현재 재생 중지 후 새 위치에서 재생
    this.audio.currentTime = start / 1000;
    this.audio.play().catch(() => {
      // 자동재생 차단 - 무시
    });

    // duration 후 정지
    setTimeout(() => {
      if (this.audio) {
        this.audio.pause();
      }
    }, duration);
  }

  setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
    if (this.audio) {
      this.audio.volume = this.volume;
    }
  }
}

export const soundManager = new SoundManager();
