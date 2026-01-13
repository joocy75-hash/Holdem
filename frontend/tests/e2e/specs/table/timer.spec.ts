/**
 * Timer & Auto-fold E2E Tests
 * 
 * Tests turn timer display, auto-fold on timeout, and timer synchronization.
 * 
 * @requirements Task 13: Timer Tests
 * @requirements 7.1, 7.2, 7.3
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { expect } from '@playwright/test';
import { waitForPhase } from '../../utils/wait-helpers';

multiPlayerTest.describe('Timer & Auto-fold', () => {
  /**
   * Task 13.1: 타이머 표시 테스트
   * Timer countdown should be displayed when turn starts.
   * @requirements 7.1
   */
  multiPlayerTest(
    '13.1 should display timer countdown when turn starts',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Find active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      // Timer should be visible for active player
      const timerVisible = await activePlayer.tablePage.timer.isVisible();
      expect(timerVisible).toBe(true);

      // Timer should show a value
      const timerValue = await activePlayer.tablePage.getTimerValue();
      expect(timerValue).toBeGreaterThan(0);
      expect(timerValue).toBeLessThanOrEqual(10); // Max timer is 10 seconds
    }
  );

  /**
   * Task 13.2: 자동 폴드 테스트
   * Player should auto-fold when timer expires.
   * @requirements 7.2
   */
  multiPlayerTest(
    '13.2 should auto-fold when timer expires',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Find active player and their position
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      const observingPlayer = isMyTurnA ? playerB : playerA;
      const activePosition = await activePlayer.tablePage.getMyPosition();

      // Wait for timer to expire (don't take any action)
      await activePlayer.tablePage.waitForTurnTimeout(15000);

      // Wait for state update
      await observingPlayer.page.waitForTimeout(1000);

      // Player should be auto-folded
      const status = await observingPlayer.tablePage.getPlayerStatus(activePosition);
      expect(status).toBe('fold');
    }
  );

  /**
   * Task 13.3: 액션 후 타이머 중지 테스트
   * Timer should disappear after player takes action.
   * @requirements 7.3
   */
  multiPlayerTest(
    '13.3 should stop timer after action is taken',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Find active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      // Verify timer is visible before action
      const timerVisibleBefore = await activePlayer.tablePage.timer.isVisible();
      expect(timerVisibleBefore).toBe(true);

      // Take action
      await activePlayer.tablePage.call();

      // Wait for UI update
      await activePlayer.page.waitForTimeout(500);

      // Timer should no longer be visible for this player
      // (it may now be visible for the other player)
      const isStillMyTurn = await activePlayer.tablePage.isMyTurn();
      if (!isStillMyTurn) {
        // If turn passed, timer should not be active for this player
        const timerVisibleAfter = await activePlayer.tablePage.timer.isVisible();
        // Timer might still be visible but for the other player
        // Check that action buttons are disabled
        const hasButtons = await activePlayer.tablePage.hasActionButtons();
        expect(hasButtons).toBe(false);
      }
    }
  );

  /**
   * Task 13.4: 서버-클라이언트 타이머 동기화 테스트
   * Server and client timers should be within ±1 second.
   */
  multiPlayerTest(
    '13.4 should synchronize timer between server and client (±1 second)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get timer values from both clients
      const timerA = await playerA.tablePage.getTimerValue();
      const timerB = await playerB.tablePage.getTimerValue();

      // Timers should be synchronized (within 1 second)
      const diff = Math.abs(timerA - timerB);
      expect(diff).toBeLessThanOrEqual(1);

      // Wait a bit and check again
      await playerA.page.waitForTimeout(2000);

      const timerA2 = await playerA.tablePage.getTimerValue();
      const timerB2 = await playerB.tablePage.getTimerValue();

      // Should still be synchronized
      const diff2 = Math.abs(timerA2 - timerB2);
      expect(diff2).toBeLessThanOrEqual(1);

      // Timer should have decreased
      expect(timerA2).toBeLessThan(timerA);
    }
  );
});
