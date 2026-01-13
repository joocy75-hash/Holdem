/**
 * Server Recovery E2E Tests
 * 
 * Tests game state recovery after server restart or crash.
 * 
 * @requirements Task 15: Server Recovery Tests
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { expect } from '@playwright/test';
import { cheatAPI } from '../../utils/cheat-api';
import { waitForPhase, waitForGameStateSync } from '../../utils/wait-helpers';

multiPlayerTest.describe('Server Recovery', () => {
  /**
   * Task 15.1: 서버 재시작 후 핸드 복구 테스트
   * Game state should be recovered from DB/Redis snapshot after server restart.
   */
  multiPlayerTest(
    '15.1 should recover hand state after server restart',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Record state before "restart"
      const potBefore = await playerA.tablePage.getPotAmount();
      const phaseBefore = await playerA.tablePage.getCurrentPhase();
      const stackABefore = await playerA.tablePage.getMyChipStack();

      // Simulate server restart via cheat API
      await cheatAPI.simulateServerRestart();

      // Wait for reconnection
      await playerA.page.waitForTimeout(5000);
      await waitForGameStateSync(playerA.page);

      // Verify state is recovered
      const potAfter = await playerA.tablePage.getPotAmount();
      const phaseAfter = await playerA.tablePage.getCurrentPhase();
      const stackAAfter = await playerA.tablePage.getMyChipStack();

      expect(potAfter).toBe(potBefore);
      expect(phaseAfter).toBe(phaseBefore);
      expect(stackAAfter).toBe(stackABefore);
    }
  );

  /**
   * Task 15.2: 복구 후 팟 금액 유지 테스트
   * Pot amount should be exactly preserved after recovery.
   */
  multiPlayerTest(
    '15.2 should preserve pot amount after recovery',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Build up pot
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.raise(100);
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.call();
      } else {
        await playerB.tablePage.raise(100);
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.call();
      }

      // Record pot
      const potBefore = await playerA.tablePage.getPotAmount();
      expect(potBefore).toBeGreaterThan(0);

      // Simulate server restart
      await cheatAPI.simulateServerRestart();
      await playerA.page.waitForTimeout(5000);
      await waitForGameStateSync(playerA.page);

      // Verify pot is preserved
      const potAfter = await playerA.tablePage.getPotAmount();
      expect(potAfter).toBe(potBefore);
    }
  );

  /**
   * Task 15.3: 복구 후 타이머 유지 테스트
   * Remaining timer should be preserved after recovery.
   */
  multiPlayerTest(
    '15.3 should preserve timer after recovery',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get timer before restart
      const timerBefore = await playerA.tablePage.getTimerValue();

      // Simulate server restart
      await cheatAPI.simulateServerRestart();
      await playerA.page.waitForTimeout(3000);
      await waitForGameStateSync(playerA.page);

      // Timer should be close to before (accounting for restart time)
      const timerAfter = await playerA.tablePage.getTimerValue();
      
      // Timer should have decreased but not reset
      // Allow for some variance due to restart time
      expect(timerAfter).toBeLessThanOrEqual(timerBefore);
      expect(timerAfter).toBeGreaterThan(0);
    }
  );

  /**
   * Task 15.4: 복구 후 Hole Card 유지 테스트
   * Players' hole cards should be preserved after recovery.
   */
  multiPlayerTest(
    '15.4 should preserve hole cards after recovery',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get hole cards before restart
      const cardsABefore = await playerA.tablePage.getHoleCards();
      const cardsBBefore = await playerB.tablePage.getHoleCards();

      expect(cardsABefore.length).toBe(2);
      expect(cardsBBefore.length).toBe(2);

      // Simulate server restart
      await cheatAPI.simulateServerRestart();
      await playerA.page.waitForTimeout(5000);
      await waitForGameStateSync(playerA.page);
      await waitForGameStateSync(playerB.page);

      // Verify hole cards are preserved
      const cardsAAfter = await playerA.tablePage.getHoleCards();
      const cardsBAfter = await playerB.tablePage.getHoleCards();

      expect(cardsAAfter).toEqual(cardsABefore);
      expect(cardsBAfter).toEqual(cardsBBefore);
    }
  );
});
