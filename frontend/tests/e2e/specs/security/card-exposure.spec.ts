/**
 * Card Security E2E Tests
 * 
 * Tests that opponent hole cards are never exposed.
 * 
 * @requirements 11.4
 * @property Property 8: Card Security
 */

import { expect } from '@playwright/test';
import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { WSInspector } from '../../utils/ws-inspector';
import { waitForPhase } from '../../utils/wait-helpers';

interface PlayerData {
  holeCards?: unknown[];
}

multiPlayerTest.describe('Card Security', () => {
  /**
   * @requirements 11.4
   * Property 8: Card Security
   * For any spectator, WS messages should never contain others' hole cards.
   */
  multiPlayerTest(
    'should not expose opponent hole cards in WebSocket messages',
    async ({ playerA, tableId, setupBothPlayersAtTable }) => {
      // Attach WS inspector to player A
      const inspectorA = new WSInspector();
      
      await inspectorA.attach(playerA.page);
      
      await setupBothPlayersAtTable(tableId);
      
      // Wait for hand to start
      await waitForPhase(playerA.page, 'preflop');
      
      // Get position
      const posA = await playerA.tablePage.getMyPosition();
      
      // Check Player A's messages - should not expose other players' cards
      const exposedToA = await inspectorA.hasExposedHoleCards(playerA.page, posA);
      expect(exposedToA).toBe(false);
    }
  );

  /**
   * Spectator should not see any hole cards
   */
  multiPlayerTest(
    'spectator should not receive any hole cards in messages',
    async ({ browser, playerA, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Wait for hand to start
      await waitForPhase(playerA.page, 'preflop');
      
      // Create spectator session
      const spectatorContext = await browser.newContext();
      const spectatorPage = await spectatorContext.newPage();
      
      // Attach WS inspector
      const spectatorInspector = new WSInspector();
      await spectatorInspector.attach(spectatorPage);
      
      // Navigate to table as spectator (not seated)
      await spectatorPage.goto(`/table/${tableId}`);
      await spectatorPage.waitForLoadState('networkidle');
      
      // Wait for state sync
      await spectatorPage.waitForTimeout(2000);
      
      // Spectator should not see any hole cards
      const messages = await spectatorInspector.getMessages(spectatorPage);
      
      for (const msg of messages) {
        if (msg.payload?.players && Array.isArray(msg.payload.players)) {
          for (const player of msg.payload.players as PlayerData[]) {
            // Spectator should never see hole cards
            expect(player.holeCards || []).toHaveLength(0);
          }
        }
      }
      
      await spectatorContext.close();
    }
  );
});
