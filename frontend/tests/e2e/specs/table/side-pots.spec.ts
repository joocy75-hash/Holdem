/**
 * Side Pot E2E Tests
 * 
 * Tests side pot creation, calculation, and distribution.
 * 
 * @requirements Task 11: Side Pot Tests
 * @requirements 6.2 확장
 */

import { test as nPlayerTest } from '../../fixtures/n-player.fixture';
import { expect } from '@playwright/test';
import { cheatAPI, parseCards } from '../../utils/cheat-api';
import { waitForPhase, waitForShowdown, waitForSidePot } from '../../utils/wait-helpers';

nPlayerTest.describe('Side Pot Creation & Distribution', () => {
  /**
   * Task 11.1: 올인 시 메인 팟 분리 테스트
   * When a player goes all-in, main pot should be separated from side pot.
   */
  nPlayerTest(
    '11.1 should separate main pot when player goes all-in',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);
      
      // Setup players with different stack sizes
      // Player 0: 100 chips (will go all-in)
      // Player 1: 500 chips
      // Player 2: 500 chips
      await cheatAPI.setPlayerStack(players[0].user.id, 100);
      await cheatAPI.setPlayerStack(players[1].user.id, 500);
      await cheatAPI.setPlayerStack(players[2].user.id, 500);

      // Setup all players at table
      for (let i = 0; i < players.length; i++) {
        await players[i].tablePage.goto(tableId);
        await players[i].tablePage.waitForTableLoad();
        const seat = await players[i].tablePage.findEmptySeat();
        if (seat !== null) {
          await players[i].tablePage.clickEmptySeat(seat);
          await players[i].tablePage.confirmBuyIn(i === 0 ? 100 : 500);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Player 0 goes all-in (100 chips)
      for (const player of players) {
        if (await player.tablePage.isMyTurn()) {
          const stack = await player.tablePage.getMyChipStack();
          if (stack === 100) {
            await player.tablePage.allIn();
            break;
          }
        }
      }

      // Other players call or raise
      for (const player of players) {
        try {
          if (await player.tablePage.isMyTurn()) {
            await player.tablePage.call();
          }
        } catch {
          // Player may have already acted
        }
      }

      // Wait for side pot to appear
      await waitForSidePot(players[1].page, 0, 10000);

      // Verify side pot exists
      const sidePots = await players[1].tablePage.getSidePots();
      expect(sidePots.length).toBeGreaterThanOrEqual(1);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 11.2: 사이드 팟 계산 정확성 테스트
   * 3인 플레이: A(100칩) 올인, B/C(500칩) 추가 레이즈
   * 메인 팟: 300칩(100×3), 사이드 팟: 800칩((500-100)×2)
   */
  nPlayerTest(
    '11.2 should calculate side pot amounts correctly',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);
      
      // Setup specific stacks
      await cheatAPI.setPlayerStack(players[0].user.id, 100);
      await cheatAPI.setPlayerStack(players[1].user.id, 500);
      await cheatAPI.setPlayerStack(players[2].user.id, 500);

      for (let i = 0; i < players.length; i++) {
        await players[i].tablePage.goto(tableId);
        await players[i].tablePage.waitForTableLoad();
        const seat = await players[i].tablePage.findEmptySeat();
        if (seat !== null) {
          await players[i].tablePage.clickEmptySeat(seat);
          await players[i].tablePage.confirmBuyIn(i === 0 ? 100 : 500);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Force specific betting scenario via cheat API
      await cheatAPI.forceBettingScenario(tableId, {
        actions: [
          { playerId: players[0].user.id, action: 'allin', amount: 100 },
          { playerId: players[1].user.id, action: 'raise', amount: 500 },
          { playerId: players[2].user.id, action: 'call', amount: 500 },
        ],
      });

      await players[0].page.waitForTimeout(2000);

      // Verify pot amounts
      const mainPot = await players[1].tablePage.getPotAmount();
      const sidePots = await players[1].tablePage.getSidePots();

      // Main pot should be 300 (100 × 3)
      expect(mainPot).toBe(300);

      // Side pot should be 800 ((500-100) × 2)
      expect(sidePots.length).toBe(1);
      expect(sidePots[0].amount).toBe(800);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 11.3: 다중 사이드 팟 테스트
   * 4인 플레이: A(100), B(200), C(500), D(500) 올인
   */
  nPlayerTest(
    '11.3 should create multiple side pots correctly',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(4);
      
      // Setup different stacks
      await cheatAPI.setPlayerStack(players[0].user.id, 100);
      await cheatAPI.setPlayerStack(players[1].user.id, 200);
      await cheatAPI.setPlayerStack(players[2].user.id, 500);
      await cheatAPI.setPlayerStack(players[3].user.id, 500);

      for (let i = 0; i < players.length; i++) {
        await players[i].tablePage.goto(tableId);
        await players[i].tablePage.waitForTableLoad();
        const seat = await players[i].tablePage.findEmptySeat();
        if (seat !== null) {
          const buyIn = [100, 200, 500, 500][i];
          await players[i].tablePage.clickEmptySeat(seat);
          await players[i].tablePage.confirmBuyIn(buyIn);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Force all-in scenario
      await cheatAPI.forceBettingScenario(tableId, {
        actions: [
          { playerId: players[0].user.id, action: 'allin', amount: 100 },
          { playerId: players[1].user.id, action: 'allin', amount: 200 },
          { playerId: players[2].user.id, action: 'allin', amount: 500 },
          { playerId: players[3].user.id, action: 'call', amount: 500 },
        ],
      });

      await players[0].page.waitForTimeout(2000);

      // Verify multiple side pots
      const sidePots = await players[2].tablePage.getSidePots();

      // Should have 2 side pots:
      // Main pot: 400 (100 × 4)
      // Side pot 1: 300 ((200-100) × 3)
      // Side pot 2: 600 ((500-200) × 2)
      expect(sidePots.length).toBe(2);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );

  /**
   * Task 11.4: 사이드 팟 승자 분배 테스트
   * 메인 팟 승자와 사이드 팟 승자가 다를 때 정확 분배 확인
   */
  nPlayerTest(
    '11.4 should distribute side pots to correct winners',
    async ({ tableId, createPlayers }) => {
      const players = await createPlayers(3);
      
      // Setup stacks
      await cheatAPI.setPlayerStack(players[0].user.id, 100);
      await cheatAPI.setPlayerStack(players[1].user.id, 500);
      await cheatAPI.setPlayerStack(players[2].user.id, 500);

      for (let i = 0; i < players.length; i++) {
        await players[i].tablePage.goto(tableId);
        await players[i].tablePage.waitForTableLoad();
        const seat = await players[i].tablePage.findEmptySeat();
        if (seat !== null) {
          await players[i].tablePage.clickEmptySeat(seat);
          await players[i].tablePage.confirmBuyIn(i === 0 ? 100 : 500);
        }
      }

      await waitForPhase(players[0].page, 'preflop');

      // Get positions for card injection
      const positions = await Promise.all(
        players.map(p => p.tablePage.getMyPosition())
      );

      // Inject cards so player 0 wins main pot, player 1 wins side pot
      // Player 0: AA (wins main pot)
      // Player 1: KK (wins side pot)
      // Player 2: QQ (loses)
      await cheatAPI.injectDeck(tableId, {
        holeCards: {
          [positions[0]]: parseCards(['As', 'Ah']) as [typeof parseCards extends (a: string[]) => (infer R)[] ? R : never, typeof parseCards extends (a: string[]) => (infer R)[] ? R : never],
          [positions[1]]: parseCards(['Ks', 'Kh']) as [typeof parseCards extends (a: string[]) => (infer R)[] ? R : never, typeof parseCards extends (a: string[]) => (infer R)[] ? R : never],
          [positions[2]]: parseCards(['Qs', 'Qh']) as [typeof parseCards extends (a: string[]) => (infer R)[] ? R : never, typeof parseCards extends (a: string[]) => (infer R)[] ? R : never],
        },
        communityCards: parseCards(['2c', '3d', '4h', '5s', '6c']),
      });

      // Force all-in scenario
      await cheatAPI.forceBettingScenario(tableId, {
        actions: [
          { playerId: players[0].user.id, action: 'allin', amount: 100 },
          { playerId: players[1].user.id, action: 'raise', amount: 500 },
          { playerId: players[2].user.id, action: 'call', amount: 500 },
        ],
      });

      // Wait for showdown
      await waitForShowdown(players[0].page);

      // Record final stacks
      const finalStack0 = await players[0].tablePage.getMyChipStack();
      const finalStack1 = await players[1].tablePage.getMyChipStack();
      const finalStack2 = await players[2].tablePage.getMyChipStack();

      // Player 0 should win main pot (300)
      expect(finalStack0).toBe(300);

      // Player 1 should win side pot (800)
      expect(finalStack1).toBe(800);

      // Player 2 should have 0
      expect(finalStack2).toBe(0);

      // Cleanup
      for (const player of players) {
        await player.context.close();
      }
    }
  );
});
