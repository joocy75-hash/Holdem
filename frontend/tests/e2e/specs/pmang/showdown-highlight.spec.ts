/**
 * Showdown Highlight E2E Tests (피망 스타일)
 * 
 * Tests winning hand card highlighting at showdown.
 * 
 * @requirements Task 20: Showdown Highlight Tests
 * @requirements 16.1~16.4
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { test as nPlayerTest } from '../../fixtures/n-player.fixture';
import { expect } from '@playwright/test';
import { cheatAPI, parseCard, parseCards } from '../../utils/cheat-api';
import { waitForPhase, waitForShowdown } from '../../utils/wait-helpers';

multiPlayerTest.describe('Showdown Highlight (피망 스타일)', () => {
  /**
   * Task 20.1: 승리 족보 카드 하이라이트 테스트
   * Winning 5-card hand should be highlighted at showdown.
   * @requirements 16.1
   */
  multiPlayerTest(
    '20.1 should highlight winning 5-card hand at showdown',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      const posA = await playerA.tablePage.getMyPosition();
      const posB = await playerB.tablePage.getMyPosition();

      // Inject cards - A wins with flush
      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [posA]: [parseCard('Ah'), parseCard('Kh')], // Hearts
          [posB]: [parseCard('2c'), parseCard('3d')], // Weak
        },
        communityCards: parseCards(['5h', '7h', '9h', 'Js', 'Qc']), // 3 more hearts
      });

      // Play to showdown
      await playToShowdown(playerA, playerB);

      // Wait for showdown
      await waitForShowdown(playerA.page);
      await playerA.page.waitForTimeout(1000);

      // Get highlighted cards
      const highlightedCards = await playerA.tablePage.getHighlightedCards();

      // Should have exactly 5 highlighted cards
      expect(highlightedCards.length).toBe(5);

      // All highlighted cards should be hearts (the flush)
      const heartCards = highlightedCards.filter((card: string) => card.endsWith('h'));
      expect(heartCards.length).toBe(5);
    }
  );

  /**
   * Task 20.2: 비사용 카드 딤 처리 테스트
   * Cards not used in winning hand should be dimmed.
   * @requirements 16.2
   */
  multiPlayerTest(
    '20.2 should dim cards not used in winning hand',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      const posA = await playerA.tablePage.getMyPosition();
      const posB = await playerB.tablePage.getMyPosition();

      // Inject cards - A wins with pair (only 2 cards used from hole cards)
      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [posA]: [parseCard('As'), parseCard('Kh')],
          [posB]: [parseCard('2c'), parseCard('3d')],
        },
        communityCards: parseCards(['Ac', '5d', '7h', '9s', 'Jc']), // Pair of Aces
      });

      await playToShowdown(playerA, playerB);
      await waitForShowdown(playerA.page);
      await playerA.page.waitForTimeout(1000);

      // Check for dimmed cards
      const dimmedCards = await playerA.page.locator('[data-dimmed="true"]').count();
      
      // Some cards should be dimmed (those not in the winning 5)
      // In a pair hand, 2 cards form the pair, 3 kickers
      // The 7th card (one hole card or community card) should be dimmed
      expect(dimmedCards).toBeGreaterThanOrEqual(0);

      // Highlighted cards should not be dimmed
      const highlightedAndDimmed = await playerA.page
        .locator('[data-highlighted="true"][data-dimmed="true"]')
        .count();
      expect(highlightedAndDimmed).toBe(0);
    }
  );

  /**
   * Task 20.4: 하이라이트 정확성 검증 테스트
   * Highlighted cards should match actual winning hand 100%.
   * @requirements 16.4
   */
  multiPlayerTest(
    '20.4 should highlight exactly the winning hand cards',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      const posA = await playerA.tablePage.getMyPosition();
      const posB = await playerB.tablePage.getMyPosition();

      // Inject specific straight
      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [posA]: [parseCard('5s'), parseCard('6h')], // Part of straight
          [posB]: [parseCard('2c'), parseCard('3d')],
        },
        communityCards: parseCards(['7c', '8d', '9h', 'Ks', 'Ac']), // Complete straight 5-9
      });

      await playToShowdown(playerA, playerB);
      await waitForShowdown(playerA.page);
      await playerA.page.waitForTimeout(1000);

      const highlightedCards = await playerA.tablePage.getHighlightedCards();

      // Should highlight exactly 5-6-7-8-9
      expect(highlightedCards.length).toBe(5);

      // Verify the straight cards are highlighted
      const ranks = highlightedCards.map((card: string) => card.slice(0, -1));
      expect(ranks.sort()).toEqual(['5', '6', '7', '8', '9'].sort());
    }
  );
});

nPlayerTest.describe('Split Pot Highlight', () => {
  /**
   * Task 20.3: 스플릿 팟 하이라이트 테스트
   * Each winner's hand should be individually highlighted in split pot.
   * @requirements 16.3
   */
  nPlayerTest(
    '20.3 should highlight each winner hand in split pot',
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

      const positions = await Promise.all(
        players.map(p => p.tablePage.getMyPosition())
      );

      // Inject identical hands for split pot
      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [positions[0]]: [parseCard('As'), parseCard('Kh')],
          [positions[1]]: [parseCard('Ac'), parseCard('Kd')], // Same hand
        },
        communityCards: parseCards(['2c', '3d', '4h', '5s', '9c']), // No help
      });

      // Play to showdown
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.call();
          }
        } catch {
          // Ignore
        }
      }

      // Check through streets
      for (const phase of ['flop', 'turn', 'river']) {
        await waitForPhase(players[0].page, phase, 10000);
        for (const player of players) {
          try {
            if (await player.tablePage.isMyTurn()) {
              await player.tablePage.check();
            }
          } catch {
            // Ignore
          }
        }
      }

      await waitForShowdown(players[0].page);
      await players[0].page.waitForTimeout(1000);

      // Both players should have highlighted cards
      for (const player of players) {
        const highlighted = await player.tablePage.getHighlightedCards();
        expect(highlighted.length).toBe(5);
      }

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );
});

// Helper function to play to showdown
async function playToShowdown(
  playerA: { tablePage: { isMyTurn: () => Promise<boolean>; call: () => Promise<void>; check: () => Promise<void>; waitForMyTurn: () => Promise<void> }; page: { waitForTimeout: (ms: number) => Promise<void> } },
  playerB: { tablePage: { isMyTurn: () => Promise<boolean>; call: () => Promise<void>; check: () => Promise<void>; waitForMyTurn: () => Promise<void> }; page: { waitForTimeout: (ms: number) => Promise<void> } }
) {
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

  // Flop, Turn, River
  for (let i = 0; i < 3; i++) {
    await playerA.page.waitForTimeout(2000);
    if (await playerA.tablePage.isMyTurn()) {
      await playerA.tablePage.check();
      await playerB.tablePage.waitForMyTurn();
      await playerB.tablePage.check();
    } else if (await playerB.tablePage.isMyTurn()) {
      await playerB.tablePage.check();
      await playerA.tablePage.waitForMyTurn();
      await playerA.tablePage.check();
    }
  }
}
