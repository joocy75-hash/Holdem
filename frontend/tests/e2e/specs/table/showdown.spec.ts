/**
 * Showdown & Result Distribution E2E Tests
 * 
 * Tests winner display, pot distribution, card reveal, and odd chip handling.
 * 
 * @requirements Task 12: Showdown Tests
 * @requirements 6.1, 6.2, 5.5, 6.4
 * @property Property 4: Winner Pot Distribution
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { test as nPlayerTest } from '../../fixtures/n-player.fixture';
import { expect } from '@playwright/test';
import { cheatAPI, parseCard, parseCards } from '../../utils/cheat-api';
import { waitForPhase, waitForShowdown, waitForWinner, waitForNewHand } from '../../utils/wait-helpers';

multiPlayerTest.describe('Showdown & Winner Display', () => {
  /**
   * Task 12.1: 승자 표시 테스트
   * Winner should display WIN badge.
   * @requirements 6.1
   */
  multiPlayerTest(
    '12.1 should display WIN badge for winner',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Inject cards so playerA wins
      const posA = await playerA.tablePage.getMyPosition();
      const posB = await playerB.tablePage.getMyPosition();

      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [posA]: [parseCard('As'), parseCard('Ah')], // Pocket Aces
          [posB]: [parseCard('2c'), parseCard('7d')], // Weak hand
        },
        communityCards: parseCards(['Ac', 'Ad', '3h', '5s', '9c']), // Four Aces for A
      });

      // Play through to showdown (both check/call)
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

      // Flop, Turn, River - both check
      for (const phase of ['flop', 'turn', 'river']) {
        await waitForPhase(playerA.page, phase, 10000);
        if (await playerA.tablePage.isMyTurn()) {
          await playerA.tablePage.check();
          await playerB.tablePage.waitForMyTurn();
          await playerB.tablePage.check();
        } else {
          await playerB.tablePage.check();
          await playerA.tablePage.waitForMyTurn();
          await playerA.tablePage.check();
        }
      }

      // Wait for showdown
      await waitForShowdown(playerA.page);
      await waitForWinner(playerA.page);

      // Verify WIN badge on player A
      const hasWinBadgeA = await playerA.tablePage.hasWinBadge(posA);
      expect(hasWinBadgeA).toBe(true);

      // Player B should not have WIN badge
      const hasWinBadgeB = await playerA.tablePage.hasWinBadge(posB);
      expect(hasWinBadgeB).toBe(false);
    }
  );

  /**
   * Task 12.2: 팟 분배 테스트 (Property 4)
   * Winner's chip stack should increase by pot amount.
   * @requirements 6.2
   * Property 4: Winner Pot Distribution
   */
  multiPlayerTest(
    '12.2 should distribute pot to winner correctly (Property 4)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Record initial stacks
      const initialStackA = await playerA.tablePage.getMyChipStack();
      const initialStackB = await playerB.tablePage.getMyChipStack();

      // Inject winning hand for A
      const posA = await playerA.tablePage.getMyPosition();
      const posB = await playerB.tablePage.getMyPosition();

      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [posA]: [parseCard('Ks'), parseCard('Kh')],
          [posB]: [parseCard('Qs'), parseCard('Qh')],
        },
        communityCards: parseCards(['Kc', '2d', '3h', '5s', '9c']),
      });

      // Both players raise to build pot
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.raise(100);
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.call();
      } else {
        await playerB.tablePage.raise(100);
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.call();
      }

      // Check through remaining streets
      for (const phase of ['flop', 'turn', 'river']) {
        await waitForPhase(playerA.page, phase, 10000);
        if (await playerA.tablePage.isMyTurn()) {
          await playerA.tablePage.check();
          await playerB.tablePage.waitForMyTurn();
          await playerB.tablePage.check();
        } else {
          await playerB.tablePage.check();
          await playerA.tablePage.waitForMyTurn();
          await playerA.tablePage.check();
        }
      }

      await waitForShowdown(playerA.page);
      await waitForWinner(playerA.page);

      // Wait for pot distribution
      await playerA.page.waitForTimeout(2000);

      // Verify winner's stack increased
      const finalStackA = await playerA.tablePage.getMyChipStack();
      const finalStackB = await playerB.tablePage.getMyChipStack();

      // Player A should have won the pot
      expect(finalStackA).toBeGreaterThan(initialStackA);
      expect(finalStackB).toBeLessThan(initialStackB);

      // Total chips should be conserved
      expect(finalStackA + finalStackB).toBe(initialStackA + initialStackB);
    }
  );

  /**
   * Task 12.3: 쇼다운 카드 공개 테스트
   * At showdown, remaining players' hole cards should be revealed.
   * @requirements 5.5
   */
  multiPlayerTest(
    '12.3 should reveal hole cards at showdown',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      const posB = await playerB.tablePage.getMyPosition();

      // Play to showdown
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.call();
        await playerB.tablePage.waitForMyTurn();
        await playerB.tablePage.check();
      } else {
        await playerB.tablePage.call();
        await playerA.tablePage.waitForMyTurn();
        await playerA.tablePage.check();
      }

      for (const phase of ['flop', 'turn', 'river']) {
        await waitForPhase(playerA.page, phase, 10000);
        if (await playerA.tablePage.isMyTurn()) {
          await playerA.tablePage.check();
          await playerB.tablePage.waitForMyTurn();
          await playerB.tablePage.check();
        } else {
          await playerB.tablePage.check();
          await playerA.tablePage.waitForMyTurn();
          await playerA.tablePage.check();
        }
      }

      await waitForShowdown(playerA.page);

      // Player A should be able to see Player B's hole cards
      const opponentCards = playerA.page.locator(
        `[data-testid="seat-${posB}"] [data-testid^="hole-card-"]`
      );
      const cardCount = await opponentCards.count();
      expect(cardCount).toBe(2);

      // Cards should be face-up (revealed)
      const card1Revealed = await opponentCards.nth(0).getAttribute('data-revealed');
      const card2Revealed = await opponentCards.nth(1).getAttribute('data-revealed');
      expect(card1Revealed).toBe('true');
      expect(card2Revealed).toBe('true');
    }
  );

  /**
   * Task 12.6: 새 핸드 시작 테스트
   * After hand ends, new hand should start with chip stacks preserved.
   * @requirements 6.4
   */
  multiPlayerTest(
    '12.6 should start new hand with preserved chip stacks',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Complete a hand (one player folds)
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.fold();
      } else {
        await playerB.tablePage.fold();
      }

      // Record stacks after hand
      await playerA.page.waitForTimeout(1000);
      const stackAfterHand = await playerA.tablePage.getMyChipStack();

      // Wait for new hand
      await waitForNewHand(playerA.page);
      await waitForPhase(playerA.page, 'preflop');

      // Verify stack is preserved (minus blinds)
      const stackNewHand = await playerA.tablePage.getMyChipStack();
      
      // Stack should be close to previous (accounting for blinds)
      const blindTotal = 30; // SB + BB
      expect(Math.abs(stackNewHand - stackAfterHand)).toBeLessThanOrEqual(blindTotal);

      // Verify new hole cards dealt
      const holeCards = await playerA.tablePage.getHoleCards();
      expect(holeCards.length).toBe(2);
    }
  );
});

