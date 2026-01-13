/**
 * Betting Convenience Buttons E2E Tests (피망 스타일)
 * 
 * Tests pot ratio buttons (1/4, 1/2, 3/4, Pot) functionality.
 * 
 * @requirements Task 19: Betting Buttons Tests
 * @requirements 15.1~15.6
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { expect } from '@playwright/test';
import { cheatAPI } from '../../utils/cheat-api';
import { waitForPhase } from '../../utils/wait-helpers';

multiPlayerTest.describe('Betting Convenience Buttons (피망 스타일)', () => {
  /**
   * Task 19.1: 1/4 Pot 버튼 계산 테스트
   * Clicking 1/4 pot button should input 25% of pot.
   * @requirements 15.1
   */
  multiPlayerTest(
    '19.1 should calculate 1/4 pot correctly',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Build pot to 1000
      await cheatAPI.forcePotAmount(tableId, 1000);
      await playerA.page.waitForTimeout(500);

      // Find active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      // Click 1/4 pot button
      await activePlayer.tablePage.clickPotRatioButton('1/4');

      // Verify input value is 250 (1000 * 0.25)
      const inputValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(inputValue).toBe(250);
    }
  );

  /**
   * Task 19.2: 1/2 Pot 버튼 계산 테스트
   * Clicking 1/2 pot button should input 50% of pot.
   * @requirements 15.2
   */
  multiPlayerTest(
    '19.2 should calculate 1/2 pot correctly',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      await cheatAPI.forcePotAmount(tableId, 1000);
      await playerA.page.waitForTimeout(500);

      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      await activePlayer.tablePage.clickPotRatioButton('1/2');

      const inputValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(inputValue).toBe(500);
    }
  );

  /**
   * Task 19.3: 3/4 Pot 버튼 계산 테스트
   * Clicking 3/4 pot button should input 75% of pot.
   * @requirements 15.3
   */
  multiPlayerTest(
    '19.3 should calculate 3/4 pot correctly',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      await cheatAPI.forcePotAmount(tableId, 1000);
      await playerA.page.waitForTimeout(500);

      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      await activePlayer.tablePage.clickPotRatioButton('3/4');

      const inputValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(inputValue).toBe(750);
    }
  );

  /**
   * Task 19.4: Pot 버튼 계산 테스트
   * Clicking pot button should input 100% of pot.
   * @requirements 15.4
   */
  multiPlayerTest(
    '19.4 should calculate full pot correctly',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      await cheatAPI.forcePotAmount(tableId, 1000);
      await playerA.page.waitForTimeout(500);

      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;

      await activePlayer.tablePage.clickPotRatioButton('pot');

      const inputValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(inputValue).toBe(1000);
    }
  );

  /**
   * Task 19.5: 실시간 팟 변경 반영 테스트
   * Button amounts should recalculate when pot changes.
   * @requirements 15.5
   */
  multiPlayerTest(
    '19.5 should recalculate button amounts when pot changes',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Initial pot
      await cheatAPI.forcePotAmount(tableId, 500);
      await playerA.page.waitForTimeout(500);

      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      const otherPlayer = isMyTurnA ? playerB : playerA;

      // Check initial 1/2 pot value
      await activePlayer.tablePage.clickPotRatioButton('1/2');
      const initialValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(initialValue).toBe(250); // 500 * 0.5

      // Other player raises, increasing pot
      await otherPlayer.page.waitForTimeout(500);
      await cheatAPI.forcePotAmount(tableId, 1000);
      await activePlayer.page.waitForTimeout(1000);

      // Click 1/2 pot again
      await activePlayer.tablePage.clickPotRatioButton('1/2');
      const updatedValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(updatedValue).toBe(500); // 1000 * 0.5
    }
  );

  /**
   * Task 19.6: 스택 초과 방지 테스트
   * Button should cap at player's stack if pot ratio exceeds it.
   * @requirements 15.6
   */
  multiPlayerTest(
    '19.6 should cap bet at player stack when pot ratio exceeds it',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Set large pot but small stack
      await cheatAPI.forcePotAmount(tableId, 10000);
      
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      
      // Get player's stack
      const playerStack = await activePlayer.tablePage.getMyChipStack();

      // Click full pot button (10000 > player stack)
      await activePlayer.tablePage.clickPotRatioButton('pot');

      // Input should be capped at player's stack
      const inputValue = await activePlayer.tablePage.getRaiseInputValue();
      expect(inputValue).toBeLessThanOrEqual(playerStack);
    }
  );
});
