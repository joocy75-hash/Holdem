/**
 * Server Authority E2E Tests
 * 
 * Tests that server rejects invalid actions.
 * 
 * @requirements 11.1, 11.2, 11.3
 * @property Property 6: Server Authority
 * @property Property 7: Idempotency
 */

import { expect } from '@playwright/test';
import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { WSInspector } from '../../utils/ws-inspector';
import { waitForPhase } from '../../utils/wait-helpers';

interface GameWindow extends Window {
  __gameWebSocket?: WebSocket;
}

multiPlayerTest.describe('Server Authority', () => {
  /**
   * @requirements 11.1
   * Property 6: Server Authority
   * For any out-of-turn action, server should reject it.
   */
  multiPlayerTest(
    'should reject action when not player turn',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');
      
      // Find which player is NOT the active player
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const inactivePlayer = isMyTurnA ? playerB : playerA;
      
      // Attach WS inspector
      const inspector = new WSInspector();
      await inspector.attach(inactivePlayer.page);
      
      // Try to raise when not turn (via direct WS message)
      await inactivePlayer.page.evaluate(() => {
        const ws = (window as unknown as GameWindow).__gameWebSocket;
        if (ws) {
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: 'test-out-of-turn',
            payload: {
              action: 'raise',
              amount: 100,
            },
          }));
        }
      });
      
      // Wait for response
      await inactivePlayer.page.waitForTimeout(1000);
      
      // Should receive error response
      const messages = await inspector.getMessages(inactivePlayer.page);
      const errorMsg = messages.find(m => m.type === 'ERROR');
      
      expect(errorMsg).toBeDefined();
    }
  );

  /**
   * @requirements 11.2
   * Server should reject action from folded player
   */
  multiPlayerTest(
    'should reject action from folded player',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');
      
      // Find active player and fold
      const isMyTurnA = await playerA.tablePage.isMyTurn();
      const activePlayer = isMyTurnA ? playerA : playerB;
      
      await activePlayer.tablePage.fold();
      
      // Wait for fold to process
      await activePlayer.page.waitForTimeout(500);
      
      // Attach WS inspector
      const inspector = new WSInspector();
      await inspector.attach(activePlayer.page);
      
      // Try to bet after folding
      await activePlayer.page.evaluate(() => {
        const ws = (window as unknown as GameWindow).__gameWebSocket;
        if (ws) {
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: 'test-folded-action',
            payload: {
              action: 'raise',
              amount: 100,
            },
          }));
        }
      });
      
      // Wait for response
      await activePlayer.page.waitForTimeout(1000);
      
      // Should receive error response
      const messages = await inspector.getMessages(activePlayer.page);
      const errorMsg = messages.find(m => m.type === 'ERROR');
      
      expect(errorMsg).toBeDefined();
    }
  );

  /**
   * @requirements 11.3
   * Property 7: Idempotency
   * For any duplicate action_id, server should process only once.
   */
  multiPlayerTest(
    'should process duplicate action_id only once',
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
        const ws = (window as unknown as GameWindow).__gameWebSocket;
        if (ws) {
          // Send first request
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: reqId,
            payload: {
              action: 'raise',
              amount: 100,
            },
          }));
          
          // Send duplicate immediately
          ws.send(JSON.stringify({
            type: 'ACTION_REQUEST',
            requestId: reqId,
            payload: {
              action: 'raise',
              amount: 100,
            },
          }));
        }
      }, requestId);
      
      // Wait for processing
      await activePlayer.page.waitForTimeout(1000);
      
      // Pot should only increase by one raise amount, not double
      const finalPot = await activePlayer.tablePage.getPotAmount();
      const increase = finalPot - initialPot;
      
      // Should be approximately one raise (100), not double (200)
      expect(increase).toBeLessThan(150);
    }
  );
});
