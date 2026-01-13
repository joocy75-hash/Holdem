# Phase 4: 테이블 Page Object 수정 체크리스트

## 📋 개요
- **우선순위**: 중간
- **예상 소요 시간**: 2-3시간
- **상태**: ✅ 완료
- **의존성**: Phase 3 완료 권장

---

## 4.1 TablePage 클래스 메서드 수정

### 파일: `frontend/tests/e2e/pages/table.page.ts`

#### 4.1.1 clickPotRatioButton() 메서드 수정
- [x] 현재 코드 분석
- [x] 실제 컴포넌트의 testid와 일치하도록 수정
- [x] 테스트 완료

**구현 상태**: 이미 올바르게 구현됨
```typescript
// pot-ratio-0.25, pot-ratio-0.5, pot-ratio-0.75, pot-ratio-1 사용
```

---

#### 4.1.2 waitForTableLoad() 메서드 개선
- [x] 현재 코드 분석
- [x] WebSocket 연결 대기 추가
- [x] 테이블 상태 수신 대기
- [x] 테스트 완료

**구현 내용**:
```typescript
async waitForTableLoad(): Promise<void> {
  // Wait for table UI to be visible
  await expect(this.table).toBeVisible({ timeout: 10000 });
  
  // Wait for WebSocket connection (Connected badge)
  await this.page.waitForSelector('.badge-success:has-text("Connected")', { 
    timeout: 10000,
    state: 'visible'
  });
}
```

---

#### 4.1.3 clickEmptySeat() 메서드 개선
- [x] 현재 코드 분석
- [x] 좌석이 실제로 비어있는지 확인
- [x] 클릭 후 바이인 모달 대기
- [x] 테스트 완료

**구현 내용**:
```typescript
async clickEmptySeat(position?: number): Promise<void> {
  if (position !== undefined) {
    // Click specific seat, verify it's empty first
    const seat = this.page.locator(`[data-testid="seat-${position}"][data-occupied="false"]`);
    await expect(seat).toBeVisible({ timeout: 5000 });
    await seat.click();
  } else {
    // Click first available empty seat
    const emptySeat = this.page.locator('[data-testid^="seat-"][data-occupied="false"]').first();
    await expect(emptySeat).toBeVisible({ timeout: 5000 });
    await emptySeat.click();
  }
  
  // Wait for buy-in modal to appear
  await expect(this.buyInModal).toBeVisible({ timeout: 5000 });
}
```

---

#### 4.1.4 confirmBuyIn() 메서드 개선
- [x] 현재 코드 분석
- [x] 모달이 보이는지 먼저 확인
- [x] 입력 후 확인 버튼 클릭
- [x] 모달 닫힘 대기
- [x] 착석 확인 로직 추가
- [x] 테스트 완료

**구현 내용**:
```typescript
async confirmBuyIn(amount: number): Promise<void> {
  // Ensure modal is visible
  await expect(this.buyInModal).toBeVisible({ timeout: 5000 });
  
  // Fill in the amount
  await this.buyInInput.fill(amount.toString());
  
  // Click confirm button
  await this.buyInConfirmButton.click();
  
  // Wait for modal to close
  await expect(this.buyInModal).not.toBeVisible({ timeout: 10000 });
  
  // Verify player is seated (has data-is-me="true")
  await this.page.waitForSelector('[data-testid^="seat-"][data-is-me="true"]', { 
    timeout: 10000 
  });
}
```

---

#### 4.1.5 getMyStack() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 내 스택 금액 파싱 로직
- [x] 테스트 완료

**구현 상태**: `getMyChipStack()` 메서드로 이미 구현됨
```typescript
async getMyChipStack(): Promise<number> {
  const myStack = this.page.getByTestId('my-stack');
  const text = await myStack.textContent();
  return parseInt(text?.replace(/[^0-9]/g, '') || '0');
}
```

---

#### 4.1.6 getPotAmount() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 팟 금액 파싱 로직
- [x] 테스트 완료

**구현 상태**: 이미 구현됨
```typescript
async getPotAmount(): Promise<number> {
  const text = await this.pot.textContent();
  return parseInt(text?.replace(/[^0-9]/g, '') || '0');
}
```

---

#### 4.1.7 getCurrentPhase() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 현재 게임 페이즈 반환 로직
- [x] 테스트 완료

**구현 상태**: 이미 구현됨
```typescript
async getCurrentPhase(): Promise<GamePhase> {
  const phase = await this.page.getByTestId('game-phase').getAttribute('data-phase');
  return (phase as GamePhase) || 'waiting';
}
```

---

## ✅ Phase 4 완료 체크포인트

```bash
# 착석 테스트 실행
cd frontend
npm run test:e2e -- --grep "seating" --project=chromium

# 바이인 테스트 실행
npm run test:e2e -- --grep "buy-in" --project=chromium
```

---

## 📝 작업 노트

### 2026-01-13 완료된 작업
1. **waitForTableLoad() 개선**
   - WebSocket 연결 대기 로직 추가 (Connected 배지 확인)

2. **clickEmptySeat() 개선**
   - position 파라미터 optional로 변경
   - 좌석이 비어있는지 확인 후 클릭
   - 바이인 모달 표시 대기

3. **confirmBuyIn() 개선**
   - 모달 표시 확인
   - 모달 닫힘 대기
   - 착석 확인 (data-is-me="true")
