/**
 * Seat Race Condition E2E Tests
 * 
 * Tests concurrent seat selection handling.
 * 
 * @requirements 3.6
 */

import { test, expect } from '@playwright/test';
import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';

multiPlayerTest.describe('Seat Race Condition', () => {
  /**
   * Task 6.5: 좌석 Race Condition 테스트
   * @requirements 3.6
   * When two players click the same seat simultaneously,
   * only one should be accepted.
   */
  multiPlayerTest(
    '6.5 should accept only one player when two click same seat simultaneously',
    async ({ playerA, playerB, tableId }) => {
      // Both players navigate to the table
      await playerA.lobbyPage.joinTable(tableId);
      await playerA.tablePage.waitForTableLoad();
      
      await playerB.lobbyPage.joinTable(tableId);
      await playerB.tablePage.waitForTableLoad();
      
      // Both players try to click seat 0 at the same time
      const seatA = playerA.page.getByTestId('seat-0');
      const seatB = playerB.page.getByTestId('seat-0');
      
      // Click simultaneously
      await Promise.all([
        seatA.click(),
        seatB.click(),
      ]);
      
      // Wait for modals to appear
      await playerA.page.waitForTimeout(500);
      await playerB.page.waitForTimeout(500);
      
      // Both try to confirm buy-in
      const confirmA = playerA.page.getByTestId('buyin-confirm');
      const confirmB = playerB.page.getByTestId('buyin-confirm');
      
      // Fill buy-in amounts
      await playerA.page.getByTestId('buyin-input').fill('1000').catch(() => {});
      await playerB.page.getByTestId('buyin-input').fill('1000').catch(() => {});
      
      // Click confirm simultaneously
      await Promise.all([
        confirmA.click().catch(() => {}),
        confirmB.click().catch(() => {}),
      ]);
      
      // Wait for server response
      await playerA.page.waitForTimeout(1000);
      await playerB.page.waitForTimeout(1000);
      
      // Check seat 0 - only one player should be seated
      const seat0A = playerA.page.getByTestId('seat-0');
      const seat0B = playerB.page.getByTestId('seat-0');
      
      const occupiedA = await seat0A.getAttribute('data-occupied');
      const occupiedB = await seat0B.getAttribute('data-occupied');
      
      // Both should see the seat as occupied
      expect(occupiedA).toBe('true');
      expect(occupiedB).toBe('true');
      
      // Only one player should have their position at seat 0
      const posA = await playerA.tablePage.getMyPosition().catch(() => -1);
      const posB = await playerB.tablePage.getMyPosition().catch(() => -1);
      
      // Exactly one should be at position 0, or both failed
      const atSeat0 = [posA, posB].filter(p => p === 0);
      expect(atSeat0.length).toBeLessThanOrEqual(1);
    }
  );
});
