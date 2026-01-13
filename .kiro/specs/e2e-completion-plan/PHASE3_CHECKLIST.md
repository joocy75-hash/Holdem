# Phase 3: 테이블 페이지 UI 완성 체크리스트

## 📋 개요
- **우선순위**: 중간
- **예상 소요 시간**: 2-3시간
- **상태**: ✅ 완료
- **의존성**: 없음 (독립적으로 진행 가능)

---

## 3.1 누락된 data-testid 속성 추가

### 파일: `frontend/src/app/table/[id]/page.tsx`

#### 3.1.1 바이인 모달 testid 추가
- [x] `data-testid="buyin-modal"` - 모달 컨테이너
- [x] `data-testid="buyin-slider"` - 바이인 금액 슬라이더
- [x] `data-testid="buyin-input"` - 바이인 금액 입력
- [x] `data-testid="buyin-confirm"` - 확인 버튼
- [x] `data-testid="buyin-cancel"` - 취소 버튼
- [x] 테스트 완료

---

#### 3.1.2 타이머 관련 testid 추가
- [x] `data-testid="turn-timer"` - 턴 타이머 표시
- [x] `data-testid="timeout-indicator"` - 타임아웃 경고 표시
- [x] 테스트 완료

---

#### 3.1.3 딜러 버튼 및 블라인드 마커 testid 추가
- [x] `data-testid="dealer-button"` + `data-position={dealerPosition}` ✅ 완료
- [x] `data-testid="small-blind-marker"` + `data-position={sbPosition}` ✅ 완료
- [x] `data-testid="big-blind-marker"` + `data-position={bbPosition}` ✅ 완료
- [x] 테스트 완료

**구현 내용**:
- 백엔드에서 `dealerPosition`, `smallBlindSeat`, `bigBlindSeat` 전송
- 프론트엔드에서 상태 변수 추가 및 UI 렌더링
- 딜러 버튼: 흰색 원형 "D" 마커
- SB 마커: 파란색 원형 "SB" 마커
- BB 마커: 빨간색 원형 "BB" 마커

---

#### 3.1.4 플레이어 스택 testid 추가
- [x] `data-testid="my-stack"` - 내 스택 표시
- [x] `data-testid={`stack-${position}`}` - 각 플레이어 스택
- [x] 테스트 완료

---

#### 3.1.5 승리 배지 testid 추가
- [x] `data-testid={`win-badge-${position}`}` - 승리 표시
- [x] 테스트 완료

---

#### 3.1.6 사이드 팟 testid 추가
- [x] `data-testid={`side-pot-${index}`}` + `data-amount` + `data-players` ✅ 완료
- [x] 테스트 완료

**구현 내용**:
- 백엔드에서 `sidePots` 배열 전송 시 UI 렌더링
- 각 사이드 팟에 `data-testid`, `data-amount`, `data-players` 속성 추가
- 노란색 배경의 사이드 팟 표시 UI

---

#### 3.1.7 네비게이션 버튼 testid 추가
- [x] `data-testid="leave-button"` ✅ 완료
- [x] `data-testid="sitout-button"` ✅ 완료
- [x] `data-testid="sitin-button"` ✅ 완료
- [x] 테스트 완료

**구현 내용**:
- Sit Out/In 버튼 UI 추가 (착석한 플레이어만 표시)
- `handleSitOut`, `handleSitIn` 핸들러 추가
- WebSocket 이벤트: `SIT_OUT_REQUEST`, `SIT_IN_REQUEST`
- 참고: 백엔드 API 구현은 별도 작업 필요

---

## 3.2 피망 스타일 컴포넌트 testid 확인

### 파일: `frontend/src/components/table/pmang/*.tsx`

#### 3.2.1 HandRankingGuide testid 확인
- [x] `data-testid="hand-ranking-guide"` ✅ 완료
- [x] `data-testid="current-hand-rank"` ✅ 완료
- [x] 테스트 완료

---

#### 3.2.2 PotRatioButtons testid 확인
- [x] `data-testid="pot-ratio-buttons"` ✅ 완료
- [x] `data-testid="pot-ratio-0.25"` ✅ 완료
- [x] `data-testid="pot-ratio-0.5"` ✅ 완료
- [x] `data-testid="pot-ratio-0.75"` ✅ 완료
- [x] `data-testid="pot-ratio-1"` ✅ 완료
- [x] `data-testid="pot-ratio-allin"` ✅ 완료
- [x] 테스트 완료

---

#### 3.2.3 ShowdownHighlight testid 확인
- [x] `data-testid="showdown-highlight"` ✅ 완료
- [x] `data-highlighted="true"` 속성 확인
- [x] 테스트 완료

---

#### 3.2.4 CardSqueeze testid 확인
- [x] `data-testid="my-hole-cards"` ✅ 완료
- [x] `data-testid="hole-card-{index}"` ✅ 완료
- [x] `data-revealed` 속성 ✅ 완료
- [x] 테스트 완료

---

## ✅ Phase 3 완료 체크포인트

```bash
# 브라우저 개발자 도구에서 확인
document.querySelectorAll('[data-testid]').length

# 피망 스타일 테스트 실행
cd frontend
npm run test:e2e -- --grep "피망" --project=chromium
```

---

## 📝 작업 노트

### 2024-01-13 완료된 작업
1. **딜러 버튼 및 블라인드 마커 UI 추가**
   - `dealerPosition`, `smallBlindPosition`, `bigBlindPosition` 상태 변수 추가
   - TABLE_SNAPSHOT, HAND_STARTED 핸들러에서 위치 데이터 처리
   - 테이블 UI에 딜러 버튼(D), SB, BB 마커 렌더링

2. **사이드 팟 UI 추가**
   - `sidePots` 상태 변수 추가
   - TABLE_SNAPSHOT, TABLE_STATE_UPDATE 핸들러에서 사이드 팟 데이터 처리
   - 테이블 UI에 사이드 팟 표시

3. **Sit Out/In 버튼 추가**
   - `isSittingOut` 상태 변수 추가
   - `handleSitOut`, `handleSitIn` 핸들러 추가
   - 헤더에 Sit Out/In 버튼 UI 추가
   - 참고: 백엔드 WebSocket 이벤트 핸들러 구현 필요 (SIT_OUT_REQUEST, SIT_IN_REQUEST)

### 백엔드 추가 작업 필요
- `SIT_OUT_REQUEST`, `SIT_IN_REQUEST` WebSocket 이벤트 핸들러 구현
- 사이드 팟 계산 및 전송 로직 확인/구현
