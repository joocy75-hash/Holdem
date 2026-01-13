/**
 * Player Departure & Sit-out E2E Tests
 * 
 * Tests player leaving during hand, sit-out, and sit-in behavior.
 * 
 * @requirements Task 11-1: Player Departure & Sit-out Tests
 * @requirements 8.2
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { test as nPlayerTest } from '../../fixtures/n-player.fixture';
import { expect } from '@playwright/test';
import { waitForPhase, waitForNewHand } from '../../utils/wait-helpers';

multiPlayerTest.describe('Player Departure During Hand', () => {
  /**
   * Task 11-1.1: 핸드 중 나가기 테스트
   * When player leaves during their turn, should auto-fold.
   * Contributed chips remain in pot.
   * @requirements 8.2
   */
  multiPlayerTest(
    '11-1.1 should auto-fold when player leaves during hand',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get initial pot
      const initialPot = await playerA.tablePage.getPotAmount();

      // Find which player's turn it is
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      const remainingPlayer = isMyTurnA ? playerB : playerA;
      const activePosition = await activePlayer.tablePage.getMyPosition();

      // Active player raises then leaves
      await activePlayer.tablePage.raise(50);
      await activePlayer.page.waitForTimeout(500);

      // Record pot after raise
      const potAfterRaise = await remainingPlayer.tablePage.getPotAmount();
      expect(potAfterRaise).toBeGreaterThan(initialPot);

      // Active player leaves during hand
      await activePlayer.tablePage.leaveTable();

      // Wait for state update
      await remainingPlayer.page.waitForTimeout(1000);

      // Verify player status shows fold or departed
      const status = await remainingPlayer.tablePage.getPlayerStatus(activePosition);
      expect(['fold', 'departed']).toContain(status);

      // Pot should still contain the contributed chips
      const finalPot = await remainingPlayer.tablePage.getPotAmount();
      expect(finalPot).toBeGreaterThanOrEqual(potAfterRaise);
    }
  );
});

nPlayerTest.describe('Sit-out & Sit-in', () => {
  /**
   * Task 11-1.2: Sit-out 상태 테스트
   * Player in sit-out should auto-fold from next hand.
   */
  nPlayerTest(
    '11-1.2 should auto-fold sit-out player from next hand',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);

      // Setup all players
      for (const player of players) {
        await player.tablePage.goto(tableId);
        await player.tablePage.waitForTableLoad();
        const seat = await player.tablePage.findEmptySeat();
        if (seat !== null) {
          await player.tablePage.clickEmptySeat(seat);
          await player.tablePage.confirmBuyIn(1000);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Player 0 sits out
      await players[0].tablePage.sitOut();
      const position0 = await players[0].tablePage.getMyPosition();

      // Complete current hand
      for (const player of players.slice(1)) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.fold();
          }
        } catch {
          // Ignore
        }
      }

      // Wait for new hand
      await waitForNewHand(players[1].page);
      await waitForPhase(players[1].page, 'preflop');

      // Verify sit-out player status
      const status = await players[1].tablePage.getPlayerStatus(position0);
      expect(['sitout', 'fold']).toContain(status);

      // Sit-out player should not have action buttons
      const hasButtons = await players[0].tablePage.hasActionButtons();
      expect(hasButtons).toBe(false);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 11-1.3: Sit-in 복귀 테스트
   * Player who sits back in should participate from next hand.
   */
  nPlayerTest(
    '11-1.3 should participate after sit-in from next hand',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);

      // Setup all players
      for (const player of players) {
        await player.tablePage.goto(tableId);
        await player.tablePage.waitForTableLoad();
        const seat = await player.tablePage.findEmptySeat();
        if (seat !== null) {
          await player.tablePage.clickEmptySeat(seat);
          await player.tablePage.confirmBuyIn(1000);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Player 0 sits out
      await players[0].tablePage.sitOut();

      // Complete current hand
      for (const player of players.slice(1)) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.fold();
          }
        } catch {
          // Ignore
        }
      }

      // Wait for new hand
      await waitForNewHand(players[1].page);

      // Player 0 sits back in
      await players[0].tablePage.sitIn();

      // Complete this hand too
      for (const player of players.slice(1)) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.fold();
          }
        } catch {
          // Ignore
        }
      }

      // Wait for another new hand
      await waitForNewHand(players[0].page);
      await waitForPhase(players[0].page, 'preflop');

      // Player 0 should now be active
      const position0 = await players[0].tablePage.getMyPosition();
      const status = await players[1].tablePage.getPlayerStatus(position0);
      expect(status).toBe('active');

      // Player 0 should receive hole cards
      const holeCards = await players[0].tablePage.getHoleCards();
      expect(holeCards.length).toBe(2);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );
});
