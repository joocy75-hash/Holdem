/**
 * Card Squeeze Animation E2E Tests (피망 스타일)
 * 
 * Tests card squeeze (쪼기) gesture and animation.
 * 
 * @requirements Task 21: Card Squeeze Tests
 * @requirements 17.1~17.7
 */

import { test as authTest } from '../../fixtures/auth.fixture';
import { expect } from '@playwright/test';
import { TablePage } from '../../pages/table.page';
import { cheatAPI } from '../../utils/cheat-api';
import { waitForPhase, waitForSqueezeComplete, waitForUIUnlock } from '../../utils/wait-helpers';

authTest.describe('Card Squeeze Animation (피망 스타일)', () => {
  /**
   * Task 21.1: 드래그 비례 카드 공개 테스트
   * Card should reveal proportionally to drag distance.
   * @requirements 17.1
   */
  authTest(
    '21.1 should reveal card proportionally to drag distance',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      // Sit at table
      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      // Wait for another player (or use cheat API to add bot)
      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Start squeeze on first card (small drag)
      await tablePage.squeezeCard(0, 20); // Small drag

      // Check reveal percentage
      const revealPercent = await authenticatedPage.evaluate(() => {
        const card = document.querySelector('[data-testid="hole-card-0"]');
        return parseFloat(card?.getAttribute('data-reveal-percent') || '0');
      });

      // Should be partially revealed
      expect(revealPercent).toBeGreaterThan(0);
      expect(revealPercent).toBeLessThan(100);

      // Release
      await tablePage.releaseCardSqueeze();
    }
  );

  /**
   * Task 21.2: 임계값 초과 시 완전 뒤집기 테스트
   * Card should fully flip when drag exceeds threshold.
   * @requirements 17.2
   */
  authTest(
    '21.2 should fully flip card when drag exceeds threshold',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Large drag to exceed threshold
      await tablePage.squeezeCard(0, 100);
      await tablePage.releaseCardSqueeze();

      // Wait for animation
      await waitForSqueezeComplete(authenticatedPage, 0);

      // Card should be fully revealed
      const isRevealed = await tablePage.isCardRevealed(0);
      expect(isRevealed).toBe(true);
    }
  );

  /**
   * Task 21.3: Snap Back 테스트
   * Card should snap back when released below threshold.
   * @requirements 17.3
   */
  authTest(
    '21.3 should snap back when released below threshold',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Small drag below threshold
      await tablePage.squeezeCard(1, 15); // Card index 1, small drag

      // Release
      await tablePage.releaseCardSqueeze();

      // Wait for snap back animation
      await authenticatedPage.waitForTimeout(500);

      // Card should NOT be revealed (snapped back)
      const isRevealed = await tablePage.isCardRevealed(1);
      expect(isRevealed).toBe(false);

      // Reveal percent should be 0 (snapped back)
      const revealPercent = await authenticatedPage.evaluate(() => {
        const card = document.querySelector('[data-testid="hole-card-1"]');
        return parseFloat(card?.getAttribute('data-reveal-percent') || '0');
      });
      expect(revealPercent).toBe(0);
    }
  );

  /**
   * Task 21.4: 앞뒷면 전환 부드러움 테스트
   * Card flip animation should be smooth.
   * @requirements 17.4
   */
  authTest(
    '21.4 should have smooth card flip animation',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Check for CSS transition on card
      const hasTransition = await authenticatedPage.evaluate(() => {
        const card = document.querySelector('[data-testid="hole-card-0"]');
        if (!card) return false;
        const style = window.getComputedStyle(card);
        return style.transition !== 'none' && style.transition !== '';
      });

      expect(hasTransition).toBe(true);

      // Perform squeeze and check animation frames
      await tablePage.squeezeCard(0, 50);
      
      // Check that transform is being applied smoothly
      const hasTransform = await authenticatedPage.evaluate(() => {
        const card = document.querySelector('[data-testid="hole-card-0"]');
        if (!card) return false;
        const style = window.getComputedStyle(card);
        return style.transform !== 'none';
      });

      expect(hasTransform).toBe(true);

      await tablePage.releaseCardSqueeze();
    }
  );

  /**
   * Task 21.5: UI 잠금 테스트
   * UI should be locked during squeeze animation.
   * @requirements 17.5
   */
  authTest(
    '21.5 should lock UI during squeeze animation',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Start squeeze
      await tablePage.squeezeCard(0, 50);

      // Check if UI is locked
      const isLocked = await tablePage.isUILocked();
      expect(isLocked).toBe(true);

      // Betting buttons should be disabled
      const foldEnabled = await tablePage.foldButton.isEnabled();
      expect(foldEnabled).toBe(false);

      await tablePage.releaseCardSqueeze();
    }
  );

  /**
   * Task 21.6: UI 잠금 해제 테스트
   * UI should unlock after squeeze completes.
   * @requirements 17.6
   */
  authTest(
    '21.6 should unlock UI after squeeze completes',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Complete squeeze
      await tablePage.squeezeCard(0, 100);
      await tablePage.releaseCardSqueeze();

      // Wait for animation to complete
      await waitForSqueezeComplete(authenticatedPage, 0);
      await waitForUIUnlock(authenticatedPage);

      // UI should be unlocked
      const isLocked = await tablePage.isUILocked();
      expect(isLocked).toBe(false);

      // If it's our turn, buttons should be enabled
      const isMyTurn = await tablePage.isMyTurn();
      if (isMyTurn) {
        const foldEnabled = await tablePage.foldButton.isEnabled();
        expect(foldEnabled).toBe(true);
      }
    }
  );

  /**
   * Task 21.7: 그래픽 버그 검증 테스트
   * No graphical glitches during squeeze at various angles.
   * @requirements 17.7
   */
  authTest(
    '21.7 should have no graphical bugs during squeeze',
    async ({ authenticatedPage, tableId }) => {
      const tablePage = new TablePage(authenticatedPage);
      await tablePage.goto(tableId);
      await tablePage.waitForTableLoad();

      await tablePage.clickEmptySeat(0);
      await tablePage.confirmBuyIn(1000);

      await cheatAPI.addBotPlayer(tableId);
      await waitForPhase(authenticatedPage, 'preflop');

      // Test various drag distances
      const dragDistances = [10, 25, 50, 75, 100];

      for (const distance of dragDistances) {
        await tablePage.squeezeCard(0, distance);

        // Check for visual glitches
        const hasGlitch = await authenticatedPage.evaluate(() => {
          const card = document.querySelector('[data-testid="hole-card-0"]');
          if (!card) return true;

          // Check for common glitches
          const rect = card.getBoundingClientRect();
          
          // Card should have valid dimensions
          if (rect.width <= 0 || rect.height <= 0) return true;
          
          // Card should be within viewport
          if (rect.left < -100 || rect.top < -100) return true;
          
          // Check for NaN in transform
          const style = window.getComputedStyle(card);
          if (style.transform.includes('NaN')) return true;

          return false;
        });

        expect(hasGlitch).toBe(false);

        await tablePage.releaseCardSqueeze();
        await authenticatedPage.waitForTimeout(300);
      }
    }
  );
});
