/**
 * Wait Helpers for E2E Tests
 * 
 * Provides utility functions for waiting on various
 * game state conditions and UI updates.
 */

import { Page } from '@playwright/test';

// Extend Window interface for game WebSocket
declare global {
  interface Window {
    __gameWebSocket?: WebSocket;
  }
}

/**
 * Wait for WebSocket connection to be established
 */
export async function waitForWebSocketConnection(
  page: Page,
  timeout: number = 10000
): Promise<void> {
  await page.waitForFunction(
    () => {
      const ws = window.__gameWebSocket;
      return ws && ws.readyState === WebSocket.OPEN;
    },
    { timeout }
  );
}

/**
 * Wait for game state to be synchronized
 */
export async function waitForGameStateSync(
  page: Page,
  timeout: number = 5000
): Promise<void> {
  await page.waitForSelector('[data-state-synced="true"]', { timeout });
}

/**
 * Wait for specific game phase
 */
export async function waitForPhase(
  page: Page,
  phase: string,
  timeout: number = 30000
): Promise<void> {
  await page.waitForSelector(`[data-phase="${phase}"]`, { timeout });
}

/**
 * Wait for pot amount to reach specific value
 */
export async function waitForPotAmount(
  page: Page,
  amount: number,
  timeout: number = 10000
): Promise<void> {
  await page.waitForFunction(
    (expectedAmount) => {
      const potElement = document.querySelector('[data-testid="pot-amount"]');
      if (!potElement) return false;
      const currentAmount = parseInt(
        potElement.textContent?.replace(/[^0-9]/g, '') || '0'
      );
      return currentAmount >= expectedAmount;
    },
    amount,
    { timeout }
  );
}

/**
 * Wait for player to be seated at position
 */
export async function waitForPlayerSeated(
  page: Page,
  position: number,
  timeout: number = 10000
): Promise<void> {
  await page.waitForSelector(
    `[data-testid="seat-${position}"][data-occupied="true"]`,
    { timeout }
  );
}

/**
 * Wait for player's turn
 */
export async function waitForTurn(
  page: Page,
  position: number,
  timeout: number = 30000
): Promise<void> {
  await page.waitForSelector(
    `[data-testid="seat-${position}"][data-is-turn="true"]`,
    { timeout }
  );
}

/**
 * Wait for showdown to complete
 */
export async function waitForShowdown(
  page: Page,
  timeout: number = 30000
): Promise<void> {
  await page.waitForSelector('[data-phase="showdown"]', { timeout });
}

/**
 * Wait for winner to be announced
 */
export async function waitForWinner(
  page: Page,
  timeout: number = 10000
): Promise<void> {
  await page.waitForSelector('[data-testid^="win-badge-"]', { timeout });
}

/**
 * Wait for new hand to start
 */
export async function waitForNewHand(
  page: Page,
  timeout: number = 15000
): Promise<void> {
  // Wait for preflop phase with hole cards dealt
  await page.waitForSelector('[data-phase="preflop"]', { timeout });
  await page.waitForSelector('[data-testid="my-hole-cards"]', { timeout });
}

/**
 * Wait for community cards to be dealt
 */
export async function waitForCommunityCards(
  page: Page,
  count: number,
  timeout: number = 10000
): Promise<void> {
  await page.waitForFunction(
    (expectedCount) => {
      const cards = document.querySelectorAll(
        '[data-testid^="community-card-"]'
      );
      return cards.length >= expectedCount;
    },
    count,
    { timeout }
  );
}

/**
 * Wait for action buttons to be enabled
 */
export async function waitForActionButtons(
  page: Page,
  timeout: number = 30000
): Promise<void> {
  await page.waitForSelector('[data-testid="fold-button"]:not([disabled])', {
    timeout,
  });
}

/**
 * Wait for action buttons to be disabled
 */
export async function waitForActionButtonsDisabled(
  page: Page,
  timeout: number = 5000
): Promise<void> {
  await page.waitForSelector('[data-testid="fold-button"][disabled]', {
    timeout,
  });
}

/**
 * Wait for timer to reach specific value
 */
export async function waitForTimerValue(
  page: Page,
  maxSeconds: number,
  timeout: number = 35000
): Promise<void> {
  await page.waitForFunction(
    (max) => {
      const timer = document.querySelector('[data-testid="turn-timer"]');
      if (!timer) return false;
      const seconds = parseInt(timer.textContent?.replace(/[^0-9]/g, '') || '0');
      return seconds <= max;
    },
    maxSeconds,
    { timeout }
  );
}

/**
 * Wait for player status change
 */
export async function waitForPlayerStatus(
  page: Page,
  position: number,
  status: string,
  timeout: number = 10000
): Promise<void> {
  await page.waitForSelector(
    `[data-testid="seat-${position}"][data-status="${status}"]`,
    { timeout }
  );
}

/**
 * Wait for chip stack update
 */
export async function waitForStackUpdate(
  page: Page,
  position: number,
  expectedStack: number,
  timeout: number = 10000
): Promise<void> {
  await page.waitForFunction(
    ({ pos, expected }) => {
      const stack = document.querySelector(`[data-testid="stack-${pos}"]`);
      if (!stack) return false;
      const current = parseInt(stack.textContent?.replace(/[^0-9]/g, '') || '0');
      return current === expected;
    },
    { pos: position, expected: expectedStack },
    { timeout }
  );
}

/**
 * Wait for side pot to appear
 */
export async function waitForSidePot(
  page: Page,
  index: number = 0,
  timeout: number = 10000
): Promise<void> {
  await page.waitForSelector(`[data-testid="side-pot-${index}"]`, { timeout });
}

/**
 * Wait for hand ranking guide update
 */
export async function waitForHandRankingUpdate(
  page: Page,
  expectedRank: string,
  timeout: number = 5000
): Promise<void> {
  await page.waitForFunction(
    (rank) => {
      const guide = document.querySelector('[data-testid="current-hand-rank"]');
      return guide?.textContent?.includes(rank);
    },
    expectedRank,
    { timeout }
  );
}

/**
 * Wait for card squeeze animation to complete
 */
export async function waitForSqueezeComplete(
  page: Page,
  cardIndex: number,
  timeout: number = 5000
): Promise<void> {
  await page.waitForSelector(
    `[data-testid="hole-card-${cardIndex}"][data-revealed="true"]`,
    { timeout }
  );
}

/**
 * Wait for UI to be unlocked after animation
 */
export async function waitForUIUnlock(
  page: Page,
  timeout: number = 5000
): Promise<void> {
  await page.waitForFunction(
    () => {
      const locked = document.querySelector('[data-ui-locked="true"]');
      return !locked;
    },
    { timeout }
  );
}

/**
 * Retry an action until it succeeds or timeout
 */
export async function retryUntilSuccess<T>(
  action: () => Promise<T>,
  maxAttempts: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await action();
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
  
  throw lastError;
}

/**
 * Wait for network idle (no pending requests)
 */
export async function waitForNetworkIdle(
  page: Page,
  timeout: number = 5000
): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}
