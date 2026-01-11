# 서드파티 에셋 점검

> 폰트, 아이콘, 이미지, 사운드 라이선스 점검

---

## 1. 폰트

### 1.1 권장 폰트

| 폰트 | 라이선스 | 상용 사용 | 출처 |
|------|---------|----------|------|
| Inter | OFL 1.1 | ✅ | Google Fonts |
| Noto Sans KR | OFL 1.1 | ✅ | Google Fonts |
| JetBrains Mono | OFL 1.1 | ✅ | JetBrains |

### 1.2 OFL (Open Font License) 요약

- 상용 사용 허용
- 수정 및 재배포 허용
- 폰트 단독 판매 금지
- 라이선스 고지 필요

### 1.3 폰트 사용 예시

```css
/* Google Fonts CDN */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* 또는 로컬 호스팅 */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Regular.woff2') format('woff2');
  font-weight: 400;
}
```

---

## 2. 아이콘

### 2.1 권장 아이콘 라이브러리

| 라이브러리 | 라이선스 | 상용 사용 |
|-----------|---------|----------|
| Heroicons | MIT | ✅ |
| Lucide | ISC | ✅ |
| Phosphor Icons | MIT | ✅ |
| Tabler Icons | MIT | ✅ |

### 2.2 주의 필요 아이콘

| 라이브러리 | 라이선스 | 주의사항 |
|-----------|---------|---------|
| Font Awesome Free | CC BY 4.0 + OFL | 고지 필요 |
| Material Icons | Apache 2.0 | 고지 필요 |

---

## 3. 카드 이미지

### 3.1 옵션

| 옵션 | 라이선스 | 비용 |
|------|---------|------|
| 자체 제작 | 소유 | 디자인 비용 |
| 오픈소스 | 다양 | 무료 |
| 상용 구매 | 상용 | 유료 |

### 3.2 오픈소스 카드 덱

| 프로젝트 | 라이선스 | 출처 |
|---------|---------|------|
| svg-cards | LGPL 2.1 | GitHub |
| poker-cards | MIT | GitHub |
| vector-playing-cards | Public Domain | GitHub |

### 3.3 권장: Public Domain 또는 자체 제작

```
/public/cards/
├── 2c.svg  # 2 of Clubs
├── 2d.svg  # 2 of Diamonds
├── 2h.svg  # 2 of Hearts
├── 2s.svg  # 2 of Spades
├── ...
├── As.svg  # Ace of Spades
└── back.svg  # Card back
```

---

## 4. 사운드

### 4.1 필요 사운드

| 사운드 | 용도 |
|--------|------|
| chip_bet | 베팅 시 |
| card_deal | 카드 딜 |
| card_flip | 카드 오픈 |
| turn_alert | 턴 알림 |
| win | 승리 |
| fold | 폴드 |

### 4.2 무료 사운드 소스

| 소스 | 라이선스 | URL |
|------|---------|-----|
| Freesound | CC0/CC BY | freesound.org |
| Mixkit | Free | mixkit.co |
| Pixabay | Pixabay License | pixabay.com |

### 4.3 라이선스 확인 체크리스트

```markdown
[ ] 각 사운드 파일 출처 기록
[ ] 라이선스 유형 확인
[ ] 고지 필요 여부 확인
[ ] NOTICE 파일에 추가
```

---

## 5. 이미지/일러스트

### 5.1 테이블 배경

| 옵션 | 권장 |
|------|------|
| CSS 그라데이션 | ✅ 자체 제작 |
| SVG 패턴 | ✅ 자체 제작 |
| 이미지 파일 | 라이선스 확인 필요 |

### 5.2 아바타

| 옵션 | 라이선스 |
|------|---------|
| DiceBear | MIT |
| Boring Avatars | MIT |
| 사용자 업로드 | N/A |

---

## 6. 에셋 체크리스트

### 6.1 배포 전 확인

```markdown
## 폰트
[ ] 사용 폰트 목록 작성
[ ] 라이선스 확인
[ ] 고지 파일 추가

## 아이콘
[ ] 사용 아이콘 라이브러리 확인
[ ] 라이선스 확인
[ ] 고지 파일 추가

## 카드 이미지
[ ] 출처 확인
[ ] 라이선스 확인
[ ] 상용 사용 가능 여부 확인

## 사운드
[ ] 각 파일 출처 기록
[ ] 라이선스 확인
[ ] 고지 파일 추가

## 기타 이미지
[ ] 모든 이미지 출처 확인
[ ] 라이선스 확인
```

### 6.2 에셋 목록 템플릿

```markdown
| 파일명 | 유형 | 출처 | 라이선스 | 고지 필요 |
|--------|------|------|---------|----------|
| Inter.woff2 | 폰트 | Google Fonts | OFL 1.1 | ✅ |
| chip_bet.mp3 | 사운드 | Freesound | CC0 | ❌ |
| As.svg | 카드 | 자체 제작 | 소유 | ❌ |
```

---

## 7. NOTICE 파일 예시

```
Third-Party Assets

Fonts:
- Inter by Rasmus Andersson (OFL 1.1)
- Noto Sans KR by Google (OFL 1.1)

Icons:
- Heroicons by Tailwind Labs (MIT)

Sounds:
- chip_bet.mp3 from Freesound (CC0)
- card_deal.mp3 from Mixkit (Free License)

Card Images:
- Custom designed, owned by [Company]
```

---

## 관련 문서

- [60-license-audit.md](./60-license-audit.md) - 라이선스 감사
- [33-ui-components.md](./33-ui-components.md) - UI 컴포넌트