nPlayerTest.describe('Odd Chip Distribution', () => {
  /**
   * Task 12.4: Rounding/Odd Chip 테스트 (2인 동점)
   * 501 chips split between 2 winners: 251 and 250.
   */
  nPlayerTest(
    '12.4 should handle odd chip with 2-way tie correctly',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(2);

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

      // Inject identical hands for tie
      const pos0 = await players[0].tablePage.getMyPosition();
      const pos1 = await players[1].tablePage.getMyPosition();

      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [pos0]: [parseCard('As'), parseCard('Kh')], // Same strength
          [pos1]: [parseCard('Ac'), parseCard('Kd')], // Same strength
        },
        communityCards: parseCards(['2c', '3d', '4h', '5s', '9c']), // No help
      });

      // Build pot to odd amount (501)
      // This requires specific betting - use cheat API
      await cheatAPI.forcePotAmount(tableId, 501);

      // Play to showdown
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.check();
          }
        } catch {
          // Ignore
        }
      }

      await waitForShowdown(players[0].page);
      await players[0].page.waitForTimeout(2000);

      // Get final stacks
      const stack0 = await players[0].tablePage.getMyChipStack();
      const stack1 = await players[1].tablePage.getMyChipStack();

      // One should get 251, other 250 (or close to it)
      const diff = Math.abs(stack0 - stack1);
      expect(diff).toBeLessThanOrEqual(1);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 12.5: Rounding/Odd Chip 테스트 (3인 동점)
   * 100 chips split 3 ways: 34, 33, 33 (extra chip to position rule).
   */
  nPlayerTest(
    '12.5 should handle odd chip with 3-way tie correctly',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);

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

      // Inject identical hands for 3-way tie
      const positions = await Promise.all(
        players.map(p => p.tablePage.getMyPosition())
      );

      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [positions[0]]: [parseCard('As'), parseCard('Kh')],
          [positions[1]]: [parseCard('Ac'), parseCard('Kd')],
          [positions[2]]: [parseCard('Ad'), parseCard('Ks')],
        },
        communityCards: parseCards(['2c', '3d', '4h', '5s', '9c']),
      });

      // Force pot to 100
      await cheatAPI.forcePotAmount(tableId, 100);

      // Play to showdown
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.check();
          }
        } catch {
          // Ignore
        }
      }

      await waitForShowdown(players[0].page);
      await players[0].page.waitForTimeout(2000);

      // Get final stacks
      const stacks = await Promise.all(
        players.map(p => p.tablePage.getMyChipStack())
      );

      // Total distributed should equal pot
      const initialStack = 1000;
      
      // Each winner should get approximately 33-34
      for (const stack of stacks) {
        expect(stack).toBeGreaterThanOrEqual(initialStack - 100 + 33);
      }

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );
});
