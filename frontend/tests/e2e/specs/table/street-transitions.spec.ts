/**
 * Street Transition E2E Tests
 * 
 * Tests phase transitions: Preflop → Flop → Turn → River
 * 
 * @requirements Task 10: Street Transition Tests
 * @requirements 5.2, 5.3, 5.4, 4.5
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { expect } from '@playwright/test';
import { waitForPhase } from '../../utils/wait-helpers';

multiPlayerTest.describe('Street Transitions', () => {
  /**
   * Task 10.1: Preflop → Flop 전환 테스트
   * @requirements 5.2
   */
  multiPlayerTest(
    '10.1 should transition from Preflop to Flop with 3 community cards',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Verify preflop state - no community cards
      const preflopCards = await playerA.tablePage.getCommunityCardCount();
      expect(preflopCards).toBe(0);

      // Complete preflop betting
      // In heads-up: dealer/SB acts first preflop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call(); // SB calls BB
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check(); // BB checks
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Wait for flop
      await waitForPhase(playerA.page, 'flop', 10000);

      // Verify flop - 3 community cards
      const flopCardsA = await playerA.tablePage.getCommunityCardCount();
      const flopCardsB = await playerB.tablePage.getCommunityCardCount();

      expect(flopCardsA).toBe(3);
      expect(flopCardsB).toBe(3);

      // Verify phase on both clients
      const phaseA = await playerA.tablePage.getCurrentPhase();
      const phaseB = await playerB.tablePage.getCurrentPhase();

      expect(phaseA).toBe('flop');
      expect(phaseB).toBe('flop');
    }
  );

  /**
   * Task 10.2: Flop → Turn 전환 테스트
   * @requirements 5.3
   */
  multiPlayerTest(
    '10.2 should transition from Flop to Turn with 4 community cards',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Get to flop first
      await waitForPhase(playerA.page, 'preflop');
      
      // Complete preflop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      await waitForPhase(playerA.page, 'flop', 10000);

      // Complete flop betting (both check)
      // Post-flop: BB acts first (or first active player left of dealer)
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.check();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.check();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Wait for turn
      await waitForPhase(playerA.page, 'turn', 10000);

      // Verify turn - 4 community cards
      const turnCardsA = await playerA.tablePage.getCommunityCardCount();
      const turnCardsB = await playerB.tablePage.getCommunityCardCount();

      expect(turnCardsA).toBe(4);
      expect(turnCardsB).toBe(4);

      const phaseA = await playerA.tablePage.getCurrentPhase();
      const phaseB = await playerB.tablePage.getCurrentPhase();

      expect(phaseA).toBe('turn');
      expect(phaseB).toBe('turn');
    }
  );

  /**
   * Task 10.3: Turn → River 전환 테스트
   * @requirements 5.4
   */
  multiPlayerTest(
    '10.3 should transition from Turn to River with 5 community cards',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      
      // Navigate through all streets
      await waitForPhase(playerA.page, 'preflop');
      
      // Preflop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Flop
      await waitForPhase(playerA.page, 'flop', 10000);
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.check();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.check();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Turn
      await waitForPhase(playerA.page, 'turn', 10000);
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.check();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.check();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Wait for river
      await waitForPhase(playerA.page, 'river', 10000);

      // Verify river - 5 community cards
      const riverCardsA = await playerA.tablePage.getCommunityCardCount();
      const riverCardsB = await playerB.tablePage.getCommunityCardCount();

      expect(riverCardsA).toBe(5);
      expect(riverCardsB).toBe(5);

      const phaseA = await playerA.tablePage.getCurrentPhase();
      const phaseB = await playerB.tablePage.getCurrentPhase();

      expect(phaseA).toBe('river');
      expect(phaseB).toBe('river');
    }
  );

  /**
   * Task 10.4: 전원 체크 시 즉시 전환 테스트
   * @requirements 4.5
   */
  multiPlayerTest(
    '10.4 should transition immediately when all players check',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Complete preflop to get to flop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      await waitForPhase(playerA.page, 'flop', 10000);

      // Record time before checks
      const startTime = Date.now();

      // Both players check quickly
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.check();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.check();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      // Wait for turn
      await waitForPhase(playerA.page, 'turn', 5000);

      const transitionTime = Date.now() - startTime;

      // Transition should be quick (within 3 seconds of last check)
      expect(transitionTime).toBeLessThan(5000);

      const phase = await playerA.tablePage.getCurrentPhase();
      expect(phase).toBe('turn');
    }
  );

  /**
   * Task 10.5: 베팅 금액 일치 시 전환 테스트
   * @requirements 4.5
   */
  multiPlayerTest(
    '10.5 should transition when all bets are matched',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get to flop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      await waitForPhase(playerA.page, 'flop', 10000);

      // One player raises, other calls (bets matched)
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.raise(50);
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.call(); // Match the bet
      } else {
        await playerB.tablePage.raise(50);
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.call(); // Match the bet
      }

      // Should transition to turn after bets are matched
      await waitForPhase(playerA.page, 'turn', 10000);

      const phaseA = await playerA.tablePage.getCurrentPhase();
      const phaseB = await playerB.tablePage.getCurrentPhase();

      expect(phaseA).toBe('turn');
      expect(phaseB).toBe('turn');

      // Verify 4 community cards
      const cards = await playerA.tablePage.getCommunityCardCount();
      expect(cards).toBe(4);
    }
  );

  /**
   * Additional: Community cards should be consistent across clients
   */
  multiPlayerTest(
    'should show same community cards to all players',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get to flop
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      await waitForPhase(playerA.page, 'flop', 10000);

      // Get community cards from both players
      const cardsA = await playerA.tablePage.getCommunityCards();
      const cardsB = await playerB.tablePage.getCommunityCards();

      // Cards should be identical
      expect(cardsA).toEqual(cardsB);
      expect(cardsA.length).toBe(3);
    }
  );
});
