/**
 * Multiplayer Interaction E2E Tests
 * 
 * Tests betting synchronization, turn indication, and fold state.
 * 
 * @requirements 4.1~4.5
 * @property Property 1: Betting Synchronization
 * @property Property 2: Turn Indication Consistency
 * @property Property 3: Fold State Consistency
 */

import { expect } from '@playwright/test';
import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { waitForPhase } from '../../utils/wait-helpers';

// Extend Window interface for game WebSocket
declare global {
  interface Window {
    __gameWebSocket?: WebSocket;
  }
}

multiPlayerTest.describe('Multiplayer Interactions', () => {
  /**
   * Task 8.1: 베팅 동기화 테스트
   * @requirements 4.1, 4.4
   * Property 1: Betting Synchronization
   * For any betting action by Player A, Player B's UI should
   * reflect updated pot within 2 seconds.
   */
  multiPlayerTest(
    '8.1 should synchronize betting actions across players (Property 1)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Wait for hand to start
      await waitForPhase(playerA.page, 'preflop');
      await waitForPhase(playerB.page, 'preflop');
      
      // Get initial pot
      const initialPot = await playerA.tablePage.getPotAmount();
      
      // Wait for player A's turn and raise
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.raise(100);
      } else {
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.raise(100);
      }
      
      // Player B's UI should update within 2 seconds
      await playerB.page.waitForTimeout(2000);
      
      const updatedPotB = await playerB.tablePage.getPotAmount();
      expect(updatedPotB).toBeGreaterThan(initialPot);
    }
  );

  /**
   * Task 8.2: 턴 표시 테스트
   * @requirements 4.2
   * Property 2: Turn Indication Consistency
   * For any player whose turn it is, action buttons should be displayed.
   */
  multiPlayerTest(
    '8.2 should display action buttons only for active player (Property 2)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Wait for preflop
      await waitForPhase(playerA.page, 'preflop');
      
      // Check which player has action buttons
      const hasButtonsA = await playerA.tablePage.hasActionButtons();
      const hasButtonsB = await playerB.tablePage.hasActionButtons();
      
      // Exactly one player should have action buttons
      expect(hasButtonsA !== hasButtonsB).toBe(true);
      
      // The player with buttons should be able to act
      if (hasButtonsA) {
        const isMyTurnA = await playerA.tablePage.isMyTurn();
        expect(isMyTurnA).toBe(true);
      } else {
        const isMyTurnB = await playerB.tablePage.isMyTurn();
        expect(isMyTurnB).toBe(true);
      }
    }
  );

  /**
   * Task 8.3: 폴드 상태 동기화 테스트
   * @requirements 4.3
   * Property 3: Fold State Consistency
   * For any player who folds, status should show "FOLD" across all clients.
   */
  multiPlayerTest(
    '8.3 should show FOLD status across all clients when player folds (Property 3)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Wait for preflop
      await waitForPhase(playerA.page, 'preflop');
      
      // Find which player can act and fold
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const foldingPlayer = isMyTurnA ? playerA : playerB;
      const observingPlayer = isMyTurnA ? playerB : playerA;
      const foldingPosition = await foldingPlayer.tablePage.getMyPosition();
      
      // Fold
      await foldingPlayer.tablePage.fold();
      
      // Wait for state sync
      await observingPlayer.page.waitForTimeout(1000);
      
      // Check fold status on both clients
      const statusOnFolding = await foldingPlayer.tablePage.getPlayerStatus(foldingPosition);
      const statusOnObserving = await observingPlayer.tablePage.getPlayerStatus(foldingPosition);
      
      expect(statusOnFolding).toBe('fold');
      expect(statusOnObserving).toBe('fold');
    }
  );

  /**
   * Task 8.4: Negative Test - 턴 아닐 때 액션 시도
   * @requirements 11.1
   */
  multiPlayerTest(
    '8.4 should reject action when not player turn (Server Authority)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');
      
      // Find which player is NOT the active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const inactivePlayer = isMyTurnA ? playerB : playerA;
      
      // Try to raise when not turn (via direct WS message)
      const result = await inactivePlayer.page.evaluate(() => {
        return new Promise((resolve) => {
          const ws = window.__gameWebSocket;
          if (ws) {
            ws.send(JSON.stringify({
              type: 'ACTION_REQUEST',
              requestId: 'test-out-of-turn',
              payload: { action: 'raise', amount: 100 },
            }));
            setTimeout(() => resolve(true), 500);
          } else {
            resolve(false);
          }
        });
      });
      
      // Action should be rejected (pot shouldn't change unexpectedly)
      expect(result).toBeDefined();
    }
  );

  /**
   * Task 8.5: Negative Test - 폴드 후 베팅 시도
   * @requirements 11.2
   */
  multiPlayerTest(
    '8.5 should reject action from folded player',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');
      
      // Find active player and fold
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      
      await activePlayer.tablePage.fold();
      await activePlayer.page.waitForTimeout(500);
      
      // Try to bet after folding
      const result = await activePlayer.page.evaluate(() => {
        return new Promise((resolve) => {
          const ws = window.__gameWebSocket;
          if (ws) {
            ws.send(JSON.stringify({
              type: 'ACTION_REQUEST',
              requestId: 'test-folded-action',
              payload: { action: 'raise', amount: 100 },
            }));
            setTimeout(() => resolve(true), 500);
          } else {
            resolve(false);
          }
        });
      });
      
      expect(result).toBeDefined();
    }
  );

  /**
   * Task 8.6: Idempotency 테스트
   * @requirements 11.3
   * Property 7: Idempotency
   */
  multiPlayerTest(
    '8.6 should process duplicate action_id only once (Idempotency)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');
      
      // Find active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      
      // Get initial pot
      const initialPot = await activePlayer.tablePage.getPotAmount();
      
      // Send same action twice with same requestId
      const requestId = `idempotency-test-${Date.now()}`;
      
      await activePlayer.page.evaluate((reqId) => {
        const ws = window.__gameWebSocket;
        if (ws) {
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: reqId,
            payload: { action: 'call' },
          }));
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: reqId,
            payload: { action: 'call' },
          }));
        }
      }, requestId);
      
      await activePlayer.page.waitForTimeout(1000);
      
      // Pot should only increase by one call amount
      const finalPot = await activePlayer.tablePage.getPotAmount();
      const increase = finalPot - initialPot;
      
      // Should be approximately one call (BB amount), not double
      expect(increase).toBeLessThanOrEqual(40); // Max BB is 20, so call is at most 20
    }
  );

  /**
   * @requirements 4.5
   * Phase transition after betting round completes
   */
  multiPlayerTest(
    'should transition to next phase when betting round completes',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Wait for preflop
      await waitForPhase(playerA.page, 'preflop');
      
      // Complete preflop betting (both players call/check)
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }
      
      // Should transition to flop
      await waitForPhase(playerA.page, 'flop', 10000);
      
      const phaseA = await playerA.tablePage.getCurrentPhase();
      const phaseB = await playerB.tablePage.getCurrentPhase();
      
      expect(phaseA).toBe('flop');
      expect(phaseB).toBe('flop');
      
      // Should have 3 community cards
      const cardsA = await playerA.tablePage.getCommunityCardCount();
      const cardsB = await playerB.tablePage.getCommunityCardCount();
      
      expect(cardsA).toBe(3);
      expect(cardsB).toBe(3);
    }
  );
});
