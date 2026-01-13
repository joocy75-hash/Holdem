/**
 * Blinds & Button Movement E2E Tests
 * 
 * Tests dealer button movement, SB/BB positioning, and special rules.
 * 
 * @requirements Task 9: Blind & Button Movement Tests
 */

import { test as multiPlayerTest } from '../../fixtures/multi-player.fixture';
import { test as nPlayerTest } from '../../fixtures/n-player.fixture';
import { expect } from '@playwright/test';
import { waitForPhase, waitForNewHand } from '../../utils/wait-helpers';

multiPlayerTest.describe('Blinds & Button Movement - 2 Players', () => {
  /**
   * Task 9.3: Heads-up(2인) 특수 규칙 테스트
   * In heads-up play, dealer posts SB and acts first preflop.
   */
  multiPlayerTest(
    '9.3 should apply heads-up rules: dealer=SB, opponent=BB',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Get positions
      const dealerPosA = await playerA.tablePage.getDealerPosition();
      const sbPosA = await playerA.tablePage.getSmallBlindPosition();
      const bbPosA = await playerA.tablePage.getBigBlindPosition();

      // In heads-up: dealer = SB
      expect(dealerPosA).toBe(sbPosA);
      
      // BB should be the other player
      expect(bbPosA).not.toBe(dealerPosA);

      // Verify same on player B's view
      const dealerPosB = await playerB.tablePage.getDealerPosition();
      const sbPosB = await playerB.tablePage.getSmallBlindPosition();
      const bbPosB = await playerB.tablePage.getBigBlindPosition();

      expect(dealerPosB).toBe(sbPosB);
      expect(dealerPosA).toBe(dealerPosB);
      expect(sbPosA).toBe(sbPosB);
      expect(bbPosA).toBe(bbPosB);
    }
  );

  /**
   * Task 9.1: 딜러 버튼 이동 테스트 (2인)
   * Dealer button should move clockwise after each hand.
   */
  multiPlayerTest(
    '9.1 should move dealer button clockwise after hand (heads-up)',
    async ({ playerA, playerB, tableId, setupBothPlayersAtTable }) => {
      await setupBothPlayersAtTable(tableId);
      await waitForPhase(playerA.page, 'preflop');

      // Record initial dealer position
      const initialDealer = await playerA.tablePage.getDealerPosition();

      // Complete a hand quickly (one player folds)
      if (await playerA.tablePage.isMyTurn()) {
        await playerA.tablePage.fold();
      } else {
        await playerB.tablePage.fold();
      }

      // Wait for new hand
      await waitForNewHand(playerA.page);
      await waitForPhase(playerA.page, 'preflop');

      // Dealer should have moved
      const newDealer = await playerA.tablePage.getDealerPosition();
      expect(newDealer).not.toBe(initialDealer);
    }
  );
});

nPlayerTest.describe('Blinds & Button Movement - Multi Player', () => {
  /**
   * Task 9.2: SB/BB 위치 테스트
   * SB should be immediately left of dealer, BB left of SB.
   */
  nPlayerTest(
    '9.2 should position SB left of dealer, BB left of SB',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(4);
      
      // Setup all players at table
      for (const player of players) {
        await player.tablePage.goto(tableId);
        await player.tablePage.waitForTableLoad();
        const emptySeat = await player.tablePage.findEmptySeat();
        if (emptySeat !== null) {
          await player.tablePage.clickEmptySeat(emptySeat);
          await player.tablePage.confirmBuyIn(1000);
        }
      }

      // Wait for hand to start
      await waitForPhase(players[0].page, 'preflop');

      // Get positions from first player's view
      const dealerPos = await players[0].tablePage.getDealerPosition();
      const sbPos = await players[0].tablePage.getSmallBlindPosition();
      const bbPos = await players[0].tablePage.getBigBlindPosition();

      // Calculate expected positions (clockwise)
      // In a 4-player game with positions 0,1,2,3
      // If dealer is at position X, SB is at (X+1)%4, BB is at (X+2)%4
      const expectedSB = (dealerPos + 1) % 4;
      const expectedBB = (dealerPos + 2) % 4;

      expect(sbPos).toBe(expectedSB);
      expect(bbPos).toBe(expectedBB);

      // Verify consistency across all players
      for (const player of players) {
        const pDealer = await player.tablePage.getDealerPosition();
        const pSB = await player.tablePage.getSmallBlindPosition();
        const pBB = await player.tablePage.getBigBlindPosition();

        expect(pDealer).toBe(dealerPos);
        expect(pSB).toBe(sbPos);
        expect(pBB).toBe(bbPos);
      }

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 9.1: 딜러 버튼 이동 테스트 (다인)
   */
  nPlayerTest(
    '9.1 should move dealer button clockwise after hand (multi-player)',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);
      
      // Setup all players
      for (const player of players) {
        await player.tablePage.goto(tableId);
        await player.tablePage.waitForTableLoad();
        const emptySeat = await player.tablePage.findEmptySeat();
        if (emptySeat !== null) {
          await player.tablePage.clickEmptySeat(emptySeat);
          await player.tablePage.confirmBuyIn(1000);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Record initial dealer
      const initialDealer = await players[0].tablePage.getDealerPosition();

      // Complete hand by having everyone fold except one
      for (const player of players) {
        if (await player.tablePage.isMyTurn()) {
          await player.tablePage.fold();
          break;
        }
      }

      // Wait for remaining players to act
      await players[0].page.waitForTimeout(2000);
      
      // Force hand completion if needed
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.fold();
          }
        } catch {
          // Player may have already folded or hand ended
        }
      }

      // Wait for new hand
      await waitForNewHand(players[0].page);
      await waitForPhase(players[0].page, 'preflop');

      // Dealer should have moved clockwise
      const newDealer = await players[0].tablePage.getDealerPosition();
      const expectedNewDealer = (initialDealer + 1) % 3;
      
      expect(newDealer).toBe(expectedNewDealer);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 9.4: 플레이어 이탈 후 버튼 이동 테스트
   */
  nPlayerTest(
    '9.4 should skip departed player when moving button',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(4);
      
      // Setup all players
      const positions: number[] = [];
      for (const player of players) {
        await player.tablePage.goto(tableId);
        await player.tablePage.waitForTableLoad();
        const emptySeat = await player.tablePage.findEmptySeat();
        if (emptySeat !== null) {
          await player.tablePage.clickEmptySeat(emptySeat);
          await player.tablePage.confirmBuyIn(1000);
          positions.push(emptySeat);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Record initial dealer
      const initialDealer = await players[0].tablePage.getDealerPosition();

      // Have one player leave (the one who would be next dealer)
      const nextDealerPos = (initialDealer + 1) % 4;
      const leavingPlayerIndex = positions.indexOf(nextDealerPos);
      
      if (leavingPlayerIndex !== -1) {
        await players[leavingPlayerIndex].tablePage.leaveTable();
        await players[leavingPlayerIndex].context.close();
        players.splice(leavingPlayerIndex, 1);
      }

      // Complete current hand
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.fold();
          }
        } catch {
          // Ignore errors
        }
      }

      // Wait for new hand
      await waitForNewHand(players[0].page);
      await waitForPhase(players[0].page, 'preflop');

      // Dealer should skip the departed position
      const newDealer = await players[0].tablePage.getDealerPosition();
      expect(newDealer).not.toBe(nextDealerPos);

      // Cleanup remaining players
      for (const player of players) {
        await player.context.close();
      }
    }
  );
});
