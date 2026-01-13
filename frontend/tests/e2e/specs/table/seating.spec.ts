/**
 * Table Seating E2E Tests
 * 
 * Tests table UI, seat selection, and buy-in flow.
 * 
 * @requirements 3.1~3.6
 */

import { expect } from '@playwright/test';
import { test as authTest } from '../../fixtures/auth.fixture';
import { TablePage } from '../../pages/table.page';

authTest.describe('Table Seating', () => {
  /**
   * Task 6.1: 테이블 UI 렌더링 테스트
   * @requirements 3.1
   */
  authTest('6.1 should display poker table UI with seat positions', async ({
    authenticatedPage,
    tableId,
  }) => {
    const tablePage = new TablePage(authenticatedPage);
    await tablePage.goto(tableId);
    await tablePage.waitForTableLoad();
    
    // Table should be visible
    await expect(tablePage.table).toBeVisible();
    
    // Check for seat elements (6 seats)
    for (let i = 0; i < 6; i++) {
      const seat = authenticatedPage.getByTestId(`seat-${i}`);
      await expect(seat).toBeVisible();
    }
  });

  /**
   * Task 6.2: 바이인 모달 테스트
   * @requirements 3.2
   */
  authTest('6.2 should show buy-in modal when clicking empty seat', async ({
    authenticatedPage,
    tableId,
  }) => {
    const tablePage = new TablePage(authenticatedPage);
    await tablePage.goto(tableId);
    await tablePage.waitForTableLoad();
    
    await tablePage.clickEmptySeat(0);
    
    await expect(tablePage.buyInModal).toBeVisible();
    await expect(tablePage.buyInSlider).toBeVisible();
    await expect(tablePage.buyInConfirmButton).toBeVisible();
    
    // Cancel to reset state
    await tablePage.buyInCancelButton.click();
  });

  /**
   * Task 6.3: 바이인 완료 테스트
   * @requirements 3.3
   */
  authTest('6.3 should seat player with correct chip stack after buy-in', async ({
    authenticatedPage,
    tableId,
  }) => {
    const tablePage = new TablePage(authenticatedPage);
    await tablePage.goto(tableId);
    await tablePage.waitForTableLoad();
    
    await tablePage.clickEmptySeat(0);
    await tablePage.confirmBuyIn(1000);
    
    // Modal should close
    await expect(tablePage.buyInModal).not.toBeVisible();
    
    // Player should be seated with correct stack
    const stack = await tablePage.getMyChipStack();
    expect(stack).toBe(1000);
    
    // Position should be 0
    const position = await tablePage.getMyPosition();
    expect(position).toBe(0);
  });

  /**
   * Task 6.4: 잔액 부족 테스트
   * @requirements 3.4
   */
  authTest('6.4 should show error when balance is insufficient', async ({
    authenticatedPage,
    tableId,
  }) => {
    const tablePage = new TablePage(authenticatedPage);
    await tablePage.goto(tableId);
    await tablePage.waitForTableLoad();
    
    // Find an empty seat
    const emptySeat = authenticatedPage.locator('[data-testid^="seat-"][data-occupied="false"]').first();
    const seatExists = await emptySeat.isVisible().catch(() => false);
    
    if (seatExists) {
      await emptySeat.click();
      
      // Wait for modal to appear
      await expect(tablePage.buyInModal).toBeVisible();
      
      // Try to enter amount more than balance (very high amount)
      await tablePage.buyInInput.fill('9999999');
      
      // The confirm button should be disabled when amount exceeds balance
      const isDisabled = await tablePage.buyInConfirmButton.isDisabled();
      
      // Either button is disabled OR error message is shown
      const errorVisible = await authenticatedPage
        .getByTestId('buyin-error')
        .isVisible()
        .catch(() => false);
      
      // Validation: either button disabled or error shown
      expect(isDisabled || errorVisible).toBe(true);
      
      // Modal should still be open (not closed)
      await expect(tablePage.buyInModal).toBeVisible();
    }
  });
});
